# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ — GİRDİ SÖZLEŞMESİ

Uygulama projesi iki hesap ailesini birlikte kullanır:

    MUKAVEMET      engine/mukavemet.py        ( 10 bölüm )
    ELEKTRİK       engine/avan.py'nin 3-6.    ( kabin ve kuyu aydınlatması,
                   bölümleri + topraklama +     kurulu güç cetveli, gerilim
                   makine dairesi aydınlatması  düşümü ve kesit kontrolü )

BU MODÜLÜN VARLIK SEBEBİ:  iki aile ORTAK GİRDİLERİ paylaşır — kabin
ölçüleri, beyan yükü, hız, kuyu boyu, motor gücü, askı oranı, ray profili.
Aynı değeri iki kere sormak yalnız zahmet değil, HATA KAYNAĞIDIR:  biri
düzeltilip öteki unutulduğunda iki hesap sessizce ayrışır ve pafta kendi
içinde çelişir.

Bu yüzden:
  · Ortak girdiler YALNIZ mukavemet sözleşmesinde tanımlıdır
    ( engine/mukavemet_girdi.ALANLAR ) — orası Excel'e karşı hücre hücre
    doğrulanır, tek doğruluk kaynağıdır.
  · Elektrik hesaplarının mukavemette KARŞILIĞI OLMAYAN girdileri burada,
    ayrı bir grupta tanımlanır.
  · Ortak olanlar `kopru()` ile mukavemet girdisinden TÜRETİLİR, kullanıcıya
    ikinci kez sorulmaz.

Not:  ofis standardı ( U · κ · εmax · armatürler · priz · cosφ · β · çubuk )
zaten "Sabitler / Ofis Standardı" sekmesinden gelir;  o da ikinci kez
sorulmaz.
"""
from engine.uygulama import mukavemet as MK
from engine.uygulama import sabitler as US
from engine.uygulama import mukavemet_girdi as MG
from engine.uygulama import mukavemet_tablolari as MT

#  Tanınmayan makine tipinde geri düşülecek verim.  Gerçek verim makine
#  tipinden ve projenin kendi ofis sabitlerinden gelir ( US.verim ).
MK_VERIM = US.OFIS.VARSAYILAN_VERIM

#  ( anahtar , etiket , birim , tür , seçenekler , varsayılan )
#  Mukavemette KARŞILIĞI OLMAYAN girdiler.  Hepsi elektrik hesaplarına girer.
#  PROJE GENELİ GİRDİLER.  Temel topraklama ve makine dairesi BİNAYA aittir,
#  asansöre değil:  bir binada dört asansör varsa topraklama tektir ve makine
#  dairesi ortaktır.  Çoklu projede bunlar asansör formunun DIŞINDA bir kez
#  girilir ve her asansörün girdi setine karıştırılır — elektrik köprüsü
#  onları orada bekler.  Liste burada durur ki API ve arayüz aynı yerden
#  okusun;  iki yerde tutulsaydı ayrışırlardı.
PROJE_GENELI_ALANLAR = ("temel_a", "temel_b", "serit_L",
                        "mk_yok", "mk_uzunluk", "mk_genislik")

EK_ALANLAR = (
    ("kuyu_genisligi",  "Kuyu genişliği  ( KG )",            "mm",   "sayi", None, 2400),
    ("kolon_kesit",     "S1 — Kolon hattı kesiti",           "mm²",  "sayi", None, 16),
    ("kolon_uzunluk",   "L1 — Kolon hattı uzunluğu",         "m",    "sayi", None, None),
    ("makine_kesit",    "S2 — Makine besleme kesiti",        "mm²",  "sayi", None, 6),
    ("makine_uzunluk",  "L2 — Makine besleme uzunluğu",      "m",    "sayi", None, 12),
    ("temel_a",         "Temel uzunluğu",                    "m",    "sayi", None, None),
    ("temel_b",         "Temel genişliği",                   "m",    "sayi", None, None),
    ("serit_L",         "Topraklama şeridi boyu",            "m",    "sayi", None, None),
    ("mk_yok",          "Makine dairesiz  ( MRL )",          "—",    "onay", None, True),
    ("mk_uzunluk",      "Makine dairesi uzunluğu",           "m",    "sayi", None, None),
    ("mk_genislik",     "Makine dairesi genişliği",          "m",    "sayi", None, None),
)

EK_ALAN = {a[0]: a for a in EK_ALANLAR}

EK_GRUP = ("Elektrik ve topraklama  ( uygulama projesi )",
           tuple(a[0] for a in EK_ALANLAR))

#  ELEKTRİK VE PROJE GENELİ BÖLÜMLERİN GİRDİ GRUPLARI.
#  mukavemet_girdi.BOLUM_GRUBU'nun devamı — oradaki on bölüm mukavemetin,
#  buradakiler avan motorundan ödünç alınanlardır.  Anahtar yine bölümün
#  KİMLİĞİDİR;  numara kullanılırken bu sözlük "mukavemet 10 bölümdür,
#  elektrik 11'den başlar" varsayımını taşımak zorundaydı ve mukavemete bir
#  bölüm eklendiğinde sessizce yanlış bölümü gösterecekti.
#
#  PROJE GENELİ BÖLÜMLER DE ARTIK EŞLENİYOR.  Numara ile eşlenemiyorlardı:
#  makine dairesi varsa topraklama 16'dan, yoksa 15'ten başlıyordu.
EK_BOLUM_GRUBU = {
    "kabin_aydinlatma":          ("Kabin ve kapı",),        # ← kabin ölçüleri
    "kuyu_aydinlatma":           (EK_GRUP[0], "Durak ve kuyu"),   # ← KG · kuyu boyu
    #  ELEKTRİK GRUBU DEĞİL.  Cetvelde kuyu aydınlatması var, ama armatür
    #  ADEDİ kuyu YÜKSEKLİĞİNDEN gelir;  kuyu genişliği yalnız lux kontrolüne
    #  girer ve kurulu gücü değiştirmez.  Gücü belirleyenler motor ( Nsç ) ve
    #  kabin ölçüsü ( kabin armatür adedi ).
    "kurulu_guc":                ("Makine ve motor", "Kabin ve kapı"),
    "gerilim_dusumu":            (EK_GRUP[0], "Makine ve motor"),  # ← S1 · L1 · S2 · L2
    "makine_dairesi_aydinlatma": (EK_GRUP[0],),             # ← makine dairesi ölçüsü
    "topraklama_yatay":          (EK_GRUP[0],),             # ← temel a · b · şerit L
    "topraklama_dikey":          (EK_GRUP[0],),
    "topraklama_toplam":         (EK_GRUP[0],),
}



def arayuz_alanlari():
    """Formun kendini üretmesi için tüm gruplar  ( mukavemet + elektrik )."""
    veri = MG.arayuz_alanlari()
    veri["gruplar"].append({
        "ad": EK_GRUP[0],
        "alanlar": [{"anahtar": a, "hucre": "", "etiket": et, "birim": b,
                     "tur": t, "secenekler": list(s) if s is not None else None,
                     "varsayilan": v}
                    for a, et, b, t, s, v in EK_ALANLAR],
    })
    veri["bolum_grubu"].update({no: list(gr)
                                for no, gr in EK_BOLUM_GRUBU.items()})
    return veri


def varsayilanlar():
    g = MG.varsayilanlar()
    for a, _et, _b, _t, _s, v in EK_ALANLAR:
        g[a] = v
    return g


def tamamla(g):
    g = MG.tamamla(g)
    for a, _et, _b, _t, _s, v in EK_ALANLAR:
        g.setdefault(a, v)
    return g


def dogrula(g):
    """Mukavemet doğrulaması + elektrik girdilerinin denetimi."""
    hata = list(MG.dogrula(g))
    for a, et, birim, tur, _s, _v in EK_ALANLAR:
        d = g.get(a)
        ad = f"{et} ({birim})" if birim not in ("—", "") else et
        if tur == "onay":
            continue
        if d is None or d == "":
            continue                       # boş bırakılabilir — hesap uyarır
        if not isinstance(d, (int, float)) or isinstance(d, bool) or d < 0:
            hata.append(f"{ad}: negatif olmayan bir sayı olmalı ( {d!r} girildi ).")
    #  Makine dairesi işaretli DEĞİLSE ölçüsü istenir;  yoksa aydınlatma
    #  hesabı sessizce yapılamaz hâle gelirdi.
    if not g.get("mk_yok"):
        for a in ("mk_uzunluk", "mk_genislik"):
            if not (isinstance(g.get(a), (int, float)) and g[a] > 0):
                hata.append(f"{EK_ALAN[a][1]}: makine dairesi varsa ölçüsü girilmelidir "
                            "( ya da 'Makine dairesiz ( MRL )' kutusunu işaretleyin ).")
    return hata


def kopru(g):
    """ORTAK GİRDİ KÖPRÜSÜ  —  mukavemet girdisi  →  avan asansör girdisi.

    Buradaki her satır, kullanıcıya İKİNCİ KEZ SORULMAYAN bir alandır.
    Sağ taraf mukavemet sözleşmesinden gelir;  sol taraf engine/avan.py'nin
    beklediği addır.
    """
    ray = MT.ray(g.get("kabin_ray_profili"), "Gr")
    asansor = {
        "aktif": True,
        "tanim": "Uygulama projesi",
        #  ── ortak ── ( mukavemetten )
        "Q_elle": g.get("beyan_yuku"),            # beyan yükü          [kg]
        "V": g.get("beyan_hizi"),                 # kabin hızı          [m/s]
        "Gk_elle": g.get("kabin_agirligi"),       # boş kabin kütlesi   [kg]
        "kabin_boyu": g.get("kabin_derinligi"),   # avanda "boy" = derinlik
        "kabin_genisligi": g.get("kabin_genisligi"),
        "Hk": (g.get("kuyu_boyu") or 0) / 1000.0,  # kuyu yüksekliği    [m]
        "Nsc": g.get("motor_gucu"),               # seçilen motor gücü  [kW]
        "i_palanga": g.get("aski_orani"),
        "gr": ray,                                # ray metre ağırlığı  [kg/m]
        #  Motor verimi:  MAKİNE TİPİNDEN gelir ( ofis standardı, tek kaynak
        #  engine/ortak/ofis.py ) ve TOPLAM SİSTEM VERİMİDİR — askı kaybı
        #  içindedir.  İki taraf aynı sayıyı kullanır;  eskiden avan bunun
        #  üstüne Δη = 0,10 uyguluyordu ve köprü "taban η" geçirmek zorundaydı.
        #  Δη kalktığı için o ayrım da kalktı.  ( Daha eskiden buradan sabit
        #  0,92 geçiyordu:  aynı asansör için avan ve uygulama paftaları
        #  farklı motor gücü veriyordu. )
        "makine_tipi": g.get("makine_tipi"),
        "eta": US.verim(US.sabitler(g.get("_ofis")), g.get("makine_tipi")),
        #  ── uygulama projesine özgü ──
        "kuyu_genisligi": g.get("kuyu_genisligi"),
        "S1": g.get("kolon_kesit"), "L1": g.get("kolon_uzunluk"),
        "S2": g.get("makine_kesit"), "L2": g.get("makine_uzunluk"),
    }
    ortak = {
        "temel_a": g.get("temel_a"), "temel_b": g.get("temel_b"),
        "serit_L": g.get("serit_L"),
        "mk_yok": bool(g.get("mk_yok")),
        "mk_uzunluk": g.get("mk_uzunluk"), "mk_genislik": g.get("mk_genislik"),
    }
    #  OFİS STANDARDI  ( Sabitler sekmesi ):  armatür ışık akısı, priz, cosφ,
    #  εmax, κ, U, β, çubuk sayısı …  Elektrik ve topraklama hesapları bunları
    #  kullanır;  köprüden geçmezse kullanıcının sekmedeki değişikliği hiçbir
    #  şeyi değiştirmezdi.
    return {"ortak": ortak, "asansorler": [asansor],
            "sabitler": _avan_sabitleri(g.get("_ofis")), "trafik": {}}


#  Uygulamanın ofis sabiti  →  avan motorunun beklediği anahtar.  Elektrik ve
#  topraklama hesapları avan motorunda koştuğu için ( ELEKTRIK_BOLUMLERI )
#  uygulamanın kendi setinden karşılığı olanlar oraya çevrilir.  Adı aynı
#  olanlar zaten eşleşir;  liste yalnız ADI FARKLI olanlar içindir.
AVAN_KARSILIGI = {}
#  Avan motoruna GEÇMEYECEKLER:  yalnız mukavemeti ilgilendirirler ve avan
#  tarafında aynı adla başka bir anlam taşıyabilirler.
AVAN_DISI = ("q_denge", "sigma_em", "k1_kaymali", "k1_makarali", "k1_ani",
             "yan_yatak_L_X", "halat_pay_m", "Gs", "verim_dislisiz",
             "verim_disli") + MK.SIGINMA_PAYLARI


def _avan_sabitleri(ofis):
    """Uygulamanın ofis setinden, avan motorunun kullanabileceği alt küme."""
    if not isinstance(ofis, dict):
        return {}
    d = {}
    for k, v in ofis.items():
        if k in AVAN_DISI:
            continue
        d[AVAN_KARSILIGI.get(k, k)] = v
    return d


#  ORTAK ALANLARIN LİSTESİ  —  arayüz bunu "bu değer mukavemetten geliyor"
#  diye gösterir;  belgeleme ve test de buradan okur.
ORTAK_KOPRU = (
    ("Beyan yükü",           "beyan_yuku",        "Q"),
    ("Beyan hızı",           "beyan_hizi",        "V"),
    ("Boş kabin ağırlığı",   "kabin_agirligi",    "Gk"),
    ("Kabin derinliği",      "kabin_derinligi",   "a  ( kabin boyu )"),
    ("Kabin genişliği",      "kabin_genisligi",   "b"),
    ("Kuyu boyu",            "kuyu_boyu",         "Hk"),
    ("Motor gücü",           "motor_gucu",        "Nsç"),
    ("Askı oranı",           "aski_orani",        "i"),
    ("Kabin rayı profili",   "kabin_ray_profili", "gr  ( ray metre ağırlığı )"),
)
