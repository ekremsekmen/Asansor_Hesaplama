# -*- coding: utf-8 -*-
"""
OFİS STANDARDI  —  HER İKİ PROJENİN ORTAK KABULLERİ

Burada yalnız AVAN ve UYGULAMA projelerinin İKİSİNİN BİRDEN kullandığı,
projeye değil OFİSE ait kabuller durur.  İki proje ayrı klasörlerdedir
( engine/avan · engine/uygulama ) ve ayrı çalışma kitapları kullanır;  ama
aynı fiziksel büyüklüğün iki yerde iki farklı sayı olması hata demektir.

NİÇİN AYRI DOSYA:
    Makine verimi η bir süre iki yerde ayrı ayrı duruyordu — avan tarafında
    makine tipine bağlı ( dişlisiz 0,85 · dişli 0,50 ), mukavemet tarafında
    ise makine tipinden bağımsız sabit 0,92.  Aynı asansör için iki pafta
    farklı motor gücü veriyordu ve mukavemetinki DÜŞÜK, yani emniyetsiz
    olandı ( dişli makinede gerçek ihtiyacın yarısı ).  Tek kaynağa
    alınmasının sebebi budur:  buradan okuyan iki taraf bir daha ayrışamaz.
"""
import math


#  Makine tipine göre verim  ( ofis kabulü ).  Anahtarlar, mukavemet çalışma
#  kitabının 'Veri Girişi'!B130 açılır listesindeki metinlerle AYNI olmalıdır
#  ( "Dişli,Dişlisiz" ) — yoksa Excel'den gelen değer tabloda bulunamaz.
MAKINE_VERIMLERI = {
    "Dişlisiz": 0.85,
    "Dişli":    0.50,
}

#  Palangalı ( i > 1 ) sistemde verim düşüşü  —  MMO/697 §2.4.
#  Avan tarafında SABİTLER A'dan değiştirilebilir;  uygulama projesi de aynı
#  ofis sabitini okur ( bkz. mukavemet._motor ).
PALANGA_VERIM_DUSUSU = 0.10

#  Tanınmayan makine tipinde kullanılacak verim.  Kaynak mukavemet kitabının
#  11!AQ22 hücresindeki eski sabittir;  yalnız GERİYE DÖNÜK uyum içindir,
#  yeni hesaplarda makine tipi her zaman girilir.
VARSAYILAN_VERIM = 0.92


#  ---------------------------------------------------------------------
#  ANMA YÜKÜNE GÖRE ORTALAMA BOŞ KABİN KÜTLESİ  Gk   ( ofis tablosu )
#  ---------------------------------------------------------------------
#  BU TABLO STANDARTTAN GELMİYOR — böyle bir çizelge yoktur.
#  TS EN 81-20 ve TS EN 81-50 boş kabin kütlesini ( P ) her yerde GİRDİ
#  olarak tanımlar:  "P is the mass of the empty car and components
#  supported by the car…".  Dokuz ayrı yerde geçer, hiçbirinde sayı ya da
#  çizelge verilmez;  kabinin kaç kilo geleceğini imalatçı belirler.
#  ISO 4190-1 aynı yük serisi için ( 320 · 450 · 630 · 800 · 1000 · 1275 ·
#  1600 · 1800 · 2000 kg ) kabin ÖLÇÜLERİNİ verir, kütle vermez.
#
#  BU MMO/697'NİN TABLO-11'İ DEĞİLDİR.  Kitabın Tablo-11'i "beyan yüküne
#  göre kullanılabilir en büyük kabin alanı"dır ( 450 kg → 1,30 m² ) ve
#  boş kabin kütlesi vermez.  Aşağıdaki değerler OFİSİN KENDİ İMALATÇI
#  DENEYİMİNDEN gelir;  paftada kaynağı da öyle yazılır.
#
#  NİÇİN ORTAK DOSYADA:  avan tarafı bu tabloyu zaten kullanıyordu;  şimdi
#  uygulama projesi de boş kabin ağırlığını buradan doldurur.  İki yerde iki
#  ayrı kopya tutulsaydı biri güncellenip öteki unutulur, aynı asansör iki
#  projede iki farklı kabin kütlesiyle hesaplanırdı.
GK_TABLOSU = ((450, 500), (630, 650), (800, 800), (1000, 950), (1125, 1020),
              (1275, 1100), (1600, 1350), (2000, 1600), (2500, 1900))

GK_KAYNAGI = "OFİS TABLOSU  —  ortalama boş kabin kütlesi  ( standart sayısı değildir )"

#  Tablonun kapsadığı yük aralığı.  Dışında UÇ DEĞERE SABİTLENİR:  100 kg'lık
#  bir asansöre 500 kg'lık kabin gelir.  Sayı ekranda görünür ve elle
#  değiştirilebilir;  kapsam dışında tabloya güvenilmemelidir.
GK_ALT, GK_UST = GK_TABLOSU[0][0], GK_TABLOSU[-1][0]


def bos_kabin_kutlesi(Q):
    """Anma yüküne göre ortalama boş kabin kütlesi  ( kg ) — TAHMİNDİR.

    Ara yükler doğrusal ara değerle bulunur ve 10 kg'a yuvarlanır ( kaynak
    çalışma kitabının ROUND'u ).  Aralık dışında uç değere sabitlenir.
    """
    if not isinstance(Q, (int, float)) or isinstance(Q, bool):
        return None
    if Q <= GK_ALT:
        return float(GK_TABLOSU[0][1])
    if Q >= GK_UST:
        return float(GK_TABLOSU[-1][1])
    for (x0, y0), (x1, y1) in zip(GK_TABLOSU, GK_TABLOSU[1:]):
        if x0 <= Q <= x1:
            y = y0 + (Q - x0) * (y1 - y0) / (x1 - x0)
            #  Excel'in ROUND'u yarımı YUKARI yuvarlar;  Python'unki bankacı
            #  yuvarlaması yapar ( 865 → 860 ).  Fark 10 kg'lık kademede
            #  görünür, o yüzden elle yapılır.
            return float(math.floor(y / 10.0 + 0.5) * 10)
    return None


def makine_verimi(makine_tipi):
    """Makine tipine göre η.  Tanınmayan tip için None."""
    return MAKINE_VERIMLERI.get(makine_tipi)


def sistem_verimi(makine_tipi, aski_orani=1, palanga_dususu=None):
    """η′  —  makine tipi ve askı oranına göre sistem verimi.

    Palangalı sistemde ( i > 1 ) ek makara ve halat sürtünmesi yüzünden
    verim düşer;  MMO/697 §2.4 bunu sabit bir düşüşle karşılar.
    Tanınmayan makine tipinde VARSAYILAN_VERIM'e dönülür.
    """
    eta = makine_verimi(makine_tipi)
    if eta is None:
        eta = VARSAYILAN_VERIM
    dusus = PALANGA_VERIM_DUSUSU if palanga_dususu is None else palanga_dususu
    try:
        palangali = float(aski_orani) > 1
    except (TypeError, ValueError):
        palangali = False
    return (eta - dusus) if palangali else eta
