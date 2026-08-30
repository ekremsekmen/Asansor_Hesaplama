# -*- coding: utf-8 -*-
"""
TEST 2  —  KENAR DURUMLAR VE TABLO SINIRLARI

Excel'e ihtiyaç duymaz; motorun kendi kurallarını sınar:
tablo sınırları, yuvarlama kuralları, kapsam dışı girdiler, hata mesajları.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import avan as AV, tables as T, traffic as TR   # noqa: E402
from engine.steps import excel_round, tavana_yuvarla, yukari_yuvarla, tr as TRS  # noqa: E402
from testler.ortak import Rapor                              # noqa: E402

TEMEL = dict(bina_tipi="Konut", bina_yuksekligi=39.98, yapi_yuksekligi=43, N=11,
             hizli1=44, hizli2=3, h=3, P=10, kapi_genisligi=900,
             kapi_tipi="Merkezden Açılan Oto.")
ORT = dict(U=380, kappa=56, eps_max=3, temel_a=26.55, temel_b=16.4, beta=150,
           serit_L=58.5, cubuk_sayisi=4, mk_uzunluk=0, mk_genislik=0)
AS = dict(tanim="A", kapasite=10, V=1.6, eta=0.85, Hk=32.85, kuyu_genisligi=1800,
          kabin_boyu=1450, kabin_genisligi=1300, gr=17.91, Fmk=350, Fsh=100,
          Nsc=11, S1=6, L1=32.85, S2=6, L2=3, kablo_tipi="NHXMH FE180")


def g(**kw):
    d = dict(TEMEL)
    d.update(kw)
    return d


def calistir():
    print("\n\033[1mTEST 2 — KENAR DURUMLAR VE TABLO SINIRLARI\033[0m")
    r = Rapor("Kenar durumlar")

    # ---------------------------------------------------- yuvarlama kuralları
    # Excel ROUND yarımı YUKARI yuvarlar; Python'un round() bankacı yuvarlaması yapar.
    for x, b, bek in ((865, -1, 870), (875, -1, 880), (2.5, 0, 3), (3.5, 0, 4),
                      (-2.5, 0, -3), (0.125, 2, 0.13)):
        r.esit(f"excel_round({x},{b})", excel_round(x, b), bek)
    for x, k, bek in ((63921.0, 10, 63930), (63930.0, 10, 63930), (0.1, 10, 10)):
        r.esit(f"tavana_yuvarla({x},{k})", tavana_yuvarla(x, k), bek)
    for x, bek in ((3.0001, 4), (3.0, 3), (2.9999, 3)):
        r.esit(f"yukari_yuvarla({x})", yukari_yuvarla(x, 0), bek)

    # ---------------------------------------------------- Türkçe sayı biçimi
    r.esit("tr(1234.5)", TRS(1234.5), "1.234,50")
    r.esit("tr(0.075, 4)", TRS(0.075, 4), "0,0750")
    r.esit("tr(None)", TRS(None), "—")

    # ---------------------------------------------------- Tablo-3 / Tablo-5
    # Kapalı formüller MMO/697 tablolarıyla örtüşmeli, sınır dışında None dönmeli.
    r.esit("H(N=1,P=10)", T.tablo3_H(1, 10), 1.0)
    r.esit("S(N=1,P=10)", T.tablo5_S(1, 10), 1.0)
    r.kontrol("H(N=31) kapsam dışı", T.tablo3_H(31, 10) is None)
    r.kontrol("H(P=35) kapsam dışı", T.tablo3_H(10, 35) is None)
    r.kontrol("H(P=5) kapsam dışı", T.tablo3_H(10, 5) is None)
    r.kontrol("S artan P ile artmalı", T.tablo5_S(10, 20) > T.tablo5_S(10, 10))
    r.kontrol("H ≤ N olmalı", all(T.tablo3_H(n, 10) <= n for n in range(1, 31)))
    r.kontrol("S ≤ N olmalı", all(T.tablo5_S(n, 10) <= n + 1e-9 for n in range(1, 31)))

    # ---------------------------------------------------- Tablo-2 hız kademeleri
    for durak, bek in ((2, 1), (9, 1), (10, 1.6), (14, 1.6), (15, 2), (19, 2), (20, 2.5), (40, 2.5)):
        r.esit(f"Tablo-2 Konut {durak} durak", T.tablo2_min_hiz("Konut", durak), bek)
    for durak, bek in ((5, 1), (6, 1.6), (10, 1.6), (11, 2), (15, 2), (16, 2.5), (19, 2.5), (20, 3.5)):
        r.esit(f"Tablo-2 Büro {durak} durak", T.tablo2_min_hiz("Büro ve İş Merkezi", durak), bek)
    for durak, bek in ((6, 1), (7, 1.6), (10, 1.6), (11, 2), (15, 2), (16, 2.5), (20, 3.5)):
        r.esit(f"Tablo-2 Otel {durak} durak", T.tablo2_min_hiz("Otel", durak), bek)
    r.kontrol("Tablo-2 tanımsız grup → None", T.tablo2_min_hiz(None, 10) is None)

    # ---------------------------------------------------- Tablo-6 tg
    for V, bek in ((0.63, 10), (1, 7), (1.6, 6), (1.75, 5.8875), (2, 5.7),
                   (2.5, 5.5), (3, 5.25), (3.5, 5), (5, 4.5), (6, 4.3)):
        r.esit(f"Tablo-6 tg(V={V})", T.tablo6_tg(V), bek)
    r.esit("1,75 m/s ara değer notu", T.tg_kaynagi(1.75), "Tablo-6 (ara değer — enterpolasyon)")
    r.esit("1,60 m/s tablo değeri", T.tg_kaynagi(1.6), "Tablo-6")

    # ---------------------------------------------------- Tablo-4 / Tablo-8
    r.esit("Tablo-4 900 Merkezden", T.tablo4_ta_tk(900, "Merkezden Açılan Oto."), (2.3, 2.9))
    r.esit("Tablo-4 eşanlamlı ad", T.tablo4_ta_tk(900, "Merkezden Açılan Otomatik"), (2.3, 2.9))
    r.esit("Tablo-4 1300 kabin içi → yok", T.tablo4_ta_tk(1300, "Kabin İçi Oto. Kat K.Ç."), (None, None))
    r.esit("Tablo-4 1200 kabin içi → yok", T.tablo4_ta_tk(1200, "Kabin İçi Oto. Kat K.Ç."), (None, None))
    #  1000 ve 1200 mm MMO Tablo-4'te basılı değildir; komşu satırların TAM ORTASI olmalı
    for kt in ("Teleskopik Otomatik", "Merkezden Açılan Oto."):
        for ara, alt, ust in ((1000, 900, 1100), (1200, 1100, 1300)):
            bek = tuple((T.TABLO_4[alt][kt][j] + T.TABLO_4[ust][kt][j]) / 2 for j in (0, 1))
            r.esit(f"Tablo-4 {ara} {kt[:9]} = ({alt}+{ust})/2", T.tablo4_ta_tk(ara, kt), bek)
    r.esit("Tablo-4 1000 kabin içi = (5+6)/2", T.tablo4_ta_tk(1000, "Kabin İçi Oto. Kat K.Ç."), (5.5, 5.5))
    r.esit("1000 mm ara değer notu", T.tablo4_kaynagi(1000), "Tablo-4 (ara değer — enterpolasyon)")
    r.esit("900 mm tablo değeri", T.tablo4_kaynagi(900), "Tablo-4")
    #  700 mm ISO tablosunun dışında — 800→900 eğiminden dış değerleme
    r.esit("Tablo-8 tp(700) dış değer", T.tablo8_tp(700), 1.3)
    r.esit("Tablo-8 tp(700) = 800 + (800−900)", T.tablo8_tp(700),
           T.TABLO_8[800] + (T.TABLO_8[800] - T.TABLO_8[900]))
    r.kontrol("700 mm kaynağı kapsam dışı diyor", "kapsam dışı" in T.tablo8_kaynagi(700))
    r.esit("800 mm tablo kaynağı", T.tablo8_kaynagi(800), "ISO 8100-32:2020, Tablo 6")
    r.esit("Tablo-8 tp(1200)", T.tablo8_tp(1200), 0.9)
    r.kontrol("tp kapı genişledikçe azalır (monoton)",
              all(T.tablo8_tp(a) >= T.tablo8_tp(b)
                  for a, b in zip(T.KAPI_GENISLIKLERI, T.KAPI_GENISLIKLERI[1:])))
    r.kontrol("ta/tk kapı genişledikçe artar (monoton)",
              all(T.TABLO_4[a]["Teleskopik Otomatik"][j] <= T.TABLO_4[b]["Teleskopik Otomatik"][j]
                  for j in (0, 1)
                  for a, b in zip(T.KAPI_GENISLIKLERI, T.KAPI_GENISLIKLERI[1:])))
    r.kontrol("her genişlik iki tabloda da var (boşluk kalmadı)",
              all(T.tablo8_tp(w) is not None
                  and T.tablo4_ta_tk(w, "Teleskopik Otomatik")[0] is not None
                  for w in T.KAPI_GENISLIKLERI))

    # ---------------------------------------------------- Tablo-7 / Tablo-11
    r.esit("Tablo-7 15 kişi (istisna)", T.tablo7_yuk(15), 1125)
    r.esit("Tablo-7 10 kişi", T.tablo7_yuk(10), 800)
    r.esit("Tablo-11 alt sınır", T.tablo11_Gk(300), 500)
    r.esit("Tablo-11 üst sınır", T.tablo11_Gk(5000), 1900)
    r.esit("Tablo-11 tam nokta 800", T.tablo11_Gk(800), 800)
    r.esit("Tablo-11 ara değer 900", T.tablo11_Gk(900), 880)
    r.kontrol("Tablo-11 monoton artan",
              all(T.tablo11_Gk(q) <= T.tablo11_Gk(q + 50) for q in range(450, 2450, 50)))

    # ---------------------------------------------------- aydınlatma verimi
    # k bir ALT satıra yuvarlanarak okunur (emniyetli taraf)
    r.esit("η(k=0,50) alt sınıra kenetlenir", T.ayd_verim(0.50, 2), 0.23)
    r.esit("η(k=0,79) → 0,60 satırı", T.ayd_verim(0.79, 2), 0.23)
    r.esit("η(k=0,80) → 0,80 satırı", T.ayd_verim(0.80, 2), 0.29)
    r.esit("η(k=9,9) üst satır", T.ayd_verim(9.9, 2), 0.57)
    r.esit("η sütun 5", T.ayd_verim(1.5, 5), 0.36)

    # ---------------------------------------------------- trafik: hata yolları
    r.kontrol("boş girdi çökmez",
              "HESAP HATASI" in (TR.hesapla_tek({"bina_tipi": "Konut"}).get("hata") or ""))
    r.kontrol("geçersiz bina tipi",
              "Bina tipi" in (TR.hesapla_tek({"bina_tipi": "Yok Böyle"}).get("hata") or ""))
    r.kontrol("N=31 → bölgeli hesap uyarısı",
              "30" in (TR.hesapla_tek(g(N=31)).get("hata") or ""))
    #  Boşluklar kapandı: yedi genişliğin tamamı hesaplanabilmeli
    for w in T.KAPI_GENISLIKLERI:
        r.kontrol(f"kapı {w} mm hesaplanabiliyor",
                  TR.hesapla_tek(g(kapi_genisligi=w)).get("hata") is None)
    r.kontrol("1000 mm ara değer uyarısı veriyor",
              any("enterpolasyon" in u for u in TR.hesapla_tek(g(kapi_genisligi=1000))["uyarilar"]))
    r.kontrol("700 mm dış değerleme uyarısı veriyor",
              any("dış değerleme" in u for u in TR.hesapla_tek(g(kapi_genisligi=700))["uyarilar"]))
    r.kontrol("700 mm erişilebilirlik uyarısı veriyor",
              any("TS EN 81-70" in u for u in TR.hesapla_tek(g(kapi_genisligi=700))["uyarilar"]))
    r.kontrol("elle ta/tk girilince ara değer uyarısı susar",
              not any("enterpolasyon" in u for u in
                      TR.hesapla_tek(g(kapi_genisligi=1000, manuel_ta=2.4,
                                       manuel_tk=3.0))["uyarilar"]))
    #  Kabin içi kapı tipi 1200/1300 mm'de tabloda yok → net hata, elle girişle geçer
    for w in (1200, 1300):
        s_ = TR.hesapla_tek(g(kapi_genisligi=w, kapi_tipi="Kabin İçi Oto. Kat K.Ç."))
        r.kontrol(f"kabin içi {w} mm → açıklayıcı hata",
                  "Kabin İçi" in (s_.get("hata") or ""))
        r.kontrol(f"kabin içi {w} mm + elle ta/tk geçer",
                  TR.hesapla_tek(g(kapi_genisligi=w, kapi_tipi="Kabin İçi Oto. Kat K.Ç.",
                                   manuel_ta=6.0, manuel_tk=6.0)).get("hata") is None)
    # ---------------------------------------------------- bodrum durağı
    #  MMO/697 s.14/s.16 : H ve S ana giriş ÜSTÜNDEKİ kat adedi N ile tanımlıdır.
    #  Bodrum durağı H, S ve TR'yi değiştirmez; yalnız Tablo-2 durak adedine ve
    #  toplam seyahat mesafesine girer.
    t0 = TR.hesapla_tek(g(N=13, h=3, manuel_V=1.6))
    t2 = TR.hesapla_tek(g(N=13, h=3, bodrum=2, manuel_V=1.6))
    r.esit("bodrum H'yi değiştirmez", t2["ozet"]["H"], t0["ozet"]["H"])
    r.esit("bodrum S'yi değiştirmez", t2["ozet"]["S"], t0["ozet"]["S"])
    r.esit("bodrum TR'yi değiştirmez (hız sabitken)", t2["ozet"]["TR"], t0["ozet"]["TR"])
    r.esit("durak = N + 1 + Nb", t2["ozet"]["durak"], 16)
    r.esit("bodrumsuz durak = N + 1", t0["ozet"]["durak"], 14)
    r.esit("toplam seyahat = (N+Nb)·h", t2["ozet"]["toplam_seyahat"], 45)
    r.esit("bodrumsuz seyahat = N·h", t0["ozet"]["toplam_seyahat"], 39)
    #  Konut: durak ≤14 → 1,6 m/s ; 15-19 → 2,0 m/s.  Bodrum eşiği aşırır.
    r.esit("bodrum Tablo-2 asgari hızını yükseltir",
           TR.hesapla_tek(g(N=13, h=3, bodrum=2))["ozet"]["V"], 2)
    r.esit("bodrumsuz Tablo-2 asgari hızı",
           TR.hesapla_tek(g(N=13, h=3))["ozet"]["V"], 1.6)
    r.esit("bodrum boş = 0", TR.hesapla_tek(g(bodrum=""))["ozet"]["bodrum"], 0)
    r.esit("bodrum None = 0", TR.hesapla_tek(g(bodrum=None))["ozet"]["bodrum"], 0)
    for kotu in (-1, 2.5, 11, "abc"):
        r.kontrol(f"bodrum {kotu!r} reddedilir",
                  "bodrum" in (TR.hesapla_tek(g(bodrum=kotu)).get("hata") or ""))
    #  Bodrum notu bir YÖNTEM açıklamasıdır: ekranda ( ! ) balonuna girer,
    #  paftaya ise basılır — bu yüzden "aciklamalar" listesinde durur.
    r.kontrol("bodrum açıklaması üretiliyor",
              any("H (Tablo-3)" in n for b in t2["bolumler"] for n in b["aciklamalar"]))
    r.kontrol("bodrum açıklaması uyarı listesine karışmıyor",
              not any("H (Tablo-3)" in n for b in t2["bolumler"] for n in b["notlar"]))
    r.kontrol("bodrumsuzda bodrum açıklaması yok",
              not any("H (Tablo-3)" in n for b in t0["bolumler"]
                      for n in list(b["notlar"]) + list(b["aciklamalar"])))
    #  Nüfus türetimi SONUÇTUR — görünür kalmalı, balona girmemeli
    r.kontrol("nüfus türetimi görünür notlarda",
              any("b = " in n or "→ b" in n for b in t2["bolumler"] for n in b["notlar"]))
    r.kontrol("Tablo-1 kuralı açıklamalarda",
              any("Tablo-1:" in n for b in t2["bolumler"] for n in b["aciklamalar"]))
    #  Her bölümde iki liste de bulunmalı (arayüz ve PDF ikisini de okur)
    r.kontrol("her bölümde iki not listesi var",
              all(isinstance(b.get("notlar"), list) and isinstance(b.get("aciklamalar"), list)
                  for s_ in (t0, t2) for b in s_["bolumler"]))

    # ---------------------------------------------------- erişilebilirlik
    r.kontrol("6 kişi erişilebilirlik uyarısı",
              any("81-70" in u for u in TR.hesapla_tek(g(P=6))["uyarilar"]))
    r.kontrol("10 kişi 900 mm uyarı vermez",
              not any("81-70" in u for u in TR.hesapla_tek(g(P=10, kapi_genisligi=900))["uyarilar"]))
    r.kontrol("6 kişi öneri sıralamasında en iyi seçilmez",
              all(not o.get("onerilen") for o in TR.hesapla_tek(g())["oneriler"]
                  if o["kapasite"] == 6))
    r.kontrol("öneri satırları erişilebilirlik bayrağı taşır",
              all("erisilebilir" in o for o in TR.hesapla_tek(g())["oneriler"]))
    r.kontrol("erisilebilir_mi 8 kişi 800 mm", T.erisilebilir_mi(8, 800))
    r.kontrol("erisilebilir_mi 8 kişi 700 mm değil", not T.erisilebilir_mi(8, 700))
    r.kontrol("erisilebilir_mi 6 kişi değil", not T.erisilebilir_mi(6, 900))

    # ---------------------------------------------------- Kamu binaları
    kamu = TR.hesapla_tek(g(bina_tipi="Kamu Binaları"))
    r.kontrol("kamu %k varsayımı paftada", any("Tablo-9" in u for u in kamu["uyarilar"]))
    r.kontrol("kamu hız varsayımı paftada", any("Tablo-2" in u for u in kamu["uyarilar"]))
    r.esit("kamu %k = İş Merkezi", kamu["ozet"]["k"],
           T.TABLO_9["İş Merkezi"][kamu["ozet"]["standart"]])
    r.kontrol("kamuda manuel k kabul edilir",
              TR.hesapla_tek(g(bina_tipi="Kamu Binaları", manuel_k=0.13))["ozet"]["k"] == 0.13)

    # ---------------------------------------------------- Tablo-7 15 kişi
    r.esit("15 kişi tabloda açık", T.TABLO_7[15], 1125)
    r.esit("15 kişi kaynağı ayrı", T.tablo7_kaynagi(15), "MMO örneği s.53-54 (Tablo-7 dışı)")
    r.esit("16 kişi normal kaynak", T.tablo7_kaynagi(16), "Tablo-7")
    r.kontrol("15 kişi hesaplanabiliyor", TR.hesapla_tek(g(P=15)).get("hata") is None)

    r.kontrol("nüfus yok → uyarı",
              "Nüfus" in (TR.hesapla_tek(g(hizli1=None, hizli2=None)).get("hata") or ""))
    r.kontrol("Tablo-9 varken manuel k reddedilir",
              "manuel k girilemez" in (TR.hesapla_tek(g(manuel_k=0.2)).get("hata") or ""))
    r.kontrol("geçersiz manuel hız reddedilir",
              "hız" in (TR.hesapla_tek(g(manuel_V=1.3)).get("hata") or "").lower())
    r.kontrol("karma bina k'sız hesaplanmaz",
              TR.hesapla_tek(g(bina_tipi="Karma Binalar (İşyeri ve Konut)")).get("hata") is not None)

    # ---------------------------------------------------- trafik: doğru davranış
    s = TR.hesapla_tek(g())
    r.esit("hesap standardı yüksek yapıda", s["ozet"]["standart"], "Yükseltilmiş")
    r.esit("adet = MAX(taşıma, bekleme)", s["ozet"]["adet"],
           int(max(1, s["ozet"]["tasima_adedi"], s["ozet"]["bekleme_adedi"])))
    r.kontrol("Ieer = TR / adet",
              abs(s["ozet"]["Ieer"] - s["ozet"]["TR"] / s["ozet"]["adet"]) < 1e-9)
    r.esit("standart eşiği tam 21,50 m", TR.hesapla_tek(
        g(bina_yuksekligi=21.50, yapi_yuksekligi=30.50))["ozet"]["standart"], "Standart")
    r.esit("21,51 m → Yükseltilmiş", TR.hesapla_tek(
        g(bina_yuksekligi=21.51, yapi_yuksekligi=30.50))["ozet"]["standart"], "Yükseltilmiş")
    r.esit("b<200 → n=0,30", TR.hesapla_tek(g(hizli1=10, hizli2=3))["ozet"]["n_artis"], 0.3)
    r.esit("b≥200 → n=0,25", TR.hesapla_tek(g(hizli1=40, hizli2=4))["ozet"]["n_artis"], 0.25)
    r.esit("elle adet uygulanır", TR.hesapla_tek(g(manuel_adet=5))["ozet"]["adet"], 5)
    r.kontrol("elle adet yetersizse Kabul Edilmez",
              TR.hesapla_tek(g(manuel_adet=1))["ozet"]["sonuc"].startswith("Kabul Edilmez"))
    r.kontrol("öneri tablosu 6 kişiliği önermez",
              all(not x.get("onerilen") for x in s["oneriler"] if x["kapasite"] == 6))
    r.kontrol("öneri tablosunda tam bir öneri var",
              sum(1 for x in s["oneriler"] if x.get("onerilen")) == 1)

    # ---------------------------------------------------- çoklu asansör
    c = dict(bina_tipi="Konut", bina_yuksekligi=39.98, yapi_yuksekligi=43, N=11,
             hizli1=44, hizli2=3, h=3,
             asansorler=[dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
                         dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")])
    s = TR.hesapla_coklu(c)
    r.kontrol("Reş = ΣR", abs(s["ozet"]["Res"] - sum(a["R"] for a in s["asansorler"])) < 1e-9)
    r.kontrol("1/TReş = Σ(1/TR)",
              abs(1 / s["ozet"]["TRes"] - sum(1 / a["TR"] for a in s["asansorler"])) < 1e-9)
    r.kontrol("TReş her TR'den küçük",
              all(s["ozet"]["TRes"] < a["TR"] for a in s["asansorler"]))
    r.kontrol("boş liste → uyarı",
              "en az bir" in (TR.hesapla_coklu(dict(c, asansorler=[])).get("hata") or ""))
    r.kontrol("geçersiz durak reddedilir",
              TR.hesapla_coklu(dict(c, asansorler=[
                  dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", durak=99)
              ])).get("hata") is not None)
    r.kontrol("N grup maksimumu değilse uyarı",
              TR.hesapla_coklu(dict(c, asansorler=[
                  dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik", durak=5),
                  dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", durak=6)
              ])).get("hata") is not None)
    tek1 = TR.hesapla_tek(g(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"))
    cok1 = TR.hesapla_coklu(dict(c, asansorler=[dict(P=10, kapi_genisligi=900,
                                                     kapi_tipi="Teleskopik Otomatik")]))
    r.kontrol("tek ve çoklu aynı asansörde aynı TR'yi verir",
              abs(tek1["ozet"]["TR"] - cok1["asansorler"][0]["TR"]) < 1e-9)

    # ---------------------------------------------------- avan
    a = AV.hesapla({"ortak": ORT, "asansorler": [AS]})["asansorler"][0]["ozet"]
    r.kontrol("P = Gk + Gf", abs(a["P"] - (a["Gk"] + a["Gf"])) < 1e-9)
    r.kontrol("Ga = P + q·Q", abs(a["Ga"] - (a["P"] + 0.5 * a["Q"])) < 1e-9)
    r.kontrol("P1 10 N'a yuvarlanmış", a["P1"] % 10 == 0)
    r.kontrol("kurulu güç = kalemler toplamı",
              abs(a["P_kurulu"] - (a["g_motor"] + a["g_kuyu"] + a["g_kabin"] + a["g_priz"])) < 1e-9)
    r.kontrol("ε = ε1 + ε2", abs(a["eps"] - (a["eps1"] + a["eps2"])) < 1e-9)
    r.kontrol("kuyu armatürü = MAX(n1, n2)", a["n_kuyu"] == max(a["n1_kuyu"], a["n2_kuyu"]))
    for V, k1 in ((0.5, 5), (0.63, 5), (0.7, 3), (1.0, 3), (1.01, 2), (2.5, 2)):
        r.esit(f"k1 (V={V})", AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, V=V)]}
                                         )["asansorler"][0]["ozet"]["k1"], k1)
    r.esit("palanga i=1 → η′ = η",
           AV.hesapla({"ortak": ORT, "asansorler": [AS], "sabitler": {"i_palanga": 1}}
                      )["asansorler"][0]["ozet"]["eta_p"], 0.85)
    r.esit("palanga i=2 → η′ = η − 0,10",
           AV.hesapla({"ortak": ORT, "asansorler": [AS]})["asansorler"][0]["ozet"]["eta_p"], 0.75)
    r.kontrol("Dmax=0 → geometrik kontrol kapalı",
              AV.hesapla({"ortak": ORT, "asansorler": [AS], "sabitler": {"kuyu_Dmax": 0}}
                         )["asansorler"][0]["ozet"]["n2_kuyu"] == 0)
    r.kontrol("tanımsız asansör pasif",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, kapasite=None)]}
                         )["asansorler"][0]["aktif"] is False)
    r.kontrol("Q elle ile Tablo-7 dışı kapasite çalışır",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, kapasite=None, Q_elle=1125)]}
                         )["asansorler"][0]["ozet"]["Q"] == 1125)
    r.kontrol("Gk elle Tablo-11'i geçersiz kılar",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, Gk_elle=740)]}
                         )["asansorler"][0]["ozet"]["Gk"] == 740)
    r.kontrol("motor yetersizse UYGUN DEĞİL",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, Nsc=5)]}
                         )["asansorler"][0]["ozet"]["motor_uygun"] is False)
    kesit = AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, S1=1.5, L1=200)]}
                       )["asansorler"][0]["ozet"]
    r.kontrol("kesit yetersizse ε ve I uyarır", not kesit["eps_uygun"] and not kesit["akim_uygun"])
    r.kontrol("tablo dışı kesitte Iz yok",
              AV.hesapla({"ortak": ORT, "asansorler": [dict(AS, S1=3)]}
                         )["asansorler"][0]["ozet"]["Iz"] is None)

    # topraklama
    t = AV.hesapla({"ortak": ORT, "asansorler": [AS]})["topraklama"]
    r.kontrol("Re paralel bağıntısı",
              abs(t["Re"] - t["Ry"] * t["Rc"] / (t["Ry"] + t["Rc"])) < 1e-9)
    r.kontrol("Re < Ry ve Re < Rç", t["Re"] < t["Ry"] and t["Re"] < t["Rc"])
    t0 = AV.hesapla({"ortak": dict(ORT, cubuk_sayisi=0), "asansorler": [AS]})["topraklama"]
    r.kontrol("çubuk yoksa Re = Ry", abs(t0["Re"] - t0["Ry"]) < 1e-9 and t0["Rc"] is None)
    r.kontrol("temel ölçüsü eksikse pasif",
              AV.hesapla({"ortak": dict(ORT, temel_a=0), "asansorler": [AS]}
                         )["topraklama"]["aktif"] is False)
    r.esit("Re max = UL / IΔn", t["Re_max"], 50 / 0.3)

    # makine dairesi
    r.kontrol("MRL sistemde makine dairesi hesabı yok",
              AV.hesapla({"ortak": ORT, "asansorler": [AS]})["makine_dairesi"]["aktif"] is False)
    mk = AV.hesapla({"ortak": dict(ORT, mk_uzunluk=4200, mk_genislik=3100),
                     "asansorler": [AS]})["makine_dairesi"]
    r.kontrol("makine daireli sistemde hesap yapılır", mk["aktif"] and mk["n"] >= 1)

    # 4 asansör + tesis toplamı
    dort = AV.hesapla({"ortak": ORT, "asansorler": [AS] * 4})
    r.esit("4 asansör aktif", len([x for x in dort["asansorler"] if x["aktif"]]), 4)
    r.kontrol("tesis kurulu gücü = Σ asansör",
              abs(dort["ozet"]["tesis_kurulu_guc"]
                  - sum(x["ozet"]["P_kurulu"] for x in dort["asansorler"] if x["aktif"])) < 1e-9)

    # ---------------------------------------------------- belirlenimcilik
    a1 = TR.hesapla_tek(g())["ozet"]
    a2 = TR.hesapla_tek(g())["ozet"]
    r.kontrol("aynı girdi → aynı sonuç (trafik)", a1 == a2)
    b1 = AV.hesapla({"ortak": ORT, "asansorler": [AS]})["asansorler"][0]["ozet"]
    b2 = AV.hesapla({"ortak": ORT, "asansorler": [AS]})["asansorler"][0]["ozet"]
    r.kontrol("aynı girdi → aynı sonuç (avan)", b1 == b2)

    # ============================================================
    #  ÇOKLU : asansör bazında bodrum ve imalatçı süreleri
    # ============================================================
    def gc(**kw):
        temel = dict(bina_tipi="Konut", bina_yuksekligi=39.98, yapi_yuksekligi=43,
                     N=11, hizli1=44, hizli2=3, h=3)
        asan = kw.pop("asansorler", None) or [
            dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
            dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik")]
        temel.update(kw)
        temel["asansorler"] = asan
        return temel

    c0 = TR.hesapla_coklu(gc())
    r.kontrol("çoklu temel senaryo hatasız", c0.get("hata") is None)
    r.esit("çoklu ortak durak = N+1", c0["ozet"]["durak"], 12)
    c1 = TR.hesapla_coklu(gc(bodrum=3))
    r.esit("çoklu ortak bodrum durak adedine girer", c1["asansorler"][0]["durak_toplam"], 15)
    r.esit("çoklu bodrum H'yi değiştirmez", c1["asansorler"][0]["H"], c0["asansorler"][0]["H"])
    r.esit("çoklu bodrum S'yi değiştirmez", c1["asansorler"][0]["S"], c0["asansorler"][0]["S"])
    c2 = TR.hesapla_coklu(gc(bodrum=1, asansorler=[
        dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik"),
        dict(P=16, kapi_genisligi=1100, kapi_tipi="Teleskopik Otomatik", bodrum=4)]))
    r.esit("A1 ortak bodrumu alır", c2["asansorler"][0]["bodrum"], 1)
    r.esit("A2 kendi bodrumunu alır", c2["asansorler"][1]["bodrum"], 4)
    r.esit("A1 durak toplam", c2["asansorler"][0]["durak_toplam"], 13)
    r.esit("A2 durak toplam", c2["asansorler"][1]["durak_toplam"], 16)
    r.kontrol("çoklu geçersiz bodrum reddedilir",
              "bodrum" in (TR.hesapla_coklu(gc(asansorler=[
                  dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik",
                       bodrum=99)])).get("hata") or ""))
    c3 = TR.hesapla_coklu(gc(asansorler=[
        dict(P=10, kapi_genisligi=900, kapi_tipi="Teleskopik Otomatik",
             manuel_ta=2.9, manuel_tk=3.4, manuel_tg=6.2, manuel_tp=1.15)]))
    a3 = c3["asansorler"][0]
    r.esit("çoklu manuel ta", a3["ta"], 2.9)
    r.esit("çoklu manuel tk", a3["tk"], 3.4)
    r.esit("çoklu manuel tg", a3["tg"], 6.2)
    r.esit("çoklu manuel tp", a3["tp"], 1.15)
    r.esit("çoklu manuel sayısı", a3["elle_sure"], 4)
    r.esit("çoklu manuel kaynağı", a3["kaynak_ta"], "İmalatçı verisi")
    r.kontrol("çoklu manuel süre uyarısı",
              any("imalatçı verisiyle" in u for u in c3["uyarilar"]))
    r.kontrol("çoklu kabin içi 1300 → elle süreyle geçer",
              TR.hesapla_coklu(gc(asansorler=[
                  dict(P=10, kapi_genisligi=1300, kapi_tipi="Kabin İçi Oto. Kat K.Ç.",
                       manuel_ta=6.0, manuel_tk=6.0)])).get("hata") is None)
    r.kontrol("çoklu 6 kişi erişilebilirlik uyarısı",
              any("81-70" in u for u in TR.hesapla_coklu(gc(asansorler=[
                  dict(P=6, kapi_genisligi=800, kapi_tipi="Teleskopik Otomatik")]))["uyarilar"]))
    kamuc = TR.hesapla_coklu(gc(bina_tipi="Kamu Binaları"))
    r.kontrol("çoklu kamu varsayımları paftada",
              sum(1 for u in kamuc["uyarilar"] if "Kamu" in u) >= 2)

    # ============================================================
    #  AVAN : asansör bazında palanga ve denge faktörü
    # ============================================================
    ORTAK_Y = {"U": 380, "kappa": 56, "eps_max": 3, "temel_a": 26.55, "temel_b": 16.4,
               "beta": 150, "serit_L": 58.5, "cubuk_sayisi": 4,
               "mk_uzunluk": 0, "mk_genislik": 0}
    TEMEL_AS = dict(tanim="İnsan", kapasite=13, V=1.6, eta=0.85, Hk=32.85,
                    kuyu_genisligi=1800, kabin_boyu=1450, kabin_genisligi=1300,
                    gr=17.91, Fmk=350, Fsh=100, Nsc=11, S1=6, L1=32.85, S2=6, L2=3,
                    kablo_tipi="NHXMH")

    def av(*asan, **kw):
        return AV.hesapla({"ortak": ORTAK_Y, "asansorler": list(asan), **kw})

    v0 = av(dict(TEMEL_AS))
    v1 = av(dict(TEMEL_AS, i_palanga=1))
    o0, o1 = v0["asansorler"][0]["ozet"], v1["asansorler"][0]["ozet"]
    r.esit("palanga 2 → η′ = η − 0,10", o0["eta_p"], 0.75)
    r.esit("palanga 1 → η′ = η", o1["eta_p"], 0.85)
    r.kontrol("palanga 1 daha küçük motor gücü verir", o1["N_hes"] < o0["N_hes"])
    v2 = av(dict(TEMEL_AS, q_denge=0.45))
    o2 = v2["asansorler"][0]["ozet"]
    r.esit("asansör bazında q kullanılır", o2["Ga"], o2["P"] + 0.45 * o2["Q"])
    r.esit("varsayılan q kullanılır", o0["Ga"], o0["P"] + 0.50 * o0["Q"])
    v3 = av(dict(TEMEL_AS), dict(TEMEL_AS, eta=0.50, i_palanga=1, q_denge=0.40))
    x, y = v3["asansorler"][0]["ozet"], v3["asansorler"][1]["ozet"]
    r.esit("karışık projede A1 η′", x["eta_p"], 0.75)
    r.esit("karışık projede A2 η′", y["eta_p"], 0.50)
    r.esit("karışık projede A2 Ga", y["Ga"], y["P"] + 0.40 * y["Q"])
    v4 = av(dict(TEMEL_AS, i_palanga=9, q_denge=5))
    o4 = v4["asansorler"][0]["ozet"]
    r.esit("geçersiz palanga varsayılana döner", o4["eta_p"], 0.75)
    r.esit("geçersiz q varsayılana döner", o4["Ga"], o4["P"] + 0.50 * o4["Q"])
    r.esit("i kaynağı — asansör bazı", v1["asansorler"][0]["ozet"]["i_kaynak"],
           "GİRİŞ — asansör bazında")
    r.esit("i kaynağı — ofis standardı", o0["i_kaynak"], "SABİTLER B")
    r.esit("q kaynağı — asansör bazı", o2["q_kaynak"], "GİRİŞ — asansör bazında")
    v5 = AV.hesapla({"ortak": ORTAK_Y, "sabitler": {"q_denge": 0.42},
                     "asansorler": [dict(TEMEL_AS), dict(TEMEL_AS, q_denge=0.55)]})
    aa, bb = v5["asansorler"][0]["ozet"], v5["asansorler"][1]["ozet"]
    r.esit("ofis standardı boş kolona uygulanır", aa["Ga"], aa["P"] + 0.42 * aa["Q"])
    r.esit("asansör bazı ofis standardını ezer", bb["Ga"], bb["P"] + 0.55 * bb["Q"])

    # ============================================================
    #  TRAFİK  →  AVAN  tutarlılık köprüsü
    # ============================================================
    t = TR.hesapla_tek(g(N=13, h=3, P=13, manuel_V=1.6))
    kopru = TR.trafik_ozeti(t)
    n_as = len(kopru["asansorler"])
    r.kontrol("köprü asansör listesi doluyor", n_as >= 1)
    r.esit("köprü kapasitesi", kopru["asansorler"][0]["P"], 13)
    r.esit("köprü seyahati", kopru["asansorler"][0]["toplam_seyahat"], 39)

    def kopru_uyari(**kw):
        return av(*[dict(TEMEL_AS, **kw) for _ in range(n_as)], trafik=kopru)["uyarilar"]

    r.kontrol("tutarlı girdide köprü uyarısı yok",
              not any("NOLU ASANSÖR:" in u for u in kopru_uyari(Hk=44.5)))
    r.kontrol("kapasite tutarsızlığı yakalanır",
              any("kapasite" in u for u in kopru_uyari(kapasite=10, Hk=44.5)))
    r.kontrol("hız tutarsızlığı yakalanır",
              any("kabin hızı" in u for u in kopru_uyari(V=2.5, Hk=44.5)))
    r.kontrol("Hk < seyahat yakalanır",
              any("küçük ya da ona eşit" in u for u in kopru_uyari(Hk=30)))
    r.kontrol("dar pay uyarısı",
              any("kuyu dibi + üst boşluk payı yalnız" in u for u in kopru_uyari(Hk=41)))
    r.kontrol("aşırı pay uyarısı",
              any("olağandışı büyük" in u for u in kopru_uyari(Hk=60)))
    r.kontrol("adet uyuşmazlığı yakalanır",
              any("adet asansör veriyor" in u for u in
                  av(dict(TEMEL_AS, Hk=44.5),
                     trafik={"asansorler": [{"P": 13, "V": 1.6}, {"P": 13, "V": 1.6}]})["uyarilar"]))
    r.kontrol("köprü yoksa uyarı da yok",
              not any("NOLU ASANSÖR:" in u for u in av(dict(TEMEL_AS))["uyarilar"]))
    for bozuk in (None, "metin", 5, [], {"asansorler": "x"}):
        r.kontrol(f"bozuk köprü {bozuk!r} çökmez",
                  isinstance(av(dict(TEMEL_AS), trafik=bozuk).get("uyarilar"), list))

    # ============================================================
    #  MAKİNE TİPİ × ASKI ORANI  ve  TOPLAM SİSTEM VERİMİ
    # ============================================================
    #  MMO/697 s.21: dişlisiz 0,85 · dişli 0,50   —   §2.4: palangalı η − 0,10
    r.esit("MMO makine verimi — dişlisiz", T.makine_verimi("Dişlisiz"), 0.85)
    r.esit("MMO makine verimi — dişli", T.makine_verimi("Dişli"), 0.50)
    r.kontrol("tanınmayan makine tipi None", T.makine_verimi("Hidrolik") is None)
    r.esit("askı metni 1", T.aski_orani_metni(1), "1:1")
    r.esit("askı metni 2", T.aski_orani_metni(2), "2:1")

    def eta_p(**kw):
        return av(dict(TEMEL_AS, **kw))["asansorler"][0]["ozet"]["eta_p"]

    for tip, i, bek in (("Dişli", 1, 0.50), ("Dişli", 2, 0.40),
                        ("Dişlisiz", 1, 0.85), ("Dişlisiz", 2, 0.75)):
        r.esit(f"MMO {tip} {T.aski_orani_metni(i)} → η′",
               eta_p(makine_tipi=tip, eta=T.makine_verimi(tip), i_palanga=i), bek)
    #  Motor GÜCÜ askı oranından yalnız verim üzerinden etkilenir
    n11 = av(dict(TEMEL_AS, makine_tipi="Dişlisiz", eta=0.85,
                  i_palanga=1))["asansorler"][0]["ozet"]["N_hes"]
    n21 = av(dict(TEMEL_AS, makine_tipi="Dişlisiz", eta=0.85,
                  i_palanga=2))["asansorler"][0]["ozet"]["N_hes"]
    r.kontrol("2:1 daha büyük motor gerektiriyor ( yalnız verim farkı )", n21 > n11)
    r.esit("oran tam olarak η′ oranı kadar", n21 / n11, 0.85 / 0.75, tol=1e-9)

    #  TOPLAM sistem verimi: palanga düşüşü İKİNCİ KEZ uygulanmamalı
    r.esit("toplam verim 0,82 · 2:1 → η′ = 0,82",
           eta_p(makine_tipi="Dişlisiz", eta=0.82, i_palanga=2, toplam_verim=True), 0.82)
    r.esit("toplam verim 0,60 · 1:1 → η′ = 0,60",
           eta_p(makine_tipi="Dişli", eta=0.60, i_palanga=1, toplam_verim=True), 0.60)
    r.esit("toplam verim işaretsiz 0,82 · 2:1 → η′ = 0,72",
           eta_p(makine_tipi="Dişlisiz", eta=0.82, i_palanga=2), 0.72)
    #  Excel'den "Evet"/"Hayır" metni de kabul edilmeli
    r.esit("Excel 'Evet' metni kabul ediliyor",
           eta_p(makine_tipi="Dişlisiz", eta=0.82, i_palanga=2, toplam_verim="Evet"), 0.82)
    r.esit("Excel 'Hayır' metni kabul ediliyor",
           eta_p(makine_tipi="Dişlisiz", eta=0.82, i_palanga=2, toplam_verim="Hayır"), 0.72)
    #  Uyarılar
    v_t = av(dict(TEMEL_AS, makine_tipi="Dişlisiz", eta=0.82, i_palanga=2,
                  toplam_verim=True))["asansorler"][0]["bolumler"][0]
    r.kontrol("toplam verim notu paftada",
              any("TOPLAM SİSTEM VERİMİ" in n for n in v_t["notlar"]))
    r.kontrol("askı oranı açıklaması ( ! ) balonunda",
              any("GÜÇ bağıntısıdır" in n for n in v_t["aciklamalar"]))
    v_s = av(dict(TEMEL_AS, makine_tipi="Dişli", eta=0.70,
                  i_palanga=1))["asansorler"][0]["bolumler"][0]
    r.kontrol("MMO değerinden sapma bildiriliyor",
              any("farklı girilmiştir" in n for n in v_s["notlar"]))
    v_n = av(dict(TEMEL_AS, makine_tipi="Dişli", eta=0.50,
                  i_palanga=1))["asansorler"][0]["bolumler"][0]
    r.kontrol("MMO değeri kullanılınca sapma notu yok",
              not any("farklı girilmiştir" in n for n in v_n["notlar"]))
    #  Askı oranı özette metin olarak da bulunmalı
    r.esit("özette askı metni",
           av(dict(TEMEL_AS, i_palanga=2))["asansorler"][0]["ozet"]["aski"], "2:1")

    # ============================================================
    #  MAKİNE DAİRESİ YOK ( MRL ) İŞARET KUTUSU
    # ============================================================
    def mk(**kw):
        return AV.hesapla({"ortak": dict(ORTAK_Y, **kw),
                           "asansorler": [dict(TEMEL_AS)]})["makine_dairesi"]

    r.kontrol("MRL işaretli → hesap yapılmaz", mk(mk_yok=True)["aktif"] is False)
    r.kontrol("MRL işaretli → açık ifade", "işaretlendi" in mk(mk_yok=True)["uyari"])
    r.kontrol("MRL işaretli, ölçü olsa da hesaplanmaz",
              mk(mk_yok=True, mk_uzunluk=4200, mk_genislik=3100)["aktif"] is False)
    r.kontrol("MRL değil + ölçü var → hesaplanır",
              mk(mk_yok=False, mk_uzunluk=4200, mk_genislik=3100)["aktif"] is True)
    r.kontrol("MRL değil + ölçü yok → açık uyarı",
              "ÖLÇÜLERİ GİRİLMEDİ" in (mk(mk_yok=False).get("uyari") or ""))
    #  Kutu hiç gönderilmemişse ESKİ davranış korunur ( eski proje dosyaları )
    r.kontrol("kutu yokken ölçüsüz → MRL kabul edilir", mk()["aktif"] is False)
    r.kontrol("kutu yokken ölçü varsa → hesaplanır",
              mk(mk_uzunluk=4200, mk_genislik=3100)["aktif"] is True)
    for ham in ("Evet", "evet", True, "1"):
        r.kontrol(f"MRL {ham!r} doğru okundu", mk(mk_yok=ham)["aktif"] is False)
    for ham in ("Hayır", "hayir", False, ""):
        r.kontrol(f"MRL {ham!r} → ölçü aranıyor",
                  "ÖLÇÜLERİ GİRİLMEDİ" in (mk(mk_yok=ham).get("uyari") or "")
                  or mk(mk_yok=ham)["aktif"] is False)

    # ==================================================================
    #  v1.6 — MANUEL k  ( tek ve çoklu yolda AYNI davranış )
    # ==================================================================
    _gk = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 44, "hizli2": 3,
           "asansorler": [{"P": 10, "kapi_genisligi": 900,
                           "kapi_tipi": "Teleskopik Otomatik"},
                          {"P": 16, "kapi_genisligi": 1100,
                           "kapi_tipi": "Teleskopik Otomatik"}]}
    r.kontrol("çoklu: manuel k yokken hesap yapılıyor",
              not TR.hesapla_coklu(dict(_gk)).get("hata"))
    r.kontrol("çoklu: Tablo-9 varken manuel k reddediliyor",
              "manuel k girilemez" in (TR.hesapla_coklu(
                  dict(_gk, manuel_k=0.08)).get("hata") or ""))
    _gt = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "P": 10,
           "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik"}
    r.kontrol("tek: Tablo-9 varken manuel k reddediliyor",
              "manuel k girilemez" in (TR.hesapla_tek(
                  dict(_gt, manuel_k=0.08)).get("hata") or ""))
    #  Kamu binasında manuel k GEÇERLİDİR ( Tablo-9'da kamu yok )
    _gkamu = dict(_gk, bina_tipi="Kamu Binaları", hizli1=5280, hizli2="")
    _rk = TR.hesapla_coklu(dict(_gkamu, manuel_k=0.08))
    r.kontrol("çoklu: kamu binasında manuel k kabul ediliyor",
              not _rk.get("hata") and abs(_rk["ozet"]["k"] - 0.08) < 1e-9)

    # ==================================================================
    #  v1.6 — OFİS VARSAYILANLARI, OTOMATİK MOTOR GÜCÜ, L1 TÜRETMESİ
    # ==================================================================
    O_ORT = {"temel_a": 26.55, "temel_b": 16.4, "serit_L": 58.5, "mk_yok": True}
    O_AS = {"tanim": "A", "kapasite": 10, "V": 1.6, "eta": 0.85, "Hk": 38.5,
            "kuyu_genisligi": 1800, "kabin_boyu": 1450, "kabin_genisligi": 1300,
            "i_palanga": 2, "makine_tipi": "Dişlisiz"}

    def av(as_ek=None, sabit=None, ortak_ek=None):
        o = dict(O_ORT); o.update(ortak_ek or {})
        a = dict(O_AS);  a.update(as_ek or {})
        return AV.hesapla({"ortak": o, "asansorler": [a], "sabitler": sabit or {}})

    #  Boş bırakılan malzeme alanları ofis varsayılanından gelir
    t = av()
    r.kontrol("boş alanlarla hesap yapılıyor", t["asansorler"][0]["aktif"] is True)
    oz = t["asansorler"][0]["ozet"]
    r.esit("kablo tipi ofis varsayılanından", oz["kablo_tipi"], "NHXMH FE180")
    r.esit("S1 ofis varsayılanından", oz["S1"], 6)
    r.esit("L1 = Hk + ofis payı", round(oz["L1"], 4), round(38.5 + 3.5, 4))

    #  Ofis varsayılanı değiştirilince hesap da değişir
    t2 = av(sabit={"S1": 10, "L1_pay": 5})
    r.esit("ofis S1 değişince kullanılan da değişti", t2["asansorler"][0]["ozet"]["S1"], 10)
    r.esit("ofis L1 payı değişince L1 değişti",
           round(t2["asansorler"][0]["ozet"]["L1"], 4), round(38.5 + 5, 4))

    #  Asansör bazında ezme, ofis varsayılanını yener
    r.esit("asansör bazında S1 ofis değerini eziyor",
           av(as_ek={"S1": 16}, sabit={"S1": 10})["asansorler"][0]["ozet"]["S1"], 16)
    r.esit("asansör bazında L1 ofis türetmesini eziyor",
           av(as_ek={"L1": 51.5})["asansorler"][0]["ozet"]["L1"], 51.5)
    r.esit("asansör bazında kablo tipi eziliyor",
           av(as_ek={"kablo_tipi": "N2XH"})["asansorler"][0]["ozet"]["kablo_tipi"], "N2XH")

    #  Geçersiz ofis değeri yok sayılır, varsayılana dönülür ve bildirilir
    t3 = av(sabit={"gr": -5})
    r.kontrol("geçersiz ofis değeri reddedildi",
              any("gr" in x for x in t3["sabitler"]["_reddedilen"]))
    r.esit("reddedilince varsayılana dönüldü", t3["sabitler"]["gr"], 17.91)

    #  Ortak alanlar ( U / κ / εmax / β / çubuk adedi ) da ofis varsayılanından
    r.kontrol("ortak alanlar boşken hesap yapılıyor",
              av(ortak_ek={"U": "", "kappa": "", "eps_max": "",
                           "beta": "", "cubuk_sayisi": ""})["topraklama"]["aktif"] is True)
    r.esit("β boşken ofis varsayılanı kullanıldı",
           round(av(ortak_ek={"beta": ""})["ozet"]["Re"], 4),
           round(av(ortak_ek={"beta": 150})["ozet"]["Re"], 4))

    #  β ve çubuk adedi ofis standardına taşındı ( v1.7 ) — avan panelinde
    #  artık alan yok, motor değeri ofis varsayılanından almalı ve ofis
    #  değeri değişince hesap da değişmeli.
    _tb = lambda ek=None, sab=None: av(ortak_ek=ek, sabit=sab)["ozet"]["Re"]
    r.kontrol("β alanı hiç gönderilmese de topraklama hesaplanıyor",
              av(ortak_ek={"beta": "", "cubuk_sayisi": ""})["topraklama"]["aktif"] is True)
    r.esit("β boşken ofis varsayılanı ( 150 ) kullanılıyor",
           round(_tb({"beta": ""}), 4), round(_tb({"beta": 150}), 4))
    r.esit("çubuk adedi boşken ofis varsayılanı ( 4 ) kullanılıyor",
           round(_tb({"cubuk_sayisi": ""}), 4), round(_tb({"cubuk_sayisi": 4}), 4))
    r.kontrol("ofis β'sı değişince topraklama direnci değişiyor",
              abs(_tb({"beta": ""}, {"beta": 90}) - _tb({"beta": ""})) > 1e-6)
    r.kontrol("ofis çubuk adedi değişince direnç değişiyor",
              abs(_tb({"cubuk_sayisi": ""}, {"cubuk_sayisi": 8})
                  - _tb({"cubuk_sayisi": ""})) > 1e-6)

    #  Nsç — standart kademeden otomatik seçim
    r.esit("motor kademesi: 13,33 kW → 15", T.motor_sec(13.33), 15.0)
    r.esit("motor kademesi: tam eşit değer kendisi", T.motor_sec(11.0), 11.0)
    r.esit("motor kademesi: küçük güç → en alt kademe", T.motor_sec(0.4), 2.2)
    r.kontrol("motor kademesi: hesap yoksa None", T.motor_sec(None) is None)
    r.kontrol("motor kademesi: liste üstü → None", T.motor_sec(9999) is None)
    o16 = av(as_ek={"kapasite": 16})["asansorler"][0]["ozet"]
    r.esit("16 kişilik asansöre 15 kW seçildi", o16["Nsc"], 15.0)
    r.kontrol("otomatik seçim motor kontrolünü geçiyor", o16["motor_uygun"] is True)
    r.kontrol("otomatik seçim hesaplanan güçten büyük", o16["Nsc"] >= o16["N_hes"])
    #  Elle girilen küçük değer korunur ama UYGUN DEĞİL der ( Excel'deki durum )
    o16e = av(as_ek={"kapasite": 16, "Nsc": 11})["asansorler"][0]["ozet"]
    r.esit("elle girilen Nsç korunuyor", o16e["Nsc"], 11)
    r.kontrol("elle girilen küçük Nsç uygun değil", o16e["motor_uygun"] is False)

    #  girdileri_coz — XLSX'e yazılacak çözülmüş girdi
    c = AV.girdileri_coz({"ortak": dict(O_ORT), "asansorler": [dict(O_AS)],
                          "sabitler": {}})
    for anahtar, beklenen in (("gr", 17.91), ("Fmk", 350), ("Fsh", 100),
                              ("S1", 6), ("S2", 6), ("L2", 3),
                              ("kablo_tipi", "NHXMH FE180"), ("L1", 42.0),
                              ("Nsc", 11.0)):
        r.esit(f"çözülmüş girdi {anahtar}", c["asansorler"][0][anahtar], beklenen)
    for anahtar, beklenen in (("U", 380), ("kappa", 56), ("eps_max", 3),
                              ("beta", 150), ("cubuk_sayisi", 4)):
        r.esit(f"çözülmüş ortak {anahtar}", c["ortak"][anahtar], beklenen)
    r.kontrol("çözme işlemi özgün girdiyi bozmuyor", "gr" not in O_AS)

    # ==================================================================
    #  v1.7 — GEÇERSİZ GİRDİ YOLLARI
    #  Bu altı bulgu bir dış denetimde ortaya çıktı: hesap "normal" girdilerde
    #  Excel ile birebir tutuyordu, ama geçersiz girdi yollarında program
    #  yanlışlıkla "uygun" sonucu verebiliyordu.  Her biri için kalıcı test.
    # ==================================================================
    _gt = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "P": 10,
           "kapi_genisligi": 900, "kapi_tipi": "Merkezden Açılan Oto."}
    _gc = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 44, "hizli2": 3,
           "asansorler": [{"P": 10, "kapi_genisligi": 900,
                           "kapi_tipi": "Teleskopik Otomatik"},
                          {"P": 16, "kapi_genisligi": 1100,
                           "kapi_tipi": "Teleskopik Otomatik"}]}

    #  1) MANUEL SÜRELER  —  0 / negatif / saçma büyük değer reddedilmeli.
    #     Dördü de 0 iken TR = 24,5 sn çıkıyor, ts = −1,88 sn gibi imkânsız bir
    #     ara değer oluşuyor ve 44 daireli bina 1 asansörle "yeterli" görünüyordu.
    r.kontrol("tek: dört manuel süre de 0 → reddediliyor",
              bool(TR.hesapla_tek(dict(_gt, manuel_ta=0, manuel_tk=0,
                                       manuel_tg=0, manuel_tp=0)).get("hata")))
    for _alan in ("manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp"):
        for _d in (0, -5):
            r.kontrol(f"tek: {_alan} = {_d} reddediliyor",
                      bool(TR.hesapla_tek(dict(_gt, **{_alan: _d})).get("hata")))
    r.kontrol("tek: manuel ta = 999 s reddediliyor",
              bool(TR.hesapla_tek(dict(_gt, manuel_ta=999)).get("hata")))
    r.kontrol("tek: makul manuel süre KABUL ediliyor",
              not TR.hesapla_tek(dict(_gt, manuel_ta=2.9)).get("hata"))
    _v = dict(_gc)
    _v["asansorler"] = [dict(_gc["asansorler"][0], manuel_tg=-5), _gc["asansorler"][1]]
    r.kontrol("çoklu: asansör bazında negatif süre reddediliyor",
              "ASANSÖR-1" in (TR.hesapla_coklu(_v).get("hata") or ""))
    _v["asansorler"] = [dict(_gc["asansorler"][0], manuel_ta=2.9), _gc["asansorler"][1]]
    r.kontrol("çoklu: makul manuel süre KABUL ediliyor",
              not TR.hesapla_coklu(_v).get("hata"))

    #  2) ÇOKLU HESAP  —  bina girdileri tek asansör hesabıyla AYNI denetimden
    #     geçmeli.  ( h = −3 m ile "Yükseltilmiş kriteri karşılanıyor" çıkıyordu. )
    for _ad, _ek in (("h = -3", {"h": -3}), ("h = 0", {"h": 0}), ("h = 99", {"h": 99}),
                     ("bina yüksekliği boş", {"bina_yuksekligi": ""}),
                     ("yapı yüksekliği boş", {"yapi_yuksekligi": ""})):
        _rc = TR.hesapla_coklu(dict(_gc, **_ek))
        _rt = TR.hesapla_tek(dict(_gt, **_ek))
        r.kontrol(f"çoklu: {_ad} reddediliyor", bool(_rc.get("hata")))
        r.kontrol(f"tek: {_ad} reddediliyor", bool(_rt.get("hata")))
    r.kontrol("çoklu: normal girdi hâlâ hesaplanıyor",
              not TR.hesapla_coklu(dict(_gc)).get("hata"))

    #  3) BELİRSİZ SAYI  —  "1.200" bin iki yüz mü, bir virgül iki mi?
    #     Sessizce 1,2 okunuyordu: 1.200 daireli binada asansör adedi 41 → 2.
    import main as _M
    for _ham in ("1.200", "1,200", "2.500", "12.345", "1,000", "100,000", "-1.500"):
        r.kontrol(f"belirsiz sayı reddediliyor: {_ham!r}", _M._sayi(_ham) is None)
        r.kontrol(f"belirsiz olarak işaretleniyor: {_ham!r}", _M.belirsiz_sayi_mi(_ham))
    #  Sıfırla başlayan ondalıklar BELİRSİZ DEĞİLDİR: binlik ayracı sıfırdan
    #  sonra gelmez.  "0,075" ( manuel k = %7,5 ) geçerli kalmalıdır.
    for _ham, _bek in (("1200", 1200), ("39,98", 39.98), ("39.98", 39.98),
                       ("1.234,56", 1234.56), ("1,234.56", 1234.56),
                       ("1.2", 1.2), ("0.5", 0.5), ("1.20", 1.2),
                       ("0,075", 0.075), ("0.075", 0.075), ("0,750", 0.75)):
        r.kontrol(f"geçerli sayı okunuyor: {_ham!r} = {_bek}",
                  abs((_M._sayi(_ham) or 0) - _bek) < 1e-9)
        r.kontrol(f"belirsiz sayılmıyor: {_ham!r}", not _M.belirsiz_sayi_mi(_ham))

    #  4) AVAN — elle girilen fiziksel büyüklüklerin sınırı
    _oa = {"temel_a": 26.55, "temel_b": 16.4, "serit_L": 58.5, "mk_yok": True}
    _aa = {"tanim": "A", "kapasite": 10, "V": 1.6, "eta": 0.85, "Hk": 38.5,
           "kuyu_genisligi": 1800, "kabin_boyu": 1450, "kabin_genisligi": 1300,
           "i_palanga": 2, "makine_tipi": "Dişlisiz"}

    def _av(ek=None, sab=None):
        a = dict(_aa); a.update(ek or {})
        return AV.hesapla({"ortak": _oa, "asansorler": [a], "sabitler": sab or {}})

    r.kontrol("avan: normal girdi hesaplanıyor", _av()["asansorler"][0]["aktif"] is True)
    for _ad, _ek in (("Q elle = 0", {"Q_elle": 0}), ("Q elle = -500", {"Q_elle": -500}),
                     ("Gk elle = 0", {"Gk_elle": 0}), ("Gk elle = -800", {"Gk_elle": -800}),
                     ("η = 10", {"eta": 10}), ("η = 0", {"eta": 0})):
        r.kontrol(f"avan: {_ad} reddediliyor",
                  _av(_ek)["asansorler"][0]["aktif"] is False)

    #  5) Tablo-11 dışı anma yükü  —  Gk sessizce uç değere sabitlenmemeli
    r.kontrol("avan: Q = 5000 kg ( Tablo-11 dışı ) Gk elle olmadan reddediliyor",
              _av({"Q_elle": 5000})["asansorler"][0]["aktif"] is False)
    r.kontrol("avan: Tablo-11 dışı uyarısı tabloyu adıyla anıyor",
              "Tablo-11" in (_av({"Q_elle": 5000})["asansorler"][0].get("uyari") or ""))
    _t11 = _av({"Q_elle": 5000, "Gk_elle": 2400})["asansorler"][0]
    r.kontrol("avan: Gk elle verilince Tablo-11 dışı yük hesaplanıyor",
              _t11["aktif"] is True and _t11["ozet"]["Gk"] == 2400)
    r.kontrol("avan: Q = 300 kg ( tablo altı ) da reddediliyor",
              _av({"Q_elle": 300})["asansorler"][0]["aktif"] is False)

    #  6) Denge faktörü q  —  q = 1 iken N = 0 kW çıkıp 2,2 kW motor
    #     "uygun" görünüyordu.
    for _q in (0, 1, 1.5, -0.2):
        _rq = _av({"q_denge": _q})
        r.kontrol(f"avan: q = {_q} kullanılmıyor, varsayılana dönülüyor",
                  abs(_rq["asansorler"][0]["ozet"]["q_denge"] - 0.50) < 1e-9)
        r.kontrol(f"avan: q = {_q} için uyarı çıkıyor",
                  any("denge faktörü" in x for x in (_rq.get("uyarilar") or [])))
    r.kontrol("avan: q = 0,45 kabul ediliyor",
              abs(_av({"q_denge": 0.45})["asansorler"][0]["ozet"]["q_denge"] - 0.45) < 1e-9)
    r.kontrol("avan: q = 0,60 kabul ediliyor ama uygulama bandı uyarısı çıkıyor",
              any("bandındadır" in x for x in (_av({"q_denge": 0.60}).get("uyarilar") or [])))

    #  Aralık dışı ofis alanları SESSİZ düşmemeli
    for _ad, _ek in (("gr = -17", {"gr": -17}), ("Fmk = -350", {"Fmk": -350}),
                     ("Nsç = -11", {"Nsc": -11}), ("L1 = -40", {"L1": -40}),
                     ("S1 = 0", {"S1": 0})):
        _ru = _av(_ek)
        r.kontrol(f"avan: {_ad} uyarı üretiyor",
                  bool(_ru.get("uyarilar")), f"→ {_ru.get('uyarilar')}")
    r.kontrol("avan: geçerli girdide gereksiz uyarı yok", not (_av().get("uyarilar") or []))

    # ==================================================================
    #  v1.8 — ŞERİT BOYU ( L ) TEMEL ÖLÇÜLERİNDEN TÜRETİLİR
    #  Ofiste temel için yalnız UZUNLUK ve GENİŞLİK giriliyor; band boyu
    #  bunlardan çıkarılır.  Girilirse girilen değer kullanılır.
    # ==================================================================
    _S = AV.sabitler({})
    r.esit("karelaj gözü ofis varsayılanı 20 m", _S["goz_araligi"], 20)

    #  Formülün kendisi:  L = 2·( a + b ) + na·b + nb·a
    _L, _ring, _na, _nb = AV.serit_boyu_tahmin(31.05, 18.9, 20)
    r.esit("ring = 2·( a + b )", round(_ring, 4), round(2 * (31.05 + 18.9), 4))
    r.esit("31,05 m kenar için 1 enine bağ", _na, 1)
    r.esit("18,90 m kenar için bağ gerekmiyor", _nb, 0)
    r.esit("L = ring + 1 · b", round(_L, 4), round(2 * (31.05 + 18.9) + 18.9, 4))
    r.esit("20 × 20 m'den küçük temelde bağ yok",
           AV.serit_boyu_tahmin(15, 10, 20)[0], 50)
    r.kontrol("ölçü yoksa türetme yok", AV.serit_boyu_tahmin(0, 18.9, 20)[0] is None)
    #  Tam 20 m kenar bağ gerektirmez ( kayan nokta payı ile )
    r.esit("tam 20 m kenarda bağ yok", AV.serit_boyu_tahmin(20, 20, 20)[0], 80)
    r.esit("20,01 m kenarda bağ çıkıyor", AV.serit_boyu_tahmin(20.01, 20, 20)[2], 1)

    _TO = {"temel_a": 31.05, "temel_b": 18.9}
    _t = AV.hesapla_topraklama(dict(_TO), _S)
    r.kontrol("L boşken hesap çalışıyor", _t["aktif"] is True)
    r.esit("L türetildi", round(_t["L"], 2), 118.80)
    r.esit("L kaynağı türetilen", _t["L_kaynak"], "türetilen")

    #  PAFTA, boyun nereden geldiğini YAZMAZ — türetme programın iç
    #  kolaylığıdır, teslim edilen hesabın konusu değil.
    _p1 = _t["bolumler"][0]
    r.kontrol("paftada türetme adımı YOK",
              not any("enine bağlar" in (x.get("formul") or "") for x in _p1["adimlar"]))
    r.kontrol("paftada türetme notu YOK",
              not any("TÜRETİL" in x for x in (_p1.get("notlar") or [])))
    r.kontrol("paftada L sıradan girdi satırı",
              any(x.get("sembol") == "L" and x.get("kaynak") == "GİRİŞ"
                  for x in _p1["adimlar"]))

    #  Elle girilen boy türetileni EZER — plan çizilince gerçek boy yazılır
    _te = AV.hesapla_topraklama(dict(_TO, serit_L=140), _S)
    r.esit("elle girilen L kullanılıyor", _te["L"], 140)
    r.esit("elle girilince kaynak GİRİŞ", _te["L_kaynak"], "GİRİŞ")
    r.kontrol("elle girilince türetme notu yok", not _te["bolumler"][0].get("notlar"))
    #  Pafta iki durumda da AYNI görünmeli — yalnız sayı değişir
    r.esit("pafta yapısı türetilende ve elle girilende aynı",
           [(x.get("sembol"), x.get("formul"), x.get("kaynak")) for x in _p1["adimlar"]],
           [(x.get("sembol"), x.get("formul"), x.get("kaynak"))
            for x in _te["bolumler"][0]["adimlar"]])

    #  Ofis paftasının kendi sayısı ( 31,05 × 18,90 · L = 140 · β = 150 · Is = 4 )
    r.esit("ofis paftası Ry", round(_te["Ry"], 2), 3.82)
    r.esit("ofis paftası Rç", round(_te["Rc"], 2), 25.00)
    r.esit("ofis paftası Re", round(_te["Re"], 3), 3.310)
    r.esit("ofis paftası Re max", round(_te["Re_max"], 2), 166.67)
    r.kontrol("ofis paftası sonucu: uygun", _te["uygun"] is True)

    #  Göz aralığı ofis sabitidir — değişince türetilen boy da değişir
    _t10 = AV.hesapla_topraklama(dict(_TO), AV.sabitler({"goz_araligi": 10}))
    r.kontrol("göz 10 m olunca L uzuyor", _t10["L"] > _t["L"],
              f"→ {_t10['L']:.2f} > {_t['L']:.2f}")
    r.kontrol("geçersiz göz aralığı reddediliyor",
              any("goz_araligi" in x
                  for x in AV.sabitler({"goz_araligi": 0})["_reddedilen"]))

    #  Ölçü yoksa hesap kapanır ve hata metni ölçüleri işaret eder
    _ty = AV.hesapla_topraklama({"temel_b": 18.9}, _S)
    r.kontrol("uzunluk yoksa topraklama kapalı", _ty["aktif"] is False)
    r.kontrol("hata metni temel ölçülerini işaret ediyor",
              "uzunluk" in _ty["uyari"] and "genişlik" in _ty["uyari"])

    #  XLSX yolu: türetilen boy GİRİŞ hücresine YAZILMALI, yoksa Excel
    #  boş hücreyle hesaplar ve indirilen dosya ekrandakinden farklı çıkar.
    _v = {"ortak": dict(_TO, mk_yok=True), "asansorler": [dict(O_AS)], "sabitler": {}}
    _c = AV.girdileri_coz(_v)
    r.esit("türetilen L girdiye yazıldı", round(_c["ortak"]["serit_L"], 2), 118.80)
    r.esit("elle girilen L girdide korunuyor",
           AV.girdileri_coz({"ortak": dict(_TO, serit_L=58.5, mk_yok=True),
                             "asansorler": [dict(O_AS)]})["ortak"]["serit_L"], 58.5)
    r.esit("özette şerit boyu ve kaynağı var",
           (round(AV.hesapla(_v)["ozet"]["serit_L"], 2),
            AV.hesapla(_v)["ozet"]["serit_L_kaynak"]), (118.80, "türetilen"))

    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
