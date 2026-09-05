# -*- coding: utf-8 -*-
"""
MUKAVEMET HESABI — GİRDİ SÖZLEŞMESİ        ( uygulama projesi )

Kaynak:  templates/MUKAVEMET_HESABI.xlsx · "Veri Girişi" sayfası
Tüketen: "11-Muk. Hesapları" sayfası  ( → engine/mukavemet.py )

Bu modül hesap YAPMAZ.  Yalnızca mukavemet motorunun hangi girdileri
beklediğini, her birinin Excel'deki karşılığını, birimini, seçenek
listesini ve varsayılanını tanımlar.  Arayüz, XLSX içe/dışa aktarım ve
doğrulama testi hep buradan okur — tek doğruluk kaynağı.

AVANDAN AYRIDIR.  Avan tarafındaki tablolar ( engine/tables.py ) MMO/697
avan kitabından gelir; buradakiler bu Excel'in kendi tablolarıdır ve
bilerek ayrı tutulmuştur ( bkz. engine/mukavemet_tablolari.py ).
"""
from engine.ortak import ofis as OFIS
from engine.uygulama import mukavemet_tablolari as MT

#  Kabin durak yüksekliklerinin Excel'deki yeri:  G12:G34  ( 20 durak +
#  3 boş satır ).  Motor bunları tek tek değil, liste olarak alır.
DURAK_HUCRELERI = tuple(f"G{r}" for r in range(12, 35))
DURAK_AZAMI = 20


def _s(*d):
    return tuple(d)


#  ( anahtar, hücre, etiket, birim, tür, seçenekler, varsayılan )
#    tür:  "sayi" · "secim" · "liste" · "hesap"
#    "hesap" alanları kullanıcıdan alınmaz — tamamla() üretir.
ALANLAR = (
    # ── ASANSÖR TEKNİK BİLGİLERİ ──────────────────────────────────────
    #  SEÇENEKLER TABLODAN TÜRETİLİR.  Elle yazılan ikinci bir liste, kabin
    #  alanı tablosuyla ayrışabilir — nitekim kaynak kitapta ayrışmıştı:
    #  EN 81-20 Çizelge 6'nın 7 beyan yükü listede yoktu ve o yüklerde hiç
    #  hesap yapılamıyordu.  Artık tek kaynak KABIN_ALANI'dır.
    ("beyan_yuku",        "C59",  "Beyan yükü",                        "kg",   "secim",
     tuple(k[0] for k in MT.KABIN_ALANI), 800),
    ("beyan_hizi",        "C61",  "Beyan hızı",                        "m/s",  "secim",
     _s(0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6), 1),
    ("seyir_mesafesi",    "C63",  "Seyir mesafesi",                    "m",    "sayi", None, 21),
    ("kabin_agirligi",    "C75",  "Kabin ağırlığı",                    "kg",   "sayi", None, 700),
    ("karsi_agirlik",     "C80",  "Karşı ağırlık",                     "kg",   "hesap", None, None),
    ("aski_orani",        "B100", "Askı oranı  ( 1 : n )",             "—",    "secim", _s(1, 2), 2),

    # ── KABİN VE KAPI ─────────────────────────────────────────────────
    ("kabin_genisligi",   "C73",  "Kabin genişliği",                   "mm",   "sayi", None, 1450),
    ("kabin_derinligi",   "C74",  "Kabin derinliği",                   "mm",   "sayi", None, 1350),
    ("kat_kapisi_tipi",   "C66",  "Kat kapısı tipi",                   "—",    "secim",
     MT.KAPI_TIPLERI, "Teleskopik Sol"),
    ("kapi_genisligi",    "C71",  "Kat kapısı genişliği",              "mm",   "secim",
     _s(700, 800, 900, 1000, 1100, 1200, 1300, 1400), 900),
    ("uzun_pervaz",       "F69",  "Uzun pervaz",                       "mm",   "sayi", None, 90),
    ("kabin_kaciklik",    "C76",  "Kabin merkezinin y ekseninde kaçıklığı", "mm", "sayi", None, 0),
    ("agirlik_yeri",      "C77",  "Karşı ağırlık yeri",                "—",    "secim",
     _s("Sağ", "Sol", "Arka"), "Sağ"),
    ("kapi_agirligi",     "F127", "Kabin kapısı ağırlığı  ( F_D1 )",   "kg",   "sayi", None, 75),
    ("kapi_mekanizma_payi", "F128", "Kapı mekanizma ağ. mrk. payı",    "mm",   "sayi", None, 50),

    # ── DURAK VE KUYU ─────────────────────────────────────────────────
    ("durak_yukseklikleri", "G12:G34", "Durak yükseklikleri",          "mm",   "liste", None,
     _s(3000, 3000, 3000, 3000, 3000, 3000, 3000, 3750)),
    ("son_kat_yuksekligi", "B132", "Son kat yüksekliği",               "mm",   "sayi", None, 3750),
    ("kuyu_boyu",         "F80",  "Kuyu boyu",                         "mm",   "hesap", None, None),
    ("kaide_yuksekligi",  "F107", "Kaide yüksekliği",                  "mm",   "sayi", None, 750),
    ("kuyu_dibi",         "F114", "Kuyu dibi yüksekliği  ( KY )",      "mm",   "sayi", None, 1600),
    ("kuyu_derinligi",    "F111", "Kuyu derinliği  ( KD )",            "mm",   "sayi", None, 1600),
    ("ray_kapi_arasi",    "F112", "Ray - kapı arası  ( RK )",          "mm",   "sayi", None, 650),
    ("agirlik_ray_duvar", "F113", "Ağırlık ray merkezi - duvar",       "mm",   "sayi", None, 125),

    # ── MAKİNE VE MOTOR ───────────────────────────────────────────────
    ("motor_gucu",        "F95",  "Motor gücü",                        "kW",   "sayi", None, 4.9),
    ("makine_agirligi",   "F126", "Makine - motor ağırlığı  ( Gm )",   "kg",   "sayi", None, 300),
    ("sap_kasnak_yuk",    "F97",  "C  ( sap. kasnak yükü )",           "mm",   "sayi", None, 230),
    ("makine_yatak_yuk",  "F98",  "D  ( makine yatak yükü )",          "mm",   "sayi", None, 172),
    ("tahrik_kasnak_capi", "F99", "D1 ( tahrik kasnağı çapı )",        "mm",   "sayi", None, 240),
    ("saptirma_kasnak_capi", "F100", "D2 ( saptırma kasnağı çapı )",   "mm",   "sayi", None, 240),
    ("sase_yuksekligi",   "F101", "Şase yüksekliği",                   "mm",   "sayi", None, 1100),
    ("dikine_kiris",      "F102", "E  ( dikine kiriş ölçüsü )",        "—",    "secim",
     MT.NPU_OLCULERI, 120),
    ("dikine_kiris_tipi", "G102", "E  ( dikine kiriş profili )",       "—",    "secim", _s("NPU"), "NPU"),
    ("yan_yatak",         "F103", "F  ( yan yatak ölçüsü )",           "—",    "secim",
     MT.NPU_OLCULERI, 120),
    ("yan_yatak_tipi",    "G103", "F  ( yan yatak profili )",          "—",    "secim", _s("NPU"), "NPU"),
    ("yan_yatak_boyu",    "F104", "Yan yatak boyu",                    "mm",   "sayi", None, 1400),

    # ── ASKI HALATLARI ────────────────────────────────────────────────
    ("halat_adedi",       "B98",  "Askı halatı adedi",                 "adet", "sayi", None, 7),
    ("halat_capi",        "B99",  "Askı halatı çapı",                  "mm",   "secim",
     MT.HALAT_CAPLARI, 6.5),
    ("kanal_sekli",       "F105", "Kasnak kanal şekli",                "—",    "secim",
     MT.KANAL_SEKILLERI, "Altı Kesik V Kanal"),
    ("kanal_isleme",      "F106", "Kanal işleme şekli",                "—",    "secim",
     MT.KANAL_ISLEME_SEKILLERI, "Sertleştirilmemiş"),
    ("halat_arasi_yan",   "F109", "Halat arası  ( yan ağırlıkta )",    "mm",   "sayi", None, 1182),
    #  EN 81-50 m.5.12.2 — Nequiv(p).  Kaynak Excel bunları hücreye SABİT
    #  yazar ( 11!AH105 = 1 , AH106 = 0 );  oysa tesisin askı düzenine bağlıdır.
    ("kasnak_tek_yon",    "",     "Tek yönde bükülmeli kasnak sayısı  ( Nps )", "adet", "sayi", None, 1),
    ("kasnak_ters_yon",   "",     "Ters yönde bükülmeli kasnak sayısı  ( Npr )", "adet", "sayi", None, 0),
    ("acil_frenleme_a",   "B133", "Acil frenleme yavaşlaması  ( a )",  "m/s²", "sayi", None, 0.8),
    ("kablo_tipi_1",      "B107", "1. bükülgen kablo tipi",            "—",    "secim",
     MT.KABLO_TIPLERI, "24 x 0,75"),
    #  2. kablo tipi GİRDİ DEĞİLDİR:  kaynak kitapta kat kapısı tipinden
    #  HLOOKUP ile türetilir ( 'Veri Girişi'!B108 ).  Sorulmaz, hesaplanır.
    ("kablo_tipi_2",      "B108", "2. bükülgen kablo tipi",            "—",    "hesap", None, None),
    ("halat_arasi",       "F108", "Halat arası  ( kullanılan )",       "mm",   "hesap", None, None),

    # ── REGÜLATÖR ─────────────────────────────────────────────────────
    ("reg_halat_capi",    "B104", "Regülatör halatı çapı",             "mm",   "secim", _s(6, 6.5, 8), 6),
    ("reg_kasnak_capi",   "F121", "Regülatör kasnak çapı  ( Dreg )",   "mm",   "sayi", None, 300),
    ("reg_kanal_acisi",   "F122", "Regülatör kanal açısı",             "°",    "sayi", None, 40),
    ("reg_surtunme",      "F123", "Regülatör sürtünme faktörü  ( μ )", "—",    "sayi", None, 0.2),
    ("reg_gergi_agirligi", "F124", "Regülatör gergi ağırlığı  ( Gra )", "kg",  "sayi", None, 70),

    # ── KILAVUZ RAYLAR ────────────────────────────────────────────────
    ("kabin_ray_profili", "E73",  "Kabin rayı profili",                "—",    "secim",
     MT.RAY_PROFILLERI, "89 x 62 x 15,88"),
    ("agirlik_ray_profili", "F73", "Ağırlık rayı profili",             "—",    "secim",
     MT.RAY_PROFILLERI, "50 x 50 x 5"),
    ("kabin_konsol_arasi", "B111", "Kabin rayı konsollar arası en uzun mesafe", "mm", "sayi", None, 3000),
    ("agirlik_konsol_arasi", "B112", "Ağırlık rayı konsollar arası en uzun mesafe", "mm", "sayi", None, 3000),
    ("kabin_ray_sayisi",  "B115", "Kabin rayı sayısı",                 "adet", "sayi", None, 2),
    ("agirlik_ray_sayisi", "B116", "Ağırlık rayı sayısı",              "adet", "sayi", None, 2),
    ("ray_celigi_rm",     "B131", "Ray çeliği Rm",                     "N/mm²", "secim",
     MT.RAY_CELIKLERI, 370),
    #  Makine tipi kaynak kitapta B130'da DURUYOR ( açılır listesi bile var:
    #  "Dişli,Dişlisiz" ) ama hiçbir hesaba girmiyordu — motor gücü sabit
    #  η = 0,92 ile hesaplanıyordu.  Artık verim buradan belirlenir;  ofisin
    #  kendi tablosu ( engine/ortak/ofis.py ) dişli makinede 0,50 der.
    ("makine_tipi",       "B130", "Makine tipi",                       "—",    "secim",
     tuple(OFIS.MAKINE_VERIMLERI), "Dişlisiz"),
    ("kabin_paten_arasi", "B127", "Kabin paten arası",                 "mm",   "sayi", None, 3400),
    ("agirlik_paten_arasi", "B128", "Ağırlık paten arası",             "mm",   "sayi", None, 3400),
    ("guvenlik_tertibati", "G36", "Güvenlik tertibatı ( fren bloğu ) tipi", "—", "secim",
     MT.DARBE_TIPLERI_ADLARI, "Kaymalı"),
    #  TS EN 81-50 m.5.10.5 flanş eğilmesindeki ℓ.  Kaynak Excel'de karşılığı
    #  YOKTUR ( oraya 1 yazılıdır ), bu yüzden hücre alanı boştur.  Boş
    #  bırakılırsa ray tablosundaki balata yarı genişliğinden türetilir.
    ("paten_balata_boyu", "", "Paten balatası uzunluğu  ( ℓ )",  "mm",   "sayi", None, None),

    # ── KARŞI AĞIRLIK ─────────────────────────────────────────────────
    ("agirlik_malzemesi", "B118", "Karşı ağırlık malzemesi",           "—",    "secim",
     MT.AGIRLIK_MALZEMELERI, "Barit"),
    ("agirlik_ray_arasi", "B119", "Ağırlık ray arası",                 "mm",   "secim",
     MT.RAY_ARALARI, 1050),

    # ── TAMPONLAR ─────────────────────────────────────────────────────
    ("kabin_tampon_baba",   "F118", "Kabin tamponu baba yüksekliği",   "mm",   "sayi", None, 1000),
    ("agirlik_tampon_baba", "F119", "Ağırlık tamponu baba yüksekliği", "mm",   "sayi", None, 300),
    ("kabin_tampon_ezilme", "B121", "Kabin tamponu ezilme miktarı",    "mm",   "sayi", None, 90),
    ("kabin_carpma_arasi",  "B122", "Kabin tamponu - çarpma plakası arası", "mm", "sayi", None, 150),
    ("kabin_tampon_boyu",   "B123", "Kabin tamponu uzunluğu",          "mm",   "sayi", None, 100),
    ("agirlik_tampon_ezilme", "B124", "Ağırlık tamponu ezilme miktarı", "mm",  "sayi", None, 90),
    ("agirlik_carpma_arasi", "B125", "Ağırlık tamponu - çarpma plakası arası", "mm", "sayi", None, 150),
)

#  Hızlı erişim
ALAN = {a[0]: a for a in ALANLAR}
HUCRE_ALAN = {a[1]: a[0] for a in ALANLAR}
HESAPLANAN = tuple(a[0] for a in ALANLAR if a[4] == "hesap")


#  BOŞ BIRAKILABİLEN alanlar.  Boşsa motor değeri kendisi türetir ve
#  paftada kaynağını "türetilen" diye yazar;  zorunlu tutmak kullanıcıyı
#  bilmediği bir sayıyı uydurmaya iter.
#  TS EN 81-50 m.5.11.2.2.2 — hesaba girecek en küçük yavaşlama.
ACIL_FRENLEME_ASGARI = 0.5

#  ---------------------------------------------------------------------
#  FİZİKSEL GİRDİ SINIRLARI
#  ---------------------------------------------------------------------
#  ADET alanları TAM SAYI olmalıdır:  6,5 halat ya da 2,5 ray diye bir şey
#  yoktur, ama hesap böyle bir girdiyle sorunsuz koşup "UYGUN" veriyordu.
TAM_SAYI_ALANLARI = ("halat_adedi", "kabin_ray_sayisi", "agirlik_ray_sayisi",
                     "kasnak_tek_yon", "kasnak_ters_yon", "durak_sayisi")
#  SIFIR OLAMAYAN alanlar:  bölen ya da uzunluk oldukları için 0 girildiğinde
#  hesap teknik bir hatayla ( TypeError · ZeroDivisionError ) çöküyordu;
#  kullanıcı hangi alanın sorunlu olduğunu göremiyordu.
POZITIF_ALANLAR = ("kabin_konsol_arasi", "agirlik_konsol_arasi",
                   "kabin_paten_arasi", "agirlik_paten_arasi",
                   "yan_yatak_boyu", "sase_yuksekligi", "tahrik_kasnak_capi",
                   "halat_capi", "reg_kasnak_capi", "reg_halat_capi",
                   "kabin_genisligi", "kabin_derinligi", "kuyu_derinligi")
#  AÇI alanları:  0 < açı < 180.  360° girildiğinde sin(180°) = 0 çıkıyor ve
#  hesap OverflowError ile çöküyordu.
ACI_ALANLARI = {"reg_kanal_acisi": (1, 179)}

OPSIYONEL_ALANLAR = ("paten_balata_boyu",)

#  Hesapta BÖLEN olarak geçen alanlar — sıfır kabul edilmez.
BOLEN_ALANLAR = (
    "kabin_agirligi", "aski_orani", "halat_capi", "reg_halat_capi",
    "saptirma_kasnak_capi", "tahrik_kasnak_capi", "reg_kanal_acisi",
    "yan_yatak_boyu", "kabin_ray_sayisi", "agirlik_ray_sayisi",
    "kabin_paten_arasi", "agirlik_paten_arasi", "halat_adedi",
)

#  ( girdi anahtarı , [ ( tablo sütunu , okuyucu ) … ] , ne olduğu )
TABLO_GEREKLI = (
    ("kabin_ray_profili",
     [(k, (lambda p, k=k: MT.ray(p, k))) for k in
      ("A", "Ix", "Iy", "Wx", "Wy", "ix", "c")]
     + [(k, (lambda p, k=k: MT.ray_geo(p, k))) for k in ("h1_b_f", "h1_f")],
     "kesit değerleri"),
    ("agirlik_ray_profili",
     [(k, (lambda p, k=k: MT.ray(p, k))) for k in
      ("A", "Gr", "Ix", "Iy", "Wx", "Wy", "c")]
     + [(k, (lambda p, k=k: MT.ray_geo(p, k))) for k in ("h1_b_f", "h1_f")],
     "kesit değerleri"),
    ("dikine_kiris", [("A", lambda x: MT.npu(x, "A")),
                      ("ix", lambda x: MT.npu(x, "ix"))], "kesit değerleri"),
    ("yan_yatak", [("Wx", lambda x: MT.npu(x, "Wx"))], "kesit değerleri"),
    ("halat_capi", [("1 m ağırlığı", MT.halat_agirlik),
                    ("kopma yükü", MT.halat_kopma)], "halat verisi"),
    ("reg_halat_capi", [("1 m ağırlığı", MT.halat_agirlik),
                        ("kopma yükü", MT.halat_kopma)], "halat verisi"),
    ("kanal_sekli", [("Nequiv(t)", MT.kanal_nequiv_t)], "kasnak verisi"),
    ("guvenlik_tertibati", [("k1", MT.darbe_k1)], "darbe katsayısı"),
    ("agirlik_malzemesi", [("derinlik", MT.agirlik_derinlik)], "malzeme verisi"),
    ("agirlik_ray_arasi", [("genişlik", MT.agirlik_genisligi)], "genişlik karşılığı"),
    ("ray_celigi_rm", [("σperm normal", MT.sigma_perm_normal),
                       ("σperm güv.tert.", MT.sigma_perm_guvenlik)],
     "izin verilen gerilmeler"),
    ("kablo_tipi_1", [("ağırlık", MT.kablo_agirligi)], "kablo verisi"),
    ("kablo_tipi_2", [("ağırlık", MT.kablo_agirligi)], "kablo verisi"),
    ("beyan_yuku", [("kişi sayısı", MT.kabin_kisi),
                    ("en büyük alan", MT.kabin_azami_alan),
                    ("en küçük alan", MT.kabin_asgari_alan)], "kabin alanı verisi"),
)


#  ARAYÜZ GRUPLARI.  Form kendini bu listeden üretir;  sıralama ve başlıklar
#  Excel'in "Veri Girişi" sayfasındaki bloklarla aynı tutulmuştur ki kâğıttan
#  giren kullanıcı sırayı şaşırmasın.
GRUPLAR = (
    ("Asansör teknik bilgileri",
     ("beyan_yuku", "beyan_hizi", "seyir_mesafesi", "kabin_agirligi",
      "aski_orani")),
    ("Kabin ve kapı",
     ("kabin_genisligi", "kabin_derinligi", "kat_kapisi_tipi", "kapi_genisligi",
      "uzun_pervaz",
      "kabin_kaciklik", "agirlik_yeri", "kapi_agirligi", "kapi_mekanizma_payi")),
    ("Durak ve kuyu",
     ("durak_yukseklikleri", "son_kat_yuksekligi", "kaide_yuksekligi",
      "kuyu_dibi", "kuyu_derinligi", "ray_kapi_arasi", "agirlik_ray_duvar")),
    ("Makine ve motor",
     ("motor_gucu", "makine_agirligi", "sap_kasnak_yuk", "makine_yatak_yuk",
      "tahrik_kasnak_capi", "saptirma_kasnak_capi", "sase_yuksekligi",
      "dikine_kiris", "dikine_kiris_tipi", "yan_yatak", "yan_yatak_tipi",
      "yan_yatak_boyu", "makine_tipi")),
    ("Askı halatları",
     ("halat_adedi", "halat_capi", "kanal_sekli", "kanal_isleme",
      "halat_arasi_yan", "kasnak_tek_yon", "kasnak_ters_yon",
      "acil_frenleme_a", "kablo_tipi_1")),
    ("Hız regülatörü",
     ("reg_halat_capi", "reg_kasnak_capi", "reg_kanal_acisi", "reg_surtunme",
      "reg_gergi_agirligi")),
    ("Kılavuz raylar",
     ("kabin_ray_profili", "agirlik_ray_profili", "kabin_konsol_arasi",
      "agirlik_konsol_arasi", "kabin_ray_sayisi", "agirlik_ray_sayisi",
      "ray_celigi_rm", "kabin_paten_arasi", "agirlik_paten_arasi",
      "guvenlik_tertibati", "paten_balata_boyu")),
    ("Karşı ağırlık", ("agirlik_malzemesi", "agirlik_ray_arasi")),
    ("Tamponlar",
     ("kabin_tampon_baba", "agirlik_tampon_baba", "kabin_tampon_ezilme",
      "kabin_carpma_arasi", "kabin_tampon_boyu", "agirlik_tampon_ezilme",
      "agirlik_carpma_arasi")),
)


def arayuz_alanlari():
    """Formun kendini üretmesi için alan tanımları  ( JSON'a hazır )."""
    gruplar = []
    for ad, anahtarlar in GRUPLAR:
        alanlar = []
        for a in anahtarlar:
            _k, hucre, etiket, birim, tur, secenekler, varsayilan = ALAN[a]
            alanlar.append({
                "anahtar": a, "hucre": hucre, "etiket": etiket, "birim": birim,
                "tur": tur,
                "secenekler": list(secenekler) if secenekler is not None else None,
                "varsayilan": list(varsayilan) if tur == "liste" else varsayilan,
            })
        gruplar.append({"ad": ad, "alanlar": alanlar})
    return {"gruplar": gruplar, "durak_azami": DURAK_AZAMI,
            "hesaplanan": list(HESAPLANAN)}


def varsayilanlar():
    """Excel'deki örnek projenin girdileri — arayüzün açılış değerleri."""
    g = {}
    for anahtar, _h, _e, _b, tur, _s2, var in ALANLAR:
        if tur == "hesap":
            continue
        g[anahtar] = list(var) if tur == "liste" else var
    return tamamla(g)


def tamamla(g):
    """Excel'de formülle üretilen üç girdiyi doldurur.

    C80  karşı ağırlık = kabin ağırlığı + beyan yükü / 2
    F80  kuyu boyu     = seyir × 1000 + son kat yüksekliği + kuyu dibi
    F108 halat arası   = arka ağırlıkta  KD − RK − ( ağırlık ray-duvar ),
                         yan ağırlıkta   elle girilen F109
    """
    g = dict(g)
    ka, by = g.get("kabin_agirligi"), g.get("beyan_yuku")
    if _sayi(ka) and _sayi(by):
        g["karsi_agirlik"] = ka + by / 2.0
    sm, sk, kd = g.get("seyir_mesafesi"), g.get("son_kat_yuksekligi"), g.get("kuyu_dibi")
    if _sayi(sm) and _sayi(sk) and _sayi(kd):
        g["kuyu_boyu"] = sm * 1000.0 + sk + kd
    if g.get("agirlik_yeri") == "Arka":
        a, b, c = g.get("kuyu_derinligi"), g.get("ray_kapi_arasi"), g.get("agirlik_ray_duvar")
        g["halat_arasi"] = (a - b - c) if (_sayi(a) and _sayi(b) and _sayi(c)) else None
    else:
        g["halat_arasi"] = g.get("halat_arasi_yan")
    #  2. bükülgen kablo kat kapısı tipinden türetilir  ( Veri Girişi!B108 )
    g["kablo_tipi_2"] = MT.kapi_kablosu(g.get("kat_kapisi_tipi"))
    return g


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def dogrula(g):
    """Girdi sözlüğünü denetler; hata metinleri listesi döner ( boşsa temiz )."""
    hata = []
    for anahtar, _h, etiket, birim, tur, secenekler, _v in ALANLAR:
        if tur == "hesap":
            continue
        d = g.get(anahtar)
        ad = f"{etiket} ({birim})" if birim not in ("—", "") else etiket
        if tur == "liste":
            if not isinstance(d, (list, tuple)) or not d:
                hata.append(f"{ad}: en az bir durak yüksekliği girilmeli.")
                continue
            if len(d) > DURAK_AZAMI:
                hata.append(f"{ad}: en çok {DURAK_AZAMI} durak girilebilir "
                            f"( {len(d)} girildi ).")
            for i, v in enumerate(d, 1):
                if not _sayi(v) or v <= 0:
                    hata.append(f"{ad}: {i}. durak yüksekliği pozitif bir sayı olmalı.")
            continue
        if d is None or d == "":
            if anahtar not in OPSIYONEL_ALANLAR:
                hata.append(f"{ad}: boş bırakılamaz.")
            continue
        if secenekler is not None and d not in secenekler:
            hata.append(f"{ad}: geçersiz seçim — {d!r}. "
                        f"Seçenekler: {', '.join(str(x) for x in secenekler)}.")
            continue
        if tur == "sayi" and (not _sayi(d) or d < 0):
            hata.append(f"{ad}: negatif olmayan bir sayı olmalı ( {d!r} girildi ).")

    #  Tutarlılık
    dy = g.get("durak_yukseklikleri")
    sk = g.get("son_kat_yuksekligi")
    if isinstance(dy, (list, tuple)) and dy and _sayi(sk) and _sayi(dy[-1]) and dy[-1] != sk:
        hata.append(f"Son kat yüksekliği ({sk} mm) ile son durak yüksekliği "
                    f"({dy[-1]} mm) uyuşmuyor.")
    sm = g.get("seyir_mesafesi")
    if isinstance(dy, (list, tuple)) and dy and _sayi(sm) and all(_sayi(v) for v in dy):
        bek = (sum(dy) - dy[-1]) / 1000.0
        if abs(bek - sm) > 0.001:
            hata.append(f"Seyir mesafesi ({sm} m) durak yüksekliklerinden çıkan "
                        f"{bek:g} m ile uyuşmuyor.")
    #  SIFIR OLAMAYACAK ALANLAR.  Bunlar hesapta BÖLEN olarak geçer;  sıfır
    #  girilirse motor ZeroDivisionError ile çöker.  Kullanıcıya çökme değil
    #  neyi düzelteceği söylenmeli.
    for anahtar in BOLEN_ALANLAR:
        d = g.get(anahtar)
        if _sayi(d) and d == 0:
            hata.append(f"{ALAN[anahtar][2]}: sıfır olamaz — bu değer hesapta "
                        "bölen olarak kullanılır.")

    #  TABLO BÜTÜNLÜĞÜ.  Bir seçenek listede var ama tablosunda karşılığı
    #  eksikse hesap sessizce yanlış sonuç vermemeli.  ( Kaynak Excel'in NPU
    #  tablosunda 240 · 280 · 300 için atalet yarıçapı yoktur;  Excel'de bu
    #  seçim #SAYI/0! üretir. )
    for anahtar, oku, ne in TABLO_GEREKLI:
        d = g.get(anahtar)
        if d is None or d == "":
            continue
        eksik = [a for a, f in oku if f(d) is None]
        if eksik:
            hata.append(f"{ALAN[anahtar][2]}: seçilen '{d}' için tabloda "
                        f"{ne} eksik ( {', '.join(eksik)} ). Başka bir değer seçin.")

    #  ACİL FRENLEME YAVAŞLAMASININ İKİ SINIRI DA VARDIR.
    #  Üst sınır TS EN 81-20'den:  en çok 1 gn.
    #  ALT sınır TS EN 81-50 m.5.11.2.2.2'den:  "In no case shall the rate of
    #  retardation to consider be less than … 0,5 m/s²".  Bu sınır önce
    #  denetlenmiyordu;  küçük bir a atalet kuvvetini küçültür, T1/T2 oranını
    #  iyileştirir ve tahrik yeteneğini olduğundan İYİ gösterir — emniyetsiz.
    ivme = g.get("acil_frenleme_a")
    if _sayi(ivme) and ivme > 9.81:
        hata.append(f"Acil frenleme yavaşlaması ({ivme} m/s²) TS EN 81-20 gereği "
                    "1 gn = 9,81 m/s² değerini aşamaz.")
    if _sayi(ivme) and ivme < ACIL_FRENLEME_ASGARI:
        hata.append(f"Acil frenleme yavaşlaması ({ivme} m/s²) TS EN 81-50 "
                    f"m.5.11.2.2.2 gereği {ACIL_FRENLEME_ASGARI} m/s²'nin "
                    "altına inemez. ( Tampon kursu kısıtlıysa daha küçük bir "
                    "değer ancak tamponun tasarım yavaşlamasıyla birlikte "
                    "gerekçelendirilebilir. )")
    #  ADET · POZİTİFLİK · AÇI  —  fiziksel sınırlar
    for anahtar in TAM_SAYI_ALANLARI:
        d = g.get(anahtar)
        if _sayi(d) and float(d) != int(d):
            hata.append(f"{ALAN[anahtar][2]}: adet tam sayı olmalıdır "
                        f"( {d} girildi ).")
    for anahtar in POZITIF_ALANLAR:
        d = g.get(anahtar)
        if anahtar in ALAN and d is not None and (not _sayi(d) or d <= 0):
            hata.append(f"{ALAN[anahtar][2]}: sıfırdan büyük olmalıdır "
                        f"( {d} girildi ).")
    for anahtar, (alt, ust) in ACI_ALANLARI.items():
        d = g.get(anahtar)
        if d is not None and (not _sayi(d) or not (alt <= d <= ust)):
            hata.append(f"{ALAN[anahtar][2]}: {alt}° ile {ust}° arasında "
                        f"olmalıdır ( {d} girildi ).")

    #  MAKİNE KAİDESİ GEOMETRİSİ.  Bölüm 2 basit kiriş modelidir:  açıklığı L
    #  olan kirişte tekil yük, A mesnedinden X = L − mesnet payı uzaklıktadır.
    #  Model 0 < X < L gerektirir.  L mesnet payından küçükse X NEGATİF çıkar;
    #  o zaman moment ve gerilme de negatif olur ve "σe ≤ σem" karşılaştırması
    #  bunu SESSİZCE "uygun" sayar ( −5.350 N/mm² ≤ 130 doğrudur ).  Sayı
    #  fiziksel değildir;  geometri baştan reddedilmelidir.
    L = g.get("yan_yatak_boyu")
    pay = (g.get("_ofis") or {}).get("yan_yatak_L_X")
    if not _sayi(pay):
        from engine.uygulama import sabitler as _US
        pay = _US.VARSAYILAN["yan_yatak_L_X"]
    if _sayi(L) and _sayi(pay) and L - pay <= 0:
        hata.append(f"Yan yatak boyu ({L} mm) mesnet payından ({pay} mm) büyük "
                    "olmalıdır. Makine kaidesi hesabı, açıklığı L olan basit "
                    f"kirişte yükün mesnetten X = L − {pay} uzaklıkta olduğunu "
                    "kabul eder; X ≤ 0 fiziksel değildir.")

    if g.get("agirlik_yeri") == "Arka":
        a, b, c = g.get("kuyu_derinligi"), g.get("ray_kapi_arasi"), g.get("agirlik_ray_duvar")
        if _sayi(a) and _sayi(b) and _sayi(c) and a - b - c <= 0:
            hata.append("Arka karşı ağırlıkta halat arası pozitif çıkmıyor: "
                        f"KD − RK − (ray-duvar) = {a} − {b} − {c} = {a - b - c} mm.")
    return hata


def toplam_ray_boyu(g):
    """Kılavuz ray toplam boyu ( m ) — Excel: (ΣG12:G34 + F107−200 + F114−300)/1000."""
    dy = g.get("durak_yukseklikleri") or ()
    if not all(_sayi(v) for v in dy) or not dy:
        return None
    ky, kd = g.get("kaide_yuksekligi"), g.get("kuyu_dibi")
    if not (_sayi(ky) and _sayi(kd)):
        return None
    return (sum(dy) + (ky - 200) + (kd - 300)) / 1000.0
