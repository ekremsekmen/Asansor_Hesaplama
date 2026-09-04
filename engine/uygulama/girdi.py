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
from engine.uygulama import mukavemet_girdi as MG
from engine.uygulama import mukavemet_tablolari as MT

MK_VERIM = MK.SABIT["motor_verimi"]

#  ( anahtar , etiket , birim , tür , seçenekler , varsayılan )
#  Mukavemette KARŞILIĞI OLMAYAN girdiler.  Hepsi elektrik hesaplarına girer.
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
        #  Motor verimi:  mukavemet motorunun kabulü kullanılır ( MMO 208/7
        #  hesabındaki η ).  Avan tarafına da aynı değer gider ki iki hesap
        #  aynı verimden konuşsun;  kullanıcıya ayrıca sorulmaz.
        "eta": MK_VERIM,
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
    sabitler = g.get("_ofis")
    return {"ortak": ortak, "asansorler": [asansor],
            "sabitler": sabitler if isinstance(sabitler, dict) else {},
            "trafik": {}}


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
