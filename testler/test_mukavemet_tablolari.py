# -*- coding: utf-8 -*-
"""
TEST 8  —  MUKAVEMET TABLOLARI + GİRDİ SÖZLEŞMESİ  ( uygulama projesi )

engine/mukavemet_tablolari.py içindeki her tabloyu KAYNAK EXCEL'e karşı
birebir doğrular:  templates/MUKAVEMET_HESABI.xlsx

NİÇİN AYRI TEST:  bu tablolar Excel'den makineyle aktarıldı.  Aktarma
sırasında bir sütun kayması ya da satır atlaması olsa hiçbir hesap testi
bunu göremezdi — motor kendi ( yanlış ) tablosuyla tutarlı çalışırdı.
Bu test, aktarımın kendisini denetler.

Kaynak dosya yoksa test ATLANIR, hata vermez.
"""
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.uygulama import mukavemet as MK                        # noqa: E402
from engine.uygulama import mukavemet_girdi as MG                  # noqa: E402
from engine.uygulama import mukavemet_tablolari as MT              # noqa: E402
from exports import mukavemet_xlsx as MX                   # noqa: E402
from testler.ortak import Rapor                           # noqa: E402

#  Teslim edilen kitapta karşılığı olan, kaynak kitapta olmayan girdiler
_EK_ANAHTARLAR = set(MX.EK_GIRDI_ANAHTARLARI)
_HESAP_ANAHTARLARI = {a for a, _h in MX.HESAP_SAYFASI_GIRDILERI}

KAYNAK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "templates", "MUKAVEMET_HESABI.xlsx")

#  ( modüldeki tablo, Excel sayfası, aralık, Excel'den alınacak sütun sırası )
#  sütun sırası:  Excel aralığındaki 0-tabanlı indisler
ESLESME = (
    ("RAY_PROFILI",       "TABLOLAR",    "I60:S65",  None),
    ("RAY_GEOMETRI",      "TABLOLAR",    "I69:N74",  None),
    ("HALAT",             "TABLOLAR",    "A32:F43",  (0, 1, 2, 4, 5)),
    ("NPU_PROFIL",        "TABLOLAR",    "M36:AH53", (0, 9, 10, 11, 12, 13, 14, 15, 16)),
    ("KABIN_ALANI",       "TABLOLAR",    "H78:K99",  (0, 1, 2, 3)),
    ("DARBE_TIPLERI",     "TABLOLAR",    "H32:K35",  (0, 3)),
    ("AGIRLIK_MALZEMESI", "TABLOLAR",    "U61:W62",  (0, 1, 2)),
    ("RAY_CELIGI",        "TEKNİK",      "P2:R4",    (0, 1, 2)),
    ("KANAL_ISLEME",      "Veri Girişi", "T42:W43",  (0, 1, 2, 3)),
    ("BUKULGEN_KABLO",    "TABLOLAR",    "D61:G64",  (0, 1, 2, 3)),
)


#  KAYNAK KİTAPTAN GENİŞLETİLEN TABLOLAR.  Kitabın satırlarına dokunulmaz;
#  yalnız standardın gerektirdiği satırlar EKLENİR.  Burada hem "kitabın
#  hiçbir satırı değişmedi" hem de "eklenenler beklenenlerdir" denetlenir —
#  yoksa genişletme, sessizce kaynak veriyi değiştirmenin kapısı olurdu.
GENISLETILEN = {
    #  T75/B ( 75 x 62 x 10 ) kitabın listesinde yoktu.  Orta kapasiteli
    #  asansörlerin en yaygın rayıdır ve yokluğu, o rayla çizilmiş projeyi
    #  programla HİÇ hesaplanamaz kılıyordu.  Kesit değerleri ISO 7465'ten;
    #  iki bağımsız kaynak doğruluyor ( bkz. mukavemet_tablolari ).
    "RAY_PROFILI":  {"eklenen": ("75 x 62 x 10",), "degisen": {}},
    "RAY_GEOMETRI": {"eklenen": ("75 x 62 x 10",), "degisen": {}},
    #  EN 81-20 Çizelge 6'da olup kitapta olmayan beyan yükleri.
    "KABIN_ALANI": {
        "eklenen": (100, 1050, 1250, 1350, 1425, 1500, 2500),
        #  320 kg Çizelge 6'da YOKTUR;  standardın ara değer notu 300/375
        #  arası 0,953 m² verir, kitap 0,97 yazar ( emniyetsiz taraf ).
        "degisen": {320: (4, 0.953, 0.79)},
    },
}


def _kanal_tablosu(r, ws):
    """Nequiv(t) OFİS AÇILARINDAN türetilir;  varsayılan açılarda kitapla birebir.

    Kitabın tablosu ( D47:G52 ) her kanal şeklinin karşısına tek bir açı ve
    tek bir Nequiv(t) çiviler.  Modül artık TS EN 81-50 Çizelge 2'yi kullanıp
    değeri γ / β'dan hesaplıyor.  Burada iki şey denetlenir:
        · kitabın satırları DEĞİŞMEMİŞ  ( sapmanın dayanağı odur ),
        · ofisin varsayılan açılarında türetilen değer kitapla AYNI.
    """
    from engine.uygulama import sabitler as US
    O = US.sabitler(None)
    satir = {}
    for r_ in range(47, 53):
        ad = ws[f"D{r_}"].value
        if ad not in (None, ""):
            satir[str(ad).strip()] = (ws[f"F{r_}"].value, ws[f"G{r_}"].value)
    r.esit("kaynak kanal tablosu satır sayısı", len(satir), len(MT.KANAL_SEKLI))
    for ad, _tur, _gecis in MT.KANAL_SEKLI:
        aci_x, neq_x = satir.get(ad, (None, None))
        #  Kitabın "açı" sütunu iki büyüklüğü karıştırır:  V kanalda γ,
        #  altı kesik kanalda β.  Karşılaştırma buna göre yapılır.
        _tur = MT.kanal_turu(ad)
        bizim_aci = (O["kanal_beta"] if _tur == "UK"
                     else (None if _tur == "U" else O["kanal_gama_v"]))
        bizim = MT.kanal_nequiv_t(ad, O["kanal_gama_v"], O["kanal_beta"])
        if _tur == "VK":
            #  ALTI KESİK V'DE BİLEREK AYRILIYORUZ:  kitap onu Çizelge 2'nin
            #  β satırından okuyor ( 5,0 ), standart ise V satırındadır
            #  ( γ = 38° → 12 ).  Bkz. EXCEL_FARKLARI ㉕.
            r.esit(f"kanal '{ad}' kitapta β satırından okunuyor", neq_x, 5)
            r.esit(f"kanal '{ad}' bizde V satırından  ( standart )", bizim, 12.0)
            continue
        r.kontrol(f"kanal '{ad}' açısı kitapla aynı  ( varsayılan ofis )",
                  _esit(bizim_aci, aci_x), f"→ modül {bizim_aci!r}, Excel {aci_x!r}")
        r.kontrol(f"kanal '{ad}' Nequiv(t) kitapla aynı  ( varsayılan ofis )",
                  _esit(bizim, neq_x), f"→ modül {bizim!r}, Excel {neq_x!r}")
    #  ÇİZELGE 2'NİN KENDİSİ  —  TS EN 81-50 m.5.12.2.2
    for aci, bek in MT.NEQUIV_V:
        r.esit(f"Çizelge 2  V kanal γ = {aci}°",
               MT.kanal_nequiv_t("V Kanal", aci, 90), bek)
    #  β SATIRI "U-Undercut grooves" SATIRIDIR:  altı kesik YARIM DAİRE.
    #  Altı kesik V, Çizelge 2'nin V satırındadır ( bkz. EXCEL_FARKLARI ).
    for aci, bek in MT.NEQUIV_U_ALTI_KESIK:
        r.esit(f"Çizelge 2  altı kesik yarım daire β = {aci}°",
               MT.kanal_nequiv_t("Altı Kesik Yarım Daire Kanal", 38, aci), bek)
    for aci, bek in MT.NEQUIV_V:
        r.esit(f"Çizelge 2  altı kesik V γ = {aci}°  ( V satırı )",
               MT.kanal_nequiv_t("Altı Kesik V Kanal", aci, 90), bek)
    r.esit("altı kesik V'de β Nequiv'i değiştirmez",
           MT.kanal_nequiv_t("Altı Kesik V Kanal", 38, 105), 12.0)
    # ------------------------------------------------------------------
    #  TS EN 81-50 Ek E  —  STANDARDIN KENDİ ÇÖZÜMLÜ ÖRNEKLERİ
    #  Ek E üç sayısal örnek verir;  üçü de burada yeniden üretilir.
    #  E.1'de standart Kp'yi 2,07'ye YUVARLAYIP çarpar ( 2,07 × 2 = 4,14 );
    #  tam değer 2,0736 → 4,1472'dir.  Program yuvarlamaz, bu yüzden
    #  karşılaştırma standardın kendi yuvarlamasına tolerans tanır.
    # ------------------------------------------------------------------
    for _ad, _kanal, _g, _b, _Dt, _Dp, _nps, _npr, _nt, _neq in (
            ("E.1  2:1 · V kanal", "V Kanal", 40, 90, 600, 500, 2, 0, 10.0, 14.14),
            ("E.2  1:1 · altı kesik U", "Altı Kesik Yarım Daire Kanal",
             38, 90, 600, 400, 1, 0, 5.0, 10.06),
            ("E.3  1:1 çift sarım · U", "Yarım Daire Kanal (Çift Sarım)",
             38, 90, 600, 600, 2, 0, 2.0, 4.0)):
        _t = MT.kanal_nequiv_t(_kanal, _g, _b)
        r.esit(f"Ek E {_ad}: Nequiv(t)", _t, _nt)
        _kp = (_Dt / _Dp) ** 4
        _n = _t + _kp * (_nps + 4 * _npr)
        r.kontrol(f"Ek E {_ad}: Nequiv = {_neq}", abs(_n - _neq) <= 0.01,
                  f"→ program {_n:.4f}, standart {_neq}")
        r.esit("Çizelge 2  alt kesilmesiz yarım daire",
           MT.kanal_nequiv_t("Yarım Daire Kanal", 38, 90), 1.0)
    r.esit("çift sarımda iki geçiş",
           MT.kanal_nequiv_t("Yarım Daire Kanal (Çift Sarım)", 38, 90), 2.0)
    #  Ara değer:  çizelgenin kendi notu doğrusal ara değere izin verir
    r.esit("Çizelge 2  ara değer β = 87,5°  ( altı kesik yarım daire )",
           MT.kanal_nequiv_t("Altı Kesik Yarım Daire Kanal", 38, 87.5), 4.4)
    r.esit("Çizelge 2  ara değer γ = 39°",
           MT.kanal_nequiv_t("V Kanal", 39, 90), 11.0)
    r.esit("Çizelge 2  ara değer γ = 43,5°  ( altı kesik V, V satırı )",
           MT.kanal_nequiv_t("Altı Kesik V Kanal", 43.5, 90), 7.25)


def _genisletilen_tablo(r, ad, tablo, excel):
    ex = {satir[0]: tuple(satir[1:]) for satir in excel}
    mo = {satir[0]: tuple(satir[1:]) for satir in tablo}
    kural = GENISLETILEN[ad]
    r.esit(f"{ad}: kitabın satırlarının hepsi duruyor",
           sorted(set(ex) - set(mo)), [])
    r.esit(f"{ad}: eklenenler beklenenlerle aynı",
           sorted(set(mo) - set(ex)), sorted(kural["eklenen"]))
    for anahtar, deger in sorted(ex.items()):
        beklenen = kural["degisen"].get(anahtar, deger)
        r.kontrol(f"{ad}[{anahtar}]",
                  all(_esit(a, b) for a, b in zip(mo[anahtar], beklenen)),
                  f"→ modül {mo[anahtar]!r}, beklenen {beklenen!r}")


def _esit(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return (a if a is not None else "") == (b if b is not None else "")


def calistir():
    print("\n\033[1mTEST 8 — MUKAVEMET TABLOLARI + GİRDİ SÖZLEŞMESİ\033[0m")
    r = Rapor("Mukavemet tabloları")
    if not os.path.isfile(KAYNAK):
        r.atla(f"Kaynak Excel yok — {os.path.basename(KAYNAK)}")
        return r
    warnings.filterwarnings("ignore")
    import openpyxl
    wb = openpyxl.load_workbook(KAYNAK, data_only=True)

    def oku(sayfa, aralik, sutunlar):
        cikti = []
        for satir in wb[sayfa][aralik]:
            v = [c.value for c in satir]
            if v[0] is None:
                continue
            cikti.append(tuple(v[i] for i in sutunlar) if sutunlar else tuple(v))
        return cikti

    for ad, sayfa, aralik, sutunlar in ESLESME:
        tablo = getattr(MT, ad)
        excel = oku(sayfa, aralik, sutunlar)
        if ad in GENISLETILEN:
            _genisletilen_tablo(r, ad, tablo, excel)
            continue
        if not r.esit(f"{ad}: satır sayısı", len(tablo), len(excel)):
            continue
        for i, (m, e) in enumerate(zip(tablo, excel)):
            if not r.esit(f"{ad}[{i}]: sütun sayısı", len(m), len(e)):
                continue
            for j, (mv, ev) in enumerate(zip(m, e)):
                r.kontrol(f"{ad}[{i}][{j}]", _esit(mv, ev), f"→ modül {mv!r}, Excel {ev!r}")

    #  KANAL TABLOSU:  modül artık Nequiv(t)'yi kitaptan değil, ofis
    #  açılarından ve TS EN 81-50 Çizelge 2'den türetiyor.
    _kanal_tablosu(r, wb["TABLOLAR"])

    #  ω tablosu:  231 satır, λ = 20…250
    om = oku("TABLOLAR", "A47:B277", (0, 1))
    r.esit("OMEGA: satır sayısı", len(MT.OMEGA), len(om))
    r.esit("OMEGA: λ alt sınırı", MT.OMEGA_LAMBDA_MIN, om[0][0])
    r.esit("OMEGA: λ üst sınırı", MT.OMEGA_LAMBDA_MAX, om[-1][0])
    for lam, w in om:
        r.kontrol(f"ω(λ={lam})", _esit(MT.omega(lam), w),
                  f"→ modül {MT.omega(lam)!r}, Excel {w!r}")
    r.kontrol("ω tablo dışı λ için None", MT.omega(19) is None and MT.omega(251) is None)

    #  AĞIRLIK RAY ARASI → GENİŞLİK TABLOSU KALDIRILDI.  Kitapta duruyor
    #  ( X59:Z60 ) ama motor artık okumaz:  TS EN 81-50 Ek C.2.2 karşı
    #  ağırlığın KENDİ ölçülerini ( Gx · Gy ) veri olarak ister, ray
    #  arasından türetme diye bir bağıntı yoktur.  Türetme işlevlerinin
    #  GERİ GELMEDİĞİ denetlenir — geri gelirse üç değere kilitli girdi de
    #  geri gelmiş demektir.
    for _kalkti in ("AGIRLIK_RAY_ARASI", "RAY_ARALARI", "agirlik_genisligi",
                    "agirlik_derinlik"):
        r.kontrol(f"kaldırılan türetme geri gelmedi: {_kalkti}",
                  not hasattr(MT, _kalkti))
    r.kontrol("karşı ağırlık ölçüleri GİRDİ",
              all(a in MG.ALAN for a in ("agirlik_genisligi", "agirlik_derinligi")))

    #  Erişim işlevleri gerçekten doğru sütunu okuyor mu
    p = "89 x 62 x 15,88"
    r.esit("ray() Gr", MT.ray(p, "Gr"), 12.38)
    r.esit("ray() Wx", MT.ray(p, "Wx"), 14350)
    r.esit("ray() ix", MT.ray(p, "ix"), 19.48)
    r.esit("npu() A", MT.npu(120, "A"), 17)
    r.esit("npu() Wx", MT.npu(120, "Wx"), 60.7)
    r.esit("npu() ix", MT.npu(120, "ix"), 4.62)
    r.esit("halat_kopma()", MT.halat_kopma(6.5), 24700)
    r.esit("k2 sabiti", MT.K2_NORMAL_KULLANMA, 1.2)
    r.esit("kablo_agirligi()", MT.kablo_agirligi("24 x 0,75"), 0.642)
    r.kontrol("bilinmeyen anahtar None döner",
              MT.ray("yok", "Gr") is None and MT.halat_kopma(99) is None)

    _girdi_sozlesmesi(r, wb)
    return r


#  Excel'in kendi açılır liste ( veri doğrulama ) aralıkları, girdi
#  alanlarının seçenek listesinin kaynağıdır.  İki alanda bilerek
#  ayrıldık; burada Excel'in HAM listesini kilitliyoruz ki kaynak dosya
#  değişirse fark yeniden gözden geçirilsin.
BILINEN_FARK = {
    #  Excel'in açılır listesi "Döküm" yazıyor, ama VLOOKUP tablosunun
    #  ( TABLOLAR!U61:W62 ) anahtarı "Pik Döküm".  Excel'de "Döküm"
    #  seçilirse arama #YOK verir — kaynaktaki hata.  Modül tablo
    #  anahtarını kullanıyor.
    "agirlik_malzemesi": (["Barit", "Döküm"], ["Barit", "Pik Döküm"]),
    #  Hız listesinin sonunda 5 adet dolgu 0 var; hız 0 anlamsız.
    "beyan_hizi": ([0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6, 0, 0, 0, 0, 0],
                   [0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6]),
    #  KİTABIN LİSTESİ EKSİKTİ:  EN 81-20 Çizelge 6'nın 28 yükünden 7'si
    #  yoktu ( 100 · 1050 · 1250 · 1350 · 1425 · 1500 · 2500 kg ) ve liste
    #  kapalı olduğu için o yüklerde hiç hesap yapılamıyordu.  Modül tabloyu
    #  standarda tamamladı;  teslim edilen kitabın listesi de genişletilir
    #  ( bkz. exports/mukavemet_xlsx._liste_tamamla ).
    #  RAY LİSTESİ DE GENİŞLETİLDİ  —  T75/B kitapta yok  ( yukarıya bkz. ).
    #  Teslim edilen kopyanın listesi ve VLOOKUP tabloları da genişletilir
    #  ( bkz. exports/mukavemet_xlsx._ray_tablosu_genislet ).
    "kabin_ray_profili": (["50 x 50 x 5", "70 x 65 x 9", "89 x 62 x 15,88",
                           "90 x 75 x 16", "125 x 82 x 16", "127 x 89 x 16"],
                          ["50 x 50 x 5", "70 x 65 x 9", "75 x 62 x 10",
                           "89 x 62 x 15,88", "90 x 75 x 16", "125 x 82 x 16",
                           "127 x 89 x 16"]),
    "agirlik_ray_profili": (["50 x 50 x 5", "70 x 65 x 9", "89 x 62 x 15,88",
                             "90 x 75 x 16", "125 x 82 x 16", "127 x 89 x 16"],
                            ["50 x 50 x 5", "70 x 65 x 9", "75 x 62 x 10",
                             "89 x 62 x 15,88", "90 x 75 x 16", "125 x 82 x 16",
                             "127 x 89 x 16"]),
    "beyan_yuku": ([180, 225, 300, 320, 375, 400, 450, 525, 600, 630, 675,
                    750, 800, 825, 900, 975, 1000, 1125, 1200, 1275, 1600, 2000],
                   [100, 180, 225, 300, 320, 375, 400, 450, 525, 600, 630, 675,
                    750, 800, 825, 900, 975, 1000, 1050, 1125, 1200, 1250, 1275,
                    1350, 1425, 1500, 1600, 2000, 2500]),
}


#  KAYNAK KİTAPTA AÇILIR LİSTESİ OLAN ama modülde SERBEST bırakılan alanlar.
#  Kaynak kitap tarihî referanstır ve olduğu gibi kalır;  serbestleştirme
#  EXCEL_FARKLARI'nda belgelenir ve teslim edilen kopyada doğrulama
#  kaldırılır.  ( değer:  farkın kaydında geçmesi beklenen anahtar sözcük )
SERBESTLESTIRILEN = {"agirlik_ray_arasi": "Karşı ağırlığın ölçüleri"}


def _ek_satir_denetimi(r):
    """Ek girdi satırları ofis sabitleri bloğuyla çakışmamalı.

    İkisi de 'Veri Girişi'!A sütununa yazılır.  Ek girdi listesi büyüyünce
    blok aşağı kaydırılmazsa etiketler birbirini EZİYOR ve hata sessiz
    kalıyor:  ofis sabitleri yalnız varsayılandan farklıyken yazıldığı için
    çoğu senaryoda blok boş oluyor ve çakışma görünmüyor.
    """
    from exports import mukavemet_xlsx as _X
    _son = max(row for _a, row, *_x in _X.EK_GIRDI_HUCRELERI)
    r.kontrol("ek girdi satırları ofis bloğuna taşmıyor",
              not _X._ek_satir_cakismasi(),
              f"→ son ek girdi satırı {_son}, ofis başlığı {_X.OFIS_BASLIK}")
    r.kontrol("ek girdi satır numaraları benzersiz",
              len({row for _a, row, *_x in _X.EK_GIRDI_HUCRELERI})
              == len(_X.EK_GIRDI_HUCRELERI))
    r.kontrol("ofis bloğu arama penceresi başlığı kapsıyor",
              _X.OFIS_BASLIK in _X.OFIS_ARAMA,
              f"→ {_X.OFIS_BASLIK} ∉ {_X.OFIS_ARAMA}")


def _girdi_sozlesmesi(r, wb):
    _ek_satir_denetimi(r)
    """engine/mukavemet_girdi.py ↔ 'Veri Girişi' sayfası."""
    from openpyxl.utils import range_boundaries
    ws = wb["Veri Girişi"]

    #  Hücre → veri doğrulama aralığı
    dv_araligi = {}
    for dv in ws.data_validations.dataValidation:
        f1 = str(dv.formula1 or "")
        if not f1.startswith("$"):
            continue
        for rng in dv.sqref.ranges:
            mn, mr, mx, mxr = range_boundaries(str(rng))
            for c in range(mn, mx + 1):
                for w in range(mr, mxr + 1):
                    dv_araligi[ws.cell(row=w, column=c).coordinate] = f1.replace("$", "")

    for anahtar, hucre, etiket, _b, tur, secenekler, varsayilan in MG.ALANLAR:
        if tur == "hesap":
            r.kontrol(f"girdi {anahtar}: seçenek/varsayılan taşımıyor",
                      secenekler is None and varsayilan is None)
            continue
        if tur == "liste":
            excel = [ws[h].value for h in MG.DURAK_HUCRELERI]
            excel = [v for v in excel if v not in (None, "")]
            r.esit(f"girdi {anahtar}: varsayılan", list(varsayilan), excel)
            r.esit("durak hücresi sayısı", len(MG.DURAK_HUCRELERI), 23)
            continue

        r.kontrol(f"girdi {anahtar}: etiket dolu", bool(etiket and etiket.strip()))
        if not hucre:
            #  Kaynak Excel'in "Veri Girişi" sayfasında KARŞILIĞI OLMAYAN alan.
            #  Excel bu değerleri ya hesap sayfasına sabit yazar ( Nps · Npr ),
            #  ya hiç sormaz ( paten balata boyu ), ya da programın kendi
            #  eklediği alandır ( toplam verim · ağırlık güvenlik tertibatı ).
            #  Varsayılanı Excel'e karşı denetlenemez;  seçenek listesi varsa
            #  varsayılanın o listede olduğu doğrulanır.
            if secenekler is not None:
                r.kontrol(f"girdi {anahtar}: varsayılan seçenek listesinde",
                          varsayilan in secenekler,
                          f"→ {varsayilan!r} ∉ {secenekler!r}")
            #  Bu alanlar teslim edilen kitaba AYRI bir blokta yazılır ve
            #  geri okunur;  yoksa revizyonda sessizce kaybolurlardı.
            r.kontrol(f"girdi {anahtar}: teslim kopyasında yeri var",
                      anahtar in _EK_ANAHTARLAR or anahtar in _HESAP_ANAHTARLARI,
                      "→ ne EK_GIRDI_HUCRELERI'nde ne de hesap sayfasında")
            continue
        r.kontrol(f"girdi {anahtar}: varsayılan Excel'deki değer ({hucre})",
                  _esit(varsayilan, ws[hucre].value),
                  f"→ modül {varsayilan!r}, Excel {ws[hucre].value!r}")

        ar = dv_araligi.get(hucre)
        if secenekler is None:
            if anahtar in SERBESTLESTIRILEN:
                #  KAYNAK KİTAPTA LİSTE VAR, MODÜLDE YOK — BİLEREK.
                #  Gerekçesi mukavemet.EXCEL_FARKLARI'nda yazılıdır ve teslim
                #  edilen kopyada doğrulama KALDIRILIR ( aşağıda denetleniyor ),
                #  yoksa pafta serbest, kitap kilitli olurdu.
                r.kontrol(f"girdi {anahtar}: serbestleştirme belgeli",
                          any(anahtar in a[0].lower().replace(" ", "_")
                              or SERBESTLESTIRILEN[anahtar] in a[0]
                              for a in MK.EXCEL_FARKLARI),
                          "→ EXCEL_FARKLARI'nda kaydı yok")
                continue
            r.kontrol(f"girdi {anahtar}: Excel'de de açılır liste yok", ar is None,
                      f"→ Excel'de {ar} listesi var, modülde serbest sayı")
            continue
        if ar is None:
            continue          #  seçenekler bir tablodan geliyor, DV yok
        ex = [c.value for row in ws[ar] for c in row if c.value not in (None, "")]
        if anahtar in BILINEN_FARK:
            ham, modul = BILINEN_FARK[anahtar]
            r.kontrol(f"girdi {anahtar}: Excel listesi bilinen farkla aynı ({ar})",
                      sorted(map(str, ham)) == sorted(map(str, ex)),
                      f"→ beklenen {ham}, Excel {ex}")
            r.kontrol(f"girdi {anahtar}: modül belgelenen listeyi kullanıyor",
                      sorted(map(str, modul)) == sorted(map(str, secenekler)),
                      f"→ modül {list(secenekler)}, belgelenen {modul}")
            continue
        r.kontrol(f"girdi {anahtar}: seçenekler ≡ Excel açılır listesi ({ar})",
                  sorted(map(str, secenekler)) == sorted(map(str, ex)),
                  f"→ modül {list(secenekler)}, Excel {ex}")

    #  Hesaplanan üç alan Excel formülüyle aynı sonucu veriyor mu
    v = wb  # data_only=True yüklendi
    g = MG.varsayilanlar()
    #  ( "halat_arasi" KALDIRILDI:  yalnız sarılma açısının payındaydı
    #    ( A = Ra − 2·R1 ) ve α artık proje girdisi — bkz. EXCEL_FARKLARI. )
    for anahtar, hucre in (("karsi_agirlik", "C80"), ("kuyu_boyu", "F80")):
        r.kontrol(f"hesaplanan {anahtar} ≡ Excel {hucre}",
                  _esit(g[anahtar], v["Veri Girişi"][hucre].value),
                  f"→ modül {g[anahtar]!r}, Excel {v['Veri Girişi'][hucre].value!r}")
    r.kontrol("varsayılan girdiler doğrulamadan temiz geçiyor", MG.dogrula(g) == [],
              f"→ {MG.dogrula(g)}")
    r.esit("toplam ray boyu (m)", MG.toplam_ray_boyu(g), 26.6)


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
