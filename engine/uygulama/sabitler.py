# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİNİN OFİS STANDARDI            ( avandan AYRI )

Avan ve uygulama ayrı projelerdir:  ayrı mühendis, ayrı çıktı.  Kabulleri de aynı olmak ZORUNDA DEĞİLDİR — avan ön tasarımdır ve
genel, emniyetli kabullerle çalışır;  uygulama kesin tasarımdır ve elinde
imalatçı verisi vardır.  Dişlisiz makine için avanda 0,85 kabulü yeterliyken
uygulamada makinenin kataloğundaki 0,88 kullanılabilir.

BU, BUGÜN DÜZELTTİĞİMİZ η HATASININ TEKRARI DEĞİLDİR.  O hatada iki sayı
KODUN İÇİNDE, kimsenin göremediği yerde duruyordu;  görülemediği için ayrıştı
ve kimse fark etmedi.  Buradakiler ekranda durur, mühendis bilerek girer ve
pafta her değeri KAYNAĞIYLA birlikte basar.  Ayrışırlarsa bilerek ayrışırlar.

FABRİKA AYARI ortaktır:  engine/ortak/ofis.py.  İki proje de oradan başlar;
sonrası her projenin kendi kararıdır.
"""
from engine.avan import hesap as _AVAN
from engine.ortak import ofis as OFIS
from engine.uygulama import mukavemet_tablolari as MT

_AVAN_VARSAYILAN = {**_AVAN.SABIT_B_VARSAYILAN, **_AVAN.OFIS_VARSAYILAN}

#  Fiziksel dönüşümler ve STANDARDIN dayattığı sayılar buraya GİRMEZ:
#  gn · 102 · 1,34 · k3 = 1,2 ( EN 81-20 Çiz.14 ) · Dt/dh ≥ 40
#  ( EN 81-20 m.5.5.2.1 ).  Onlar ofis kabulü değildir, değiştirilemezler;
#  yerleri engine/uygulama/mukavemet.py içindeki SABIT sözlüğüdür.

VARSAYILAN = {
    # ── ① MAKİNE VE MOTOR ────────────────────────────────────────────
    "verim_dislisiz":   OFIS.MAKINE_VERIMLERI["Dişlisiz"],
    "verim_disli":      OFIS.MAKINE_VERIMLERI["Dişli"],
    #  Denge ( kompanzasyon ) zinciri TAKILDIĞINDA halat dengesizliğinin
    #  yüzde kaçını karşıladığı.  Zincir halatı dengelemek için takılır ve
    #  halat ağırlığına göre seçilir — bu yüzden varsayılan TAM DENGELEMEDİR.
    #  Zincirin metre ağırlığı sahada ölçülemediği için bir OFİS KABULÜDÜR:
    #  tedarikçisi bilerek hafif zincir takan bir ofis bu değeri düşürür ve
    #  bütün projeleri birden düzeltir.  Paftada λ satırında görünür.
    #  Tam dengeleme için gereken zincir:  askı oranı × halat kg/m × adet.
    "denge_zinciri_orani": 100,  # λ, %                       ( zincir VARSA )
    "Gs":               0,      # Sürtünme yükü, kg
    "q_denge":          0.50,   # Karşı ağırlık denge oranı
    "halat_pay_m":      5,      # Halat boyu payı, m

    #  ── TAHRİK KANALI GEOMETRİSİ ─────────────────────────────────────
    #  Kasnak kanalının açıları imalatçıdan gelir;  proje bazında
    #  bilinemedikleri için ofis kabulü olarak burada dururlar.
    #  TS EN 81-50 sınırları:  β ≤ 105°  ·  V kanalda γ ≥ 35°  ·  yarım
    #  daire kanalda γ ≥ 25°.
    "kanal_gama_v":    38,      # V kanal açısı γ            [°]
    "kanal_gama_yd":   25,      # Yarım daire kanal açısı γ  [°]
    "kanal_beta":      90,      # Alt kesilme açısı β        [°]

    # ── ② MUKAVEMET KABULLERİ ────────────────────────────────────────
    #  σem ve k1 STANDARDIN sayıları DEĞİLDİR.  TS EN 81-20 makine kaidesi
    #  için yük modeli vermez;  Çizelge 14 ( k1 ) o standartta açıkça
    #  KILAVUZ RAY hesabına aittir.  Buradaki kullanım ödünçtür ve emniyetli
    #  taraftadır — σem = 130, aynı standardın ST 37 için verdiği
    #  Rm/1,8 = 205,6 N/mm²'nin yaklaşık yarısıdır.  Ekranda durmalarının
    #  sebebi budur:  ofis bunları gözden geçirebilmelidir.
    "sigma_em":         130,    # ST 37 emniyet gerilmesi, N/mm²
    "k1_kaymali":       2,      # Kaymalı güvenlik tertibatı
    "k1_makarali":      3,      # Ani frenlemeli makaralı
    "k1_ani":           5,      # Ani frenlemeli
    #  TS EN 81-20 Çizelge 14:  k1 ve k2'nin değeri çizelgede YAZILIDIR
    #  ( k2 = 1,2 ), k3 için ise çizelge "the value has to be determined by
    #  the manufacturer due to the actual installation" der — yani standardın
    #  verdiği bir sayı YOKTUR.  Bu yüzden k3 ofis sabitidir, motorda çivili
    #  değildir;  varsayılanı 1,2'dir.
    "k3_yardimci":      1.2,    # Yardımcı donanım darbe katsayısı k3
    "yan_yatak_L_X":    335,    # Kaide kiriş mesnet payı, mm
    #  BURKULMA EKSENİ.  Çubuk EN KÜÇÜK atalet yarıçapına sahip eksende
    #  burkulur;  program bu yüzden min( ix ; iy ) kullanır.  Şase, dikine
    #  kirişi zayıf ekseninde yanal olarak MESNETLİYORSA burkulma o eksende
    #  olamaz ve λ güçlü eksenden ( ix ) hesaplanır.  Bu bir KABULDÜR:
    #  varsayılan 0'dır ( mesnet yok — emniyetli taraf ), ofis mesnedi
    #  çizimle gösterebiliyorsa 1 yapar.  ( 0 / 1 )
    "kaide_zayif_eksen_mesnetli": 0,

    # ── ②b KASNAK ATALETİ  ( TS EN 81-50 m.5.11.2.2 ) ────────────────
    #  Tahrik hesabındaki  Σ( mP·iP·a ) / r  terimi kasnağın ATALET
    #  MOMENTİNİ ister:  mP = J / R².  J bir bileşen özelliğidir ve
    #  standart onu imalatçıdan bekler — elimizde yoktur ve sahada da
    #  kimse veri sayfasından okuyup girmez.  Bu yüzden kasnak, çapı ve
    #  halat düzeni bilinen bir DÖKÜM DİSK olarak modellenir:
    #
    #      J = ½·π·ρ·A·( R⁴ − R₁⁴ )  +  ½·π·ρ·A₁·R₁⁴
    #      R  = Dp / 2          ( saptırma kasnaklarının ortalama çapı )
    #      R₁ = ( Dp − göbek ) / 2
    #      A  = ( ns−1 )·1,6·dr + kanal payı        ( kasnak genişliği )
    #      A₁ = A × göbek genişlik oranı
    #
    #  Aşağıdaki dört sayı STANDARTTA YOKTUR, ofis kabulüdür — ekranda
    #  durur ve değiştirilebilir.  Model, ELEport'un yayımlanmış örnek
    #  paftasıyla doğrulanmıştır:  Dp = 294 mm · 7 × 6,5 mm halat için
    #  J = 0,2920 kg·m² hesaplanır, paftalarında 0,29 yazar  ( %0,7 ).
    "kasnak_yogunluk":   7400,  # ρ — döküm kasnak, kg/m³
    "kasnak_gobek_pay":    40,  # Dp − 40  →  göbek incelme çapı, mm
    "kasnak_kanal_payi":   30,  # A bağıntısının sabit payı, mm
    "kasnak_gobek_orani": 0.25, # A₁ = A × 0,25
    #  Askı düzenine göre KASNAK ADEDİ.  Bu iki sayı TAHMİN DEĞİLDİR:
    #  TS EN 81-50 Ek D'nin 2:1 çözümlü örneği katsayıları AÇIK yazar —
    #      T1 … + mPcar · 2 · a / 2 …        ( kabin tarafı  : 2 kasnak )
    #      T2 … − mPcwt · 1 · a / 2 …        ( ağırlık tarafı: 1 kasnak )
    #  Başka bir düzende ( ör. kabin altında tek kasnak ) buradan değiştirilir.
    #  1:1'de kasnak yoktur, terim sıfırdır  ( koşul III ).
    "kasnak_adet_kabin":    2,  # r > 1 iken kabin tarafındaki kasnak sayısı
    "kasnak_adet_agirlik":  1,  # r > 1 iken ağırlık tarafındaki kasnak sayısı

    # ── ②c KUYU SÜRTÜNMESİ  ( TS EN 81-50 m.5.11.2.2 · Ek D ) ───────────
    #  Acil frenlemede kabinin ve karşı ağırlığın kılavuzlarda ve kasnak
    #  yataklarında gördüğü sürtünme.  Standart FRcar / FRcwt'yi "KUYUDAKİ
    #  sürtünme kuvveti" diye tanımlar, formüle FR / r olarak sokar ve "asgari
    #  bir sürtünme kuvveti sağlanamıyorsa silinmelidir" der — sayı vermez.
    #  Yüzde, o taraftaki GÖVDENİN frenleme sırasındaki ağırlık kuvvetine
    #  uygulanır:  kabin ( P + Q + MCR + MTrav )·( gn ± a ) ,  karşı ağırlık
    #  ( Mcwt + MCR )·( gn ∓ a ).  ELEport ve new block da böyle kurar.
    #  %2 / %1,5 new block'un ve ofisin değeridir;  ELEport ağırlık
    #  tarafında %2 alır.  Frenlemede sürtünme LEHE çalıştığı için küçük değer
    #  emniyetli taraftır.  Asgari sürtünme sağlanamıyorsa 0 yazılır.
    "kuyu_surtunme_kabin":   2,    # %
    "kuyu_surtunme_agirlik": 1.5,  # %

    # ── ③ SIĞINMA PAYLARI  ( kabin / kuyu geometrisi ) ───────────────
    #  Bunlar kabin imalatına bağlı ofis kabulleridir;  TS EN 81-20 sayısı
    #  DEĞİLDİR.  Standardın asgari açıklıkları ( 100 · 500 · 300 mm ve
    #  sığınma hacimleri ) burada YOKTUR — onlar değiştirilemez.
    "kabin_yuksekligi":  2400,
    "kabin_ust_donanim": 2100,
    "paten_payi":         300,
    "tavan_payi":         150,
    "revizyon_payi":      500,
    "etek_payi":          400,
    "etek_kotu":          950,
    "ray_alt_payi":       270,
    "regulator_payi":     300,

    #  ④ ⑤ ⑥ ELEKTRİK VARSAYILANLARI AVAN MOTORUNDAN OKUNUR.
    #  Bu hesaplar avan motorunda koşar ve köprü oraya yalnız DEĞİŞTİRİLEN
    #  değeri geçirir ( bkz. girdi._avan_sabitleri );  boş bırakılan alanı
    #  motor KENDİ varsayılanıyla hesaplar.  Burada ayrı bir sayı yazmak,
    #  ekranda motorun kullanmadığı bir değeri göstermek olurdu.
    **{k: _AVAN_VARSAYILAN[k] for k in (
        # ── ④ AYDINLATMA
        "kabin_armatur_W", "kabin_armatur_lm", "kabin_ustu_armatur",
        "kuyu_armatur_W", "kuyu_armatur_lm", "kuyu_Dmax", "ayd_sutun",
        # ── ⑤ KURULU GÜÇ VE GERİLİM DÜŞÜMÜ
        "U", "kappa", "eps_max", "cosfi", "motor_elektrik_verimi",
        "priz_adedi", "priz_gucu", "kablo_tipi", "sigorta_katsayisi",
        # ── ⑥ TOPRAKLAMA
        "beta", "cubuk_sayisi", "goz_araligi", "lc", "UL", "IDn")},
}

#  Metin alanları — sayı denetimine girmez
METIN = ("kablo_tipi",)

ARALIK = {
    "verim_dislisiz": (0.1, 1), "verim_disli": (0.1, 1),
    "denge_zinciri_orani": (0, 100), "Gs": (0, 5000), "q_denge": (0.2, 0.8),
    "halat_pay_m": (0, 100),
    #  Sınırlar tek yerde durur ( mukavemet_tablolari ):  standardın kendi
    #  m.5.11.2.3.1 sınırlarıdır ve iki dosyada ayrı ayrı yazılırsa ayrışır.
    "kanal_gama_v": (MT.GAMA_ASGARI_V, MT.GAMA_AZAMI),
    "kanal_gama_yd": (MT.GAMA_ASGARI_U, MT.GAMA_AZAMI),
    "kanal_beta": (0, MT.BETA_AZAMI),
    "sigma_em": (10, 400), "k1_kaymali": (1, 10), "k1_makarali": (1, 10),
    "k1_ani": (1, 10), "k3_yardimci": (1, 10),
    "yan_yatak_L_X": (0, 5000), "kaide_zayif_eksen_mesnetli": (0, 1),
    "kasnak_yogunluk": (1000, 20000), "kasnak_gobek_pay": (0, 500),
    "kasnak_kanal_payi": (0, 500), "kasnak_gobek_orani": (0, 1),
    "kasnak_adet_kabin": (0, 10), "kasnak_adet_agirlik": (0, 10),
    "kuyu_surtunme_kabin": (0, 10), "kuyu_surtunme_agirlik": (0, 10),
    "kabin_yuksekligi": (0, 10000), "kabin_ust_donanim": (0, 10000),
    "paten_payi": (0, 5000), "tavan_payi": (0, 5000),
    "revizyon_payi": (0, 5000), "etek_payi": (0, 5000),
    "etek_kotu": (0, 5000), "ray_alt_payi": (0, 5000),
    "regulator_payi": (0, 5000),
    "kabin_armatur_W": (0.1, 1000), "kabin_armatur_lm": (1, 100000),
    "kabin_ustu_armatur": (0, 20), "kuyu_armatur_W": (0.1, 1000),
    "kuyu_armatur_lm": (1, 100000), "kuyu_Dmax": (0, 100), "ayd_sutun": (1, 10),
    "U": (100, 1000), "kappa": (10, 100), "eps_max": (0.1, 20),
    "cosfi": (0.1, 1), "motor_elektrik_verimi": (0.1, 1), "priz_adedi": (0, 50), "priz_gucu": (0, 10000),
    "sigorta_katsayisi": (1, 4),
    "beta": (1, 100000), "cubuk_sayisi": (0, 100), "goz_araligi": (1, 200),
    "lc": (0.1, 50), "UL": (1, 1000), "IDn": (0.001, 10),
}

#  Ekran düzeni:  [ başlık, açıklama, alanlar ].  Uygulama projesi YALNIZ
#  bunları görür;  avanın MMO/697 kuvvet sabitleri burada YOKTUR.
GRUPLAR = (
    ("① MAKİNE VE MOTOR",
     "TS EN 81-50 · MMO 208/7 — motor gücü ve verim",
     ("verim_dislisiz", "verim_disli", "denge_zinciri_orani",
      "Gs", "q_denge", "halat_pay_m",
      "kanal_gama_v", "kanal_gama_yd", "kanal_beta")),
    ("② MUKAVEMET KABULLERİ",
     "makine kaidesi ve ray hesabı — TS EN 81-20 bu yük modelini VERMEZ, "
     "aşağıdakiler ofis kabulüdür",
     ("sigma_em", "k1_kaymali", "k1_makarali", "k1_ani", "k3_yardimci",
      "yan_yatak_L_X", "kaide_zayif_eksen_mesnetli")),
    ("②b KASNAK ATALETİ",
     "tahrik hesabındaki Σ( mP·iP·a )/r terimi — TS EN 81-50 kasnağın atalet "
     "momentini imalatçıdan ister;  aşağıdaki dört sayı kasnağı döküm disk "
     "olarak modelleyen OFİS KABULÜDÜR",
     ("kasnak_yogunluk", "kasnak_gobek_pay", "kasnak_kanal_payi",
      "kasnak_gobek_orani", "kasnak_adet_kabin", "kasnak_adet_agirlik")),
    ("②c KUYU SÜRTÜNMESİ",
     "acil frenlemede kılavuz ve kasnak yatağı sürtünmesi — TS EN 81-50 "
     "m.5.11.2.2 sayı vermez;  asgari sürtünme sağlanamıyorsa 0 yazılır",
     ("kuyu_surtunme_kabin", "kuyu_surtunme_agirlik")),
    ("③ SIĞINMA PAYLARI",
     "kabin gövde ve kuyu geometrisi — kabin imalatına bağlıdır, "
     "TS EN 81-20 sayısı değildir",
     ("kabin_yuksekligi", "kabin_ust_donanim", "paten_payi", "tavan_payi",
      "revizyon_payi", "etek_payi", "etek_kotu", "ray_alt_payi",
      "regulator_payi")),
    ("④ AYDINLATMA",
     "kabin · kuyu · makine dairesi aydınlatma hesapları",
     ("kabin_armatur_W", "kabin_armatur_lm", "kabin_ustu_armatur",
      "kuyu_armatur_W", "kuyu_armatur_lm", "kuyu_Dmax", "ayd_sutun")),
    ("⑤ KURULU GÜÇ VE GERİLİM DÜŞÜMÜ",
     "IEC 60364-5-52 — kurulu güç, hat akımı, kablo ve gerilim düşümü",
     ("U", "kappa", "eps_max", "cosfi", "motor_elektrik_verimi",
      "priz_adedi", "priz_gucu", "kablo_tipi", "sigorta_katsayisi")),
    ("⑥ TEMEL TOPRAKLAMA",
     "IEEE Std 80 · BYKHY — temel ve çubuk topraklayıcı",
     ("beta", "cubuk_sayisi", "goz_araligi", "lc", "UL", "IDn")),
)

ETIKET = {
    #  ── kasnak ataleti  ( TS EN 81-50 m.5.11.2.2 · Ek D )
    "kasnak_yogunluk": ("Kasnak malzemesi yoğunluğu ρ (kg/m³)",
                        "döküm kasnak;  J = ½·π·ρ·A·(R⁴−R₁⁴) + ½·π·ρ·A₁·R₁⁴"),
    "kasnak_gobek_pay": ("Kasnak göbek incelme payı (mm)",
                         "R₁ = ( Dp − pay ) / 2 — göbekteki et kalınlığı azalması"),
    "kasnak_kanal_payi": ("Kasnak genişliği sabit payı (mm)",
                          "A = ( ns−1 )·1,6·dr + pay — kanal dışındaki kenar payı"),
    "kasnak_gobek_orani": ("Kasnak göbek genişlik oranı",
                           "A₁ = A × oran — göbeğin incelmiş bölümünün genişliği"),
    "kasnak_adet_kabin": ("Kabin tarafındaki kasnak sayısı iPcar (adet)",
                          "TS EN 81-50 Ek D'nin 2:1 örneği  mPcar·2·a/2  yazar"),
    "kasnak_adet_agirlik": ("Ağırlık tarafındaki kasnak sayısı iPcwt (adet)",
                            "Ek D'nin aynı örneği  mPcwt·1·a/2  yazar"),
    #  ── kuyu sürtünmesi  ( TS EN 81-50 m.5.11.2.2 )
    "kuyu_surtunme_kabin": ("Kabin tarafı kuyu sürtünmesi FRcar (%)",
                            "( P + Q + MCR + MTrav )·( gn ± a ) kuvvetinin yüzdesi"),
    "kuyu_surtunme_agirlik": ("Ağırlık tarafı kuyu sürtünmesi FRcwt (%)",
                              "( Mcwt + MCR )·( gn ∓ a ) kuvvetinin yüzdesi"),
    "k3_yardimci": ("Yardımcı donanım darbe katsayısı k3",
                    "TS EN 81-20 Çizelge 14 k3'e SAYI VERMEZ — "
                    "'imalatçı tarafından, gerçek tesise göre belirlenir'"),
    "verim_dislisiz": ("Dişlisiz makine TOPLAM sistem verimi η",
                       "askı ( palanga ) kaybı DÂHİL — N = Gmax·v/(η·102)"),
    "verim_disli": ("Dişli makine TOPLAM sistem verimi η",
                    "redüktör ve askı ( palanga ) kaybı DÂHİL"),
    "denge_zinciri_orani": ("Denge zinciri dengeleme oranı λ (%)",
                            "zincir VARSA halat dengesizliğinin yüzde kaçını "
                            "karşıladığı — %100 = tam dengeleme"),
    "Gs": ("Sürtünme yükü Gs (kg)", "Gmax = F1 + Gs − Ga"),
    "q_denge": ("Denge faktörü q", "karşı ağırlık = P + q·Q;  0,50 yükün yarısını dengeler"),
    "halat_pay_m": ("Halat boyu payı (m)", "kuyu boyuna eklenen pay"),
    "kanal_gama_v": ("V kanal açısı γ (°)",
                     "TS EN 81-50 m.5.11.2.3.1.2 — asansörlerde 35°'den küçük olamaz"),
    "kanal_gama_yd": ("Yarım daire kanal açısı γ (°)",
                      "TS EN 81-50 m.5.11.2.3.1.1 — hiçbir durumda 25°'den küçük olamaz"),
    "kanal_beta": ("Alt kesilme açısı β (°)", "TS EN 81-50 — 105°'yi aşamaz"),
    "sigma_em": ("ST 37 emniyet gerilmesi σem (N/mm²)",
                 "makine kaidesi;  TS EN 81-20'nin ST 37 için verdiği Rm/1,8 = 205,6 N/mm²'den katıdır"),
    "k1_kaymali": ("k1 — kaymalı güvenlik tertibatı", "makine kaidesi darbe katsayısı"),
    "k1_makarali": ("k1 — ani frenlemeli makaralı", "makine kaidesi darbe katsayısı"),
    "k1_ani": ("k1 — ani frenlemeli", "makine kaidesi darbe katsayısı;  kaideyi kaymalıya göre 2,5 kat büyütür"),
    "yan_yatak_L_X": ("Yan yatak mesnet payı (mm)", "X = L − bu değer"),
    "kaide_zayif_eksen_mesnetli": (
        "Kaide zayıf ekseni mesnetli  ( 0 / 1 )",
        "0 = mesnet yok, λ en küçük atalet yarıçapından ( emniyetli ) · "
        "1 = şase zayıf ekseni bağlıyor, λ güçlü eksenden ( ix )"),
    "kabin_yuksekligi": ("Kabin gövde yüksekliği (mm)", "üst paten – ray üst ucu payı"),
    "kabin_ust_donanim": ("Kabin üstü kotu (mm)", "kabin üstü serbest yükseklik hesabında"),
    "paten_payi": ("Paten payı (mm)", ""),
    "tavan_payi": ("Kuyu tavanı payı (mm)", ""),
    "revizyon_payi": ("Revizyon kutusu payı (mm)", ""),
    "etek_payi": ("Etek payı (mm)", ""),
    "etek_kotu": ("Etek kotu (mm)", ""),
    "ray_alt_payi": ("Ray altı payı (mm)", ""),
    "regulator_payi": ("Regülatör payı (mm)", ""),
    "kabin_armatur_W": ("Kabin armatürü (W)", ""),
    "kabin_armatur_lm": ("Kabin armatürü ışık akısı (lm)", ""),
    "kabin_ustu_armatur": ("Kabin üstü armatür adedi", ""),
    "kuyu_armatur_W": ("Kuyu armatürü (W)", ""),
    "kuyu_armatur_lm": ("Kuyu armatürü ışık akısı (lm)", ""),
    "kuyu_Dmax": ("Armatürler arası azami aralık (m)", "0 = kontrol kapalı"),
    "ayd_sutun": ("Aydınlatma tablosu sütunu", "tavan .80 / duvar .50 / zemin .10"),
    "U": ("Şebeke gerilimi (V)", "fazlar arası"),
    "kappa": ("İletken iletkenliği κ (m/Ω·mm²)",
              "bakır, normal çalışma = 44,4  ( TS HD 60364-5-52 EK-G )"),
    "eps_max": ("İzin verilen gerilim düşümü (%)", ""),
    "cosfi": ("Güç katsayısı cosφ", ""),
    "motor_elektrik_verimi": ("Motorun elektrik verimi ηm",
                              "şebekeden çekilen güç = mil gücü / ηm;  kablo ve sigorta bu akıma göre seçilir"),
    "priz_adedi": ("Priz adedi", ""),
    "priz_gucu": ("Priz gücü (W)", ""),
    "kablo_tipi": ("Kablo tipi", "akım taşıma kapasitesi bu tipten okunur"),
    "sigorta_katsayisi": ("Motor sigortası kalkış katsayısı",
                          "sigorta = bu katsayı × motor akımı, standart kademeye yuvarlanır"),
    "beta": ("Toprak özgül direnci β (Ω·m)", ""),
    "cubuk_sayisi": ("Çubuk topraklayıcı adedi", ""),
    "goz_araligi": ("Karelaj gözü (m)", ""),
    "lc": ("Çubuk topraklayıcı boyu (m)", ""),
    "UL": ("İzin verilen temas gerilimi UL (V)", "TT sistem"),
    "IDn": ("Kaçak akım rölesi anma akımı IΔn (A)", ""),
}


def sabitler(ozel=None):
    """Ofis standardı + kullanıcının ezmeleri.

    Geçersiz değer YOK SAYILIR ve varsayılan kullanılır;  reddedilenlerin
    listesi ``_reddedilen`` anahtarında döner — sessizce düşmesin.
    """
    s = dict(VARSAYILAN)
    reddedilen = []
    for k, v in (ozel or {}).items():
        if v is None or k not in VARSAYILAN:
            continue
        if k in METIN:
            metin = str(v).strip()
            if metin:
                s[k] = metin
            continue
        if isinstance(v, bool) or not isinstance(v, (int, float)):
            reddedilen.append(k)
            continue
        alt, ust = ARALIK.get(k, (None, None))
        if alt is not None and not (alt <= v <= ust):
            reddedilen.append(k)
            continue
        s[k] = v
    s["_reddedilen"] = reddedilen
    return s


def verim(S, makine_tipi):
    """η  —  ofis sabitlerinden okunan TOPLAM SİSTEM VERİMİ.

    Askı ( palanga ) kaybı bu değerin İÇİNDEDİR;  askı oranına bağlı ayrı
    bir düzeltme YOKTUR ( bkz. engine/ortak/ofis.py — "PALANGA VERİM
    DÜŞÜŞÜ KALDIRILDI" ).  Tanınmayan makine tipinde ortak fabrika ayarına
    dönülür.
    """
    eta = {"Dişlisiz": S.get("verim_dislisiz"),
           "Dişli": S.get("verim_disli")}.get(makine_tipi)
    return OFIS.VARSAYILAN_VERIM if eta is None else eta


def darbe_k1(S, tertibat):
    """k1  —  güvenlik tertibatı tipine göre, ofis sabitlerinden."""
    return {"Kaymalı": S.get("k1_kaymali"),
            "Ani Frenlemeli Makaralı": S.get("k1_makarali"),
            "Ani Frenlemeli": S.get("k1_ani")}.get(tertibat, MT.darbe_k1(tertibat))
