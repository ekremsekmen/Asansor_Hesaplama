# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ  —  MUKAVEMET HESABI TABLOLARI

Kaynak:  MUKAVEMET_FİNAL.xlsx  ( TABLOLAR · TEKNİK · Veri Girişi sayfaları )
Değerler o dosyadan MAKİNE İLE aktarılmıştır, elle yazılmamıştır;
testler/test_mukavemet_tablolari.py aynı dosyaya karşı birebir doğrular.

AVAN MODÜLÜNDEN AYRIDIR.  Avan tarafı MMO/697'yi uygular ( engine/tables.py );
burası uygulama projesinin kendi kaynağını uygular.  İki tarafın ortak konuları
( ör. kabin alanı ) BİLEREK ayrı tutulur — dayanakları farklıdır ve paftalarda
kaynakları da ayrı yazılır.
"""


def _sayi(x):
    """Sayı mı  ( bool tuzağı dâhil )."""
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def _ara(tablo, anahtar, sutun=1):
    """Excel'in DÜŞEYARA( … ; 0 ) karşılığı — birebir eşleşme, yoksa None."""
    for satir in tablo:
        if satir[0] == anahtar:
            return satir[sutun]
    return None


# =====================================================================
#  KILAVUZ RAY PROFİLLERİ  ( ISO 7465 )        [ TABLOLAR!I60:S65 ]
#  Hesabın EN ÇOK okuduğu tablo — 49 atıf.
#      Gr kg/m · A mm² · Ix mm⁴ · Iy mm⁴ · Wx mm³ · Wy mm³ · ix mm · iy mm
#      c mm ( flanş ) · e mm
# =====================================================================
RAY_PROFILI = (
    ('50 x 50 x 5', 3.7, 475, 112400, 52500, 3150, 2100, 15.38, 10.51, 5, 14.3),
    ('70 x 65 x 9', 7.47, 951, 413000, 186500, 9240, 5350, 20.9, 14, 6, 20.4),
    ('89 x 62 x 15,88', 12.38, 1577, 598300, 524100, 14350, 11780, 19.48, 18.23, 9.5, 20.32),
    ('90 x 75 x 16', 13.55, 1730, 1020000, 530000, 20870, 11800, 24.3, 17.5, 10, 26.1),
    ('125 x 82 x 16', 18, 2290, 1511000, 1566000, 26200, 25100, 25.7, 25.2, 10, 24.3),
    ('127 x 89 x 16', 22.48, 2863, 1984000, 2300000, 30900, 36200, 26.3, 28.3, 10, 24.7),
)

RAY_PROFILLERI = tuple(s[0] for s in RAY_PROFILI)
_RAY_SUTUN = {"Gr": 1, "A": 2, "Ix": 3, "Iy": 4, "Wx": 5, "Wy": 6,
              "ix": 7, "iy": 8, "c": 9, "e": 10}


def ray(profil, ozellik):
    """Ray profilinin bir özelliği.  ozellik: Gr/A/Ix/Iy/Wx/Wy/ix/iy/c/e"""
    return _ara(RAY_PROFILI, profil, _RAY_SUTUN[ozellik])


# =====================================================================
#  RAY PROFİLİ — FLANŞ GEOMETRİSİ             [ TABLOLAR!I69:N74 ]
#      f mm · b mm · h1 mm · (h1−b−f) mm · (h1−f) mm
# =====================================================================
RAY_GEOMETRI = (
    ('50 x 50 x 5', 8, 13.5, 50, 28.5, 42),
    ('70 x 65 x 9', 8, 17, 65, 40, 57),
    ('89 x 62 x 15,88', 11.1, 17, 62, 33.9, 50.9),
    ('90 x 75 x 16', 10, 21, 75, 44, 65),
    ('125 x 82 x 16', 12, 21, 82, 49, 70),
    ('127 x 89 x 16', 15.9, 25.5, 89, 47.6, 73.1),
)

_RAY_GEO_SUTUN = {"f": 1, "b": 2, "h1": 3, "h1_b_f": 4, "h1_f": 5}


def ray_geo(profil, ozellik):
    return _ara(RAY_GEOMETRI, profil, _RAY_GEO_SUTUN[ozellik])


# =====================================================================
#  ASKI HALATLARI  ( TS 12385-5 )              [ TABLOLAR!A32:F43 ]
#      çap mm · 1 m ağırlık kg · en küçük kopma yükü N · tip · sınıf
# =====================================================================
HALAT = (
    (6, 0.129, 23100, '6x19 Lif Özlü', 1770),
    (6.5, 0.152, 24700, '6x19 Lif Özlü', 1770),
    (7, 0.1795, 27400, '6x19 Lif Özlü', 1770),
    (8, 0.23, 31700, '6x19 Lif Özlü', '1370/1770'),
    (9, 0.291, 40100, '6x19 Lif Özlü', '1370/1770'),
    (10, 0.34, 49500, '6x19 Lif Özlü', '1370/1770'),
    (11, 0.411, 53200, '8x19 Lif Özlü', '1370/1770'),
    (12, 0.49, 63300, '8x19 Lif Özlü', '1370/1770'),
    (13, 0.575, 74300, '8x19 Lif Özlü', '1370/1770'),
    (14, 0.666, 86100, '8x19 Lif Özlü', '1370/1770'),
    (15, 0.765, 98900, '8x19 Lif Özlü', '1370/1770'),
    (16, 0.87, 113000, '8x19 Lif Özlü', '1370/1770'),
)

HALAT_CAPLARI = tuple(s[0] for s in HALAT)


def halat_agirlik(cap):
    """Halatın 1 m'sinin ağırlığı, kg."""
    return _ara(HALAT, cap, 1)


def halat_kopma(cap):
    """Halatın en küçük kopma yükü Tmin, N."""
    return _ara(HALAT, cap, 2)


def halat_tipi(cap):
    return _ara(HALAT, cap, 3)


# =====================================================================
#  BURKULMA KATSAYISI  ω   ( λ = 20 … 250, adım 1 )   [ TABLOLAR!A47:B277 ]
# =====================================================================
OMEGA_LAMBDA_MIN, OMEGA_LAMBDA_MAX = 20, 250
OMEGA = (
    1.04, 1.04, 1.04, 1.05, 1.05, 1.06,
    1.06, 1.06, 1.07, 1.08, 1.08, 1.09,
    1.09, 1.1, 1.1, 1.11, 1.11, 1.12,
    1.13, 1.13, 1.14, 1.14, 1.15, 1.16,
    1.16, 1.17, 1.18, 1.19, 1.19, 1.2,
    1.21, 1.22, 1.23, 1.23, 1.24, 1.25,
    1.26, 1.27, 1.28, 1.29, 1.3, 1.31,
    1.32, 1.33, 1.34, 1.35, 1.36, 1.37,
    1.39, 1.4, 1.41, 1.42, 1.44, 1.45,
    1.46, 1.48, 1.49, 1.5, 1.52, 1.53,
    1.55, 1.56, 1.58, 1.59, 1.61, 1.62,
    1.64, 1.66, 1.68, 1.69, 1.71, 1.73,
    1.74, 1.76, 1.78, 1.8, 1.82, 1.84,
    1.86, 1.88, 1.9, 1.92, 1.94, 1.96,
    1.98, 2, 2.02, 2.05, 2.07, 2.09,
    2.11, 2.14, 2.16, 2.18, 2.21, 2.23,
    2.27, 2.31, 2.35, 2.39, 2.43, 2.47,
    2.51, 2.55, 2.6, 2.64, 2.68, 2.72,
    2.77, 2.81, 2.85, 2.9, 2.94, 2.99,
    3.03, 3.08, 3.12, 3.17, 3.22, 3.26,
    3.31, 3.36, 3.41, 3.45, 3.5, 3.55,
    3.6, 3.65, 3.7, 3.75, 3.8, 3.85040487,
    3.90157248, 3.9530778300000002, 4.00492092, 4.05710175, 4.10962032, 4.1624766300000005,
    4.21567068, 4.26920247, 4.323072, 4.37727927, 4.43182428, 4.48670703,
    4.54192752, 4.59748575, 4.65338172, 4.70961543, 4.76618688, 4.82309607,
    4.880343, 4.93792767, 4.99585008, 5.05411023, 5.11270812, 5.17164375,
    5.23091712, 5.29052823, 5.35047708, 5.41076367, 5.471388, 5.53235007,
    5.59364988, 5.6552874300000004, 5.71726272, 5.77957575, 5.84222652, 5.90521503,
    5.96854128, 6.03220527, 6.096207, 6.16054647, 6.22522368, 6.29023863,
    6.35559132, 6.42128175, 6.48730992, 6.55367583, 6.62037948, 6.68742087,
    6.7548, 6.82251687, 6.89057148, 6.95896383, 7.02769392, 7.09676175,
    7.1661673200000005, 7.23591063, 7.30599168, 7.37641047, 7.447167, 7.51826127,
    7.58969328, 7.66146303, 7.73357052, 7.80601575, 7.87879872, 7.95191943,
    8.02537788, 8.09917407, 8.173308, 8.24777967, 8.32258908, 8.39773623,
    8.47322112, 8.54904375, 8.62520412, 8.70170223, 8.77853808, 8.85571167,
    8.933223, 9.01107207, 9.089258880000001, 9.16778343, 9.24664572, 9.325845750000001,
    9.40538352, 9.48525903, 9.56547228, 9.64602327, 9.726912, 9.80813847,
    9.88970268, 9.97160463, 10.05384432, 10.13642175, 10.21933692, 10.30258983,
    10.38618048, 10.47010887, 10.554375,
)



def omega(lam):
    """Kaynak Excel'in ω tablosundan okur  ( YALNIZ Rm = 370 eğrisi ).

    Yeni kodda kullanmayın — ω çeliğin çekme dayanımına göre değişir,
    bkz. omega_en8150().  Bu işlev tabloyu Excel'e karşı doğrulayan test
    için ve geriye dönük uyum için duruyor.
    """
    if not _sayi(lam):
        return None
    lam = int(lam)
    if OMEGA_LAMBDA_MIN <= lam <= OMEGA_LAMBDA_MAX:
        return OMEGA[lam - OMEGA_LAMBDA_MIN]
    return None


# ---------------------------------------------------------------------
#  ω  —  TS EN 81-50 m.5.10.3  ( burkulma, "omega" yöntemi )
# ---------------------------------------------------------------------
#  ω YALNIZ narinliğe değil, RAY ÇELİĞİNİN ÇEKME DAYANIMINA da bağlıdır.
#  Standart iki eğri verir ( Rm = 370 ve Rm = 520 ) ve aradaki dayanımlar
#  için doğrusal ara değer ister:
#
#      ω(λ) = ω370(λ) + ( ω520(λ) − ω370(λ) ) · ( Rm − 370 ) / ( 520 − 370 )
#
#  Standardın kendi notu:  işlenmiş raylarda 440 N/mm² yaygın olduğu için
#  bu ara değerleme "her zaman yapılmalıdır".
#
#  KAYNAK EXCEL'İN TABLOSU YALNIZ Rm = 370 EĞRİSİDİR ( 231/231 değeri
#  aşağıdaki OMEGA_370 formülleriyle birebir çıkar ).  Excel bu tabloyu
#  ray çeliğinden bağımsız kullanır;  440 ve 520 için ω'yı %23 ve %50
#  DÜŞÜK verir, yani burkulma gerilmesini olduğundan küçük gösterir.
OMEGA_370 = ((60, 0.00012920, 1.89, 1.0),
             (85, 0.00004627, 2.14, 1.0),
             (115, 0.00001711, 2.35, 1.04),
             (250, 0.00016887, 2.00, 0.0))
OMEGA_520 = ((50, 0.00008240, 2.06, 1.021),
             (70, 0.00001895, 2.41, 1.05),
             (89, 0.00002447, 2.36, 1.03),
             (250, 0.00025330, 2.00, 0.0))
OMEGA_RM_ALT, OMEGA_RM_UST = 370, 520


def _omega_egri(egri, lam):
    for ust, kat, us, ek in egri:
        if lam <= ust:
            return kat * lam ** us + ek
    return None


def omega_en8150(lam, rm=OMEGA_RM_ALT):
    """ω  ( TS EN 81-50 m.5.10.3 )  —  narinlik ve ray çeliğine göre."""
    if not (_sayi(lam) and _sayi(rm)):
        return None
    if not (OMEGA_LAMBDA_MIN <= lam <= OMEGA_LAMBDA_MAX):
        return None
    a = _omega_egri(OMEGA_370, lam)
    if rm <= OMEGA_RM_ALT:
        return a
    b = _omega_egri(OMEGA_520, lam)
    if rm >= OMEGA_RM_UST:
        return b
    return a + (b - a) * (rm - OMEGA_RM_ALT) / (OMEGA_RM_UST - OMEGA_RM_ALT)


# =====================================================================
#  NPU / NPI PROFİLLERİ  ( makine kaidesi kirişleri )  [ TABLOLAR!M36:AH53 ]
#      A cm² · G kg/m · Ix cm⁴ · Wx cm³ · ix cm · Iy cm⁴ · Wy cm³ · iy cm
#  NOT:  Excel'de AB38 satırı "Imin — eylemsizlik momenti" diye etiketli ama
#  okuduğu sütun ix'tir ( atalet yarıçapı ) ve λ = L1 / imin'de öyle kullanılır.
#  Buradaki ad matematiğe göre verilmiştir.
# =====================================================================
NPU_PROFIL = (
    ('30x15', 2.21, 1.74, 2.21, 1.69, 1.07, 0.38, 0.39, 0.42),
    (30, 5.44, 4.27, 6.39, 4.26, 1.08, 5.33, 2.68, 0.99),
    ('40x20', 3.66, 2.87, 7.58, 3.79, 1.44, 1.14, 0.86, 0.56),
    (40, 6.21, 4.87, 14.1, 7.05, 1.5, 6.68, 3.08, 1.04),
    ('50x25', 4.92, 3.86, 16.8, 6.73, 1.85, 2.49, 1.48, 0.71),
    (50, 7.12, 5.59, 26.4, 10.6, 1.92, 9.12, 3.75, 1.13),
    (60, 6.46, 5.07, 31.6, 10.5, 2.21, 4.51, 2.16, 0.84),
    (65, 9.03, 7.09, 57.5, 17.7, 2.52, 14.1, 5.07, 1.25),
    (80, 11, 8.64, 106, 26.5, 3.1, 19.4, 6.36, 1.33),
    (100, 13.5, 10.6, 206, 41.2, 3.91, 29.3, 8.49, 1.47),
    (120, 17, 13.4, 364, 60.7, 4.62, 43.2, 11.1, 1.59),
    (140, 20.4, 16, 605, 86.4, 5.45, 62.7, 14.8, 1.75),
    (160, 24, 18.8, 925, 116, 6.21, 85.3, 18.3, 1.89),
    (180, 28, 22, 1350, 150, 6.95, 114, 22.4, 2.02),
    (200, 32.2, 25.3, 1910, 191, 7.7, 148, 27, 2.14),
    (240, 42.3, 33.2, 3600, 300, None, 248, 39.6, None),
    (280, 47.5, 41.8, 6280, 448, None, 399, 57.2, None),
    (300, 50, 46.2, 8030, 535, None, 495, 67.8, None),
)

NPU_OLCULERI = tuple(r[0] for r in NPU_PROFIL)

_NPU_SUTUN = {"A": 1, "G": 2, "Ix": 3, "Wx": 4, "ix": 5,
              "Iy": 6, "Wy": 7, "iy": 8}


def npu(olcu, ozellik):
    """NPU/NPI profil özelliği.  olcu sayı ( 120 ) ya da metin ( '30x15' )."""
    return _ara(NPU_PROFIL, olcu, _NPU_SUTUN[ozellik])


# =====================================================================
#  KABİN ALANI  ( beyan yükü → kişi · en büyük · en küçük alan )
#                                               [ TABLOLAR!H78:K99 ]
#  DİKKAT:  Avan modülünün MMO/697 Tablo-11'i ile 22 satırın 21'i AYNIDIR;
#  tek fark burada 320 kg satırının BULUNMASIDIR ( kitapta yok ).  İki tablo
#  bilerek ayrı tutulur — biri kitabı, diğeri bu hesabın kaynağını uygular.
# =====================================================================
#  KAYNAK KİTABIN TABLOSU EKSİKTİ.  EN 81-20 Çizelge 6'nın 28 beyan yükünden
#  7'si kitapta yoktu ( 100 · 1050 · 1250 · 1350 · 1425 · 1500 · 2500 kg ) ve
#  açılır liste kapalı olduğu için o yüklerde HİÇ hesap yapılamıyordu — 1250
#  ve 1500 kg yaygın asansörlerdir.  Tablo standarda tamamlandı;  eklenen
#  satırlar aşağıda ★ ile işaretlidir.
#
#  Sütunlar:  beyan yükü · kişi · azami alan ( Çiz.6 ) · asgari alan ( Çiz.8 )
#  Kişi sayısı m.5.4.2.3.1 a):  Q/75, aşağı yuvarlanır.
#  Çizelge 8'de 20 kişiden sonrası:  3,13 + 0,115 × ( kişi − 20 ).
KABIN_ALANI = (
    (100, 1, 0.37, 0.28),          # ★ Çiz.6 — tek kişilik asansör asgarisi
    (180, 2, 0.58, 0.49),
    (225, 3, 0.7, 0.6),
    (300, 4, 0.9, 0.79),
    (320, 4, 0.953, 0.79),   # Çiz.6'da YOK — 300/375 arası doğrusal ara değer
    (375, 5, 1.1, 0.98),
    (400, 5, 1.17, 0.98),
    (450, 6, 1.3, 1.17),
    (525, 7, 1.45, 1.31),
    (600, 8, 1.6, 1.45),
    (630, 8, 1.66, 1.45),
    (675, 9, 1.75, 1.59),
    (750, 10, 1.9, 1.73),
    (800, 10, 2, 1.73),
    (825, 11, 2.05, 1.87),
    (900, 12, 2.2, 2.01),
    (975, 13, 2.35, 2.15),
    (1000, 13, 2.4, 2.15),
    (1050, 14, 2.5, 2.29),      # ★
    (1125, 15, 2.65, 2.43),
    (1200, 16, 2.8, 2.57),
    (1250, 16, 2.9, 2.57),      # ★
    (1275, 17, 2.95, 2.71),
    (1350, 18, 3.1, 2.85),      # ★
    (1425, 19, 3.25, 2.99),     # ★
    (1500, 20, 3.4, 3.13),      # ★
    (1600, 21, 3.56, 3.245),
    (2000, 26, 4.2, 3.82),
    (2500, 33, 5.0, 4.625),     # ★  Çiz.6'nın son satırı
)



#  ---------------------------------------------------------------------
#  RAY TABLOSUNUN KENDİ TUTARLILIĞI
#  ---------------------------------------------------------------------
#  Atalet yarıçapı tanımı gereği  i = √( I / A )  olmalıdır.  Kaynak kitabın
#  kendi 60. satırı bunu FORMÜLLE hesaplar ( =ROUND(SQRT(L60/K60),2) ), yani
#  ofisin tanımı da budur;  ama iki satırda elle yazılmış değerler tutmuyor:
#
#      70 x 65 x 9      ix  20,90   √(Ix/A) = 20,84   %0,3
#      125 x 82 x 16    iy  25,20   √(Iy/A) = 26,15   %3,6
#
#  125'lik satırda A, Ix ve ix birbiriyle tutarlıdır ( √(1511000/2290) =
#  25,69 ≈ 25,7 );  tutmayan TEK sayı iy'dir.  Hangisinin doğru olduğu ISO
#  7465'in kendi tablosundan teyit edilmelidir — elimizde o yok.
#
#  DEĞER DEĞİŞTİRİLMEDİ:  tabloda duran küçük iy, narinliği ( λ = l/i ) BÜYÜK
#  gösterir, dolayısıyla ω ve burkulma gerilmesi de büyük çıkar — yani
#  emniyetli taraftadır.  Doğrulanmamış bir sayıyı emniyetsiz yönde
#  değiştirmek yerine tutarsızlık burada AÇIKÇA işaretlenir.
#  %0,5 eşiğini AŞAN satır:  70'likteki %0,3 yuvarlama payı içindedir.
RAY_TUTARSIZ = ("125 x 82 x 16",)


def ray_tutarsizliklari(tolerans=0.005):
    """i ≠ √(I/A) olan satırlar  →  [ ( profil, eksen, tablo, hesap ) ]."""
    import math as _m
    bulunan = []
    for satir in RAY_PROFILI:
        ad = satir[0]
        A = ray(ad, "A")
        for eksen, atalet in (("ix", "Ix"), ("iy", "Iy")):
            tablo = ray(ad, eksen)
            hesap = _m.sqrt(ray(ad, atalet) / A)
            if abs(tablo - hesap) > tolerans * hesap:
                bulunan.append((ad, eksen, tablo, round(hesap, 3)))
    return bulunan


def kabin_kisi(beyan_yuku):
    return _ara(KABIN_ALANI, beyan_yuku, 1)


def kabin_azami_alan(beyan_yuku):
    """Kullanılabilir EN BÜYÜK kabin alanı, m²."""
    return _ara(KABIN_ALANI, beyan_yuku, 2)


def kabin_asgari_alan(beyan_yuku):
    """Kullanılabilir EN KÜÇÜK kabin alanı, m²."""
    return _ara(KABIN_ALANI, beyan_yuku, 3)


# =====================================================================
#  TAHRİK KASNAĞI KANAL ŞEKLİ            [ TABLOLAR!D47:G52 ]
# =====================================================================
#  KANAL AÇISI ARTIK TABLODA DEĞİL, OFİS SABİTİDİR.
#
#  Kitabın tablosu her kanal şeklinin karşısına TEK bir açı ve TEK bir
#  Nequiv(t) yazar ( V → 38° / 12 ,  altı kesik → 90° / 5 ).  O sütun
#  aslında iki ayrı büyüklüğü karıştırır:  V kanalda γ ( kanal açısı ),
#  altı kesik kanalda β ( alt kesilme açısı ).  Üstelik ikisi de DONDURULMUŞ:
#  ofis sabitlerinden γ = 45° seçilse bile tablo 38 yazmaya, Nequiv(t) 12
#  kalmaya devam ediyordu — pafta hesabın kullandığı sayıyı yazmıyordu.
#
#  TS EN 81-50 m.5.12.2.2 Çizelge 2 Nequiv(t)'yi doğrudan bu açıların
#  fonksiyonu verir ve "çizelgede olmayan açılar için doğrusal ara değer"
#  ister.  Tablo artık şeklin YALNIZ TÜRÜNÜ tutar;  açılar ofis
#  sabitlerinden gelir ve Nequiv(t) onlardan hesaplanır.
#
#     tür    anlamı                             f bağıntısı ( m.5.11.2.3.1 )
#     'V'    V kanal, alt kesilmesiz            m.5.11.2.3.1.2   ( β = 0 )
#     'VK'   V kanal, altı kesik                m.5.11.2.3.1.2   ( β )
#     'U'    yarım daire, alt kesilmesiz        m.5.11.2.3.1.1   ( β = 0 )
#     'UK'   yarım daire, altı kesik            m.5.11.2.3.1.1   ( β )
#
#  ( ad , tür , tahrik kasnağı üzerinden geçiş sayısı )
KANAL_SEKLI = (
    ('V Kanal',                       'V',  1),
    ('Altı Kesik V Kanal',            'VK', 1),
    ('Yarım Daire Kanal',             'U',  1),
    ('Altı Kesik Yarım Daire Kanal',  'UK', 1),
    #  Çift sarımda halat tahrik kasnağının üzerinden İKİ kez geçer;  her
    #  geçiş bir basit eğilmedir, bu yüzden Nequiv(t) iki katıdır.
    ('Yarım Daire Kanal (Çift Sarım)', 'U', 2),
)

KANAL_SEKILLERI = tuple(s[0] for s in KANAL_SEKLI)


def kanal_turu(sekil):
    """Kanalın türü:  'V' · 'VK' · 'U' · 'UK'  ( bilinmeyen şekilde None )."""
    return _ara(KANAL_SEKLI, sekil, 1)


def kanal_gecis_sayisi(sekil):
    """Halatın tahrik kasnağı üzerinden geçiş sayısı  ( çift sarımda 2 )."""
    return _ara(KANAL_SEKLI, sekil, 2)


# ---------------------------------------------------------------------
#  TS EN 81-50 m.5.12.2.2  Çizelge 2  —  Nequiv(t)
# ---------------------------------------------------------------------
#      V kanal          γ  35°   36°   38°   40°   42°   45°   50°
#                  Nequiv(t) 18,5   16    12    10     8   6,5     5
#      Altı kesik U     β  75°   80°   85°   90°   95°  100°  105°
#                  Nequiv(t)  2,5   3,0   3,8   5,0   6,7  10,0  15,2
#      Alt kesilmesiz U         Nequiv(t) = 1
#  "Values for angles not in the table may be determined by linear
#   interpolation."  —  çizelgenin kendi notu.
NEQUIV_V = ((35, 18.5), (36, 16.0), (38, 12.0), (40, 10.0),
            (42, 8.0), (45, 6.5), (50, 5.0))
NEQUIV_U_ALTI_KESIK = ((75, 2.5), (80, 3.0), (85, 3.8), (90, 5.0),
                       (95, 6.7), (100, 10.0), (105, 15.2))

#  m.5.11.2.3.1.1 / m.5.11.2.3.1.2'nin kendi sınırları
BETA_AZAMI = 105.0        # "shall not exceed 105° (1,83 rad)"
GAMA_ASGARI_U = 25.0      # yarım daire:  "in no case … less than 25°"
GAMA_ASGARI_V = 35.0      # V kanal:  "in no case, angle γ shall be less than 35°"
GAMA_AZAMI = 90.0         # γ bir kanal açısıdır;  90°'yi aşamaz


def _dogrusal_ara(tablo, x):
    """Çizelge 2 için doğrusal ara değer;  aralık dışında uç değere sabitler."""
    if not _sayi(x):
        return None
    if x <= tablo[0][0]:
        return tablo[0][1]
    if x >= tablo[-1][0]:
        return tablo[-1][1]
    for (x0, y0), (x1, y1) in zip(tablo, tablo[1:]):
        if x0 <= x <= x1:
            return y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return None


def kanal_acisi(sekil, gama_v=None, gama_yd=None):
    """Hesapta KULLANILAN γ  ( kanal açısı ).  Alt kesilme açısı β değildir.

    Kitabın tablosu altı kesik kanallarda bu sütuna β yazıyordu;  pafta
    "γ = 90°" basıp hesapta 38° kullanıyordu.
    """
    tur = kanal_turu(sekil)
    if tur is None:
        return None
    return gama_yd if tur in ("U", "UK") else gama_v


def kanal_beta(sekil, beta=None):
    """Alt kesilme açısı β.  Alt kesilmesi olmayan kanalda 0'dır."""
    return beta if kanal_alti_kesik_mi(sekil) else 0.0


#  ---------------------------------------------------------------------
#  KANAL ŞEKLİNİN SÜRTÜNME BAĞINTISI
#  ---------------------------------------------------------------------
#  TS EN 81-50 sürtünme çarpanı f için İKİ AYRI madde verir:
#
#    m.5.11.2.3.1.1  YARIM DAİRE ( ve altı kesik yarım daire ) kanal
#        f = μ · 4( cos(γ/2) − sin(β/2) ) / ( π − β − γ − sin β + sin γ )
#        γ imalatçıdan gelir, hiçbir durumda 25°'den küçük olamaz.
#
#    m.5.11.2.3.1.2  V KANAL
#        sertleştirilmemiş, yükleme / acil frenleme :
#            f = μ · 4( 1 − sin(β/2) ) / ( π − β − sin β )        ( γ girmez )
#        sertleştirilmiş                            :  f = μ / sin(γ/2)
#        ağırlık bloke ( ikisinde de )              :  f = μ / sin(γ/2)
#        γ asansörlerde 35°'den küçük olamaz.
#
#  Kaynak kitap kanal şeklinden BAĞIMSIZ olarak hep V kanal bağıntısını
#  kullanıyordu;  yarım daire seçilebildiği hâlde onun maddesi hiç
#  uygulanmıyordu ( bkz. EXCEL_FARKLARI ).
KANAL_YARIM_DAIRE = tuple(a for a, t, _g in KANAL_SEKLI if t in ("U", "UK"))
#  Altı kesik olanlar:  β = alt kesilme açısı;  ötekilerde β = 0.
KANAL_ALTI_KESIK = tuple(a for a, t, _g in KANAL_SEKLI if t in ("VK", "UK"))


def kanal_yarim_daire_mi(sekil):
    return sekil in KANAL_YARIM_DAIRE


def kanal_alti_kesik_mi(sekil):
    return sekil in KANAL_ALTI_KESIK


def kanal_nequiv_t(sekil, gama_v=None, beta=None):
    """Kasnakların eşdeğer sayısı Nequiv(t)  ( TS EN 81-50 Çizelge 2 ).

    Kitap bunu kanalın ADINA bağlı sabit bir tablodan okuyordu;  ofis
    sabiti γ ya da β değiştiğinde kımıldamıyordu.  Çizelge 2 ise Nequiv(t)'yi
    doğrudan o açıların fonksiyonu verir.
    """
    tur = kanal_turu(sekil)
    if tur is None:
        return None
    gecis = kanal_gecis_sayisi(sekil) or 1
    if tur == "V":
        taban = _dogrusal_ara(NEQUIV_V, gama_v)
    elif tur in ("VK", "UK"):
        #  Altı kesik kanal — V de olsa U da olsa Çizelge 2'nin alt kesilme
        #  satırı geçerlidir;  belirleyici olan β'dır.
        taban = _dogrusal_ara(NEQUIV_U_ALTI_KESIK, beta)
    else:                                   # 'U' — alt kesilmesiz yarım daire
        taban = 1.0
    return None if taban is None else taban * gecis


# =====================================================================
#  DARBE KATSAYISI  k1   ( TS EN 81-20 Çizelge 14 )   [ TABLOLAR!H32:K35 ]
#  Bu tablo GÜVENLİK TERTİBATI TİPİNE bakar.  Avan modülü aynı çizelgeyi
#  HIZA göre okur ( MMO/697 Çizelge-1 iki sütunu yan yana verir ).  Normal
#  kurulumda ikisi aynı değeri üretir;  düşük hızlı bir asansöre kademeli
#  tertibat konursa ayrışırlar — o durumda tertibat tipi daha doğrudur.
# =====================================================================
DARBE_TIPLERI = (
    ('Kaymalı', 2),
    ('Ani Frenlemeli Makaralı', 3),
    ('Ani Frenlemeli', 5),
)



DARBE_TIPLERI_ADLARI = tuple(r[0] for r in DARBE_TIPLERI)


def darbe_k1(tertibat_tipi):
    return _ara(DARBE_TIPLERI, tertibat_tipi, 1)


#  Normal kullanma hareketi  ( TS EN 81-20 Çizelge 14 · MMO/697 Çizelge-1 )
K2_NORMAL_KULLANMA = 1.2


# =====================================================================
#  BÜKÜLGEN ( GEZİCİ ) KABLO                        [ TABLOLAR!D61:G64 ]
# =====================================================================
#  Kabin ile kuyu arasındaki asma kablo.  MTrav ( gezici kablo indirgenmiş
#  kütlesi ) hesabına girer.
BUKULGEN_KABLO = (
    ('12 x 0,75', 33.8, 4.2, 0.284),
    ('24 x 0,75', 70.4, 4.2, 0.642),
    ('12 x 1,00', 36.2, 4.2, 0.33),
    ('24 x 1,00', 70.4, 4.2, 0.62),
)

KABLO_TIPLERI = tuple(r[0] for r in BUKULGEN_KABLO)


# =====================================================================
#  KAT KAPISI TİPİ  →  2. BÜKÜLGEN KABLO      [ Veri Girişi!M39:R40 ]
# =====================================================================
#  Kaynak kitapta 2. kablo tipi GİRDİ DEĞİLDİR:  kat kapısı tipinden
#  HLOOKUP ile türetilir ( manuel kapıda daha ince kablo ).
KAPI_KABLO = (
    ('Manuel Sağ', '12 x 0,75'),
    ('Manuel Sol', '12 x 0,75'),
    ('Otomatik Merkezi', '24 x 0,75'),
    ('Teleskopik Sağ', '24 x 0,75'),
    ('Teleskopik Sol', '24 x 0,75'),
)

KAPI_TIPLERI = tuple(r[0] for r in KAPI_KABLO)


def kapi_kablosu(kapi_tipi):
    """Kat kapısı tipine karşılık gelen 2. bükülgen kablo tipi."""
    return _ara(KAPI_KABLO, kapi_tipi, 1)


def kablo_agirligi(tip):
    """Bükülgen kablonun metre ağırlığı ( kg/m )."""
    return _ara(BUKULGEN_KABLO, tip, 3)


def kablo_en(tip):
    return _ara(BUKULGEN_KABLO, tip, 1)


def kablo_yukseklik(tip):
    return _ara(BUKULGEN_KABLO, tip, 2)


# =====================================================================
#  KARŞI AĞIRLIK MALZEMESİ  ( derinlik · yükseklik mm )  [ TABLOLAR!U61:W62 ]
# =====================================================================
#  NOT:  Excel'deki VLOOKUP aralığı U61:W63'tür, ama 63. satır bir tablo
#  satırı değil — orada duran =( C80-150 )/... formülü yalnızca U64'e
#  girer, U64'ü de hiçbir hesap okumaz.  Ölü artık; tabloya alınmadı.
AGIRLIK_MALZEMESI = (
    ('Barit', 150, 101),
    ('Pik Döküm', 100, 100),
)



AGIRLIK_MALZEMELERI = tuple(r[0] for r in AGIRLIK_MALZEMESI)


def agirlik_derinlik(malzeme):
    return _ara(AGIRLIK_MALZEMESI, malzeme, 1)


def agirlik_yukseklik(malzeme):
    return _ara(AGIRLIK_MALZEMESI, malzeme, 2)


# =====================================================================
#  AĞIRLIK RAY ARASI → KARŞI AĞIRLIK GENİŞLİĞİ       [ TABLOLAR!X59:Z60 ]
# =====================================================================
#  Excel:  HLOOKUP( 'Veri Girişi'!B119 ; X59:Z60 ; 2 ; 0 )
#  Üst satır aranan anahtar ( ray arası mm ), alt satır sonuç
#  ( karşı ağırlık çerçeve genişliği mm ).
#
#  NOT:  X61/X62 satırları ( 30·42·60 ve 84·123·169 ) yalnızca TABLOLAR!U63
#  ölü formülüne girer; hiçbir hesap okumaz — tabloya alınmadı.
AGIRLIK_RAY_ARASI = (
    (700, 1050, 1400),
    (660, 960, 1320),
)

RAY_ARALARI = AGIRLIK_RAY_ARASI[0]


def agirlik_genisligi(ray_arasi):
    """Ağırlık ray arası ( mm ) → karşı ağırlık genişliği ( mm )."""
    anahtar, sonuc = AGIRLIK_RAY_ARASI
    for i, v in enumerate(anahtar):
        if v == ray_arasi:
            return sonuc[i]
    return None


# =====================================================================
#  KILAVUZ RAY ÇELİĞİ  Rm → izin verilen gerilmeler    [ TEKNİK!P2:R4 ]
#      σperm normal kullanma · σperm güvenlik tertibatı çalışması  ( N/mm² )
# =====================================================================
RAY_CELIGI = (
    (370, 165, 205),
    (440, 195, 244),
    (520, 230, 288),
)

RAY_CELIKLERI = tuple(s[0] for s in RAY_CELIGI)


def sigma_perm_normal(rm):
    return _ara(RAY_CELIGI, rm, 1)


def sigma_perm_guvenlik(rm):
    return _ara(RAY_CELIGI, rm, 2)


# =====================================================================
#  KANAL İŞLEME ŞEKLİ → SÜRTÜNME ÇARPANI  f     [ Veri Girişi!T42:W43 ]
#      yükleme · durdurma tertibatı ( fren ) · kabinin bloke edilmesi
# =====================================================================
#  DİKKAT — BU SÜTUNLAR μ DEĞİL f'DİR.  Kitap satırı "sürtünme katsayısı μ"
#  diye adlandırır ama içindeki sayılar sürtünme ÇARPANIDIR:  sertleştirilmiş
#  kanalın yükleme değeri 0,30716 = 0,1 / sin( 38° / 2 ), yani μ = 0,1'in
#  f'ye dönüşmüş hâlidir.  ( μ'nün kendisi 0,1 · 0,1/(1+v/10) · 0,2'dir ve
#  SABIT sözlüğünde durur. )
#
#  DEĞERLER ÇİVİLİDİR:  γ = 38° ve β = 90° ile hesaplanmışlardır.  Ofis
#  sabitleri değişince bunlar değişmez — bu yüzden motor bu tabloyu HİÇ
#  kullanmaz, f'yi her seferinde m.5.11.2.3.1'den kendisi hesaplar
#  ( mukavemet._tahrik ).  Tablo yalnız kitabın hücreleriyle karşılaştırma
#  testi için durur;  ekrandaki tablo da f'yi ofis sabitlerinden üretir
#  ( engine/uygulama/tablolar_gorunum.py ).
KANAL_ISLEME = (
    ('Sertleştirilmemiş', 0.20525235013903476, 0.1865930455809407, 0.6143106973514485),
    ('Sertleştirilmiş', 0.30715534867572425, 0.27923213515974926, 0.6143106973514485),
)

KANAL_ISLEME_SEKILLERI = tuple(s[0] for s in KANAL_ISLEME)
_SURTUNME_SUTUN = {"yukleme": 1, "fren": 2, "bloke": 3}


def surtunme(isleme_sekli, durum):
    """Kitabın çivili f değeri  ( γ = 38° · β = 90° ).  durum: yukleme | fren | bloke

    Yeni kodda kullanmayın:  f kanal şekline ve ofis açılarına bağlıdır,
    bkz. mukavemet._tahrik.  Bu işlev yalnız kitabın hücrelerini doğrulayan
    test için durur.
    """
    return _ara(KANAL_ISLEME, isleme_sekli, _SURTUNME_SUTUN[durum])
