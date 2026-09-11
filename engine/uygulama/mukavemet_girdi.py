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
from engine.ortak.steps import evet_mi
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
    #  ASANSÖR ADI.  Bir binada dört asansör olabilir ve hepsi ayrı kuyudadır;
    #  paftaları birbirinden ayırt edilebilmeli.  Boş bırakılırsa "1 nolu
    #  asansör" gibi numarayla anılır.  Kaynak Excel'de karşılığı yoktur
    #  ( tek asansörlük bir kitaptır ), o yüzden hücre adresi boştur.
    ("asansor_adi",       "",     "Asansör adı  ( paftada görünür )",  "—",    "metin", None, None),
    #  SEÇENEKLER TABLODAN TÜRETİLİR.  Elle yazılan ikinci bir liste, kabin
    #  alanı tablosuyla ayrışabilir — nitekim kaynak kitapta ayrışmıştı:
    #  EN 81-20 Çizelge 6'nın 7 beyan yükü listede yoktu ve o yüklerde hiç
    #  hesap yapılamıyordu.  Artık tek kaynak KABIN_ALANI'dır.
    ("beyan_yuku",        "C59",  "Beyan yükü",                        "kg",   "secim",
     tuple(k[0] for k in MT.KABIN_ALANI), 800),
    ("beyan_hizi",        "C61",  "Beyan hızı",                        "m/s",  "secim",
     _s(0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6), 1),
    ("seyir_mesafesi",    "C63",  "Seyir mesafesi",                    "m",    "sayi", None, 21),
    #  BOŞ BIRAKILIRSA OFİS TABLOSUNDAN DOLAR  ( engine/ortak/ofis.py ).
    #  Standartlarda böyle bir çizelge yoktur — TS EN 81-20 / 81-50 kabin
    #  kütlesini ( P ) hep GİRDİ olarak tanımlar;  tablo ofisin kendi
    #  imalatçı deneyimidir ve avan tarafında da aynı yerden okunur.
    #  VARSAYILANI 700'DÜR:  kaynak kitabın örnek projesinin değeri ( C75 ) ve
    #  bütün Excel karşılaştırma testlerinin dayanağı odur.  Beyan yükü
    #  değiştirildiğinde arayüz alanı tablodan günceller.
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
    #  ASKI NOKTASI ( S ) — KAÇIKLIKTAN AYRI BİR NOKTADIR.
    #  Ek C.1.2 ray eksenini orijin alıp beş nokta tanımlar:  kabin merkezi
    #  ( C ), boş kabin kütlesi ( P ), beyan yükü ( Q ), ASKI ( S ) ve kapı.
    #  Kaçıklık ağırlığın NEREDE DURDUĞU, askı ise NEREDEN ASILDIĞIDIR;  ray
    #  kuvveti ikisinin arasındaki moment kolundan doğar — C.2.2.1 ve
    #  C.2.3.1 bu yüzden ( xQ − xs ) ve ( yp − ys ) yazar.
    #  Kabin ortada olup askı kaçık olabilir ( o zaman kaçıklık 0 iken kuvvet
    #  vardır ), ya da kabin kaçık olup kendi üstünden asılı olabilir ( o
    #  zaman boş kabinin momenti sıfırlanır ).
    #  C.2.1'DE ( güvenlik tertibatı ) BU NOKTA GEÇMEZ:  tertibat RAYI
    #  kavradığı için tepki ray ekseninden ölçülür.  Bölümün hükmünü genelde
    #  o durum verdiğinden ( k1 = 2 ), varsayılan 0 çoğu projede sonucu
    #  değiştirmez — ama eksantrik askılı yerleşimde gerçek değer girilmelidir.
    ("aski_kaciklik_x",   "",     "Askı noktasının x kaçıklığı  ( xs )", "mm", "sayi", None, 0),
    ("aski_kaciklik_y",   "",     "Askı noktasının y kaçıklığı  ( ys )", "mm", "sayi", None, 0),
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
    ("saptirma_kasnak_capi", "F100", "D2 — saptırma kasnaklarının ORTALAMA çapı", "mm", "sayi", None, 240),
    #  Ds — EN KÜÇÜK kasnak çapı.  Sf formülündeki Kp = (Dt/Dp)⁴ ORTALAMA
    #  bükülme şiddetini temsil eder;  EN 81-20 m.5.5.2.1'in D/dr ≥ 40 sınırı
    #  ise HER kasnak için ayrı ayrı geçerlidir — ortalama sınırı geçse bile
    #  tek bir küçük kasnak geçemiyor olabilir.  Boş bırakılırsa ortalama çap
    #  kullanılır ( eski davranış ).
    ("saptirma_kasnak_min_capi", "", "Ds — saptırma kasnaklarının EN KÜÇÜK çapı  ( boşsa ortalama )",
     "mm", "sayi", None, None),
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
    #  KATALOG HALAT VERİSİ.  Birim kütle ve kopma yükü TS 12385-5 tablosundan
    #  ( 6x19 / 8x19 LİF ÖZLÜ ) çapa göre okunuyordu ve elle girme yolu yoktu.
    #  Küçük kasnaklı dişlisiz makinelerde kullanılan çelik özlü / özel halatlar
    #  o tabloda HİÇ YOKTUR:  6,5 mm için tablo 0,152 kg/m · 24,7 kN derken
    #  katalog 0,179 kg/m · 31,5 kN verir.  Fark iki ayrı yöne çalışıyordu —
    #  hafif halat motoru KÜÇÜK gösteriyor ( emniyetsiz ), düşük kopma yükü ise
    #  güvenlik katsayısını olduğundan KÖTÜ gösterip standarda uyan tasarımlara
    #  "UYGUN DEĞİL" dedirtiyordu.  Boş bırakılırsa tablo kullanılır.
    #  λ — DENGE ( KOMPANZASYON ) ZİNCİRİ ORANI.  Zincir, kabin ile karşı
    #  ağırlık arasında asılıdır ve halatın kabin en alttayken yarattığı
    #  dengesizliği karşılar.  Program bunu HİÇ bilmiyordu:  zincirli bir
    #  tesiste motoru gereğinden büyük hesaplıyordu ( 120 m seyirde 20,7 kW
    #  yerine 39,3 kW ).  %0 = zincir yok  ·  %100 = tam dengeleme.
    ("denge_zinciri",     "",     "Denge ( kompanzasyon ) zinciri",     "—",    "secim",
     ("Yok", "Var"), "Yok"),
    ("halat_birim_kutle", "",     "Askı halatı 1 m ağırlığı  ( imalatçı — boşsa tablo )",
     "kg/m", "sayi", None, None),
    ("halat_kopma_kN",    "",     "Askı halatı en küçük kopma yükü  ( imalatçı — boşsa tablo )",
     "kN", "sayi", None, None),
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
    #  KATALOG VERİSİ ASKI HALATINDA VARDI, REGÜLATÖRDE YOKTU.  TS 12385-5
    #  tablosu yalnız LİF ÖZLÜ halatları kapsar;  regülatör halatları çoğu
    #  zaman çelik özlüdür ve kopma yükleri belirgin biçimde yüksektir
    #  ( 6 mm:  tablo 23,1 kN — piyasadaki çelik özlü 28 kN ).  Program bu
    #  yüzden UYGUN tasarımları reddedebiliyordu.  Boş bırakılırsa tablo.
    ("reg_halat_birim_kutle", "", "Regülatör halatı 1 m ağırlığı  ( imalatçı — boşsa tablo )",
     "kg/m", "sayi", None, None),
    ("reg_halat_kopma_kN", "",   "Regülatör halatı en küçük kopma yükü  ( imalatçı — boşsa tablo )",
     "kN",   "sayi", None, None),
    #  TS EN 81-20 m.5.6.2.2.1.1 d):  regülatörün ürettiği çekme kuvveti,
    #  "güvenlik tertibatını devreye sokmak için GEREKENİN İKİ KATI" ile
    #  300 N'un BÜYÜĞÜNDEN az olamaz.  O kuvvet İMALATÇI VERİSİDİR;  kitap
    #  onun yerine halatın kendi statik gergisinin iki katını koyuyordu
    #  ( bkz. EXCEL_FARKLARI ).  Boş bırakılırsa yalnız 300 N sınırı
    #  denetlenir ve pafta eksiği açıkça yazar.
    ("guvenlik_devreye_kuvvet", "", "Güv. tertibatını devreye sokma kuvveti  ( imalatçı )",
     "N", "sayi", None, None),
    #  Tst — SEÇİLEN makinenin tahrik kasnağına izin verdiği azami STATİK yük
    #  ( imalatçı kataloğu ).  Motor gücü "UYGUN" çıkıp kasnak yükü aşılmış bir
    #  makine seçilebiliyordu:  hiçbir şey bakmıyordu.  Boş bırakılırsa kontrol
    #  yapılmaz ve pafta bunu açıkça yazar.
    #  ── MAKİNE YÜKÜNÜN YOLU  ( TS EN 81-20 m.5.7.2.3.7 ) ──────────────
    #  "If the machine or rope suspensions are FIXED TO THE GUIDE RAILS,
    #   additional load cases according to the Table 13 shall be considered."
    #  m.5.2.1.8.4 aynı durumu kuyu tabanı için de anar:  "...load on traction
    #  sheave due to rebound WHEN MACHINE ON RAILS".
    #
    #  Makine dairesiz ( MRL ) tesiste makine kuyunun üstündedir ve yükü ya
    #  RAYLARA ya da BİNA YAPISINA iner.  Standart makinenin nereye
    #  oturabileceğine dair kapalı bir liste vermez — m.5.2.1.8.1 "yapı
    #  taşıyacak, ayrıntısı ulusal yapı yönetmeliğinde" der.  Hesabı
    #  değiştiren TEK ayrım, yükün asansörün KENDİ parçasına ( raya ) değip
    #  değmediğidir.
    #
    #  KİRİŞ TEK BAŞINA CEVAP DEĞİLDİR:  makinenin altındaki platformun
    #  uçları raylara cıvatalıysa yük yine raya iner — "Kılavuz raylara".
    #
    #  ONAY KUTUSU DEĞİL, AÇIK SEÇİM.  İşaretsiz bir kutu SESSİZ VARSAYIMDIR:
    #  kullanıcı dokunmadığında program onun adına "bina yapısına" diye karar
    #  vermiş oluyordu ve bu yalnız paftadaki uyarı satırında görünüyordu.
    #  Seçim olarak sorulunca hangi yolun kabul edildiği HESAP SATIRI olur.
    #  ( Eski projeler ve Excel kitapları True/'EVET' taşır;  MT.makine_raya_mi
    #    ikisini de anlar. )
    ("makine_raya_biniyor", "",   "Makine yükünün yolu",
     "—",    "secim", MT.MAKINE_YUK_YOLU, MT.MAKINE_YUK_YOLU[0]),
    #  RAY BAŞINA okunur — m.5.7.2.3.7 Maux'u "per guide rail" diye tanımlar.
    #  Boş bırakılırsa ( Gm + Tst ) / ray sayısı olarak TÜRETİLİR:  makinenin
    #  kendi ağırlığı + tahrik kasnağına gelen statik yük, iki kabin rayına
    #  simetrik paylaşılmış kabul edilir.  Asimetrik bağlantıda ya da yükün
    #  bir kısmı duvara gidiyorsa imalatçının verdiği BİR RAYA DÜŞEN sayı
    #  buraya yazılır ( ELEport:  "calculated separately, the larger value
    #  should be taken" ).
    ("raya_binen_yuk",    "",     "Bir raya düşen makine yükü  ( imalatçı — boşsa türetilir )",
     "kg",   "sayi", None, None),
    ("makine_tst",        "",     "Tst — makinenin azami kasnak statik yükü  ( imalatçı )",
     "kg", "sayi", None, None),
    #  TS EN 81-20 m.5.6.2.2.1.1 a):  devreye girme hızı beyan hızının en az
    #  %115'i ve tertibat tipine göre belirlenen üst sınırın ALTINDA olmalı.
    #  Değer regülatörün TİP İNCELEME belgesinden gelir.
    ("reg_devreye_hizi",  "",     "Regülatör devreye girme hızı  ( imalatçı )", "m/s", "sayi", None, None),

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
    #  "Ofis verimi η toplam sistem verimidir" ANAHTARI KALDIRILDI.
    #  η artık HER ZAMAN toplam sistem verimidir ( askı kaybı içinde ) —
    #  seçilecek bir şey kalmadı.  Bkz. engine/ortak/ofis.py, "PALANGA VERİM
    #  DÜŞÜŞÜ KALDIRILDI".  Eski projelerin JSON'unda kalan toplam_verim
    #  anahtarı yok sayılır, geri yükleme bozulmaz.
    ("kabin_paten_arasi", "B127", "Kabin paten arası",                 "mm",   "sayi", None, 3400),
    ("agirlik_paten_arasi", "B128", "Ağırlık paten arası",             "mm",   "sayi", None, 3400),
    ("guvenlik_tertibati", "G36", "Güvenlik tertibatı ( fren bloğu ) tipi", "—", "secim",
     MT.DARBE_TIPLERI_ADLARI, "Kaymalı"),
    #  SIĞINMA HACMİ TİPİ  ( TS EN 81-20 m.5.2.5.7.1 · m.5.2.5.8.1 ).
    #  Standart üç duruştan BİRİNİ ister;  program bunu bilmiyor, ÇÖMELME
    #  tipini koda çivilemişti ve yatarak tipiyle uygun olan tesislere
    #  "UYGUN DEĞİL" diyordu.  Beyan edilen tip paftaya yazılır.
    ("siginma_tipi_ust",  "",     "Kabin üstü sığınma hacmi tipi",     "—",    "secim",
     MT.SIGINMA_TIPLERI_UST, "Çömelme"),
    ("siginma_tipi_dip",  "",     "Kuyu dibi sığınma hacmi tipi",      "—",    "secim",
     MT.SIGINMA_TIPLERI_DIP, "Çömelme"),
    #  TS EN 81-50 m.5.10.5 flanş eğilmesindeki ℓ.  Kaynak Excel'de karşılığı
    #  YOKTUR ( oraya 1 yazılıdır ), bu yüzden hücre alanı boştur.  Boş
    #  bırakılırsa ray tablosundaki balata yarı genişliğinden türetilir.
    ("paten_balata_boyu", "", "Paten balatası uzunluğu  ( ℓ )",  "mm",   "sayi", None, None),
    #  TS EN 81-50 m.5.10.5 / Ek C.2.1.4 flanş eğilmesi için İKİ formül verir:
    #  makaralı patende 1,85·Fx/c² , kaymalı patende balata boyuna bağlı olan.
    #  Kitap yalnız kaymalıyı tanıyordu.
    ("paten_tipi",        "",     "Paten tipi",                        "—",    "secim",
     _s("Kaymalı", "Makaralı"), "Kaymalı"),
    #  Ek C.2.1.2 / C.2.2.2 / C.2.3.2:  Fv = … + Fp.  Fp, bir raydaki bütün
    #  konsol klipslerinin itme kuvvetidir ( binanın oturması, betonun
    #  büzülmesi ).  Kitapta hiç yoktu;  varsayılan 0, değeri tesise bağlıdır.
    ("klips_itme_kuvveti", "",    "Fp ( konsol klipslerinin itme kuvveti )", "N", "sayi", None, 0),
    #  Ek C.2.1.5 / C.2.2.5 / C.2.3.5:  δ = 0,7·F·l³/(48·E·I) + δstr.
    #  δstr binanın kendi sehimidir;  kitapta hiç yoktu, varsayılan 0.
    ("yapi_sehim_x",      "",     "δstr-x ( bina yapısının x sehimi )", "mm",   "sayi", None, 0),
    ("yapi_sehim_y",      "",     "δstr-y ( bina yapısının y sehimi )", "mm",   "sayi", None, 0),

    # ── KARŞI AĞIRLIK ─────────────────────────────────────────────────
    ("agirlik_malzemesi", "B118", "Karşı ağırlık malzemesi",           "—",    "secim",
     MT.AGIRLIK_MALZEMELERI, "Barit"),
    #  KARŞI AĞIRLIĞIN KENDİ İKİ ÖLÇÜSÜ  —  TS EN 81-50 Ek C.2.2'nin Gx · Gy
    #  Eksantriklikler bunlardan çıkar:  Dxa = %10 × derinlik ( Gx ),
    #  Dya = %5 × genişlik ( Gy ).  Standardı izleyen ray hesabı kılavuzu da
    #  ikisini VERİ olarak alır ( "Gx = 130 mm, Gy = 960 mm Counterweight
    #  dimensions" ), referans uygulama projesi de doğrudan sorar.
    #
    #  ESKİDEN TÜRETİLİYORLARDI ve ikisi de yanlıştı:  genişlik ray arasından
    #  ( üç değere kilitli açılır liste ), derinlik malzemeden.  Ölçü ne ray
    #  arasının ne malzemenin özelliğidir — imal edilen ÇERÇEVENİN özelliğidir.
    #  Program kabin tarafında zaten böyle yapıyor ( kabin_genisligi ·
    #  kabin_derinligi ).
    ("agirlik_genisligi",  "",     "Karşı ağırlık genişliği  ( Gy )", "mm", "sayi", None, 960),
    ("agirlik_derinligi",  "",     "Karşı ağırlık derinliği  ( Gx )", "mm", "sayi", None, 150),
    #  Ray arası PAFTA BİLGİSİDİR.  Mukavemet hesabına girmez ( standartta
    #  ray arası → genişlik diye bir bağıntı yoktur );  kuyu yerleşimine ve
    #  inşaat projesine ait bir ölçü olduğu için sorulmaya devam eder.
    ("agirlik_ray_arasi", "B119", "Ağırlık ray arası  ( pafta bilgisi )", "mm", "sayi", None, 1050),
    #  TS EN 81-20 m.5.6.1:  karşı ağırlıkta güvenlik tertibatı, kuyunun
    #  altındaki hacme girilebiliyorsa ZORUNLUDUR.  Varsa ağırlık rayı
    #  TS EN 81-50 Ek C.2.1'e göre de ( k1 darbe katsayısıyla ) hesaplanmalıdır;
    #  kitap yalnız C.2.2'yi ( normal işletme ) kuruyordu.
    ("agirlik_guvenlik_tertibati", "", "Karşı ağırlıkta güvenlik tertibatı", "—", "secim",
     ("Yok",) + MT.DARBE_TIPLERI_ADLARI, "Yok"),

    # ── TAMPONLAR ─────────────────────────────────────────────────────
    #  TİP, KONTROLÜN KENDİSİNİ SEÇER.  TS EN 81-20 m.5.8.1 tamponları üçe
    #  ayırır ve her birine başka bir kural bağlar ( strok formülü, hız
    #  sınırı );  tip sorulmadan bu kuralların hiçbiri denetlenemiyordu.
    #  Kaynak kitapta bu alan yoktur — ofis poliüretan kullanıyor, varsayılan
    #  odur ( teslim kopyasına ayrı blokta yazılır ).
    ("tampon_tipi",         "",     "Tampon tipi",                     "—",    "secim",
     MT.TAMPON_TIPLERI_ADLARI, MT.TAMPON_TIPLERI_ADLARI[1]),
    #  ADET, KUYU TABANINA DÜŞEN KUVVETİ BÖLER.  m.5.2.1.8.5 kuvveti
    #  "evenly distributed between the total number of car buffers" der:
    #  toplam 4·gn·(P+Q)'dur ama döşemenin TAŞIYACAĞI şey tampon BAŞINA
    #  düşendir.  Kaynak kitapta bu alan yok, toplam kuvvet veriliyordu.
    ("kabin_tampon_adedi",  "",     "Kabin tamponu adedi",             "adet", "sayi", None, 1),
    ("agirlik_tampon_adedi", "",    "Ağırlık tamponu adedi",           "adet", "sayi", None, 1),
    ("kabin_tampon_baba",   "F118", "Kabin tamponu baba yüksekliği",   "mm",   "sayi", None, 1000),
    ("agirlik_tampon_baba", "F119", "Ağırlık tamponu baba yüksekliği", "mm",   "sayi", None, 300),
    ("kabin_tampon_ezilme", "B121", "Kabin tamponu ezilme miktarı",    "mm",   "sayi", None, 90),
    ("kabin_carpma_arasi",  "B122", "Kabin tamponu - çarpma plakası arası", "mm", "sayi", None, 150),
    ("kabin_tampon_boyu",   "B123", "Kabin tamponu uzunluğu",          "mm",   "sayi", None, 100),
    ("agirlik_tampon_ezilme", "B124", "Ağırlık tamponu ezilme miktarı", "mm",  "sayi", None, 90),
    ("agirlik_carpma_arasi", "B125", "Ağırlık tamponu - çarpma plakası arası", "mm", "sayi", None, 150),
)

#  İŞARETLİ ( NEGATİF OLABİLEN ) ALANLAR
#  TS EN 81-50 Ek C.1.2 ray eksenini ORİJİN alan bir Kartezyen sistem kurar:
#  kabin merkezi, boş kabin kütlesi, beyan yükü, askı ve kapı konumları bu
#  eksene göre İŞARETLİ koordinatlardır.  Ray ekseninin bir yanı artı, öbür
#  yanı eksidir ve işaret momentin YÖNÜNÜ belirler — C.2.2.1'in ( yp − ys )
#  kolu, iki nokta ray ekseninin ayrı yanlarındaysa büyür, aynı yanındaysa
#  küçülür.  Bu alanları "negatif olamaz" saymak, kaçıklığı yalnız tek yöne
#  izin vermek demekti;  ELEport'un örnek projesinde de Yp = −15,0 cm'dir.
#
#  ÖTEKİ ALANLAR NEGATİF OLAMAZ:  uzunluk, kütle, çap, sehim ve adet
#  büyüklüktür, işareti yoktur.
ISARETLI_ALANLAR = ("kabin_kaciklik", "aski_kaciklik_x", "aski_kaciklik_y")

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

#  kabin_agirligi BURADA DEĞİLDİR:  tamamla() onu ofis tablosundan doldurur
#  ve doldurma bir tek beyan yükü geçersizken başarısız olur — o durumda
#  "boş bırakılamaz" hatası çıkmalı, hesap None ile devam etmemelidir.
OPSIYONEL_ALANLAR = ("asansor_adi",
                     "paten_balata_boyu", "guvenlik_devreye_kuvvet",
                     "reg_devreye_hizi", "makine_tst",
                     "halat_birim_kutle", "halat_kopma_kN",
                     "reg_halat_birim_kutle", "reg_halat_kopma_kN",
                     "raya_binen_yuk",
                     "saptirma_kasnak_min_capi")

#  TS EN 81-20 m.5.6.2.2.1.3 b):  kaymalı ( traction ) hız regülatörü için
#  hesaba katılacak azami sürtünme katsayısı.
REG_MU_AZAMI = 0.2

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
    #  iy DE ARANIR:  burkulma en küçük atalet yarıçapından hesaplanır
    #  ( bkz. mukavemet._makine ), eksik profil sessizce geçmemelidir.
    ("dikine_kiris", [("A", lambda x: MT.npu(x, "A")),
                      ("ix", lambda x: MT.npu(x, "ix")),
                      ("iy", lambda x: MT.npu(x, "iy"))], "kesit değerleri"),
    ("yan_yatak", [("Wx", lambda x: MT.npu(x, "Wx"))], "kesit değerleri"),
    ("halat_capi", [("1 m ağırlığı", MT.halat_agirlik),
                    ("kopma yükü", MT.halat_kopma)], "halat verisi"),
    ("reg_halat_capi", [("1 m ağırlığı", MT.halat_agirlik),
                        ("kopma yükü", MT.halat_kopma)], "halat verisi"),
    #  Nequiv(t) artık şeklin adından değil, ofis açılarından hesaplanır
    #  ( EN 81-50 Çizelge 2 );  burada yalnız şeklin TANINDIĞI denetlenir.
    ("kanal_sekli", [("kanal türü", MT.kanal_turu)], "kasnak verisi"),
    ("guvenlik_tertibati", [("k1", MT.darbe_k1)], "darbe katsayısı"),


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
     ("asansor_adi", "beyan_yuku", "beyan_hizi", "seyir_mesafesi",
      "kabin_agirligi", "aski_orani")),
    ("Kabin ve kapı",
     ("kabin_genisligi", "kabin_derinligi", "kat_kapisi_tipi", "kapi_genisligi",
      "uzun_pervaz",
      "kabin_kaciklik", "aski_kaciklik_x", "aski_kaciklik_y",
      "agirlik_yeri", "kapi_agirligi", "kapi_mekanizma_payi")),
    ("Durak ve kuyu",
     ("durak_yukseklikleri", "son_kat_yuksekligi", "kaide_yuksekligi",
      "kuyu_dibi", "kuyu_derinligi", "ray_kapi_arasi", "agirlik_ray_duvar",
      "siginma_tipi_ust", "siginma_tipi_dip")),
    ("Makine ve motor",
     ("motor_gucu", "makine_agirligi", "sap_kasnak_yuk", "makine_yatak_yuk",
      "tahrik_kasnak_capi", "saptirma_kasnak_capi",
      "saptirma_kasnak_min_capi", "sase_yuksekligi",
      "dikine_kiris", "dikine_kiris_tipi", "yan_yatak", "yan_yatak_tipi",
      "yan_yatak_boyu", "makine_tipi", "makine_tst",
      "makine_raya_biniyor", "raya_binen_yuk")),
    ("Askı halatları",
     ("halat_adedi", "halat_capi", "kanal_sekli", "kanal_isleme",
      "halat_birim_kutle", "halat_kopma_kN", "denge_zinciri",
      "halat_arasi_yan", "kasnak_tek_yon", "kasnak_ters_yon",
      "acil_frenleme_a", "kablo_tipi_1")),
    ("Hız regülatörü",
     ("reg_halat_capi", "reg_kasnak_capi", "reg_kanal_acisi", "reg_surtunme",
      "reg_gergi_agirligi", "reg_halat_birim_kutle", "reg_halat_kopma_kN",
      "guvenlik_devreye_kuvvet", "reg_devreye_hizi")),
    ("Kılavuz raylar",
     ("kabin_ray_profili", "agirlik_ray_profili", "kabin_konsol_arasi",
      "agirlik_konsol_arasi", "kabin_ray_sayisi", "agirlik_ray_sayisi",
      "ray_celigi_rm", "kabin_paten_arasi", "agirlik_paten_arasi",
      "guvenlik_tertibati", "paten_balata_boyu", "paten_tipi",
      "klips_itme_kuvveti", "yapi_sehim_x", "yapi_sehim_y")),
    ("Karşı ağırlık", ("agirlik_genisligi", "agirlik_derinligi",
                       "agirlik_malzemesi", "agirlik_ray_arasi",
                       "agirlik_guvenlik_tertibati")),
    ("Tamponlar",
     ("tampon_tipi", "kabin_tampon_adedi", "agirlik_tampon_adedi",
      "kabin_tampon_baba", "agirlik_tampon_baba", "kabin_tampon_ezilme",
      "kabin_carpma_arasi", "kabin_tampon_boyu", "agirlik_tampon_ezilme",
      "agirlik_carpma_arasi")),
)


#  HESAP BÖLÜMÜ  →  onu besleyen GİRDİ GRUPLARI.
#  Revizyonda mühendis "halat bölümü kaldı, neyi değiştireceğim" diye
#  düşünür — girdi grubunun adıyla değil, HESAP BÖLÜMÜYLE.  Arayüz, sonuç
#  tablosundaki bir bölüme tıklandığında doğrudan onun girdilerini açar.
#  Eşleme burada durur çünkü hangi girdinin hangi hesaba girdiği MOTORUN
#  bilgisidir;  arayüzde tutulursa motor değişince sessizce bayatlar.
#
#  ANAHTAR BÖLÜMÜN KİMLİĞİDİR, NUMARASI DEĞİL.  Bir süre numara ( "4" )
#  kullanılıyordu ve bu iki yerden birden bozuktu:  numara projeye göre
#  kayıyor ( makine dairesi yoksa topraklama bir sıra öne geliyor ), bu
#  yüzden proje geneli bölümler hiç eşlenemiyordu;  ayrıca elektrik
#  bölümlerini eşlemek için "mukavemet 10 bölümdür, elektrik 11'den başlar"
#  varsayımını ikinci bir dosyaya gömmek gerekiyordu.  Kimlik bölümün
#  doğduğu yerde verilir ve hiç değişmez ( bkz. ortak/steps.Bolum ).
#
#  Sıra ÖNEM SIRASIDIR:  ilk grup bölümün ana girdilerini taşır, ikincisi o
#  bölümün kontrollerinden en az birini tek başına belirleyen ikinci gruptur.
#  İkiyle sınırlıdır — üç grup açmak akordeonu listeye çevirir ve aranan alan
#  yine kaybolur.  Listeler, motor kodundaki g[...] okumaları taranarak
#  çıkarılmıştır ve test_uygulama bunu her koşuda yeniden denetler.
BOLUM_GRUBU = {
    #  bölüm kimliği             asıl grup            ikinci grup
    "motor_gucu":            ("Makine ve motor", "Askı halatları"),
    "makine_konstruksiyonu": ("Makine ve motor",),
    "kabin_alani":           ("Kabin ve kapı",),
    "aski_halatlari":        ("Askı halatları", "Makine ve motor"),
    "regulator_halati":      ("Hız regülatörü",),
    "tahrik_yetenegi":       ("Askı halatları", "Makine ve motor"),
    "kabin_raylari":         ("Kılavuz raylar", "Kabin ve kapı"),
    "agirlik_raylari":       ("Kılavuz raylar", "Karşı ağırlık"),
    #  TAMPONLAR DEĞİL.  Bölüm tampon KUVVETLERİNİ ( Fkt · Fat ) verir ama
    #  bunlar kütle × g'dir;  tampon geometrisi ( baba yüksekliği · ezilme ·
    #  uzunluk ) kuvvete girmez.  Pertürbasyon taraması Tamponlar grubundaki
    #  yedi alanın da bu bölümü hiç değiştirmediğini gösterdi.
    "kuyu_tabani":           ("Kılavuz raylar", "Karşı ağırlık"),
    "tamponlar":             ("Tamponlar", "Asansör teknik bilgileri"),
    "siginma_alanlari":      ("Durak ve kuyu", "Tamponlar"),
}


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
    return {"gruplar": gruplar,
            "bolum_grubu": {no: list(gr) for no, gr in BOLUM_GRUBU.items()},
            #  MALZEME → ALIŞILMIŞ DERİNLİK.  Bu bir HESAP tablosu DEĞİL,
            #  formun başlangıç değeridir:  malzeme seçilince derinlik kutusu
            #  bu sayıyla dolar, mühendis üzerine yazabilir ve hesap her
            #  hâlükârda KUTUDAKİ sayıyı okur.  Eskiden motor derinliği
            #  malzemeden türetiyordu;  o türetme kaldırıldı ( TS EN 81-50
            #  Ek C.2.2 ölçüyü veri olarak ister ), ama seçim yapınca ekranda
            #  hiçbir şeyin değişmemesi sessiz bir tuzaktı.
            "malzeme_derinligi": {r[0]: r[1] for r in MT.AGIRLIK_MALZEMESI},
            "durak_azami": DURAK_AZAMI,
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
    #  BOŞ KABİN KÜTLESİ:  girilmemişse ofis tablosundan doldurulur.
    #  Kaynak kitapta bu hücre ( C75 ) elle doldurulur;  program aynı tabloyu
    #  avan tarafında da kullandığı için iki proje aynı asansöre aynı kütleyi
    #  verir.  Elle girilen değer HER ZAMAN önceliklidir.
    by = g.get("beyan_yuku")
    if g.get("kabin_agirligi") is None or (
            isinstance(g.get("kabin_agirligi"), str)
            and not g["kabin_agirligi"].strip()):
        g["kabin_agirligi"] = OFIS.bos_kabin_kutlesi(by)
        g["kabin_agirligi_kaynak"] = OFIS.GK_KAYNAGI
    elif not (g.get("kabin_agirligi_kaynak") == OFIS.GK_KAYNAGI
              and g.get("kabin_agirligi") == OFIS.bos_kabin_kutlesi(by)):
        # Tekrar tamamlanırken otomatik değerin kaynağını koru.
        # Kütle değiştirilmişse artık elle girilen değerdir.
        g["kabin_agirligi_kaynak"] = "GİRİŞ"
    ka = g.get("kabin_agirligi")
    #  KARŞI AĞIRLIK DENGE ORANI OFİS SABİTİDİR.
    #  Kaynak kitabın C80 formülü "kabin ağırlığı + beyan yükü / 2" diye
    #  ÇİVİLİDİR;  ofis q'yu değiştirse bile 0,50 kalır.  Oysa bölüm 1
    #  Ga'yı  P + q·Q  ile kurar.  q = 0,60'ta aynı projede İKİ FARKLI karşı
    #  ağırlık oluşuyordu:  motor ve ağırlık tamponu 1.180 kg, tahrik ve
    #  ağırlık rayı 1.100 kg.  Aynı fiziksel parçanın kütlesi her hesapta
    #  aynı olmalıdır.
    from engine.uygulama import sabitler as _US
    # Motor, tahrik ve tampon aynı doğrulanmış denge oranını kullanmalı.
    # Ham sözlüğü koru: reddedilen girdiler uyarılarda gösterilmeye devam eder.
    q = _US.sabitler(g.get("_ofis"))["q_denge"]
    if _sayi(ka) and _sayi(by):
        g["karsi_agirlik"] = ka + q * by
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
    #  ESKİ BİÇİM:  makine yükünün yolu bir zamanlar ONAY KUTUSUYDU ve
    #  True / "EVET" olarak kaydediliyordu.  Eski .uygulama dosyaları ve
    #  teslim edilmiş Excel kitapları bu değeri taşır;  seçime çevrilmezse
    #  doğrulama "geçersiz seçim — True" deyip projeyi hiç açmaz.
    _yy = g.get("makine_raya_biniyor")
    if _yy is not None and _yy not in MT.MAKINE_YUK_YOLU:
        g["makine_raya_biniyor"] = (MT.MAKINE_YUK_YOLU[1]
                                    if MT.makine_raya_mi(_yy)
                                    else MT.MAKINE_YUK_YOLU[0])
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
        if tur == "sayi" and not _sayi(d):
            hata.append(f"{ad}: sayı olmalı ( {d!r} girildi ).")
        elif tur == "sayi" and d < 0 and anahtar not in ISARETLI_ALANLAR:
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
    nh = g.get("halat_adedi")
    if _sayi(nh) and nh < 2:
        hata.append("Askı halatı adedi en az 2 olmalıdır "
                    "(TS EN 81-20 m.5.5.1.3).")
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

    #  OPSİYONEL ALANLARIN POZİTİFLİK VE FİZİKSEL SINIRLARI
    #  Boş bırakılabilirler;  ama girilmişse pozitif ve fiziksel olmalıdır.
    #  paten_balata_boyu = 0 girildiğinde motor bunu sessizce türetilene
    #  çeviriyor, 0,001 mm girildiğinde ise formül paydası pozitif kaldığı
    #  için mikroskobik balatayla "UYGUN" çıkıyordu.
    #  ( 20 mm alt sınırı standart maddesi değil;  yazılımsal koruma, sınır
    #  değer kontrolü / sanitization ve fiziksel tutarlılık kalkanıdır. )
    pbb = g.get("paten_balata_boyu")
    if pbb is not None and pbb != "":
        if not _sayi(pbb) or pbb <= 0:
            hata.append(f"{ALAN['paten_balata_boyu'][2]}: sıfırdan büyük olmalıdır ( {pbb!r} girildi ).")
        elif pbb < 20:
            hata.append(f"Paten balatası uzunluğu ({pbb:g} mm) fiziksel değil — balata boyu en az 20 mm olmalıdır.")
        else:
            kpa = g.get("kabin_paten_arasi")
            if _sayi(kpa) and pbb >= kpa:
                hata.append(f"Paten balatası uzunluğu ({pbb:g} mm) kabin patenler arası mesafeden ({kpa:g} mm) küçük olmalıdır.")
    gdk = g.get("guvenlik_devreye_kuvvet")
    if gdk is not None and gdk != "":
        if not _sayi(gdk) or gdk <= 0:
            hata.append(f"{ALAN['guvenlik_devreye_kuvvet'][2]}: sıfırdan büyük olmalıdır ( {gdk!r} girildi ).")

    #  KATALOG HALAT VERİSİ ve Tst — hepsi opsiyoneldir, girilirse MAKUL olmalı.
    #  Kopma yükü alanı kN'dir:  katalog "31,5 kN" der, projeci 31500 yazarsa
    #  güvenlik katsayısı 1000 kat büyür ve HER tasarım "UYGUN" görünürdü.
    #  Üst sınır o hatayı yakalar.
    for _ad, _alt, _ust in (("halat_birim_kutle", 0.02, 5.0),
                            ("halat_kopma_kN", 5.0, 2000.0),
                            ("reg_halat_birim_kutle", 0.02, 5.0),
                            ("reg_halat_kopma_kN", 5.0, 2000.0),
                            ("makine_tst", 100.0, 100000.0),
                            ("raya_binen_yuk", 1.0, 50000.0),
                            ):
        _v = g.get(_ad)
        if _v is None or _v == "":
            continue
        if not _sayi(_v) or not (_alt <= _v <= _ust):
            hata.append(f"{ALAN[_ad][2]}: {_alt} - {_ust} aralığında olmalıdır "
                        f"( {_v!r} girildi ).")

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

    #  ------------------------------------------------------------------
    #  RAY NARİNLİĞİ  λ = konsol arası / ix        TS EN 81-50 m.5.10.3
    #  ------------------------------------------------------------------
    #  TAHRİK KASNAĞI GEOMETRİSİ            TS EN 81-50 m.5.11.2 / m.5.11.3
    #  ------------------------------------------------------------------
    #  Sarılma açısı α = 180° − arctan( ( Ra − 2·R1 ) / B ) bağıntısı TEK
    #  SARIMLI bir tahrik kasnağını modeller:  halat kasnağın iki yanından
    #  aşağı iner ve α en çok 180° olur.  Ra < 2·R1 girildiğinde pay
    #  negatife düşüyor, α 180°'yi aşıyordu ( Ra = 100 mm'de 187,65° ) ve
    #  hesap sorunsuz devam ediyordu.  Yön EMNİYETSİZDİR:  e^(f·α) sınırı
    #  α ile büyür, yani tahrik yeteneği olduğundan iyi çıkar.
    Ra, Dt = g.get("halat_arasi"), g.get("tahrik_kasnak_capi")
    if _sayi(Ra) and _sayi(Dt) and Dt > 0 and Ra < Dt:
        hata.append(
            f"Halat arası ({Ra:g} mm) tahrik kasnağı çapından ({Dt:g} mm) küçük "
            "olamaz. Tek sarımlı kasnakta halatlar kasnağın iki yanından "
            "teğet iner; halat arası en az kasnak çapı kadardır. Daha küçük "
            "bir değer sarılma açısını 180°'nin üstüne çıkarır ve tahrik "
            "yeteneğini olduğundan İYİ gösterir."
            + ("  ( Karşı ağırlık arkada:  halat arası KD − RK − ray-duvar'dan "
               "hesaplanır. )" if g.get("agirlik_yeri") == "Arka" else ""))

    #  ------------------------------------------------------------------
    #  SİSTEM VERİMİ  η  FİZİKSEL OLMALI             0 < η ≤ 1
    #  ------------------------------------------------------------------
    #  Δη kalktığı için η artık kendi başına negatife düşemez;  bu kalkan
    #  yine de durur, çünkü ofis sabiti ekrandan elle girilir ve ARALIK
    #  ( 0,1 - 1 ) atlanırsa N = Gmax·v/(η·102) sıfıra bölünür.
    from engine.uygulama import sabitler as _USv
    _O = _USv.sabitler(g.get("_ofis"))
    _tip = g.get("makine_tipi")
    _etap = _USv.verim(_O, _tip)
    if not (_sayi(_etap) and 0 < _etap <= 1):
        hata.append(
            f"Toplam sistem verimi η = {_etap} fiziksel değil — 0 < η ≤ 1 "
            f"olmalı ( '{_tip}' makine ). Sabitler sekmesinden düzeltin.")

    #  ------------------------------------------------------------------
    #  HALAT BOYU POZİTİF OLMALI  —  tampon / paten yığını kuyuya sığmalı
    #  ------------------------------------------------------------------
    #  lh = ( kuyu boyu − yığın ) / 1000 + pay.  Yığın kuyu boyunu aşarsa
    #  halat boyu NEGATİF çıkıyor ( 30 m paten arasında −4,82 m ) ve halat
    #  ağırlığı Gh = −5,13 kg oluyor.  Negatif ağırlık yükten DÜŞÜLÜYOR:
    #  motor gücünü azaltıyor, halat güvenlik katsayısını yükseltiyor —
    #  yani imkânsız bir geometri hesabı İYİLEŞTİRİYORDU.
    _yigin_ad = ("agirlik_tampon_baba", "agirlik_carpma_arasi",
                 "agirlik_tampon_ezilme", "agirlik_paten_arasi",
                 "kabin_paten_arasi")
    _y = {a: g.get(a) for a in _yigin_ad}
    _kb = g.get("kuyu_boyu")
    if _sayi(_kb) and all(_sayi(v) for v in _y.values()):
        _yigin = (_y["agirlik_tampon_baba"] + _y["agirlik_carpma_arasi"]
                  - _y["agirlik_tampon_ezilme"] + _y["agirlik_paten_arasi"]
                  + _y["kabin_paten_arasi"])
        if _kb - _yigin <= 0:
            hata.append(
                f"Tampon / paten yığını ({_yigin:g} mm) kuyu boyundan "
                f"({_kb:g} mm) büyük — halat boyu negatif çıkar. "
                "Toplama giren ölçüler:  ağırlık tampon babası "
                f"{_y['agirlik_tampon_baba']:g} + ağırlık çarpma arası "
                f"{_y['agirlik_carpma_arasi']:g} − ağırlık tampon ezilmesi "
                f"{_y['agirlik_tampon_ezilme']:g} + ağırlık paten arası "
                f"{_y['agirlik_paten_arasi']:g} + kabin paten arası "
                f"{_y['kabin_paten_arasi']:g}.")

    #  ------------------------------------------------------------------
    #  REGÜLATÖR SÜRTÜNME KATSAYISI       TS EN 81-20 m.5.6.2.2.1.3 b)
    #  ------------------------------------------------------------------
    #  Standart bu hesap için sürtünme katsayısının ÜST DEĞERİNİ kendisi
    #  verir:  "taking into account a friction factor µmax equal to 0,2 for
    #  traction type overspeed governor".  Alan sınırsızdı;  μ = 5 gibi bir
    #  değer kabul ediliyordu.
    mu = g.get("reg_surtunme")
    if _sayi(mu) and mu > REG_MU_AZAMI:
        hata.append(f"Regülatör sürtünme katsayısı ({mu:g}) TS EN 81-20 "
                    f"m.5.6.2.2.1.3 b)'nin verdiği µmax = {REG_MU_AZAMI:g} "
                    "değerini aşamaz.")
    return hata


def uyarilar(g):
    """Hesabı DURDURMAYAN ama paftaya yazılması gereken uyarılar.

    ``dogrula`` hesabı imkânsız kılan girdileri reddeder;  burası hesabın
    yapılabildiği ama bir kontrolün DÜŞECEĞİ durumları bildirir.  İkisi ayrı
    kanaldır:  biri projeyi hiç hesaplatmaz, öteki sonucu "uygun değil"
    yapar ve sebebini yazar.
    """
    uyari = []
    #  ------------------------------------------------------------------
    #  MAKİNE DAİRESİZ TESİSTE MAKİNENİN YÜKÜ BİR YERE GİDER.
    #  TS EN 81-20 m.5.7.2.3.7 makine raya bağlıysa EK YÜK DURUMLARI ister.
    #  Kutu işaretsizse program yükü BİNA YAPISINA verilmiş kabul eder ve
    #  raya yalnız ofis kabulü olan ufak donanımı ( 150 N ) koyar.  Bu bir
    #  KABULDÜR ve sessiz kalmamalıdır:  makine gerçekten raylara biniyorsa
    #  ray ve kuyu tabanı yükü olduğundan küçük çıkar.
    #  ------------------------------------------------------------------
    #  Makine dairesi VARKEN kutu işaretliyse seçim yok sayılır — sessiz
    #  kalmamalı, çünkü kullanıcı işaretlediğini sanır.
    if not evet_mi(g.get("mk_yok")) and MT.makine_raya_mi(g.get("makine_raya_biniyor")):
        uyari.append(
            "'Makine yükü kılavuz raylara biniyor' seçimi YOK SAYILDI — proje "
            "makine daireli. Makine kendi kaidesinde durur ve yükü bölüm "
            "2'de hesaplanır; aynı yükü raya da bindirmek onu iki kez sayardı. "
            "Seçim ancak 'Makine dairesiz ( MRL )' işaretliyken uygulanır.")
    if evet_mi(g.get("mk_yok")) and not MT.makine_raya_mi(g.get("makine_raya_biniyor")):
        uyari.append(
            "MAKİNE YÜKÜ BİNA YAPISINA AKTARILIYOR — makine dairesiz ( MRL ) "
            "sistemde makinenin yükü kuyu üstü kirişe, duvara ya da konsola "
            "iner ve bu yapı TS EN 81-20 m.5.2.1.8.1 ile Ek E uyarınca İNŞAAT "
            "PROJESİNDE hesaplanır;  paftada verilen yük o hesabın girdisidir. "
            "Makinenin ya da altındaki kirişin uçları kılavuz raylara "
            "bağlıysa 'Makine yükünün yolu' alanından 'Kılavuz raylara' "
            "seçilmelidir — m.5.7.2.3.7 o durumda ek yük durumları ister.")
    #  ------------------------------------------------------------------
    #  ω tablosu YALNIZ 20 ≤ λ ≤ 250 arasında tanımlıdır.  Üst sınırın
    #  dışında ω yoktur;  motor bunu ham bir Python hatasıyla ( None ile
    #  çarpım ) bildiriyordu ve kullanıcı hangi alanın sorunlu olduğunu
    #  göremiyordu.  50 x 50 x 5 rayda sınır 3.845 mm'dir — varsayılan
    #  3.000 mm konsol aralığına yakın, yani gerçekçi bir girdiyle
    #  karşılaşılıyordu.
    #
    #  ALT SINIRDA HATA YOKTUR:  λ < 20 burkulmanın belirleyici olmadığı
    #  bölgedir, motor λ'yı 20'ye yuvarlar ( makine kaidesinde de öyle ).
    #  BURKULMA YALNIZ GÜVENLİK TERTİBATI ÇALIŞTIĞINDA VARDIR.
    #  ω, Ek C.2.1.2'de ( güvenlik tertibatının çalışması ) geçer;  C.2.2 ve
    #  C.2.3 normal çalışma hâlleridir ve orada Fv = Mg·gn + Fp'dir, ω yoktur.
    #  Kabinde tertibat her zaman vardır;  karşı ağırlıkta ise SEÇİME bağlıdır.
    #  Tertibat yoksa rayı sıkıştıran Fk de yoktur, λ > 250 bir şeyi
    #  düşürmez — orada uyarmak yanlış alarm olurdu.
    _agirlik_gt = str(g.get("agirlik_guvenlik_tertibati") or "Yok") != "Yok"
    for ray_alan, konsol_alan, ne, _gerekli in (
            ("kabin_ray_profili", "kabin_konsol_arasi", "Kabin", True),
            ("agirlik_ray_profili", "agirlik_konsol_arasi", "Karşı ağırlık",
             _agirlik_gt)):
        if not _gerekli:
            continue
        prof, l = g.get(ray_alan), g.get(konsol_alan)
        #  NARİNLİK EN KÜÇÜK ATALET YARIÇAPINDAN ÖLÇÜLÜR  ( m.5.10.3:
        #  "i is the MINIMUM radius of gyration" ).  Burada ix okunuyordu;
        #  kataloğun altı profilinden beşinde iy < ix olduğu için tablo
        #  dışına düşen geometriler ( λ > 250 ) sessizce kabul ediliyordu.
        _ix = MT.ray(prof, "ix") if prof else None
        _iy = MT.ray(prof, "iy") if prof else None
        imin = min(_ix, _iy) if _sayi(_ix) and _sayi(_iy) else None
        if _sayi(imin) and imin > 0 and _sayi(l) and l > 0:
            lam = l / imin
            if lam > MT.OMEGA_LAMBDA_MAX:
                azami = MT.OMEGA_LAMBDA_MAX * imin
                #  GİRDİ REDDEDİLMEZ, UYARILIR.  Eskiden burası hata veriyor ve
                #  bütün proje hesaplanamıyordu.  Oysa λ > 250 yalnız ω'yı
                #  tanımsız bırakır:  eğilme, birleşik gerilme, flanş ve sehim
                #  hesapları geçerliliğini korur.  Motor ω = None'ı zaten
                #  karşılıyor — bölüm "TABLO DIŞI" der ve burkulma kontrolü
                #  DÜŞER, yani sonuç UYGUN DEĞİL çıkar.  ELEport'un paftası da
                #  aynı şeyi yapar:  "when λ > 250 … σk also cannot be
                #  calculated".  Hesabı büsbütün durdurmak, kullanıcıya öteki
                #  bölümlerin sonucunu da göstermiyordu.
                uyari.append(
                    f"{ne} rayı fazla narin:  λ = konsol arası / imin = "
                    f"{l:g} / {imin:g} = {lam:.1f}  >  {MT.OMEGA_LAMBDA_MAX}. "
                    "TS EN 81-50 m.5.10.3'ün ω tablosu bu narinliğin ötesinde "
                    "tanımlı değildir;  BURKULMA HESABI YAPILAMAZ ve bölüm "
                    f"uygun çıkmaz. '{ALAN[konsol_alan][2]}' en çok "
                    f"{azami:.0f} mm olabilir ( '{prof}' rayı için ), ya da daha "
                    "büyük kesitli bir ray profili seçilmelidir.")

    #  ------------------------------------------------------------------
    #  TAM EZİLME = KURULU YÜKSEKLİĞİN %90'I   TS EN 81-20 m.5.8.2.1.2.2
    #  ------------------------------------------------------------------
    #  Madde "fully compressed" terimini TANIMLAR:  Çizelge 2'nin uç
    #  konumlarında tampon, kurulu yüksekliğinin %90'ı kadar ezilmiş sayılır
    #  ( bağlantı elemanları daha azıyla sınırlıyorsa o kadar ).  Program bu
    #  sayıyı sığınma açıklıklarında kullanır:
    #      kuyu dibi açıklığı = baba + ( tampon boyu − ezilme )
    #  Girilen ezilme gerçeğinden KÜÇÜKSE açıklık OLDUĞUNDAN BÜYÜK çıkar ve
    #  m.5.2.5.8'in 500 mm'si yanlışlıkla sağlanmış görünür — emniyetsiz yön.
    #  Lineer olmayan tamponda uyarılır;  lineer ve hidrolikte strok zaten
    #  bağıntıyla denetlendiği için burada tekrarlanmaz.
    _tip = g.get("tampon_tipi")
    if _tip and MT.tampon(_tip)[2] is None:
        _boy, _ez = g.get("kabin_tampon_boyu"), g.get("kabin_tampon_ezilme")
        if _sayi(_boy) and _sayi(_ez) and _boy > 0:
            _tam = MT.TAMPON_TAM_EZILME_ORANI * _boy
            if _ez < _tam - 0.5:
                uyari.append(
                    f"Kabin tamponu ezilmesi ({_ez:g} mm), kurulu yüksekliğin "
                    f"%{MT.TAMPON_TAM_EZILME_ORANI * 100:.0f}'ından "
                    f"({_tam:.0f} mm) küçük.  TS EN 81-20 m.5.8.2.1.2.2 "
                    "\"tam ezilmiş\" durumu bu oranla tanımlar;  daha küçük bir "
                    "değer kuyu dibi açıklığını olduğundan BÜYÜK gösterir. "
                    "Bağlantı elemanları ezilmeyi gerçekten sınırlıyorsa değer "
                    "doğrudur, yoksa tampon boyuyla uyumlu hâle getirilmelidir.")
    return uyari


def toplam_ray_boyu(g):
    """Kılavuz ray toplam boyu ( m ) — Excel: (ΣG12:G34 + F107−200 + F114−300)/1000."""
    dy = g.get("durak_yukseklikleri") or ()
    if not all(_sayi(v) for v in dy) or not dy:
        return None
    ky, kd = g.get("kaide_yuksekligi"), g.get("kuyu_dibi")
    if not (_sayi(ky) and _sayi(kd)):
        return None
    return (sum(dy) + (ky - 200) + (kd - 300)) / 1000.0
