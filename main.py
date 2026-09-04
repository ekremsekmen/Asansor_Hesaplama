# -*- coding: utf-8 -*-
"""
ASANSÖR AVAN HESAPLAMA PROGRAMI
=================================
Yerel sunucu + tarayıcı arayüzü.  Çalıştırmak için:

    python3 main.py

Tarayıcı kendiliğinden açılır (http://127.0.0.1:8760).
Program tümüyle bilgisayarınızda çalışır, internet gerektirmez.
"""
import json
import math
import os
import re
import sys
import threading
import webbrowser
from datetime import date

from fastapi import Body, FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine import avan as E_AVAN            # noqa: E402
from engine import mukavemet_girdi as E_MGR  # noqa: E402
from engine import uygulama as E_UYG         # noqa: E402
from engine import uygulama_girdi as E_UGR   # noqa: E402
from engine import tables as E_TAB           # noqa: E402
from engine import traffic as E_TRF          # noqa: E402
#  CAD çıktısı ezdxf + pdfminer.six ister.  Bunlar kurulu değilse PROGRAM
#  YİNE AÇILIR — yalnız "Avan Projesini DWG al" düğmesi anlaşılır bir hata verir.
_BASLATICI = "baslat.bat" if os.name == "nt" else "baslat.command"
try:
    from exports import dxf_export as X_DXF      # noqa: E402
except Exception as _dxf_hata:                   # noqa: BLE001
    X_DXF, _DXF_HATA = None, str(_dxf_hata)
else:
    _DXF_HATA = None
from exports import kapak_export as X_KAPAK  # noqa: E402
from exports import mukavemet_xlsx as X_MXLS  # noqa: E402
from exports import pdf_export as X_PDF      # noqa: E402
from exports import sablon_denetim as X_DEN
from exports import xlsx_export as X_XLS     # noqa: E402
from exports import xlsx_import as X_IMP     # noqa: E402

SURUM = "2.7"
KOK = os.path.dirname(os.path.abspath(__file__))
PORT = int(os.environ.get("AVAN_PORT", "8760"))

app = FastAPI(title="Asansör Avan Hesaplama Programı", version=SURUM,
              docs_url=None, redoc_url=None)


# ------------------------------------------------------------------ yardımcı
#  BELİRSİZ SAYI  —  "1.200" bin iki yüz mü, bir nokta iki mi?
#  Program ondalık ayracı olarak hem virgülü hem noktayı kabul ediyor; bu da
#  TEK ayraçlı ve ardından TAM ÜÇ RAKAM gelen yazımları belirsiz bırakır:
#  Türkçede 1.200 = bin iki yüz, 1,200 = bir virgül iki.  Program bunu
#  tahmin ETMEZ — reddeder ve kullanıcıya nasıl yazması gerektiğini söyler.
#  Sessizce 1,2 okumak 1.200 daireli bir binada asansör adedini 41'den 2'ye
#  düşürüyordu.
#  Tam sayı kısmı SIFIRLA BAŞLAMAMALI: "0,075" ( = %7,5 ) belirsiz değildir,
#  çünkü binlik ayracı sıfırdan sonra gelmez.  Belirsiz olan "1.200" gibi
#  1-3 basamaklı, sıfırla başlamayan bir sayıdan sonra tam üç rakam gelmesidir.
BELIRSIZ_SAYI = re.compile(r"^[+-]?[1-9]\d{0,2}[.,]\d{3}$")


def belirsiz_sayi_mi(x) -> bool:
    if not isinstance(x, str):
        return False
    return bool(BELIRSIZ_SAYI.match(x.strip().replace(" ", "").replace("\u00a0", "")))


def _sayi(x):
    """
    Metni sayıya çevirir.  Kabul edilen biçimler:
        "1,60"  "1.60"  "1.234,56"  "1,234.56"  "  3  "  12  3.0
    Geçersiz, boş, sonsuz, NaN veya BELİRSİZ değerlerde None döner —
    bu sayede bozuk girdi hesabı çökertmez, "eksik girdi" olarak işlenir.
    """
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return x if math.isfinite(x) else None
    if not isinstance(x, str):
        return None
    s = x.strip().replace(" ", "").replace("\u00a0", "")
    if s == "":
        return None
    if BELIRSIZ_SAYI.match(s):        # "1.200" / "1,200" → hangisi belli değil
        return None
    # Hangi ayraç SONDA ise ondalık ayracıdır; diğeri binlik ayracıdır.
    son_virgul, son_nokta = s.rfind(","), s.rfind(".")
    if son_virgul >= 0 and son_nokta >= 0:
        if son_virgul > son_nokta:                    # 1.234,56  → TR biçimi
            s = s.replace(".", "").replace(",", ".")
        else:                                         # 1,234.56  → EN biçimi
            s = s.replace(",", "")
    elif son_virgul >= 0:
        s = s.replace(",", ".")                       # 1,60
    try:
        f = float(s)
    except ValueError:
        return None
    if not math.isfinite(f):                          # inf / -inf / nan
        return None
    if abs(f) > 1e12:                                 # anlamsız büyüklükler
        return None
    return int(f) if f.is_integer() else f


#  Belirsiz yazılmış alanların adları burada toplanır ki kullanıcıya
#  "eksik girdi" yerine gerçek sebep söylenebilsin.
#
#  İSTEK BAŞINA AYRI LİSTE:  FastAPI'de `def` ( async olmayan ) uç noktalar bir
#  iş parçacığı havuzunda koşar, yani İKİ İSTEK AYNI ANDA çalışabilir.  Ortak
#  bir liste kullanılsaydı biri listeyi temizlerken diğeri okuyabilir ve
#  geçerli bir indirme "belirsiz sayı" diye reddedilebilir ya da tersi, bozuk
#  bir girdi denetimden kaçabilirdi.  ( Ekran her tuş vuruşunda hesap
#  isterken indirmeye basılması bu iki isteği gerçekten çakıştırır. )
class _BelirsizListesi(threading.local):
    def __init__(self):
        self.kalemler = []

    def clear(self):
        self.kalemler = []

    def append(self, x):
        self.kalemler.append(x)

    def __bool__(self):
        return bool(self.kalemler)

    def __iter__(self):
        return iter(self.kalemler)


_BELIRSIZ = _BelirsizListesi()
#  BELİRSİZLİKTEN BAŞKA SEBEPLE REDDEDİLEN GİRDİLER ( negatif miktar, seçilmemiş
#  kalem, şablon sınırını aşan satır … ).  Ayrı tutulur çünkü belirsiz-sayı
#  açıklaması ( "binlik ayracı mı ondalık mı" ) bunlar için YANLIŞ olur.
_RED = _BelirsizListesi()


def _temiz(d: dict, sayisal: tuple, on_ek: str = "") -> dict:
    out = dict(d or {})
    for k in sayisal:
        ham = out.get(k)
        if belirsiz_sayi_mi(ham):
            _BELIRSIZ.append(f"{on_ek}{k} = {str(ham).strip()}")
        out[k] = _sayi(ham)
    return out


def _belirsiz_hata():
    """Reddedilen girdi varsa açık hata metni, yoksa None."""
    if _BELIRSIZ:
        liste = "  ·  ".join(sorted(set(_BELIRSIZ.kalemler))[:6])
        return ("HESAP HATASI: Belirsiz sayı yazımı  —  " + liste +
                "   ·   Bu yazımda binlik ayracı mı ondalık ayracı mı olduğu "
                "anlaşılmıyor ( Türkçede 1.200 = bin iki yüz, 1,200 = bir virgül iki; "
                "program ikisini de ondalık kabul ediyor ). Binlik ayracı KULLANMAYIN: "
                "bin iki yüz için 1200, bir virgül iki için 1,2 yazın.")
    if _RED:
        return ("HESAP HATASI: Girdi kabul edilmedi  —  "
                + "  ·  ".join(sorted(set(_RED.kalemler))[:6])
                + "   ·   Satırı düzeltin ya da kaldırın; sessizce yok sayılmaz.")
    return None

TRAFIK_SAYISAL = ("bina_yuksekligi", "yapi_yuksekligi", "N", "hizli1", "hizli2", "h", "P",
                  "kapi_genisligi", "bodrum", "manuel_k", "manuel_V", "manuel_ta",
                  "manuel_tk", "manuel_tg", "manuel_tp", "manuel_adet")
ASANSOR_SAYISAL = ("P", "kapi_genisligi", "V", "durak", "h", "bodrum",
                   "manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp")
AVAN_ORTAK_SAYISAL = ("U", "kappa", "eps_max", "temel_a", "temel_b", "beta", "serit_L",
                      "cubuk_sayisi", "mk_uzunluk", "mk_genislik")
AVAN_AS_SAYISAL = ("i_palanga", "q_denge",
                   "kapasite", "Q_elle", "V", "eta", "Hk", "kuyu_genisligi", "kabin_boyu",
                   "kabin_genisligi", "Gk_elle", "gr", "Fmk", "Fsh", "Nsc",
                   "S1", "L1", "S2", "L2")


#  EK NÜFUS SATIRLARI  —  BOZUK GİRDİ SESSİZCE SİLİNMEZ.
#  Eskiden okunamayan miktar ( "1.200", "abc" ) satırı hesaptan tamamen
#  çıkarıyordu:  1200 yazınca 11 asansör, 1.200 yazınca 2 asansör çıkıyor ve
#  aradaki fark hiçbir yerde söylenmiyordu.  Belirsiz yazım zaten _BELIRSIZ
#  listesine düşer ( ekran ve indirme aynı kapıdan geçer ); geri kalan bozuk
#  ya da negatif satırlar için açık hata üretilir.
EK_NUFUS_AZAMI = 11          # şablondaki satır adedi ( bkz. hucre_haritasi )


def _ek_nufus_oku(ham):
    """Ek nüfus satırlarını okur.  Bozuk satırlar `_BELIRSIZ` üzerinden bildirilir."""
    satirlar = []
    for i, s in enumerate(_sozluk_listesi(ham), 1):
        kalem, ham_miktar = s.get("kalem"), s.get("miktar")
        if not kalem and (ham_miktar in (None, "")):
            continue                                  # tümüyle boş satır — yok say
        if belirsiz_sayi_mi(ham_miktar):
            _BELIRSIZ.append(f"ek nüfus {i}. satır miktarı = {str(ham_miktar).strip()}")
            continue
        miktar = _sayi(ham_miktar)
        if not kalem:
            _RED.append(f"ek nüfus {i}. satırında Tablo-1 kalemi seçilmemiş")
            continue
        if miktar is None:
            _RED.append(f"ek nüfus {i}. satır miktarı sayı değil "
                        f"( {str(ham_miktar).strip()[:20]!r} )")
            continue
        if miktar < 0:
            _RED.append(f"ek nüfus {i}. satır miktarı negatif ( {miktar} ) — "
                    "nüfus eksiltilemez")
            continue
        satirlar.append({"aciklama": s.get("aciklama"), "miktar": miktar, "kalem": kalem})
    #  ŞABLON SINIRI:  fazlası Excel'e yazılamaz, sessizce düşerdi.
    if len(satirlar) > EK_NUFUS_AZAMI:
        _RED.append(f"ek nüfus satır adedi {len(satirlar)} — Excel şablonu en fazla "
                    f"{EK_NUFUS_AZAMI} satır taşır; kalemleri birleştirin")
        return satirlar[:EK_NUFUS_AZAMI]
    return satirlar


def _sozluk_listesi(x):
    """Yalnız sözlük öğelerini geçiren güvenli liste — bozuk gövdede çökmez."""
    if not isinstance(x, (list, tuple)):
        return []
    return [e for e in x if isinstance(e, dict)]


def _trafik_girdi(veri: dict):
    """
    Trafik girdisini tek biçime getirir:  bina alanları + `asansorler` listesi.

    Yöntemi ( tek / çoklu ) ARTIK KULLANICI SEÇMEZ, veri belirler — bkz.
    engine.traffic.hesapla().  Eski `mod` alanı ve düz `P / kapi_genisligi /
    kapi_tipi` girdileri geriye dönük uyumluluk için hâlâ kabul edilir:
    liste boşsa düz alanlardan TEK asansörlük bir liste kurulur.
    """
    _BELIRSIZ.clear(); _RED.clear()
    veri = veri if isinstance(veri, dict) else {}
    ham = veri.get("girdiler")
    ham = ham if isinstance(ham, dict) else {}
    g = _temiz(ham, TRAFIK_SAYISAL)
    g["ek_nufus"] = _ek_nufus_oku(ham.get("ek_nufus"))
    liste = [_temiz(a, ASANSOR_SAYISAL, f"ASANSÖR-{i}: ")
             for i, a in enumerate(_sozluk_listesi(ham.get("asansorler")), 1)
             if _sayi(a.get("P")) is not None][:4]
    if not liste and g.get("P") is not None:
        bir = {k: g.get(k) for k in ("P", "kapi_genisligi",
                                     "manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp")}
        bir["kapi_tipi"] = ham.get("kapi_tipi")
        liste = [bir]
    g["asansorler"] = liste
    return g


def _avan_girdi(veri: dict):
    _BELIRSIZ.clear(); _RED.clear()
    veri = veri if isinstance(veri, dict) else {}
    v = veri.get("girdiler")
    v = v if isinstance(v, dict) else {}
    ortak_ham = v.get("ortak")
    ortak = _temiz(ortak_ham if isinstance(ortak_ham, dict) else {}, AVAN_ORTAK_SAYISAL)
    asansorler = []
    for sira, a in enumerate(_sozluk_listesi(v.get("asansorler"))[:4], 1):
        if not a.get("aktif", True):
            asansorler.append(None)
            continue
        t = _temiz(a, AVAN_AS_SAYISAL, f"{sira} NOLU ASANSÖR: ")
        asansorler.append(t if (t.get("kapasite") or t.get("Q_elle")) else None)
    sb_ham = v.get("sabitler")
    sb = {k: _sayi(x) for k, x in (sb_ham if isinstance(sb_ham, dict) else {}).items()}
    return {"ortak": ortak, "asansorler": asansorler, "sabitler": sb,
            "trafik": _trafik_koprusu(v.get("trafik"))}


def _trafik_koprusu(ham):
    """
    Avan tarafına gönderilen trafik özeti — dışarıdan gelen veriye güvenmeden
    yalnız beklenen alanları, sayıya çevirerek alır.
    """
    if not isinstance(ham, dict):
        return {}
    liste = []
    for a in _sozluk_listesi(ham.get("asansorler"))[:4]:
        liste.append({"P": _sayi(a.get("P")), "V": _sayi(a.get("V")),
                      "toplam_seyahat": _sayi(a.get("toplam_seyahat"))})
    if not liste:
        return {}
    return {"tip": ham.get("tip") if ham.get("tip") in ("tek", "coklu") else None,
            "N": _sayi(ham.get("N")), "bodrum": _sayi(ham.get("bodrum")),
            "h": _sayi(ham.get("h")), "adet": _sayi(ham.get("adet")),
            "asansorler": liste}


# ------------------------------------------------------------------ uçlar
@app.get("/", response_class=HTMLResponse)
def anasayfa():
    with open(os.path.join(KOK, "static", "index.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/api/secenekler")
def secenekler():
    return {
        "bina_tipleri": E_TAB.BINA_TIPLERI,
        "kapi_genislikleri": E_TAB.KAPI_GENISLIKLERI,
        "kapi_tipleri": E_TAB.KAPI_TIPLERI,
        "kapasiteler": E_TAB.GECERLI_KAPASITELER,
        "hizlar": E_TAB.GECERLI_HIZLAR,
        "nufus_kalemleri": list(E_TAB.TABLO_1.keys()),
        "tablo_1": E_TAB.TABLO_1,
        "kesitler": sorted(E_TAB.KABLO_IZ.keys()),
        "makine_tipleri": E_TAB.MAKINE_TIPLERI,
        "aski_oranlari": E_TAB.ASKI_ORANLARI,
        "sabit_b": E_AVAN.SABIT_B_VARSAYILAN,
        "sabit_b_yedek": list(E_AVAN.SABIT_B_YEDEK),
        "ofis_varsayilan": E_AVAN.OFIS_VARSAYILAN,
        "ofis_asansor_alanlari": list(E_AVAN.OFIS_ASANSOR_ALANLARI),
        "ofis_ortak_alanlari": list(E_AVAN.OFIS_ORTAK_ALANLARI),
        "motor_kademeleri": list(E_TAB.MOTOR_KADEMELERI),
        "sabit_a": E_AVAN.SABIT_A,
        "bugun": date.today().strftime("%d.%m.%Y"),
        "tablo_10": E_TAB.TABLO_10,
        "tablo_9": E_TAB.TABLO_9,
        "tablo_7": E_TAB.TABLO_7,
        "tablo_4": {str(k): v for k, v in E_TAB.TABLO_4.items()},
        "tablo_8": {str(k): v for k, v in E_TAB.TABLO_8.items()},
        "tablo_11": E_TAB.TABLO_11,
        "kablo_iz": {str(k): v for k, v in E_TAB.KABLO_IZ.items()},
        "ayd_sutun_aciklama": E_TAB.AYD_SUTUN_ACIKLAMA,
    }


# ------------------------------------------------- uygulama projesi: mukavemet
@app.get("/api/uygulama/alanlar")
def uygulama_alanlari():
    """Formun kendini üretmesi için girdi sözleşmesi.

    Mukavemet alanları + elektrik hesaplarının mukavemette KARŞILIĞI OLMAYAN
    alanları.  Ortak girdiler burada BİR KEZ geçer ( bkz. uygulama_girdi ).
    """
    veri = E_UGR.arayuz_alanlari()
    veri["ortak_kopru"] = [{"mukavemet": ad, "anahtar": a, "avan": av}
                           for ad, a, av in E_UGR.ORTAK_KOPRU]
    return veri


def _mukavemet_girdi(veri: dict):
    """Arayüzden gelen ham metinleri sözleşmenin beklediği türlere çevirir.

    Seçim alanları LİSTEDEKİ değere eşlenir:  arayüz her şeyi metin olarak
    yollar, oysa seçeneklerin çoğu sayıdır ( 800 · 1,6 · 370 ).  Eşleme
    burada yapılmazsa motorun doğrulaması "geçersiz seçim" der.
    """
    _BELIRSIZ.clear(); _RED.clear()
    v = (veri or {}).get("girdiler")
    v = v if isinstance(v, dict) else {}
    g = {}
    #  Elektrik hesaplarının ek alanları  ( kuyu genişliği · kesitler ·
    #  temel ölçüleri · makine dairesi ).  Onay kutusu mantıksal, geri kalanı
    #  serbest sayıdır;  boş bırakılabilir — hesap eksikliği kendisi bildirir.
    for anahtar, _et, _b2, tur2, _s2, _v2 in E_UGR.EK_ALANLAR:
        if anahtar not in v:
            continue
        ham = v[anahtar]
        if tur2 == "onay":
            g[anahtar] = ham if isinstance(ham, bool) else str(ham).lower() in (
                "1", "true", "evet", "on")
            continue
        if belirsiz_sayi_mi(ham):
            _BELIRSIZ.append(f"{_et} = {str(ham).strip()}")
        g[anahtar] = _sayi(ham)
    for anahtar, _h, etiket, _b, tur, secenekler, _var in E_MGR.ALANLAR:
        if tur == "hesap" or anahtar not in v:
            continue
        ham = v[anahtar]
        if tur == "liste":
            liste = []
            for x in (ham if isinstance(ham, list) else []):
                if x is None or str(x).strip() == "":
                    continue
                if belirsiz_sayi_mi(x):
                    _BELIRSIZ.append(f"{etiket}: {str(x).strip()}")
                liste.append(_sayi(x))
            g[anahtar] = liste
            continue
        if belirsiz_sayi_mi(ham):
            _BELIRSIZ.append(f"{etiket} = {str(ham).strip()}")
        if secenekler is None:
            g[anahtar] = _sayi(ham) if tur == "sayi" else ham
            continue
        #  Seçenek listesi:  önce birebir, sonra sayısal eşleşme aranır
        if ham in secenekler:
            g[anahtar] = ham
            continue
        sayi = _sayi(ham)
        esles = next((o for o in secenekler
                      if isinstance(o, (int, float)) and not isinstance(o, bool)
                      and sayi is not None and abs(o - sayi) < 1e-9), None)
        g[anahtar] = esles if esles is not None else (
            ham if str(ham).strip() != "" else None)
    #  Ofis standardı ( Sabitler sekmesi ) — elektrik ve topraklama hesapları
    #  buradan besleniyor;  avan tarafındaki ile aynı biçimde alınır.
    sb = (veri or {}).get("sabitler")
    g["_ofis"] = {k: _sayi(x) for k, x in sb.items()} if isinstance(sb, dict) else {}
    return g


@app.post("/api/uygulama")
def api_uygulama(veri: dict = Body(...)):
    """Uygulama projesinin tamamı — mukavemet + elektrik + topraklama."""
    try:
        g = _mukavemet_girdi(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"aktif": False, "hata": [belirsiz]}, status_code=200)
        s = E_UYG.hesapla(g)
        #  "_h" motorun Excel hücre haritasıdır — doğrulama testleri içindir,
        #  arayüzün işine yaramaz ve yanıtı gereksiz büyütür.
        s.pop("_h", None)
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"aktif": False, "hata": [f"HESAP HATASI: {e}"]},
                            status_code=200)


@app.post("/api/trafik")
def api_trafik(veri: dict = Body(...)):
    try:
        g = _trafik_girdi(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        s = E_TRF.hesapla(g)
        #  Avan sekmesi bu özeti geri gönderir; kapasite / hız / kuyu yüksekliği
        #  tutarsızlığı orada uyarı olarak görünür.
        s["avan_koprusu"] = E_TRF.trafik_ozeti(s)
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"hata": f"HESAP HATASI: {e}"}, status_code=200)


@app.post("/api/avan")
def api_avan(veri: dict = Body(...)):
    try:
        g = _avan_girdi(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        s = E_AVAN.hesapla(g)
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"hata": f"HESAP HATASI: {e}"}, status_code=200)


def _proje_kimligi(veri):
    """
    KAPAK SEKMESİNDEKİ PROJE KİMLİĞİ  →  indirilen dosyanın adı ve XLSX'in
    dosya özellikleri.

    Bu bağlanmadan önce her indirme "Asansor - Avan Hesaplari.xlsx" adıyla
    iniyordu:  aynı klasördeki iki projenin dosyaları birbirinden ayırt
    edilemiyor, ikincisi "(1)" olarak kaydediliyordu.  Pafta içeriği
    değişmez — proje adı yalnız KAPAK sayfasında yazılıdır.
    """
    k = veri.get("kapak") if isinstance(veri.get("kapak"), dict) else {}

    def _birlestir(*alanlar):
        return " ".join(str(k.get(x) or "").strip() for x in alanlar).strip()

    return {"proje_adi": str(k.get("project_title") or "").strip(),
            "isveren": str(k.get("owner") or k.get("contractor") or "").strip(),
            "pafta_no": str(k.get("sheet_no") or "").strip(),
            "tarih": "",
            "muhendis": _birlestir("elec_name", "elec_surname")
            or _birlestir("mech_name", "mech_surname")}


def _dosya_adi(proje, ek, uzanti):
    ad = (proje or {}).get("proje_adi") or "Asansor"
    ad = "".join(c for c in str(ad) if c.isalnum() or c in " -_")[:48].strip() or "Asansor"
    return f"{ad} - {ek}.{uzanti}"


def _indir(icerik: bytes, ad: str, tur: str):
    from urllib.parse import quote
    return Response(icerik, media_type=tur, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(ad)}"})


XLSX_TUR = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _uretilemedi(e: Exception):
    """
    Dosya üretilemediğinde JSON hata döndürür.  Arayüz Content-Type'a bakarak
    bunu bozuk bir dosya olarak indirmek yerine ekranda mesaj olarak gösterir.
    """
    ileti = str(e)
    if isinstance(e, FileNotFoundError) or "No such file" in ileti:
        ileti = ("Excel şablonu bulunamadı. XLSX çıktısı ofisin kendi Excel dosyasını "
                 "şablon olarak kullanır — 'templates' klasöründeki iki dosya yerinde "
                 "olmalıdır. (Ekrandaki hesap ve PDF çıktısı şablon olmadan da çalışır.)")
    return JSONResponse({"hata": f"DOSYA ÜRETİLEMEDİ — {ileti}"}, status_code=422)


@app.post("/api/indir/trafik-xlsx")
def indir_trafik_xlsx(veri: dict = Body(...)):
    try:
        g = _trafik_girdi(veri)
        #  Ekranda reddedilen bir girdiyle DOSYA ÜRETİLMEZ.  Belirsiz sayı
        #  yazımı ( "1.200" ) _sayi() tarafından boşa çevriliyor; denetim
        #  olmadan hücre boş kalıyor ve dosya eksik girdiyle teslim edilebilir
        #  hâlde çıkıyordu.  Ekran ile indirme aynı kapıdan geçmeli.
        belirsiz = _belirsiz_hata()          # ekran neyi reddediyorsa indirme de reddeder
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        #  HESAP HATALIYSA XLSX ÜRETİLMEZ.  PDF hatayı paftaya BASAR ( okunur bir
        #  belge çıkar ), ama Excel şablonu yalnız girdi hücrelerini alır:
        #  Python'a özgü denetimler ( ör. "durak adedi N+1 olmalıdır" ) şablonda
        #  yoktur, dolayısıyla ekranda reddedilen bir hesap dosyada SORUNSUZ
        #  görünür.  Ekran neyi reddediyorsa indirme de reddeder.
        _s = E_TRF.hesapla(g)
        if _s.get("hata"):
            return JSONResponse({"hata": _s["hata"]}, status_code=200)
        mod = _s.get("yol", "tek")                    # yöntemi veri belirler
        ek = "Trafik Hesabi (PAFTA)" if mod == "tek" else "Coklu Asansor Trafik (PAFTA-COKLU)"
        _p = _proje_kimligi(veri)
        return _indir(X_XLS.trafik_xlsx(mod, g, _p),
                      _dosya_adi(_p, ek, "xlsx"), XLSX_TUR)
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/trafik-pdf")
def indir_trafik_pdf(veri: dict = Body(...)):
    try:
        g = _trafik_girdi(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        s = E_TRF.hesapla(g)
        ek = "Trafik Hesabi" if s.get("yol") == "tek" else "Coklu Asansor Trafik"
        _p = _proje_kimligi(veri)
        return _indir(X_PDF.trafik_pdf(s, _p),
                      _dosya_adi(_p, ek, "pdf"), "application/pdf")
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.get("/api/sablon")
def sablon_durumu():
    """
    Şablon dosyalarının kimliği ve denetim sonucu.  Arayüz bunu açılışta
    sorar; yanlış / eski bir şablon konulmuşsa kullanıcı XLSX indirmeyi
    denemeden önce görür.
    """
    d = []
    for tur, yol, ad in (("trafik", X_XLS.TRAFIK_SABLON, "Trafik hesabı şablonu"),
                         ("avan", X_XLS.AVAN_SABLON, "Avan hesapları şablonu")):
        try:
            s = X_DEN.denetle(yol, tur)
        except Exception as e:                                # noqa: BLE001
            s = {"uygun": False, "dosya": os.path.basename(yol), "md5": None,
                 "sayfa_sayisi": 0, "hatalar": [f"Denetim yapılamadı: {e}"]}
        d.append({"tur": tur, "baslik": ad, **s})
    return {"uygun": all(x["uygun"] for x in d), "sablonlar": d}


@app.post("/api/indir/avan-xlsx")
def indir_avan_xlsx(veri: dict = Body(...)):
    try:
        #  Ofis varsayılanlarının girdiye yazılması avan_xlsx içinde yapılır.
        g = _avan_girdi(veri)
        belirsiz = _belirsiz_hata()          # ekran neyi reddediyorsa indirme de reddeder
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        #  Hesap hatalıysa XLSX üretilmez ( gerekçe: bkz. trafik-xlsx ).
        #  Avan tarafında hata, asansör kartının "aktif" olmamasıyla bildirilir.
        _s = E_AVAN.hesapla(g)
        _pasif = [a.get("uyari") for a in (_s.get("asansorler") or [])
                  if a and not a.get("aktif") and a.get("uyari")
                  and "TANIMLANMAMIŞ" not in str(a.get("uyari"))]
        if _s.get("hata") or _pasif:
            return JSONResponse({"hata": _s.get("hata") or _pasif[0]}, status_code=200)
        _p = _proje_kimligi(veri)
        return _indir(X_XLS.avan_xlsx(g, _p),
                      _dosya_adi(_p, "Avan Hesaplari", "xlsx"), XLSX_TUR)
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/avan-pdf")
def indir_avan_pdf(veri: dict = Body(...)):
    try:
        g = _avan_girdi(veri)
        belirsiz = _belirsiz_hata()          # ekran neyi reddediyorsa indirme de reddeder
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        s = E_AVAN.hesapla(g)
        _p = _proje_kimligi(veri)
        return _indir(X_PDF.avan_pdf(s, _p),
                      _dosya_adi(_p, "Avan Hesaplari", "pdf"), "application/pdf")
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/proje-dwg")
def indir_proje_dwg(veri: dict = Body(...)):
    """
    BÜTÜN PROJE  —  tek CAD dosyası.

    Kapak, ofis TİP PROJE FORMATININ antet hücresine; trafik paftası ve avan
    hesapları formatın büyük çerçevesine A4 boyutunda dizilir ( şablon yoksa
    yan yana serbest bir şerit ).  Geometri programın KENDİ PDF'lerinden
    okunur, bu yüzden CAD çıktısı paftanın birebir aynısıdır
    ( bkz. exports/dxf_export ).
    """
    if X_DXF is None:
        return JSONResponse(
            {"hata": "HESAP HATASI: CAD çıktısı için gereken kitaplıklar kurulu değil "
                     f"( {_DXF_HATA} ).  Programı kapatıp {_BASLATICI} dosyasını "
                     "yeniden çalıştırın; eksik kitaplıklar kendiliğinden kurulur."},
            status_code=200)
    try:
        paftalar = []
        kapak = veri.get("kapak") if isinstance(veri.get("kapak"), dict) else None
        if kapak:
            paftalar.append(("Kapak", X_KAPAK.pdf_bytes(kapak)))

        #  Trafik ve avan girdileri ayrı ayrı temizlenir; ikisi de belirsiz
        #  sayı denetiminden geçer — ekran neyi reddediyorsa CAD çıktısı da
        #  reddeder, yarım bir proje dosyası teslim edilmez.
        ham = veri.get("girdiler") if isinstance(veri.get("girdiler"), dict) else {}
        trafik_ham = ham.get("trafik")
        if isinstance(trafik_ham, dict):
            g = _trafik_girdi({"girdiler": trafik_ham})
            belirsiz = _belirsiz_hata()
            if belirsiz:
                return JSONResponse({"hata": belirsiz}, status_code=200)
            paftalar.append(("Trafik", X_PDF.trafik_pdf(E_TRF.hesapla(g))))

        avan_ham = ham.get("avan")
        if isinstance(avan_ham, dict):
            a = _avan_girdi({"girdiler": avan_ham})
            belirsiz = _belirsiz_hata()
            if belirsiz:
                return JSONResponse({"hata": belirsiz}, status_code=200)
            paftalar.append(("Avan", X_PDF.avan_pdf(E_AVAN.hesapla(a))))

        if not paftalar:
            return JSONResponse(
                {"hata": "HESAP HATASI: Projede hiç sayfa yok — önce kapağı doldurun "
                         "ya da trafik / avan hesabını yapın."}, status_code=200)

        ad = _dosya_adi(_proje_kimligi(veri), "Avan Projesi", "zip")
        paket, sebep, tasti = X_DXF.proje_paketi(paftalar, os.path.splitext(ad)[0])
        yanit = _indir(paket, ad, "application/zip")
        #  Kullanıcının BİLMESİ GEREKENLER başlıkta taşınır:
        #    DXF   → DWG üretilemedi, pakette yalnız DXF var ( sebebi OKUBENI'de )
        #    TASMA → paftalar formatın çerçevesine sığmadı, taşan sayfalar var
        notlar = ([ "DXF" ] if sebep else []) + ([ "TASMA" ] if tasti else [])
        if notlar:
            yanit.headers["X-Avan-Not"] = ",".join(notlar)
        return yanit
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


def _uygulama_sonucu(veri):
    """Girdileri okuyup uygulama hesabını koşturur.  ( sonuc , hata_yaniti )"""
    g = _mukavemet_girdi(veri)
    belirsiz = _belirsiz_hata()
    if belirsiz:
        return None, JSONResponse({"hata": belirsiz}, status_code=200)
    s = E_UYG.hesapla(g)
    if not s.get("aktif"):
        return None, JSONResponse(
            {"hata": "HESAP HATASI: " + "  ·  ".join(s.get("hata") or [])},
            status_code=200)
    return s, None


@app.post("/api/indir/uygulama-pdf")
def indir_uygulama_pdf(veri: dict = Body(...)):
    try:
        s, yanit = _uygulama_sonucu(veri)
        if yanit is not None:
            return yanit
        _p = _proje_kimligi(veri)
        return _indir(X_PDF.uygulama_pdf(s, _p),
                      _dosya_adi(_p, "Uygulama Projesi Hesaplari", "pdf"),
                      "application/pdf")
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/uygulama-xlsx")
def indir_uygulama_xlsx(veri: dict = Body(...)):
    """MUKAVEMET çalışma kitabı, kullanıcının girdileriyle doldurulmuş hâlde."""
    try:
        #  Hesap durduran girdiyle XLSX üretilmez:  formüller #YOK / #SAYI/0!
        #  dolu bir dosya teslim etmek, hatayı gizlemekten başka işe yaramaz.
        s, yanit = _uygulama_sonucu(veri)
        if yanit is not None:
            return yanit
        _p = _proje_kimligi(veri)
        return _indir(X_MXLS.mukavemet_xlsx(s["girdi"], _p),
                      _dosya_adi(_p, "Mukavemet Hesaplari", "xlsx"),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except FileNotFoundError as e:
        return JSONResponse({"hata": f"HESAP HATASI: {e}"}, status_code=200)
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/uygulama-dwg")
def indir_uygulama_dwg(veri: dict = Body(...)):
    """Uygulama projesi paftası — ofis tip proje formatına yerleştirilmiş CAD."""
    if X_DXF is None:
        return JSONResponse(
            {"hata": "HESAP HATASI: CAD çıktısı için gereken kitaplıklar kurulu değil "
                     f"( {_DXF_HATA} ).  Programı kapatıp {_BASLATICI} dosyasını "
                     "yeniden çalıştırın; eksik kitaplıklar kendiliğinden kurulur."},
            status_code=200)
    try:
        s, yanit = _uygulama_sonucu(veri)
        if yanit is not None:
            return yanit
        #  Uygulama projesinin kapağı MMO'nun AYRI kitabındadır — avan kapağı
        #  buraya basılmaz;  pakette yalnız hesap paftası olur.
        paftalar = [("Uygulama Projesi", X_PDF.uygulama_pdf(s))]
        ad = _dosya_adi(_proje_kimligi(veri), "Uygulama Projesi", "zip")
        paket, sebep, tasti = X_DXF.proje_paketi(paftalar, os.path.splitext(ad)[0])
        yanit = _indir(paket, ad, "application/zip")
        notlar = (["DXF"] if sebep else []) + (["TASMA"] if tasti else [])
        if notlar:
            yanit.headers["X-Avan-Not"] = ",".join(notlar)
        return yanit
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/kapak-pdf")
def indir_kapak_pdf(veri: dict = Body(...)):
    """Hesap motorundan bağımsız, tek sayfalık avan proje kapağı."""
    try:
        return _indir(X_KAPAK.pdf_bytes(veri.get("kapak")),
                      _dosya_adi(_proje_kimligi(veri), "Kapak", "pdf"),
                      "application/pdf")
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/xlsx-yukle")
def api_xlsx_yukle(veri: dict = Body(...)):
    """
    Programın ürettiği bir XLSX dosyasından girdileri geri yükler.

    Revizyon akışı:  proje klasöründeki Excel'i yükle → değişen girdiyi
    düzelt → güncel PDF ve XLSX'i yeniden indir.

    Dosya, arayüz tarafından base64 olarak gönderilir; böylece programın
    ek bir Python paketine ( multipart ) ihtiyacı olmaz.
    """
    import base64
    try:
        ham = (veri or {}).get("icerik") or ""
        if isinstance(ham, str) and "," in ham[:80] and ham.strip().startswith("data:"):
            ham = ham.split(",", 1)[1]              # data: URL başlığını at
        icerik = base64.b64decode(ham, validate=False)
    except Exception:                                         # noqa: BLE001
        return JSONResponse({"hata": "Dosya içeriği okunamadı."}, status_code=422)
    if len(icerik) < 1000:
        return JSONResponse({"hata": "Dosya boş veya çok küçük."}, status_code=422)
    if len(icerik) > 25 * 1024 * 1024:
        return JSONResponse({"hata": "Dosya çok büyük (en fazla 25 MB)."}, status_code=422)
    #  MUKAVEMET ÇALIŞMA KİTABI  ( uygulama projesi ).  Avan içe aktarıcısı
    #  bu dosyayı tanımaz;  önce o denetlenir, yoksa "tanınmayan dosya"
    #  hatası verirdi.  Dönen yapı avanınkiyle aynıdır — arayüzün uygula()
    #  işlevi ikisini de aynı yoldan işler.
    try:
        if X_MXLS.mukavemet_dosyasi_mi(icerik):
            g = X_MXLS.xlsx_oku(icerik)
            alanlar, durak = {}, []
            for anahtar, _h, _e, _b, tur, _s2, _v in E_MGR.ALANLAR:
                if anahtar not in g:
                    continue
                if tur == "liste":
                    durak = [str(x) for x in g[anahtar]]
                    continue
                alanlar[f"m_{anahtar}"] = g[anahtar]
            return JSONResponse({
                "tur": "mukavemet", "alanlar": alanlar, "muk_durak": durak,
                "proje": {}, "ozet": f"Mukavemet hesabı — {len(durak)} durak, "
                                     f"{len(alanlar)} girdi geri yüklendi."})
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"hata": f"Mukavemet dosyası okunamadı: {e}"},
                            status_code=422)
    try:
        return JSONResponse(X_IMP.xlsx_oku(icerik))
    except X_IMP.YuklemeHatasi as e:
        return JSONResponse({"hata": str(e)}, status_code=422)
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"hata": f"Dosya yüklenemedi: {e}"}, status_code=422)


@app.get("/api/saglik")
def saglik():
    return {"durum": "calisiyor", "surum": SURUM}


app.mount("/static", StaticFiles(directory=os.path.join(KOK, "static")), name="static")


# ------------------------------------------------------------------ başlat
def _bos_port(ilk, deneme=20):
    """İlk boş portu bulur — program zaten açıksa ikinci kopya çakışmasın."""
    import socket
    for p in range(ilk, ilk + deneme):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    return None


def _zaten_calisiyor(port):
    """Bu portta bizim programımız mı çalışıyor?"""
    try:
        import urllib.request
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/saglik", timeout=2) as c:
            return json.loads(c.read()).get("durum") == "calisiyor"
    except Exception:                                         # noqa: BLE001
        return False


def calistir():
    import uvicorn
    port = PORT
    if _zaten_calisiyor(port):
        url = f"http://127.0.0.1:{port}"
        print(f"\n  Program zaten açık  →  {url}\n  Tarayıcı yönlendiriliyor…\n")
        webbrowser.open(url)
        return
    if _bos_port(port, 1) is None:
        yeni = _bos_port(port + 1)
        if yeni is None:
            print(f"\n  {port} ve sonraki portlar dolu. Başka bir program bu portları "
                  "kullanıyor olabilir.\n  Bilgisayarı yeniden başlatıp tekrar deneyin.\n")
            return
        print(f"\n  {port} portu başka bir program tarafından kullanılıyor — "
              f"{yeni} portuna geçildi.")
        port = yeni

    url = f"http://127.0.0.1:{port}"
    print("\n" + "═" * 62)
    print(f"  ASANSÖR AVAN HESAPLAMA PROGRAMI   ·   sürüm {SURUM}")
    print("═" * 62)
    print(f"  Program çalışıyor :  {url}")
    print("  Tarayıcı kendiliğinden açılmazsa bu adresi yapıştırın.")
    print("  Kapatmak için bu pencerede  Ctrl + C  tuşlayın.")
    print("═" * 62 + "\n")
    threading.Timer(1.2, lambda: webbrowser.open(url)).start()
    try:
        uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")
    except KeyboardInterrupt:
        print("\n  Program kapatıldı.\n")


if __name__ == "__main__":
    calistir()
