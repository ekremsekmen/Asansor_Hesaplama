# -*- coding: utf-8 -*-
"""
TEST 1  —  EXCEL UYUMU  (bağımsız doğrulama)

Her senaryo için:
   1) girdiler ofis Excel ŞABLONUNA yazılır,
   2) dosya LibreOffice ile açılıp YENİDEN HESAPLANIR
      ( yani hesabı Excel'in kendi formülleri yapar, program değil ),
   3) çıkan her hücre programın motoruyla karşılaştırılır.

Bu, programın Excel'den sapıp sapmadığını gösteren en güçlü testtir.
LibreOffice kurulu değilse test zarifçe atlanır.
"""
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import openpyxl                                          # noqa: E402
from engine.avan import hesap as AV
from engine.avan import tablolar as T
from engine.avan import trafik as TR  # noqa: E402
from exports import xlsx_export as X                     # noqa: E402
from testler.ortak import Rapor, yeniden_hesapla, soffice_yolu, hata_hucresi_ara  # noqa: E402

# Geçici dosyalar sistemin temp klasörüne yazılır — proje klasörü kirlenmez
# ve silme izni kısıtlı makinelerde test takılmaz.
GECICI = os.path.join(tempfile.gettempdir(),
                      "avan_test_" + os.path.splitext(os.path.basename(__file__))[0])


# =====================================================================
#  SENARYOLAR  —  rastgele değil, sistemli.  Tablo sınırlarını ve
#  bina tiplerini kasten zorlar.
# =====================================================================
def _nufus(bina_tipi, kucuk=False):
    """Her bina tipi için b < 200 ve b ≥ 200 üreten girdiler (n = 0,30 / 0,25)."""
    if bina_tipi == "Konut":
        return (12, 3) if kucuk else (60, 3)
    if bina_tipi.startswith(("İş Merkezi", "Kamu")):
        return (1200, None) if kucuk else (4800, None)
    if bina_tipi.startswith("Otel"):
        return (120, None) if kucuk else (400, None)
    if bina_tipi == "Hastane":
        return (40, None) if kucuk else (200, None)
    if bina_tipi == "Katlı Otopark":
        return (100, 20) if kucuk else (300, 60)
    return (None, None)


TAM_KAPI = [(800, "Teleskopik Otomatik"), (800, "Merkezden Açılan Oto."),
            (900, "Teleskopik Otomatik"), (900, "Merkezden Açılan Oto."),
            (1100, "Teleskopik Otomatik"), (1100, "Merkezden Açılan Oto."),
            (1300, "Teleskopik Otomatik"), (1300, "Merkezden Açılan Oto.")]


def tek_senaryolar():
    s = []
    # a) her bina tipi — küçük ve büyük nüfus (n katsayısının iki kolu)
    for bt, veri in T.TABLO_10.items():
        for kucuk in (True, False):
            h1, h2 = _nufus(bt, kucuk)
            if h1 is None:
                continue
            g = dict(bina_tipi=bt, bina_yuksekligi=18.0, yapi_yuksekligi=24.0, N=6, h=3.0,
                     hizli1=h1, hizli2=h2, P=10, kapi_genisligi=900,
                     kapi_tipi="Merkezden Açılan Oto.")
            if veri["k_tipi"] is None:
                g["manuel_k"] = 0.12
            if veri["hiz_grubu"] is None:
                g["manuel_V"] = 1.6
            s.append((f"bina={bt[:22]} b{'<' if kucuk else '≥'}200", g))
    # b) tüm kapasiteler  (15 kişi = MMO örnek istisnası dâhil)
    for P in T.GECERLI_KAPASITELER:
        s.append((f"P={P} kişi", dict(bina_tipi="Konut", bina_yuksekligi=30.0,
                  yapi_yuksekligi=34.0, N=10, h=3.0, hizli1=50, hizli2=3, P=P,
                  kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")))
    # c) N sınırları  (Tablo-3/5 kapsamı 1…30)
    for N in (1, 2, 3, 9, 10, 14, 15, 19, 20, 29, 30):
        s.append((f"N={N} kat", dict(bina_tipi="Konut", bina_yuksekligi=60.0,
                  yapi_yuksekligi=66.0, N=N, h=3.0, hizli1=40, hizli2=3, P=13,
                  kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")))
    # d) tüm geçerli hızlar  (Tablo-6 tg kademeleri + iki ara değer)
    for V in T.GECERLI_HIZLAR:
        s.append((f"V={V} m/s", dict(bina_tipi="Konut", bina_yuksekligi=45.0,
                  yapi_yuksekligi=50.0, N=15, h=3.0, hizli1=70, hizli2=3, P=16,
                  kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", manuel_V=V)))
    # e-0) bodrum durakları — Tablo-2 durak adedini değiştirir, H/S'yi değiştirmez
    for nb in (0, 1, 2, 5, 10):
        s.append((f"bodrum={nb} durak", dict(bina_tipi="Konut", bina_yuksekligi=39.0,
                  yapi_yuksekligi=46.0, N=12, h=3.0, hizli1=60, hizli2=3, P=13,
                  kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", bodrum=nb)))
    #   bodrum + manuel hız + Tablo-2'si olmayan bina tipi
    s.append(("bodrum + manuel V", dict(bina_tipi="Hastane", bina_yuksekligi=26.0,
              yapi_yuksekligi=34.0, N=8, h=3.3, hizli1=180, P=20, bodrum=3,
              manuel_V=1.6, kapi_genisligi=1300, kapi_tipi="Merkezden Açılan Oto.")))
    #   bodrum eşiği: Konut'ta durak 14→15 geçişi hızı 1,6'dan 2,0'a çıkarır
    for nb in (1, 2):
        s.append((f"bodrum eşiği nb={nb}", dict(bina_tipi="Konut", bina_yuksekligi=40.0,
                  yapi_yuksekligi=46.0, N=13, h=3.0, hizli1=60, hizli2=3, P=10,
                  kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", bodrum=nb)))
    # e-1) ARA DEĞERLİ kapı genişlikleri — Tablo-4 (1000/1200) ve Tablo-8 (700)
    for kg in T.KAPI_GENISLIKLERI:
        for kt in ("Teleskopik Otomatik", "Merkezden Açılan Oto."):
            s.append((f"ara kapı {kg} {kt[:10]}", dict(bina_tipi="Konut",
                      bina_yuksekligi=33.0, yapi_yuksekligi=38.0, N=10, h=3.0,
                      hizli1=48, hizli2=3, P=13, kapi_genisligi=kg, kapi_tipi=kt)))
    #   kabin içi kapı — tabloda olan genişlikler
    for kg in (700, 800, 900, 1000, 1100):
        s.append((f"kabin içi {kg}", dict(bina_tipi="Konut", bina_yuksekligi=33.0,
                  yapi_yuksekligi=38.0, N=10, h=3.0, hizli1=48, hizli2=3, P=13,
                  kapi_genisligi=kg, kapi_tipi="Kabin İçi Oto. Kat K.Ç.")))
    # e) tüm tam hesaplanabilir kapı birleşimleri
    for kg, kt in TAM_KAPI:
        s.append((f"kapı {kg} {kt[:12]}", dict(bina_tipi="Otel (4* ve üzeri)",
                  bina_yuksekligi=40.0, yapi_yuksekligi=45.0, N=12, h=3.2,
                  hizli1=260, hizli2=None, P=16, kapi_genisligi=kg, kapi_tipi=kt)))
    # f) yükseklik eşiği — Standart / Yükseltilmiş sınırı (BYKHY md.4)
    for by, yy, ad in ((21.50, 30.50, "eşikte"), (21.51, 30.50, "bina>21,5"),
                       (21.50, 30.51, "yapı>30,5")):
        s.append((f"standart {ad}", dict(bina_tipi="Konut", bina_yuksekligi=by,
                  yapi_yuksekligi=yy, N=7, h=3.0, hizli1=45, hizli2=3, P=10,
                  kapi_genisligi=900, kapi_tipi="Merkezden Açılan Oto.")))
    # g) elle süre girişleri ve elle asansör adedi
    s.append(("elle ta/tk/tg/tp", dict(bina_tipi="Konut", bina_yuksekligi=30.0,
              yapi_yuksekligi=34.0, N=10, h=3.0, hizli1=50, hizli2=3, P=10,
              kapi_genisligi=900, kapi_tipi="Merkezden Açılan Oto.",
              manuel_ta=2.1, manuel_tk=2.7, manuel_tg=5.9, manuel_tp=1.05)))
    s.append(("elle adet=4", dict(bina_tipi="Konut", bina_yuksekligi=30.0,
              yapi_yuksekligi=34.0, N=10, h=3.0, hizli1=50, hizli2=3, P=10,
              kapi_genisligi=900, kapi_tipi="Merkezden Açılan Oto.", manuel_adet=4)))
    # h) ondalık kat yüksekliği ve ondalık oda sayısı
    s.append(("h=2,85 / oda=2,4", dict(bina_tipi="Konut", bina_yuksekligi=28.5,
              yapi_yuksekligi=33.0, N=10, h=2.85, hizli1=48, hizli2=2.4, P=13,
              kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")))
    return s


def coklu_senaryolar():
    s = []
    KAP = [(8, 800), (10, 900), (13, 1100), (16, 1100), (20, 1100), (25, 1300)]
    for n in (1, 2, 3, 4):
        s.append((f"{n} asansör", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
                  yapi_yuksekligi=43.0, N=11, h=3.0, hizli1=44, hizli2=3,
                  asansorler=[dict(P=KAP[i][0], kapi_genisligi=KAP[i][1],
                                   kapi_tipi="Teleskopik Otomatik") for i in range(n)])))
    # farklı durak sayısı (asansör bazında N)
    s.append(("farklı durak", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=43.0, N=11, h=3.0, hizli1=44, hizli2=3,
              asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", durak=12),
                          dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", durak=6),
                          dict(P=13, kapi_genisligi=1100, kapi_tipi="Merkezden Açılan Oto.", durak=4)])))
    # asansör bazında hız ve kat yüksekliği
    s.append(("asansör bazında V/h", dict(bina_tipi="İş Merkezi (Çok Firmalı)",
              bina_yuksekligi=48.0, yapi_yuksekligi=54.0, N=16, h=3.0, hizli1=7200,
              asansorler=[dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", V=2.5),
                          dict(P=20, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", V=3.5, h=3.4)])))
    # Tablo-9'da olmayan bina tipi + manuel k
    s.append(("karma bina, manuel k/V", dict(bina_tipi="Karma Binalar (İşyeri ve Konut)",
              bina_yuksekligi=35.0, yapi_yuksekligi=40.0, N=12, h=3.0, hizli1=None,
              manuel_k=0.13, manuel_V=2.0,
              ek_nufus=[{"aciklama": "Ofis katları", "miktar": 3600,
                         "kalem": "İŞ MERKEZİ — Çalışma alanı"},
                        {"aciklama": "Konut ilk yatak odası", "miktar": 20,
                         "kalem": "KONUT — İlk yatak odası"}],
              asansorler=[dict(P=13, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik"),
                          dict(P=13, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")])))
    # bodrum: ortak ve asansör bazında
    s.append(("çoklu ortak bodrum", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=46.0, N=11, h=3.0, hizli1=44, hizli2=3, bodrum=3,
              asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
                          dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")])))
    s.append(("çoklu asansör bazında bodrum", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=46.0, N=11, h=3.0, hizli1=44, hizli2=3, bodrum=1,
              asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", bodrum=0),
                          dict(P=13, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", bodrum=4),
                          dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik",
                               bodrum=2, durak=8)])))
    # asansör bazında imalatçı süreleri
    s.append(("çoklu manuel süreler", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=43.0, N=11, h=3.0, hizli1=44, hizli2=3,
              asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik",
                               manuel_ta=2.9, manuel_tk=3.4),
                          dict(P=13, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik",
                               manuel_tg=6.2, manuel_tp=1.15),
                          dict(P=16, kapi_genisligi=1300, kapi_tipi="Kabin İçi Oto. Kat K.Ç.",
                               manuel_ta=6.0, manuel_tk=6.0, manuel_tg=5.5, manuel_tp=0.95)])))
    # ara değerli kapılar (Tablo-4 1000/1200, Tablo-8 700)
    s.append(("çoklu ara kapılar", dict(bina_tipi="Konut", bina_yuksekligi=39.98,
              yapi_yuksekligi=43.0, N=11, h=3.0, hizli1=44, hizli2=3,
              asansorler=[dict(P=10, kapi_genisligi=700, kapi_tipi="Teleskopik Otomatik"),
                          dict(P=13, kapi_genisligi=1000, kapi_tipi="Merkezden Açılan Oto."),
                          dict(P=16, kapi_genisligi=1200, kapi_tipi="Teleskopik Otomatik")])))
    # hastane (Tablo-2'de yok → manuel V)
    s.append(("hastane, manuel V", dict(bina_tipi="Hastane", bina_yuksekligi=26.0,
              yapi_yuksekligi=31.0, N=8, h=3.3, hizli1=180, manuel_V=1.6,
              asansorler=[dict(P=20, kapi_genisligi=1300, kapi_tipi="Merkezden Açılan Oto."),
                          dict(P=25, kapi_genisligi=1300, kapi_tipi="Merkezden Açılan Oto.")])))
    return s


def avan_senaryolar():
    """Her senaryo bir çalışma kitabı; kitap başına en çok 4 asansör."""
    ORT = dict(U=380, kappa=56, eps_max=3, temel_a=26.55, temel_b=16.4, beta=150,
               serit_L=58.5, cubuk_sayisi=4, mk_uzunluk=0, mk_genislik=0)

    def A(**kw):
        t = dict(tanim="A", kapasite=10, V=1.6, eta=0.85, Hk=32.85, kuyu_genisligi=1800,
                 kabin_boyu=1450, kabin_genisligi=1300, gr=17.91, Fmk=350, Fsh=100,
                 Nsc=11, S1=6, L1=32.85, S2=6, L2=3, kablo_tipi="NHXMH FE180")
        t.update(kw)
        return t

    s = []
    # a) tüm kapasiteler (4'erli gruplar)
    kaps = T.GECERLI_KAPASITELER
    for i in range(0, len(kaps), 4):
        grup = kaps[i:i + 4]
        s.append((f"kapasite {grup}", {"ortak": ORT,
                  "asansorler": [A(kapasite=p, tanim=f"{p} kişi") for p in grup]}))
    # b) k1 darbe faktörünün üç kademesi + palanga 1/2
    s.append(("k1 kademeleri", {"ortak": ORT, "asansorler": [
        A(V=0.63, tanim="k1=5"), A(V=1.0, tanim="k1=3"), A(V=1.6, tanim="k1=2"), A(V=2.5, tanim="k1=2")]}))
    s.append(("palanga i=1", {"ortak": ORT, "sabitler": {"i_palanga": 1},
                              "asansorler": [A(tanim="doğrudan askı")]}))
    # b-2) askı ve denge ASANSÖR BAZINDA — dişlili + dişlisiz karışık proje
    s.append(("asansör bazında askı/denge", {"ortak": ORT, "asansorler": [
        A(tanim="2:1 dişlisiz"),
        A(tanim="1:1 dişlili", eta=0.50, i_palanga=1, q_denge=0.40),
        A(tanim="2:1 q=0,45", kapasite=16, q_denge=0.45),
        A(tanim="1:1 q=0,55", kapasite=13, i_palanga=1, q_denge=0.55)]}))
    # b-3) MAKİNE TİPİ × ASKI ORANI — MMO/697 dört birleşimi
    s.append(("makine tipi × askı (MMO)", {"ortak": ORT, "asansorler": [
        A(tanim="dişli 1:1",    makine_tipi="Dişli",    eta=0.50, i_palanga=1),
        A(tanim="dişli 2:1",    makine_tipi="Dişli",    eta=0.50, i_palanga=2),
        A(tanim="dişlisiz 1:1", makine_tipi="Dişlisiz", eta=0.85, i_palanga=1),
        A(tanim="dişlisiz 2:1", makine_tipi="Dişlisiz", eta=0.85, i_palanga=2)]}))
    # b-4) TOPLAM SİSTEM VERİMİ — askı oranı η'yı değiştirmemeli ( Δη yok )
    s.append(("toplam sistem verimi", {"ortak": ORT, "asansorler": [
        A(tanim="dişli 1:1", makine_tipi="Dişli", eta=0.60, i_palanga=1),
        A(tanim="dişlisiz 2:1", makine_tipi="Dişlisiz", eta=0.82, i_palanga=2),
        A(tanim="dişlisiz 2:1 ofis", makine_tipi="Dişlisiz", eta=0.85, i_palanga=2),
        A(tanim="dişlisiz 2:1 katalog", makine_tipi="Dişlisiz", eta=0.78,
          i_palanga=2)]}))
    # b-5) OFİS VARSAYILANLARI — alanlar BOŞ bırakılır.  Program bunları
    #      dosyaya yazmalı ki Excel kendi başına aynı sonucu versin.
    BOS_ORT = dict(temel_a=26.55, temel_b=16.4, serit_L=58.5,
                   mk_uzunluk=0, mk_genislik=0)

    def AB(**kw):
        """Ofis varsayılanına düşen alanları HİÇ vermeyen asansör."""
        t = dict(tanim="A", kapasite=10, V=1.6, eta=0.85, Hk=32.85,
                 kuyu_genisligi=1800, kabin_boyu=1450, kabin_genisligi=1300)
        t.update(kw)
        return t

    s.append(("ofis varsayılanları — alanlar boş", {"ortak": BOS_ORT, "asansorler": [
        AB(tanim="tamamı ofis"),
        AB(tanim="16 kişi — motor otomatik", kapasite=16),
        AB(tanim="ray ezilmiş", gr=23.7),
        AB(tanim="L1 elle", L1=45.5, Nsc=22)]}))
    s.append(("ofis varsayılanı değiştirilmiş", {"ortak": BOS_ORT,
              "sabitler": {"gr": 23.7, "Fmk": 480, "Fsh": 120, "S1": 10, "S2": 10,
                           "L2": 4.5, "L1_pay": 5, "U": 400, "kappa": 58,
                           "eps_max": 4, "beta": 90, "cubuk_sayisi": 6},
              "asansorler": [AB(tanim="yeni ofis standardı"),
                             AB(tanim="25 kişi", kapasite=25, V=2.5)]}))
    s.append(("ofis standardı + asansör bazı", {"ortak": ORT,
              "sabitler": {"i_palanga": 1, "q_denge": 0.42}, "asansorler": [
                  A(tanim="ofis standardı"),
                  A(tanim="ezilmiş", i_palanga=2, q_denge=0.55)]}))
    # c) makine dairesi — kutu işaretli / işaretsiz
    s.append(("makine daireli", {"ortak": dict(ORT, mk_yok=False, mk_uzunluk=4200,
                                               mk_genislik=3100),
                                 "asansorler": [A(), A(kapasite=16)]}))
    s.append(("MRL kutusu işaretli", {"ortak": dict(ORT, mk_yok=True),
                                      "asansorler": [A()]}))
    s.append(("MRL kutusu işaretli ama ölçü var",
              {"ortak": dict(ORT, mk_yok=True, mk_uzunluk=4200, mk_genislik=3100),
               "asansorler": [A()]}))
    # d) topraklama varyasyonları
    s.append(("çubuksuz topraklama", {"ortak": dict(ORT, cubuk_sayisi=0), "asansorler": [A()]}))
    s.append(("β=300, 8 çubuk", {"ortak": dict(ORT, beta=300, cubuk_sayisi=8, serit_L=120),
                                 "asansorler": [A()]}))
    #  d-2) ŞERİT BOYU TÜRETİLEN — ofiste yalnız uzunluk ve genişlik girilir.
    #  Program türettiği boyu GİRİŞ!C13'e yazmalı ki Excel kendi başına aynı
    #  Ry ve Re'yi bulsun.  ( Ofis paftası ölçüleri: 31,05 × 18,90 m )
    TUR_ORT = dict(temel_a=31.05, temel_b=18.9, mk_uzunluk=0, mk_genislik=0)
    s.append(("şerit boyu türetilen — L boş",
              {"ortak": TUR_ORT, "asansorler": [A(tanim="ofis temeli")]}))
    s.append(("şerit boyu türetilen — göz 10 m",
              {"ortak": TUR_ORT, "sabitler": {"goz_araligi": 10},
               "asansorler": [A(tanim="sık karelaj")]}))
    s.append(("şerit boyu türetilen — enine bağ gerekmiyor",
              {"ortak": dict(temel_a=15.0, temel_b=10.0, mk_uzunluk=0, mk_genislik=0),
               "asansorler": [A(tanim="küçük temel")]}))
    # e) elektrik: farklı kesit / uzunluk / gerilim / alüminyum iletken
    s.append(("400 V, alüminyum", {"ortak": dict(ORT, U=400, kappa=35),
                                   "asansorler": [A(S1=10, L1=60), A(S1=16, L1=95, kapasite=20)]}))
    s.append(("kesit yetersiz", {"ortak": ORT, "asansorler": [A(S1=1.5, L1=180, Nsc=18.5)]}))
    # f) Tablo-11 ara değerler + elle Gk / elle Q
    s.append(("Q elle 1125 / Gk elle", {"ortak": ORT, "asansorler": [
        A(kapasite=None, Q_elle=1125, tanim="MMO örneği"),
        A(Gk_elle=740, tanim="imalatçı Gk"),
        A(kapasite=None, Q_elle=900, tanim="ara yük"),
        A(kapasite=None, Q_elle=1400, tanim="ara yük 2")]}))
    # g) uç boyutlar — küçük kabin / uzun kuyu / dişli makine
    s.append(("uç boyutlar", {"ortak": ORT, "asansorler": [
        A(Hk=9.0, kuyu_genisligi=1500, kabin_boyu=1100, kabin_genisligi=1100, tanim="kısa kuyu"),
        A(Hk=70.0, kuyu_genisligi=2650, kabin_boyu=2100, kabin_genisligi=1600, Nsc=18.5, tanim="uzun kuyu"),
        A(eta=0.50, tanim="dişli makine"),
        A(gr=8.9, tanim="T89 ray")]}))
    # h) ofis standardı değiştirilmiş
    s.append(("ofis standardı değişik", {
        "ortak": ORT,
        "sabitler": {"q_denge": 0.45, "gf": 2.0, "Fmt": 120, "kuyu_Dmax": 0,
                     "priz_adedi": 4, "priz_gucu": 250, "cosfi": 0.85,
                     "kuyu_armatur_lm": 2100, "kabin_armatur_lm": 400, "ayd_sutun": 5},
        "asansorler": [A(), A(kapasite=16, V=1.0)]}))
    return s


# =====================================================================
#  KARŞILAŞTIRILACAK HÜCRELER
# =====================================================================
TEK_HUCRE = {
    "C8": "standart", "C15": "p", "C20": "b", "C21": "n_artis", "C22": "B",
    "C23": "V", "C24": "H", "C25": "S", "C26": "ta", "C27": "tk", "C28": "tg",
    "C29": "tp", "C30": "k", "C33": "tv", "C34": "ts", "C35": "TR", "C36": "R",
    "C37": "adet", "C38": "Ieer", "C42": "esik_standart", "C43": "esik_yukseltilmis",
    "C44": "sonuc", "E13": "yuk_kg",
    "H16": "bodrum", "H17": "toplam_seyahat",
}
COKLU_HUCRE = {
    "B8": "standart", "B14": "b", "B15": "n_artis", "B16": "B", "B17": "k",
    "B40": "Res", "B41": "gereken", "B43": "TRes", "B44": "Izul", "B53": "sonuc",
    "H13": "bodrum",
}
COKLU_ASANSOR_SATIR = {27: "p", 28: "H", 29: "S", 30: "ta", 31: "tk", 32: "tg",
                       33: "tp", 34: "tv", 35: "ts", 36: "TR", 37: "R",
                       38: "yuk_kg", 57: "V", 60: "N", 101: "bodrum"}
AVAN_HUCRE = {
    "E6": "Q", "E7": "V", "E8": "q_denge", "E9": "i_palanga", "E10": "eta", "E14": "N_hes", "E15": "Nsc",
    "E21": "Gk", "E24": "Gf", "E26": "P", "E30": "Ga", "E31": "k1", "E34": "Lr",
    "E36": "Mg", "E40": "P1", "E44": "P2", "E48": "PR", "E52": "PK", "E56": "Fs",
    "E63": "kabin_a", "E64": "kabin_b", "E67": "k_kabin", "E68": "eta_kabin",
    "E72": "T_kabin", "E75": "Z_kabin", "E76": "n_kabin",
    "E80": "kuyu_a", "E81": "kuyu_b", "E84": "k_kuyu", "E85": "eta_kuyu",
    "E89": "T_kuyu", "E92": "Z_kuyu", "E93": "n1_kuyu", "E96": "n2_kuyu", "E97": "n_kuyu",
    "E102": "g_motor", "E103": "g_kuyu", "E104": "g_kabin", "E105": "g_priz",
    "E106": "P_kurulu", "E125": "eps1", "E130": "eps2", "E132": "eps",
    "E137": "I", "E138": "Iz",
}
TOPRAKLAMA_HUCRE = {"E7": "A", "E9": "r", "E11": "D", "E15": "Ry", "E21": "Rc",
                    "E25": "Re", "E29": "Re_max"}
MK_HUCRE = {"E10": "k", "E11": "eta", "E15": "T", "E18": "Z", "E19": "n"}


def _oku(yol, sayfa, adresler):
    ws = openpyxl.load_workbook(yol, data_only=True)[sayfa]
    return {a: ws[a].value for a in adresler}


def calistir():
    print("\n\033[1mTEST 1 — EXCEL UYUMU\033[0m"
          "   (girdiler şablona yazılır, LibreOffice yeniden hesaplar, motorla karşılaştırılır)")
    r = Rapor("Excel uyumu")
    if not soffice_yolu():
        r.atla("LibreOffice bulunamadı — bu test yalnız LibreOffice kurulu makinede çalışır.")
        return r

    shutil.rmtree(GECICI, ignore_errors=True)
    giris, cikis = os.path.join(GECICI, "girdi"), os.path.join(GECICI, "cikti")
    os.makedirs(giris, exist_ok=True)

    tek, coklu, avan = tek_senaryolar(), coklu_senaryolar(), avan_senaryolar()
    dosyalar = []
    for i, (_, g) in enumerate(tek):
        p = f"{giris}/tek{i:03d}.xlsx"
        open(p, "wb").write(X.trafik_xlsx("tek", g)); dosyalar.append(p)
    for i, (_, g) in enumerate(coklu):
        p = f"{giris}/cok{i:03d}.xlsx"
        open(p, "wb").write(X.trafik_xlsx("coklu", g)); dosyalar.append(p)
    for i, (_, v) in enumerate(avan):
        p = f"{giris}/avan{i:03d}.xlsx"
        open(p, "wb").write(X.avan_xlsx(v)); dosyalar.append(p)

    print(f"   {len(dosyalar)} çalışma kitabı üretildi "
          f"({len(tek)} tek + {len(coklu)} çoklu + {len(avan)} avan) — "
          "LibreOffice yeniden hesaplıyor…")
    yeniden_hesapla(dosyalar, cikis)

    # ---------------- tek asansör
    for i, (ad, g) in enumerate(tek):
        yol = f"{cikis}/tek{i:03d}.xlsx"
        if not os.path.exists(yol):
            r.kontrol(f"[tek] {ad} dosya üretilemedi", False)
            continue
        s = TR.hesapla_tek(g)
        if s.get("hata"):
            continue
        x = _oku(yol, "HESAPLAMA", list(TEK_HUCRE))
        for adres, anahtar in TEK_HUCRE.items():
            r.esit(f"[tek] {ad} · HESAPLAMA!{adres} ({anahtar})", x[adres], s["ozet"][anahtar])
        pafta = _oku(yol, "PAFTA", ["A33"])
        r.esit(f"[tek] {ad} · PAFTA!A33 (sonuç)", pafta["A33"], s["ozet"]["sonuc"])
        for e in hata_hucresi_ara(yol):
            r.kontrol(f"[tek] {ad} · Excel hata hücresi", False, e)

    # ---------------- çoklu asansör
    for i, (ad, g) in enumerate(coklu):
        yol = f"{cikis}/cok{i:03d}.xlsx"
        if not os.path.exists(yol):
            r.kontrol(f"[çoklu] {ad} dosya üretilemedi", False)
            continue
        s = TR.hesapla_coklu(g)
        if s.get("hata"):
            continue
        x = _oku(yol, "ÇOKLU ASANSÖR", list(COKLU_HUCRE))
        for adres, anahtar in COKLU_HUCRE.items():
            r.esit(f"[çoklu] {ad} · {adres} ({anahtar})", x[adres], s["ozet"][anahtar])
        kolon = "BCDE"
        adr = [f"{kolon[j]}{sat}" for j in range(len(s["asansorler"]))
               for sat in COKLU_ASANSOR_SATIR]
        xa = _oku(yol, "ÇOKLU ASANSÖR", adr)
        for j, asn in enumerate(s["asansorler"]):
            for sat, anahtar in COKLU_ASANSOR_SATIR.items():
                r.esit(f"[çoklu] {ad} · {kolon[j]}{sat} ({anahtar})",
                       xa[f"{kolon[j]}{sat}"], asn[anahtar])
        pc = _oku(yol, "PAFTA-COKLU", ["A29"])
        r.esit(f"[çoklu] {ad} · PAFTA-COKLU!A29", pc["A29"], s["ozet"]["sonuc"])
        for e in hata_hucresi_ara(yol):
            r.kontrol(f"[çoklu] {ad} · Excel hata hücresi", False, e)

    # ---------------- avan
    for i, (ad, v) in enumerate(avan):
        yol = f"{cikis}/avan{i:03d}.xlsx"
        if not os.path.exists(yol):
            r.kontrol(f"[avan] {ad} dosya üretilemedi", False)
            continue
        s = AV.hesapla(v)
        for j, a in enumerate(s["asansorler"]):
            if not a.get("aktif"):
                continue
            x = _oku(yol, f"{j+1} NOLU ASANSÖR", list(AVAN_HUCRE))
            for adres, anahtar in AVAN_HUCRE.items():
                r.esit(f"[avan] {ad} · A{j+1}!{adres} ({anahtar})", x[adres], a["ozet"][anahtar])
        tp = s["topraklama"]
        if tp.get("aktif"):
            x = _oku(yol, "TOPRAKLAMA", list(TOPRAKLAMA_HUCRE))
            for adres, anahtar in TOPRAKLAMA_HUCRE.items():
                bek = tp[anahtar]
                if bek is None:
                    continue
                r.esit(f"[avan] {ad} · TOPRAKLAMA!{adres} ({anahtar})", x[adres], bek)
        mk = s["makine_dairesi"]
        if mk.get("aktif"):
            x = _oku(yol, "MK.DAİRESİ AYD.", list(MK_HUCRE))
            for adres, anahtar in MK_HUCRE.items():
                r.esit(f"[avan] {ad} · MK!{adres} ({anahtar})", x[adres], mk[anahtar])
        for e in hata_hucresi_ara(yol):
            r.kontrol(f"[avan] {ad} · Excel hata hücresi", False, e)

    shutil.rmtree(GECICI, ignore_errors=True)
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
