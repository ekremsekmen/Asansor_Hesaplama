# -*- coding: utf-8 -*-
"""
TEST 4  —  ÇIKTI BÜTÜNLÜĞÜ  (XLSX ve PDF)

Üretilen dosyalar gerçekten açılabiliyor mu, içinde Excel hata hücresi var mı,
doğru sayfaları taşıyor mu, PDF geçerli ve Türkçe karakterler yerinde mi?
"""
import os
import re
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl                                            # noqa: E402
from engine import avan as AV, traffic as TR               # noqa: E402
from exports import hucre_haritasi as H                    # noqa: E402
from exports import pdf_export as PE, xlsx_export as XE    # noqa: E402
from testler.ortak import Rapor, hata_hucresi_ara, yeniden_hesapla, soffice_yolu  # noqa: E402

# Geçici dosyalar sistemin temp klasörüne yazılır — proje klasörü kirlenmez
# ve silme izni kısıtlı makinelerde test takılmaz.
GECICI = os.path.join(tempfile.gettempdir(),
                      "avan_test_" + os.path.splitext(os.path.basename(__file__))[0])

PROJE = {"proje_adi": "Türkçe Şıkır Ğüzel Öİ Projesi", "isveren": "ÇAĞDAŞ İnşaat A.Ş.",
         "pafta_no": "EL-04", "tarih": "27.08.2026", "muhendis": "Ekrem Sekmen"}

GT = dict(bina_tipi="Konut", bina_yuksekligi=39.98, yapi_yuksekligi=43, N=11, h=3,
          hizli1=44, hizli2=3, P=10, kapi_genisligi=900, kapi_tipi="Merkezden Açılan Oto.")
GC = dict(bina_tipi="Konut", bina_yuksekligi=39.98, yapi_yuksekligi=43, N=11, h=3,
          hizli1=44, hizli2=3,
          asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
                      dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")])
ORT = dict(U=380, kappa=56, eps_max=3, temel_a=26.55, temel_b=16.4, beta=150,
           serit_L=58.5, cubuk_sayisi=4, mk_uzunluk=4200, mk_genislik=3100)
A1 = dict(tanim="İnsan", kapasite=10, V=1.6, eta=0.85, Hk=32.85, kuyu_genisligi=1800,
          kabin_boyu=1450, kabin_genisligi=1300, gr=17.91, Fmk=350, Fsh=100, Nsc=11,
          S1=6, L1=32.85, S2=6, L2=3, kablo_tipi="NHXMH FE180")
A2 = dict(A1, tanim="Sedye + Yük", kapasite=16, V=1.0, kuyu_genisligi=2650,
          kabin_boyu=1350, kabin_genisligi=2100)
AV_VERI = {"ortak": ORT, "asansorler": [A1, A2, A1, A2]}

TR_HARF = "ÇĞİÖŞÜçğıöşü"


def calistir():
    print("\n\033[1mTEST 4 — ÇIKTI BÜTÜNLÜĞÜ (XLSX ve PDF)\033[0m")
    r = Rapor("Çıktı bütünlüğü")
    shutil.rmtree(GECICI, ignore_errors=True)
    os.makedirs(GECICI, exist_ok=True)

    # ---------------------------------------------------------- XLSX
    dosyalar = {
        "tek": (XE.trafik_xlsx("tek", GT), ["HESAPLAMA", "PAFTA"], ["ÇOKLU ASANSÖR", "PAFTA-COKLU"], "PAFTA"),
        "coklu": (XE.trafik_xlsx("coklu", GC), ["ÇOKLU ASANSÖR", "PAFTA-COKLU"], ["HESAPLAMA", "PAFTA"], "PAFTA-COKLU"),
        "avan": (XE.avan_xlsx(AV_VERI),
                 ["GİRİŞ", "ÖZET", "1 NOLU ASANSÖR", "2 NOLU ASANSÖR", "3 NOLU ASANSÖR",
                  "4 NOLU ASANSÖR", "MK.DAİRESİ AYD.", "TOPRAKLAMA", "TABLOLAR", "SABİTLER"],
                 [], "ÖZET"),
    }
    for ad, (icerik, olmali, olmamali, aktif) in dosyalar.items():
        yol = os.path.join(GECICI, f"{ad}.xlsx")
        open(yol, "wb").write(icerik)
        r.kontrol(f"{ad}.xlsx ZIP imzası", icerik[:2] == b"PK")
        r.kontrol(f"{ad}.xlsx makul boyut", 20_000 < len(icerik) < 5_000_000, f"→ {len(icerik)} bayt")
        try:
            wb = openpyxl.load_workbook(yol)
        except Exception as e:                                   # noqa: BLE001
            r.kontrol(f"{ad}.xlsx açılabiliyor", False, f"→ {e}")
            continue
        r.kontrol(f"{ad}.xlsx açılabiliyor", True)
        for sh in olmali:
            r.kontrol(f"{ad}.xlsx '{sh}' sayfası var", sh in wb.sheetnames)
        for sh in olmamali:
            r.kontrol(f"{ad}.xlsx '{sh}' sayfası ÇIKARILMIŞ", sh not in wb.sheetnames)
        r.esit(f"{ad}.xlsx açılışta gelen sayfa", wb.active.title, aktif)
        r.kontrol(f"{ad}.xlsx açılışta yeniden hesaplanacak",
                  bool(getattr(wb.calculation, "fullCalcOnLoad", False)))
        # tanımlı adlarda kırık başvuru olmamalı
        kirik = [n for n, d in wb.defined_names.items() if "#REF" in str(d.value)]
        r.kontrol(f"{ad}.xlsx tanımlı adlar sağlam", not kirik, f"→ {kirik}")

    # yeniden hesaplandığında hata hücresi kalmamalı
    if soffice_yolu():
        cikis = os.path.join(GECICI, "hesaplandi")
        yeniden_hesapla([os.path.join(GECICI, f"{a}.xlsx") for a in dosyalar], cikis)
        for ad in dosyalar:
            y = os.path.join(cikis, f"{ad}.xlsx")
            if not os.path.exists(y):
                r.kontrol(f"{ad}.xlsx yeniden hesaplanabildi", False)
                continue
            hatalar = hata_hucresi_ara(y)
            r.kontrol(f"{ad}.xlsx hesap sonrası hata hücresi yok", not hatalar,
                      f"→ {hatalar[:4]}")
    else:
        r.atla("LibreOffice yok — XLSX yeniden hesaplama kontrolü atlandı")

    # ---------------------------------------------------------- PDF
    pdfler = {
        "tek": PE.trafik_pdf(TR.hesapla_tek(GT), PROJE),
        "coklu": PE.trafik_pdf(TR.hesapla_coklu(GC), PROJE),
        "avan": PE.avan_pdf(AV.hesapla(AV_VERI), PROJE),
        # hesap hatalı girdide de geçerli belge üretilmeli
        "hatali": PE.trafik_pdf(TR.hesapla_tek({"bina_tipi": "Konut"}), PROJE),
        "bos_avan": PE.avan_pdf(AV.hesapla({"ortak": {}, "asansorler": []}), PROJE),
        "projesiz": PE.trafik_pdf(TR.hesapla_tek(GT), None),
    }
    BEKLENEN_BASLIK = {"tek": "ASANSÖR TRAFİK HESABI",
                       "coklu": "ÇOKLU ASANSÖR TRAFİK HESABI",
                       "avan": "ASANSÖR AVAN PROJE HESAPLARI",
                       "hatali": "ASANSÖR TRAFİK HESABI",
                       "bos_avan": "ASANSÖR AVAN PROJE HESAPLARI",
                       "projesiz": "ASANSÖR TRAFİK HESABI"}
    try:
        import pypdfium2 as pdfium
    except ImportError:
        pdfium = None

    for ad, icerik in pdfler.items():
        yol = os.path.join(GECICI, f"{ad}.pdf")
        open(yol, "wb").write(icerik)
        r.kontrol(f"{ad}.pdf imzası", icerik[:4] == b"%PDF")
        r.kontrol(f"{ad}.pdf sonlandırılmış", b"%%EOF" in icerik[-2048:])
        r.kontrol(f"{ad}.pdf makul boyut", 5_000 < len(icerik) < 20_000_000,
                  f"→ {len(icerik)} bayt")
        if not pdfium:
            continue
        try:
            d = pdfium.PdfDocument(yol)
            sayfa = len(d)
        except Exception as e:                                   # noqa: BLE001
            r.kontrol(f"{ad}.pdf açılabiliyor", False, f"→ {e}")
            continue
        r.kontrol(f"{ad}.pdf açılabiliyor ({sayfa} sayfa)", sayfa >= 1)
        metinler = [d[i].get_textpage().get_text_range() for i in range(sayfa)]
        tam = "\n".join(metinler)
        # her sayfada üst şerit doğru belgeyi göstermeli
        for i, m in enumerate(metinler):
            ilk = m.split("\n")[0] if m else ""
            r.kontrol(f"{ad}.pdf s.{i+1} üst şerit doğru",
                      ilk.startswith(BEKLENEN_BASLIK[ad]), f"→ {ilk[:60]!r}")
        # Türkçe karakterler bozulmamalı
        r.kontrol(f"{ad}.pdf Türkçe karakterler yerinde",
                  any(h in tam for h in TR_HARF))
        r.kontrol(f"{ad}.pdf kırık karakter yok",
                  "�" not in tam and "□" not in tam)
        # sayfa numarası ve tarih alt bilgide olmalı
        r.kontrol(f"{ad}.pdf sayfa numarası var", re.search(r"Sayfa\s*\d+", tam) is not None)
        # başlık üstverisi
        try:
            import pypdf
            import warnings
            warnings.filterwarnings("ignore")
            m = pypdf.PdfReader(yol).metadata
            r.kontrol(f"{ad}.pdf üstveri başlığı doğru",
                      str(m.get("/Title", "")).startswith(BEKLENEN_BASLIK[ad]),
                      f"→ {m.get('/Title')!r}")
        except ImportError:
            pass

    # proje bilgisi antette görünmeli
    if pdfium:
        d = pdfium.PdfDocument(os.path.join(GECICI, "tek.pdf"))
        t = d[0].get_textpage().get_text_range()
        r.kontrol("pafta antedinde proje adı var", "Türkçe Şıkır" in t)
        r.kontrol("pafta antedinde işveren var", "ÇAĞDAŞ" in t)
        r.kontrol("imza kutusunda mühendis adı var",
                  "Ekrem Sekmen" in "\n".join(d[i].get_textpage().get_text_range()
                                              for i in range(len(d))))

    # ------------------------------------------------- v1.3 içerik kontrolleri
    #  Yeni büyüklükler paftaya gerçekten basılıyor mu?
    if pdfium:
        def _metin(icerik):
            import tempfile as _t
            y = os.path.join(GECICI, "_gecici_icerik.pdf")
            open(y, "wb").write(icerik)
            d = pdfium.PdfDocument(y)
            return "\n".join(d[i].get_textpage().get_text_range() for i in range(len(d)))

        m = _metin(PE.trafik_pdf(TR.hesapla_tek(dict(GT, bodrum=2)), PROJE))
        for beklenen in ("Bodrum durak adedi", "Toplam durak adedi",
                         "Toplam seyahat mesafesi", "H (Tablo-3)"):
            r.kontrol(f"tek pafta: '{beklenen}' basıldı", beklenen in m)
        m0 = _metin(PE.trafik_pdf(TR.hesapla_tek(GT), PROJE))
        r.kontrol("bodrumsuzda bodrum notu basılmıyor", "H (Tablo-3)" not in m0)
        #  ara değerli kapı ve erişilebilirlik uyarıları
        m = _metin(PE.trafik_pdf(TR.hesapla_tek(dict(GT, kapi_genisligi=1000)), PROJE))
        r.kontrol("1000 mm ara değer uyarısı paftada", "enterpolasyon" in m)
        m = _metin(PE.trafik_pdf(TR.hesapla_tek(dict(GT, P=6, kapi_genisligi=700)), PROJE))
        r.kontrol("erişilebilirlik uyarısı paftada", "81-70" in m)
        r.kontrol("dış değerleme uyarısı paftada", "değerleme" in m)
        #  kamu binası varsayımları
        m = _metin(PE.trafik_pdf(TR.hesapla_tek(dict(GT, bina_tipi="Kamu Binaları")), PROJE))
        r.kontrol("kamu %k varsayımı paftada", "Tablo-9" in m and "MERKEZ" in m.upper())
        #  çoklu: asansör bazında bodrum ve imalatçı süresi
        m = _metin(PE.trafik_pdf(TR.hesapla_coklu(dict(
            GC, bodrum=2,
            asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik",
                             manuel_ta=2.9)])), PROJE))
        r.kontrol("çoklu paftada bodrum satırı", "Bodrum durak adedi" in m)
        r.kontrol("çoklu paftada imalatçı süresi uyarısı", "imalatçı verisiyle" in m)
        #  avan: asansör bazında askı/denge ve tutarlılık uyarısı
        _t = TR.hesapla_tek(dict(GT, bodrum=1))
        _av = AV.hesapla({"ortak": ORT,
                          "asansorler": [dict(A1, i_palanga=1, q_denge=0.4)],
                          "trafik": TR.trafik_ozeti(_t)})
        m = _metin(PE.avan_pdf(_av, PROJE))
        r.kontrol("avan paftasında asansör bazı kaynağı", "bazında" in m)
        r.kontrol("avan paftasında tutarlılık uyarısı", "NOLU ASANSÖR:" in m)

    # ---------------------------------------------------------- büyük/uç durumlar
    buyuk = dict(GC, asansorler=[dict(P=25, kapi_genisligi=1300,
                                      kapi_tipi="Merkezden Açılan Oto.") for _ in range(4)])
    b = PE.trafik_pdf(TR.hesapla_coklu(buyuk), PROJE)
    r.kontrol("4 asansörlü çoklu PDF üretildi", b[:4] == b"%PDF" and len(b) > 10_000)
    uzun = dict(PROJE, proje_adi="A" * 300, isveren="B" * 300)
    b = PE.trafik_pdf(TR.hesapla_tek(GT), uzun)
    r.kontrol("çok uzun proje adı PDF'i bozmadı", b[:4] == b"%PDF")
    x = XE.trafik_xlsx("tek", dict(GT, ek_nufus=[
        {"aciklama": "Kalem " + str(i), "miktar": 10, "kalem": "KONUT — Diğer oda"}
        for i in range(30)]))
    r.kontrol("30 ek nüfus satırı XLSX'i bozmadı", x[:2] == b"PK")

    # ---------------------------------------------------------- şablon eksikse
    #  Hesap ve PDF şablonsuz da çalışmalı; XLSX üretilemez ama kullanıcı
    #  bozuk bir dosya indirmemeli — anlaşılır hata almalı.
    #
    #  ÖNEMLİ: bu kontrol gerçek şablon dosyalarına DOKUNMAZ.  Yalnız modülün
    #  yol değişkenleri geçici olarak var olmayan bir dosyayı gösterir; test
    #  bitince eski değerlerine döner.  Böylece silme izni kısıtlı makinelerde
    #  de güvenle çalışır.
    yok = os.path.join(tempfile.gettempdir(), "avan_olmayan_sablon.xlsx")
    eski_trafik, eski_avan = XE.TRAFIK_SABLON, XE.AVAN_SABLON
    XE.TRAFIK_SABLON = XE.AVAN_SABLON = yok
    try:
        s2 = TR.hesapla_tek(GT)
        r.kontrol("şablonsuz hesap çalışıyor", s2.get("hata") is None and s2["ozet"]["TR"] > 0)
        p2 = PE.trafik_pdf(s2, PROJE)
        r.kontrol("şablonsuz PDF üretiliyor", p2[:4] == b"%PDF" and len(p2) > 10_000)
        p3 = PE.avan_pdf(AV.hesapla(AV_VERI), PROJE)
        r.kontrol("şablonsuz avan PDF üretiliyor", p3[:4] == b"%PDF")
        for ad, fn in (("trafik", lambda: XE.trafik_xlsx("tek", GT)),
                       ("avan", lambda: XE.avan_xlsx(AV_VERI))):
            hata_alindi = False
            try:
                fn()
            except Exception:                                # noqa: BLE001
                hata_alindi = True
            r.kontrol(f"şablonsuz {ad} XLSX açıkça hata veriyor "
                      "(sessizce bozuk dosya değil)", hata_alindi)
    finally:
        XE.TRAFIK_SABLON, XE.AVAN_SABLON = eski_trafik, eski_avan
    r.kontrol("şablon dosyaları yerinde ve okunabilir",
              os.path.isfile(XE.TRAFIK_SABLON) and os.path.isfile(XE.AVAN_SABLON)
              and os.path.getsize(XE.TRAFIK_SABLON) > 10_000
              and os.path.getsize(XE.AVAN_SABLON) > 10_000)
    r.kontrol("şablonla XLSX yeniden üretilebiliyor",
              XE.trafik_xlsx("tek", GT)[:2] == b"PK")

    # ------------------------------------------------ YANLIŞ / ESKİ ŞABLON
    #  En sinsi hata: templates/ klasörüne yanlış ya da eski bir Excel konursa
    #  program yine dosya üretir, hesap doğru olduğu için ekranda hiçbir
    #  belirti çıkmaz, hata yalnız teslim edilen paftada görünür.
    #
    #  ÖNEMLİ: aşağıdaki senaryolar gerçek şablonlara DOKUNMAZ — geçici bir
    #  klasöre KOPYALANIR, kopyalar bozulur ve modülün yol değişkenleri
    #  geçici olarak oraya çevrilir.
    import openpyxl as _op
    from exports import sablon_denetim as SD

    r.kontrol("gerçek trafik şablonu denetimden geçiyor",
              SD.denetle(XE.TRAFIK_SABLON, "trafik", onbellek=False)["uygun"])
    r.kontrol("gerçek avan şablonu denetimden geçiyor",
              SD.denetle(XE.AVAN_SABLON, "avan", onbellek=False)["uygun"])
    r.kontrol("denetim parmak izi ( md5 ) veriyor",
              len(SD.denetle(XE.AVAN_SABLON, "avan", onbellek=False)["md5"] or "") == 32)

    _D = tempfile.mkdtemp(prefix="avan_sablon_")

    def _bozuk(kaynak, degisiklikler):
        """Şablonun KOPYASINI bozar, yolunu döndürür."""
        hedef = os.path.join(_D, "s%d.xlsx" % (len(os.listdir(_D)) + 1))
        shutil.copy(kaynak, hedef)
        wb = _op.load_workbook(hedef)
        for sayfa, adres, deger in degisiklikler:
            wb[sayfa][adres] = deger
        wb.save(hedef)
        return hedef

    #  1) ESKİ trafik şablonu — Tablo-4'te 1000 mm satırı, Tablo-8'de 700 mm
    #     sütunu v1.3'te eklenmişti; eski dosyada yoktur.
    _eski = _bozuk(XE.TRAFIK_SABLON, [("TABLO-4", "A7", 1100),
                                      ("TABLO-8", "B1", 800)])
    _s = SD.denetle(_eski, "trafik", onbellek=False)
    r.kontrol("eski trafik şablonu yakalanıyor", _s["uygun"] is False)
    r.kontrol("eski şablon hatası TABLO-4'ü gösteriyor",
              any("TABLO-4" in h for h in _s["hatalar"]))
    r.kontrol("eski şablon hatası TABLO-8'i gösteriyor",
              any("TABLO-8" in h for h in _s["hatalar"]))

    #  2) Tablo DEĞERİ kaymış avan şablonu ( Tablo-11 boş kabin kütlesi )
    _deger = _bozuk(XE.AVAN_SABLON, [("TABLOLAR", "B75", 1150)])
    _s = SD.denetle(_deger, "avan", onbellek=False)
    r.kontrol("tablo değeri kaymış avan şablonu yakalanıyor", _s["uygun"] is False)
    r.kontrol("hata hangi hücre olduğunu söylüyor",
              any("TABLOLAR!B75" in h for h in _s["hatalar"]))

    #  3) YANLIŞ DOSYA — avan şablonu trafik yerine konmuş
    _s = SD.denetle(XE.AVAN_SABLON, "trafik", onbellek=False)
    r.kontrol("yanlış dosya ( avan → trafik ) yakalanıyor", _s["uygun"] is False)
    r.kontrol("eksik sayfa olarak bildiriliyor",
              any("Eksik sayfa" in h for h in _s["hatalar"]))

    #  4) Excel bile olmayan dosya
    _degil = os.path.join(_D, "degil.xlsx")
    open(_degil, "w", encoding="utf-8").write("bu bir excel değil")
    _s = SD.denetle(_degil, "avan", onbellek=False)
    r.kontrol("Excel olmayan dosya yakalanıyor", _s["uygun"] is False)

    #  5) Girdi hücresi BİRLEŞTİRİLMİŞ alana düşerse — yazılan değer kaybolur
    _bir = os.path.join(_D, "birlesik.xlsx")
    shutil.copy(XE.AVAN_SABLON, _bir)
    _wb = _op.load_workbook(_bir)
    _wb[H.AVAN_SAYFA].merge_cells("C23:C24")     # kapasite hücresini yut
    _wb.save(_bir)
    _s = SD.denetle(_bir, "avan", onbellek=False)
    r.kontrol("birleştirilmiş alana düşen girdi hücresi yakalanıyor",
              _s["uygun"] is False
              and any("birleştirilmiş" in h for h in _s["hatalar"]))

    #  6) DENETİMDEN GEÇMEYEN ŞABLONLA XLSX ÜRETİLMEZ
    _eski_t, _eski_a = XE.TRAFIK_SABLON, XE.AVAN_SABLON
    XE.TRAFIK_SABLON, XE.AVAN_SABLON = _eski, _deger
    try:
        for ad, fn in (("trafik", lambda: XE.trafik_xlsx("tek", GT)),
                       ("avan", lambda: XE.avan_xlsx(AV_VERI))):
            _mesaj = ""
            try:
                fn()
            except SD.SablonHatasi as e:
                _mesaj = str(e)
            except Exception as e:                           # noqa: BLE001
                _mesaj = "BEKLENMEYEN: " + type(e).__name__
            r.kontrol(f"bozuk şablonla {ad} XLSX ÜRETİLMİYOR",
                      "ŞABLON UYUŞMUYOR" in _mesaj, f"→ {_mesaj[:70]}")
    finally:
        XE.TRAFIK_SABLON, XE.AVAN_SABLON = _eski_t, _eski_a

    #  Gerçek şablonlar bozulmadı mı — testin kendisi zarar vermemeli
    r.kontrol("gerçek trafik şablonu hâlâ uygun",
              SD.denetle(XE.TRAFIK_SABLON, "trafik", onbellek=False)["uygun"])
    r.kontrol("gerçek avan şablonu hâlâ uygun",
              SD.denetle(XE.AVAN_SABLON, "avan", onbellek=False)["uygun"])
    r.kontrol("doğru şablonla XLSX yine üretiliyor",
              XE.avan_xlsx(AV_VERI)[:2] == b"PK")

    shutil.rmtree(GECICI, ignore_errors=True)
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
