# -*- coding: utf-8 -*-
"""
ASANSÖR AVAN PROJE HESAPLARI
  MMO/697 (2. Baskı, Ocak 2020) s.18-21  ·  TS EN 81-20  ·  IEEE Std 80

"ASANSOR AVAN HESAPLARI.xlsx" dosyasındaki
  · GİRİŞ / SABİTLER / TABLOLAR
  · 1-4 NOLU ASANSÖR   (6 hesap bölümü)
  · MK.DAİRESİ AYD.
  · TOPRAKLAMA
  · ÖZET
sayfalarının birebir Python karşılığıdır.
"""
import math
from . import tables as T
from .steps import (Bolum, veri, hesap, metin, tr, trn,
                    yukari_yuvarla, tavana_yuvarla, excel_round, sayi_mi)


# ---------------------------------------------------------------- SABİTLER
#  A) Yönetmelik / standart sabitleri — değiştirilmez
SABIT_A = {
    "gn": 9.81,                    # Yerçekimi ivmesi          MMO/697 s.18 — TS EN 81-20
    "tampon_katsayi": 4,           # F = 4·gn·(P+Q)            MMO/697 §2.3.3.1-2
    "k1_hizli": 2,                 # V > 1,00 m/s              MMO/697 Çizelge-1
    "k1_orta": 3,                  # 0,63 < V ≤ 1,00 m/s
    "k1_yavas": 5,                 # 0,15 < V ≤ 0,63 m/s
    "motor_sabiti": 102,           # N = (1/η)·[(Q/2·V)/102]   MMO/697 §2.4
    "palanga_verim_dususu": 0.10,  # Palangalı sistemde verim %10 az       MMO/697 §2.4
    "kirlenme_faktoru": 1.25,      # Aydınlatmada bakım faktörü d
    "E_makine_dairesi": 200,       # lüx     TS EN 81-20
    "E_kabin": 100,                # lüx     TS EN 81-20
    "E_kuyu": 50,                  # lüx     TS EN 81-20
    "kuyu_ek_armatur": 2,          # Kuyu dibi + kuyu üstü
    "h_armatur": 1.0,              # Armatür–çalışma düzlemi arası yükseklik, m
    "ray_dusumu": 0.20,            # I = Hk − 0,20, m
    "flexbil_sabiti": 3.0,         # Flexbil boyu = Hk/2 + 3, m
}

#  B) Ofis standardı — varsayılan; gerekirse değiştirilebilir.
#  ASKI ORANI (i) asansörün KENDİ ÖZELLİĞİDİR — kapasite ve hız gibi GİRİŞ
#  sayfasından asansör bazında girilir; buradaki değer yalnız boş bırakılan
#  kolon için yedektir.  Denge faktörü q uygulamada hep 0,50 olduğundan ofis
#  standardında durur, gerekirse asansör bazında ezilir.
SABIT_B_VARSAYILAN = {
    "i_palanga": 2,          # yedek — asıl giriş asansör bazındadır
    "q_denge": 0.50,         # Denge faktörü
    "n_ray": 2,              # Kabin kılavuz ray sayısı
    "gf": 1.5,               # Gezici kablo (flexbil) birim kütlesi, kg/m
    "Fmt": 150,              # Montör ağırlığı, kg
    "kabin_armatur_W": 5,    # LED spot
    "kabin_armatur_lm": 300,
    "kabin_ustu_armatur": 1,
    "kuyu_armatur_W": 40,    # Flüoresan
    "kuyu_armatur_lm": 2600, # Ofis teamülü (Tablo-4'te 40 W = 2100 lm)
    "kuyu_Dmax": 7,          # Armatürler arası azami aralık, m (0 = kontrol kapalı)
    "priz_adedi": 3,
    "priz_gucu": 300,        # W
    "cosfi": 0.90,
    "UL": 50,                # İzin verilen temas gerilimi, V (TT sistem)
    "IDn": 0.30,             # Kaçak akım rölesi anma akımı, A
    "lc": 1.5,               # Çubuk topraklayıcı boyu, m
    "ayd_sutun": 2,          # TABLOLAR Tablo-2 sütunu (tavan .80 / duvar .50 / zemin .10)
}


#  Ofis standardı değerlerinin geçerlilik aralıkları.
#  Aralık dışında bir değer girilirse hesap çökmez; varsayılana dönülür ve
#  hangi alanın reddedildiği kullanıcıya bildirilir.
#  ARTIK OFİS SABİTİ DEĞİL — asansörün kendi girdisi olan, burada yalnız
#  YEDEK olarak duran alanlar.  Askı ( palanga ) oranı asansöre özeldir
#  ( GİRİŞ 53. satır ); SABİTLER'deki değer yalnız boş bırakılan kolon için
#  kullanılır, bu yüzden arayüzde "ofis standardı" diye gösterilmez.
SABIT_B_YEDEK = ("i_palanga",)

SABIT_B_ARALIK = {
    #  q = 1 iken N = ( 1 − q )·Q·V/… = 0 çıkıyor ve 2,2 kW motor "uygun"
    #  görünüyordu; q = 0 ise karşı ağırlık hiç dengelemiyor demektir.  İkisi de
    #  fiziksel değil.  Uygulama bandı 0,40 - 0,55; bu aralığın dışı UYARI,
    #  aşağıdaki sert sınırların dışı ise REDDEDİLİR.
    "i_palanga": (1, 4), "q_denge": (0.2, 0.8), "n_ray": (1, 8), "gf": (0, 50),
    "Fmt": (0, 1000), "kabin_armatur_W": (0.1, 1000), "kabin_armatur_lm": (1, 100000),
    "kabin_ustu_armatur": (0, 20), "kuyu_armatur_W": (0.1, 1000),
    "kuyu_armatur_lm": (1, 100000), "kuyu_Dmax": (0, 100), "priz_adedi": (0, 50),
    "priz_gucu": (0, 10000), "cosfi": (0.1, 1), "UL": (1, 1000), "IDn": (0.001, 10),
    "lc": (0.1, 50), "ayd_sutun": (1, 10),
}


# =====================================================================
#  C )  OFİS VARSAYILANLARI
#  Asansörden asansöre, projeden projeye DEĞİŞMEYEN ama Excel'de SABİTLER
#  sayfasında değil GİRİŞ sayfasının kendi girdi hücrelerinde duran değerler.
#  Program bunları burada bir kez tutar; asansör alanı boş bırakılırsa
#  buradan gelir ve XLSX'e yine aynı GİRİŞ hücresine yazılır — bu yüzden
#  Excel şablonunda HİÇBİR değişiklik gerekmez.
#
#  Bir asansörde farklı bir değer gerekiyorsa ( ör. daha ağır bir makine )
#  o asansörün kartından girilir; girilen değer buradakini ezer.
# =====================================================================
OFIS_VARSAYILAN = {
    # kesin sabitler — yönetmelik / malzeme fiziği
    "U": 380,                 # Şebeke gerilimi (fazlar arası), V
    "kappa": 56,              # Bakır iletkenlik, m/(Ω·mm²)
    "eps_max": 3,             # İzin verilen gerilim düşümü, %
    # ofis malzeme standardı — asansör bazında
    "gr": 17.91,              # Kılavuz ray birim kütlesi, kg/m
    "Fmk": 350,               # Makine ağırlığı, kg
    "Fsh": 100,               # Makine sehpası ağırlığı, kg
    "S1": 6,                  # Kolon hattı kesiti, mm²
    "S2": 6,                  # Makine besleme kesiti, mm²
    "L2": 3,                  # Makine besleme uzunluğu, m
    "kablo_tipi": "NHXMH FE180",
    "L1_pay": 3.5,            # L1 = Hk + bu pay  ( pano ile kuyu arası )
    # ofis varsayılanı — projeye göre değişebilir
    "beta": 150,              # Toprak özgül direnci, Ω·m
    "cubuk_sayisi": 4,        # Çubuk topraklayıcı adedi
    "goz_araligi": 20,        # Temel topraklama karelaj gözü, m ( 20 × 20 )
}

#  KAT YÜKSEKLİĞİ ve KAPI TİPİ burada DEĞİLDİR:  her projede değişirler,
#  bu yüzden ait oldukları yerde — trafik hesabı sekmesinde — girilirler.
#  ( v1.6'da ofis varsayılanı yapılmışlardı; v1.7'de geri alındı. )

#  Metin alanları — sayı denetimine girmez
OFIS_METIN = ("kablo_tipi",)

OFIS_ARALIK = {
    "U": (100, 1000), "kappa": (10, 100), "eps_max": (0.1, 20),
    "gr": (1, 200), "Fmk": (1, 5000), "Fsh": (0, 3000),
    "S1": (1, 400), "S2": (1, 400), "L2": (0.1, 500), "L1_pay": (0, 100),
    "beta": (1, 100000), "cubuk_sayisi": (0, 100), "goz_araligi": (1, 200),
}

#  Asansör kartından ezilebilen ofis varsayılanları ( "özel değer" bölümü )
OFIS_ASANSOR_ALANLARI = ("gr", "Fmk", "Fsh", "S1", "S2", "L2", "kablo_tipi")
#  Avan ortak panelinden gelen, boş bırakılırsa ofis varsayılanına düşenler
OFIS_ORTAK_ALANLARI = ("U", "kappa", "eps_max", "beta", "cubuk_sayisi")


def sabitler(ozel=None):
    """
    Yönetmelik sabitleri (A) + ofis standardı (B).
    `ozel` içindeki geçersiz değerler yok sayılır, varsayılan kullanılır;
    reddedilenlerin listesi "_reddedilen" anahtarında döner.
    """
    s = dict(SABIT_A)
    s.update(SABIT_B_VARSAYILAN)
    s.update(OFIS_VARSAYILAN)
    reddedilen = []
    for k, v in (ozel or {}).items():
        if v is None or (k not in SABIT_B_VARSAYILAN and k not in OFIS_VARSAYILAN):
            continue
        if k in OFIS_METIN:                       # metin alanı — boş değilse geçerli
            metin = str(v).strip()
            if metin:
                s[k] = metin
            continue
        alt, ust = SABIT_B_ARALIK.get(k) or OFIS_ARALIK.get(k) or (None, None)
        if not sayi_mi(v) or (alt is not None and not (alt <= v <= ust)):
            reddedilen.append(f"{k} = {v}")
            continue
        s[k] = v
    if "ayd_sutun" in s:
        s["ayd_sutun"] = int(round(s["ayd_sutun"]))
    s["_reddedilen"] = reddedilen
    return s


def _evet_mi(x):
    """Excel'den 'Evet' / 'Hayır', arayüzden True / False gelebilir."""
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    return str(x).strip().lower() in ("evet", "e", "var", "true", "1", "yes")


#  Asansör kartında girilen değer aralık dışıysa program varsayılana döner.
#  Bu SESSİZ kalmamalı: kullanıcı bir sayı yazdı, program başka bir sayı
#  kullanıyor.  Reddedilenler burada toplanıp uyarı olarak basılır.
ALAN_ADI = {
    "i_palanga": "i — askı oranı", "q_denge": "q — denge faktörü",
    "gr": "gr — ray birim kütlesi", "Fmk": "Fmk — makine ağırlığı",
    "Fsh": "Fsh — sehpa ağırlığı", "S1": "S1 — kolon hattı kesiti",
    "S2": "S2 — makine besleme kesiti", "L2": "L2 — makine besleme uzunluğu",
    "kablo_tipi": "kablo tipi", "U": "U — şebeke gerilimi",
    "kappa": "κ — iletkenlik", "eps_max": "εmax — gerilim düşümü sınırı",
    "beta": "β — toprak özgül direnci", "cubuk_sayisi": "Is — çubuk adedi",
    "goz_araligi": "karelaj gözü — temel topraklama",
}


def _red_yaz(red, anahtar, deger, alt, ust, yerine):
    if red is None:
        return
    red.append(f"{ALAN_ADI.get(anahtar, anahtar)} = {tr(deger)} "
               f"( geçerli aralık {tr(alt)} - {tr(ust)} ) → {tr(yerine)} kullanıldı")


def _asansor_sabiti(a, S, anahtar, red=None):
    """
    Asansör bazında girilmiş bir ofis-standardı değerini okur.
    Geçersiz / boş ise SABİTLER B değerine döner.
    Dönen: (deger, kaynak_metni)
    """
    deger = (a or {}).get(anahtar)
    if deger not in (None, ""):
        alt, ust = SABIT_B_ARALIK.get(anahtar, (None, None))
        if sayi_mi(deger) and (alt is None or alt <= deger <= ust):
            return deger, "GİRİŞ — asansör bazında"
        _red_yaz(red, anahtar, deger, alt, ust, S[anahtar])
    return S[anahtar], "SABİTLER B"


def _ofis_degeri(a, S, anahtar, red=None):
    """
    Ofis varsayılanı olan bir asansör alanını okur.
    Asansör kartında bir değer varsa o, yoksa ofis varsayılanı kullanılır.
    Dönen: (deger, kaynak_metni)
    """
    deger = (a or {}).get(anahtar)
    if anahtar in OFIS_METIN:
        metin = str(deger or "").strip()
        if metin:
            return metin, "GİRİŞ — asansör bazında"
        return S[anahtar], "OFİS VARSAYILANI"
    if deger not in (None, ""):
        alt, ust = OFIS_ARALIK.get(anahtar, (None, None))
        if sayi_mi(deger) and (alt is None or alt <= deger <= ust):
            return deger, "GİRİŞ — asansör bazında"
        _red_yaz(red, anahtar, deger, alt, ust, S[anahtar])
    return S[anahtar], "OFİS VARSAYILANI"


def _ortak_degeri(ortak, S, anahtar, red=None):
    """Avan ortak panelindeki bir alanı okur; boşsa ofis varsayılanına düşer."""
    deger = (ortak or {}).get(anahtar)
    if deger not in (None, ""):
        alt, ust = OFIS_ARALIK.get(anahtar, (None, None))
        if sayi_mi(deger) and (alt is None or alt <= deger <= ust):
            return deger
        _red_yaz(red, anahtar, deger, alt, ust, S[anahtar])
    return S[anahtar]


# =====================================================================
#  TEK ASANSÖRÜN AVAN HESABI  —  "n NOLU ASANSÖR" sayfası
# =====================================================================
def hesapla_asansor(a: dict, ortak: dict, S: dict, no: int = 1) -> dict:
    """
    a     : asansör girdileri (GİRİŞ sayfası C..F kolonu)
    ortak : ortak girdiler (GİRİŞ sayfası 1. bölüm)
    S     : sabitler
    """
    # ---------- girdiler
    tanim = a.get("tanim") or ""
    P_kap = a.get("kapasite")
    Q_elle = a.get("Q_elle")
    V = a.get("V")
    eta = a.get("eta")
    Hk = a.get("Hk")
    kuyu_b = a.get("kuyu_genisligi")
    kabin_a = a.get("kabin_boyu")
    kabin_b = a.get("kabin_genisligi")
    #  OFİS VARSAYILANLARI — asansörden asansöre değişmeyen malzeme değerleri.
    #  Asansör kartında bir değer varsa o kullanılır, yoksa ofis standardı.
    #  Aralık dışı bir değer girildiyse varsayılana dönülür ve bu SESSİZ
    #  kalmaz: red listesi paftaya uyarı olarak basılır.
    red = []
    gr,   gr_kaynak   = _ofis_degeri(a, S, "gr", red)
    Fmk,  Fmk_kaynak  = _ofis_degeri(a, S, "Fmk", red)
    Fsh,  Fsh_kaynak  = _ofis_degeri(a, S, "Fsh", red)
    S1,   S1_kaynak   = _ofis_degeri(a, S, "S1", red)
    S2,   S2_kaynak   = _ofis_degeri(a, S, "S2", red)
    L2,   L2_kaynak   = _ofis_degeri(a, S, "L2", red)
    kablo_tipi, kablo_kaynak = _ofis_degeri(a, S, "kablo_tipi", red)
    Nsc_giris = a.get("Nsc")

    #  L1 — kolon hattı uzunluğu.  Boş bırakılırsa kuyu yüksekliği + ofis payı
    #  ( pano ile kuyu arasındaki mesafe ) kullanılır; plandan ölçülen değer
    #  farklıysa alan doldurulur.
    L1_giris = a.get("L1")
    if L1_giris not in (None, "") and not (sayi_mi(L1_giris) and 0 < L1_giris <= 500):
        red.append(f"L1 — kolon hattı uzunluğu = {tr(L1_giris)} ( geçerli aralık "
                   "0 - 500 m ) → Hk + ofis payı kullanıldı")
    if sayi_mi(L1_giris) and L1_giris > 0:
        L1, L1_kaynak = L1_giris, "GİRİŞ"
    elif sayi_mi(Hk):
        L1 = Hk + S["L1_pay"]
        L1_kaynak = f"Hk + ofis payı ( {tr(S['L1_pay'])} m )"
    else:
        L1, L1_kaynak = None, "GİRİŞ"
    Gk_elle = a.get("Gk_elle")
    makine_tipi = a.get("makine_tipi") or ""
    #  "Girilen verim TOPLAM sistem verimidir" işaretliyse MMO/697 §2.4'teki
    #  palanga verim düşüşü İKİNCİ KEZ uygulanmaz — askı kaybı zaten o
    #  değerin içindedir (aksi hâlde çift sayılır).
    toplam_verim = _evet_mi(a.get("toplam_verim"))

    #  Şebeke gerilimi, iletkenlik ve izin verilen gerilim düşümü ofis
    #  varsayılanıdır; ortak panelde boş bırakılırsa oradan gelir.
    U_sebeke = _ortak_degeri(ortak, S, "U", red)
    kappa = _ortak_degeri(ortak, S, "kappa", red)
    eps_max = _ortak_degeri(ortak, S, "eps_max", red)

    # ---------- ELLE GİRİLEN FİZİKSEL BÜYÜKLÜKLERİN SINIRLARI
    #  Denetimsizken  Q elle = 0  →  N = 0 kW  →  2,2 kW motor "uygun" çıkıyor;
    #  Gk elle negatif olabiliyor; η = 10 girilince motor gereksiz küçülüyordu.
    #  Bunlar hesabı DURDURUR — sessizce yanlış bir motor seçilmesindense
    #  kullanıcıya hangi alanın imkânsız olduğu söylenir.
    FIZIKSEL = [
        ("Q elle — anma yükü", Q_elle, 50, 20000, "kg"),
        ("Gk elle — boş kabin kütlesi", Gk_elle, 50, 20000, "kg"),
        ("η — makine verimi", eta, 0.05, 1.0, "—"),
    ]
    for ad, deger, alt, ust, birim in FIZIKSEL:
        if deger in (None, ""):
            continue
        if not sayi_mi(deger) or not (alt <= deger <= ust):
            return {"no": no, "aktif": False,
                    "uyari": f"!!!   {no} NOLU ASANSÖR — {ad} = {tr(deger)} {birim}   ·   "
                             f"geçerli aralık {tr(alt)} - {tr(ust)} {birim}. "
                             "Sıfır, negatif ya da fiziksel olmayan bir değer girilemez; "
                             "boş bırakırsanız tablo / ofis değeri kullanılır.   !!!"}

    # ---------- Q  (Tablo-7 → elle)
    Q0 = T.TABLO_7.get(P_kap) if sayi_mi(P_kap) else None
    Q = Q_elle if sayi_mi(Q_elle) else Q0
    if not sayi_mi(Q):
        return {"no": no, "aktif": False,
                "uyari": ("!!!   BU ASANSÖR TANIMLANMAMIŞ   —   hesaplar boştur   !!!"
                          if not sayi_mi(P_kap) else
                          "!!!   KAPASİTE TABLO-7 DIŞI   —   'Anma yükü — elle' alanını doldurun   !!!")}

    # ---------- zorunlu girdi denetimi
    #  Eksik ya da geçersiz bir alan varsa hesap yapılmaz; hangi alanların
    #  eksik olduğu adıyla bildirilir (program çökmez).
    ZORUNLU = [
        ("V", V, "Kabin hızı"), ("eta", eta, "Makine verimi"),
        ("Hk", Hk, "Kuyu yüksekliği"), ("kuyu_genisligi", kuyu_b, "Kuyu genişliği"),
        ("kabin_boyu", kabin_a, "Kabin boyu"), ("kabin_genisligi", kabin_b, "Kabin genişliği"),
        ("gr", gr, "Kılavuz ray birim kütlesi"), ("Fmk", Fmk, "Makine ağırlığı"),
        ("Fsh", Fsh, "Makine sehpası ağırlığı"),
        ("S1", S1, "Kolon hattı kesiti"), ("L1", L1, "Kolon hattı uzunluğu"),
        ("S2", S2, "Makine besleme kesiti"), ("L2", L2, "Makine besleme uzunluğu"),
        ("U", U_sebeke, "Şebeke gerilimi"), ("kappa", kappa, "İletken iletkenliği"),
        ("eps_max", eps_max, "İzin verilen gerilim düşümü"),
    ]
    eksik = [ad for _, deger, ad in ZORUNLU if not sayi_mi(deger)]
    # sıfır veya negatif olamayacak alanlar
    POZITIF = [("Kabin hızı", V), ("Makine verimi", eta), ("Kuyu yüksekliği", Hk),
               ("Kuyu genişliği", kuyu_b), ("Kabin boyu", kabin_a),
               ("Kabin genişliği", kabin_b),
               ("Kolon hattı kesiti", S1), ("Makine besleme kesiti", S2),
               ("Şebeke gerilimi", U_sebeke), ("İletken iletkenliği", kappa)]
    gecersiz = [ad for ad, d in POZITIF if sayi_mi(d) and d <= 0]
    if eksik or gecersiz:
        parcalar = []
        if eksik:
            parcalar.append("eksik : " + ", ".join(eksik))
        if gecersiz:
            parcalar.append("sıfır veya negatif olamaz : " + ", ".join(gecersiz))
        return {"no": no, "aktif": False,
                "uyari": f"!!!   {no} NOLU ASANSÖR — girdi tamamlanmadı   ·   "
                         + "   ·   ".join(parcalar) + "   !!!"}

    # ---------- Gk  (Tablo-11 → elle)
    #  Tablo-11 yalnız 450 - 2500 kg arasını kapsar.  Dışına çıkıldığında
    #  tablo SESSİZCE uç değere sabitleniyordu:  Q = 5000 kg için de
    #  Gk = 1900 kg kullanılıyor, kuvvet hesapları olduğundan küçük çıkıyordu.
    #  Artık bu durumda 'Gk elle' zorunludur.
    T11_ALT, T11_UST = T.TABLO_11[0][0], T.TABLO_11[-1][0]
    if not sayi_mi(Gk_elle) and not (T11_ALT <= Q <= T11_UST):
        return {"no": no, "aktif": False,
                "uyari": f"!!!   {no} NOLU ASANSÖR — anma yükü {trn(Q,0)} kg, MMO/697 "
                         f"Tablo-11'in kapsamı DIŞINDA ( {trn(T11_ALT,0)} - "
                         f"{trn(T11_UST,0)} kg )   ·   boş kabin kütlesi tablodan "
                         "türetilemez, 'Gk elle' alanına imalatçı değerini girin.   !!!"}
    Gk0 = T.tablo11_Gk(Q)
    Gk = Gk_elle if sayi_mi(Gk_elle) else Gk0

    bolumler = []

    # =========================================================
    # 1 -  MOTOR GÜCÜ HESABI            (MMO/697 s.21)
    # =========================================================
    #  Askı ( palanga ) oranı asansörün kendi özelliğidir; boş bırakılırsa
    #  SABİTLER B'deki yedek değer kullanılır.  Denge faktörü ofis
    #  standardındadır, gerekirse asansör bazında ezilir.
    i_pal, i_kaynak = _asansor_sabiti(a, S, "i_palanga", red)
    q, q_kaynak = _asansor_sabiti(a, S, "q_denge", red)
    if toplam_verim:
        eta_p = eta
        eta_p_aciklama = "Girilen değer TOPLAM sistem verimidir — palanga düşüşü uygulanmaz"
        eta_p_kaynak = "GİRİŞ — toplam sistem verimi"
    else:
        eta_p = (eta - S["palanga_verim_dususu"]) if i_pal > 1 else eta    # η′
        eta_p_aciklama = "Palangalı sistemde verim ( i > 1 ise η − 0,10 )"
        eta_p_kaynak = "SABİTLER A  /  MMO/697 §2.4"
    N_hes = ((1 - q) * Q * V / (S["motor_sabiti"] * eta_p)) \
        if (sayi_mi(eta_p) and eta_p > 0) else None

    #  Nsç — SEÇİLEN motor gücü.  Elle girilmemişse hesaplanan güçten büyük
    #  ilk STANDART anma gücü seçilir ( IEC 60072 kademeleri ).  Böylece
    #  "hesap 13,33 kW diyor ama 11 kW yazılmış" durumu oluşmaz.
    if Nsc_giris not in (None, "") and not (sayi_mi(Nsc_giris) and 0 < Nsc_giris <= 500):
        red.append(f"Nsç — seçilen motor gücü = {tr(Nsc_giris)} kW ( geçerli aralık "
                   "0 - 500 kW ) → standart kademeden otomatik seçildi")
    if sayi_mi(Nsc_giris) and Nsc_giris > 0:
        Nsc, Nsc_kaynak = Nsc_giris, "GİRİŞ — elle seçildi"
    else:
        Nsc = T.motor_sec(N_hes)
        Nsc_kaynak = "otomatik — standart kademe ( IEC 60072 )"
    if not sayi_mi(Nsc) or Nsc <= 0:
        return {"no": no, "aktif": False,
                "uyari": f"!!!   {no} NOLU ASANSÖR — motor gücü belirlenemedi   ·   "
                         "hesaplanan güç bulunamadığı için standart kademe "
                         "seçilemedi; 'Nsç' alanını elle doldurun   !!!"}
    motor_uygun = sayi_mi(N_hes) and sayi_mi(Nsc) and Nsc >= N_hes

    b1 = Bolum("1 -  MOTOR GÜCÜ HESABI", "MMO / 697  —  s.21")
    b1["adimlar"] = [
        veri("Q", "Anma yükü", Q, "kg", "GİRİŞ", 0),
        veri("V", "Kabin hızı", V, "m/s", "GİRİŞ"),
        veri("q", "Denge faktörü ( karşı ağırlığın dengelediği oran )", q, "—", q_kaynak),
        veri("", "Makine tipi", makine_tipi or "—", "",
             "GİRİŞ" if makine_tipi else "belirtilmedi"),
        veri("i", f"Askı ( palanga ) oranı   —   {T.aski_orani_metni(i_pal)}",
             i_pal, "—", i_kaynak, 0),
        veri("η", "Makine verimi", eta, "—",
             "GİRİŞ — toplam sistem verimi" if toplam_verim
             else (f"GİRİŞ  ( {makine_tipi} — MMO/697 s.21 )" if makine_tipi else "GİRİŞ")),
        veri("η′", eta_p_aciklama, eta_p, "—", eta_p_kaynak),
        hesap("N   =   ( 1 − q ) · Q · V   /   ( 102 · η′ )",
              f"=   ( 1 − {tr(q)} ) · {trn(Q,0)} · {tr(V)}   /   ( 102 · {tr(eta_p)} )",
              N_hes, "kW", "hesaplanan"),
        veri("Nsç", "SEÇİLEN motor gücü", Nsc, "kW", Nsc_kaynak),
    ]
    #  q uygulama bandı — sert sınırlar SABIT_B_ARALIK'ta ( 0,20 - 0,80 );
    #  burası pratikteki bandın dışını "bilerek mi" diye sorar.
    Q_BANT_ALT, Q_BANT_UST = 0.40, 0.55
    if sayi_mi(q) and not (Q_BANT_ALT <= q <= Q_BANT_UST):
        red.append(f"q — denge faktörü {tr(q)} olarak kullanıldı; uygulamada "
                   f"{tr(Q_BANT_ALT)} - {tr(Q_BANT_UST)} bandındadır. "
                   "Karşı ağırlık dengelemesi bu değerde ise gerekçesi paftaya yazılmalıdır")
    b1["aciklamalar"] = [T.VERIM_NOTU]
    if toplam_verim:
        b1["notlar"] = [T.TOPLAM_VERIM_NOTU]
    else:
        mmo_eta = T.makine_verimi(makine_tipi)
        if mmo_eta is not None and sayi_mi(eta) and abs(eta - mmo_eta) > 1e-9:
            b1["notlar"] = [
                f"η, {makine_tipi} makine için MMO/697 s.21'de verilen {tr(mmo_eta)} "
                f"değerinden farklı girilmiştir ( {tr(eta)} ). Kaynağı paftada "
                "belirtilmelidir."]
    b1["sonuc"] = {"baslik": "KONTROL      Nsç  ≥  N",
                   "metin": "UYGUN" if motor_uygun else "UYGUN DEĞİL — motoru büyütün",
                   "uygun": bool(motor_uygun)}
    bolumler.append(b1)

    # =========================================================
    # 2 -  KUVVET HESAPLARI             (MMO/697 s.18-20 / TS EN 81-20)
    # =========================================================
    gn = S["gn"]
    Gf = S["gf"] * (Hk / 2 + S["flexbil_sabiti"])          # gezici kablo kütlesi
    P_kut = Gk + Gf                                        # kabin tarafı toplam kütle
    Ga = P_kut + q * Q                                     # karşı ağırlık kütlesi
    k1 = S["k1_hizli"] if V > 1 else (S["k1_orta"] if V > 0.63 else S["k1_yavas"])
    n_ray = S["n_ray"]
    Lr = Hk - S["ray_dusumu"]                              # kılavuz ray uzunluğu
    Mg = Lr * gr                                           # bir ray hattının kütlesi

    P1 = tavana_yuvarla(S["tampon_katsayi"] * gn * (P_kut + Q), 10)
    P2 = tavana_yuvarla(S["tampon_katsayi"] * gn * Ga, 10)
    PR = tavana_yuvarla(k1 * gn * (P_kut + Q) / n_ray + Mg * gn, 10)
    PK = tavana_yuvarla(k1 * gn * Ga / n_ray + Mg * gn, 10)
    Fs = tavana_yuvarla(gn * (Fmk + Fsh + S["Fmt"] + P_kut + Q + Ga), 10)

    b2 = Bolum("2 -  KUVVET HESAPLARI", "MMO / 697  s.18-20   /   TS EN 81-20")
    b2["adimlar"] = [
        metin("ORTAK BÜYÜKLÜKLER"),
        veri("gn", "Yerçekimi ivmesi", gn, "m/s²", "SABİTLER A"),
        veri("Gk", "Boş kabin kütlesi", Gk, "kg", "GİRİŞ" if sayi_mi(Gk_elle) else "Tablo-11", 0),
        veri("gf", "Gezici kablo ( flexbil ) birim kütlesi", S["gf"], "kg/m", "SABİTLER B"),
        hesap("Gf   =   gf · ( Hk / 2  +  3 )",
              f"=   {tr(S['gf'])}  ·  ( {tr(Hk)} / 2  +  3 )", Gf, "kg", "gezici kablo kütlesi"),
        hesap("P    =   Gk  +  Gf",
              f"=   {trn(Gk,0)}  +  {tr(Gf)}", P_kut, "kg", "kabin tarafı toplam kütle"),
        veri("Q", "Anma yükü", Q, "kg", "GİRİŞ", 0),
        veri("q", "Denge faktörü", q, "—", q_kaynak),
        hesap("Ga  =   P  +  q · Q",
              f"=   {tr(P_kut)}  +  {tr(q)} · {trn(Q,0)}", Ga, "kg", "karşı ağırlık kütlesi"),
        veri("k1", "Darbe faktörü ( V > 1 → 2 / V > 0,63 → 3 / V ≤ 0,63 → 5 )", k1, "—",
             "SABİTLER A  /  MMO/697 Çiz-1", 0),
        veri("n", "Kabin kılavuz ray sayısı", n_ray, "adet", "SABİTLER B", 0),
        veri("gr", "1 m kılavuz rayın kütlesi", gr, "kg/m", gr_kaynak),
        veri("Lr", "Kılavuz ray uzunluğu ( Hk − 0,20 )", Lr, "m", "SABİTLER A"),
        hesap("Mg  =   Lr · gr", f"=   {tr(Lr)}  ·  {tr(gr)}", Mg, "kg", "bir ray hattının kütlesi"),

        metin("A -  KUYU ALT BOŞLUĞU TABANINA GELEN KUVVET  ( kabin tamponu altı )"),
        hesap("P1  =   4 · gn · ( P  +  Q )",
              f"=   4  ·  {tr(gn)}  ·  ( {tr(P_kut)}  +  {trn(Q,0)} )", P1, "N", "", 0),

        metin("B -  KARŞI AĞIRLIK TAMPONU ALTINDAKİ ZEMİNE GELEN KUVVET"),
        hesap("P2  =   4 · gn · ( P  +  q · Q )   =   4 · gn · Ga",
              f"=   4  ·  {tr(gn)}  ·  {tr(Ga)}", P2, "N", "", 0),

        metin("C -  KABİN KILAVUZ RAYLARINA GELEN DÜŞEY KUVVET"),
        hesap("PR  =   k1 · gn · ( P  +  Q ) / n   +   Mg · gn",
              f"=   {trn(k1,0)} · {tr(gn)} · ( {tr(P_kut)} + {trn(Q,0)} ) / {trn(n_ray,0)}"
              f"   +   {tr(Mg)} · {tr(gn)}", PR, "N", "", 0),

        metin("D -  KARŞI AĞIRLIK KILAVUZ RAYLARINA GELEN DÜŞEY KUVVET"),
        hesap("PK  =   k1 · gn · Ga / n   +   Mg · gn",
              f"=   {trn(k1,0)} · {tr(gn)} · {tr(Ga)} / {trn(n_ray,0)}   +   {tr(Mg)} · {tr(gn)}",
              PK, "N", "", 0),

        metin("E -  KUYU ÜSTÜ BETONUNA ETKİ EDEN KUVVET"),
        hesap("Fs  =   gn · ( Fmk  +  Fsh  +  Fmt  +  P  +  Q  +  Ga )",
              f"=   {tr(gn)} · ( {trn(Fmk,0)} + {trn(Fsh,0)} + {trn(S['Fmt'],0)} + "
              f"{tr(P_kut)} + {trn(Q,0)} + {tr(Ga)} )", Fs, "N", "", 0),
    ]
    b2["aciklamalar"] = [
        "PR ve PK, MMO/697 §2.3.3 formülündeki  Mg · gn  ray kütlesi terimini içerir "
        "( kitabın §4.3 örnek hesabı bu terimi ihmal etmiştir ).",
        "Karşı ağırlıkta paraşüt ( fren ) bulunması hâlinde PK dikkate alınır.",
    ]
    if sayi_mi(Lr) and Lr > 40:
        b2["notlar"] = ["Kılavuz ray uzunluğu 40 m'yi aşıyor "
                        f"( Lr = {tr(Lr)} m ) — halat / kompanzasyon kuvveti Fp uygulama "
                        "projesinde ayrıca hesaplanmalıdır  ( MMO/697 s.20 )."]
    else:
        b2["aciklamalar"].append(
            "Kılavuz ray uzunluğu 40 m'yi aşarsa halat / kompanzasyon kuvveti Fp uygulama "
            "projesinde ayrıca hesaplanır  ( MMO/697 s.20 ).")
    bolumler.append(b2)

    # =========================================================
    # 3 -  KABİN AYDINLATMA HESABI      (TS EN 81-20)
    # =========================================================
    ka = kabin_a / 1000
    kb = kabin_b / 1000
    hh = S["h_armatur"]
    k_kabin = ka * kb / (hh * (ka + kb))
    eta_kabin = T.ayd_verim(k_kabin, S["ayd_sutun"])
    E_kabin = S["E_kabin"]
    d = S["kirlenme_faktoru"]
    T_kabin = E_kabin * ka * kb * d / eta_kabin if eta_kabin else None
    OL_kabin = S["kabin_armatur_lm"]
    Z_kabin = T_kabin / OL_kabin if sayi_mi(T_kabin) else None
    n_kabin = int(yukari_yuvarla(Z_kabin, 0)) if sayi_mi(Z_kabin) else None

    b3 = Bolum("3 -  KABİN AYDINLATMA HESABI", "TS EN 81-20")
    b3["adimlar"] = [
        veri("a", "Kabin boyu", ka, "m", "GİRİŞ"),
        veri("b", "Kabin genişliği", kb, "m", "GİRİŞ"),
        veri("h", "Armatür ile çalışma düzlemi arasındaki yükseklik", hh, "m", "SABİTLER A"),
        hesap("k   =   a · b   /   ( h · ( a + b ) )",
              f"=   {tr(ka)} · {tr(kb)}   /   ( {tr(hh)} · ( {tr(ka)} + {tr(kb)} ) )",
              k_kabin, "—", "bölge indeksi", 4),
        veri("η", "Oda aydınlatma verimi", eta_kabin, "—", "TABLOLAR T2"),
        veri("E", "Asgari aydınlatma şiddeti", E_kabin, "lüx", "SABİTLER A", 0),
        veri("d", "Kirlenme ( bakım ) faktörü", d, "—", "SABİTLER A"),
        hesap("T   =   E · a · b · d   /   η",
              f"=   {trn(E_kabin,0)} · {tr(ka)} · {tr(kb)} · {tr(d)}   /   {tr(eta_kabin)}",
              T_kabin, "lm", "gerekli toplam ışık akısı"),
        veri("ØL", "Bir armatürün ışık akısı", OL_kabin, "lm", "SABİTLER B", 0),
        hesap("Z   =   T   /   ØL", f"=   {tr(T_kabin)}   /   {trn(OL_kabin,0)}",
              Z_kabin, "adet", "hesaplanan armatür sayısı"),
        veri("n", "SEÇİLEN armatür sayısı  ( Z yukarı yuvarlanır )", n_kabin, "adet", "", 0),
    ]
    b3["sonuc"] = {"baslik": "SONUÇ",
                   "metin": f"{n_kabin} adet {trn(S['kabin_armatur_W'],0)} W armatür kullanılacaktır.",
                   "uygun": True}
    bolumler.append(b3)

    # =========================================================
    # 4 -  KUYU AYDINLATMA HESABI       (TS EN 81-20)
    # =========================================================
    qa = Hk
    qb = kuyu_b / 1000
    k_kuyu = qa * qb / (hh * (qa + qb))
    eta_kuyu = T.ayd_verim(k_kuyu, S["ayd_sutun"])
    E_kuyu = S["E_kuyu"]
    T_kuyu = E_kuyu * qa * qb * d / eta_kuyu if eta_kuyu else None
    OL_kuyu = S["kuyu_armatur_lm"]
    Z_kuyu = T_kuyu / OL_kuyu if sayi_mi(T_kuyu) else None
    n1 = int(yukari_yuvarla(Z_kuyu, 0)) + S["kuyu_ek_armatur"] if sayi_mi(Z_kuyu) else None
    Dmax = S["kuyu_Dmax"]
    n2 = int(yukari_yuvarla((Hk - 1) / Dmax, 0)) + 1 if (sayi_mi(Dmax) and Dmax > 0) else 0
    n_kuyu = int(max(n1 or 0, n2 or 0)) if sayi_mi(n1) else None

    b4 = Bolum("4 -  KUYU AYDINLATMA HESABI", "TS EN 81-20")
    b4["adimlar"] = [
        veri("a", "Kuyu yüksekliği ( kuyu boyu )", qa, "m", "GİRİŞ"),
        veri("b", "Kuyu genişliği", qb, "m", "GİRİŞ"),
        veri("h", "Armatür ile çalışma düzlemi arasındaki yükseklik", hh, "m", "SABİTLER A"),
        hesap("k   =   a · b   /   ( h · ( a + b ) )",
              f"=   {tr(qa)} · {tr(qb)}   /   ( {tr(hh)} · ( {tr(qa)} + {tr(qb)} ) )",
              k_kuyu, "—", "bölge indeksi", 4),
        veri("η", "Oda aydınlatma verimi", eta_kuyu, "—", "TABLOLAR T2"),
        veri("E", "Asgari aydınlatma şiddeti", E_kuyu, "lüx", "SABİTLER A", 0),
        veri("d", "Kirlenme ( bakım ) faktörü", d, "—", "SABİTLER A"),
        hesap("T   =   E · a · b · d   /   η",
              f"=   {trn(E_kuyu,0)} · {tr(qa)} · {tr(qb)} · {tr(d)}   /   {tr(eta_kuyu)}",
              T_kuyu, "lm", "gerekli toplam ışık akısı"),
        veri("ØL", "Bir armatürün ışık akısı", OL_kuyu, "lm", "SABİTLER B", 0),
        hesap("Z   =   T   /   ØL", f"=   {tr(T_kuyu)}   /   {trn(OL_kuyu,0)}",
              Z_kuyu, "adet", "hesaplanan armatür sayısı"),
        veri("n1", "Işık akısından  =  ROUNDUP( Z ) + 2   ( kuyu dibi + üstü )", n1, "adet",
             "SABİTLER A", 0),
        veri("Dmax", "Armatürler arası azami aralık", Dmax, "m", "SABİTLER B", 0),
        hesap("n2  =   ROUNDUP( ( Hk − 1 ) / Dmax )  +  1",
              (f"=   ROUNDUP( ( {tr(Hk)} − 1 ) / {tr(Dmax)} )  +  1"
               if (sayi_mi(Dmax) and Dmax > 0) else "—   ( aralık kontrolü kapalı )"),
              n2, "adet", "geometrik asgari adet", 0),
        veri("n", "SEÇİLEN armatür sayısı  =  MAX ( n1 ; n2 )", n_kuyu, "adet", "", 0),
    ]
    b4["sonuc"] = {"baslik": "SONUÇ",
                   "metin": f"{n_kuyu} adet {trn(S['kuyu_armatur_W'],0)} W armatür kullanılacaktır.",
                   "uygun": True}
    bolumler.append(b4)

    # =========================================================
    # 5 -  KURULU GÜÇ CETVELİ                        ( TAS )
    # =========================================================
    g_motor = Nsc * 1000
    g_kuyu = n_kuyu * S["kuyu_armatur_W"]
    g_kabin = (n_kabin + S["kabin_ustu_armatur"]) * S["kabin_armatur_W"]
    g_priz = S["priz_adedi"] * S["priz_gucu"]
    P_kurulu = g_motor + g_kuyu + g_kabin + g_priz

    b5 = Bolum(f"5 -  KURULU GÜÇ CETVELİ", f"tablo adı :  TAS{no}")
    b5["cetvel"] = [
        {"lin": 1, "sorti": "MOTOR", "guc": g_motor, "birim": "W", "sigorta": "4 x 25"},
        {"lin": 2, "sorti": f"KUYU AYDINLATMASI          ( {n_kuyu} X {trn(S['kuyu_armatur_W'],0)} W )",
         "guc": g_kuyu, "birim": "W", "sigorta": "10"},
        {"lin": 3, "sorti": (f"KABİN + KABİN ÜSTÜ AYD.     ( {n_kabin} X {trn(S['kabin_armatur_W'],0)} W"
                             f"  +  {trn(S['kabin_ustu_armatur'],0)} X {trn(S['kabin_armatur_W'],0)} W )"),
         "guc": g_kabin, "birim": "W", "sigorta": "10"},
        {"lin": 4, "sorti": f"TOPLAM PRİZ          ( {trn(S['priz_adedi'],0)} X {trn(S['priz_gucu'],0)} W )",
         "guc": g_priz, "birim": "W", "sigorta": "16"},
    ]
    b5["sonuc"] = {"baslik": "ASANSÖRÜN KURULU GÜCÜ",
                   "metin": f"{trn(P_kurulu,0)} W", "uygun": True}
    bolumler.append(b5)

    # =========================================================
    # 6 -  GERİLİM DÜŞÜMÜ VE KESİT KONTROLÜ
    # =========================================================
    cosfi = S["cosfi"]
    eps1 = (100 * P_kurulu * L1 / (kappa * S1 * U_sebeke ** 2)) \
        if all(sayi_mi(x) and x > 0 for x in (kappa, S1, U_sebeke)) else None
    P_motor_W = Nsc * 1000
    eps2 = (100 * P_motor_W * L2 / (kappa * S2 * U_sebeke ** 2)) \
        if all(sayi_mi(x) and x > 0 for x in (kappa, S2, U_sebeke)) else None
    eps = (eps1 + eps2) if all(sayi_mi(x) for x in (eps1, eps2)) else None
    eps_uygun = sayi_mi(eps) and sayi_mi(eps_max) and eps <= eps_max
    I_hat = (P_kurulu / (math.sqrt(3) * U_sebeke * cosfi)) \
        if all(sayi_mi(x) and x > 0 for x in (U_sebeke, cosfi)) else None
    Iz = T.kablo_iz(S1)
    akim_uygun = sayi_mi(I_hat) and sayi_mi(Iz) and I_hat <= Iz

    b6 = Bolum("6 -  GERİLİM DÜŞÜMÜ VE KESİT KONTROLÜ", "Elektrik İç Tesisleri Yönetmeliği")
    b6["aciklamalar"] = [
        "ε %  =  100 · P · L  /  ( κ · S · U² )          I  =  P  /  ( √3 · U · cosφ )",
        "Kolon hattı asansörün TOPLAM kurulu gücünü ( motor + aydınlatma + priz ) taşır; "
        "makine besleme hattı yalnız motoru besler.",
    ]
    b6["notlar"] = [
        "Aydınlatma ve priz devrelerinde izin verilen gerilim düşümü %1,5'tir; bu devrelerin "
        "uç noktalara kadar düşümü uygulama projesinde kontrol edilecektir.",
    ]
    b6["adimlar"] = [
        veri("U", "Şebeke gerilimi ( fazlar arası )", U_sebeke, "V", "GİRİŞ", 0),
        veri("cosφ", "Güç katsayısı", cosfi, "—", "SABİTLER B"),
        veri("κ", "İletken iletkenliği", kappa, "m/Ω·mm²", "GİRİŞ", 0),
        veri("P1", "Asansörün toplam kurulu gücü", P_kurulu, "W", "yukarıdan", 0),
        veri("L1", "Kolon hattı uzunluğu", L1, "m", L1_kaynak),
        veri("S1", "Kolon hattı kesiti", S1, "mm²", S1_kaynak),
        hesap("ε1  =   100 · P1 · L1   /   ( κ · S1 · U² )",
              f"=   100 · {trn(P_kurulu,0)} · {tr(L1)}   /   ( {trn(kappa,0)} · {tr(S1)} · {trn(U_sebeke,0)}² )",
              eps1, "%", "kolon hattı", 3),
        veri("P2", "Makine ( motor ) gücü", P_motor_W, "W", "GİRİŞ", 0),
        veri("L2", "Makine besleme uzunluğu", L2, "m", L2_kaynak),
        veri("S2", "Makine besleme kesiti", S2, "mm²", S2_kaynak),
        hesap("ε2  =   100 · P2 · L2   /   ( κ · S2 · U² )",
              f"=   100 · {trn(P_motor_W,0)} · {tr(L2)}   /   ( {trn(kappa,0)} · {tr(S2)} · {trn(U_sebeke,0)}² )",
              eps2, "%", "makine besleme", 3),
        hesap("ε   =   ε1  +  ε2",
              f"=   {tr(eps1,3)}  +  {tr(eps2,3)}", eps, "%", "toplam", 3),
        veri("εmax", "İzin verilen gerilim düşümü", eps_max, "%", "GİRİŞ", 1),
        hesap("I   =   P1   /   ( √3 · U · cosφ )",
              f"=   {trn(P_kurulu,0)}   /   ( 1,73 · {trn(U_sebeke,0)} · {tr(cosfi)} )",
              I_hat, "A", "hat akımı"),
        veri("Iz", "Kablonun akım taşıma kapasitesi", Iz if sayi_mi(Iz) else "tablo dışı",
             "A", "TABLOLAR / IEC 60364-5-52", 1),
    ]
    b6["sonuc"] = {
        "baslik": "KONTROL      ε ≤ εmax    ve    I ≤ Iz",
        "metin": (f"Seçilen kablo :   {tr(S1)} mm²  {kablo_tipi}   —   "
                  + ("uygundur." if (eps_uygun and akim_uygun) else "UYGUN DEĞİLDİR.")),
        "uygun": bool(eps_uygun and akim_uygun),
        "alt": [f"ε  ≤  εmax  :  " + ("UYGUN" if eps_uygun else "UYGUN DEĞİL — kesiti büyütün"),
                f"I  ≤  Iz    :  " + ("UYGUN" if akim_uygun else "UYGUN DEĞİL — kesiti büyütün")],
    }
    bolumler.append(b6)

    return {
        "no": no, "aktif": True, "tanim": tanim, "baslik": f"{no} NOLU ASANSÖR",
        #  Girilip de kullanılamayan değerler — sessiz kalmamalı
        "uyarilar": [f"⚠ {no} NOLU ASANSÖR: {x}" for x in red],
        "bolumler": bolumler,
        "ozet": {
            "tanim": tanim, "kapasite": P_kap, "Q": Q, "Q0": Q0, "V": V, "eta": eta,
            "eta_p": eta_p, "Gk": Gk, "Gk0": Gk0, "Gf": Gf, "P": P_kut, "Ga": Ga,
            "i_palanga": i_pal, "q_denge": q,
            "i_kaynak": i_kaynak, "q_kaynak": q_kaynak,
            "makine_tipi": makine_tipi, "toplam_verim": toplam_verim,
            "aski": T.aski_orani_metni(i_pal),
            "k1": k1, "Lr": Lr, "Mg": Mg,
            "N_hes": N_hes, "Nsc": Nsc, "motor_uygun": motor_uygun,
            "P1": P1, "P2": P2, "PR": PR, "PK": PK, "Fs": Fs,
            "n_kabin": n_kabin, "n_kuyu": n_kuyu, "k_kabin": k_kabin, "k_kuyu": k_kuyu,
            "eta_kabin": eta_kabin, "T_kabin": T_kabin, "Z_kabin": Z_kabin,
            "eta_kuyu": eta_kuyu, "T_kuyu": T_kuyu, "Z_kuyu": Z_kuyu,
            "n1_kuyu": n1, "n2_kuyu": n2,
            "g_motor": g_motor, "g_kuyu": g_kuyu, "g_kabin": g_kabin, "g_priz": g_priz,
            "kabin_a": ka, "kabin_b": kb, "kuyu_a": qa, "kuyu_b": qb,
            "P_kurulu": P_kurulu, "eps1": eps1, "eps2": eps2, "eps": eps,
            "eps_uygun": eps_uygun, "I": I_hat, "Iz": Iz, "akim_uygun": akim_uygun,
            "Hk": Hk, "kablo_tipi": kablo_tipi, "S1": S1, "L1": L1,
        },
    }


# =====================================================================
#  MAKİNE DAİRESİ AYDINLATMASI      —  MK.DAİRESİ AYD. sayfası
# =====================================================================
def hesapla_makine_dairesi(ortak: dict, S: dict) -> dict:
    A = ortak.get("mk_uzunluk")
    B = ortak.get("mk_genislik")
    #  "Makine dairesi yok ( MRL )" işaret kutusu açık bir tercihtir; ölçü
    #  alanlarına 0 yazmayı beklemek yerine kullanıcı bunu doğrudan söyler.
    #  Kutu hiç gönderilmemişse ( eski proje dosyaları ) eski davranışa
    #  dönülür: ölçü yoksa MRL kabul edilir.
    isaretli = "mk_yok" in (ortak or {})
    mk_yok = _evet_mi(ortak.get("mk_yok"))
    olcu_var = sayi_mi(A) and sayi_mi(B) and A > 0 and B > 0
    if mk_yok:
        return {"aktif": False, "mk_yok": True,
                "uyari": "Makine dairesi yok ( MRL ) olarak işaretlendi  —  "
                         "bu hesap uygulanmaz."}
    if not olcu_var:
        if isaretli:
            return {"aktif": False, "mk_yok": False,
                    "uyari": "!!!   MAKİNE DAİRESİ ÖLÇÜLERİ GİRİLMEDİ   —   A ve B "
                             "ölçüsünü girin ya da 'Makine dairesi yok ( MRL )' "
                             "kutusunu işaretleyin   !!!"}
        return {"aktif": False, "mk_yok": True,
                "uyari": "Makine dairesiz ( MRL ) sistem  —  bu hesap uygulanmaz."}
    a = A / 1000
    b = B / 1000
    hh = S["h_armatur"]
    k = a * b / (hh * (a + b))
    eta = T.ayd_verim(k, S["ayd_sutun"])
    E = S["E_makine_dairesi"]
    d = S["kirlenme_faktoru"]
    Tt = E * a * b * d / eta if eta else None
    OL = S["kuyu_armatur_lm"]
    Z = Tt / OL if sayi_mi(Tt) else None
    n = int(yukari_yuvarla(Z, 0)) if sayi_mi(Z) else None

    bl = Bolum("MAKİNE DAİRESİ AYDINLATMA HESABI", "TS EN 81-20")
    bl["adimlar"] = [
        veri("a", "Makine dairesi uzunluğu", a, "m", "GİRİŞ"),
        veri("b", "Makine dairesi genişliği", b, "m", "GİRİŞ"),
        veri("h", "Armatür ile çalışma düzlemi arasındaki yükseklik", hh, "m", "SABİTLER A"),
        hesap("k   =   a · b   /   ( h · ( a + b ) )",
              f"=   {tr(a)} · {tr(b)}   /   ( {tr(hh)} · ( {tr(a)} + {tr(b)} ) )", k, "—", "bölge indeksi", 4),
        veri("η", "Oda aydınlatma verimi", eta, "—", "TABLOLAR T2"),
        veri("E", "Asgari aydınlatma şiddeti", E, "lüx", "SABİTLER A", 0),
        veri("d", "Kirlenme ( bakım ) faktörü", d, "—", "SABİTLER A"),
        hesap("T   =   E · a · b · d   /   η",
              f"=   {trn(E,0)} · {tr(a)} · {tr(b)} · {tr(d)}   /   {tr(eta)}", Tt, "lm", ""),
        veri("ØL", "Bir armatürün ışık akısı", OL, "lm", "SABİTLER B", 0),
        hesap("Z   =   T   /   ØL", f"=   {tr(Tt)}   /   {trn(OL,0)}", Z, "adet", ""),
        veri("n", "SEÇİLEN armatür sayısı  ( Z yukarı yuvarlanır )", n, "adet", "", 0),
    ]
    bl["sonuc"] = {"baslik": "SONUÇ",
                   "metin": f"{n} adet {trn(S['kuyu_armatur_W'],0)} W armatür kullanılacaktır.",
                   "uygun": True}
    return {"aktif": True, "bolum": bl, "n": n, "k": k, "eta": eta, "T": Tt, "Z": Z}


# =====================================================================
#  TEMEL TOPRAKLAMA HESABI          —  TOPRAKLAMA sayfası
# =====================================================================
def serit_boyu_tahmin(a, b, goz=20.0):
    """
    ŞERİT ( BAND ) BOYU  —  temel ölçülerinden türetme.

    Avan aşamasında elektrik projesinin topraklama planı henüz çizilmemiş
    olur; ofiste de yalnız temelin UZUNLUĞU ve GENİŞLİĞİ girilir.  Uygulama
    kuralı:  band temelin çevresini KAPALI RİNG olarak dolaşır, gözler
    `goz` × `goz` m'yi geçmeyecek şekilde enine / boyuna bağ atılır.

        L   =   2 · ( a + b )   +   na · b   +   nb · a
        na  =   tavan( a / goz ) − 1        ( b boyunda enine bağ )
        nb  =   tavan( b / goz ) − 1        ( a boyunda boyuna bağ )

    Döner:  ( L, ring, na, nb ).  a ya da b geçersizse L = None.
    """
    if not (sayi_mi(a) and sayi_mi(b) and a > 0 and b > 0):
        return None, None, 0, 0
    if not (sayi_mi(goz) and goz > 0):
        goz = 20.0
    ring = 2 * (a + b)
    na = max(0, math.ceil(a / goz - 1e-9) - 1)
    nb = max(0, math.ceil(b / goz - 1e-9) - 1)
    return ring + na * b + nb * a, ring, na, nb


def hesapla_topraklama(ortak: dict, S: dict) -> dict:
    a = ortak.get("temel_a")
    b = ortak.get("temel_b")
    beta = _ortak_degeri(ortak, S, "beta")
    L = ortak.get("serit_L")
    Is = _ortak_degeri(ortak, S, "cubuk_sayisi")
    goz = S.get("goz_araligi", 20)

    #  ŞERİT BOYU GİRDİ DEĞİL, TÜRETİLEN DEĞERDİR.  Ofiste temel için yalnız
    #  uzunluk ve genişlik giriliyor; band boyu bunlardan çıkarılır.  Kullanıcı
    #  topraklama planından gerçek boyu okuyabiliyorsa yazar, yazdığı değer
    #  türetileni ezer.
    L_kaynak, L_ring, L_na, L_nb = "GİRİŞ", None, 0, 0
    if not (sayi_mi(L) and L > 0):
        L, L_ring, L_na, L_nb = serit_boyu_tahmin(a, b, goz)
        L_kaynak = "türetilen"

    if not all(sayi_mi(x) and x > 0 for x in (a, b, beta, L)):
        return {"aktif": False,
                "uyari": ("!!!   Temel ölçüleri ( uzunluk × genişlik ) ya da toprak "
                          "özgül direnci eksik veya sıfır   !!!")}

    A = a * b
    r = math.sqrt(A / math.pi)
    D = 2 * r
    Ry = beta / (2 * D) + beta / L
    lc = S["lc"]
    Rc = (beta / (Is * lc)) if (sayi_mi(Is) and Is > 0 and lc > 0) else None
    Re = (Ry * Rc / (Ry + Rc)) if sayi_mi(Rc) else Ry
    UL = S["UL"]
    IDn = S["IDn"]
    Re_max = UL / IDn if IDn > 0 else None
    uygun = sayi_mi(Re) and sayi_mi(Re_max) and Re <= Re_max

    b1 = Bolum("1 -  YATAY ( TEMEL ) TOPRAKLAYICI", "IEEE Std 80")
    b1["adimlar"] = [
        hesap("A   =   a · b", f"=   {tr(a)}  ·  {tr(b)}", A, "m²", "temel alanı"),
        hesap("r   =   √ ( A / π )", f"=   √ ( {tr(A)} / 3,1416 )", r, "m", "eşdeğer yarıçap"),
        hesap("D   =   2 · r", f"=   2  ·  {tr(r)}", D, "m", "eşdeğer daire çapı"),
        veri("β", "Toprak özgül direnci", beta, "Ω·m", "GİRİŞ", 0),
        #  PAFTADA L HER ZAMAN SIRADAN BİR GİRDİ SATIRIDIR.  Boyun elle mi
        #  girildiği yoksa temel ölçülerinden mi türetildiği paftaya YAZILMAZ —
        #  türetme programın iç kolaylığıdır, teslim edilen hesabın konusu
        #  değil.  ( Kaynak bilgisi yalnız ekranda, alanın altında görünür. )
        veri("L", "Temel / şerit iletken uzunluğu", L, "m", "GİRİŞ"),
        hesap("Ry  =   β / ( 2 · D )   +   β / L",
              f"=   {trn(beta,0)} / ( 2 · {tr(D)} )   +   {trn(beta,0)} / {tr(L)}",
              Ry, "Ω", "IEEE Std 80", 3),
    ]

    b2 = Bolum("2 -  DİKEY ( ÇUBUK ) TOPRAKLAYICI")
    b2["adimlar"] = [
        veri("lç", "Bir çubuğun boyu", lc, "m", "SABİTLER B"),
        veri("Is", "Paralel bağlı çubuk sayısı", Is, "adet", "GİRİŞ", 0),
        hesap("Rç  =   β / ( Is · lç )",
              (f"=   {trn(beta,0)} / ( {trn(Is,0)}  ·  {tr(lc)} )" if sayi_mi(Rc)
               else "—   ( çubuk topraklayıcı yok )"),
              Rc, "Ω", "tek çubuk β/lç — Is adet paralel", 3),
    ]

    b3 = Bolum("3 -  TOPLAM TOPRAKLAMA DİRENCİ VE KONTROL")
    b3["adimlar"] = [
        hesap("Re  =   ( Ry · Rç )  /  ( Ry  +  Rç )",
              (f"=   ( {tr(Ry)} · {tr(Rc)} )  /  ( {tr(Ry)} + {tr(Rc)} )" if sayi_mi(Rc)
               else f"=   {tr(Ry)}   ( yalnız temel topraklayıcı )"),
              Re, "Ω", "paralel", 3),
        veri("UL", "İzin verilen temas gerilimi", UL, "V", "SABİTLER B", 0),
        veri("IΔn", "Kaçak akım rölesi anma akımı", IDn, "A", "SABİTLER B"),
        hesap("Re max  =   UL   /   IΔn", f"=   {trn(UL,0)}   /   {tr(IDn)}", Re_max, "Ω", "", 2),
    ]
    b3["sonuc"] = {
        "baslik": "KONTROL      Re  ≤  Re max",
        "metin": (f"Re = {tr(Re)} Ω   ≤   {tr(Re_max)} Ω   olduğundan temel topraklaması yeterlidir."
                  if uygun else
                  f"Re = {tr(Re)} Ω   >   {tr(Re_max)} Ω   —   ek topraklayıcı gereklidir."),
        "uygun": bool(uygun),
    }
    #  İlk iki satır sonucun GEÇERLİLİK ŞARTIDIR — ekranda görünür kalır.
    b3["notlar"] = [
        "HESAPLANAN TAHMİNİ DEĞERDİR — TESİS TAMAMLANDIKTAN SONRA ÖLÇÜMLE DOĞRULANACAKTIR.",
        f"KABULLER: TT şebeke, UL = {trn(S['UL'],0)} V, IΔn = {tr(S['IDn'])} A. "
        "Şebeke TN sistem ise bu kontrol ölçütü geçerli değildir.",
    ]
    b3["aciklamalar"] = [
        "Toprak özgül direnci β zemin etüdünden alınmalıdır; verilmemişse 150 Ω·m kabul "
        "edilir. Rç bağıntısı çubuk çapını ve çubuklar arası etkileşimi içermeyen bir ön "
        "kabuldür — kesin değer ölçümle bulunur.",
    ]
    return {"aktif": True, "bolumler": [b1, b2, b3],
            "A": A, "r": r, "D": D, "Ry": Ry, "Rc": Rc, "Re": Re,
            "Re_max": Re_max, "uygun": uygun,
            "L": L, "L_kaynak": L_kaynak, "L_ring": L_ring,
            "L_na": L_na, "L_nb": L_nb, "goz_araligi": goz}


# =====================================================================
#  TÜM AVAN HESABI  ( ÖZET dâhil )
# =====================================================================
#  Kuyu yüksekliği ile seyahat mesafesi arasındaki pay ( kuyu dibi + üst boşluk ).
#  TS EN 81-20 kuyu dibi ve üst boşluk asgarilerini hıza ve tampon tipine göre
#  belirler; uygulamada bu pay tipik olarak 4,5 – 7 m arasındadır.  Aşağıdaki
#  sınırlar HESABI DURDURMAZ, yalnız "kontrol et" uyarısı üretir.
HK_PAY_ALT = 3.5     # m — bunun altı şüpheli
HK_PAY_UST = 12.0    # m — bunun üstü şüpheli


def _trafik_tutarlilik(trafik, asansorler_girdi):
    """
    Trafik sekmesindeki sonuçla avan girdilerini karşılaştırır.
    Aktarımdan sonra trafikte yapılan bir değişiklik avan sekmesine
    yansımadıysa burada görünür.  Yalnız uyarı üretir, hesabı durdurmaz.
    """
    u = []
    if not isinstance(trafik, dict):
        return u
    ham = trafik.get("asansorler")
    t_list = [t for t in ham if isinstance(t, dict)] if isinstance(ham, list) else []
    if not t_list:
        return u
    ham_a = asansorler_girdi if isinstance(asansorler_girdi, list) else []
    a_sayi = len([a for a in ham_a if isinstance(a, dict)])
    t_sayi = len(t_list)

    #  ADET  —  avan adedi trafik grubundan AZ olamaz: gruptaki her asansörün
    #  elektrik hesabı da yapılmalıdır.  FAZLASI ise olağandır ( trafik
    #  hesabına girmeyen ayrı bir yük ya da sedye asansörü ); bu bir hata
    #  değil, paftaya yazılan bir nottur.
    if a_sayi < t_sayi:
        u.append(f"⚠ Trafik hesabı {t_sayi} adet asansör veriyor, avanda {a_sayi} adet "
                 f"tanımlı — eksik {t_sayi - a_sayi} asansörün motor gücü, kurulu güç ve "
                 "gerilim düşümü hesabı yapılmamış olur.")
    elif a_sayi > t_sayi:
        u.append(f"ℹ Avanda trafik grubunda olmayan {a_sayi - t_sayi} asansör var "
                 "( ayrı yük / sedye asansörü ). Kurulu güce ve gerilim düşümüne girer, "
                 "trafik kontrolüne girmez.")

    #  DEĞER  —  yalnız trafik grubundaki asansörler karşılaştırılır ve
    #  karşılaştırma SIRA NUMARASINA göredir ( 3 nolu avan asansörü 3 nolu
    #  trafik asansörüyle ), aradaki tanımsız kolonlar hizayı kaydırmaz.
    for i in range(1, min(t_sayi, 4) + 1):
        a = ham_a[i - 1] if i - 1 < len(ham_a) else None
        if not isinstance(a, dict):
            continue
        t = t_list[i - 1]
        P_a, P_t = a.get("kapasite"), t.get("P")
        if sayi_mi(P_a) and sayi_mi(P_t) and P_a != P_t:
            u.append(f"⚠ {i} NOLU ASANSÖR: kapasite trafik hesabında {trn(P_t,0)} kişi, "
                     f"avan girdisinde {trn(P_a,0)} kişi — avandaki değer ELLE "
                     "değiştirilmiş. Bilerek yapıldıysa gerekçesi paftaya yazılmalıdır; "
                     "değilse 'Trafikten güncelle' düğmesi eşitler.")
        V_a, V_t = a.get("V"), t.get("V")
        if sayi_mi(V_a) and sayi_mi(V_t) and abs(V_a - V_t) > 1e-9:
            u.append(f"⚠ {i} NOLU ASANSÖR: kabin hızı trafik hesabında {tr(V_t)} m/s, "
                     f"avan girdisinde {tr(V_a)} m/s — avandaki değer ELLE değiştirilmiş. "
                     "Bilerek yapıldıysa gerekçesi paftaya yazılmalıdır; değilse "
                     "'Trafikten güncelle' düğmesi eşitler.")
        Hk, seyahat = a.get("Hk"), t.get("toplam_seyahat")
        if sayi_mi(Hk) and sayi_mi(seyahat) and seyahat > 0:
            pay = Hk - seyahat
            if pay <= 0:
                u.append(f"⚠ {i} NOLU ASANSÖR: kuyu yüksekliği {tr(Hk)} m, toplam seyahat "
                         f"mesafesinden ( {tr(seyahat)} m ) küçük ya da ona eşit — kuyu dibi ve "
                         "üst boşluk için pay kalmıyor. Hk değerini kontrol edin.")
            elif pay < HK_PAY_ALT:
                u.append(f"⚠ {i} NOLU ASANSÖR: kuyu dibi + üst boşluk payı yalnız {tr(pay)} m "
                         f"( Hk {tr(Hk)} − seyahat {tr(seyahat)} ). TS EN 81-20 asgarileri için "
                         "kontrol edin.")
            elif pay > HK_PAY_UST:
                u.append(f"⚠ {i} NOLU ASANSÖR: kuyu dibi + üst boşluk payı {tr(pay)} m "
                         f"( Hk {tr(Hk)} − seyahat {tr(seyahat)} ) olağandışı büyük — kat "
                         "sayısı ya da Hk girdisi güncel olmayabilir.")
    return u


def girdileri_coz(veriler: dict) -> dict:
    """
    Ofis varsayılanlarını ve otomatik belirlenen değerleri GİRDİNİN İÇİNE yazar.

    Yalnız XLSX çıktısında kullanılır: Excel'in kendi formülleri boş bir girdi
    hücresiyle çalışamaz, bu yüzden dosyaya PROGRAMIN KULLANDIĞI değer
    yazılmalıdır — aksi hâlde indirilen dosya ekrandakinden farklı hesaplar.

    Hesap yolunda KULLANILMAZ; orada girdi ham hâliyle kalır ki paftada
    değerin nereden geldiği ( GİRİŞ / OFİS VARSAYILANI / otomatik ) yazılabilsin.
    """
    veriler = veriler if isinstance(veriler, dict) else {}
    S = sabitler(veriler.get("sabitler"))
    ortak = dict(veriler.get("ortak") or {})
    for k in OFIS_ORTAK_ALANLARI:
        ortak[k] = _ortak_degeri(ortak, S, k)

    sonuc = hesapla(veriler)
    hesaplanan = {h.get("no"): h for h in (sonuc.get("asansorler") or []) if h}

    #  Şerit boyu boş bırakılmışsa temel ölçülerinden türetilir; Excel'in
    #  TOPRAKLAMA sayfası GİRİŞ!C13'ü okuduğu için hücre boş kalamaz —
    #  programın kullandığı değer dosyaya da yazılmalıdır.
    tp = sonuc.get("topraklama") or {}
    if not (sayi_mi(ortak.get("serit_L")) and ortak["serit_L"] > 0) and sayi_mi(tp.get("L")):
        ortak["serit_L"] = tp["L"]

    cozulmus = []
    for i, a in enumerate(veriler.get("asansorler") or [], 1):
        if not a:
            cozulmus.append(a)
            continue
        y = dict(a)
        for k in OFIS_ASANSOR_ALANLARI:
            y[k] = _ofis_degeri(a, S, k)[0]
        oz = (hesaplanan.get(i) or {}).get("ozet") or {}
        for k in ("L1", "Nsc"):
            girilen = y.get(k)
            if not (sayi_mi(girilen) and girilen > 0) and sayi_mi(oz.get(k)):
                y[k] = oz[k]
        cozulmus.append(y)

    yeni = dict(veriler)
    yeni["ortak"] = ortak
    yeni["asansorler"] = cozulmus
    return yeni


def hesapla(veriler: dict) -> dict:
    ortak = veriler.get("ortak") or {}
    S = sabitler(veriler.get("sabitler"))
    asansorler = []
    for i, a in enumerate(veriler.get("asansorler") or [], 1):
        if not a:
            continue
        asansorler.append(hesapla_asansor(a, ortak, S, i))

    mk = hesapla_makine_dairesi(ortak, S)
    tp = hesapla_topraklama(ortak, S)

    aktifler = [a for a in asansorler if a.get("aktif")]
    tesis_kurulu = sum(a["ozet"]["P_kurulu"] for a in aktifler)

    ozet = {
        "asansorler": [{"no": a["no"], **a["ozet"]} for a in aktifler],
        "tesis_kurulu_guc": tesis_kurulu,
        "Re": tp.get("Re") if tp.get("aktif") else None,
        "topraklama_uygun": tp.get("uygun") if tp.get("aktif") else None,
        #  Şerit boyu artık türetilebilir — arayüz yer tutucusunda hangi değerin
        #  kullanıldığı ve nereden geldiği görünsün.
        "serit_L": tp.get("L"),
        "serit_L_kaynak": tp.get("L_kaynak"),
        "serit_L_ring": tp.get("L_ring"),
        "serit_L_na": tp.get("L_na"),
        "serit_L_nb": tp.get("L_nb"),
        "eps_max": ortak.get("eps_max"),
    }
    uyarilar = []
    if S.get("_reddedilen"):
        uyarilar.append(
            "⚠ Ofis standardında geçersiz değer yok sayıldı, varsayılan kullanıldı : "
            + " · ".join(S["_reddedilen"]))
    for a in asansorler:
        if not a:
            continue
        if not a.get("aktif") and a.get("uyari"):
            uyarilar.append(a["uyari"])
        uyarilar += a.get("uyarilar") or []
    uyarilar += _trafik_tutarlilik(veriler.get("trafik"), veriler.get("asansorler"))
    return {"asansorler": asansorler, "makine_dairesi": mk, "topraklama": tp,
            "ozet": ozet, "sabitler": S, "ortak": ortak, "uyarilar": uyarilar}
