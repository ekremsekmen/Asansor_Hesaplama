# -*- coding: utf-8 -*-
"""
MUKAVEMET HESABI — GİRDİ SÖZLEŞMESİ        ( uygulama projesi )

Tüketen:  engine/uygulama/mukavemet.py

Bu modül hesap YAPMAZ.  Yalnızca mukavemet motorunun hangi girdileri
beklediğini, her birinin birimini, seçenek listesini ve varsayılanını
tanımlar.  Arayüz, API ve doğrulama testleri hep buradan okur — tek
doğruluk kaynağı.

AVANDAN AYRIDIR.  Avan tarafındaki tablolar ( engine/avan/tablolar.py )
MMO/697 avan kitabından gelir;  uygulama projesinin tabloları bilerek ayrı
tutulmuştur ( bkz. engine/uygulama/mukavemet_tablolari.py ).
"""
from engine.ortak import ofis as OFIS
from engine.ortak.steps import evet_mi
from engine.uygulama import mukavemet_tablolari as MT


def _s(*d):
    return tuple(d)


#  ( anahtar, etiket, birim, tür, seçenekler, varsayılan )
#    tür:  "sayi" · "secim" · "hesap"
#    "hesap" alanları kullanıcıdan alınmaz — tamamla() üretir.
ALANLAR = (
    # ── ASANSÖR TEKNİK BİLGİLERİ ──────────────────────────────────────
    #  ASANSÖR ADI.  Bir binada dört asansör olabilir ve hepsi ayrı kuyudadır;
    #  paftaları birbirinden ayırt edilebilmeli.  Boş bırakılırsa "1 nolu
    #  asansör" gibi numarayla anılır.
    ("asansor_adi",       "Asansör adı  ( paftada görünür )",  "—",    "metin", None, None),
    #  ASANSÖR TİPİ.  TS EN 81-20 m.5.7.2.3.6 kapı eşiğine binen kuvveti
    #  asansörün TİPİNE göre verir:  insan asansöründe Fs = 0,4·gn·Q, yük-insan
    #  asansöründe 0,6·gn·Q.  Beyan yüküne bağlı bir eşik ( Q < 2500 kg →
    #  0,4 ) standartta yoktur — 1600 kg bir yük-insan asansörü 0,4 ile
    #  emniyetsiz hesaplanırdı.
    ("asansor_tipi",      "Asansör tipi",                      "—",    "secim",
     MT.ASANSOR_TIPLERI, MT.ASANSOR_TIPLERI[0]),
    #  SEÇENEKLER TABLODAN TÜRETİLİR.  Elle yazılan ikinci bir liste, kabin
    #  alanı tablosuyla ayrışabilir ( EN 81-20 Çizelge 6'nın bazı yükleri
    #  listede olmaz, o yüklerde hesap yapılamaz ).  Tek kaynak KABIN_ALANI'dır.
    ("beyan_yuku",        "Beyan yükü",                        "kg",   "secim",
     tuple(k[0] for k in MT.KABIN_ALANI), 800),
    ("beyan_hizi",        "Beyan hızı",                        "m/s",  "secim",
     _s(0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6), 1),
    ("seyir_mesafesi",    "Seyir mesafesi",                    "m",    "sayi", None, 21),
    #  BOŞ BIRAKILIRSA OFİS TABLOSUNDAN DOLAR  ( engine/ortak/ofis.py ).
    #  Standartlarda böyle bir çizelge yoktur — TS EN 81-20 / 81-50 kabin
    #  kütlesini ( P ) hep GİRDİ olarak tanımlar;  tablo ofisin kendi
    #  imalatçı deneyimidir ve avan tarafında da aynı yerden okunur.
    #  VARSAYILANI 700'DÜR:  örnek projenin değeri ve doğrulama testlerinin
    #  dayanağı odur.  Beyan yükü değiştirildiğinde arayüz alanı tablodan
    #  günceller.
    ("kabin_agirligi",    "Kabin ağırlığı",                    "kg",   "sayi", None, 700),
    ("karsi_agirlik",     "Karşı ağırlık",                     "kg",   "hesap", None, None),
    ("aski_orani",        "Askı oranı  ( 1 : n )",             "—",    "secim", _s(1, 2), 2),

    # ── KABİN VE KAPI ─────────────────────────────────────────────────
    ("kabin_genisligi",   "Kabin genişliği",                   "mm",   "sayi", None, 1450),
    ("kabin_derinligi",   "Kabin derinliği",                   "mm",   "sayi", None, 1350),
    ("kat_kapisi_tipi",   "Kat kapısı tipi",                   "—",    "secim",
     MT.KAPI_TIPLERI, "Teleskopik Sol"),
    ("kapi_genisligi",    "Kat kapısı genişliği",              "mm",   "secim",
     _s(700, 800, 900, 1000, 1100, 1200, 1300, 1400), 900),
    ("uzun_pervaz",       "Uzun pervaz",                       "mm",   "sayi", None, 90),
    ("kabin_kaciklik",    "Kabin merkezinin y ekseninde kaçıklığı", "mm", "sayi", None, 0),
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
    ("aski_kaciklik_x",   "Askı noktasının x kaçıklığı  ( xs )", "mm", "sayi", None, 0),
    ("aski_kaciklik_y",   "Askı noktasının y kaçıklığı  ( ys )", "mm", "sayi", None, 0),
    #  BOŞ KABİNİN AĞIRLIK MERKEZİ ( P )  —  Ek C.1.2'nin xp · yp'si.
    #  Boş bırakılırsa TÜRETİLİR:  gövde kabin merkezinde, kapı ( ofis
    #  standardındaki ağırlığıyla ) kapı tarafında, gezici kablo ve denge
    #  zinciri kabin merkezinde kabul edilir ve yp = yc olur ( bkz.
    #  mukavemet._kabin_raylari ).  İmalatçı ağırlık merkezini veriyorsa buraya
    #  girilir;  ray ekseninden ölçülür ve P'nin TAMAMINA uygulanır ( kapı,
    #  gezici kablo, zincir dahil — m.5.7.2.3.2 ).  ELEport bu iki değeri
    #  doğrudan sorar ( Xp · Yp );  türetme onları temsil edemiyordu — örnek
    #  projesinde xp = +250 mm iken kabin merkezi −140 mm'dedir.
    ("kabin_agirlik_merkezi_x", "Boş kabinin ağırlık merkezi x  ( xp — boşsa türetilir )",
     "mm", "sayi", None, None),
    ("kabin_agirlik_merkezi_y", "Boş kabinin ağırlık merkezi y  ( yp — boşsa türetilir )",
     "mm", "sayi", None, None),
    ("agirlik_yeri",      "Karşı ağırlık yeri",                "—",    "secim",
     _s("Sağ", "Sol", "Arka"), "Sağ"),
    #  Kabin kapısı ağırlığı burada SORULMAZ — ofis standardıdır
    #  ( engine/uygulama/sabitler.py · kabin_kapisi_agirligi ).
    ("kapi_mekanizma_payi", "Kapı mekanizma ağ. mrk. payı",    "mm",   "sayi", None, 50),

    # ── DURAK VE KUYU ─────────────────────────────────────────────────
    #  KATLAR TEK TEK SORULMAZ.  Hesap durak yüksekliklerinden yalnız
    #  TOPLAMI ( ray boyu · regülatör halatı ) ve SON DURAĞINKİNİ ( kuyu
    #  boyu · sığınma ) kullanıyordu;  toplam da  seyir mesafesi + son kat
    #  yüksekliğidir.  Liste kaldırıldı:  15 katlı binaya 15 kez "3000"
    #  yazdırıyor, sonuca hiçbir şey katmıyordu.  Farklı kat yükseklikleri
    #  zaten seyir mesafesinin içindedir.
    #
    #  SON KAT YÜKSEKLİĞİ:  en üst durak döşemesinden kuyu tavanına.
    ("son_kat_yuksekligi", "Son kat yüksekliği",               "mm",   "sayi", None, 3750),
    ("kuyu_boyu",         "Kuyu boyu",                         "mm",   "hesap", None, None),
    #  TABLİYE BETON YÜKSEKLİĞİ  —  makine dairesinin beton döşemesi.
    #  Kılavuz ray boyuna ve regülatör halatı boyuna "tabliye − 200 mm"
    #  olarak girer ( ofis modeli ).  YALNIZ MAKİNE DAİRELİ TESİSTE SORULUR:
    #  makine dairesiz ( MRL ) tesiste tabliye yoktur — makine kuyu
    #  üstündeki NPU kirişlere oturur — ve hesaba 0 girer ( bkz. tabliye ).
    #  Eskiden adı "Kaide yüksekliği"ydi ve MRL'de de 750 mm ekleniyordu:
    #  olmayan bir tabliye ray ve regülatör halatı boyunu uzatıyordu.
    #  Varsayılan 1.200 mm:  ofisin makine daireli şablonundaki değer.
    ("tabliye_yuksekligi", "Tabliye beton yüksekliği",         "mm",   "sayi", None, 1200),
    ("kuyu_dibi",         "Kuyu dibi yüksekliği  ( KY )",      "mm",   "sayi", None, 1600),
    #  KUYU DERİNLİĞİ ( KD ) ve AĞIRLIK RAY MERKEZİ - DUVAR SORULMAZ.  İkisi
    #  yalnız arka ağırlıkta halat arasını ( KD − RK − ray-duvar ) türetmek
    #  için vardı;  o türetme α doğrudan beyan edilince kalktı ( bkz.
    #  "halat_arasi" notu ).  Sonra hiçbir hesaba ve paftaya girmediler —
    #  yalnız artık türetilmeyen o sayının pozitifliğini denetleyen bir
    #  kontrolde okunuyorlardı.
    ("ray_kapi_arasi",    "Ray - kapı arası  ( RK )",          "mm",   "sayi", None, 650),

    # ── MAKİNE VE MOTOR ───────────────────────────────────────────────
    ("motor_gucu",        "Motor gücü",                        "kW",   "sayi", None, 4.9),
    ("makine_agirligi",   "Makine - motor ağırlığı  ( Gm )",   "kg",   "sayi", None, 300),
    #  C ( sap. kasnak yükü ) ve D ( makine yatak yükü ) KALDIRILDI.
    #  İkisi de YALNIZ sarılma açısını türetmek için vardı:
    #      B = H − C + D ,  α = 180° − arctan( ( Ra − 2·R1 ) / B )
    #  α artık doğrudan beyan ediliyor ( bkz. "sarilma_acisi" ), o yüzden
    #  bu iki ölçü hiçbir sonuca girmiyordu — formda durup kullanıcıyı
    #  oyalıyorlardı.  ELEport da açıyı doğrudan sorar ve bu ölçüleri hiç
    #  istemez.
    ("tahrik_kasnak_capi", "D1 ( tahrik kasnağı çapı )",        "mm",   "sayi", None, 240),
    ("saptirma_kasnak_capi", "D2 — saptırma kasnaklarının ORTALAMA çapı", "mm", "sayi", None, 240),
    #  Ds — EN KÜÇÜK kasnak çapı.  Sf formülündeki Kp = (Dt/Dp)⁴ ORTALAMA
    #  bükülme şiddetini temsil eder;  EN 81-20 m.5.5.2.1'in D/dr ≥ 40 sınırı
    #  ise HER kasnak için ayrı ayrı geçerlidir — ortalama sınırı geçse bile
    #  tek bir küçük kasnak geçemiyor olabilir.  Boş bırakılırsa ortalama çap
    #  kullanılır ( eski davranış ).
    ("saptirma_kasnak_min_capi", "Ds — saptırma kasnaklarının EN KÜÇÜK çapı  ( boşsa ortalama )",
     "mm", "sayi", None, None),
    ("sase_yuksekligi",   "Şase yüksekliği",                   "mm",   "sayi", None, 1100),
    #  PROFİL TİPİ SORULMAZ:  tablo yalnız NPU tanır ve seçim kutusunun tek
    #  seçeneği vardı.  Pafta profili "NPU <ölçü>" diye kendisi yazar.
    ("dikine_kiris",      "E  ( dikine kiriş ölçüsü )",        "—",    "secim",
     MT.NPU_OLCULERI, 120),
    #  YAN YATAK = MAKİNENİN ALTINDAKİ KİRİŞ.  Makine dairesinde kaidenin
    #  yatay kirişidir;  makine dairesiz ( MRL ) tesiste makine kuyu üstünde
    #  doğrudan bu NPU kirişlere oturur ( kolon yoktur ).  İki yerleşimde de
    #  sorulur ve bölüm 2'de eğilmeye göre denetlenir.  Varsayılan NPU 140:
    #  ofisin sahada gördüğü kiriş ( kullanıcı kararı;  örnek projede 120 ).
    ("yan_yatak",         "F  ( yan yatak — makine kirişi ölçüsü )", "—", "secim",
     MT.NPU_OLCULERI, 140),
    ("yan_yatak_boyu",    "Yan yatak ( makine kirişi ) boyu",  "mm",   "sayi", None, 1400),

    # ── ASKI HALATLARI ────────────────────────────────────────────────
    ("halat_adedi",       "Askı halatı adedi",                 "adet", "sayi", None, 7),
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
    ("denge_zinciri",     "Denge ( kompanzasyon ) zinciri",     "—",    "secim",
     ("Yok", "Var"), "Yok"),
    ("halat_birim_kutle", "Askı halatı 1 m ağırlığı  ( imalatçı — boşsa tablo )",
     "kg/m", "sayi", None, None),
    ("halat_kopma_kN",    "Askı halatı en küçük kopma yükü  ( imalatçı — boşsa tablo )",
     "kN", "sayi", None, None),
    ("halat_capi",        "Askı halatı çapı",                  "mm",   "secim",
     MT.HALAT_CAPLARI, 6.5),
    #  D/d ≥ 40 — BELGEYLE AŞILABİLEN SINIR.  TS EN 81-20 m.5.5.2.1'in 40'ı
    #  uyumlaştırılmış standart şartıdır;  Asansör Yönetmeliği ( 2014/33/AB )
    #  Ek-I 1.3 askı elemanları için sayısal oran vermez.  240 mm kasnak ile
    #  6,5 mm halat gibi birleşimler bu sapmayı onaylanmış kuruluş belgesiyle
    #  kanıtlar.  "Var" seçilirse 40'ın altı hata sayılmaz;  Sf ( EN 81-50
    #  m.5.12 ) yine aynen aranır — küçük kasnağın bedelini zaten o öder.
    #  ELEport aynı yerde Sf'yi de 12'ye indirir;  bu bilerek alınmadı.
    ("kasnak_belgesi",    "Dt/dh < 40 için onaylanmış kuruluş belgesi",
     "—",    "secim", ("Yok", "Var"), "Yok"),
    ("kanal_sekli",       "Kasnak kanal şekli",                "—",    "secim",
     MT.KANAL_SEKILLERI, "Altı Kesik V Kanal"),
    ("kanal_isleme",      "Kanal işleme şekli",                "—",    "secim",
     MT.KANAL_ISLEME_SEKILLERI, "Sertleştirilmemiş"),
    # Açı doğrudan beyan edilir; eksik açıya varsayılan atanmaz.
    ("sarilma_acisi",     "α — halat sarılma açısı",
     "°", "sayi", None, None),
    #  EN 81-50 m.5.12.2 — Nequiv(p).  Sabit değil, tesisin askı düzenine bağlıdır.
    #  BOŞ BIRAKILIRSA ASKI ORANINDAN GELİR  ( bkz. kasnak_tek_yon_askidan ).
    ("kasnak_tek_yon",    "Tek yönde bükülmeli kasnak sayısı  ( Nps — boşsa askı oranından )",
     "adet", "sayi", None, None),
    ("kasnak_ters_yon",   "Ters yönde bükülmeli kasnak sayısı  ( Npr )", "adet", "sayi", None, 0),
    ("acil_frenleme_a",   "Acil frenleme yavaşlaması  ( a )",  "m/s²", "sayi", None, 0.8),
    ("kablo_tipi_1",      "1. bükülgen kablo tipi",            "—",    "secim",
     MT.KABLO_TIPLERI, "24 x 0,75"),
    #  2. kablo tipi GİRDİ DEĞİLDİR:  kat kapısı tipinden türetilir.
    #  Sorulmaz, hesaplanır.
    ("kablo_tipi_2",      "2. bükülgen kablo tipi",            "—",    "hesap", None, None),
    #  GEZİCİ KABLONUN İMALATÇI AĞIRLIĞI.  Program iki kabloyu tablodan alır
    #  ( 1. tip + kat kapısından türeyen 2. tip ) ve tablo dört kablo tanır;
    #  tek kablolu ya da farklı kesitli bir tesis girilemiyordu ( ELEport
    #  örneği:  tek kablo 0,44 kg/m — tablo 2 × 0,642 = 1,284 kg/m verir ).
    #  MTrav motor gücüne, P'ye ( ray · kuyu tabanı ) ve tahrike girer.
    #  TOPLAMDIR:  bütün gezici kabloların metre ağırlıkları toplanıp yazılır.
    #  Boş bırakılırsa tablo kullanılır.
    ("kablo_birim_kutle", "Gezici kabloların toplam 1 m ağırlığı  ( imalatçı — boşsa tablo )",
     "kg/m", "sayi", None, None),
    #  "halat_arasi" ( Ra ) da KALDIRILDI — o da yalnız α'nın payındaydı
    #  ( A = Ra − 2·R1 ).  Arka ağırlıkta kuyu derinliği − ray-kapı arası −
    #  ağırlık ray-duvar'dan türetiliyordu;  o üç ölçü kendi hesaplarında
    #  duruyor, yalnız bu türetme kalktı.

    # ── REGÜLATÖR ─────────────────────────────────────────────────────
    ("reg_halat_capi",    "Regülatör halatı çapı",             "mm",   "secim", _s(6, 6.5, 8), 6),
    ("reg_kasnak_capi",   "Regülatör kasnak çapı  ( Dreg )",   "mm",   "sayi", None, 300),
    ("reg_kanal_acisi",   "Regülatör kanal açısı",             "°",    "sayi", None, 40),
    ("reg_surtunme",      "Regülatör sürtünme faktörü  ( μ )", "—",    "sayi", None, 0.2),
    ("reg_gergi_agirligi", "Regülatör gergi ağırlığı  ( Gra )", "kg",  "sayi", None, 70),
    #  KATALOG VERİSİ ASKI HALATINDA VARDI, REGÜLATÖRDE YOKTU.  TS 12385-5
    #  tablosu yalnız LİF ÖZLÜ halatları kapsar;  regülatör halatları çoğu
    #  zaman çelik özlüdür ve kopma yükleri belirgin biçimde yüksektir
    #  ( 6 mm:  tablo 23,1 kN — piyasadaki çelik özlü 28 kN ).  Program bu
    #  yüzden UYGUN tasarımları reddedebiliyordu.  Boş bırakılırsa tablo.
    ("reg_halat_birim_kutle", "Regülatör halatı 1 m ağırlığı  ( imalatçı — boşsa tablo )",
     "kg/m", "sayi", None, None),
    ("reg_halat_kopma_kN", "Regülatör halatı en küçük kopma yükü  ( imalatçı — boşsa tablo )",
     "kN",   "sayi", None, None),
    #  TS EN 81-20 m.5.6.2.2.1.1 d):  regülatörün ürettiği çekme kuvveti,
    #  "güvenlik tertibatını devreye sokmak için GEREKENİN İKİ KATI" ile
    #  300 N'un BÜYÜĞÜNDEN az olamaz.  O kuvvet İMALATÇI VERİSİDİR ( halatın
    #  kendi statik gergisinin iki katı DEĞİLDİR ).  Boş bırakılırsa yalnız
    #  300 N sınırı denetlenir ve pafta eksiği açıkça yazar.
    ("guvenlik_devreye_kuvvet", "Güv. tertibatını devreye sokma kuvveti  ( imalatçı )",
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
    #  ( Eski projeler True/'EVET' taşır;  MT.makine_raya_mi ikisini de anlar. )
    ("makine_raya_biniyor", "Makine yükünün yolu",
     "—",    "secim", MT.MAKINE_YUK_YOLU, MT.MAKINE_YUK_YOLU[0]),
    #  BİR RAYA DÜŞEN MAKİNE YÜKÜ SORULMAZ.  "Bina yapısına" seçildiğinde
    #  hesaba hiç girmez;  "Kılavuz raylara" seçildiğinde makinenin yükü
    #  ( Gm + Tst ) kabin VE karşı ağırlık raylarına EŞİT dağıtılır ( bkz.
    #  mukavemet._makine_ray_payi ).  Eskiden imalatçının asimetrik değeri için ayrı bir
    #  kutu vardı;  yük yolu "bina yapısına" iken de görünüyordu.
    ("makine_tst",        "Tst — makinenin azami kasnak statik yükü  ( imalatçı )",
     "kg", "sayi", None, None),
    #  TS EN 81-20 m.5.6.2.2.1.1 a):  devreye girme hızı beyan hızının en az
    #  %115'i ve tertibat tipine göre belirlenen üst sınırın ALTINDA olmalı.
    #  Değer regülatörün TİP İNCELEME belgesinden gelir.
    ("reg_devreye_hizi",  "Regülatör devreye girme hızı  ( imalatçı )", "m/s", "sayi", None, None),

    # ── KILAVUZ RAYLAR ────────────────────────────────────────────────
    ("kabin_ray_profili", "Kabin rayı profili",                "—",    "secim",
     MT.RAY_PROFILLERI, "89 x 62 x 15,88"),
    ("agirlik_ray_profili", "Ağırlık rayı profili",             "—",    "secim",
     MT.RAY_PROFILLERI, "50 x 50 x 5"),
    ("kabin_konsol_arasi", "Kabin rayı konsollar arası en uzun mesafe", "mm", "sayi", None, 3000),
    ("agirlik_konsol_arasi", "Ağırlık rayı konsollar arası en uzun mesafe", "mm", "sayi", None, 3000),
    ("kabin_ray_sayisi",  "Kabin rayı sayısı",                 "adet", "sayi", None, 2),
    ("agirlik_ray_sayisi", "Ağırlık rayı sayısı",              "adet", "sayi", None, 2),
    ("ray_celigi_rm",     "Ray çeliği Rm",                     "N/mm²", "secim",
     MT.RAY_CELIKLERI, 370),
    #  Makine tipi motor verimini belirler;  ofisin tablosu
    #  ( engine/ortak/ofis.py ) dişlisiz makinede 0,85, dişlide 0,50 der.
    ("makine_tipi",       "Makine tipi",                       "—",    "secim",
     tuple(OFIS.MAKINE_VERIMLERI), "Dişlisiz"),
    #  PROJENİN MAKİNESİNE AİT VERİM.  Ofis değeri makine tipine göre tektir
    #  ( dişlisiz · dişli ),  ama her projenin makinesi başkadır ve
    #  imalatçının verdiği verim ondan ayrılabilir.  Tek projenin verimi için
    #  Sabitler'deki ofis değerini değiştirmek BÜTÜN projeleri değiştirirdi.
    #  Boşsa makine tipinden ofis değeri kullanılır ( bkz. sistem_verimi ).
    #  Anlamı ofis değeriyle AYNIDIR:  toplam sistem verimi, askı kaybı dâhil.
    ("makine_verimi",     "Toplam sistem verimi η  ( imalatçı — boşsa ofis değeri )",
     "—", "sayi", None, None),
    #  "Ofis verimi η toplam sistem verimidir" ANAHTARI KALDIRILDI.
    #  η artık HER ZAMAN toplam sistem verimidir ( askı kaybı içinde ) —
    #  seçilecek bir şey kalmadı.  Bkz. engine/ortak/ofis.py, "PALANGA VERİM
    #  DÜŞÜŞÜ KALDIRILDI".  Eski projelerin JSON'unda kalan toplam_verim
    #  anahtarı yok sayılır, geri yükleme bozulmaz.
    ("kabin_paten_arasi", "Kabin paten arası",                 "mm",   "sayi", None, 3400),
    ("agirlik_paten_arasi", "Ağırlık paten arası",             "mm",   "sayi", None, 3400),
    ("guvenlik_tertibati", "Güvenlik tertibatı ( fren bloğu ) tipi", "—", "secim",
     MT.DARBE_TIPLERI_ADLARI, "Kaymalı"),
    #  SIĞINMA HACMİ TİPİ  ( TS EN 81-20 m.5.2.5.7.1 · m.5.2.5.8.1 ).
    #  Standart üç duruştan BİRİNİ ister;  program bunu bilmiyor, ÇÖMELME
    #  tipini koda çivilemişti ve yatarak tipiyle uygun olan tesislere
    #  "UYGUN DEĞİL" diyordu.  Beyan edilen tip paftaya yazılır.
    ("siginma_tipi_ust",  "Kabin üstü sığınma hacmi tipi",     "—",    "secim",
     MT.SIGINMA_TIPLERI_UST, "Çömelme"),
    ("siginma_tipi_dip",  "Kuyu dibi sığınma hacmi tipi",      "—",    "secim",
     MT.SIGINMA_TIPLERI_DIP, "Çömelme"),
    #  TS EN 81-50 m.5.10.5 flanş eğilmesindeki ℓ ( KABİN paten balatasının
    #  uzunluğu ).  Boş bırakılırsa ray tablosundaki balata yarı genişliğinden
    #  türetilir.  Karşı ağırlığın kaymalı pateni bu değeri KULLANMAZ:  iki
    #  patenin balatası aynı parça değildir;  onun ℓ'si kendi rayından
    #  türetilir ( bkz. mukavemet._balata_boyu ).
    ("paten_balata_boyu", "Kabin paten balatası uzunluğu  ( ℓ )", "mm", "sayi", None, None),
    #  TS EN 81-50 m.5.10.5 / Ek C.2.1.4 flanş eğilmesi için İKİ formül verir:
    #  makaralı patende 1,85·Fx/c² , kaymalı patende balata boyuna bağlı olan.
    #  PATEN TİPİ RAY BAŞINADIR.  Kabin ve karşı ağırlık patenleri ayrı
    #  seçilir:  kabinde kaymalı, karşı ağırlıkta makaralı paten yaygın bir
    #  düzendir ve tek seçimle girilemiyordu — karşı ağırlık rayının flanş
    #  gerilmesi yanlış formülle hesaplanıyordu.
    ("paten_tipi",        "Kabin paten tipi",                  "—",    "secim",
     _s("Kaymalı", "Makaralı"), "Kaymalı"),
    ("agirlik_paten_tipi", "Karşı ağırlık paten tipi",         "—",    "secim",
     _s("Kaymalı", "Makaralı"), "Kaymalı"),
    #  Ek C.2.1.2 / C.2.2.2 / C.2.3.2:  Fv = … + Fp.  Fp, bir raydaki bütün
    #  konsol klipslerinin itme kuvvetidir ( binanın oturması, betonun
    #  büzülmesi ).  Varsayılan 0, değeri tesise bağlıdır.
    ("klips_itme_kuvveti", "Fp ( konsol klipslerinin itme kuvveti )", "N", "sayi", None, 0),
    #  Ek C.2.1.5 / C.2.2.5 / C.2.3.5:  δ = 0,7·F·l³/(48·E·I) + δstr.
    #  δstr binanın kendi sehimidir;  varsayılan 0.
    ("yapi_sehim_x",      "δstr-x ( bina yapısının x sehimi )", "mm",   "sayi", None, 0),
    ("yapi_sehim_y",      "δstr-y ( bina yapısının y sehimi )", "mm",   "sayi", None, 0),

    # ── KARŞI AĞIRLIK ─────────────────────────────────────────────────
    ("agirlik_malzemesi", "Karşı ağırlık malzemesi",           "—",    "secim",
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
    ("agirlik_genisligi",  "Karşı ağırlık genişliği  ( Gy )", "mm", "sayi", None, 960),
    ("agirlik_derinligi",  "Karşı ağırlık derinliği  ( Gx )", "mm", "sayi", None, 150),
    #  AĞIRLIK RAY ARASI SORULMAZ.  Mukavemet hesabına girmiyordu ( standartta
    #  ray arası → genişlik diye bir bağıntı yoktur ) ve paftada yalnız
    #  "hesaba girmez" notlu bir bilgi satırıydı;  CAD çizimi de kullanmıyordu.
    #  Ölçü kuyu yerleşim çiziminde durur.
    #  TS EN 81-20 m.5.6.1:  karşı ağırlıkta güvenlik tertibatı, kuyunun
    #  altındaki hacme girilebiliyorsa ZORUNLUDUR.  Varsa ağırlık rayı
    #  yalnız C.2.2'ye ( normal işletme ) değil TS EN 81-50 Ek C.2.1'e göre de
    #  ( k1 darbe katsayısıyla ) hesaplanmalıdır.
    ("agirlik_guvenlik_tertibati", "Karşı ağırlıkta güvenlik tertibatı", "—", "secim",
     ("Yok",) + MT.DARBE_TIPLERI_ADLARI, "Yok"),

    # ── TAMPONLAR ─────────────────────────────────────────────────────
    #  TİP, KONTROLÜN KENDİSİNİ SEÇER.  TS EN 81-20 m.5.8.1 tamponları üçe
    #  ayırır ve her birine başka bir kural bağlar ( strok formülü, hız
    #  sınırı );  tip sorulmadan bu kuralların hiçbiri denetlenemiyordu.
    #  Ofis poliüretan kullanıyor, varsayılan odur.
    ("tampon_tipi",         "Tampon tipi",                     "—",    "secim",
     MT.TAMPON_TIPLERI_ADLARI, MT.TAMPON_TIPLERI_ADLARI[1]),
    #  ADET, KUYU TABANINA DÜŞEN KUVVETİ BÖLER.  m.5.2.1.8.5 kuvveti
    #  "evenly distributed between the total number of car buffers" der:
    #  toplam 4·gn·(P+Q)'dur ama döşemenin TAŞIYACAĞI şey tampon BAŞINA
    #  düşendir.
    ("kabin_tampon_adedi",  "Kabin tamponu adedi",             "adet", "sayi", None, 1),
    ("agirlik_tampon_adedi", "Ağırlık tamponu adedi",           "adet", "sayi", None, 1),
    ("kabin_tampon_baba",   "Kabin tamponu baba yüksekliği",   "mm",   "sayi", None, 1000),
    ("agirlik_tampon_baba", "Ağırlık tamponu baba yüksekliği", "mm",   "sayi", None, 300),
    ("kabin_tampon_ezilme", "Kabin tamponu ezilme miktarı",    "mm",   "sayi", None, 90),
    ("kabin_carpma_arasi",  "Kabin tamponu - çarpma plakası arası", "mm", "sayi", None, 150),
    ("kabin_tampon_boyu",   "Kabin tamponu uzunluğu",          "mm",   "sayi", None, 100),
    ("agirlik_tampon_ezilme", "Ağırlık tamponu ezilme miktarı", "mm",  "sayi", None, 90),
    ("agirlik_carpma_arasi", "Ağırlık tamponu - çarpma plakası arası", "mm", "sayi", None, 150),
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
ISARETLI_ALANLAR = ("kabin_kaciklik", "aski_kaciklik_x", "aski_kaciklik_y",
                    "kabin_agirlik_merkezi_x", "kabin_agirlik_merkezi_y")

#  Hızlı erişim
ALAN = {a[0]: a for a in ALANLAR}
HESAPLANAN = tuple(a[0] for a in ALANLAR if a[3] == "hesap")


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
                     "kasnak_tek_yon", "kasnak_ters_yon")
#  SIFIR OLAMAYAN alanlar:  bölen ya da uzunluk oldukları için 0 girildiğinde
#  hesap teknik bir hatayla ( TypeError · ZeroDivisionError ) çöküyordu;
#  kullanıcı hangi alanın sorunlu olduğunu göremiyordu.
POZITIF_ALANLAR = ("kabin_konsol_arasi", "agirlik_konsol_arasi",
                   "kabin_paten_arasi", "agirlik_paten_arasi",
                   "yan_yatak_boyu", "sase_yuksekligi", "tahrik_kasnak_capi",
                   "halat_capi", "reg_kasnak_capi", "reg_halat_capi",
                   "kabin_genisligi", "kabin_derinligi",
                   #  Eskiden listenin "her durak pozitif" kuralı sağlıyordu.
                   "son_kat_yuksekligi")
#  MAKİNE YERLEŞİMİNE GÖRE HESABA GİRMEYEN ALANLAR.  Ekranda gizlenirler;
#  gizli bir alandaki değer projeyi DURDURMAMALI ( bkz. uygulanmayan ).
#    · Makine dairesi olmadan var olmayanlar:  tabliye ve kaidenin kolonları
#      ( şase yüksekliği · dikine kiriş ).  Makinenin altındaki kiriş
#      ( yan yatak ) MRL'de de vardır ve sorulur.
#    · Makine yükünün yolu yalnız MRL'de sorulur — makine daireli tesiste
#      makine kendi kaidesindedir, yükü raya binmez.
MAKINE_DAIRESI_ALANLARI = ("tabliye_yuksekligi", "sase_yuksekligi", "dikine_kiris")
RAYA_BINEN_ALANLARI = ("makine_raya_biniyor",)


def uygulanmayan(g):
    """Bu makine yerleşiminde hesaba girmeyen mukavemet alanları."""
    return (set(MAKINE_DAIRESI_ALANLARI) if evet_mi(g.get("mk_yok"))
            else set(RAYA_BINEN_ALANLARI))

#  AÇI alanları:  0 < açı < 180.  360° girildiğinde sin(180°) = 0 çıkıyor ve
#  hesap OverflowError ile çöküyordu.
#  α — sarılma açısı:  tek sarımda en çok yarım tur, çift sarımda bir tam
#  tur.  Üst sınır 360'tır;  seçilen kanal şekline göre DARALTMAYI motor
#  yapar ( bkz. mukavemet._tahrik · alfa_ust ), çünkü burada kanal şekli
#  ile açı alanı birbirini görmez.
ACI_ALANLARI = {"reg_kanal_acisi": (1, 179), "sarilma_acisi": (1, 360)}

#  kabin_agirligi BURADA DEĞİLDİR:  tamamla() onu ofis tablosundan doldurur
#  ve doldurma bir tek beyan yükü geçersizken başarısız olur — o durumda
#  "boş bırakılamaz" hatası çıkmalı, hesap None ile devam etmemelidir.
OPSIYONEL_ALANLAR = ("asansor_adi", "sarilma_acisi", "kasnak_tek_yon",
                     "kabin_agirlik_merkezi_x", "kabin_agirlik_merkezi_y",
                     "paten_balata_boyu", "guvenlik_devreye_kuvvet",
                     "reg_devreye_hizi", "makine_tst", "makine_verimi",
                     "halat_birim_kutle", "halat_kopma_kN",
                     "reg_halat_birim_kutle", "reg_halat_kopma_kN",
                     "saptirma_kasnak_min_capi", "kablo_birim_kutle")

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
#  hesabın akışını izler.
GRUPLAR = (
    ("Asansör teknik bilgileri",
     ("asansor_adi", "asansor_tipi", "beyan_yuku", "beyan_hizi", "seyir_mesafesi",
      "kabin_agirligi", "aski_orani")),
    ("Kabin ve kapı",
     ("kabin_genisligi", "kabin_derinligi", "kat_kapisi_tipi", "kapi_genisligi",
      "uzun_pervaz",
      "kabin_kaciklik", "aski_kaciklik_x", "aski_kaciklik_y",
      "kabin_agirlik_merkezi_x", "kabin_agirlik_merkezi_y",
      "agirlik_yeri", "kapi_mekanizma_payi")),
    ("Durak ve kuyu",
     ("son_kat_yuksekligi", "tabliye_yuksekligi",
      "kuyu_dibi", "ray_kapi_arasi",
      "siginma_tipi_ust", "siginma_tipi_dip")),
    ("Makine ve motor",
     ("motor_gucu", "makine_agirligi",
      "tahrik_kasnak_capi", "saptirma_kasnak_capi",
      "saptirma_kasnak_min_capi", "sase_yuksekligi",
      "dikine_kiris", "yan_yatak",
      "yan_yatak_boyu", "makine_tipi", "makine_verimi", "makine_tst",
      "makine_raya_biniyor")),
    ("Askı halatları",
     ("halat_adedi", "halat_capi", "kasnak_belgesi", "kanal_sekli", "kanal_isleme",
      "sarilma_acisi",
      "halat_birim_kutle", "halat_kopma_kN", "denge_zinciri",
      "kasnak_tek_yon", "kasnak_ters_yon",
      "acil_frenleme_a", "kablo_tipi_1", "kablo_birim_kutle")),
    ("Hız regülatörü",
     ("reg_halat_capi", "reg_kasnak_capi", "reg_kanal_acisi", "reg_surtunme",
      "reg_gergi_agirligi", "reg_halat_birim_kutle", "reg_halat_kopma_kN",
      "guvenlik_devreye_kuvvet", "reg_devreye_hizi")),
    ("Kılavuz raylar",
     ("kabin_ray_profili", "agirlik_ray_profili", "kabin_konsol_arasi",
      "agirlik_konsol_arasi", "kabin_ray_sayisi", "agirlik_ray_sayisi",
      "ray_celigi_rm", "kabin_paten_arasi", "agirlik_paten_arasi",
      "guvenlik_tertibati", "paten_tipi", "paten_balata_boyu",
      "agirlik_paten_tipi",
      "klips_itme_kuvveti", "yapi_sehim_x", "yapi_sehim_y")),
    ("Karşı ağırlık", ("agirlik_genisligi", "agirlik_derinligi",
                       "agirlik_malzemesi",
                       "agirlik_guvenlik_tertibati")),
    ("Tamponlar",
     ("tampon_tipi", "kabin_tampon_adedi", "agirlik_tampon_adedi",
      "kabin_tampon_baba", "agirlik_tampon_baba", "kabin_tampon_ezilme",
      "kabin_carpma_arasi", "kabin_tampon_boyu", "agirlik_tampon_ezilme",
      "agirlik_carpma_arasi")),
)


#  GELİŞMİŞ ALANLAR.  Her grubun altında kapalı duran "Gelişmiş" bölümünde
#  gösterilirler;  hesaba AYNEN girerler ve paftaya aynen basılırlar — yalnız
#  formda ilk bakışta görünmezler.
#
#  Ölçüt:  değer binadan ya da projeden gelmiyorsa ( ürünün ya da ofisin
#  sabiti ), zaten tablodan / başka bir girdiden dolduruluyorsa ya da yanlış
#  kaldığında sonuç bunu hata / uyarı olarak söylüyorsa buradadır.  GÖRÜNÜR
#  KALANLAR her projede değişenler ve yanlış kalınca sonucu çok değiştiren
#  beyanlardır:  askı oranı · ray-kapı arası · güvenlik tertibatı tipi ·
#  karşı ağırlıkta güvenlik tertibatı · sarılma açısı · regülatörün iki
#  imalatçı değeri ( girilmezse bölüm HESAP EKSİK kalır ).
#
#  ÜÇ KAÇIKLIK GÖRÜNÜR KALIR ( kabin merkezi y · askı xs · ys ).  Ürün
#  sabiti değil, çizime bağlı ölçülerdir;  varsayılan 0 standart yerleşimdir
#  ( kabin raylar arasında ortada, askı ray ekseninde ).  100 mm kaçıklık beş
#  projenin dördünde kabin rayı hükmünü çevirdi:  kaçık bir yerleşimde gizli
#  bir 0 unutulursa ray hesabı emniyetsiz tarafta kalır ve "değiştirildi"
#  sayacı unutulan değeri yakalayamaz.
#
#  Seçim 5 proje üzerinde her girdi gerçekçi değerlere çekilerek yapıldı;
#  karşı ağırlık yeri, malzeme ve kabin tamponu - çarpma plakası arası
#  hesabın hiçbir sayısını değiştirmedi, kaide yüksekliği en çok %1,3
#  etkiledi.
GELISMIS_ALANLAR = frozenset((
    # Asansör teknik bilgileri
    "asansor_tipi", "kabin_agirligi",
    # Kabin ve kapı
    "uzun_pervaz", "agirlik_yeri", "kapi_mekanizma_payi",
    "kabin_agirlik_merkezi_x", "kabin_agirlik_merkezi_y",
    # Durak ve kuyu
    "siginma_tipi_ust", "siginma_tipi_dip",
    # Makine ve motor
    "saptirma_kasnak_min_capi", "sase_yuksekligi", "dikine_kiris", "yan_yatak",
    "yan_yatak_boyu", "makine_verimi",
    # Askı halatları
    "kasnak_belgesi", "kanal_sekli", "kanal_isleme", "halat_birim_kutle",
    "halat_kopma_kN", "denge_zinciri", "kasnak_tek_yon", "kasnak_ters_yon",
    "acil_frenleme_a", "kablo_tipi_1", "kablo_birim_kutle",
    # Hız regülatörü
    "reg_halat_capi", "reg_kasnak_capi", "reg_kanal_acisi", "reg_surtunme",
    "reg_gergi_agirligi", "reg_halat_birim_kutle", "reg_halat_kopma_kN",
    #  İkisi de imalatçı verisidir ve proje aşamasında çoğu zaman bilinmez;
    #  boşsa paftaya standardın şartı yazılır ( bkz. mukavemet._regulator ).
    "guvenlik_devreye_kuvvet", "reg_devreye_hizi",
    # Kılavuz raylar
    "kabin_ray_sayisi", "agirlik_ray_sayisi", "ray_celigi_rm",
    "kabin_paten_arasi", "agirlik_paten_arasi", "paten_tipi",
    "paten_balata_boyu", "agirlik_paten_tipi", "klips_itme_kuvveti",
    "yapi_sehim_x", "yapi_sehim_y",
    # Karşı ağırlık
    "agirlik_genisligi", "agirlik_derinligi", "agirlik_malzemesi",
    # Tamponlar
    "tampon_tipi", "kabin_tampon_adedi", "agirlik_tampon_adedi",
    "kabin_tampon_ezilme", "kabin_carpma_arasi", "kabin_tampon_boyu",
    "agirlik_tampon_ezilme", "agirlik_carpma_arasi",
))


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
            _k, etiket, birim, tur, secenekler, varsayilan = ALAN[a]
            alanlar.append({
                "anahtar": a, "etiket": etiket, "birim": birim,
                "tur": tur,
                "secenekler": list(secenekler) if secenekler is not None else None,
                "varsayilan": varsayilan,
                "gelismis": a in GELISMIS_ALANLAR,
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
            "hesaplanan": list(HESAPLANAN)}


def varsayilanlar():
    """Örnek projenin girdileri — arayüzün açılış değerleri."""
    g = {}
    for anahtar, _e, _b, tur, _s2, var in ALANLAR:
        if tur == "hesap":
            continue
        g[anahtar] = var
    return tamamla(g)


def tamamla(g):
    """Girdilerden türetilen alanları doldurur.

    kabin ağırlığı  boşsa ofis tablosundan
    karşı ağırlık   = kabin ağırlığı + q × beyan yükü
    kuyu boyu       = seyir × 1000 + son kat yüksekliği + kuyu dibi
    2. kablo tipi   kat kapısı tipinden
    """
    g = dict(g)
    if isinstance(g.get("sarilma_acisi"), str) and not g["sarilma_acisi"].strip():
        g["sarilma_acisi"] = None
    #  BOŞ KABİN KÜTLESİ:  girilmemişse ofis tablosundan doldurulur.
    #  Program aynı tabloyu avan tarafında da kullandığı için iki proje aynı asansöre aynı kütleyi
    #  verir.  Elle girilen değer HER ZAMAN önceliklidir.
    by = g.get("beyan_yuku")
    if g.get("kabin_agirligi") is None or (
            isinstance(g.get("kabin_agirligi"), str)
            and not g["kabin_agirligi"].strip()):
        g["kabin_agirligi"] = OFIS.bos_kabin_kutlesi(by)
        g["kabin_agirligi_kaynak"] = OFIS.GK_KAYNAGI
    else:
        #  KAYNAK DEĞERDEN OKUNUR, GEÇMİŞTEN DEĞİL.  Ekran tablo değerini
        #  kutuya yazar;  sonraki her istek o sayıyı taşır.  Kaynak "boş mu
        #  geldi" diye belirlenince aynı girdi ilk hesapta "OFİS TABLOSU",
        #  sonrakilerde ( ve indirilen paftada ) "GİRİŞ" yazıyordu.  Değer bu
        #  beyan yükünün tablo değeriyse kaynak tablodur;  değilse girilmiştir.
        g["kabin_agirligi_kaynak"] = (
            OFIS.GK_KAYNAGI if g.get("kabin_agirligi") == OFIS.bos_kabin_kutlesi(by)
            else "GİRİŞ")
    ka = g.get("kabin_agirligi")
    #  KARŞI AĞIRLIK DENGE ORANI OFİS SABİTİDİR.
    #  Bölüm 1 Ga'yı  P + q·Q  ile kurar;  karşı ağırlık da buradan aynı q
    #  ile kurulur.  "Beyan yükü / 2" diye çivilenseydi q = 0,60'ta aynı
    #  projede iki farklı karşı ağırlık oluşurdu — aynı fiziksel parçanın
    #  kütlesi her hesapta aynı olmalıdır.
    from engine.uygulama import sabitler as _US
    # Motor, tahrik ve tampon aynı doğrulanmış denge oranını kullanmalı.
    # Ham sözlüğü koru: reddedilen girdiler uyarılarda gösterilmeye devam eder.
    q = _US.sabitler(g.get("_ofis"))["q_denge"]
    if _sayi(ka) and _sayi(by):
        g["karsi_agirlik"] = ka + q * by
    _tavan, kd = alt_duraktan_tavana(g), g.get("kuyu_dibi")
    if _tavan is not None and _sayi(kd):
        g["kuyu_boyu"] = _tavan + kd
    #  2. bükülgen kablo kat kapısı tipinden türetilir
    g["kablo_tipi_2"] = MT.kapi_kablosu(g.get("kat_kapisi_tipi"))
    #  ESKİ BİÇİM:  makine yükünün yolu bir zamanlar ONAY KUTUSUYDU ve
    #  True / "EVET" olarak kaydediliyordu.  Eski .uygulama dosyaları bu
    #  değeri taşır;  seçime çevrilmezse
    #  doğrulama "geçersiz seçim — True" deyip projeyi hiç açmaz.
    _yy = g.get("makine_raya_biniyor")
    if _yy is not None and _yy not in MT.MAKINE_YUK_YOLU:
        g["makine_raya_biniyor"] = (MT.MAKINE_YUK_YOLU[1]
                                    if MT.makine_raya_mi(_yy)
                                    else MT.MAKINE_YUK_YOLU[0])
    return g


def _sayi(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def sistem_verimi(g):
    """η ve girilip girilmediği:  projeye girilen verim, yoksa makine tipinden
    ofis değeri.  Mukavemet ve elektrik köprüsü AYNI değeri buradan okur."""
    e = g.get("makine_verimi")
    if _sayi(e):
        return e, True
    from engine.uygulama import sabitler as _US
    return _US.verim(_US.sabitler(g.get("_ofis")), g.get("makine_tipi")), False


def dogrula(g):
    """Girdi sözlüğünü denetler; hata metinleri listesi döner ( boşsa temiz )."""
    hata = []
    #  Hesaba girmeyen, ekranda da görünmeyen bir alan projeyi durdurmamalı.
    atla = uygulanmayan(g)
    for anahtar, etiket, birim, tur, secenekler, _v in ALANLAR:
        if tur == "hesap" or anahtar in atla:
            continue
        d = g.get(anahtar)
        ad = f"{etiket} ({birim})" if birim not in ("—", "") else etiket
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

    #  SIFIR OLAMAYACAK ALANLAR.  Bunlar hesapta BÖLEN olarak geçer;  sıfır
    #  girilirse motor ZeroDivisionError ile çöker.  Kullanıcıya çökme değil
    #  neyi düzelteceği söylenmeli.
    for anahtar in BOLEN_ALANLAR:
        d = g.get(anahtar)
        if anahtar not in atla and _sayi(d) and d == 0:
            hata.append(f"{ALAN[anahtar][1]}: sıfır olamaz — bu değer hesapta "
                        "bölen olarak kullanılır.")

    #  TABLO BÜTÜNLÜĞÜ.  Bir seçenek listede var ama tablosunda karşılığı
    #  eksikse hesap sessizce yanlış sonuç vermemeli  ( ör. NPU tablosunda
    #  240 · 280 · 300 için atalet yarıçapı yoktur ).
    for anahtar, oku, ne in TABLO_GEREKLI:
        d = g.get(anahtar)
        if anahtar in atla or d is None or d == "":
            continue
        eksik = [a for a, f in oku if f(d) is None]
        if eksik:
            hata.append(f"{ALAN[anahtar][1]}: seçilen '{d}' için tabloda "
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
            hata.append(f"{ALAN[anahtar][1]}: adet tam sayı olmalıdır "
                        f"( {d} girildi ).")
    nh = g.get("halat_adedi")
    if _sayi(nh) and nh < 2:
        hata.append("Askı halatı adedi en az 2 olmalıdır "
                    "(TS EN 81-20 m.5.5.1.3).")
    for anahtar in POZITIF_ALANLAR:
        d = g.get(anahtar)
        if anahtar in atla:
            continue
        if anahtar in ALAN and d is not None and (not _sayi(d) or d <= 0):
            hata.append(f"{ALAN[anahtar][1]}: sıfırdan büyük olmalıdır "
                        f"( {d} girildi ).")
    for anahtar, (alt, ust) in ACI_ALANLARI.items():
        d = g.get(anahtar)
        if d is not None and (not _sayi(d) or not (alt <= d <= ust)):
            hata.append(f"{ALAN[anahtar][1]}: {alt}° ile {ust}° arasında "
                        f"olmalıdır ( {d} girildi ).")

    #  ------------------------------------------------------------------
    #  SARILMA AÇISI KANALIN SARIM SAYISINA GÖRE FİZİKSEL OLMALI
    #  ------------------------------------------------------------------
    #  Tek sarımda halat tahrik kasnağını en çok yarım tur sarar ( ≤ 180° ).
    #  Çift sarımda iki kez geçer ve toplam açı yarım turu AŞAR ( > 180° );
    #  180° ve altı bir değer tek sarıma aittir — büyük ihtimalle tek geçişin
    #  açısı girilmiştir.  Bu kontrol eskiden yalnız motorun içindeydi:  motor
    #  bölümü "uygun değil" sayıyor ama altındaki üç yük durumuna imkânsız
    #  açıyla "UYGUN" basıyordu ( tek sarım · 300° ).  Açı kanal şekline
    #  bağlı olduğundan alanın kendi aralığıyla ( 1–360° ) denetlenemez;
    #  burada, iki alan birlikte görülürken reddedilir.
    _aci, _kanal = g.get("sarilma_acisi"), g.get("kanal_sekli")
    if _sayi(_aci) and 1 <= _aci <= 360 and MT.kanal_turu(_kanal) is not None:
        if (MT.kanal_gecis_sayisi(_kanal) or 1) > 1:
            if _aci <= 180:
                hata.append(
                    f"Sarılma açısı α ({_aci:g}°) çift sarımlı kanalda 180°'yi "
                    "aşmalıdır. Çift sarımda halat tahrik kasnağının üzerinden "
                    "iki kez geçer; 180° ve altı bir açı tek sarıma aittir. "
                    "İki geçişin TOPLAM sarılma açısını girin.")
        elif _aci > 180:
            hata.append(
                f"Sarılma açısı α ({_aci:g}°) tek sarımlı kanalda 180°'yi "
                "aşamaz — halat tahrik kasnağını en çok yarım tur sarar. "
                "Çift sarım kullanılıyorsa kanal şeklini ona göre seçin.")

    #  ------------------------------------------------------------------
    #  SERTLEŞTİRİLMEMİŞ V KANALIN ALT KESİLMESİ OLMALIDIR
    #  ------------------------------------------------------------------
    #  TS EN 81-50 m.5.11.2.3.1.2:  "Where the groove has not been submitted
    #  to an additional hardening process, in order to limit the
    #  deterioration of traction due to wear, an undercut is necessary."
    #  Normatif gövdededir, not değildir.  Bu birleşim eskiden yalnız bir not
    #  alıyor ve sayısal kontroller geçerse tahrik bölümü "UYGUNDUR" diyordu
    #  ( 576 senaryonun 142'sinde ).  Seçim SESSİZCE "sertleştirilmiş"e
    #  çevrilmez — o, gerçek kasnağın özelliğini değiştirmek olurdu.
    if MT.kanal_turu(_kanal) == "V" and g.get("kanal_isleme") == "Sertleştirilmemiş":
        hata.append(
            "Alt kesilmesiz V kanal sertleştirilmemiş olamaz — TS EN 81-50 "
            "m.5.11.2.3.1.2 sertleştirilmemiş V kanalda aşınmadan doğan tahrik "
            "kaybını sınırlamak için ALT KESİLME ister. Kanal ya "
            "sertleştirilmiş olmalı ya da 'Altı Kesik V Kanal' seçilmelidir.")

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
            hata.append(f"{ALAN['paten_balata_boyu'][1]}: sıfırdan büyük olmalıdır ( {pbb!r} girildi ).")
        elif pbb < 20:
            hata.append(f"Paten balatası uzunluğu ({pbb:g} mm) fiziksel değil — balata boyu en az 20 mm olmalıdır.")
        else:
            kpa = g.get("kabin_paten_arasi")
            if _sayi(kpa) and pbb >= kpa:
                hata.append(f"Paten balatası uzunluğu ({pbb:g} mm) kabin patenler arası mesafeden ({kpa:g} mm) küçük olmalıdır.")
    gdk = g.get("guvenlik_devreye_kuvvet")
    if gdk is not None and gdk != "":
        if not _sayi(gdk) or gdk <= 0:
            hata.append(f"{ALAN['guvenlik_devreye_kuvvet'][1]}: sıfırdan büyük olmalıdır ( {gdk!r} girildi ).")

    #  KATALOG HALAT VERİSİ ve Tst — hepsi opsiyoneldir, girilirse MAKUL olmalı.
    #  Kopma yükü alanı kN'dir:  katalog "31,5 kN" der, projeci 31500 yazarsa
    #  güvenlik katsayısı 1000 kat büyür ve HER tasarım "UYGUN" görünürdü.
    #  Üst sınır o hatayı yakalar.
    for _ad, _alt, _ust in (("halat_birim_kutle", 0.02, 5.0),
                            ("kablo_birim_kutle", 0.05, 20.0),
                            ("halat_kopma_kN", 5.0, 2000.0),
                            ("reg_halat_birim_kutle", 0.02, 5.0),
                            ("reg_halat_kopma_kN", 5.0, 2000.0),
                            ("makine_tst", 100.0, 100000.0),
                            #  Sabitler'deki ofis verimiyle aynı aralık.
                            ("makine_verimi", 0.1, 1.0),
                            ):
        _v = g.get(_ad)
        if _v is None or _v == "":
            continue
        if not _sayi(_v) or not (_alt <= _v <= _ust):
            hata.append(f"{ALAN[_ad][1]}: {_alt} - {_ust} aralığında olmalıdır "
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
    if "yan_yatak_boyu" not in atla and _sayi(L) and _sayi(pay) and L - pay <= 0:
        hata.append(f"Yan yatak boyu ({L} mm) mesnet payından ({pay} mm) büyük "
                    "olmalıdır. Makine kaidesi hesabı, açıklığı L olan basit "
                    f"kirişte yükün mesnetten X = L − {pay} uzaklıkta olduğunu "
                    "kabul eder; X ≤ 0 fiziksel değildir.")

    #  ------------------------------------------------------------------
    #  RAY NARİNLİĞİ  λ = konsol arası / ix        TS EN 81-50 m.5.10.3
    #  ------------------------------------------------------------------
    #  TAHRİK KASNAĞI GEOMETRİSİ            TS EN 81-50 m.5.11.2 / m.5.11.3
    #  ------------------------------------------------------------------
    #  ( "Halat arası tahrik kasnağı çapından küçük olamaz" doğrulaması
    #    KALDIRILDI.  O kural, α'yı Ra'dan türeten geometrik modelin
    #    kendisini korumak içindi:  Ra < 2·R1'de pay negatife düşüyor ve α
    #    180°'yi aşıyordu.  α artık doğrudan beyan ediliyor ve kendi
    #    aralığında ( 1° – 360° ) denetleniyor;  Ra diye bir girdi kalmadı. )

    #  ------------------------------------------------------------------
    #  SİSTEM VERİMİ  η  FİZİKSEL OLMALI             0 < η ≤ 1
    #  ------------------------------------------------------------------
    #  Δη kalktığı için η artık kendi başına negatife düşemez;  bu kalkan
    #  yine de durur, çünkü ofis sabiti ekrandan elle girilir ve ARALIK
    #  ( 0,1 - 1 ) atlanırsa N = Gmax·v/(η·102) sıfıra bölünür.
    #  Projeye verim girilmişse aralığını yukarıdaki katalog denetimi
    #  bekler;  ofis değeri o projede kullanılmadığı için burada aranmaz.
    _tip = g.get("makine_tipi")
    _etap, _eta_girildi = sistem_verimi(g)
    if not _eta_girildi and not (_sayi(_etap) and 0 < _etap <= 1):
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
    #  SARILMA AÇISI ZORUNLU BEYANDIR ( bkz. mukavemet.ALFA_YOK ).
    #  Girilmemişse tahrik yeteneğinin dört sınırı hesaplanmaz;  proje
    #  "uygundur" çıkamaz ve sebep burada, açıkça söylenir.
    #  ------------------------------------------------------------------
    if g.get("sarilma_acisi") in (None, ""):
        uyari.append(
            "SARILMA AÇISI α GİRİLMEDİ — halatın tahrik kasnağını sardığı "
            "toplam açıyı proje yerleşiminden belirleyip girin (tek sarımda en "
            "çok 180°, çift sarımda 180°–360°). Açı girilene kadar tahrik "
            "yeteneğinin dört sınırı hesaplanmaz ve bölüm HESAP EKSİK kalır.")
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
                    f"uygun çıkmaz. '{ALAN[konsol_alan][1]}' en çok "
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


def alt_duraktan_tavana(g):
    """En alt durak döşemesinden kuyu tavanına ( mm )  =  seyir × 1000 + son kat.

    Eski durak listesinin TOPLAMIYDI;  ray boyu, regülatör halatı ve kuyu
    boyu bu tek sayıdan türer.  Girdiler sayı değilse None.
    """
    sm, sk = g.get("seyir_mesafesi"), g.get("son_kat_yuksekligi")
    if not (_sayi(sm) and _sayi(sk)):
        return None
    return sm * 1000.0 + sk


def tabliye(g):
    """Hesaba giren tabliye beton yüksekliği ( mm ).

    Makine dairesiz ( MRL ) tesiste tabliye yoktur:  0.  Makine dairelide
    girilen değer;  sayı değilse None.
    """
    if evet_mi(g.get("mk_yok")):
        return 0.0
    t = g.get("tabliye_yuksekligi")
    return t if _sayi(t) else None


def toplam_ray_boyu(g):
    """Kılavuz ray toplam boyu ( m )  =  ( seyir + son kat + tabliye − 200 + kuyu dibi − 300 ) / 1000.

    Tabliye makine dairesiz tesiste 0'dır ( bkz. tabliye ).
    """
    tavan = alt_duraktan_tavana(g)
    ky, kd = tabliye(g), g.get("kuyu_dibi")
    if tavan is None or not (_sayi(ky) and _sayi(kd)):
        return None
    return (tavan + (ky - 200) + (kd - 300)) / 1000.0


#  Nps  —  TEK YÖNDE BÜKÜLMELİ KASNAK SAYISI, BOŞ BIRAKILINCA  ( TS EN 81-50 Ek E )
#  m.5.12.3 güvenlik katsayısını halatın EN OLUMSUZ KESİTİ için ister:  sayılan,
#  halatın tamamının geçtiği kasnaklar değil, tek bir kesitin çalışırken
#  üzerinden geçtiği kasnaklardır.  Standardın iki çözümlü örneği:
#     Şekil E.1 — 2:1 askı       Nps = 2   kabin kesiti iki kabin kasnağından
#                                          geçer;  hareketli kasnak ters
#                                          bükülme sayılmaz ( Npr = 0 )
#     Şekil E.2 — 1:1 askı       Nps = 1   tahrik kasnağının saptırma kasnağı
#  OFİS DÜZENİ:  2:1'de tahrik kasnağının saptırma kasnağı KARŞI AĞIRLIK
#  tarafındadır.  Ağırlık kesiti saptırma + ağırlık kasnağından geçer ( 2 ),
#  kabin kesiti iki kabin kasnağından ( 2 ) — ikisi de Şekil E.1'in sayısı.
#  Saptırma kabin tarafında olan bir düzende kabin kesiti 3 kasnaktan geçer;
#  o projede değer elle girilir.
#  ESKİ VARSAYILAN 1'Dİ ve 2:1'de programın kendi uyarısına ( "en az iki kabin
#  kasnağı" ) takılıyordu:  Nequiv küçük, gereken Sf olduğundan küçük çıkıyordu.
def kasnak_tek_yon_askidan(r):
    return 1 if r == 1 else 2


def kasnak_tek_yon(g):
    """( Nps , girildi_mi ).  Boşsa askı oranından türetilir."""
    d = g.get("kasnak_tek_yon")
    if d is None or (isinstance(d, str) and not d.strip()):
        return kasnak_tek_yon_askidan(g.get("aski_orani")), False
    return d, True
