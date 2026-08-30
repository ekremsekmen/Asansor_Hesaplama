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
from engine import tables as E_TAB           # noqa: E402
from engine import traffic as E_TRF          # noqa: E402
from exports import kapak_export as X_KAPAK  # noqa: E402
from exports import pdf_export as X_PDF      # noqa: E402
from exports import sablon_denetim as X_DEN
from exports import xlsx_export as X_XLS     # noqa: E402
from exports import xlsx_import as X_IMP     # noqa: E402

SURUM = "1.8"
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
_BELIRSIZ = []


def _temiz(d: dict, sayisal: tuple, on_ek: str = "") -> dict:
    out = dict(d or {})
    for k in sayisal:
        ham = out.get(k)
        if belirsiz_sayi_mi(ham):
            _BELIRSIZ.append(f"{on_ek}{k} = {str(ham).strip()}")
        out[k] = _sayi(ham)
    return out


def _belirsiz_hata():
    """Belirsiz yazılmış sayı varsa açık hata metni, yoksa None."""
    if not _BELIRSIZ:
        return None
    liste = "  ·  ".join(sorted(set(_BELIRSIZ))[:6])
    return ("HESAP HATASI: Belirsiz sayı yazımı  —  " + liste +
            "   ·   Bu yazımda binlik ayracı mı ondalık ayracı mı olduğu "
            "anlaşılmıyor ( Türkçede 1.200 = bin iki yüz, 1,200 = bir virgül iki; "
            "program ikisini de ondalık kabul ediyor ). Binlik ayracı KULLANMAYIN: "
            "bin iki yüz için 1200, bir virgül iki için 1,2 yazın.")

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


def _sozluk_listesi(x):
    """Yalnız sözlük öğelerini geçiren güvenli liste — bozuk gövdede çökmez."""
    if not isinstance(x, (list, tuple)):
        return []
    return [e for e in x if isinstance(e, dict)]


def _trafik_girdi(veri: dict):
    _BELIRSIZ.clear()
    veri = veri if isinstance(veri, dict) else {}
    mod = veri.get("mod") if veri.get("mod") in ("tek", "coklu") else "tek"
    ham = veri.get("girdiler")
    ham = ham if isinstance(ham, dict) else {}
    g = _temiz(ham, TRAFIK_SAYISAL)
    g["ek_nufus"] = [{"aciklama": s.get("aciklama"), "miktar": _sayi(s.get("miktar")),
                      "kalem": s.get("kalem")}
                     for s in _sozluk_listesi(ham.get("ek_nufus"))
                     if s.get("kalem") and _sayi(s.get("miktar")) is not None]
    if mod == "coklu":
        g["asansorler"] = [_temiz(a, ASANSOR_SAYISAL, f"ASANSÖR-{i}: ")
                           for i, a in enumerate(_sozluk_listesi(ham.get("asansorler")), 1)
                           if _sayi(a.get("P")) is not None][:4]
    return mod, g


def _avan_girdi(veri: dict):
    _BELIRSIZ.clear()
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


@app.post("/api/trafik")
def api_trafik(veri: dict = Body(...)):
    try:
        mod, g = _trafik_girdi(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        s = E_TRF.hesapla_coklu(g) if mod == "coklu" else E_TRF.hesapla_tek(g)
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
        mod, g = _trafik_girdi(veri)
        ek = "Trafik Hesabi (PAFTA)" if mod == "tek" else "Coklu Asansor Trafik (PAFTA-COKLU)"
        return _indir(X_XLS.trafik_xlsx(mod, g),
                      _dosya_adi(None, ek, "xlsx"), XLSX_TUR)
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/trafik-pdf")
def indir_trafik_pdf(veri: dict = Body(...)):
    try:
        mod, g = _trafik_girdi(veri)
        belirsiz = _belirsiz_hata()
        if belirsiz:
            return JSONResponse({"hata": belirsiz}, status_code=200)
        s = E_TRF.hesapla_coklu(g) if mod == "coklu" else E_TRF.hesapla_tek(g)
        ek = "Trafik Hesabi" if mod == "tek" else "Coklu Asansor Trafik"
        return _indir(X_PDF.trafik_pdf(s),
                      _dosya_adi(None, ek, "pdf"), "application/pdf")
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
        return _indir(X_XLS.avan_xlsx(_avan_girdi(veri)),
                      _dosya_adi(None, "Avan Hesaplari", "xlsx"), XLSX_TUR)
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/avan-pdf")
def indir_avan_pdf(veri: dict = Body(...)):
    try:
        s = E_AVAN.hesapla(_avan_girdi(veri))
        return _indir(X_PDF.avan_pdf(s),
                      _dosya_adi(None, "Avan Hesaplari", "pdf"), "application/pdf")
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


@app.post("/api/indir/kapak-pdf")
def indir_kapak_pdf(veri: dict = Body(...)):
    """Hesap motorundan bağımsız, tek sayfalık avan proje kapağı."""
    try:
        return _indir(X_KAPAK.pdf_bytes(veri.get("kapak")),
                      _dosya_adi(None, "Kapak", "pdf"), "application/pdf")
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
