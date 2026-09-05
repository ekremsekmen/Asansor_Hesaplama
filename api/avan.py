# -*- coding: utf-8 -*-
"""
AVAN PROJE UÇLARI

Trafik hesabı, avan hesapları, proje kapağı ve bunların XLSX / PDF / CAD
çıktıları.  Uygulama projesinden bağımsızdır.
"""
import json
import os
from datetime import date

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from api.ortak import (KOK, _BELIRSIZ, _RED, _belirsiz_hata, _dosya_adi,
                       _indir, _paket_ekleri, _proje_kimligi, _sayi,
                       _sozluk_listesi, _temiz, _uretilemedi, belirsiz_sayi_mi)
from engine.avan import hesap as E_AVAN
from engine.avan import tablolar as E_TAB
from engine.avan import trafik as E_TRF
from exports import kapak_export as X_KAPAK
from exports import pdf_export as X_PDF
from exports import sablon_denetim as X_DEN
from exports import xlsx_export as X_XLS

try:
    from exports import dxf_export as X_DXF
    _DXF_HATA = None
except Exception as _e:                                   # noqa: BLE001
    X_DXF, _DXF_HATA = None, _e
_BASLATICI = "baslat.command" if os.name != "nt" else "baslat.bat"

router = APIRouter()

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

XLSX_TUR = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

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
@router.get("/api/secenekler")
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
@router.post("/api/trafik")
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


@router.post("/api/avan")
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


@router.post("/api/indir/trafik-xlsx")
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


@router.post("/api/indir/trafik-pdf")
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


@router.get("/api/sablon")
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


@router.post("/api/indir/avan-xlsx")
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


@router.post("/api/indir/avan-pdf")
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


@router.post("/api/indir/proje-dwg")
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
        #  Pakete ÇALIŞMA KİTAPLARI ve PROJE DOSYASI da girer:  teslim paketi
        #  ile geri dönüş noktası aynı arşivde dursun.
        kok = os.path.splitext(ad)[0]
        ekler = list(_paket_ekleri(veri, "avan"))
        if isinstance(trafik_ham, dict):
            try:
                _t = E_TRF.hesapla(g)
                if not _t.get("hata"):
                    ekler.append((f"{kok} - Trafik.xlsx",
                                  X_XLS.trafik_xlsx(_t.get("yol", "tek"), g,
                                                    _proje_kimligi(veri))))
            except Exception:                                 # noqa: BLE001
                pass          # şablon yoksa paket yine çıkar, kitap olmaz
        if isinstance(avan_ham, dict):
            try:
                ekler.append((f"{kok} - Avan.xlsx",
                              X_XLS.avan_xlsx(a, _proje_kimligi(veri))))
            except Exception:                                 # noqa: BLE001
                pass
        paket, sebep, tasti = X_DXF.proje_paketi(paftalar, kok, ekler)
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


@router.post("/api/indir/kapak-pdf")
def indir_kapak_pdf(veri: dict = Body(...)):
    """Hesap motorundan bağımsız, tek sayfalık avan proje kapağı."""
    try:
        return _indir(X_KAPAK.pdf_bytes(veri.get("kapak")),
                      _dosya_adi(_proje_kimligi(veri), "Kapak", "pdf"),
                      "application/pdf")
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


