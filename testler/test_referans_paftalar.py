# -*- coding: utf-8 -*-
"""
TEST 12  —  DIŞ REFERANS PAFTALARI  ( başka programların çıktıları )

Motorun sayılarını, aynı asansörü hesaplayan BAŞKA İKİ PROGRAMIN yayımlanmış
paftalarına karşı doğrular:

    ELEport        ~/asansör projeleri/sample-project.pdf   ( PROJE 5 · Elevator 3 )
    "new block"    ~/asansör projeleri/new block-Model.pdf

NİÇİN AYRI TEST:  öteki bütün testler ya motoru KENDİ kaynak Excel'imize ya da
kendi altın çıktımıza karşı denetler.  İkisi de bizim yorumumuzdur — ikisinde
birden aynı yanlışı yapıyorsak hiçbiri bunu göremez.  Burada karşılaştırma
noktası dışarıdadır:  aynı standardı uygulayan, bizden bağımsız yazılmış iki
program.

BEKLENEN DEĞERLER PAFTALARIN KENDİ BASILI SAYILARIDIR.  Elle kopyalandılar;
kaynak satırları aşağıda tek tek yazılıdır ki doğrulanabilsinler.

TOLERANSLAR GEVŞEKTİR VE SEBEPLERİ YAZILIDIR.  İki program aynı standardı
uygular ama ara kabulleri ( kasnak ataleti modeli, yuvarlama, katalog
toleransı ) aynı değildir;  amaç birebir eşitlik değil, BİR YERDE SESSİZCE
AYRIŞMADIĞIMIZI görmektir.  Sapma büyürse buradan görünür.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.uygulama import mukavemet as MK                       # noqa: E402
from testler.ortak import Rapor                                   # noqa: E402


# =====================================================================
#  ELEPORT  —  sample-project.pdf  ·  "PROJE 5 / Elevator 3"
# =====================================================================
#  Girdiler paftanın "CALCULATION OF STEEL ROPES IN ROPE-TRACTION ELEVATORS"
#  başlıklı sayfasındaki girdi bloğundan alındı.  Durak yükseklikleri orada
#  yoktur;  seyir mesafesi 29,0 m olacak şekilde 11 × 2.900 mm kuruldu
#  ( seyir = ( durak sayısı − 1 ) × kat yüksekliği ).
ELEPORT = {
    "beyan_yuku": 800,                  # Actual Load Q : 800 kg
    "kabin_agirligi": 900,              # Empty Cabin Mass P : 900 kg
    "beyan_hizi": 1.6,                  # Cabin Speed V : 1.6 m/s
    "aski_orani": 2,                    # Roping Type 2/1 · r : 2
    "seyir_mesafesi": 29.0,             # Travel Distance Htravel : 29.0 m
    "durak_yukseklikleri": [2900] * 11,
    "son_kat_yuksekligi": 2900,
    "tahrik_kasnak_capi": 240,          # Traction Sheave Diameter Dt : 240 mm
    "saptirma_kasnak_capi": 294,        # Average diameter Dp : 294 mm
    "saptirma_kasnak_min_capi": 240,    # Minimum diameter Ds : 240 mm
    "halat_capi": 6.5,                  # Rope Diameter dr : 6.5 mm
    "halat_adedi": 7,                   # Number of Rope ns : 7 piece
    "halat_birim_kutle": 0.179,         # Rope Unit Mass ms : 0.179 kg/m
    "halat_kopma_kN": 31.5,             # Rope Breaking Force Sh : 31.5 kN
    "sarilma_acisi": 180,               # Rope Winding Angle α : 180°
    "kanal_sekli": "V Kanal",           # (V) Groove - Hardened
    "kanal_isleme": "Sertleştirilmiş",
    "kasnak_tek_yon": 2,                # Nps : 2 piece
    "kasnak_ters_yon": 0,               # Npr : 0 piece
    "acil_frenleme_a": 0.5,             # Emergency Braking Deceleration a : 0.5
    "denge_zinciri": "Var",             # Compensation Chain Ratio λ : 100 %
    "_ofis": {"q_denge": 0.50,          # Counterweight Balance Factor q : 50 %
              "kanal_gama_v": 38},      # Traction Sheave Groove Angle γ : 38°
}

#  ( ad , hücre , ELEport'un bastığı değer , izin verilen sapma % , gerekçe )
ELEPORT_BEKLENEN = (
    #  Bunlar TANIM GEREĞİ aynı çıkmalı:  α doğrudan girdi, f ise
    #  m.5.11.2.3.1.2'nin kapalı bağıntısı ( μ / sin(γ/2) ).
    ("α  ( derece )",        "S184",  180.0,   0.01, "doğrudan girdi"),
    ("f  yükleme",           "AJ198",   0.307, 0.5,  "ELEport 3 haneye yuvarlıyor"),
    ("f  bloke",             "AE216",   0.614, 0.5,  "ELEport 3 haneye yuvarlıyor"),
    #  Yükleme durumu STATİKTİR:  kasnak ataleti ve sürtünme girmez, iki
    #  program da aynı kütleleri aynı bağıntıya koyar → birebir tutmalı.
    ("yükleme  T1",          "AF235", 9676.0,  0.05, "statik — ara kabul yok"),
    ("yükleme  T2",          "AJ240", 6733.0,  0.05, "statik — ara kabul yok"),
    ("yükleme  T1/T2",       "K242",     1.44, 0.5,  "ELEport 2 haneye yuvarlıyor"),
    ("yükleme  e^(fα)",      "O242",     2.62, 0.5,  "ELEport 2 haneye yuvarlıyor"),
    ("fren  e^(fα)",         "O271",     2.08, 0.5,  "ELEport 2 haneye yuvarlıyor"),
    ("bloke  e^(fα)",        "O285",     6.89, 0.5,  "ELEport 2 haneye yuvarlıyor"),
    #  FRENLEME DİNAMİKTİR:  kasnak ataleti ve kuyu sürtünmesi girer ve iki
    #  programın kabulleri farklıdır ( ELEport J'yi kendi dört yaklaşımıyla
    #  kurar, biz döküm disk modelimizle ).  %2 bunun payıdır.
    ("fren alt  T1",         "AF250", 8987.82, 2.0,  "kasnak ataleti modeli farklı"),
    ("fren alt  T2",         "AJ255", 6514.24, 2.0,  "kasnak ataleti modeli farklı"),
    ("bloke  T1/T2",         "K285",    13.47, 2.0,  "halat kütlesi dağılımı kabulü"),
)


def _eleport(r):
    s = MK.hesapla(dict(ELEPORT))
    r.kontrol("ELEport girdileri motorda geçerli", s.get("aktif"),
              f"→ {s.get('hata')}")
    if not s.get("aktif"):
        return
    h = s["_h"]
    for ad, hucre, bek, tol, neden in ELEPORT_BEKLENEN:
        v = h.get(hucre)
        if v is None:
            r.kontrol(f"ELEport · {ad}", False, f"→ {hucre} hesaplanmadı")
            continue
        sapma = abs(v - bek) / abs(bek) * 100
        r.kontrol(f"ELEport · {ad}  ( ≤ %{tol} )", sapma <= tol,
                  f"→ bizim {v:.4f} · ELEport {bek} · sapma %{sapma:.2f}  ( {neden} )")

    #  HALAT GÜVENLİK KATSAYISI  —  EN 81-50 m.5.12'nin kapalı bağıntısı.
    #  Ara kabul yoktur;  birebir tutmalıdır.
    r.kontrol("ELEport · Sf ( gereken güvenlik katsayısı )",
              abs(s["ozet"]["Sf"] - 23.54) / 23.54 * 100 <= 0.5,
              f"→ bizim {s['ozet']['Sf']:.2f} · ELEport 23,54")
    #  S ( gerçekleşen ):  bir halata düşen en büyük kuvvetten çıkar.  ELEport
    #  MSR'yi kabin en alttayken alır, biz de;  kalan fark yuvarlamadır.
    r.kontrol("ELEport · S ( gerçekleşen güvenlik katsayısı )",
              abs(s["ozet"]["S_gercek"] - 25.36) / 25.36 * 100 <= 1.0,
              f"→ bizim {s['ozet']['S_gercek']:.2f} · ELEport 25,36")

    #  ── Dt/dh = 36,92 < 40  —  BELGE YOLU ────────────────────────────
    #  ELEport bu kontrolü "halat sertifikalı" diye atlar ve Sf'yi 12'ye
    #  indirir.  Biz belgesiz projede reddederiz;  belge beyan edilince
    #  oran kabul edilir ama Sf = 23,54 aynen aranır ( 7 halat S = 25,1 ).
    _hb = lambda x: next(b for b in x["bolumler"] if b["kimlik"] == "aski_halatlari")
    r.kontrol("ELEport · belgesiz 240 / 6,5 halat bölümü UYGUN DEĞİL",
              _hb(s)["sonuc"]["uygun"] is False, f"→ {_hb(s)['sonuc']['metin']}")
    s_b = MK.hesapla(dict(ELEPORT, kasnak_belgesi="Var"))
    r.kontrol("ELEport · belgeyle halat bölümü UYGUN, Sf yine 23,54",
              _hb(s_b)["sonuc"]["uygun"] is True
              and abs(s_b["ozet"]["Sf"] - 23.54) / 23.54 * 100 <= 0.5,
              f"→ {_hb(s_b)['sonuc']['metin']} · Sf {s_b['ozet']['Sf']:.2f}")

    #  ── T1/T2 ETİKETİ:  AYNI SAYI, BAŞKA AD ───────────────────────────
    #  EN 81-50 m.5.11.2.1 T1 ve T2'yi "kasnağın İKİ YANINDAKİ kuvvetler"
    #  diye tanımlar, hangisinin T1 olduğunu söylemez.  ELEport BÜYÜK olana
    #  T1 der ve yük durumuna göre taraf değiştirir;  biz T1'i HER ZAMAN
    #  KABİN tarafı sayarız ve paftaya "T1 ( kabin tarafı )" diye yazarız.
    #  "Boş kabin en üstte frenleme"de karşı ağırlık tarafı büyüktür, bu
    #  yüzden iki paftada T1 ve T2 yer değişmiş GÖRÜNÜR.  Oran max(a/b, b/a)
    #  alındığı için hüküm ikisinde de aynıdır.  Aşağısı bunu KANITLAR:
    #  taraflar eşleştirilince sayılar tutar.
    for ad, hucre, bek in (("kabin tarafı", "AH264", 4641.92),
                           ("karşı ağırlık tarafı", "AF269", 6963.68)):
        v = h.get(hucre)
        sapma = abs(v - bek) / bek * 100 if v else 100
        r.kontrol(f"ELEport · fren üst {ad} ( taraf eşleşmesi )", sapma <= 2.0,
                  f"→ bizim {v:.2f} · ELEport {bek}  ( ELEport büyüğe T1 der, "
                  f"biz kabin tarafına )")


# =====================================================================
#  "NEW BLOCK"  —  new block-Model.pdf  ·  kabin rayı, yük arkada
# =====================================================================
#  Paftanın "2.2 Yuk dagilimi arkada iken sonuclar" bölümü.  Ray kesiti
#  kataloğumuzda birebir yoktur;  bu yüzden ray verileri ( Wx · Wy · Jx · Jy
#  · c ) paftanın KENDİ yazdığı sayılardır ve doğrudan bağıntıya konur.
#  Denetlenen şey KESİT VERİSİ DEĞİL, BAĞINTININ KENDİSİDİR.
BLOCK_RAY = {
    "k": 1.2, "Q": 1275, "P": 1200, "xQ": 175, "xP": -65, "yQ": -263,
    "n": 2, "h": 3200, "l": 1700,
    "Wy": 11400, "Wx": 20800, "Jy": 515000, "Jx": 1012000, "c": 9,
    "sigma_perm": 165,
}

#  ( ad , paftanın bastığı değer , tolerans )   —  kaynak satırlar yorumda
BLOCK_BEKLENEN = (
    ("Fx  ( yük arkada )",      266.0,  1.0),   # "Fx = 266 N"
    ("My  ( yük arkada )",    84794.0,  1.0),   # "My = 84794 Nm"
    ("σy  ( yük arkada )",        7.4,  2.0),   # "Sigm(y) = 7,4 N/mm^2"
    ("σF  ( flanş, arkada )",     6.1,  2.0),   # "Sigm(F) = 6,1 N/mm^2"
    ("δx  ( yük arkada )",        0.18, 5.0),   # "d(x) = 0,18 mm"
    ("Fy  ( yük solda )",     -1231.0,  1.0),   # "Fy = -1231 N"
    ("σx  ( yük solda )",        18.9,  2.0),   # "Sigm(x) = 18,9 N/mm^2"
)


def _block(r):
    """Paftanın ray bağıntılarını KENDİ verisiyle yeniden kurar.

    Motorun aynı bağıntıları kullandığı TEST 9 ve 11'de denetleniyor;  burada
    denetlenen, BAĞINTILARIN dış bir paftayla aynı sonucu verdiğidir.
    """
    b = BLOCK_RAY
    gn = 9.81
    # C.2.1.1 a)  Fx = k1·gn·( Q·xQ + P·xP ) / ( n·h )
    Fx = b["k"] * gn * (b["Q"] * b["xQ"] + b["P"] * b["xP"]) / (b["n"] * b["h"])
    #  m.5.10.2:  My = 3·Fx·l / 16   ( iki açıklıklı sürekli kiriş )
    My = 3 * Fx * b["l"] / 16
    sy = My / b["Wy"]
    #  C.2.1.4:  σF = 1,85·Fx / c²
    sF = 1.85 * Fx / b["c"] ** 2
    #  C.2.1.5:  δ = 0,7·F·l³ / ( 48·E·J )
    dx = 0.7 * (Fx * b["l"] ** 3) / (48 * 210000 * b["Jy"])
    # "Yuk dagilimi solda":  xQ = 0, yQ = −263
    #  Paftanın Fy paydası  h'dir;  C.2.1.1 b) ( n/2 )·h ister — n = 2'de
    #  ikisi AYNIDIR.  Bu yüzden bu pafta o farkı gösteremez;  fark bizim
    #  kendi testimizde ( test_tsen_bagimsiz ) denetleniyor.
    Fy = b["k"] * gn * (b["Q"] * b["yQ"] + b["P"] * 0) / ((b["n"] / 2) * b["h"])
    Mx = 3 * Fy * b["l"] / 16
    sx = abs(Mx / b["Wx"])
    bulunan = {"Fx  ( yük arkada )": Fx, "My  ( yük arkada )": My,
               "σy  ( yük arkada )": sy, "σF  ( flanş, arkada )": sF,
               "δx  ( yük arkada )": dx, "Fy  ( yük solda )": Fy,
               "σx  ( yük solda )": sx}
    for ad, bek, tol in BLOCK_BEKLENEN:
        v = bulunan[ad]
        sapma = abs(v - bek) / abs(bek) * 100
        r.kontrol(f"block · {ad}  ( ≤ %{tol} )", sapma <= tol,
                  f"→ bağıntı {v:.4f} · pafta {bek} · sapma %{sapma:.2f}")

    #  ── PAFTANIN KENDİ KUSURLARI  ( bizde OLMAMALI ) ──────────────────
    #  Bu pafta bizim değil;  ondan KOPYALAMAMAMIZ gereken şeyler de var.
    #  Aşağısı, aynı hatayı yapmadığımızı sabitler.
    s = MK.hesapla({})
    kb = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
    metinler = " | ".join(str(a.get("formul") or "") for a in kb["adimlar"]
                          if isinstance(a, dict))
    #  ① Paftanın Fy bağıntısı paydaya yalnız h yazar;  C.2.1.1 b) ( n/2 )·h
    #    ister.  n = 2'de ikisi aynıdır, n = 4'te pafta Fy'yi İKİ KAT
    #    büyük gösterir.  Bizde payda her zaman ( n/2 )·h olmalı.
    r.kontrol("block · Fy paydası bizde ( n/2 )·h  ( paftada yalnız h )",
              "( n / 2 )" in metinler,
              f"→ {metinler[:150]}")
    #  ② Pafta P'yi bölümden bölüme değiştiriyor ( ray 1.200 · tahrik 1.270 ·
    #    başka yerde 1.100 ).  Bizde P TEK KAYNAKTAN gelir.
    p_satir = [a for a in kb["adimlar"] if isinstance(a, dict)
               and str(a.get("formul") or "").startswith("P = boş kabin")]
    r.kontrol("block · P tek kaynaktan türüyor  ( paftada bölüme göre değişiyor )",
              len(p_satir) >= 1, f"→ {len(p_satir)} satır")


def calistir():
    r = Rapor("TEST 12 — DIŞ REFERANS PAFTALARI (ELEport · new block)")
    _eleport(r)
    _block(r)
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
