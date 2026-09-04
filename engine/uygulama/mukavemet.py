# -*- coding: utf-8 -*-
"""
MUKAVEMET HESAP MOTORU              ( UYGULAMA PROJESİ  —  avandan ayrıdır )

Kaynak Excel:  templates/MUKAVEMET_HESABI.xlsx
               "11-Muk. Hesapları" + "Askı Tipleri" sayfaları

Standartlar:  TS EN 81-20 · TS EN 81-50 · TS 12385-5 · ISO 7465
              MMO 208/7 m.2.4  ( motor gücü )
              MMO 208/4 m.3.4.6 ( makine konstrüksiyonu )

Bölümler
  1  Asansör motor gücü                       MMO 208/7 - 2.4
  2  Makine konstrüksiyonu                    MMO 208/4 - m.3.4.6
  3  Kullanılabilir kabin alanı               EN 81-20 m.5.4.2
  4  Askı halatları                           EN 81-50 m.5.12
  5  Hız regülatörü halatı                    EN 81-20 m.5.6.2.2.1
  6  Tahrik yeteneği                          EN 81-50 m.5.11.2 / m.5.11.3
  7  Kabin kılavuz rayları                    EN 81-50 m.C.2.1 / C.2.2 / C.2.3
  8  Karşı ağırlık kılavuz rayları            EN 81-50 m.5.10
  9  Kuyu tabanına gelen yükler               EN 81-20 m.5.2.1.8
 10  Sığınma alanları ve açıklıklar           EN 81-20 m.5.2.5.7 / 5.2.5.8

Çıktı biçimi avan motoruyla aynıdır ( engine.steps.Bolum / veri / hesap /
kontrol ), böylece ekran, PDF ve XLSX katmanları ortak kalır.
"""
import math

from engine.uygulama import mukavemet_girdi as MG
from engine.uygulama import mukavemet_tablolari as MT
from engine.ortak.steps import Bolum, hesap, kontrol, veri
from engine.ortak.steps import metin, tr, trn

# =====================================================================
#  KAYNAK EXCEL'DEN BİLEREK AYRILAN NOKTALAR
# =====================================================================
#  Uyulması gereken standart TS EN 81-20 / TS EN 81-50'dir;  kaynak Excel
#  yalnız bir başlangıç noktasıdır.  Aşağıdaki noktalarda Excel standarttan
#  ayrılıyor — motor STANDARDI uygular, Excel'i değil.
#
#  Her satır:  ( kısa ad , standart maddesi , Excel'in yaptığı , motorun yaptığı ,
#                etkilenen "11-Muk. Hesapları" hücreleri )
#  Doğrulama testleri bu listeyi okur;  bir sapma sessizce kapanır ya da
#  yenisi eklenirse test bunu söyler.
EXCEL_FARKLARI = (
    ("Tahrik kasnağı / halat oranı",
     "TS EN 81-20 m.5.5.2.1",
     "Başlık '≥ 40' yazar ama kontrolü 30 ile yapar. 30, aynı standardın "
     "m.5.5.6.2 c) dengeleme gergi kasnağı ve m.5.6.2.2.1.3 regülatör eşiğidir.",
     "Standardın istediği 40 uygulanır.",
     ()),
    ("Karşı ağırlık rayı σ(My) böleni",
     "TS EN 81-50 Ek C.2.1.1",
     "σ(My) için Wy'ye böler.",
     "Fy → Mx → Wx.  Standart açıkça 'Fy kuvveti Mx hesabında kullanılır' der; "
     "Excel'in kabin raylarında da, sehim satırlarında da doğrusu yapılmıştır.",
     ("AU575", "Z588", "AF590")),
    ("Durum 2'de xQ",
     "TS EN 81-50 Ek C.2.1.1",
     "Sabit 0 yazar ( satır başlığı 'xQ = xc' dese de ).",
     "xQ = xc.  Durum 2'de yük yalnız y'de kaydırılır;  x'teki moment kolu "
     "kabin merkezidir.  Ek C'nin örneğinde kabin merkezi ray ekseniyle "
     "çakışık olduğu için ( xc = 0 ) iki okuma orada ayrışmaz.",
     ("AY335", "AU338", "Z369", "AJ371", "AE374", "Z384", "AH401",
      "L435", "AU438", "Z468", "AH470", "AH495")),
    ("ω burkulma katsayısı ray çeliğine bağlı",
     "TS EN 81-50 m.5.10.3",
     "Tek bir ω tablosu kullanır;  o tablo yalnız Rm = 370 eğrisidir "
     "( 231/231 değeri standardın 370 formülleriyle birebir çıkar ) ve "
     "ray çeliğinden bağımsız uygulanır.",
     "ω, λ ve Rm'in ikisine birden bağlıdır.  Standart Rm = 370 ve 520 için "
     "iki eğri verir, aradaki dayanımlar için doğrusal ara değer ister — "
     "standardın kendi notu, işlenmiş raylarda 440 yaygın olduğu için bunun "
     "'her zaman yapılması' gerektiğini söyler.  Excel'in yaklaşımı Rm = 440 "
     "ve 520'de ω'yı %23 ve %50 DÜŞÜK verir, yani burkulma gerilmesini "
     "olduğundan küçük gösterir — emniyetsiz taraf.\n"
     "        Ayrıca Excel'in tablosu 2 haneye yuvarlıdır;  motor standardın "
     "formülünü doğrudan kullanır.  Makine kaidesi ST 37 olduğu için orada "
     "( 11!AB39 · K73 ) yalnız bu yuvarlama farkı kalır — %0,2.",
     #  ω'ya bağlı olan her şey:  ω'nın kendisi, burkulma gerilmesi σk ve
     #  σk'yı içeren birleşik gerilmeler.
     ("AD354", "AL354", "AE365", "AE374", "AB39", "K73")),
    ("Acil frenlemede μ  —  halat hızı",
     "TS EN 81-50 m.5.11.2.3.2",
     "μ = 0,1 / ( 1 + v/10 ) bağıntısına KABİN hızını koyar "
     "( 'Veri Girişi'!C61 ).",
     "Bağıntıdaki v HALAT hızıdır:  v_halat = kabin hızı × askı oranı.  "
     "EN 81-50'nin çözümlü örneğinde 1 m/s kabin hızı ve 2:1 askı için "
     "μ = 0,083 çıkar — bu ancak v = 2 m/s ile mümkündür.  Kabin hızı "
     "kullanmak μ'yü, dolayısıyla e^(f·α) sınırını BÜYÜK gösterir:  "
     "tahrik yeteneğini olduğundan iyi çıkarır — emniyetsiz taraf.",
     ("AS190", "AL202", "AV211", "O257", "O271")),
    ("Flanş eğilmesinde ℓ",
     "TS EN 81-50 m.5.10.5",
     "Paydadaki ℓ yerine 1 yazar — ℓ harfi 1 rakamı okunmuş görünüyor.",
     "ℓ = paten balatasının uzunluğu ( girdi ).  Boş bırakılırsa ray "
     "tablosundaki balata yarı genişliğinden ( 2·b ) türetilir.",
     ("Z379", "Z384", "Z476", "Z481", "Z537", "Z595")),
    ("Sığınma açıklıklarının iki alt sınırı",
     "TS EN 81-20 m.5.2.5.7.3  /  m.5.2.5.8.2 a) 2)",
     "Kabin üstü serbest yüksekliğini 1200 mm, ray dibi açıklığını 150 mm "
     "ister.  Standartta bu iki sayı yoktur;  150 mm, m.5.2.5.8.2 a) 1)'deki "
     "YATAY 0,15 m'nin düşey sınır sanılmasından gelmiş görünüyor.",
     "Kabin üstü:  m.5.2.5.7.3 ayakta durulabilen alanın üzerindeki serbest "
     "yüksekliği seçilen sığınma hacminin yüksekliğine bağlar — çömelmiş "
     "duruşta ( Çizelge 3 ) 1,00 m.  Ray dibi:  m.5.2.5.8.2 a) 2) ve Şekil 7, "
     "raya yatay XH ≤ 0,15 m uzaklıktaki karkas / paten / güvenlik tertibatı "
     "için 0,10 m verir.\n"
     "        Excel'in iki sayısı da standarttan KATI taraftadır;  yani "
     "emniyetsiz bir tasarımı geçirmez, ama standarda uygun bir projeyi "
     "haksız yere reddeder ( kuyu boyunu gereksiz büyütür ).\n"
     "        Ayrıca karşılaştırma '>' idi;  standart 'en az' dediği için "
     "sınıra eşit ölçü de uygundur — '≥' yapıldı.",
     ()),
)

#  Testlerin okuduğu düz küme
FARKLI_HUCRELER = tuple(sorted({h for *_x, hucreler in EXCEL_FARKLARI
                                for h in hucreler}))


# =====================================================================
#  SABİTLER
# =====================================================================
#  Bu değerler Excel'de doğrudan hücreye yazılıdır ( girdi değildir ).
#  Kaynakları yanlarında; değiştirmek gerekirse tek yer burasıdır.
SABIT = {
    "gn":              9.81,      # yerçekimi ivmesi              [m/s²]
    "Gs":              0,         # sürtünme yükü                 [kg]   (11!AQ8)
    "motor_verimi":    0.92,      # η                                    (11!AQ22)
    "motor_sabiti":    102,       # kW ↔ kg·m/s dönüşümü                 (11!AQ23)
    "hp_carpani":      1.34,      # kW → HP                              (11!X25)
    "halat_pay_m":     5,         # halat boyu payı               [m]    (11!AQ19)
    "sigma_em":        130,       # ST 37 emniyet gerilmesi     [N/mm²]  (11!AB40)
    "yan_yatak_L_X":   335,       # L − X  ( kaide kiriş mesnedi ) [mm]  (11!S58)
    "Dt_dh_asgari":    40,        # tahrik kasnağı / halat oranı   EN 81-20 m.5.5.2.1
    "Dreg_dreg_asgari": 30,       # regülatör kasnağı / halat oranı      (11!N142)
    "reg_kat_asgari":  8,         # regülatör halatı emniyet katsayısı   (11!K161)
    "reg_kuvvet_asgari": 300,     # F'reg alt sınırı              [N]    (11!AA156)
    "reg_sarilma_aci": 180,       # α'  regülatör kasnağı sarılma [°]    (11!AI133)
    "Nps":             1,         # tek yönde bükülmeli kasnak sayısı    (11!AH105)
    "Npr":             0,         # ters yönde bükülmeli kasnak sayısı   (11!AH106)
    "mu_yukleme":      0.1,       # μ  yükleme                           (11!V188)
    "mu_bloke":        0.2,       # μ  kabin bloke                       (11!V192)
    "kanal_acisi":     38,        # γ  sertleştirilmiş kanal      [°]    (11!AH102)
    "alt_kesilme":     90,        # β  alt kesilme açısı          [°]    (11!AH103)
    "E":               206010,    # elastisite modülü           [N/mm²]  (11!AH302)
    "k3":              1.2,       # normal kullanma darbe katsayısı      (EN 81-20 Çiz.14)
    "MY_kabin":        150,       # kabin rayına bağlı donanım    [N]    (11!AH292)
    "MY_agirlik":      50,        # ağırlık rayına bağlı donanım  [N]    (11!AH555)
    "dperm_kabin":     5,         # kabin rayı azami sehim        [mm]   (11!AH306)
    "dperm_agirlik":   10,        # ağırlık rayı azami sehim      [mm]   (11!AL600)
    "sehim_katsayi":   0.7,       # sehim formülü katsayısı              (11!R393)
    "sehim_bolen":     48,        # 48·E·I                               (11!U394)
    "moment_pay":      3,         # M = 3·F·l/16                         (11!M324)
    "moment_bolen":    16,
    "birlesik_katsayi": 0.9,      # σk + 0,9·σm                          (11!X365)
    "kabin_merkez_payi": 130,     # xc = ( derinlik/2 + 130 ) − RK  [mm] (11!AH293)
    "Dx_bolen":        8,         # Dx = derinlik / 8                    (11!S310)
    "Dy_bolen":        8,         # Dy = genişlik  / 8                   (11!S313)
    "Dxa_katsayi":     0.1,       # Dxa = 0,1 × ağırlık derinliği        (11!N562)
    "Dya_katsayi":     0.05,      # Dya = 0,05 × ağırlık genişliği       (11!AL562)
    "Fs_alt":          0.4,       # eşik kuvveti  Q < 2500 kg            (11!AH303)
    "Fs_ust":          0.6,       # eşik kuvveti  Q ≥ 2500 kg
    "Fs_sinir":        2500,      # [kg]
    "tampon_katsayi":  4,         # F = 4·gn·(P+Q)                       (11!R621)
    "q_denge":         0.5,       # karşı ağırlık denge oranı            (11!AA627)
    "FRcar_katsayi":   0.02,      # kabin sürtünme direnci        (Askı Tipleri!P128)
    "FRcwt_katsayi":   0.015,     # ağırlık sürtünme direnci      (Askı Tipleri!P129)
    "ray_kaide_payi":  200,       # ray boyu:  kaide yüksekliği − 200 mm (11!AH291)
    "ray_kuyu_payi":   300,       # ray boyu:  kuyu dibi − 300 mm
}

#  Sığınma alanı hesaplarındaki kabin/kuyu geometrisi payları.  Excel'de
#  doğrudan formüle gömülüdür ( 11!AI635…AI648 ); ofis kabulüdür, MMO ya da
#  EN 81-20 sayısı DEĞİLDİR.
SIGINMA = {
    "kabin_yuksekligi":     2400,   # üst paten - ray üst ucu payı      [mm]
    "kabin_ust_donanim":    2100,   # kabin üstü kotu                   [mm]
    "paten_payi":            300,
    "tavan_payi":            150,
    "revizyon_payi":         500,
    "etek_payi":             400,
    "etek_kotu":             950,
    "ray_alt_payi":          270,
    "regulator_payi":        300,
    #  EN 81-20 Çizelge 3 / Çizelge 4  —  çömelmiş duruş sığınma hacmi  [m]
    "ust_hacim":            (0.7, 0.5, 1.0),
    "dip_hacim":            (0.5, 0.7, 1.0),
    #  ---------------------------------------------------------------
    #  TS EN 81-20 asgari açıklıklar  [mm].  Her satırın karşısındaki
    #  madde numarası standardın kendi metnindendir.
    #  ---------------------------------------------------------------
    "min_ust_paten":         100,   # m.5.2.5.6.2  ilave kılavuzlu yol   0,10 m
    #  m.5.2.5.7.3:  kabin üstünde ayakta durulabilen her alanın üzerindeki
    #  serbest yükseklik, seçilen sığınma hacminin yüksekliği kadardır —
    #  çömelmiş duruşta ( Çizelge 3, tip 2 ) 1,00 m.  Ayrı bir sabit
    #  tutulmaz;  doğrudan  ust_hacim[2]  okunur.
    "min_revizyon":          500,   # m.5.2.5.7.2 a) kabin üstü donanım  0,50 m
    "min_kuyu_tabani":       500,   # m.5.2.5.8.2 a) kuyu dibi - kabin   0,50 m
    "min_etek":              100,   # m.5.2.5.8.2 a) 1) etek            0,10 m
    #  m.5.2.5.8.2 a) 2) + Şekil 7:  raya yatay XH ≤ 0,15 m uzaklıktaki
    #  karkas parçaları, paten ve güvenlik tertibatı için asgari düşey
    #  açıklık 0,10 m'dir.  ( Şekil 7 eğrisi:  0,15 m → 0,10 m ·
    #  0,30 m → 0,30 m ·  0,50 m ve ötesi → 0,50 m. )
    "min_ray_alt":           100,
    "min_regulator":         300,   # m.5.2.5.8.2 b) kuyuya sabit parça  0,30 m
}


def _bosluk(v):
    """0,10 m ilave kılavuzlu yol + 0,035·v² sıçrama payı  →  mm.

    TS EN 81-20'de 0,035·v² açıklığın değil, kabinin en üst konumunun
    tanımındadır ( Çizelge 2 );  0,10 m ise m.5.2.5.6.2'nin ilave kılavuzlu
    yoludur.  Kuyu ölçüleri anma konumundan alındığı için ikisi burada
    tek sınırda toplanır — eşitsizlik cebirsel olarak aynıdır.
    """
    return (0.1 + 0.035 * v * v) * 1000


def _oran(a, b):
    return max(a / b, b / a) if (a and b) else None


def _kay(o, **hucreler):
    """Hesaplanan değeri kaynak Excel'deki hücre adresine bağlar.

    Motoru Excel'e karşı hücre hücre doğrulayabilmek için tek yol budur;
    doğrulama testi bu haritayı okur, hesabı tekrar etmez.
    Anahtarlar "11-Muk. Hesapları" sayfasının adresleridir.
    """
    o.setdefault("_h", {}).update(hucreler)


# =====================================================================
#  1 -  ASANSÖR MOTOR GÜCÜ                        ( MMO 208/7 - 2.4 )
# =====================================================================
def _motor(g, o):
    S = SABIT
    Q, P, v = g["beyan_yuku"], g["kabin_agirligi"], g["beyan_hizi"]
    Dt, dh, nh, r = (g["tahrik_kasnak_capi"], g["halat_capi"],
                     g["halat_adedi"], g["aski_orani"])
    gh = MT.halat_agirlik(dh)

    #  Halat boyu:  kuyu boyundan tampon/paten yığını düşülür, 5 m pay eklenir;
    #  2:1 askıda halat iki kat gider.
    yigin = (g["agirlik_tampon_baba"] + g["agirlik_carpma_arasi"]
             - g["agirlik_tampon_ezilme"] + g["agirlik_paten_arasi"]
             + g["kabin_paten_arasi"])
    lh = (g["kuyu_boyu"] - yigin) / 1000.0 + S["halat_pay_m"]
    if r != 1:
        lh *= 2
    Gh = gh * lh * nh
    F1 = Q + P + Gh                       # kabin ve aksesuarlarının yükü
    Ga = P + S["q_denge"] * Q             # karşı ağırlık yükü
    Gmax = F1 + S["Gs"] - Ga              # maksimum artan yük
    Pm = F1 - Ga                          # makine miline gelen döndürme kuvveti
    M = Gmax * (Dt / 2000.0)              # moment
    N = Gmax * v / (S["motor_verimi"] * S["motor_sabiti"])
    HP = N * S["hp_carpani"]
    uygun = g["motor_gucu"] >= N

    o.update(Q=Q, P=P, v=v, gh=gh, lh=lh, Gh=Gh, F1=F1, Ga=Ga, Gmax=Gmax,
             N_hesap=N, motor_uygun=uygun, r=r, nh=nh, dh=dh, Dt=Dt)
    _kay(o, AQ18=gh, AQ19=lh, AQ16=Gh, AQ11=F1, AQ13=Ga, AQ9=Gmax, AQ7=Pm,
         AQ21=M, AQ23=N, X25=HP)

    b = Bolum("1 -  ASANSÖR MOTOR GÜCÜNÜN HESAPLANMASI", "MMO 208/7 - 2.4")
    b["adimlar"] = [
        veri("v", "Kabin hızı", v, "m/s", "GİRİŞ"),
        veri("Q", "Beyan yükü", Q, "kg", "GİRİŞ"),
        veri("P", "Boş kabin ağırlığı", P, "kg", "GİRİŞ"),
        veri("dh", "Halat çapı", dh, "mm", "GİRİŞ"),
        veri("nh", "Halat sayısı", nh, "adet", "GİRİŞ"),
        veri("gh", "Halatın 1 m'deki ağırlığı", gh, "kg/m",
             f"TS 12385-5  ·  {MT.halat_tipi(dh)}", 4),
        hesap("lh = ( Kuyu boyu − tampon/paten yığını ) / 1000 + 5"
              + ("  ( × 2 :  2:1 askı )" if r != 1 else ""),
              f"( {trn(g['kuyu_boyu'], 0)} − {trn(yigin, 0)} ) / 1000 + "
              f"{S['halat_pay_m']}" + ("  × 2" if r != 1 else ""),
              lh, "m", "11!AQ19"),
        hesap("Gh = gh × lh × nh", f"{tr(gh)} × {tr(lh)} × {trn(nh, 0)}",
              Gh, "kg"),
        hesap("F1 = P + Q + Gh", f"{trn(P, 0)} + {trn(Q, 0)} + {tr(Gh)}", F1, "kg"),
        hesap("Ga = P + Q / 2", f"{trn(P, 0)} + {trn(Q, 0)} / 2", Ga, "kg"),
        veri("Gs", "Sürtünme yükü", S["Gs"], "kg", "Ofis kabulü"),
        hesap("Gmax = F1 + Gs − Ga", f"{tr(F1)} + {tr(S['Gs'])} − {tr(Ga)}",
              Gmax, "kg"),
        hesap("Pm = F1 − Ga", f"{tr(F1)} − {tr(Ga)}", Pm, "kg"),
        veri("Dt", "Tahrik kasnağı çapı", Dt, "mm", "GİRİŞ"),
        hesap("M = Gmax × ( Dt / 2 )", f"{tr(Gmax)} × {tr(Dt / 2000.0)}", M, "kg·m"),
        veri("η", "Motor verimi", S["motor_verimi"], "", "Ofis kabulü"),
        hesap("N = Gmax × v / ( η × 102 )",
              f"{tr(Gmax)} × {tr(v)} / ( {tr(S['motor_verimi'])} × 102 )",
              N, "kW", "MMO 208/7 - 2.4"),
        hesap("HP = N × 1,34", f"{tr(N)} × 1,34", HP, "HP"),
        veri("Nsç", "Kullanılan motor gücü", g["motor_gucu"], "kW", "GİRİŞ"),
    ]
    b["notlar"] = [f"Binada en az {tr(N)} kW ( {tr(HP)} HP ) gücünde makine "
                   "motor kullanılacaktır."]
    b["sonuc"] = {"baslik": "KONTROL      Nsç  ≥  N",
                  "metin": "UYGUNDUR." if uygun else "UYGUN DEĞİLDİR — motoru büyütün",
                  "uygun": bool(uygun)}
    return b


# =====================================================================
#  2 -  MAKİNE KONSTRÜKSİYONU                   ( MMO 208/4 - m.3.4.6 )
# =====================================================================
def _makine(g, o):
    S, gn = SABIT, SABIT["gn"]
    k1 = MT.darbe_k1(g["guvenlik_tertibati"])
    Gm, L, L1 = g["makine_agirligi"], g["yan_yatak_boyu"], g["sase_yuksekligi"]
    A = MT.npu(g["dikine_kiris"], "A") * 100            # cm² → mm²
    #  NPU tablosunun 14. sütunu:  atalet YARIÇAPI ix ( cm ).  Excel bu satırı
    #  "Imin — eylemsizlik momenti" diye adlandırır ama λ = L1 / imin
    #  bağıntısında yarıçap kullanılır; adlandırma matematiğe göre yapıldı.
    imin = MT.npu(g["dikine_kiris"], "ix") * 10         # cm → mm
    Wx = MT.npu(g["yan_yatak"], "Wx") * 1000            # cm³ → mm³

    F = k1 * gn * (o["Q"] + o["P"] + o["Gh"] + o["Ga"] + Gm)
    F1 = F / 2.0                                        # yan yatak putreli
    X = L - S["yan_yatak_L_X"]
    FB = F1 * X / L
    FA = F1 - FB
    Mmax = FA * X
    sigma_e = Mmax / Wx
    lam_ham = L1 / imin
    lam = max(20, math.ceil(lam_ham - 1e-9))
    #  Kaide kirişi ST 37'dir ( σem = 130 ) — ω'nın Rm = 370 eğrisi geçerli.
    omega = MT.omega_en8150(lam, MT.OMEGA_RM_ALT)
    sigma_b = FB * omega / A if omega else None
    egilme_uygun = sigma_e < S["sigma_em"]
    burkulma_uygun = sigma_b is not None and sigma_b < S["sigma_em"]

    o.update(k1=k1, F_kaide=F, FA=FA, FB=FB)
    _kay(o, AB31=k1, AB37=A, AB38=imin, AB41=Wx, AB39=omega, C47=F, I51=F1,
         K58=X, O53=FB, AK53=FA, M63=Mmax, J65=sigma_e, O71=lam_ham, Z71=lam,
         K73=sigma_b)

    b = Bolum("2 -  MAKİNE KONSTRÜKSİYONUNUN HESAPLANMASI", "MMO 208/4 - m.3.4.6")
    b["adimlar"] = [
        veri("k1", "Darbe katsayısı", k1, "",
             f"EN 81-20 Çizelge 14  ·  {g['guvenlik_tertibati']}"),
        veri("Gm", "Makine motor ağırlığı", Gm, "kg", "GİRİŞ ( üretici kataloğu )"),
        veri("L", "Yan yatak boyu", L, "mm", "GİRİŞ"),
        veri("L1", "Dikine kirişin boyu", L1, "mm", "GİRİŞ"),
        veri("A", "Dikine kirişin kesit alanı", A, "mm²",
             f"NPU {g['dikine_kiris']}", 0),
        veri("imin", "Dikine kirişin atalet yarıçapı", imin, "mm",
             f"NPU {g['dikine_kiris']}"),
        veri("Wx", "Yan yatağın mukavemet momenti", Wx, "mm³",
             f"NPU {g['yan_yatak']}", 0),
        veri("σem", "Emniyet gerilmesi ( ST 37 )", S["sigma_em"], "N/mm²", "Ofis kabulü"),
        metin("Kaide üzerindeki en büyük kuvvet :"),
        hesap("F = k1 × gn × ( Q + P + Gh + Ga + Gm )",
              f"{tr(k1)} × {tr(gn)} × ( {trn(o['Q'], 0)} + {trn(o['P'], 0)} + "
              f"{tr(o['Gh'])} + {tr(o['Ga'])} + {trn(Gm, 0)} )", F, "N"),
        metin("Yan yatak putreline gelen kuvvet :"),
        hesap("F1 = F / 2", f"{tr(F)} / 2", F1, "N"),
        hesap("X = L − 335", f"{trn(L, 0)} − {S['yan_yatak_L_X']}", X, "mm"),
        hesap("FB = F1 × X / L", f"{tr(F1)} × {trn(X, 0)} / {trn(L, 0)}", FB, "N"),
        hesap("FA = F1 − FB", f"{tr(F1)} − {tr(FB)}", FA, "N"),
        metin("Kaide yatay kirişlerinde eğilme momenti ve gerilmesi :"),
        hesap("Mmax = FA × X", f"{tr(FA)} × {trn(X, 0)}", Mmax, "N·mm", ondalik=0),
        hesap("σe = Mmax / Wx", f"{trn(Mmax, 0)} / {trn(Wx, 0)}", sigma_e, "N/mm²"),
        kontrol(f"σe = {tr(sigma_e)}  <  σem = {tr(S['sigma_em'])} N/mm²  →  "
                f"NPU {g['yan_yatak']}", egilme_uygun),
        metin("Dikine kirişlerin bükülme kontrolü :"),
        hesap("λ = L1 / imin", f"{trn(L1, 0)} / {tr(imin)}", lam_ham, ""),
        veri("λ", "Yuvarlanmış burkulma narinliği ( en az 20 )", lam, "", "11!Z71", 0),
        veri("ω", "Omega değeri", omega, "", f"Burkulma tablosu  λ = {lam}", 4),
        hesap("σb = FB × ω / A",
              f"{tr(FB)} × {tr(omega)} / {trn(A, 0)}", sigma_b, "N/mm²"),
        kontrol(f"σb = {tr(sigma_b)}  <  σem = {tr(S['sigma_em'])} N/mm²  →  "
                f"NPU {g['dikine_kiris']}", burkulma_uygun),
    ]
    b["sonuc"] = {"baslik": "KONTROL      σe < σem   ve   σb < σem",
                  "metin": "UYGUNDUR." if (egilme_uygun and burkulma_uygun)
                           else "UYGUN DEĞİLDİR — kiriş kesitini büyütün",
                  "uygun": bool(egilme_uygun and burkulma_uygun)}
    return b


# =====================================================================
#  3 -  KULLANILABİLİR KABİN ALANI              ( TS EN 81-20 m.5.4.2 )
# =====================================================================
def _kabin_alani(g, o):
    Q = g["beyan_yuku"]
    W, D = g["kabin_genisligi"], g["kabin_derinligi"]
    azami = MT.kabin_azami_alan(Q)
    asgari = MT.kabin_asgari_alan(Q)
    kisi = MT.kabin_kisi(Q)
    alan = (W * D) / 1e6
    pervaz = g["uzun_pervaz"]
    #  Pervaz 100 mm ve üzerindeyse kapı önü girintisi de kullanılabilir
    #  alana katılır  ( 11!X84 ).
    if pervaz >= 100:
        alan += ((g["kapi_genisligi"] / 2.0) * pervaz) / 1e6
    ust_uygun = azami is not None and azami >= alan
    alt_uygun = asgari is not None and alan >= asgari
    o.update(kabin_alani=alan, kabin_kisi=kisi)
    _kay(o, X84=alan, AC82=azami, L86=kisi, AK88=asgari)

    b = Bolum("3 -  KULLANILABİLİR KABİN ALANI", "TS EN 81-20 m.5.4.2")
    b["adimlar"] = [
        veri("Q", "Beyan yükü", Q, "kg", "GİRİŞ"),
        veri("", "Kabin genişliği × derinliği", f"{trn(W, 0)} × {trn(D, 0)} mm"),
        hesap("Kabin alanı = ( genişlik × derinlik ) / 10⁶"
              + ("  +  ( kapı genişliği / 2 × uzun pervaz ) / 10⁶"
                 if pervaz >= 100 else ""),
              f"( {trn(W, 0)} × {trn(D, 0)} ) / 10⁶"
              + (f" + ( {trn(g['kapi_genisligi'], 0)} / 2 × {trn(pervaz, 0)} ) / 10⁶"
                 if pervaz >= 100 else ""),
              alan, "m²", "11!X84", 4),
        veri("", f"{trn(Q, 0)} kg için kullanılabilir EN BÜYÜK kabin alanı",
             azami, "m²", "EN 81-20 Çizelge 6"),
        kontrol(f"Kabin alanı {tr(alan)} m²  ≤  {tr(azami)} m²", ust_uygun),
        veri("", "Kabindeki insan sayısı", kisi, "kişi", "EN 81-20 Çizelge 6", 0),
        veri("", f"{trn(kisi, 0)} kişi için kullanılabilir EN KÜÇÜK kabin alanı",
             asgari, "m²", "EN 81-20 Çizelge 8"),
        kontrol(f"Kabin alanı {tr(alan)} m²  ≥  {tr(asgari)} m²", alt_uygun),
    ]
    b["sonuc"] = {"baslik": "KONTROL      Amin  ≤  Akabin  ≤  Amax",
                  "metin": "UYGUNDUR." if (ust_uygun and alt_uygun)
                           else "UYGUN DEĞİLDİR — kabin ölçülerini düzeltin",
                  "uygun": bool(ust_uygun and alt_uygun)}
    return b


# =====================================================================
#  4 -  ASKI HALATLARI                           ( TS EN 81-50 m.5.12 )
# =====================================================================
def _aski_halatlari(g, o):
    S, gn = SABIT, SABIT["gn"]
    Dt, dh, nh, r = o["Dt"], o["dh"], o["nh"], o["r"]
    Dp = g["saptirma_kasnak_capi"]
    oran = Dt / dh
    oran_uygun = oran >= S["Dt_dh_asgari"]

    Nps, Npr = g["kasnak_tek_yon"], g["kasnak_ters_yon"]
    Nequiv_t = MT.kanal_nequiv_t(g["kanal_sekli"])
    Tmin = MT.halat_kopma(dh)
    Smin = 16 if nh < 3 else 12
    Kp = (Dt / Dp) ** 4
    Nequiv_p = Kp * (Nps + 4 * Npr)
    Nequiv = Nequiv_t + Nequiv_p
    #  EN 81-50 m.5.12 halat güvenlik katsayısı
    Sf = 10 ** (2.6834 - (math.log10(695.85e6 * Nequiv / oran ** 8.567)
                          / math.log10(77.09 * oran ** -2.894)))
    Fmax = gn * o["F1"] / r
    Sger = nh * Tmin / Fmax
    sinir = max(Sf, Smin)
    sf_uygun = Sf >= Smin
    s_uygun = Sger >= sinir
    o.update(Sf=Sf, S_gercek=Sger)
    _kay(o, N97=oran, AH104=Nequiv_t, AH109=Tmin, AH110=Smin, T112=Kp,
         P114=Nequiv_p, V116=Nequiv, T125=Sf, T126=Sger)

    b = Bolum("4 -  ASKI HALATLARININ HESAPLANMASI", "TS EN 81-50 m.5.12")
    b["adimlar"] = [
        metin("Tahrik kasnağı & askı halatı oranı  ( TS EN 81-20 m.5.5.2.1 ) :"),
        hesap("Dt / dh", f"{trn(Dt, 0)} / {tr(dh)}", oran, ""),
        kontrol(f"Dt / dh = {tr(oran)}  ≥  {S['Dt_dh_asgari']}", oran_uygun),
        metin("Halat güvenlik katsayısının hesaplanması :"),
        veri("", "Kanal tipi", g["kanal_sekli"]),
        veri("γ", "Kanal açısı", MT.kanal_acisi(g["kanal_sekli"]), "°",
             "EN 81-50 Çizelge 2", 0),
        veri("Nequiv(t)", "Kasnakların eşdeğer sayısı", Nequiv_t, "",
             "EN 81-50 Çizelge 2", 0),
        veri("Nps", "Tek yönde bükülmeli kasnak sayısı", Nps, "adet", "GİRİŞ", 0),
        veri("Npr", "Ters yönde bükülmeli kasnak sayısı", Npr, "adet", "GİRİŞ", 0),
        veri("Dp", "Tahrik kasnağı hariç kasnakların ortalama çapı", Dp, "mm", "GİRİŞ"),
        veri("r", "Halat askı oranı", r, "", "GİRİŞ", 0),
        veri("Tmin", "Halatın en küçük kopma değeri", Tmin, "N", "TS 12385-5", 0),
        veri("Smin", "Asgari halat güvenlik katsayısı", Smin, "",
             "EN 81-20 m.5.5.2.2  ( nh < 3 ise 16 )", 0),
        hesap("Kp = ( Dt / Dp )⁴", f"( {trn(Dt, 0)} / {trn(Dp, 0)} )⁴", Kp, "", ondalik=4),
        hesap("Nequiv(p) = Kp × ( Nps + 4 × Npr )",
              f"{tr(Kp)} × ( {trn(Nps, 0)} + 4 × {trn(Npr, 0)} )", Nequiv_p, "",
              "EN 81-50 m.5.12.2"),
        hesap("Nequiv = Nequiv(t) + Nequiv(p)",
              f"{tr(Nequiv_t)} + {tr(Nequiv_p)}", Nequiv, ""),
        hesap("Sf = 10^[ 2,6834 − log( 695,85·10⁶ · Nequiv / (Dt/dh)^8,567 ) "
              "/ log( 77,09 · (Dt/dh)^−2,894 ) ]",
              f"Nequiv = {tr(Nequiv)} ,  Dt/dh = {tr(oran)}", Sf, "",
              "EN 81-50 m.5.12"),
        kontrol(f"Sf = {tr(Sf)}  ≥  Smin = {trn(Smin, 0)}", sf_uygun),
        hesap("S = nh × Tmin / Fmax        ( Fmax = gn × F1 / r )",
              f"{trn(nh, 0)} × {trn(Tmin, 0)} / ( {tr(gn)} × {tr(o['F1'])} / {trn(r, 0)} )",
              Sger, ""),
        kontrol(f"S = {tr(Sger)}  ≥  {tr(sinir)}", s_uygun),
    ]
    b["sonuc"] = {"baslik": "KONTROL      Dt/dh ≥ 30   ·   Sf ≥ Smin   ·   S ≥ Sf",
                  "metin": "UYGUNDUR." if (oran_uygun and sf_uygun and s_uygun)
                           else "UYGUN DEĞİLDİR — halat çapını / adedini artırın",
                  "uygun": bool(oran_uygun and sf_uygun and s_uygun)}
    if r > 1 and Nps < 2:
        b["notlar"] = [
            "⚠ Palangalı ( 1:" + trn(r, 0) + " ) sistemde halatın en olumsuz "
            "kesiti genelde tahrik kasnağı + EN AZ İKİ kabin kasnağı üzerinden "
            "geçer ( EN 81-50 Ek E ). Tek yönde bükülmeli kasnak sayısı "
            f"{trn(Nps, 0)} girilmiş; tesisin gerçek askı düzenine göre "
            "denetleyin — düşük girilirse Nequiv, dolayısıyla gereken "
            "asgari güvenlik katsayısı olduğundan küçük çıkar."]
    b["aciklamalar"] = [
        "TS EN 81-20 m.5.5.2.1: tahrik kasnağı / saptırma kasnağı bölüm dairesi "
        "çapının askı halatı anma çapına oranı, halatın kol sayısından bağımsız "
        "olarak EN AZ 40 olmalıdır. Kaynak Excel bu kontrolü 30 ile yapar; 30 "
        "aynı standardın dengeleme halatı gergi kasnağı ( m.5.5.6.2 ) ve "
        "regülatör ( m.5.6.2.2.1.3 ) eşiğidir, askı halatının değil."]
    return b


# =====================================================================
#  5 -  HIZ REGÜLATÖRÜ HALATI               ( TS EN 81-20 m.5.6.2.2.1 )
# =====================================================================
def _regulator(g, o):
    S, gn = SABIT, SABIT["gn"]
    Dreg, dreg = g["reg_kasnak_capi"], g["reg_halat_capi"]
    mu, gama = g["reg_surtunme"], g["reg_kanal_acisi"]
    alfa = S["reg_sarilma_aci"]
    #  Regülatör halatı kuyu boyunca iki kat gider  ( 11!AI134 )
    boy = ((sum(g["durak_yukseklikleri"]) + g["kaide_yuksekligi"]
            - S["ray_kaide_payi"]) * 2) / 1000.0
    gh = MT.halat_agirlik(dreg) * boy
    Gra = g["reg_gergi_agirligi"]
    Tmin = MT.halat_kopma(dreg)

    oran = Dreg / dreg
    oran_uygun = oran >= S["Dreg_dreg_asgari"]
    f = mu / math.sin(math.radians(gama) / 2.0)
    efa = math.exp(f * math.radians(alfa))
    Freg = gn * (gh + Gra) / 2.0
    Freg2 = Freg * efa
    sinir = max(S["reg_kuvvet_asgari"], 2 * Freg)
    kuvvet_uygun = Freg2 >= sinir
    kat = Tmin / Freg2
    kat_uygun = kat >= S["reg_kat_asgari"]

    _kay(o, AI134=gh, AI136=Tmin, J142=oran, W146=f, AF146=efa, W151=Freg,
         J156=Freg2, AA156=sinir, G161=kat)

    b = Bolum("5 -  HIZ REGÜLATÖRÜ HALATININ HESAPLANMASI",
              "TS EN 81-20 m.5.6.2.2.1  /  TS EN 81-50 m.5.11.2.3")
    b["adimlar"] = [
        veri("Dreg", "Regülatör kasnak çapı", Dreg, "mm", "GİRİŞ"),
        veri("dreg", "Regülatör halat çapı", dreg, "mm", "GİRİŞ"),
        veri("μ", "Sürtünme faktörü", mu, "", "GİRİŞ"),
        veri("γ", "Kanal açısı", gama, "°", "GİRİŞ", 0),
        veri("α'", "Regülatör kasnağı sarılma açısı", alfa, "°", "Ofis kabulü", 0),
        hesap("gh = ( 1 m ağırlık ) × ( Σ durak + kaide − 200 ) × 2 / 1000",
              f"{tr(MT.halat_agirlik(dreg))} × {tr(boy)}", gh, "kg"),
        veri("Gra", "Regülatör alt ağırlığı ve kasnak kütlesi", Gra, "kg", "GİRİŞ"),
        veri("T'min", "Halatın en küçük kopma yükü", Tmin, "N", "TS 12385-5", 0),
        metin("Regülatör kasnağı & halat oranı :"),
        hesap("Dreg / dreg", f"{trn(Dreg, 0)} / {tr(dreg)}", oran, ""),
        kontrol(f"Dreg / dreg = {tr(oran)}  ≥  {S['Dreg_dreg_asgari']}", oran_uygun),
        metin("Regülatör halatında oluşan gergi kuvveti :"),
        hesap("f = μ / sin( γ / 2 )",
              f"{tr(mu)} / sin( {trn(gama, 0)}° / 2 )", f, "", ondalik=4),
        hesap("e^(f·α')", f"exp( {tr(f)} × {trn(alfa, 0)}° )", efa, "", ondalik=4),
        hesap("Freg = gn × ( gh + Gra ) / 2",
              f"{tr(gn)} × ( {tr(gh)} + {trn(Gra, 0)} ) / 2", Freg, "N"),
        hesap("F'reg = Freg × e^(f·α')", f"{tr(Freg)} × {tr(efa)}", Freg2, "N"),
        kontrol(f"F'reg = {tr(Freg2)} N  ≥  {tr(sinir)} N   "
                "( en az 300 N ve 2 × Freg )", kuvvet_uygun),
        metin("Regülatör halatı emniyet katsayısı :"),
        hesap("T'min / F'reg", f"{trn(Tmin, 0)} / {tr(Freg2)}", kat, ""),
        kontrol(f"T'min / F'reg = {tr(kat)}  ≥  {S['reg_kat_asgari']}", kat_uygun),
    ]
    b["sonuc"] = {"baslik": "KONTROL      Dreg/dreg ≥ 30   ·   F'reg ≥ 300 N   ·   "
                            "T'min/F'reg ≥ 8",
                  "metin": "UYGUNDUR." if (oran_uygun and kuvvet_uygun and kat_uygun)
                           else "UYGUN DEĞİLDİR",
                  "uygun": bool(oran_uygun and kuvvet_uygun and kat_uygun)}
    return b


# =====================================================================
#  6 -  TAHRİK YETENEĞİ                  ( TS EN 81-50 m.5.11.2 / 5.11.3 )
# =====================================================================
#  Yük durumları  —  Excel'in "Askı Tipleri" sayfası ( L…Q sütunları ).
#  Her durum, EN 81-50 m.5.11.2 terimlerini kendi işaretleriyle üretir.
YUK_DURUMLARI = (
    ("yukleme", "Kabinin yüklenmesi  ( %125 yüklü kabin en alt durakta dururken )"),
    ("fren_alt", "Acil frenleme  ( %100 yüklü kabin en alt durakta )"),
    ("fren_ust", "Acil frenleme  ( boş kabin en üst durakta )"),
    ("bloke", "Karşı ağırlığın asılı kalması  ( boş kabin en üstte )"),
)


def _terimler(g, o, durum):
    """Bir yük durumunun EN 81-50 m.5.11.2 terimleri  ( Askı Tipleri sayfası )."""
    S = SABIT
    Q, P, r = o["Q"], o["P"], o["r"]
    nh, gh, H = o["nh"], o["gh"], g["seyir_mesafesi"]
    Mcwt = g["karsi_agirlik"]
    a_in = g["acil_frenleme_a"]
    w_kablo = ((MT.kablo_agirligi(g["kablo_tipi_1"]) or 0)
               + (MT.kablo_agirligi(g["kablo_tipi_2"]) or 0))
    ycar = ycwt = H / 2.0        # Askı Tipleri!*131 · *132

    t = {"P": P, "Q": 0.0, "Mcwt": Mcwt, "MCRcar": 0.0, "MCRcwt": 0.0,
         "MComp": 0.0, "MTrav": 0.0, "mPTD": 0.0, "mDP": 0.0, "iPDT": 0.0,
         "r": r, "gn": S["gn"], "a": 0.0,
         "MSRcar": 0.0, "MSRcwt": 0.0, "FRcar": 0.0, "FRcwt": 0.0}
    #  MSR:  askı halatlarının kabin / karşı ağırlık tarafındaki indirgenmiş
    #  kütlesi.  Kabin ve karşı ağırlık tarafı Excel'de AYRI satırlardan
    #  ( ycar · ycwt ) okunur;  ikisi sayısal olarak eşit olsa da ayrım korunur.
    ust_car = (0.5 * H + ycar) * nh * gh      # kabin en üstte  →  halat kabin tarafında
    alt_car = (0.5 * H - ycar) * nh * gh      # kabin en altta  ( ycar = H/2 → 0 )
    ust_cwt = (0.5 * H + ycwt) * nh * gh
    alt_cwt = (0.5 * H - ycwt) * nh * gh
    #  MTrav:  gezici kablonun indirgenmiş kütlesi
    trav = (0.25 * H + 0.5 * ycar) * w_kablo

    if durum == "yukleme":                    # Askı Tipleri sütun M
        t["Q"] = 1.25 * Q
        t["MSRcar"], t["MSRcwt"] = alt_car, ust_cwt
    elif durum == "fren_alt":                 # sütun P
        t["Q"] = Q
        t["a"] = a_in
        t["MSRcar"], t["MSRcwt"] = alt_car, ust_cwt
    elif durum == "fren_ust":                 # sütun Q
        t["a"] = a_in
        t["MSRcar"], t["MSRcwt"] = ust_car, alt_cwt
        t["MTrav"] = trav
    elif durum == "bloke":                    # sütun O
        t["Mcwt"] = 0.0
        t["MSRcar"] = alt_car
        #  Excel bu tek hücrede farklı bir bağıntı kullanır  ( Askı Tipleri!O120 ):
        #  MSRcwt = nh × H × gh   —  yarım seyir yerine tam seyir.
        t["MSRcwt"] = nh * H * gh
        t["MTrav"] = trav
    return t


def _T1(t, FRcar, i):
    """Kabin tarafındaki halat kuvveti  T1  ( EN 81-50 m.5.11.2 ).

    i = ( a , MSR , iPDT , mDP , FR )  işaretleri — her yük durumunda farklıdır.
    """
    r, gn, a = t["r"], t["gn"], t["a"]
    return ((t["P"] + t["Q"] + t["MCRcar"] + t["MTrav"]) * (gn + i[0] * a) / r
            + (t["MComp"] / 2.0 / r) * gn
            + i[1] * t["MSRcar"] * (gn + a * (r * r + 2) / 3.0)
            + i[2] * (t["iPDT"] * t["mPTD"] * a) / (2.0 * r)
            + i[3] * t["mDP"] * a / 2.0
            + i[4] * FRcar / r)


def _T2(t, FRcwt, i):
    """Karşı ağırlık tarafındaki halat kuvveti  T2."""
    r, gn, a = t["r"], t["gn"], t["a"]
    return ((t["Mcwt"] + t["MCRcwt"]) * (gn + i[0] * a) / r
            + (t["MComp"] * gn) / (2.0 * r)
            + i[1] * t["MSRcwt"] * (gn + a * (r * r + 2) / 3.0)
            + i[2] * (t["iPDT"] * t["mPTD"] * a) / (2.0 * r)
            + i[3] * t["mDP"] * a / 2.0
            + i[4] * FRcwt / r)


#  Her yük durumunun terim işaretleri:  ( a , MSR , iPDT , mDP , FR )
#  EN 81-50 m.5.11.2'deki "±" işaretleri duruma göre değişir; Excel'in
#  11!D235…AF283 satırlarından birebir alınmıştır.
ISARETLER = {
    "yukleme":  {"T1": (+1, +1, +1, +1, +1), "T2": (+1, +1, +1, +1, +1)},
    "fren_alt": {"T1": (-1, +1, +1, +1, -1), "T2": (+1, +1, +1, -1, -1)},
    "fren_ust": {"T1": (+1, +1, +1, -1, +1), "T2": (-1, +1, +1, +1, -1)},
    "bloke":    {"T1": (+1, +1, +1, +1, +1), "T2": (+1, +1, +1, +1, +1)},
}

#  Sürtünme direnci FRcar / FRcwt, T1 / T2'nin sürtünmesiz kısmından türetilir
#  ( Askı Tipleri!P128-P129 · Q128-Q129 ).  Kullanılan işaretler T1 / T2'nin
#  kendi işaretlerinden FARKLIDIR — bu yüzden ayrı tablodur.
FR_ISARET = {
    "fren_alt": {"T1": (-1, +1, 0, 0, 0), "T2": (+1, -1, 0, 0, 0)},
    "fren_ust": {"T1": (+1, +1, -1, +1, 0), "T2": (-1, +1, +1, +1, 0)},
}


def _tahrik(g, o):
    S = SABIT
    Ra = g["halat_arasi"]
    C, D = g["sap_kasnak_yuk"], g["makine_yatak_yuk"]
    R1 = g["tahrik_kasnak_capi"] / 2.0
    H = g["sase_yuksekligi"]
    v = o["v"]

    #  Sarılma açısı
    A_yatay = Ra - 2 * R1
    B_dusey = H - C + D
    theta = math.atan2(A_yatay, B_dusey)
    alfa_derece = 180 - math.degrees(theta)
    alfa = math.radians(alfa_derece)

    #  Sürtünme katsayısı kabulleri  ( EN 81-50 m.5.11.2.3.2 )
    #  Acil frenlemedeki μ HALAT hızına bağlıdır;  palangalı sistemde halat
    #  kabinden askı oranı katı hızlı gider.  ( Kaynak Excel kabin hızını
    #  koyar — bkz. EXCEL_FARKLARI. )
    v_halat = v * o["r"]
    mu_yuk = S["mu_yukleme"]
    mu_fren = S["mu_yukleme"] / (1 + v_halat / 10.0)
    mu_bloke = S["mu_bloke"]
    gama, beta = math.radians(S["kanal_acisi"]), math.radians(S["alt_kesilme"])
    sert = g["kanal_isleme"] == "Sertleştirilmiş"
    if sert:
        f_yuk = mu_yuk / math.sin(gama / 2.0)
        f_fren = mu_fren / math.sin(gama / 2.0)
    else:
        pay = 4 * (1 - math.sin(beta / 2.0))
        payda = math.pi - beta - math.sin(beta)
        f_yuk = mu_yuk * pay / payda
        f_fren = mu_fren * pay / payda
    f_bloke = mu_bloke / math.sin(gama / 2.0)

    _kay(o, U174=A_yatay, Z178=B_dusey, C184=math.degrees(theta),
         S184=alfa_derece, AA184=alfa, AS190=mu_fren, AE216=f_bloke)
    #  Excel her iki kanal işlemesinin f değerini de ayrı satırda tutar
    _kay(o, **{("AJ198" if sert else "AU206"): f_yuk,
               ("AL202" if sert else "AV211"): f_fren})

    b = Bolum("6 -  TAHRİK YETENEĞİNİN HESAPLANMASI",
              "TS EN 81-50 m.5.11.2  /  m.5.11.3")
    b["adimlar"] = [
        veri("Ra", "Halat arası ( ray merkezleri arası mesafe )", Ra, "mm",
             "GİRİŞ  ( " + g["agirlik_yeri"] + " ağırlık )"),
        veri("C", "Saptırma kasnağı milinin yerden yüksekliği", C, "mm", "GİRİŞ"),
        veri("D", "Tahrik kasnağı mili yatak yüksekliği", D, "mm", "GİRİŞ"),
        veri("R1", "Tahrik kasnağı yarıçapı", R1, "mm"),
        veri("H", "Makine şasesi yüksekliği", H, "mm", "GİRİŞ"),
        hesap("A = Ra − 2 × R1", f"{trn(Ra, 0)} − 2 × {trn(R1, 0)}", A_yatay, "mm"),
        hesap("B = H − C + D",
              f"{trn(H, 0)} − {trn(C, 0)} + {trn(D, 0)}", B_dusey, "mm"),
        hesap("θ = arctan( A / B )",
              f"arctan( {trn(A_yatay, 0)} / {trn(B_dusey, 0)} )",
              math.degrees(theta), "°"),
        hesap("α = 180° − θ", f"180 − {tr(math.degrees(theta))}", alfa_derece, "°"),
        metin("Sürtünme katsayısı μ kabulleri  ( TS EN 81-50 Şekil 8 ) :"),
        veri("μ", "Yükleme için", mu_yuk, "", "EN 81-50 Şekil 8"),
        veri("v halat", "Halat hızı  ( kabin hızı × askı oranı )", v_halat, "m/s"),
        hesap("μ = 0,1 / ( 1 + v_halat / 10 )",
              f"0,1 / ( 1 + {tr(v_halat)} / 10 )", mu_fren, "",
              "EN 81-50 m.5.11.2.3.2"),
        veri("μ", "Kabinin bloke edildiği durumlar için", mu_bloke, "",
             "EN 81-50 Şekil 8"),
        metin(f"Sürtünme faktörü f  —  kanal işleme : {g['kanal_isleme']} :"),
        veri("f", "Kabinin yüklenmesi", f_yuk, "", "EN 81-50 m.5.11.2.3", 4),
        veri("f", "Durdurma tertibatının çalışması", f_fren, "",
             "EN 81-50 m.5.11.2.3", 4),
        veri("f", "Kabinin bloke edilmesi", f_bloke, "", "EN 81-50 m.5.11.2.3", 4),
    ]

    #  Her yük durumunun Excel'deki T1 · T2 · oran · sınır hücreleri
    DURUM_HUCRE = {
        "yukleme":  ("AF235", "AJ240", "K242", "O242"),
        "fren_alt": ("AF250", "AJ255", "K257", "O257"),
        "fren_ust": ("AH264", "AF269", "K271", "O271"),
        "bloke":    ("AH278", "AF283", "K285", "O285"),
    }
    tumu_uygun = True
    for durum, baslik in YUK_DURUMLARI:
        t = _terimler(g, o, durum)
        im = ISARETLER[durum]
        if durum in FR_ISARET:
            fi = FR_ISARET[durum]
            FRcar = S["FRcar_katsayi"] * _T1(t, 0.0, fi["T1"])
            FRcwt = S["FRcwt_katsayi"] * _T2(t, 0.0, fi["T2"])
        else:
            FRcar = FRcwt = 0.0
        T1 = _T1(t, FRcar, im["T1"])
        T2 = _T2(t, FRcwt, im["T2"])
        if durum == "bloke":
            oran = T1 / T2 if T2 else None
            f_kul = f_bloke
            sinir = math.exp(f_kul * alfa)
            uygun = oran is not None and sinir <= oran
            metni = f"e^(f·α) = {tr(sinir)}  ≤  T1/T2 = {tr(oran)}"
        else:
            oran = _oran(T1, T2)
            f_kul = f_yuk if durum == "yukleme" else f_fren
            sinir = math.exp(f_kul * alfa)
            uygun = oran is not None and sinir >= oran
            metni = f"T1/T2 = {tr(oran)}  ≤  e^(f·α) = {tr(sinir)}"
        tumu_uygun = tumu_uygun and uygun
        h1, h2, h3, h4 = DURUM_HUCRE[durum]
        _kay(o, **{h1: T1, h2: T2, h3: oran, h4: sinir})
        b["adimlar"] += [
            metin(baslik + " :", vurgu=True),
            hesap("T1  ( kabin tarafı )", "EN 81-50 m.5.11.2", T1, "N"),
            hesap("T2  ( karşı ağırlık tarafı )", "EN 81-50 m.5.11.2", T2, "N"),
            hesap("T1 / T2", f"{tr(T1)} / {tr(T2)}"
                  if durum == "bloke" else "büyük / küçük", oran, "", ondalik=4),
            hesap("e^(f·α)", f"exp( {tr(f_kul)} × {tr(alfa_derece)}° )", sinir,
                  "", "EN 81-50 m.5.11.3", 4),
            kontrol(metni, uygun),
        ]

    b["sonuc"] = {"baslik": "KONTROL      dört yük durumunda tahrik yeteneği",
                  "metin": "UYGUNDUR." if tumu_uygun else "UYGUN DEĞİLDİR",
                  "uygun": bool(tumu_uygun)}
    return b


# =====================================================================
#  RAY HESABI ORTAK YARDIMCILARI
# =====================================================================
def _ray_ozellik(profil):
    """Bir ray profilinin hesaba giren bütün kesit değerleri."""
    d = {k: MT.ray(profil, k) for k in ("A", "Ix", "Iy", "Wx", "Wy", "ix", "c")}
    d["h1_b_f"] = MT.ray_geo(profil, "h1_b_f")
    d["h1_f"] = MT.ray_geo(profil, "h1_f")
    d["b"] = MT.ray_geo(profil, "b")        # paten balatası yarı genişliği
    return d


def _moment(F, l):
    """Eğilme momenti  M = 3 · F · l / 16   ( iki açıklıklı sürekli kiriş )."""
    return SABIT["moment_pay"] * F * l / SABIT["moment_bolen"]


def _flans(F, p, balata):
    """Flanş eğilme gerilmesi  —  TS EN 81-50 m.5.10.5, kaymalı patenler.

        σF = Fx · ( h1 − b − f ) · 6 / ( c² · ( ℓ + 2·( h1 − f ) ) )

    ℓ paten balatasının UZUNLUĞUDUR.  Kaynak Excel oraya 1 yazar ( ℓ harfi
    1 rakamı okunmuş görünüyor );  bu, gerilmeyi olduğundan büyük gösterir.
    """
    return F * (p["h1_b_f"] * 6) / (p["c"] ** 2 * (balata + 2 * p["h1_f"]))


def _balata_boyu(g, p):
    """Paten balata uzunluğu ℓ  ( mm ).

    Girilmemişse ray tablosundaki balata YARI genişliğinden türetilir:
    ℓ = 2·b, yani kare balata kabulü.  Balatalar genelde genişliğinden
    uzundur;  kare kabulü ℓ'yi küçük tutar ve σF'yi EMNİYETLİ tarafta
    ( büyük ) bırakır.  Kesin değer paten imalatçısından alınmalıdır.
    """
    d = g.get("paten_balata_boyu")
    if isinstance(d, (int, float)) and not isinstance(d, bool) and d > 0:
        return d, "GİRİŞ"
    return 2 * p["b"], "türetilen  ( 2 × balata yarı genişliği )"


def _sehim(F, l, I):
    """Sehim  δ = 0,7 · l³ · F / ( 48 · E · I )."""
    S = SABIT
    return S["sehim_katsayi"] * l ** 3 * F / (S["sehim_bolen"] * S["E"] * I)


def _burkulma_omega(l, ix, rm):
    """Narinlik ve ω  —  TS EN 81-50 m.5.10.3.

    ω RAY ÇELİĞİNİN çekme dayanımına da bağlıdır;  kaynak Excel'in tek
    tablosu yalnız Rm = 370 eğrisidir ( bkz. EXCEL_FARKLARI ).
    """
    lam = math.ceil(l / ix - 1e-9)
    return lam, MT.omega_en8150(lam, rm)


def _ray_satirlari(ad, F, l, W, I, adimlar):
    """Bir kuvvet için moment · gerilme satırlarını yazar, ( σ , δ ) döndürür."""
    M = _moment(F, l)
    sigma = M / W
    d = _sehim(F, l, I)
    adimlar.extend([
        hesap(f"{ad} = 3 × F × l / 16", f"3 × {tr(F)} × {trn(l, 0)} / 16",
              M, "N·mm", ondalik=0),
        hesap(f"σ({ad}) = M / W", f"{trn(M, 0)} / {trn(W, 0)}", sigma, "N/mm²"),
    ])
    return sigma, d


# =====================================================================
#  7 -  KABİN KILAVUZ RAYLARI     ( TS EN 81-50 m.C.2.1 / C.2.2 / C.2.3 )
# =====================================================================
def _kabin_raylari(g, o):
    S, gn = SABIT, SABIT["gn"]
    Q, P = o["Q"], o["P"]
    k1, k3 = o["k1"], S["k3"]
    prof = g["kabin_ray_profili"]
    p = _ray_ozellik(prof)
    n, h, l = g["kabin_ray_sayisi"], g["kabin_paten_arasi"], g["kabin_konsol_arasi"]
    W, D = g["kabin_genisligi"], g["kabin_derinligi"]

    ray_boyu = MG.toplam_ray_boyu(g)
    Mg = ray_boyu * MT.ray(prof, "Gr")
    MY = S["MY_kabin"]
    sperm_g = MT.sigma_perm_guvenlik(g["ray_celigi_rm"])
    sperm_n = MT.sigma_perm_normal(g["ray_celigi_rm"])
    dperm = S["dperm_kabin"]

    xc = (D / 2.0 + S["kabin_merkez_payi"]) - g["ray_kapi_arasi"]
    yc = 0.0
    xp = (g["kapi_agirligi"] * (D / 2.0 + g["kapi_mekanizma_payi"])) / P
    yp = xs = ys = 0.0
    xi, yi = g["ray_kapi_arasi"], g["kabin_kaciklik"]
    balata, balata_kaynak = _balata_boyu(g, p)
    Fs = ((S["Fs_alt"] if Q < S["Fs_sinir"] else S["Fs_ust"]) * gn * Q)

    #  Durum 1  ( x ekseni ) ve Durum 2  ( y ekseni ) yük merkezleri.
    #  TS EN 81-50 Ek C.2.1.1:  yük yalnız ilgili eksende Dx/8 ya da Dy/8
    #  kadar kaydırılır;  ÖTEKİ eksendeki moment kolu kabin merkezidir.
    #  ( Kaynak Excel Durum 2'de xQ'yu sabit 0 yazar — bkz. EXCEL_FARKLARI. )
    xQ1, yQ1 = xc + D / S["Dx_bolen"], yc
    xQ2, yQ2 = xc, yc + W / S["Dy_bolen"]

    b = Bolum("7 -  KABİN KILAVUZ RAYLARININ HESAPLANMASI",
              "TS EN 81-50 m.C.2.1 / C.2.2 / C.2.3")
    ad = [
        veri("h", "Patenler arası düşey mesafe", h, "mm", "GİRİŞ"),
        veri("l", "Ray konsolları arasındaki en uzun mesafe", l, "mm", "GİRİŞ"),
        veri("n", "Ray sayısı", n, "adet", "GİRİŞ", 0),
        veri("", "Ray profili", prof, "", "ISO 7465"),
        hesap("Mg = ray boyu × Gr", f"{tr(ray_boyu)} m × {tr(MT.ray(prof, 'Gr'))} kg/m",
              Mg, "kg"),
        veri("MY", "Raylara bağlı yardımcı donanım kütlesi", MY, "N", "Ofis kabulü", 0),
        veri("xc", "Kabin merkezinin x mesafesi", xc, "mm"),
        veri("yc", "Kabin merkezinin y mesafesi", yc, "mm"),
        veri("xp", "Boş kabin ağırlık merkezinin x mesafesi", xp, "mm"),
        veri("yp", "Boş kabin ağırlık merkezinin y mesafesi", yp, "mm"),
        veri("xs", "Askı noktasının x mesafesi", xs, "mm"),
        veri("ys", "Askı noktasının y mesafesi", ys, "mm"),
        veri("xi", "Kabin kapısının x mesafesi", xi, "mm"),
        veri("yi", "Kabin kapısının y mesafesi", yi, "mm"),
        veri("E", "Elastisite modülü", S["E"], "N/mm²", "Ofis kabulü", 0),
        hesap("Fs = 0,4 × gn × Q      ( Q < 2500 kg )" if Q < S["Fs_sinir"]
              else "Fs = 0,6 × gn × Q      ( Q ≥ 2500 kg )",
              f"{tr(S['Fs_alt'] if Q < S['Fs_sinir'] else S['Fs_ust'])} × "
              f"{tr(gn)} × {trn(Q, 0)}", Fs, "N", "EN 81-20 Çizelge 13"),
        veri("σperm", "Güv. tertibatı çalışmasında izin verilen gerilme", sperm_g,
             "N/mm²", f"EN 81-20 m.5.7.3.1  ·  Rm = {trn(g['ray_celigi_rm'], 0)}", 0),
        veri("σperm", "Normal kullanmada izin verilen gerilme", sperm_n, "N/mm²",
             "EN 81-20 m.5.7.3.1", 0),
        veri("δperm", "İzin verilen en büyük eğilme miktarı", dperm, "mm",
             "EN 81-20 m.5.7.4.6", 0),
        veri("ℓ", "Paten balatasının uzunluğu", balata, "mm", balata_kaynak, 0),
        hesap("Durum 1 :  xQ = xc + D / 8",
              f"{tr(xc)} + {trn(D, 0)} / 8", xQ1, "mm"),
        hesap("Durum 2 :  yQ = yc + W / 8",
              f"{tr(yc)} + {trn(W, 0)} / 8", yQ2, "mm"),
    ]

    uygunlar = []

    def _kesim(baslik, kaynak, Fx1, Fy1, Fx2, Fy2, kk, sperm, omega=None,
               hucre=()):
        """Bir yükleme durumu için gerilme · burkulma · flanş · sehim satırları.

        hucre  her durum için  ( Fx, σx, Fy, σy, σm, σc, σ, σF, δx, δy )
               Excel adresleri;  boş dize atlanır.
        """
        ad.append(metin(baslik, vurgu=True))
        sonuc = []
        for sira, (etiket, Fx, Fy) in enumerate(
                (("Durum 1  x-ekseni", Fx1, Fy1), ("Durum 2  y-ekseni", Fx2, Fy2))):
            h = hucre[sira] if sira < len(hucre) else ()
            ad.append(metin(etiket + " :"))
            ad.append(hesap("Fx", kaynak, Fx, "N"))
            ad.append(hesap("Fy", kaynak, Fy, "N"))
            sx, dx = _ray_satirlari("Mx", Fx, l, p["Wy"], p["Iy"], ad)
            sy, dy = _ray_satirlari("My", Fy, l, p["Wx"], p["Ix"], ad)
            sm = sx + sy
            sc = (kk["Fv"] + kk["k"] * MY) / p["A"] + sm
            ad.append(hesap("σm = σ(My) + σ(Mx)", f"{tr(sy)} + {tr(sx)}", sm, "N/mm²"))
            ad.append(kontrol(f"σm = {tr(sm)}  ≤  σperm = {trn(sperm, 0)} N/mm²",
                              sm <= sperm))
            ad.append(hesap("σc = ( Fv + k × MY ) / A + σm",
                            f"( {tr(kk['Fv'])} + {tr(kk['k'])} × {trn(MY, 0)} ) / "
                            f"{trn(p['A'], 0)} + {tr(sm)}", sc, "N/mm²"))
            ad.append(kontrol(f"σc = {tr(sc)}  ≤  σperm = {trn(sperm, 0)} N/mm²",
                              sc <= sperm))
            sonuc += [sm <= sperm, sc <= sperm]
            if omega is not None:
                st = kk["sigma_k"] + S["birlesik_katsayi"] * sm
                ad.append(hesap("σ = σk + 0,9 × σm",
                                f"{tr(kk['sigma_k'])} + 0,9 × {tr(sm)}", st, "N/mm²"))
                ad.append(kontrol(f"σ = {tr(st)}  ≤  σperm = {trn(sperm, 0)} N/mm²",
                                  st <= sperm))
                sonuc.append(st <= sperm)
            sf = _flans(Fx, p, balata)
            ad.append(hesap("σF = Fx × ( h1−b−f ) × 6 / ( c² × ( ℓ + 2 × ( h1−f ) ) )",
                            f"{tr(Fx)} × {tr(p['h1_b_f'] * 6)} / "
                            f"{tr(p['c'] ** 2 * (balata + 2 * p['h1_f']))}",
                            sf, "N/mm²", "EN 81-50 m.5.10.5"))
            ad.append(kontrol(f"σF = {tr(sf)}  ≤  σperm = {trn(sperm, 0)} N/mm²",
                              sf <= sperm))
            ad.append(hesap("δx = 0,7 × l³ × Fx / ( 48 × E × Iy )",
                            f"l = {trn(l, 0)} mm ,  Iy = {trn(p['Iy'], 0)} mm⁴",
                            dx, "mm"))
            ad.append(kontrol(f"δx = {tr(dx)}  ≤  δperm = {trn(dperm, 0)} mm",
                              dx <= dperm))
            ad.append(hesap("δy = 0,7 × l³ × Fy / ( 48 × E × Ix )",
                            f"l = {trn(l, 0)} mm ,  Ix = {trn(p['Ix'], 0)} mm⁴",
                            dy, "mm"))
            ad.append(kontrol(f"δy = {tr(dy)}  ≤  δperm = {trn(dperm, 0)} mm",
                              dy <= dperm))
            sonuc += [sf <= sperm, dx <= dperm, dy <= dperm]
            if h:
                st_v = kk["sigma_k"] + S["birlesik_katsayi"] * sm if omega else None
                for adres, deger in zip(h, (Fx, sx, Fy, sy, sm, sc, st_v,
                                            sf, dx, dy)):
                    if adres:
                        _kay(o, **{adres: deger})
        uygunlar.extend(sonuc)

    # ── C.2.1  Güvenlik tertibatının çalışması ────────────────────────
    Fk = k1 * gn * (P + Q) / n + Mg * gn
    lam, omega = _burkulma_omega(l, p["ix"], g["ray_celigi_rm"])
    #  MY çarpanı burada da k3'tür ( 11!W354 = 1,2 ) — güvenlik tertibatı
    #  durumunda bile yardımcı donanım normal kullanma katsayısıyla alınır.
    sigma_k = (Fk + k3 * MY) * omega / p["A"]
    ad += [
        metin("Güvenlik Tertibatının Çalışması  ( TS EN 81-50 m.C.2.1 ) :", vurgu=True),
        hesap("Fk = k1 × gn × ( P + Q ) / n + Mg × gn",
              f"{tr(k1)} × {tr(gn)} × ( {trn(P, 0)} + {trn(Q, 0)} ) / {trn(n, 0)} "
              f"+ {tr(Mg)} × {tr(gn)}", Fk, "N"),
        hesap("λ = l / ix", f"{trn(l, 0)} / {tr(p['ix'])}", l / p["ix"], ""),
        veri("λ", "Yuvarlanmış burkulma narinliği", lam, "", "11!AV355", 0),
        veri("ω", "Omega değeri", omega, "",
             f"EN 81-50 m.5.10.3  ·  λ = {lam}  ·  Rm = {trn(g['ray_celigi_rm'], 0)}", 6),
        hesap("σk = ( Fk + k3 × MY ) × ω / A",
              f"( {tr(Fk)} + {tr(k3)} × {trn(MY, 0)} ) × {tr(omega)} / {trn(p['A'], 0)}",
              sigma_k, "N/mm²"),
        kontrol(f"σk = {tr(sigma_k)}  ≤  σperm = {trn(sperm_g, 0)} N/mm²",
                sigma_k <= sperm_g),
    ]
    uygunlar.append(sigma_k <= sperm_g)
    _kesim("Eğilme gerilmesi  ( C.2.1 ) :", "k1 × gn × ( Q·xQ + P·xp ) / ( n × h )",
           k1 * gn * (Q * xQ1 + P * xp) / (n * h),
           k1 * gn * (Q * yQ1 + P * yp) / ((n / 2.0) * h),
           k1 * gn * (Q * xQ2 + P * xp) / (n * h),
           k1 * gn * (Q * yQ2 + P * yp) / ((n / 2.0) * h),
           {"Fv": Fk, "k": k3, "sigma_k": sigma_k}, sperm_g, omega,
           (("AY321", "AU324", "AY327", "AU330", "Z360", "AJ362", "AE365",
             "Z379", "AH393", "AH396"),
            ("AY335", "AU338", "K344", "AU347", "Z369", "AJ371", "AE374",
             "Z384", "AH401", "AH404")))

    # ── C.2.2  Normal çalışma, işletme ────────────────────────────────
    Fv = Mg * gn
    sigma_v = (Fv + k3 * MY) / p["A"]
    ad += [
        metin("Normal Çalışma, İşletme  ( TS EN 81-50 m.C.2.2 ) :", vurgu=True),
        hesap("Fv = Mg × gn", f"{tr(Mg)} × {tr(gn)}", Fv, "N"),
        hesap("σv = ( Fv + k3 × MY ) / A",
              f"( {tr(Fv)} + {tr(k3)} × {trn(MY, 0)} ) / {trn(p['A'], 0)}",
              sigma_v, "N/mm²"),
        kontrol(f"σv = {tr(sigma_v)}  ≤  σperm = {trn(sperm_n, 0)} N/mm²",
                sigma_v <= sperm_n),
    ]
    uygunlar.append(sigma_v <= sperm_n)
    _kesim("Eğilme gerilmesi  ( C.2.2 ) :",
           "k3 × gn × ( Q·(xQ−xs) + P·(xp−xs) ) / ( n × h )",
           k3 * gn * (Q * (xQ1 - xs) + P * (xp - xs)) / (n * h),
           k3 * gn * (Q * (yQ1 - ys) + P * (yp - ys)) / (n * h),
           k3 * gn * (Q * (xQ2 - xs) + P * (xp - xs)) / (n * h),
           k3 * gn * (Q * (yQ2 - ys) + P * (yp - ys)) / (n * h),
           {"Fv": Fv, "k": k3}, sperm_n, None,
           (("L415", "AU418", "L424", "AU427", "Z461", "AC463", "",
             "Z476", "AH487", "AH490"),
            ("L435", "AU438", "L444", "AU447", "Z468", "AH470", "",
             "Z481", "AH495", "AH498")))

    # ── C.2.3  Normal çalışma, yükleme ────────────────────────────────
    Fx3 = (gn * P * (xp - xs) + Fs * (xi - xs)) / (n * h)
    Fy3 = (gn * P * (yp - ys) + Fs * (yi - ys)) / (n * h)
    ad.append(metin("Normal Çalışma, Yükleme  ( TS EN 81-50 m.C.2.3 ) :", vurgu=True))
    ad.append(hesap("Fx = ( gn × P × (xp−xs) + Fs × (xi−xs) ) / ( n × h )",
                    f"( {tr(gn)} × {trn(P, 0)} × {tr(xp - xs)} + {tr(Fs)} × "
                    f"{tr(xi - xs)} ) / ( {trn(n, 0)} × {trn(h, 0)} )", Fx3, "N"))
    ad.append(hesap("Fy = ( gn × P × (yp−ys) + Fs × (yi−ys) ) / ( n × h )",
                    f"( {tr(gn)} × {trn(P, 0)} × {tr(yp - ys)} + {tr(Fs)} × "
                    f"{tr(yi - ys)} ) / ( {trn(n, 0)} × {trn(h, 0)} )", Fy3, "N"))
    sx3, dx3 = _ray_satirlari("Mx", Fx3, l, p["Wy"], p["Iy"], ad)
    sy3, dy3 = _ray_satirlari("My", Fy3, l, p["Wx"], p["Ix"], ad)
    sm3 = sx3 + sy3
    sc3 = (Fv + k3 * MY) / p["A"] + sm3
    sf3 = _flans(Fx3, p, balata)
    ad += [
        hesap("σm = σ(My) + σ(Mx)", f"{tr(sy3)} + {tr(sx3)}", sm3, "N/mm²"),
        kontrol(f"σm = {tr(sm3)}  ≤  σperm = {trn(sperm_n, 0)} N/mm²", sm3 <= sperm_n),
        hesap("σc = ( Fv + k3 × MY ) / A + σm", f"σv + σm", sc3, "N/mm²"),
        kontrol(f"σc = {tr(sc3)}  ≤  σperm = {trn(sperm_n, 0)} N/mm²", sc3 <= sperm_n),
        hesap("σF  ( flanş eğilmesi )", f"Fx = {tr(Fx3)} N", sf3, "N/mm²"),
        kontrol(f"σF = {tr(sf3)}  ≤  σperm = {trn(sperm_n, 0)} N/mm²", sf3 <= sperm_n),
        hesap("δx", f"Iy = {trn(p['Iy'], 0)} mm⁴", dx3, "mm"),
        kontrol(f"δx = {tr(dx3)}  ≤  δperm = {trn(dperm, 0)} mm", dx3 <= dperm),
        hesap("δy", f"Ix = {trn(p['Ix'], 0)} mm⁴", dy3, "mm"),
        kontrol(f"δy = {tr(dy3)}  ≤  δperm = {trn(dperm, 0)} mm", dy3 <= dperm),
    ]
    uygunlar += [sm3 <= sperm_n, sc3 <= sperm_n, sf3 <= sperm_n,
                 dx3 <= dperm, dy3 <= dperm]

    _kay(o, AH291=Mg, AH293=xc, AH295=xp, AH299=xi, AH300=yi, AH303=Fs,
         AH304=sperm_g, AH305=sperm_n, Z309=xQ1, Z312=yQ2,
         AU351=Fk, AV354=l / p["ix"], AV355=lam, AD354=omega, AL354=sigma_k,
         AE452=Fv, AL455=sigma_v,
         L508=Fx3, AU511=sx3, L516=Fy3, AU519=sy3, Z530=sm3, AF532=sc3,
         Z537=sf3, AH542=dx3, AH545=dy3)
    o.update(Fk_kabin=Fk, Mg_kabin=Mg, ray_boyu=ray_boyu)
    b["adimlar"] = ad
    hepsi = all(uygunlar)
    b["sonuc"] = {"baslik": "KONTROL      σm · σc · σF ≤ σperm   ve   δ ≤ δperm",
                  "metin": "UYGUNDUR." if hepsi
                           else "UYGUN DEĞİLDİR — ray profilini büyütün ya da "
                                "konsol aralığını küçültün",
                  "uygun": bool(hepsi)}
    b["aciklamalar"] = [
        "Durum 1 yükü x ekseninde Dx/8, Durum 2 y ekseninde Dy/8 kadar "
        "kaydırır ( TS EN 81-50 Ek C.2.1.1 ); öteki eksendeki moment kolu her "
        "iki durumda da kabin merkezidir. Kaynak Excel Durum 2'de xQ'yu sabit "
        "0 yazar — standart uygulanmıştır.",
        "Flanş eğilmesinde ℓ paten balatasının uzunluğudur ( EN 81-50 "
        "m.5.10.5 ). Girilmezse ray tablosundaki balata yarı genişliğinden "
        "2·b olarak türetilir; kesin değer paten imalatçısından alınmalıdır."]
    return b


# =====================================================================
#  8 -  KARŞI AĞIRLIK KILAVUZ RAYLARI              ( TS EN 81-50 m.5.10 )
# =====================================================================
def _agirlik_raylari(g, o):
    S, gn = SABIT, SABIT["gn"]
    k3 = S["k3"]
    prof = g["agirlik_ray_profili"]
    p = _ray_ozellik(prof)
    n = g["agirlik_ray_sayisi"]
    h, l = g["agirlik_paten_arasi"], g["agirlik_konsol_arasi"]
    Mcwt = g["karsi_agirlik"]
    MY = S["MY_agirlik"]
    sperm = MT.sigma_perm_normal(g["ray_celigi_rm"])
    dperm = S["dperm_agirlik"]

    derinlik = MT.agirlik_derinlik(g["agirlik_malzemesi"])
    genislik = MT.agirlik_genisligi(g["agirlik_ray_arasi"])
    Dxa = S["Dxa_katsayi"] * derinlik
    Dya = S["Dya_katsayi"] * genislik
    xsa = ysa = 0.0

    Mg = o["ray_boyu"] * MT.ray(prof, "Gr")
    Fx = (k3 * gn * Mcwt * (Dxa - xsa)) / (n * h)
    Fy = (k3 * gn * Mcwt * (Dya - ysa)) / (n * h)
    Mx, My = _moment(Fx, l), _moment(Fy, l)
    sx, sy = Mx / p["Wy"], My / p["Wx"]
    sm = sx + sy
    Fv = Mg * gn
    sv = (Fv + k3 * MY) / p["A"]
    sc = sv + sm
    balata, balata_kaynak = _balata_boyu(g, p)
    sf = _flans(Fx, p, balata)
    dx, dy = _sehim(Fx, l, p["Iy"]), _sehim(Fy, l, p["Ix"])
    kontroller = [sm <= sperm, sc <= sperm, sf <= sperm, dx <= dperm, dy <= dperm]

    b = Bolum("8 -  KARŞI AĞIRLIK KILAVUZ RAYLARININ HESAPLANMASI",
              "TS EN 81-50 m.5.10  /  m.C.2.2")
    b["adimlar"] = [
        veri("", "Ray profili", prof, "", "ISO 7465"),
        veri("n", "Ağırlık rayı sayısı", n, "adet", "GİRİŞ", 0),
        veri("h", "Ağırlık paten arası", h, "mm", "GİRİŞ"),
        veri("l", "Ağırlık rayı konsollar arası en uzun mesafe", l, "mm", "GİRİŞ"),
        veri("Mcwt", "Karşı ağırlık kütlesi", Mcwt, "kg"),
        veri("", "Karşı ağırlık malzemesi", g["agirlik_malzemesi"]),
        veri("", "Karşı ağırlık derinliği", derinlik, "mm",
             f"Ağırlık malzemesi tablosu  ·  {g['agirlik_malzemesi']}", 0),
        veri("", "Karşı ağırlık genişliği", genislik, "mm",
             f"Ray arası {trn(g['agirlik_ray_arasi'], 0)} mm karşılığı", 0),
        hesap("Dxa = 0,1 × ağırlık derinliği",
              f"0,1 × {trn(derinlik, 0)}", Dxa, "mm"),
        hesap("Dya = 0,05 × ağırlık genişliği",
              f"0,05 × {trn(genislik, 0)}   ( ray arası {trn(g['agirlik_ray_arasi'], 0)} mm )",
              Dya, "mm"),
        veri("xsa", "Askı noktasının x mesafesi", xsa, "mm"),
        veri("ysa", "Askı noktasının y mesafesi", ysa, "mm"),
        veri("MY", "Raylara bağlı yardımcı donanım", MY, "N", "Ofis kabulü", 0),
        veri("ℓ", "Paten balatasının uzunluğu", balata, "mm", balata_kaynak, 0),
        hesap("Mg = ray boyu × Gr",
              f"{tr(o['ray_boyu'])} m × {tr(MT.ray(prof, 'Gr'))} kg/m", Mg, "kg"),
        metin("Eğilme gerilmesi  ( TS EN 81-50 m.C.2.2 ) :", vurgu=True),
        hesap("Fx = k3 × gn × Mcwt × ( Dxa − xsa ) / ( n × h )",
              f"{tr(k3)} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dxa)} / "
              f"( {trn(n, 0)} × {trn(h, 0)} )", Fx, "N"),
        hesap("Fy = k3 × gn × Mcwt × ( Dya − ysa ) / ( n × h )",
              f"{tr(k3)} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dya)} / "
              f"( {trn(n, 0)} × {trn(h, 0)} )", Fy, "N"),
        hesap("Mx = 3 × Fx × l / 16", f"3 × {tr(Fx)} × {trn(l, 0)} / 16", Mx,
              "N·mm", ondalik=0),
        hesap("σ(Mx) = Mx / Wy", f"{trn(Mx, 0)} / {trn(p['Wy'], 0)}", sx, "N/mm²"),
        hesap("My = 3 × Fy × l / 16", f"3 × {tr(Fy)} × {trn(l, 0)} / 16", My,
              "N·mm", ondalik=0),
        hesap("σ(My) = My / Wx", f"{trn(My, 0)} / {trn(p['Wx'], 0)}", sy, "N/mm²"),
        metin("Burkulma :"),
        hesap("Fv = Mg × gn", f"{tr(Mg)} × {tr(gn)}", Fv, "N"),
        hesap("σv = ( Fv + k3 × MY ) / A",
              f"( {tr(Fv)} + {tr(k3)} × {trn(MY, 0)} ) / {trn(p['A'], 0)}", sv, "N/mm²"),
        metin("Birleşik gerilme :"),
        hesap("σm = σ(Mx) + σ(My)", f"{tr(sx)} + {tr(sy)}", sm, "N/mm²"),
        kontrol(f"σm = {tr(sm)}  ≤  σperm = {trn(sperm, 0)} N/mm²", sm <= sperm),
        hesap("σc = σv + σm", f"{tr(sv)} + {tr(sm)}", sc, "N/mm²"),
        kontrol(f"σc = {tr(sc)}  ≤  σperm = {trn(sperm, 0)} N/mm²", sc <= sperm),
        metin("Flanş eğilmesi :"),
        hesap("σF = Fx × ( h1−b−f ) × 6 / ( c² × ( 1 + 2 × h1−f ) )",
              f"Fx = {tr(Fx)} N", sf, "N/mm²"),
        kontrol(f"σF = {tr(sf)}  ≤  σperm = {trn(sperm, 0)} N/mm²", sf <= sperm),
        metin("Sehim miktarları :"),
        hesap("δx = 0,7 × l³ × Fx / ( 48 × E × Iy )",
              f"Iy = {trn(p['Iy'], 0)} mm⁴", dx, "mm"),
        kontrol(f"δx = {tr(dx)}  ≤  δperm = {trn(dperm, 0)} mm", dx <= dperm),
        hesap("δy = 0,7 × l³ × Fy / ( 48 × E × Ix )",
              f"Ix = {trn(p['Ix'], 0)} mm⁴", dy, "mm"),
        kontrol(f"δy = {tr(dy)}  ≤  δperm = {trn(dperm, 0)} mm", dy <= dperm),
    ]
    b["sonuc"] = {"baslik": "KONTROL      σm · σc · σF ≤ σperm   ve   δ ≤ δperm",
                  "metin": "UYGUNDUR." if all(kontroller)
                           else "UYGUN DEĞİLDİR — ağırlık rayı profilini büyütün",
                  "uygun": bool(all(kontroller))}
    b["aciklamalar"] = [
        "KAYNAK EXCEL'DEN AYRILAN NOKTA:  Excel σ(My) için de Wy'yi kullanır "
        "( 11!AU575 ). y yönündeki kuvvet rayı x ekseni etrafında eğer, bu "
        "yüzden Wx doğrudur — Excel'in sehim satırı da zaten Ix kullanır. "
        "Burada Wx alındı; Excel'in değeri daha büyük ( emniyetli ama yanlış ) "
        "çıkar."]
    _kay(o, AH550=derinlik, AH551=genislik, N562=Dxa, AL562=Dya, AH554=Mg,
         AP566=Fx, AU569=sx, AP572=Fy, AU575=sy, AE580=Fv, AL583=sv,
         Z588=sm, AF590=sc, Z595=sf, AH600=dx, AH603=dy)
    o.update(Mg_agirlik=Mg)
    return b


# =====================================================================
#  9 -  KUYU TABANINA GELEN YÜKLER            ( TS EN 81-20 m.5.2.1.8 )
# =====================================================================
def _kuyu_tabani(g, o):
    S, gn = SABIT, SABIT["gn"]
    Q, P = o["Q"], o["P"]
    LR = o["ray_boyu"] * 1000.0                      # mm
    Gr_k = MT.ray(g["kabin_ray_profili"], "Gr")
    Gr_a = MT.ray(g["agirlik_ray_profili"], "Gr")
    FKR = (gn * Gr_k * LR / 1000.0) + S["MY_kabin"] + o["Fk_kabin"]
    FAR = (gn * Gr_a * LR / 1000.0) + S["MY_agirlik"]
    Fkt = S["tampon_katsayi"] * gn * (P + Q)
    Fat = S["tampon_katsayi"] * gn * (P + S["q_denge"] * Q)

    b = Bolum("9 -  KUYU TABANINA GELEN YÜKLERİN HESAPLANMASI",
              "TS EN 81-20 m.5.2.1.8")
    b["adimlar"] = [
        veri("LR", "Kılavuz ray boyu", LR, "mm", "Σ durak + kaide − 200 + kuyu dibi − 300", 0),
        metin("Kabin raylarına gelen kuvvetler :"),
        hesap("FKR = gn × Gr × LR / 1000 + MY + Fk",
              f"{tr(gn)} × {tr(Gr_k)} × {trn(LR, 0)} / 1000 + "
              f"{trn(S['MY_kabin'], 0)} + {tr(o['Fk_kabin'])}", FKR, "N"),
        metin("Ağırlık raylarına gelen kuvvetler :"),
        hesap("FAR = gn × Gar × Lar / 1000 + Ma",
              f"{tr(gn)} × {tr(Gr_a)} × {trn(LR, 0)} / 1000 + "
              f"{trn(S['MY_agirlik'], 0)}", FAR, "N"),
        metin("Kabin tamponlarına gelen kuvvetler :"),
        hesap("Fkt = 4 × gn × ( P + Q )",
              f"4 × {tr(gn)} × ( {trn(P, 0)} + {trn(Q, 0)} )", Fkt, "N"),
        metin("Ağırlık tamponlarına gelen kuvvetler :"),
        hesap("Fat = 4 × gn × ( P + q × Q )",
              f"4 × {tr(gn)} × ( {trn(P, 0)} + {tr(S['q_denge'])} × {trn(Q, 0)} )",
              Fat, "N"),
    ]
    b["notlar"] = [
        "Bu kuvvetler kuyu alt boşluğu tabanının ( temel / döşeme ) statik "
        "hesabına girer; inşaat projesine bildirilmelidir."]
    b["sonuc"] = {"baslik": "KUYU TABANI YÜKLERİ",
                  "metin": f"FKR = {tr(FKR)} N  ·  FAR = {tr(FAR)} N  ·  "
                           f"Fkt = {tr(Fkt)} N  ·  Fat = {tr(Fat)} N",
                  "uygun": None}
    _kay(o, AH611=LR, AX611=FKR, AN616=FAR, AF621=Fkt, AI627=Fat)
    o.update(FKR=FKR, FAR=FAR, Fkt=Fkt, Fat=Fat)
    return b


# =====================================================================
# 10 -  SIĞINMA ALANLARI VE AÇIKLIKLAR  ( EN 81-20 m.5.2.5.7 / 5.2.5.8 )
# =====================================================================
def _siginma(g, o):
    K, v = SIGINMA, o["v"]
    SK = g["son_kat_yuksekligi"]
    W, D = g["kabin_genisligi"], g["kabin_derinligi"]
    bosluk = _bosluk(v)

    #  Kabin tam kapanmış tampon üzerinde otururken kabinin altındaki yığın
    yigin = (g["kabin_paten_arasi"] + g["kabin_carpma_arasi"]
             + g["kabin_tampon_boyu"] - g["kabin_tampon_ezilme"]
             + g["kabin_tampon_baba"])
    #  Ç.2  —  cebirsel olarak  ( son kat yüksekliği − ağırlık paten arası )
    c2_agirlik = (g["kuyu_boyu"] - yigin
                  - (g["agirlik_paten_arasi"]
                     + (g["kuyu_boyu"] - SK - yigin)))
    #  Kuyu tabanı ile kabinin en alt kısmı arası
    a_dip = g["kabin_tampon_baba"] + (g["kabin_tampon_boyu"] - g["kabin_tampon_ezilme"])

    #  Excel'deki "HESAPLANAN" sütunu  ( 11!AI635 … AI648 )
    HUCRE = ("AI635", "AI636", "AI637", "AI638", "AI640",
             "AI645", "AI646", "AI647", "AI648")
    satir = [
        ("b - Üst paten / rayın üst ucu arası",
         K["min_ust_paten"], SK - K["kabin_yuksekligi"] - K["paten_payi"] - K["tavan_payi"]),
        #  m.5.2.5.7.3 — sınır, seçilen sığınma hacminin yüksekliğidir;
        #  ikisi ayrışmasın diye tek yerden okunur.
        ("c.2 - Kabin üstü / kuyu tavanının en alt kısmı arası",
         K["ust_hacim"][2] * 1000, SK - K["kabin_ust_donanim"] - K["tavan_payi"]),
        ("a - Revizyon kutusu / kuyu tavanının en alt kısmı arası",
         K["min_revizyon"],
         SK - K["kabin_ust_donanim"] - K["revizyon_payi"] - K["tavan_payi"]),
        ("b - Paten / halat bağlantısı - kuyu tavanı arası",
         bosluk, SK - K["kabin_ust_donanim"] - K["revizyon_payi"]
         - K["paten_payi"] - K["tavan_payi"]),
        ("Ç.2 - Karşı ağırlık üst pateni / rayın üst ucu arası",
         bosluk, c2_agirlik),
        ("a - Kuyu tabanı / kabinin en alt kısımları arası",
         K["min_kuyu_tabani"], a_dip),
        ("a.1 - Kuyu tabanı / kabin eteği arası",
         K["min_etek"], a_dip + K["etek_payi"] - K["etek_kotu"]),
        ("a.2 - Kılavuz raylar / kabinin en alt kısmı arası",
         K["min_ray_alt"], a_dip - g["kabin_tampon_baba"] + K["ray_alt_payi"]),
        ("b - Regülatör alt makarası / kabin en alt kısmı arası",
         K["min_regulator"], a_dip - K["regulator_payi"]),
    ]
    ad = [veri("", "En üst durak ( son kat ) yüksekliği", SK, "mm", "GİRİŞ", 0),
          hesap("Serbest boşluk = ( 0,1 + 0,035 × v² ) × 1000",
                f"( 0,1 + 0,035 × {tr(v)}² ) × 1000", bosluk, "mm",
                "TS EN 81-20 Çiz.2 + m.5.2.5.6.2"),
          metin("Kabin tavanı üzerindeki sığınma alanları  ( m.5.2.5.7 ) :",
                vurgu=True)]
    _kay(o, AD638=bosluk)
    uygunlar = []
    for i, (etiket, asgari, hesaplanan) in enumerate(satir):
        _kay(o, **{HUCRE[i]: hesaplanan})
        if i == 5:
            ad.append(metin("Kuyu boşluğundaki sığınma alanları  ( m.5.2.5.8 ) :",
                            vurgu=True))
        #  Standart "en az" der:  sınıra eşit ölçü de uygundur.
        uygun = hesaplanan >= asgari
        uygunlar.append(uygun)
        ad.append(veri("", etiket + "  ( en az " + trn(asgari, 0) + " mm )",
                       hesaplanan, "mm", "", 0))
        ad.append(kontrol(f"{trn(hesaplanan, 0)} mm  ≥  {trn(asgari, 0)} mm", uygun))

    #  Sığınma hacimleri  ( EN 81-20 Çizelge 3 — çömelmiş duruş )
    ust_h = (SK - K["kabin_ust_donanim"] - K["tavan_payi"]) / 1000.0
    for etiket, (a, bb, c), olcu in (
            ("Ç.3 - Kabin üstünde sığınma hacmi",
             K["ust_hacim"], ((W + 40) / 1000.0, (D + 20) / 1000.0, ust_h)),
            ("Ç.4 - Kuyu dibinde sığınma hacmi",
             K["dip_hacim"], (W / 1000.0, D / 1000.0, a_dip / 1000.0))):
        uygun = a <= olcu[0] and bb <= olcu[1] and c <= olcu[2]
        uygunlar.append(uygun)
        ad.append(veri("", f"{etiket}  ( en az {tr(a)} × {tr(bb)} × {tr(c)} m )",
                       f"{tr(olcu[0])} × {tr(olcu[1])} × {tr(olcu[2])} m"))
        ad.append(kontrol(etiket, uygun))

    b = Bolum("10 -  SIĞINMA ALANLARI VE AÇIKLIKLARIN UYGUNLUĞU",
              "TS EN 81-20 m.5.2.5.7  /  m.5.2.5.8")
    b["adimlar"] = ad
    b["sonuc"] = {"baslik": "KONTROL      bütün sığınma ölçüleri",
                  "metin": "UYGUNDUR." if all(uygunlar)
                           else "UYGUN DEĞİLDİR — kuyu üst/alt boşluğunu artırın",
                  "uygun": bool(all(uygunlar))}
    b["aciklamalar"] = [
        "Kabin gövde yükseklikleri, etek ve revizyon kutusu payları ( 2400 · "
        "2100 · 500 · 400 · 950 · 270 · 150 mm ) kaynak Excel'in kabulleridir; "
        "TS EN 81-20 sayısı değildir. Farklı kabin imalatında SIGINMA "
        "sözlüğünden güncellenmelidir.",
        "Buna karşılık asgari açıklıklar ( 100 · 1000 · 500 · 500 · 100 · "
        "100 · 300 mm ) doğrudan TS EN 81-20 m.5.2.5.7 ve m.5.2.5.8'dendir. "
        "Ray dibi açıklığı, parça raya yatay XH ≤ 0,15 m uzaklıkta olduğu "
        "kabulüyle Şekil 7'den 0,10 m alınır; daha uzaktaki parçalar için "
        "sınır 0,30 m ( XH = 0,30 ) ve 0,50 m ( XH ≥ 0,50 ) olur.",
        "Serbest boşluğa eklenen 0,035 × v² terimi TS EN 81-20'de açıklığın "
        "değil, kabinin EN ÜST KONUMUNUN tanımındadır ( Çizelge 2 ). Burada "
        "kuyu ölçüleri anma konumundan alındığı için aynı eşitsizlik, terim "
        "sınıra eklenerek yazılmıştır — cebirsel olarak birebir aynıdır."]
    return b


# =====================================================================
#  GİRİŞ NOKTASI
# =====================================================================
BOLUM_URETICILERI = (_motor, _makine, _kabin_alani, _aski_halatlari, _regulator,
                     _tahrik, _kabin_raylari, _agirlik_raylari, _kuyu_tabani,
                     _siginma)


def hesapla(veriler=None):
    """Mukavemet hesabının tamamı.

    veriler   girdi sözlüğü ( engine.mukavemet_girdi.ALANLAR anahtarları ).
              Eksik alanlar Excel örneğinin varsayılanlarıyla tamamlanır.
    """
    g = MG.varsayilanlar()
    g.update(veriler or {})
    g = MG.tamamla(g)
    hata = MG.dogrula(g)
    if hata:
        return {"aktif": False, "hata": hata, "girdi": g}

    o = {}
    bolumler = [uret(g, o) for uret in BOLUM_URETICILERI]
    uygunlar = [b["sonuc"]["uygun"] for b in bolumler
                if b.get("sonuc") and b["sonuc"].get("uygun") is not None]
    return {
        "aktif": True,
        "baslik": "ASANSÖR MUKAVEMET HESAPLARI",
        "girdi": g,
        "bolumler": bolumler,
        "sabitler": dict(SABIT),
        "ozet": {
            "N_hesap": o.get("N_hesap"), "motor_uygun": o.get("motor_uygun"),
            "kabin_alani": o.get("kabin_alani"), "kabin_kisi": o.get("kabin_kisi"),
            "Sf": o.get("Sf"), "S_gercek": o.get("S_gercek"),
            "ray_boyu": o.get("ray_boyu"), "Mg_kabin": o.get("Mg_kabin"),
            "Mg_agirlik": o.get("Mg_agirlik"), "Fk_kabin": o.get("Fk_kabin"),
            "FKR": o.get("FKR"), "FAR": o.get("FAR"),
            "Fkt": o.get("Fkt"), "Fat": o.get("Fat"),
            "tumu_uygun": all(uygunlar),
        },
        "uyarilar": [],
        #  Kaynak Excel doğrulaması için  { hücre adresi : hesaplanan değer }
        "_h": o.get("_h", {}),
    }
