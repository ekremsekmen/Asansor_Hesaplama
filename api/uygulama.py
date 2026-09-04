# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ UÇLARI

Mukavemet + elektrik + topraklama hesabı ve çıktıları.  Avandan bağımsızdır;
elektrik hesapları avan MOTORUNU çağırır ( engine/uygulama/hesap.py ), ama
uçlar ayrıdır.
"""
import json
import os

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from api.ortak import (_BELIRSIZ, _RED, _belirsiz_hata, _dosya_adi, _indir,
                       _proje_kimligi, _sayi, _uretilemedi, belirsiz_sayi_mi)
from engine.uygulama import girdi as E_UGR
from engine.uygulama import hesap as E_UYG
from engine.uygulama import mukavemet_girdi as E_MGR
from exports import mukavemet_xlsx as X_MXLS
from exports import pdf_export as X_PDF

try:
    from exports import dxf_export as X_DXF
    _DXF_HATA = None
except Exception as _e:                                   # noqa: BLE001
    X_DXF, _DXF_HATA = None, _e
_BASLATICI = "baslat.command" if os.name != "nt" else "baslat.bat"

router = APIRouter()

@router.get("/api/uygulama/alanlar")
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


@router.post("/api/uygulama")
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


@router.post("/api/indir/uygulama-pdf")
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


@router.post("/api/indir/uygulama-xlsx")
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


@router.post("/api/indir/uygulama-dwg")
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


