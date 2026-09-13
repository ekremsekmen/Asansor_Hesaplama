# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ UÇLARI

Mukavemet + elektrik + topraklama hesabı ve çıktıları.  Avandan bağımsızdır;
elektrik hesapları avan MOTORUNU çağırır ( engine/uygulama/hesap.py ), ama
uçlar ayrıdır.
"""
import io
import json
import os
import zipfile

from fastapi import APIRouter, Body
from fastapi.responses import JSONResponse

from api.ortak import (PAKET_NOT_KITAP, _BELIRSIZ, _RED, _belirsiz_hata,
                       _dosya_adi, _indir, _paket_ekleri, _proje_kimligi, _sayi,
                       _uretilemedi, _uretilemeyen_dosya_notu, belirsiz_sayi_mi)
from engine.uygulama import girdi as E_UGR
from engine.uygulama import sabitler as E_US
from engine.uygulama import tablolar_gorunum as E_UTB
from engine.uygulama import hesap as E_UYG
from engine.uygulama import mukavemet_girdi as E_MGR
from exports import mukavemet_xlsx as X_MXLS
from exports import kapak_export as X_KAPAK
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
    #  UYGULAMANIN KENDİ OFİS STANDARDI  —  avanınkinden ayrıdır.
    #  Ekran bu listeden kurulur;  avanın MMO/697 kuvvet sabitleri burada
    #  YOKTUR, uygulamanın mukavemet kabulleri ( σem · k1 · paylar ) ise
    #  yalnız burada vardır.
    veri["sabitler"] = {
        "varsayilan": E_US.VARSAYILAN,
        "metin": list(E_US.METIN),
        "gruplar": [{"baslik": b, "aciklama": a, "alanlar": list(al)}
                    for b, a, al in E_US.GRUPLAR],
        "etiket": {k: list(v) for k, v in E_US.ETIKET.items()},
    }
    #  Tablolar sekmesi:  uygulamanın kendi tabloları  ( ray · NPU · halat ·
    #  ω · kabin alanı … ).  Bunlar bugüne kadar yalnız motorun içindeydi,
    #  ekranda görünmüyordu — uygulama yapan mühendis kullandığı ray
    #  tablosuna bakamıyordu.
    veri["tablolar"] = E_UTB.arayuz_tablolari()
    #  Çoklu projede asansöre özel OLMAYAN alanlar — arayüz bunları asansör
    #  formunun dışında bir kez sorar ve asansörden asansöre taşımaz.
    veri["proje_geneli"] = list(E_UGR.PROJE_GENELI_ALANLAR)
    veri["asansor_azami"] = E_UYG.ASANSOR_AZAMI
    return veri


def _mukavemet_girdi(veri: dict):
    """Arayüzden gelen ham metinleri sözleşmenin beklediği türlere çevirir.

    Seçim alanları LİSTEDEKİ değere eşlenir:  arayüz her şeyi metin olarak
    yollar, oysa seçeneklerin çoğu sayıdır ( 800 · 1,6 · 370 ).  Eşleme
    burada yapılmazsa motorun doğrulaması "geçersiz seçim" der.
    """
    _BELIRSIZ.clear(); _RED.clear()
    return _girdi_coz((veri or {}).get("girdiler"), veri)


def _girdi_coz(v, veri):
    """Tek asansörün ham alanlarını türlerine çevirir.

    _BELIRSIZ / _RED KASITLI OLARAK TEMİZLENMEZ:  çoklu projede her asansör
    ayrı çağrılır ve belirsiz girdiler hepsinden TOPLANMALIDIR — temizlik
    çağıranın işidir ( bkz. _asansor_girdileri ).
    """
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
            # Boş kütle tablodan doldurulabilir; bozuk giriş boş sayılamaz.
            if (anahtar == "kabin_agirligi" and g[anahtar] is None
                    and ham is not None and str(ham).strip()):
                g[anahtar] = ham
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
    #  METİN ALANLARI SAYIYA ÇEVRİLMEZ.  Hepsine _sayi() uygulanıyordu;
    #  kablo tipine "NYY" yazınca None'a düşüyor ve sessizce varsayılan
    #  ( NHXMH FE180 ) kullanılıyordu.  Belirsiz yazımlar ( "1.200" ) da
    #  uyarısız varsayılana düşüyordu — artık bildiriliyor.
    sb = (veri or {}).get("sabitler")
    ofis = {}
    if isinstance(sb, dict):
        for k, ham in sb.items():
            if k in E_US.METIN:
                metin = str(ham).strip()
                if metin:
                    ofis[k] = metin
                continue
            if belirsiz_sayi_mi(ham):
                _BELIRSIZ.append(f"{E_US.ETIKET.get(k, (k,))[0]} = {str(ham).strip()}")
            d = _sayi(ham)
            if d is not None:
                ofis[k] = d
    g["_ofis"] = ofis
    return g


PROJE_GENELI_ALANLAR = E_UGR.PROJE_GENELI_ALANLAR


def _asansor_girdileri(veri):
    """Arayüzden gelen isteği ( 1 - 4 asansör ) çözer.

    Döner:  ( [ asansör girdi sözlükleri ] , ortak )

    GERİYE DÖNÜK:  "asansorler" yoksa eski tek asansörlük "girdiler" alanı
    kullanılır — kayıtlı eski projeler ve eski istekler çalışmaya devam eder.
    """
    _BELIRSIZ.clear(); _RED.clear()
    veri = veri or {}
    ham = veri.get("asansorler")
    if not isinstance(ham, list) or not ham:
        ham = [veri.get("girdiler")]
    ham = [x for x in ham if isinstance(x, dict)][:E_UYG.ASANSOR_AZAMI] or [{}]

    #  Proje geneli alanlar:  ayrı gönderilmişse oradan, yoksa İLK asansörün
    #  girdisinden ( eski tek asansörlük istekler bunları orada taşıyor ).
    pg_ham = veri.get("proje_geneli")
    if not isinstance(pg_ham, dict):
        pg_ham = {k: ham[0][k] for k in PROJE_GENELI_ALANLAR if k in ham[0]}
    ortak = {k: v for k, v in _girdi_coz(pg_ham, veri).items()
             if k in PROJE_GENELI_ALANLAR or k == "_ofis"}
    return [_girdi_coz(x, veri) for x in ham], ortak


def _coklu_sonuc(veri):
    """Çoklu uygulama hesabı.  ( sonuc , hata_yaniti )"""
    asansorler, ortak = _asansor_girdileri(veri)
    belirsiz = _belirsiz_hata()
    if belirsiz:
        return None, JSONResponse({"aktif": False, "hata": [belirsiz]},
                                  status_code=200)
    s = E_UYG.hesapla_coklu(asansorler, ortak)
    if not s.get("aktif"):
        return None, JSONResponse(
            {"aktif": False,
             "hata": s.get("hata") or ["HESAP HATASI"]}, status_code=200)
    return s, None


@router.post("/api/uygulama/coklu")
def api_uygulama_coklu(veri: dict = Body(...)):
    """1 - 4 asansörlük uygulama projesi."""
    try:
        s, yanit = _coklu_sonuc(veri)
        if yanit is not None:
            return yanit
        for a in s.get("asansorler") or []:
            a.pop("_h", None)          # Excel hücre haritası arayüze gerekmez
        return JSONResponse(json.loads(json.dumps(s, default=str)))
    except Exception as e:                                    # noqa: BLE001
        return JSONResponse({"aktif": False, "hata": [f"HESAP HATASI: {e}"]},
                            status_code=200)


@router.post("/api/indir/uygulama-pdf")
def indir_uygulama_pdf(veri: dict = Body(...)):
    try:
        _p = _proje_kimligi(veri)
        s, yanit = _coklu_sonuc(veri)
        if yanit is not None:
            return yanit
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
        _p = _proje_kimligi(veri)
        #  MUKAVEMET ÇALIŞMA KİTABI TEK ASANSÖRLÜKTÜR.  Şablonda tek sayfa
        #  takımı vardır ( 'Veri Girişi' · '11-Muk. Hesapları' … ) ve formüller
        #  sayfa adlarına bağlıdır;  sayfa çoğaltmak her çapraz atfı yeniden
        #  yazmayı gerektirirdi.  Çoklu projede bu yüzden ASANSÖR BAŞINA AYRI
        #  KİTAP üretilir ve hepsi tek ZIP'te verilir.
        s, yanit = _coklu_sonuc(veri)
        if yanit is not None:
            return yanit
        #  HESAP TEK YOLDAN GEÇTİ;  adede göre değişen yalnız PAKETLEMEDİR.
        if s["adet"] > 1:
            ad = _dosya_adi(_p, "Mukavemet Hesaplari", "zip")
            paket = io.BytesIO()
            with zipfile.ZipFile(paket, "w", zipfile.ZIP_DEFLATED) as z:
                for k in _asansor_kitaplari(s, _p):
                    z.writestr(k[0], k[1])
            return _indir(paket.getvalue(), ad, "application/zip")
        return _indir(X_MXLS.mukavemet_xlsx(s["asansorler"][0]["girdi"], _p),
                      _dosya_adi(_p, "Mukavemet Hesaplari", "xlsx"),
                      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    except FileNotFoundError as e:
        return JSONResponse({"hata": f"HESAP HATASI: {e}"}, status_code=200)
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


def _asansor_kitaplari(s, proje):
    """Çoklu projede asansör başına mukavemet çalışma kitabı.

    Döner:  [ ( dosya adı , içerik ) … ].

    EKSİK KİTAP SESSİZCE ATLANAMAZ.  Bir asansörün kitabı üretilemediğinde
    eskiden yalnız ``continue`` vardı:  kullanıcı iki asansörlük bir projede
    tek kitaplı — hatta boş — bir ZIP indiriyor ve eksiğin farkına
    varmıyordu.  Üretilemeyen asansörler artık paketin İÇİNE konan bir
    metin dosyasında adıyla ve sebebiyle yazılır;  paket yine çıkar ama
    eksik görünür olur.
    """
    kitaplar, eksikler = [], []
    for a in s.get("asansorler") or []:
        if not a.get("aktif"):
            eksikler.append(f"{a.get('no')} - {a.get('tanim') or ''}:  "
                            "asansör hesaplanamadı ( girdiler eksik ya da geçersiz )")
            continue
        etiket = _dosya_parcasi(f"{a.get('no')} - {a.get('tanim') or ''}")
        try:
            kitaplar.append((f"Mukavemet Hesaplari - {etiket}.xlsx",
                             X_MXLS.mukavemet_xlsx(a["girdi"], proje)))
        except Exception as e:                                # noqa: BLE001
            eksikler.append(f"{etiket}:  {e}")
    if eksikler:
        kitaplar.append(_uretilemeyen_notu(eksikler))
    return kitaplar


def _uretilemeyen_notu(eksikler):
    """Pakete konan "neyin eksik olduğu" dosyası  →  ( ad , içerik ).

    Çoklu ve tekli paket AYNI bildirimi kullanır;  eskiden tekli pakette
    kitap üretilemezse ``except Exception: pass`` vardı ve kullanıcı kitapsız
    bir ZIP indirip farkına varmıyordu.
    """
    return _uretilemeyen_dosya_notu(
        eksikler, dosya="URETILEMEYEN ASANSORLER.txt",
        aciklama="Aşağıdaki asansörlerin mukavemet çalışma kitabı üretilemedi.")


def _dosya_parcasi(metin):
    """Dosya adında kullanılabilir hâle getirir."""
    ad = "".join(c if (c.isalnum() or c in " -_") else "-" for c in str(metin))
    return " ".join(ad.split()).strip(" -") or "asansor"


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
        _p = _proje_kimligi(veri)
        s, yanit = _coklu_sonuc(veri)
        if yanit is not None:
            return yanit
        paftalar = []
        #  KAPAK.  Uygulama projesinin kapağı MMO'nun ayrı kitabındadır;  ama
        #  paket bir teslim dosyasıdır ve kapaksız gitmesi için sebep yok —
        #  kapak alanları doldurulmuşsa pakete de girer.
        kapak = veri.get("kapak_sayfasi")
        if isinstance(kapak, dict) and any(str(x).strip() for x in kapak.values()):
            paftalar.append(("Kapak", X_KAPAK.pdf_bytes(kapak)))
        paftalar.append(("Uygulama Projesi", X_PDF.uygulama_pdf(s)))
        ad = _dosya_adi(_p, "Uygulama Projesi", "zip")
        #  Pakete çalışma kitabı ve PROJE DOSYASI da girer:  teslim paketi ile
        #  geri dönüş noktası aynı arşivde dursun.  ÇOKLU PROJEDE ASANSÖR
        #  BAŞINA AYRI KİTAP girer — mukavemet şablonu tek asansörlüktür.
        ekler = list(_paket_ekleri(veri, "uygulama"))
        if s["adet"] > 1:
            ekler += _asansor_kitaplari(s, _p)
        else:
            #  Kitap üretilemezse paket yine çıkar — ama EKSİK SÖYLENİR.
            _tek = s["asansorler"][0]
            try:
                ekler.append((os.path.splitext(ad)[0] + ".xlsx",
                              X_MXLS.mukavemet_xlsx(_tek["girdi"], _p)))
            except Exception as e:                            # noqa: BLE001
                ekler.append(_uretilemeyen_notu(
                    [f"{_tek.get('no')} - {_tek.get('tanim') or ''}:  {e}"]))
        paket, sebep, tasti = X_DXF.proje_paketi(
            paftalar, os.path.splitext(ad)[0], ekler)
        yanit = _indir(paket, ad, "application/zip")
        notlar = ((["DXF"] if sebep else []) + (["TASMA"] if tasti else [])
                  + ([PAKET_NOT_KITAP] if any(a == "URETILEMEYEN ASANSORLER.txt"
                                              for a, _ in ekler) else []))
        if notlar:
            yanit.headers["X-Avan-Not"] = ",".join(notlar)
        return yanit
    except Exception as e:                                    # noqa: BLE001
        return _uretilemedi(e)


