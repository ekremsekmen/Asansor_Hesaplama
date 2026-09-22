# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİNİN TABLOLARI  —  EKRAN GÖRÜNÜMÜ

Uygulama projesinin 30'a yakın tablosu ( ray profilleri, NPU kesitleri,
halat ağırlıkları, ω burkulma, kabin alanları … ) bugüne kadar YALNIZ
motorun içindeydi:  hesaba giriyorlardı ama ekranda görünmüyorlardı.
Uygulama yapan mühendis kullandığı ray tablosuna bakamıyordu — avan
tarafında Tablolar sekmesi vardı, uygulamada yoktu.

Burası o boşluğu kapatır.  Tablolar KOPYALANMAZ;  motorun kullandığı
sözlüklerden okunur, yalnız sunum bilgisi ( başlık · sütun adları · kaynak )
eklenir.  Böylece ekrandaki tablo ile hesaba giren tablo bir daha ayrışamaz.
"""
import math

from engine.ortak.steps import yuvarla
from engine.uygulama import mukavemet_tablolari as MT
from engine.uygulama import sabitler as US


def _satirlar(kayitlar):
    return [[("" if h is None else h) for h in k] for k in kayitlar]


def _f_yukleme(sekil, mu, gama_d, beta_d, sert):
    """TS EN 81-50 m.5.11.2.3.1'in sürtünme çarpanı  —  motorla AYNI bağıntı."""
    beta = math.radians(beta_d)
    gama = math.radians(gama_d)
    if MT.kanal_yarim_daire_mi(sekil):
        pay = 4 * (math.cos(gama / 2.0) - math.sin(beta / 2.0))
        payda = (math.pi - beta - gama - math.sin(beta) + math.sin(gama))
        return mu * pay / payda
    if sert:
        return mu / math.sin(gama / 2.0)
    return mu * 4 * (1 - math.sin(beta / 2.0)) / (math.pi - beta - math.sin(beta))


def arayuz_tablolari(ofis=None):
    """Ekranın çizeceği tabloların tamamı.

    ``ofis``:  projenin ofis sabitleri.  Kanal açıları γ / β ve onlardan
    türeyen Nequiv(t) ile f, PROJENİN kendi sabitlerinden hesaplanır — ekranda
    donmuş bir tablo görünüp hesabın başka bir sayı kullanması, denetimde
    bulunan hatalardan biriydi.
    """
    O = US.sabitler(ofis)
    t = []

    t.append({
        "ad": "Kılavuz ray profilleri",
        "kaynak": "ISO 7465",
        "aciklama": "Ray hesabının bütün kesit değerleri buradan okunur.",
        "basliklar": ["Profil", "b  ( balata yarı gen. )", "A  ( mm² )",
                      "Ix  ( mm⁴ )", "Iy  ( mm⁴ )", "Wx  ( mm³ )", "Wy  ( mm³ )",
                      "ix  ( mm )", "iy  ( mm )", "c  ( mm )", "gr  ( kg/m )"],
        "satirlar": _satirlar(MT.RAY_PROFILI),
    })
    t.append({
        "ad": "Ray geometrisi  ( flanş eğilmesi )",
        "kaynak": "TS EN 81-50 m.5.10.5",
        "aciklama": "σF hesabındaki c · h1 · f ölçüleri.",
        "basliklar": ["Profil", "f", "h1", "Genişlik", "Ayak", "Yükseklik"],
        "satirlar": _satirlar(MT.RAY_GEOMETRI),
    })
    t.append({
        "ad": "Ray çeliği  —  emniyet gerilmeleri",
        "kaynak": "TS EN 81-20 Çizelge 15  ( A5 > %12 )",
        "aciklama": "σperm = Rm / St;  St = 2,25 normal · 1,8 güvenlik tertibatı.",
        "basliklar": ["Rm  ( N/mm² )", "σperm normal", "σperm güv. tertibatı"],
        "satirlar": [[rm, yuvarla(n, 2), yuvarla(gv, 2)] for rm, n, gv in MT.RAY_CELIGI],
    })
    t.append({
        "ad": "ω  —  burkulma katsayısı",
        "kaynak": "TS EN 81-50 m.5.10.3",
        "aciklama": ("λ = 20…250 için Rm = 370 ve 520 eğrileri;  aradaki "
                     "dayanımlarda doğrusal ara değer alınır."),
        "basliklar": ["λ", "ω  ( Rm = 370 )", "ω  ( Rm = 440 )", "ω  ( Rm = 520 )"],
        "satirlar": [[lam,
                      yuvarla(MT.omega_en8150(lam, 370), 4),
                      yuvarla(MT.omega_en8150(lam, 440), 4),
                      yuvarla(MT.omega_en8150(lam, 520), 4)]
                     for lam in range(MT.OMEGA_LAMBDA_MIN,
                                      MT.OMEGA_LAMBDA_MAX + 1, 5)],
    })
    t.append({
        "ad": "NPU profilleri  ( makine kaidesi )",
        "kaynak": "NPU profil tablosu  ( ofis )",
        "aciklama": ("240 · 280 · 300 satırlarında atalet yarıçapı ix BOŞTUR; "
                     "program bu seçimi açık mesajla reddeder."),
        "basliklar": ["Ölçü", "A  ( cm² )", "Wx", "Wy", "Ix", "Iy", "ix", "iy", "e"],
        "satirlar": _satirlar(MT.NPU_PROFIL),
    })
    t.append({
        "ad": "Askı halatları",
        "kaynak": "TS 12385-5",
        "aciklama": "Halat çapı → metre ağırlığı · kopma kuvveti · yapı · Rm.",
        "basliklar": ["d  ( mm )", "Ağırlık  ( kg/m )", "Kopma  ( N )",
                      "Yapı", "Rm  ( N/mm² )"],
        "satirlar": _satirlar(MT.HALAT),
    })
    t.append({
        "ad": "Kabin alanı",
        "kaynak": "TS EN 81-20 m.5.4.2  ( Çizelge 6 · 7 )",
        "aciklama": ("Beyan yüküne göre kişi sayısı ve kullanılabilir en "
                     "büyük / en küçük kabin alanı."),
        "basliklar": ["Q  ( kg )", "Kişi", "Azami alan  ( m² )", "Asgari alan  ( m² )"],
        "satirlar": _satirlar(MT.KABIN_ALANI),
    })
    t.append({
        "ad": "Tahrik kanalı",
        "kaynak": "TS EN 81-50 m.5.11.2.3.1  ·  m.5.12.2.2 Çizelge 2",
        "aciklama": ("γ ve β OFİS SABİTLERİDİR ( Sabitler sekmesi );  Nequiv(t) "
                     "onlardan Çizelge 2'ye göre hesaplanır;  ofis açısı "
                     "değişince tablo ve pafta da değişir."),
        "basliklar": ["Kanal şekli", "Tür", "γ  ( ° )", "β  ( ° )", "Nequiv(t)"],
        "satirlar": [[ad,
                      {"V": "V kanal", "VK": "V kanal, altı kesik",
                       "U": "yarım daire", "UK": "yarım daire, altı kesik"}[tur],
                      MT.kanal_acisi(ad, O["kanal_gama_v"], O["kanal_gama_yd"]),
                      MT.kanal_beta(ad, O["kanal_beta"]),
                      yuvarla(MT.kanal_nequiv_t(ad, O["kanal_gama_v"],
                                              O["kanal_beta"]), 2)]
                     for ad, tur, _gecis in MT.KANAL_SEKLI],
    })
    t.append({
        "ad": "Nequiv(t)  —  eşdeğer kasnak sayısı",
        "kaynak": "TS EN 81-50 m.5.12.2.2 Çizelge 2",
        "aciklama": ("Çizelgede olmayan açılar için doğrusal ara değer alınır "
                     "( çizelgenin kendi notu ).  Alt kesilmesiz yarım daire "
                     "kanalda Nequiv(t) = 1'dir."),
        "basliklar": ["Kanal", "Açı  ( ° )", "Nequiv(t)"],
        "satirlar": ([["V kanal  ( γ )", a, n] for a, n in MT.NEQUIV_V]
                     + [["Altı kesik  ( β )", a, n]
                        for a, n in MT.NEQUIV_U_ALTI_KESIK]),
    })
    t.append({
        "ad": "Kanal işleme  →  sürtünme çarpanı f  ( kabinin yüklenmesi )",
        "kaynak": "TS EN 81-50 m.5.11.2.3.1  ·  μ = 0,1  ( m.5.11.2.3.2 )",
        "aciklama": ("f, kanal ŞEKLİNE ve ofis açılarına göre değişir.  "
                     "Sertleştirme yalnız V kanalda fark yaratır — yarım daire "
                     "kanalın kendi maddesinde ( m.5.11.2.3.1.1 ) sertleştirme "
                     "geçmez."),
        "basliklar": ["Kanal şekli"] + list(MT.KANAL_ISLEME_SEKILLERI),
        "satirlar": [[ad] + [yuvarla(_f_yukleme(
            ad, 0.1,
            MT.kanal_acisi(ad, O["kanal_gama_v"], O["kanal_gama_yd"]),
            MT.kanal_beta(ad, O["kanal_beta"]),
            isleme == "Sertleştirilmiş"), 5)
            for isleme in MT.KANAL_ISLEME_SEKILLERI]
            for ad, _t, _g in MT.KANAL_SEKLI],
    })
    t.append({
        "ad": "Güvenlik tertibatı  —  darbe katsayısı k1",
        "kaynak": ("OFİS KABULÜ.  TS EN 81-20 Çizelge 14 bu katsayıları "
                   "KILAVUZ RAY hesabı için verir;  makine kaidesindeki "
                   "kullanım ödünçtür ( Sabitler sekmesinden değiştirilir )."),
        "aciklama": "",
        "basliklar": ["Tertibat tipi", "k1"],
        "satirlar": _satirlar(MT.DARBE_TIPLERI),
    })
    t.append({
        "ad": "Karşı ağırlık malzemesi",
        "kaynak": "ofis tablosu",
        "aciklama": "Malzeme → özgül ağırlık ve blok yüksekliği.",
        "basliklar": ["Malzeme", "γ", "h  ( mm )"],
        "satirlar": _satirlar(MT.AGIRLIK_MALZEMESI),
    })
    t.append({
        "ad": "Gezici kablo  ( bükülgen )",
        "kaynak": "ofis tablosu",
        "aciklama": "Kablo tipi → ağırlık · çap · kesit.",
        "basliklar": ["Tip", "Ağırlık", "Çap", "Kesit"],
        "satirlar": _satirlar(MT.BUKULGEN_KABLO),
    })
    t.append({
        "ad": "Kat kapısı  →  kablo tipi",
        "kaynak": "ofis kabulü",
        "aciklama": "İkinci gezici kablo, kat kapısı tipinden belirlenir.",
        "basliklar": ["Kapı tipi", "Kablo"],
        "satirlar": _satirlar(MT.KAPI_KABLO),
    })
    return t
