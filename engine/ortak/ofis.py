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
