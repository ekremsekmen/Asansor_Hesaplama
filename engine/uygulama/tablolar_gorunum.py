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
from engine.uygulama import mukavemet_tablolari as MT


def _satirlar(kayitlar):
    return [[("" if h is None else h) for h in k] for k in kayitlar]


def arayuz_tablolari():
    """Ekranın çizeceği tabloların tamamı."""
    t = []

    t.append({
        "ad": "Kılavuz ray profilleri",
        "kaynak": "ISO 7465  ·  kaynak çalışma kitabı TABLOLAR!I60:S65",
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
        "satirlar": _satirlar(MT.RAY_CELIGI),
    })
    t.append({
        "ad": "ω  —  burkulma katsayısı",
        "kaynak": "TS EN 81-50 m.5.10.3",
        "aciklama": ("λ = 20…250 için Rm = 370 ve 520 eğrileri;  aradaki "
                     "dayanımlarda doğrusal ara değer alınır.  Kaynak kitabın "
                     "tek tablosu yalnız 370 eğrisiydi ( sapma ⑤ )."),
        "basliklar": ["λ", "ω  ( Rm = 370 )", "ω  ( Rm = 440 )", "ω  ( Rm = 520 )"],
        "satirlar": [[lam,
                      round(MT.omega_en8150(lam, 370), 4),
                      round(MT.omega_en8150(lam, 440), 4),
                      round(MT.omega_en8150(lam, 520), 4)]
                     for lam in range(MT.OMEGA_LAMBDA_MIN,
                                      MT.OMEGA_LAMBDA_MAX + 1, 5)],
    })
    t.append({
        "ad": "NPU profilleri  ( makine kaidesi )",
        "kaynak": "kaynak çalışma kitabı TABLOLAR",
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
        "kaynak": "TS EN 81-50 m.5.11.2.2",
        "aciklama": "Kanal şekli → kanal açısı γ ve alt kesilme açısı β.",
        "basliklar": ["Kanal şekli", "γ  ( ° )", "β  ( ° )"],
        "satirlar": _satirlar(MT.KANAL_SEKLI),
    })
    t.append({
        "ad": "Kanal işleme",
        "kaynak": "TS EN 81-50 m.5.11.2",
        "aciklama": "Sertleştirilmiş kanalda sürtünme katsayısı farklıdır.",
        "basliklar": ["İşleme", "f  ( yükleme )", "f  ( acil frenleme )"],
        "satirlar": [[k[0], round(k[1], 5), round(k[2], 5)]
                     for k in MT.KANAL_ISLEME],
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
        "kaynak": "kaynak çalışma kitabı TABLOLAR!U61:W62",
        "aciklama": "Malzeme → özgül ağırlık ve blok yüksekliği.",
        "basliklar": ["Malzeme", "γ", "h  ( mm )"],
        "satirlar": _satirlar(MT.AGIRLIK_MALZEMESI),
    })
    t.append({
        "ad": "Ray arası  →  karşı ağırlık genişliği",
        "kaynak": "kaynak çalışma kitabı TABLOLAR",
        "aciklama": "",
        "basliklar": ["Ray arası  ( mm )", "Ağırlık genişliği  ( mm )"],
        #  Tablo iki satırlık bir eşlemedir:  ( ray araları ) → ( genişlikler ).
        #  Motorun kendi arama işlevinden okunur ki ekran ile hesap ayrışmasın.
        "satirlar": [[a, MT.agirlik_genisligi(a)] for a in MT.RAY_ARALARI],
    })
    t.append({
        "ad": "Gezici kablo  ( bükülgen )",
        "kaynak": "kaynak çalışma kitabı TABLOLAR",
        "aciklama": "Kablo tipi → ağırlık · çap · kesit.",
        "basliklar": ["Tip", "Ağırlık", "Çap", "Kesit"],
        "satirlar": _satirlar(MT.BUKULGEN_KABLO),
    })
    t.append({
        "ad": "Kat kapısı  →  kablo tipi",
        "kaynak": "kaynak çalışma kitabı  ( 'Veri Girişi'!B108 türetilir )",
        "aciklama": "İkinci gezici kablo, kat kapısı tipinden belirlenir.",
        "basliklar": ["Kapı tipi", "Kablo"],
        "satirlar": _satirlar(MT.KAPI_KABLO),
    })
    return t
