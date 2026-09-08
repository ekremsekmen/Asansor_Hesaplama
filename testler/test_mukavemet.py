# -*- coding: utf-8 -*-
"""
TEST 9  —  MUKAVEMET MOTORU  ( uygulama projesi )

engine/mukavemet.py çıktısını KAYNAK EXCEL'in kendi sonuçlarına karşı
doğrular:  templates/MUKAVEMET_HESABI.xlsx · "11-Muk. Hesapları"

YÖNTEM:  Excel'in her sonuç hücresi ( adres → beklenen değer ) bölüm bölüm
listelenir.  Motor varsayılan girdilerle koşturulur ve o bölümün sayısal
adımları arasında aynı değerin bulunması aranır.  Böylece satır sırası
değişse de hesap değişirse test kırılır.

Ayrıca:
  · özet değerleri birebir karşılaştırılır,
  · kaynak Excel'den BİLEREK ayrıldığımız iki nokta ayrıca kilitlenir,
  · girdi doğrulama ve hata yolu denenir.

Kaynak dosya yoksa Excel karşılaştırmaları ATLANIR, motor testleri koşar.
"""
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.uygulama import mukavemet as MK                       # noqa: E402
from engine.uygulama import mukavemet_tablolari as MT             # noqa: E402
from testler.ortak import Rapor                          # noqa: E402

KAYNAK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "templates", "MUKAVEMET_HESABI.xlsx")
SAYFA = "11-Muk. Hesapları"

#  bölüm sırası  →  o bölümde bulunması gereken Excel hücreleri
#  ( hücre adresi , ne olduğu )
HUCRELER = {
    0: [("AQ16", "Gh  toplam halat ağırlığı"),
        ("AQ19", "lh  halat uzunluğu"),
        ("AQ11", "F1  kabin ve aksesuar yükü"),
        ("AQ13", "Ga  karşı ağırlık yükü"),
        ("AQ9",  "Gmax  maksimum artan yük"),
        ("AQ7",  "Pm  makine miline gelen kuvvet"),
        ("AQ21", "M  moment"),
        ("AQ23", "N  hesaplanan motor gücü"),
        ("X25",  "HP  motor gücü")],
    1: [("C47",  "F  kaide üzerindeki en büyük kuvvet"),
        ("I51",  "F1  yan yatak putreli"),
        ("O53",  "FB"),
        ("AK53", "FA"),
        ("M63",  "Mmax"),
        ("J65",  "σe  eğilme gerilmesi"),
        ("O71",  "λ  ham narinlik"),
        ("K73",  "σb  burkulma gerilmesi")],
    2: [("X84",  "kabin alanı")],
    3: [("N97",  "Dt / dh"),
        ("T112", "Kp"),
        ("P114", "Nequiv(p)"),
        ("V116", "Nequiv"),
        ("T125", "Sf  halat güvenlik katsayısı"),
        ("T126", "S  gerçek güvenlik katsayısı")],
    4: [("AI134", "gh  regülatör halatı ağırlığı"),
        ("J142",  "Dreg / dreg"),
        ("W146",  "f  sürtünme değeri"),
        ("AF146", "e^(f·α')"),
        ("W151",  "Freg"),
        ("J156",  "F'reg"),
        ("G161",  "T'min / F'reg")],
    5: [("U174", "A  kasnaklar arası yatay mesafe"),
        ("Z178", "B  kasnaklar arası düşey mesafe"),
        ("C184", "θ"),
        ("S184", "α  sarılma açısı"),
        ("AS190", "μ  frenleme"),
        ("AU206", "f  yükleme ( sertleştirilmemiş )"),
        ("AV211", "f  frenleme ( sertleştirilmemiş )"),
        ("AE216", "f  bloke"),
        ("AF235", "T1  yükleme"), ("AJ240", "T2  yükleme"),
        ("AF250", "T1  frenleme en alt"), ("AJ255", "T2  frenleme en alt"),
        ("AH264", "T1  frenleme en üst"), ("AF269", "T2  frenleme en üst"),
        ("AH278", "T1  bloke"), ("AF283", "T2  bloke"),
        ("O242", "e^(f·α) yükleme"), ("O257", "e^(f·α) frenleme"),
        ("O285", "e^(f·α) bloke")],
    6: [("AH291", "Mg  kabin rayı kütlesi"),
        ("AH293", "xc"), ("AH295", "xp"), ("AH303", "Fs  eşik kuvveti"),
        ("Z309", "xQ  durum 1"), ("Z312", "yQ  durum 2"),
        ("AY321", "C.2.1 D1 Fx"), ("AU324", "C.2.1 D1 σx"),
        ("AY327", "C.2.1 D1 Fy"), ("AY335", "C.2.1 D2 Fx"),
        ("AU338", "C.2.1 D2 σx"), ("K344", "C.2.1 D2 Fy"),
        ("AU347", "C.2.1 D2 σy"),
        ("AU351", "Fk  burkulma kuvveti"), ("AL354", "σk"),
        ("Z360", "C.2.1 D1 σm"), ("AJ362", "C.2.1 D1 σc"),
        ("AE365", "C.2.1 D1 σ"),
        ("Z369", "C.2.1 D2 σm"), ("AJ371", "C.2.1 D2 σc"),
        ("AE374", "C.2.1 D2 σ"),
        ("Z379", "C.2.1 D1 σF"), ("Z384", "C.2.1 D2 σF"),
        ("AH393", "C.2.1 D1 δx"), ("AH401", "C.2.1 D2 δx"),
        ("AH404", "C.2.1 D2 δy"),
        ("L415", "C.2.2 D1 Fx"), ("AU418", "C.2.2 D1 σx"),
        ("L435", "C.2.2 D2 Fx"), ("AU438", "C.2.2 D2 σx"),
        ("L444", "C.2.2 D2 Fy"), ("AU447", "C.2.2 D2 σy"),
        ("AE452", "Fv"), ("AL455", "σv"),
        ("Z461", "C.2.2 D1 σm"), ("AC463", "C.2.2 D1 σc"),
        ("Z468", "C.2.2 D2 σm"), ("AH470", "C.2.2 D2 σc"),
        ("Z476", "C.2.2 D1 σF"),
        ("AH487", "C.2.2 D1 δx"), ("AH495", "C.2.2 D2 δx"),
        ("AH498", "C.2.2 D2 δy"),
        ("L508", "C.2.3 Fx"), ("AU511", "C.2.3 σx"),
        ("Z530", "C.2.3 σm"), ("AF532", "C.2.3 σc"),
        ("Z537", "C.2.3 σF"), ("AH542", "C.2.3 δx")],
    7: [("AH550", "ağırlık derinliği"), ("AH551", "ağırlık genişliği"),
        ("N562",  "Dxa"), ("AL562", "Dya"),
        ("AH554", "Mg  ağırlık rayı kütlesi"),
        ("AP566", "Fx"), ("AU569", "σx"),
        ("AP572", "Fy"),
        ("AE580", "Fv"), ("AL583", "σv"),
        ("Z595",  "σF"),
        ("AH600", "δx"), ("AH603", "δy")],
    8: [("AH611", "LR  ray boyu"),
        ("AX611", "FKR"), ("AN616", "FAR"),
        ("AF621", "Fkt"), ("AI627", "Fat")],
    9: [("AI635", "b - üst paten"), ("AI636", "c.2 - kabin üstü"),
        ("AI637", "a - revizyon kutusu"), ("AI638", "b - paten/halat"),
        ("AD638", "serbest boşluk"), ("AI640", "Ç.2 - ağırlık üst pateni"),
        ("AI645", "a - kuyu tabanı"), ("AI646", "a.1 - kabin eteği"),
        ("AI647", "a.2 - kılavuz raylar"), ("AI648", "b - regülatör makarası")],
}

#  KAYNAK EXCEL'DEN BİLEREK AYRILAN HÜCRELER.  Uyulması gereken standart
#  TS EN 81-20 / TS EN 81-50'dir;  bu hücrelerde Excel standarttan sapıyor,
#  motor standardı uyguluyor.  Liste MOTORDAN okunur — gerekçeler
#  engine/mukavemet.EXCEL_FARKLARI içindedir.
AYRILAN = set(MK.FARKLI_HUCRELER)


def _yakin(a, b, tol=1e-7):
    if a is None or b is None:
        return False
    try:
        buyuk = max(abs(float(a)), abs(float(b)), 1.0)
        return abs(float(a) - float(b)) <= tol * buyuk
    except (TypeError, ValueError):
        return False


def calistir():
    print("\n\033[1mTEST 9 — MUKAVEMET MOTORU (kaynak Excel'e karşı)\033[0m")
    r = Rapor("Mukavemet motoru")

    s = MK.hesapla()
    if not r.kontrol("varsayılan girdilerle hesap koşuyor", s["aktif"],
                     f"→ {s.get('hata')}"):
        return r
    b = s["bolumler"]
    r.esit("bölüm sayısı", len(b), 10)
    for i, bl in enumerate(b):
        r.kontrol(f"bölüm {i + 1} başlığı dolu", bool(bl.get("baslik")))
        r.kontrol(f"bölüm {i + 1} adım üretti", len(bl.get("adimlar") or []) > 0)
        r.kontrol(f"bölüm {i + 1} sonucu var", bool(bl.get("sonuc")))

    #  ÖRNEK PROJE İKİ BÖLÜMDEN KALIYOR — ikisi de kaynak kitabın gizlediği
    #  gerçek yetersizliklerdir:
    #    · ASKI HALATLARI — TS EN 81-20 m.5.5.2.1 tahrik kasnağı / halat
    #      oranını EN AZ 40 ister;  örnekte 240 / 6,5 = 36,9.  Kitap kontrolü
    #      30 ile yaptığı için "uygun" görünüyordu  ( sapma ① ).
    #    · MOTOR GÜCÜ — verim makine tipine bağlandı;  dişlisiz + 2:1 askıda
    #      η′ = 0,75 ve gereken güç 5,90 kW.  Örnekte seçilen motor 4,9 kW.
    #      Kitap sabit η = 0,92 ile 4,81 kW deyip "uygun" gösteriyordu
    #      ( sapma ⑨ ).
    #  Beklenen davranış budur — geri dönerse test bağırır.
    #    · HIZ REGÜLATÖRÜ — TS EN 81-20 m.5.6.2.2.1.1 d)'nin ikinci sınırı
    #      "güvenlik tertibatını devreye sokmak için gerekenin iki katı"dır ve
    #      o kuvvet İMALATÇI VERİSİDİR.  Kitabın örneğinde yoktur;  madde
    #      denetlenemediği için bölüm "HESAP EKSİK" der ( sapma ⑲ ).
    _kalan = [x["baslik"] for x in b if (x.get("sonuc") or {}).get("uygun") is False]
    r.esit("örnek proje üç bölümden kalıyor", len(_kalan), 3)
    r.kontrol("kalan bölümler motor gücü, askı halatları ve regülatör",
              sorted(x[:1] for x in _kalan) == ["1", "4", "5"], f"→ {_kalan}")
    r.kontrol("regülatör bölümü EKSİK diyor, UYGUN DEĞİL değil",
              any("HESAP EKSİK" in (x.get("sonuc") or {}).get("metin", "")
                  for x in b if x["baslik"].startswith("5 ")))
    r.esit("Dt/dh eşiği standarda göre 40", MK.SABIT["Dt_dh_asgari"], 40)
    _oran = 240 / 6.5
    r.kontrol("örnek proje 40 eşiğini sağlamıyor", _oran < 40, f"→ {_oran}")
    #  İkisi de giderilince bütün bölümler uygun olmalı
    _d = MK.hesapla({"tahrik_kasnak_capi": 280, "saptirma_kasnak_capi": 280,
                     "motor_gucu": 7.5, "guvenlik_devreye_kuvvet": 200})
    r.kontrol("kasnak 280 mm · motor 7,5 kW · imalatçı kuvveti girilince "
              "bütün bölümler uygun",
              _d["aktif"] and _d["ozet"]["tumu_uygun"],
              "→ " + ", ".join(x["baslik"] for x in (_d.get("bolumler") or [])
                               if (x.get("sonuc") or {}).get("uygun") is False))
    r.esit("ray boyu (m)", s["ozet"]["ray_boyu"], 26.6)
    r.esit("kabin kişi sayısı", s["ozet"]["kabin_kisi"], 10)

    if not os.path.isfile(KAYNAK):
        r.atla(f"Kaynak Excel yok — {os.path.basename(KAYNAK)}")
        return _girdi_yollari(r)

    warnings.filterwarnings("ignore")
    import openpyxl
    ws = openpyxl.load_workbook(KAYNAK, data_only=True)[SAYFA]

    for i, liste in HUCRELER.items():
        havuz = [a["deger"] for a in b[i]["adimlar"]
                 if isinstance(a["deger"], (int, float))
                 and not isinstance(a["deger"], bool)]
        for hucre, ne in liste:
            if hucre in AYRILAN:
                continue                 # bilerek ayrıldık — TEST 10 denetler
            bek = ws[hucre].value
            bulundu = any(_yakin(x, bek) for x in havuz)
            r.kontrol(f"böl.{i + 1}  {hucre}  {ne}", bulundu,
                      f"→ Excel {bek!r} bölümün adımlarında yok")

    #  Özet değerleri birebir.  Bilerek ayrıldığımız hücreler ( ör. AQ23 —
    #  motor gücü, verim makine tipine bağlandığı için ) burada da atlanır;
    #  onları _sapmalar() ayrıca denetler.
    for anahtar, hucre in (("N_hesap", "AQ23"), ("kabin_alani", "X84"),
                           ("Sf", "T125"), ("S_gercek", "T126"),
                           ("Mg_kabin", "AH291"), ("Mg_agirlik", "AH554"),
                           ("Fk_kabin", "AU351"), ("FKR", "AX611"),
                           ("FAR", "AN616"), ("Fkt", "AF621"), ("Fat", "AI627")):
        if hucre in AYRILAN:
            continue
        r.kontrol(f"özet {anahtar} ≡ {hucre}",
                  _yakin(s["ozet"][anahtar], ws[hucre].value),
                  f"→ motor {s['ozet'][anahtar]!r}, Excel {ws[hucre].value!r}")

    #  KAYNAK EXCEL DEĞİŞMEMİŞ Mİ.  Sapmalarımızın dayanağı, Excel'in o
    #  hücrelerde ne yaptığıdır;  kaynak dosya güncellenirse gerekçe yeniden
    #  gözden geçirilmeli.  Bu yüzden Excel'in KENDİ değerleri kilitli.
    for hucre, bek, ne in (("AU575", 24.48378151260504, "karşı ağırlık σ(My), Wy ile"),
                           ("AO312", 0, "Durum 2'de xQ sabit 0"),
                           ("Q97", 30, "Dt/dh eşiği 30")):
        r.kontrol(f"kaynak Excel {hucre} değişmemiş  ( {ne} )",
                  _yakin(ws[hucre].value, bek),
                  f"→ Excel {ws[hucre].value!r}, beklenen {bek!r} — "
                  "kaynak dosya güncellendiyse sapma gerekçesi gözden geçirilmeli")
    p = MT.ray("50 x 50 x 5", "Wx")
    #  Karşı ağırlık Fy:  k2 · gn · Mcwt · Dya / ( ( n / 2 ) · h )
    #  ( Ek C.2.2.1 b) — payda n·h DEĞİL, (n/2)·h;  bkz. EXCEL_FARKLARI )
    r.kontrol("motor σ(My) için Wx kullanıyor",
              any(_yakin(a["deger"], MK._moment(
                  1.2 * 9.81 * 1100 * 48 / ((2 / 2) * 3400), 3000) / p)
                  for a in b[7]["adimlar"] if isinstance(a["deger"], (int, float))))
    return _girdi_yollari(_denetim_bulgulari(_sapmalar(r)))


def _sapmalar(r):
    """Standart gereği Excel'den ayrıldığımız noktalar gerçekten uygulanıyor mu."""
    r.esit("sapma kaydı dolu", len(MK.EXCEL_FARKLARI), 33)
    for ad, madde, _ex, _biz, _h in MK.EXCEL_FARKLARI:
        #  Her sapmanın DAYANAĞI yazılı olmalı.  Üç geçerli dayanak vardır:
        #    · TS EN 81-20 / 81-50 maddesi
        #    · açıkça "ofis standardı"  ( ⑨ — verim tablosu;  standart makine
        #      verimi için sayı vermez, ofisin kendi avan tablosu verir )
        #    · açıkça "fiziksel"  —  kitabın bağıntısı standarda değil FİZİĞE
        #      aykırı olduğunda ( ㉝ — Gmax'ta halatın tamamını dengesizlik
        #      sayması ).  Bu üçüncü kapı bilerek DARDIR:  gerekçe metninde
        #      "fiziksel" sözcüğü geçmeli ki keyfî sapma buradan sızmasın.
        r.kontrol(f"sapma '{ad[:34]}' dayanağı yazılı",
                  bool(madde) and ("81-20" in madde or "81-50" in madde
                                   or "ofis standardı" in madde
                                   or "fiziksel" in madde),
                  f"→ {madde!r}")

    #  ① Dt/dh eşiği
    r.esit("① Dt/dh asgari oranı", MK.SABIT["Dt_dh_asgari"], 40)

    #  ② karşı ağırlık rayı σ(My)  →  Wx
    from engine.uygulama import mukavemet_tablolari as _MT
    s = MK.hesapla()
    p = _MT.ray("50 x 50 x 5", "Wx")
    _M = MK._moment(s["_h"]["AP572"], 3000)
    r.kontrol("② σ(My) Wx ile bölünüyor", _yakin(s["_h"]["AU575"], _M / p),
              f"→ {s['_h']['AU575']!r} ≠ {_M / p!r}")

    #  ③ Durum 2'de xQ = xc
    _xc = s["_h"]["AH293"]
    _bek = 2 * 9.81 * (800 * _xc + 700 * s["_h"]["AH295"]) / (2 * 3400)
    r.kontrol("③ Durum 2 Fx, xQ = xc ile hesaplanıyor",
              _yakin(s["_h"]["AY335"], _bek), f"→ {s['_h']['AY335']!r} ≠ {_bek!r}")

    #  ⑤ ω ray çeliğine bağlı  ( EN 81-50 m.5.10.3 )
    from engine.uygulama import mukavemet_tablolari as _MTb
    r.kontrol("⑤ Rm = 370 eğrisi Excel tablosunun tamamını üretiyor",
              all(abs(_MTb.omega_en8150(x, 370) - _MTb.omega(x)) <= 0.006
                  for x in range(_MTb.OMEGA_LAMBDA_MIN, _MTb.OMEGA_LAMBDA_MAX + 1)))
    _w = {rm: MK.hesapla({"ray_celigi_rm": rm})["_h"]["AD354"] for rm in (370, 440, 520)}
    r.kontrol("⑤ ω ray çeliğiyle birlikte büyüyor",
              _w[370] < _w[440] < _w[520], f"→ {_w}")
    r.kontrol("⑤ Rm 440 ara değerlemesi doğru",
              _yakin(_w[440], _w[370] + (_w[520] - _w[370]) * (440 - 370) / 150),
              f"→ {_w}")
    r.kontrol("⑤ Rm 370'te Excel tablosuyla aynı",
              _yakin(_w[370], _MTb.omega(155)), f"→ {_w[370]!r}")

    #  ⑥ acil frenlemede μ HALAT hızına bağlı  ( EN 81-50 m.5.11.2.3.2 )
    #  EN 81-50'nin çözümlü örneği:  kabin 1 m/s, askı 2:1 → μ = 0,083
    _m = MK.hesapla({"beyan_hizi": 1, "aski_orani": 2})["_h"]["AS190"]
    r.kontrol("⑥ μ, EN 81-50 örneğiyle aynı  ( 1 m/s · 2:1 → 0,0833 )",
              _yakin(_m, 0.1 / (1 + 2 / 10)), f"→ {_m!r}")
    _m1 = MK.hesapla({"beyan_hizi": 1, "aski_orani": 1})["_h"]["AS190"]
    r.kontrol("⑥ 1:1 askıda μ kabin hızıyla aynı", _yakin(_m1, 0.1 / 1.1),
              f"→ {_m1!r}")
    r.kontrol("⑥ askı oranı μ'yü değiştiriyor", _m < _m1, f"→ {_m!r} / {_m1!r}")

    #  ⑦ Nps / Npr artık girdi  ( Excel sabit yazıyordu )
    _n = {x: MK.hesapla({"kasnak_tek_yon": x})["_h"]["V116"] for x in (1, 2, 3)}
    #  Nequiv(t) = 12  ( altı kesik V, γ = 38°, Çizelge 2'nin V satırı ) + Nps
    r.esit("⑦ Nps Nequiv'i belirliyor", [_n[1], _n[2], _n[3]], [13.0, 14.0, 15.0])
    _sf = MK.hesapla({"kasnak_tek_yon": 2})["_h"]["T125"]
    r.kontrol("⑦ Nps büyüyünce gereken Sf de büyüyor",
              _sf > MK.hesapla()["_h"]["T125"], f"→ {_sf!r}")
    _b4 = [b for b in MK.hesapla()["bolumler"] if "ASKI HALAT" in b["baslik"]][0]
    r.kontrol("⑦ palangalı sistemde Nps uyarısı çıkıyor",
              any("EN AZ İKİ kabin kasnağı" in x for x in (_b4.get("notlar") or [])),
              f"→ {_b4.get('notlar')}")

    #  Sf formülü EN 81-50 m.5.12.3'ün çözümlü örneğini üretiyor mu
    #  ( LEIA örneği:  Dt/dr = 40 , Nequiv = 7  →  Sf ≈ 16 )
    import math as _m2
    _sfx = 10 ** (2.6834 - _m2.log10(695.85e6 * 7 / 40 ** 8.567)
                  / _m2.log10(77.09 * 40 ** -2.894))
    r.kontrol("Sf formülü EN 81-50 örneğini üretiyor  ( ≈ 16 )",
              15.5 <= _sfx <= 16.9, f"→ {_sfx!r}")

    #  ④ flanş eğilmesinde ℓ
    _a = MK.hesapla({"paten_balata_boyu": 60})
    _b = MK.hesapla({"paten_balata_boyu": 120})
    r.kontrol("④ balata boyu σF'yi değiştiriyor",
              _a["_h"]["Z379"] > _b["_h"]["Z379"] > 0,
              f"→ ℓ=60 {_a['_h']['Z379']!r} · ℓ=120 {_b['_h']['Z379']!r}")
    r.kontrol("④ balata boyu boşsa türetiliyor  ( 2·b )",
              _yakin(s["_h"]["Z379"],
                     MK._flans(s["_h"]["AY321"],
                               MK._ray_ozellik("89 x 62 x 15,88"), 2 * 17)))

    #  ═══════════════════════════════════════════════════════════════
    #  STANDARDIN METNİNE KARŞI BAĞIMSIZ DOĞRULAMA
    #  ═══════════════════════════════════════════════════════════════
    #  Aşağıdaki sayılar BS EN 81-20:2014 ve BS EN 81-50:2014'ün kendi
    #  metninden alınmıştır — motorun koduna bakılmadan.  Kaynak Excel'e
    #  karşı yapılan karşılaştırma "kitapla aynı mıyız" der;  bu blok
    #  "standartla aynı mıyız" der.  İkisi ayrı sorulardır.
    import math as _mt
    from engine.uygulama import mukavemet_tablolari as _MTx

    #  EN 81-20 Çizelge 14  —  darbe katsayıları
    for _tip, _bek in (("Kaymalı", 2), ("Ani Frenlemeli Makaralı", 3),
                       ("Ani Frenlemeli", 5)):
        r.esit(f"EN 81-20 Çiz.14  k1 {_tip}", _MTx.darbe_k1(_tip), _bek)
    r.esit("EN 81-20 Çiz.14  k2 = 1,2  ( hareket )", MK.SABIT["k2"], 1.2)

    #  EN 81-20 Çizelge 15  —  σperm = Rm / St
    for _rm, _nor, _guv in _MTx.RAY_CELIGI:
        r.kontrol(f"EN 81-20 Çiz.15  Rm={_rm} normal ≈ Rm/2,25",
                  abs(_nor - _rm / 2.25) <= 1.2, f"→ {_nor} · kesin {_rm/2.25:.2f}")
        r.kontrol(f"EN 81-20 Çiz.15  Rm={_rm} güv.tert. ≈ Rm/1,8",
                  abs(_guv - _rm / 1.8) <= 1.2, f"→ {_guv} · kesin {_rm/1.8:.2f}")

    #  EN 81-20 m.5.5.2  ·  m.5.6.2.2.1  ·  m.5.7.4.6
    r.esit("EN 81-20 m.5.5.2.1  Dt/dh ≥ 40", MK.SABIT["Dt_dh_asgari"], 40)
    r.esit("EN 81-20 m.5.6.2.2.1.3 c)  Dreg/dreg ≥ 30", MK.SABIT["Dreg_dreg_asgari"], 30)
    r.esit("EN 81-20 m.5.6.2.2.1.3 b)  emniyet katsayısı ≥ 8", MK.SABIT["reg_kat_asgari"], 8)
    r.esit("EN 81-20 m.5.6.2.2.1.1 d)  çekme kuvveti ≥ 300 N", MK.SABIT["reg_kuvvet_asgari"], 300)
    r.esit("EN 81-20 m.5.6.2.2.1.3 b)  μmax = 0,20", MK.SABIT["mu_bloke"], 0.2)
    r.esit("EN 81-20 m.5.7.4.6 a)  δperm = 5 mm", MK.SABIT["dperm_kabin"], 5)
    r.esit("EN 81-20 m.5.7.4.6 b)  δperm = 10 mm", MK.SABIT["dperm_agirlik"], 10)

    #  EN 81-20 Çizelge 6 / 8 / m.5.4.2.3.1  —  kabin alanı
    _CIZ6 = {100: 0.37, 180: 0.58, 225: 0.70, 300: 0.90, 375: 1.10, 400: 1.17,
             450: 1.30, 525: 1.45, 600: 1.60, 630: 1.66, 675: 1.75, 750: 1.90,
             800: 2.00, 825: 2.05, 900: 2.20, 975: 2.35, 1000: 2.40, 1050: 2.50,
             1125: 2.65, 1200: 2.80, 1250: 2.90, 1275: 2.95, 1350: 3.10,
             1425: 3.25, 1500: 3.40, 1600: 3.56, 2000: 4.20, 2500: 5.00}
    _CIZ8 = {1: 0.28, 2: 0.49, 3: 0.60, 4: 0.79, 5: 0.98, 6: 1.17, 7: 1.31,
             8: 1.45, 9: 1.59, 10: 1.73, 11: 1.87, 12: 2.01, 13: 2.15, 14: 2.29,
             15: 2.43, 16: 2.57, 17: 2.71, 18: 2.85, 19: 2.99, 20: 3.13}
    r.esit("EN 81-20 Çiz.6'nın hiçbir yükü eksik değil",
           [q for q in sorted(_CIZ6) if _MTx.kabin_azami_alan(q) is None], [])
    for _q, _a in sorted(_CIZ6.items()):
        r.kontrol(f"EN 81-20 Çiz.6  Q={_q} → {_a} m²",
                  _yakin(_MTx.kabin_azami_alan(_q), _a), f"→ {_MTx.kabin_azami_alan(_q)}")
    for _q, _k, _az, _as in _MTx.KABIN_ALANI:
        r.esit(f"EN 81-20 m.5.4.2.3.1  Q={_q} → kişi", _k, _q // 75)
        _bek = _CIZ8.get(_k) if _k <= 20 else round(3.13 + 0.115 * (_k - 20), 4)
        r.kontrol(f"EN 81-20 Çiz.8  {_k} kişi → {_bek} m²", _yakin(_as, _bek),
                  f"→ {_as}")
    #  320 kg Çizelge 6'da yoktur:  ara değer kuralı ( m.Çiz.6 dipnotu )
    r.kontrol("EN 81-20 Çiz.6 dipnotu  320 kg ara değeri",
              _yakin(_MTx.kabin_azami_alan(320), 0.90 + 0.20 * 20 / 75, 1e-3),
              f"→ {_MTx.kabin_azami_alan(320)}")

    #  EN 81-50 m.5.10.2 / 5.10.3 / 5.10.4 / 5.10.6  —  ray hesabı
    r.esit("EN 81-50 m.5.10.2.1  Mm = 3·Fh·l/16",
           (MK.SABIT["moment_pay"], MK.SABIT["moment_bolen"]), (3, 16))
    r.esit("EN 81-50 m.5.10.4  σ = σk + 0,9·σm", MK.SABIT["birlesik_katsayi"], 0.9)
    r.esit("EN 81-50 m.5.10.6  δ = 0,7·F·l³/(48·E·I)",
           (MK.SABIT["sehim_katsayi"], MK.SABIT["sehim_bolen"]), (0.7, 48))
    #  ω polinomları — standardın kendi katsayıları
    r.esit("EN 81-50 m.5.10.3  Rm=370 eğrisi",
           [(a, round(b, 8), c, d) for a, b, c, d in _MTx.OMEGA_370],
           [(60, 0.0001292, 1.89, 1.0), (85, 0.00004627, 2.14, 1.0),
            (115, 0.00001711, 2.35, 1.04), (250, 0.00016887, 2.0, 0.0)])
    r.esit("EN 81-50 m.5.10.3  Rm=520 eğrisi",
           [(a, round(b, 8), c, d) for a, b, c, d in _MTx.OMEGA_520],
           [(50, 0.0000824, 2.06, 1.021), (70, 0.00001895, 2.41, 1.05),
            (89, 0.00002447, 2.36, 1.03), (250, 0.0002533, 2.0, 0.0)])

    #  EN 81-50 Ek C.2.1.1 — kuvvet · moment · gerilme zinciri
    _sc = MK.hesapla()
    _gc, _hc = _sc["girdi"], _sc["_h"]
    _k1 = _MTx.darbe_k1(_gc["guvenlik_tertibati"])
    _n, _hh = _gc["kabin_ray_sayisi"], _gc["kabin_paten_arasi"]
    _l = _gc["kabin_konsol_arasi"]
    _p = _MTx.RAY_PROFILI
    _Wy = _MTx.ray(_gc["kabin_ray_profili"], "Wy")
    _xc, _xp = _hc["AH293"], _hc["AH295"]
    _xQ = _xc + _gc["kabin_derinligi"] / 8.0
    _Fx = _k1 * 9.81 * (_gc["beyan_yuku"] * _xQ + _gc["kabin_agirligi"] * _xp) / (_n * _hh)
    r.kontrol("EN 81-50 C.2.1.1 a)  Fx = k1·gn·(Q·xQ+P·xP)/(n·h)",
              _yakin(_hc["AY321"], _Fx), f"→ motor {_hc['AY321']!r}, standart {_Fx!r}")
    r.kontrol("EN 81-50 C.2.1.1 a)  σy = (3·Fx·l/16)/Wy",
              _yakin(_hc["AU324"], 3 * _Fx * _l / 16 / _Wy),
              f"→ motor {_hc['AU324']!r}")
    #  C.2.1.2 burkulma
    _Fv = _k1 * 9.81 * (_gc["kabin_agirligi"] + _gc["beyan_yuku"]) / _n + _hc["AH291"] * 9.81
    r.kontrol("EN 81-50 C.2.1.2  Fv = k1·gn·(P+Q)/n + Mg·gn",
              _yakin(_hc["AU351"], _Fv), f"→ motor {_hc['AU351']!r}, standart {_Fv!r}")

    #  ⑪  acil frenleme yavaşlamasının ALT sınırı  ( m.5.11.2.2.2 )
    from engine.uygulama import mukavemet_girdi as _MGa
    r.esit("EN 81-50 m.5.11.2.2.2  asgari yavaşlama 0,5 m/s²",
           _MGa.ACIL_FRENLEME_ASGARI, 0.5)
    for _a, _bek in ((0.05, False), (0.2, False), (0.5, True), (0.8, True),
                     (9.81, True), (10, False)):
        _sa = MK.hesapla({"acil_frenleme_a": _a})
        r.esit(f"a = {_a} m/s² {'kabul' if _bek else 'RED'}", _sa["aktif"], _bek)
    r.kontrol("alt sınır hatası maddeyi yazıyor",
              any("5.11.2.2.2" in x for x in
                  (MK.hesapla({"acil_frenleme_a": 0.2}).get("hata") or [])))

    #  ⑫  sürtünme çarpanı f  —  kanal şekline göre AYRI madde
    import math as _mf
    _O = MK.hesapla()["ozet"] and None
    from engine.uygulama import sabitler as _USf
    _Sf = _USf.sabitler()
    r.esit("EN 81-50  V kanal γ ≥ 35°", _Sf["kanal_gama_v"] >= 35, True)
    r.esit("EN 81-50  yarım daire γ ≥ 25°", _Sf["kanal_gama_yd"] >= 25, True)
    r.esit("EN 81-50  β ≤ 105°", _Sf["kanal_beta"] <= 105, True)

    def _f_std(sekil, isleme, mu):
        """Standardın kendi bağıntısı — motorun koduna bakılmadan."""
        yd = sekil in _MTx.KANAL_YARIM_DAIRE
        b = _mf.radians(_Sf["kanal_beta"] if sekil in _MTx.KANAL_ALTI_KESIK else 0)
        gm = _mf.radians(_Sf["kanal_gama_yd"] if yd else _Sf["kanal_gama_v"])
        if yd:
            return mu * 4 * (_mf.cos(gm/2) - _mf.sin(b/2)) / (
                _mf.pi - b - gm - _mf.sin(b) + _mf.sin(gm))
        if isleme == "Sertleştirilmiş":
            return mu / _mf.sin(gm/2)
        return mu * 4 * (1 - _mf.sin(b/2)) / (_mf.pi - b - _mf.sin(b))

    for _sk in _MTx.KANAL_SEKILLERI:
        for _is in ("Sertleştirilmemiş", "Sertleştirilmiş"):
            _x = MK.hesapla({"kanal_sekli": _sk, "kanal_isleme": _is})
            _h2 = _x["_h"]
            _fm = _h2.get("AU206") if _h2.get("AU206") is not None else _h2.get("AJ198")
            r.kontrol(f"f yükleme  {_sk[:26]} · {_is[:14]}",
                      _yakin(_fm, _f_std(_sk, _is, 0.1)),
                      f"→ motor {_fm!r}, standart {_f_std(_sk, _is, 0.1)!r}")
    #  Kanal şekli f'yi GERÇEKTEN değiştirmeli  ( eskiden değiştirmiyordu )
    _fset = set()
    for _sk in _MTx.KANAL_SEKILLERI:
        _h2 = MK.hesapla({"kanal_sekli": _sk})["_h"]
        _fset.add(round(_h2.get("AU206") or _h2.get("AJ198"), 6))
    r.kontrol("kanal şekli sürtünme çarpanını değiştiriyor", len(_fset) > 1,
              f"→ {_fset}")
    #  Sertleştirilmemiş + alt kesilmesiz V kanal:  standart dışı, uyarı çıkmalı
    _b6 = [b for b in MK.hesapla({"kanal_sekli": "V Kanal",
                                  "kanal_isleme": "Sertleştirilmemiş"})["bolumler"]
           if b["baslik"].startswith("6")][0]
    r.kontrol("alt kesilmesiz sertleştirilmemiş kanal UYARI veriyor",
              any("STANDART DIŞI" in x for x in (_b6.get("notlar") or [])),
              f"→ {_b6.get('notlar')}")

    #  ⑨  motor verimi makine tipine bağlı  ( ofis standardı, TEK KAYNAK )
    from engine.ortak import ofis as _OF
    from engine.uygulama import mukavemet_girdi as _MG
    import engine.avan.tablolar as _AT
    r.kontrol("⑨ verim tablosu avan ile UYGULAMA'da tek kaynak",
              _AT.MAKINE_TIPLERI is _OF.MAKINE_VERIMLERI,
              "→ tablo ikiye ayrılmış;  yeniden ayrışabilir")
    r.esit("⑨ ofis verim tablosu", dict(_OF.MAKINE_VERIMLERI),
           {"Dişlisiz": 0.85, "Dişli": 0.50})
    r.kontrol("⑨ palanga verim düşüşü Δη KALDIRILDI  ( toplamsal model )",
              not hasattr(_OF, "PALANGA_VERIM_DUSUSU"),
              "→ Δη geri gelmiş;  makara kaybı çarpımsaldır, sabit sayı çıkarılamaz")
    r.kontrol("⑨ makine tipi artık girdi ve Excel'de B130'a bağlı",
              ("makine_tipi", "B130") in [(a[0], a[1]) for a in _MG.ALANLAR],
              f"→ {[a[:2] for a in _MG.ALANLAR if a[0] == 'makine_tipi']}")
    #  η TOPLAM SİSTEM VERİMİDİR:  askı oranı onu DEĞİŞTİRMEZ.
    _bek9 = {("Dişlisiz", 1): 0.85, ("Dişlisiz", 2): 0.85,
             ("Dişli", 1): 0.50, ("Dişli", 2): 0.50}
    for (_t, _r2), _e in sorted(_bek9.items()):
        _v = MK.hesapla({"makine_tipi": _t, "aski_orani": _r2})["_h"]["AQ22"]
        r.kontrol(f"⑨ η  {_t} {_r2}:1  = {_e}", _yakin(_v, _e), f"→ {_v!r}")
    _s9 = MK.hesapla({"makine_tipi": "Dişli", "aski_orani": 1})
    _bekN = _s9["_h"]["AQ9"] * _s9["girdi"]["beyan_hizi"] / (0.50 * 102)
    r.kontrol("⑨ N = Gmax·v/(η·102)", _yakin(_s9["_h"]["AQ23"], _bekN),
              f"→ {_s9['_h']['AQ23']!r} ≠ {_bekN!r}")
    r.kontrol("⑨ dişli makine dişlisizden BÜYÜK güç istiyor",
              MK.hesapla({"makine_tipi": "Dişli"})["_h"]["AQ23"]
              > MK.hesapla({"makine_tipi": "Dişlisiz"})["_h"]["AQ23"])
    r.kontrol("⑨ kitabın eski sabiti 0,92 hiçbir senaryoda kullanılmıyor",
              all(not _yakin(MK.hesapla({"makine_tipi": _t, "aski_orani": _r2})["_h"]["AQ22"],
                             0.92) for _t in ("Dişlisiz", "Dişli") for _r2 in (1, 2)))
    from engine.uygulama import girdi as _UG
    import engine.avan.hesap as _AVh
    for _t in ("Dişlisiz", "Dişli"):
        for _r2 in (1, 2):
            _g9 = _UG.tamamla(dict(_UG.varsayilanlar(), makine_tipi=_t, aski_orani=_r2))
            _oz9 = _AVh.hesapla(_UG.kopru(_g9))["asansorler"][0]["ozet"]
            r.kontrol(f"⑨ köprü η′ aynı  ( {_t} {_r2}:1 )",
                      _yakin(_oz9["eta_p"], _bek9[(_t, _r2)]),
                      f"→ avan {_oz9['eta_p']!r}, beklenen {_bek9[(_t, _r2)]}")

    #  ⑧ sığınma açıklıklarının alt sınırları  ( EN 81-20 m.5.2.5.7 / 5.2.5.8 )
    _S = MK.SIGINMA
    r.esit("⑧ ray dibi açıklığı  ( m.5.2.5.8.2 a) 2) · Şekil 7 )",
           _S["min_ray_alt"], 100)
    r.esit("⑧ kuyu dibi - kabin  ( m.5.2.5.8.2 a) )", _S["min_kuyu_tabani"], 500)
    r.esit("⑧ etek açıklığı  ( m.5.2.5.8.2 a) 1) )", _S["min_etek"], 100)
    r.esit("⑧ kuyuya sabit parça  ( m.5.2.5.8.2 b) )", _S["min_regulator"], 300)
    r.esit("⑧ kabin üstü donanım  ( m.5.2.5.7.2 a) )", _S["min_revizyon"], 500)
    r.esit("⑧ ilave kılavuzlu yol  ( m.5.2.5.6.2 )", _S["min_ust_paten"], 100)
    #  Sığınma hacimleri SIGINMA sözlüğünden çıkarıldı:  duruş tipi artık
    #  tesise özel bir BEYAN ( girdi ), ölçüler MT.SIGINMA_HACMI tablosundan.
    r.kontrol("⑧ sığınma hacimleri artık ofis sabiti DEĞİL",
              "ust_hacim" not in _S and "dip_hacim" not in _S, f"→ {sorted(_S)}")
    r.esit("⑧ sığınma duruşları  ( EN 81-20 m.5.2.5.7.1 · m.5.2.5.8.1 )",
           {ad: (a, b, c) for ad, a, b, c in _MT.SIGINMA_HACMI},
           {"Dik duruş": (0.40, 0.50, 2.00), "Çömelme": (0.50, 0.70, 1.00),
            "Yatarak": (0.70, 1.00, 0.50)})
    r.kontrol("⑧ yatarak duruş YALNIZ kuyu dibinde",
              "Yatarak" in _MT.SIGINMA_TIPLERI_DIP
              and "Yatarak" not in _MT.SIGINMA_TIPLERI_UST,
              f"→ üst {_MT.SIGINMA_TIPLERI_UST} · dip {_MT.SIGINMA_TIPLERI_DIP}")
    r.esit("⑧ varsayılan duruş çömelme  ( eski davranış korunuyor )",
           [_MT.siginma_hacmi("Çömelme", "ust"), _MT.siginma_hacmi("Çömelme", "dip")],
           [(0.7, 0.5, 1.0), (0.5, 0.7, 1.0)])
    r.kontrol("⑧ artık ayrı bir min_kabin_ustu sabiti yok",
              "min_kabin_ustu" not in _S, f"→ {sorted(_S)}")

    _b10 = [b for b in s["bolumler"] if b["baslik"].startswith("10")][0]
    _sinir = {}
    for a in _b10["adimlar"]:
        _ac = str(a.get("aciklama") or "")
        if "( en az" in _ac and "mm )" in _ac:
            _sinir[_ac.split("  ( en az")[0]] = float(
                _ac.split("en az")[1].split("mm")[0].strip().replace(".", ""))
    r.esit("⑧ kabin üstü sınırı sığınma yüksekliğinden okunuyor",
           _sinir.get("c.2 - Kabin üstü / kuyu tavanının en alt kısmı arası"),
           _MT.siginma_hacmi("Çömelme", "ust")[2] * 1000)
    r.esit("⑧ ray dibi sınırı pafta metnine de yansıyor",
           _sinir.get("a.2 - Kılavuz raylar / kabinin en alt kısmı arası"), 100.0)
    r.kontrol("⑧ sınıra eşit ölçü UYGUN sayılıyor  ( 'en az' )",
              all(("≥" in str(a.get("aciklama") or "")) or
                  ("mm  >  " not in str(a.get("aciklama") or ""))
                  for a in _b10["adimlar"]),
              "→ '>' karşılaştırması kalmış")
    r.kontrol("⑧ bölüm notu payların ofis kabulü olduğunu söylüyor",
              any("kabulleridir" in x for x in _b10["aciklamalar"]))
    r.kontrol("⑧ bölüm notu açıklıkların standarttan geldiğini söylüyor",
              any("m.5.2.5.7 ve m.5.2.5.8" in x for x in _b10["aciklamalar"]),
              f"→ {_b10['aciklamalar']}")
    return r


def _denetim_bulgulari(r):
    """BAĞIMSIZ DENETİMDE BULUNAN HATALARIN HER BİRİ YENİDEN ÜRETİLİR.

    Testlerin geçmesi hataların yokluğunu göstermez;  aşağıdaki on bulgunun
    hiçbirini paketin geri kalanı yakalamıyordu.  Her kontrol, hatanın ESKİ
    hâlini üreten girdiyle çalışır ve düzeltmenin yerinde durduğunu gösterir.
    """
    from engine.uygulama import mukavemet_girdi as _MG
    from engine.uygulama import mukavemet_tablolari as _MTd
    from engine.uygulama import sabitler as _USd

    #  ── B1  "Sf ≥ Smin" bir geçme ölçütü değildir  ( EN 81-20 m.5.5.2.2 )
    #  Dt 400 · dh 8 · yarım daire kanal:  Sf = 7,89 ( < 12 ) ama gerçekleşen
    #  S = 32,5 — hem Sf'nin hem Smin'in çok üstünde.  Kitap bunu reddediyordu.
    _b1 = MK.hesapla({"tahrik_kasnak_capi": 400, "saptirma_kasnak_capi": 400,
                      "halat_capi": 8, "halat_adedi": 8,
                      "kanal_sekli": "Yarım Daire Kanal"})
    _s4 = [x for x in _b1["bolumler"] if x["baslik"].startswith("4 ")][0]
    r.kontrol("B1  Sf < Smin ama S ikisinin de üstünde → bölüm 4 UYGUN",
              _s4["sonuc"]["uygun"] is True,
              f"→ Sf={_b1['ozet']['Sf']!r} S={_b1['ozet']['S_gercek']!r} "
              f"{_s4['sonuc']['metin']!r}")
    r.kontrol("B1  Sf gerçekten Smin'in altında  ( ölçütün eskiden kestiği yer )",
              _b1["ozet"]["Sf"] < 12 < _b1["ozet"]["S_gercek"],
              f"→ {_b1['ozet']['Sf']!r} / {_b1['ozet']['S_gercek']!r}")
    #  S gerçekten yetersizse bölüm yine kalmalı
    _b1k = MK.hesapla({"tahrik_kasnak_capi": 400, "saptirma_kasnak_capi": 400,
                       "halat_capi": 8, "halat_adedi": 2})
    _s4k = [x for x in _b1k["bolumler"] if x["baslik"].startswith("4 ")][0]
    r.kontrol("B1  S yetersizse bölüm 4 yine UYGUN DEĞİL",
              _s4k["sonuc"]["uygun"] is False,
              f"→ S={_b1k['ozet']['S_gercek']!r}")

    #  ── B2  Sonuç başlığı kontrolün gerçekten kullandığı eşiği yazar
    r.kontrol("B2  bölüm 4 başlığı 40 eşiğini yazıyor",
              "40" in _s4["sonuc"]["baslik"] and "30" not in _s4["sonuc"]["baslik"],
              f"→ {_s4['sonuc']['baslik']!r}")
    r.kontrol("B2  bölüm 4 başlığı S ≥ max( Sf ; Smin ) diyor",
              "max( Sf ; Smin )" in _s4["sonuc"]["baslik"],
              f"→ {_s4['sonuc']['baslik']!r}")

    #  ── B3  ω tanım aralığı dışında ÇÖKME yok, alan adını söyleyen hata var
    _g3 = _MG.tamamla(dict(_MG.varsayilanlar(),
                           kabin_ray_profili="50 x 50 x 5",
                           kabin_konsol_arasi=3900))
    _h3 = _MG.dogrula(_g3)
    r.kontrol("B3  λ > 250 girdi doğrulamasında reddediliyor",
              any("narin" in x and "konsollar arası" in x for x in _h3),
              f"→ {_h3}")
    r.kontrol("B3  hata, izin verilen en büyük aralığı söylüyor",
              any("3.845" in x or "3845" in x for x in _h3), f"→ {_h3}")
    #  İKİNCİ KALKAN:  doğrulama atlansa bile motor çökmemeli
    _dog = MK.MG.dogrula
    try:
        MK.MG.dogrula = lambda g: []
        _s3 = MK.hesapla(_g3)
        _b7 = [x for x in _s3["bolumler"] if x["baslik"].startswith("7 ")][0]
        r.kontrol("B3  doğrulama atlansa bile motor çökmüyor", _s3["aktif"] is True)
        r.kontrol("B3  ω yoksa bölüm 7 UYGUN DEĞİL diyor",
                  _b7["sonuc"]["uygun"] is False)
    except Exception as _e:                                   # noqa: BLE001
        r.kontrol("B3  doğrulama atlansa bile motor çökmüyor", False, f"→ {_e!r}")
    finally:
        MK.MG.dogrula = _dog
    #  λ alt sınırda kırpılıyor  ( bölüm 2 zaten öyle yapıyordu )
    _lam, _om = MK._burkulma_omega(200, 19.48, 370)
    r.esit("B3  λ en az 20'ye kırpılıyor", _lam, 20)
    r.kontrol("B3  kırpılan λ'da ω var", _om is not None)

    #  ── B4  Halat kütlesinin taraf dağılımı  ( EN 81-50 m.5.11.2.2 )
    _o4 = {"ofis": _USd.sabitler(None), "Q": 800.0, "P": 700.0, "r": 2,
           "nh": 7, "gh": 0.152, "F1": 0.0}
    _g4 = _MG.varsayilanlar()
    _tam = _g4["seyir_mesafesi"] * 7 * 0.152
    for _durum, _alt in (("yukleme", True), ("fren_alt", True),
                         ("fren_ust", False), ("bloke", False)):
        _t = MK._terimler(_g4, _o4, _durum)
        _kabinde = _t["MSRcar"] > _t["MSRcwt"]
        r.kontrol(f"B4  '{_durum}' — kabin "
                  + ("EN ALTTA → halat kabin tarafında" if _alt
                     else "EN ÜSTTE → halat ağırlık tarafında"),
                  _kabinde is _alt,
                  f"→ MSRcar={_t['MSRcar']:.2f} MSRcwt={_t['MSRcwt']:.2f}")
        r.kontrol(f"B4  '{_durum}' toplam halat kütlesi korunuyor",
                  _yakin(_t["MSRcar"] + _t["MSRcwt"], _tam, 1e-6),
                  f"→ {_t['MSRcar'] + _t['MSRcwt']:.3f} ≠ {_tam:.3f}")
    #  Yüksek binada karar değişiyor — düzeltmenin emniyet etkisi
    _y = {"seyir_mesafesi": 76.0, "durak_yukseklikleri": [4000] * 19 + [3000],
          "son_kat_yuksekligi": 3000, "halat_capi": 13, "halat_adedi": 8,
          "aski_orani": 1, "tahrik_kasnak_capi": 640,
          "saptirma_kasnak_capi": 640, "motor_gucu": 30}
    _sy = MK.hesapla(_y)
    r.kontrol("B4  76 m seyirde hesap yapılabiliyor", _sy["aktif"] is True,
              f"→ {_sy.get('hata')}")
    if _sy["aktif"]:
        _t1 = MK._terimler(_sy["girdi"], {"ofis": _USd.sabitler(None),
                                          "Q": 800.0, "P": 700.0, "r": 1,
                                          "nh": 8, "gh": 0.64, "F1": 0.0},
                           "yukleme")
        r.kontrol("B4  uzun kuyuda halat kütlesi kabin tarafında  ( yükleme )",
                  _t1["MSRcar"] > 300 and _t1["MSRcwt"] == 0,
                  f"→ {_t1['MSRcar']!r} / {_t1['MSRcwt']!r}")

    #  ── B6  Sarılma açısı α tek sarımda 180°'yi aşamaz
    _g6 = _MG.tamamla(dict(_MG.varsayilanlar(), halat_arasi_yan=200))
    r.kontrol("B6  Ra < Dt girdi doğrulamasında reddediliyor",
              any("Halat arası" in x and "kasnak" in x for x in _MG.dogrula(_g6)),
              f"→ {_MG.dogrula(_g6)}")
    _b6 = [x for x in MK.hesapla()["bolumler"] if x["baslik"].startswith("6 ")][0]
    r.kontrol("B6  bölüm 6'da α aralık kontrolü var",
              any("tek sarımlı" in str(a.get("aciklama", ""))
                  for a in _b6["adimlar"]),
              "→ α kontrol satırı yok")

    #  ── B7  Nequiv(t) ve pafta γ'sı ofis sabitini izliyor
    _n38 = MK.hesapla()["_h"]["AH104"]
    _n45 = MK.hesapla({"_ofis": {"kanal_gama_v": 45}})["_h"]["AH104"]
    #  ALTI KESİK V DE BİR V KANALDIR  ( Çizelge 2'nin V satırı, γ ile ).
    #  Kitap onu β satırından okuyup 5,0 diyordu — bkz. EXCEL_FARKLARI.
    r.esit("B7  altı kesik V, γ = 38° → Nequiv(t) = 12", _n38, 12.0)
    r.esit("B7  altı kesik V γ = 45° → 6,5  ( V satırını izliyor )", _n45, 6.5)
    r.esit("B7  altı kesik V'de β Nequiv'i DEĞİŞTİRMEZ",
           MK.hesapla({"_ofis": {"kanal_beta": 100}})["_h"]["AH104"], 12.0)
    _sb = MK.hesapla({"kanal_sekli": "V Kanal"})["_h"]["AH104"]
    _sb45 = MK.hesapla({"kanal_sekli": "V Kanal",
                        "_ofis": {"kanal_gama_v": 45}})["_h"]["AH104"]
    r.esit("B7  V kanal γ = 38° → 12", _sb, 12.0)
    r.esit("B7  V kanal γ = 45° → 6,5  ( ofis sabiti izleniyor )", _sb45, 6.5)
    #  β satırı ALTI KESİK YARIM DAİRE kanalda geçerlidir
    _uk = {b: MK.hesapla({"kanal_sekli": "Altı Kesik Yarım Daire Kanal",
                          "_ofis": {"kanal_beta": b}})["_h"]["AH104"]
           for b in (90, 100)}
    r.esit("B7  altı kesik yarım daire β = 90° → 5", _uk[90], 5.0)
    r.esit("B7  altı kesik yarım daire β = 100° → 10", _uk[100], 10.0)
    #  Paftaya basılan γ, hesabın kullandığı γ ile aynı mı
    for _sekil, _bek in (("V Kanal", 38), ("Yarım Daire Kanal", 25),
                         ("Altı Kesik V Kanal", 38)):
        _s7 = MK.hesapla({"kanal_sekli": _sekil})
        _b4x = [x for x in _s7["bolumler"] if x["baslik"].startswith("4 ")][0]
        _gam = [a["deger"] for a in _b4x["adimlar"] if a.get("sembol") == "γ"]
        r.esit(f"B7  '{_sekil}' paftada γ = hesabın γ'sı", _gam, [_bek])
    r.kontrol("B7  V kanalın açısı β sütunundan okunmuyor",
              _MTd.kanal_acisi("Altı Kesik V Kanal", 38, 25) == 38,
              "→ altı kesik V kanalda γ hâlâ 90 okunuyor")

    #  ── B8  Mil kuvveti ve moment askı oranına göre iniyor
    _m1 = MK.hesapla({"aski_orani": 1})["_h"]["AQ21"]
    _m2 = MK.hesapla({"aski_orani": 2})["_h"]["AQ21"]
    _p1 = MK.hesapla({"aski_orani": 1})["_h"]["AQ7"]
    _p2 = MK.hesapla({"aski_orani": 2})["_h"]["AQ7"]
    _gmax2 = MK.hesapla({"aski_orani": 2})["_h"]["AQ9"]
    r.kontrol("B8  2:1'de moment = ( Gmax / 2 ) × Dt/2",
              _yakin(_m2, _gmax2 / 2 * 240 / 2000), f"→ {_m2!r} / {_gmax2!r}")
    r.kontrol("B8  askı oranı momenti değiştiriyor", _m1 != _m2 and _p1 != _p2,
              f"→ M {_m1!r}/{_m2!r} · Pm {_p1!r}/{_p2!r}")

    #  ── B9  η TOPLAM SİSTEM VERİMİDİR:  askı oranı verimi değiştirmez
    _v0 = MK.hesapla({"aski_orani": 2})["_h"]["AQ22"]
    _v1 = MK.hesapla({"aski_orani": 1})["_h"]["AQ22"]
    r.kontrol("B9  askı oranı η'yı DEĞİŞTİRMİYOR  ( Δη kaldırıldı )",
              _yakin(_v0, _v1), f"→ 2:1 {_v0!r} · 1:1 {_v1!r}")
    r.kontrol("B9  η ofis tablosundan birebir geliyor",
              _yakin(_v0, _USd.VARSAYILAN["verim_dislisiz"]),
              f"→ {_v0!r} ≠ {_USd.VARSAYILAN['verim_dislisiz']!r}")
    r.kontrol("B9  'toplam_verim' anahtarı artık girdi listesinde yok",
              "toplam_verim" not in [a[0] for a in MK.MG.ALANLAR])

    #  ── B9b  Tst  —  kasnak statik yükü, denge zinciri DÂHİL
    #  Zincir Gmax'ta dengesizliği AZALTIR ama kasnak statik yükünde ARTIRIR;
    #  ikisi ayrı büyüklüktür.  Zincir Tst'ye girmezse yük olduğundan küçük
    #  çıkar ve kasnak yükü aşılmış bir makine "UYGUN" görünür — EMNİYETSİZ.
    _t0 = MK.hesapla({"aski_orani": 2, "denge_zinciri": "Yok"})["ozet"]
    _t1 = MK.hesapla({"aski_orani": 2, "denge_zinciri": "Var"})["ozet"]
    r.kontrol("B9b denge zinciri Tst'yi ARTIRIYOR",
              _t1["Tst_hesap"] > _t0["Tst_hesap"],
              f"→ λ=0 {_t0['Tst_hesap']!r} · λ=100 {_t1['Tst_hesap']!r}")
    r.kontrol("B9b aynı zincir Gmax'ı AZALTIYOR  ( ters yönde )",
              _t1["N_hesap"] < _t0["N_hesap"],
              f"→ λ=0 {_t0['N_hesap']!r} · λ=100 {_t1['N_hesap']!r}")
    #  Artış tam olarak MCR/i kadar olmalı
    _g9 = MK.hesapla({"aski_orani": 2, "denge_zinciri": "Var"})["girdi"]
    _MCR = 2 * _g9["seyir_mesafesi"] * MK.MT.halat_agirlik(_g9["halat_capi"]) \
           * _g9["halat_adedi"]
    r.kontrol("B9b artış tam olarak MCR / i kadar",
              _yakin(_t1["Tst_hesap"] - _t0["Tst_hesap"], _MCR / 2),
              f"→ {_t1['Tst_hesap'] - _t0['Tst_hesap']!r} ≠ {_MCR / 2!r}")
    #  ── B9c  Ds ( EN KÜÇÜK kasnak )  ile  Dp ( ORTALAMA )  AYRI kullanılır
    #  Kp = (Dt/Dp)⁴ ortalama bükülme şiddetidir;  m.5.5.2.1'in D/dr ≥ 40
    #  sınırı ise HER kasnak için geçerlidir — en küçüğe uygulanmalı.
    _dsz = {"tahrik_kasnak_capi": 320, "halat_capi": 8,
            "saptirma_kasnak_capi": 295, "kasnak_tek_yon": 2, "motor_gucu": 11}
    _d_bos = MK.hesapla(dict(_dsz))
    _d_320 = MK.hesapla(dict(_dsz, saptirma_kasnak_min_capi=320))
    _d_200 = MK.hesapla(dict(_dsz, saptirma_kasnak_min_capi=200))
    _b4 = lambda x: [b for b in x["bolumler"] if b["baslik"].startswith("4")][0]
    r.kontrol("B9c Ds boşken ORTALAMA çapa düşülüyor  ( eski davranış )",
              _b4(_d_bos)["sonuc"]["uygun"] is False,
              "→ 295/8 = 36,9 < 40 olmalıydı")
    r.kontrol("B9c Ds = 320 girilince oran kontrolü ONA uygulanıyor",
              _b4(_d_320)["sonuc"]["uygun"] is True,
              f"→ {_b4(_d_320)['sonuc']['metin']}")
    r.kontrol("B9c Ds = 200 girilince reddediliyor",
              _b4(_d_200)["sonuc"]["uygun"] is False)
    r.kontrol("B9c Ds, Sf'yi DEĞİŞTİRMİYOR  ( Kp hâlâ ortalamadan )",
              _yakin(_d_bos["ozet"]["Sf"], _d_320["ozet"]["Sf"])
              and _yakin(_d_bos["ozet"]["Sf"], _d_200["ozet"]["Sf"]),
              f"→ {_d_bos['ozet']['Sf']!r} · {_d_320['ozet']['Sf']!r} · "
              f"{_d_200['ozet']['Sf']!r}")

    #  ── B9d  Denge zinciri TAHRİK hesabına da girer  ( EN 81-50 m.5.11.2 )
    #  MCRcar / MCRcwt terimleri _T1 / _T2'de vardı ama hiç atanmıyordu.
    #  Zincirin dağılımı HALATIN TAM TERSİDİR ve toplamı her konumda sabittir.
    def _ter(zincir, durum):
        _g = MK.hesapla({"aski_orani": 2, "denge_zinciri": zincir})["girdi"]
        _o = {"ofis": MK.US.sabitler(None)}
        MK._motor(_g, _o)
        return MK._terimler(_g, _o, durum), _o
    for _d in ("yukleme", "fren_alt", "fren_ust", "bloke"):
        _t0, _ = _ter("Yok", _d)
        r.kontrol(f"B9d zincirsizde MCR terimleri sıfır  ( {_d} )",
                  _t0["MCRcar"] == 0.0 and _t0["MCRcwt"] == 0.0,
                  f"→ {_t0['MCRcar']!r} / {_t0['MCRcwt']!r}")
    _talt, _o1 = _ter("Var", "yukleme")     # kabin EN ALTTA
    _tust, _ = _ter("Var", "bloke")         # kabin EN ÜSTTE
    _MCR = _o1["MCR"]
    r.kontrol("B9d kabin EN ALTTA → zincir KARŞI AĞIRLIK tarafında",
              _yakin(_talt["MCRcar"], 0.0) and _yakin(_talt["MCRcwt"], _MCR),
              f"→ car {_talt['MCRcar']!r} · cwt {_talt['MCRcwt']!r} · MCR {_MCR!r}")
    r.kontrol("B9d kabin EN ÜSTTE → zincir KABİN tarafında",
              _yakin(_tust["MCRcar"], _MCR) and _yakin(_tust["MCRcwt"], 0.0),
              f"→ car {_tust['MCRcar']!r} · cwt {_tust['MCRcwt']!r}")
    r.kontrol("B9d zincir kütlesi her konumda KORUNUYOR",
              _yakin(_talt["MCRcar"] + _talt["MCRcwt"],
                     _tust["MCRcar"] + _tust["MCRcwt"]))
    r.kontrol("B9d zincir dağılımı HALATIN TERSİ",
              (_talt["MSRcar"] > _talt["MSRcwt"]) != (_talt["MCRcar"] > _talt["MCRcwt"]),
              f"→ MSR {_talt['MSRcar']:.1f}/{_talt['MSRcwt']:.1f} · "
              f"MCR {_talt['MCRcar']:.1f}/{_talt['MCRcwt']:.1f}")

    r.kontrol("B9b Tst girilmezse kontrol yapılmıyor, karar bozulmuyor",
              MK.hesapla({"motor_gucu": 11})["bolumler"][0]["sonuc"]["uygun"] is True
              and MK.hesapla({"motor_gucu": 11, "makine_tst": 100000}
                             )["bolumler"][0]["sonuc"]["uygun"] is True)

    #  ── B10  Kabin önü girintisi  ( EN 81-20 m.5.4.2.1.3 )
    _a90 = MK.hesapla({"uzun_pervaz": 90})["ozet"]["kabin_alani"]
    _a100 = MK.hesapla({"uzun_pervaz": 100})["ozet"]["kabin_alani"]
    _a300 = MK.hesapla({"uzun_pervaz": 300})["ozet"]["kabin_alani"]
    _kuru = 1450 * 1350 / 1e6
    r.kontrol("B10  pervaz ≤ 100 mm alana katılmıyor",
              _yakin(_a90, _kuru) and _yakin(_a100, _kuru),
              f"→ 90:{_a90!r} 100:{_a100!r} kuru:{_kuru!r}")
    r.kontrol("B10  pervaz > 100 mm ise girintinin TAMAMI katılıyor",
              _yakin(_a300, _kuru + 900 * 300 / 1e6),
              f"→ {_a300!r} ≠ {_kuru + 0.27!r}")

    #  ── B12  Regülatör:  ÇEKME kuvveti ve ikinci sınır imalatçıdan gelir
    #  m.5.6.2.2.1.1 d) regülatörün ÜRETTİĞİ kuvveti sınırlar — kasnağın iki
    #  yanındaki gerginlik FARKI ( Fçekme = F'reg − Freg ).  m.5.6.2.2.1.3 b)
    #  ise halattaki EN BÜYÜK gerginliği ( F'reg ) emniyet katsayısına sokar.
    #  Kitap ikisini de F'reg ile yapıyordu.
    _s5 = MK.hesapla()
    _b5 = [x for x in _s5["bolumler"] if x["baslik"].startswith("5 ")][0]
    _h5 = _s5["_h"]
    r.kontrol("B12  Fçekme = F'reg − Freg",
              _yakin(_h5["U156"], _h5["J156"] - _h5["W151"]),
              f"→ {_h5['U156']!r} ≠ {_h5['J156'] - _h5['W151']!r}")
    r.kontrol("B12  Fçekme halattaki toplam gerginlikten KÜÇÜK",
              0 < _h5["U156"] < _h5["J156"], f"→ {_h5['U156']!r} / {_h5['J156']!r}")
    r.kontrol("B12  emniyet katsayısı F'reg ile hesaplanıyor  ( m.5.6.2.2.1.3 b )",
              _yakin(_h5["G161"], _h5["AI136"] / _h5["J156"]),
              f"→ {_h5['G161']!r}")
    r.esit("B12  imalatçı kuvveti yoksa sınır 300 N", _h5["AA156"], 300)
    #  Girilmemişse madde DENETLENEMEZ:  bölüm 'HESAP EKSİK' der ve proje
    #  'uygundur' çıkmaz.
    r.kontrol("B12  imalatçı kuvveti yoksa bölüm HESAP EKSİK diyor",
              _b5["sonuc"]["uygun"] is False
              and "HESAP EKSİK" in _b5["sonuc"]["metin"],
              f"→ {_b5['sonuc']!r}")
    r.esit("B12  eksik hesap özete giriyor", _s5["ozet"]["eksik_hesap"],
           [_b5["sonuc"]["metin"]])
    r.kontrol("B12  eksik hesapla proje uygun çıkmıyor",
              _s5["ozet"]["tumu_uygun"] is False)
    r.kontrol("B12  imalatçı kuvveti yoksa bölüm sebebini yazıyor",
              any("İNCELEME" in x.upper() for x in (_b5.get("notlar") or [])),
              f"→ {_b5.get('notlar')}")
    r.esit("B12  imalatçı kuvveti girilince sınır 2 katı",
           MK.hesapla({"guvenlik_devreye_kuvvet": 900})["_h"]["AA156"], 1800)
    r.esit("B12  küçük imalatçı kuvvetinde 300 N belirleyici",
           MK.hesapla({"guvenlik_devreye_kuvvet": 100})["_h"]["AA156"], 300)
    #  Kuvvet girilince bölüm yeniden hesaplanabilir hâle gelir
    _b5v = [x for x in MK.hesapla({"guvenlik_devreye_kuvvet": 200})["bolumler"]
            if x["baslik"].startswith("5 ")][0]
    r.kontrol("B12  kuvvet girilince bölüm hesaplanıyor",
              _b5v["sonuc"]["uygun"] is True and "EKSİK" not in _b5v["sonuc"]["metin"],
              f"→ {_b5v['sonuc']!r}")
    #  Ölçüt gerçekten Fçekme ile:  çok büyük bir imalatçı kuvvetinde kalmalı
    _b5r = [x for x in MK.hesapla({"guvenlik_devreye_kuvvet": 9000})["bolumler"]
            if x["baslik"].startswith("5 ")][0]
    r.kontrol("B12  aşırı imalatçı kuvvetinde bölüm kalıyor",
              _b5r["sonuc"]["uygun"] is False)

    # Toplam gerginin geçtiği, NET çekmenin kaldığı gerçek regresyon aralığı.
    _net = MK.hesapla({"guvenlik_devreye_kuvvet": 1100})
    r.kontrol("B12 net çekme yetersizken toplam gerilme uygunluk vermez",
              _net["_h"]["J156"] > 2200 > _net["_h"]["U156"]
              and _net["bolumler"][4]["sonuc"]["uygun"] is False)

    #  ── B12.2  Kabin tertibatı hız sınırı  ( TS EN 81-20 m.5.6.2.1.2.1 b) )
    _b5_ani_hizli = MK.hesapla({"beyan_hizi": 1.0, "guvenlik_tertibati": "Ani Frenlemeli",
                                "guvenlik_devreye_kuvvet": 400})["bolumler"][4]
    r.kontrol("B12.2  v > 0,63 iken ani frenlemeli kabin tertibatı reddedilir",
              _b5_ani_hizli["sonuc"]["uygun"] is False
              and "0,63" in _b5_ani_hizli["sonuc"]["metin"],
              f"→ {_b5_ani_hizli['sonuc']!r}")

    _b5_ani_yavas = MK.hesapla({"beyan_hizi": 0.63, "guvenlik_tertibati": "Ani Frenlemeli",
                                "guvenlik_devreye_kuvvet": 400})["bolumler"][4]
    r.kontrol("B12.2  v ≤ 0,63 iken ani frenlemeli kabin tertibatı kabul edilir",
              _b5_ani_yavas["sonuc"]["uygun"] is True,
              f"→ {_b5_ani_yavas['sonuc']!r}")

    #  ── B12.3  Regülatör devreye girme hızı penceresi  ( m.5.6.2.2.1.1 a) )
    _b5_reg_dusuk = MK.hesapla({"beyan_hizi": 1.0, "guvenlik_devreye_kuvvet": 400,
                                "reg_devreye_hizi": 1.05})["bolumler"][4]
    r.kontrol("B12.3  v_dev < 1,15·v reddedilir",
              _b5_reg_dusuk["sonuc"]["uygun"] is False,
              f"→ {_b5_reg_dusuk['sonuc']!r}")

    _b5_reg_uygun = MK.hesapla({"beyan_hizi": 1.0, "guvenlik_devreye_kuvvet": 400,
                                "reg_devreye_hizi": 1.25})["bolumler"][4]
    r.kontrol("B12.3  1,15·v ≤ v_dev < v_üst kabul edilir",
              _b5_reg_uygun["sonuc"]["uygun"] is True,
              f"→ {_b5_reg_uygun['sonuc']!r}")

    #  ── B13  Karşı ağırlıkta güvenlik tertibatı  ( EN 81-50 Ek C.2.1 )
    _yok = MK.hesapla()["bolumler"][7]
    _var = MK.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı"})["bolumler"][7]
    r.kontrol("B13  tertibat yokken C.2.1 hesaplanmıyor",
              "C.2.1" not in _yok["baslik"] + str(_yok.get("kaynak", "")),
              f"→ {_yok['baslik']!r}")
    r.kontrol("B13  tertibat varken C.2.1 adımları geliyor",
              any("m.C.2.1" in str(a.get("deger", "")) for a in _var["adimlar"]),
              "→ C.2.1 başlığı yok")
    r.kontrol("B13  C.2.1 adım sayısını artırıyor",
              len(_var["adimlar"]) > len(_yok["adimlar"]) + 10,
              f"→ {len(_yok['adimlar'])} → {len(_var['adimlar'])}")
    #  k1 büyüdükçe ray zorlanır:  ani frenlemeli tertibatta 50x50x5 kalmalı
    r.kontrol("B13  ani frenlemeli tertibatta ince ray UYGUN DEĞİL",
              MK.hesapla({"agirlik_guvenlik_tertibati": "Ani Frenlemeli"}
                         )["bolumler"][7]["sonuc"]["uygun"] is False)

    #  ── B13.2  Karşı ağırlık tertibatı hız sınırı  ( TS EN 81-20 m.5.6.2.1.2.3 )
    _b8_ani_hizli = MK.hesapla({"beyan_hizi": 1.6,
                                "agirlik_guvenlik_tertibati": "Ani Frenlemeli",
                                "agirlik_ray_profili": "70 x 65 x 9"})["bolumler"][7]
    r.kontrol("B13.2  v > 1,0 iken ani frenlemeli karşı ağırlık tertibatı reddedilir",
              _b8_ani_hizli["sonuc"]["uygun"] is False
              and "kaymalı tip olmalıdır" in _b8_ani_hizli["sonuc"]["metin"],
              f"→ {_b8_ani_hizli['sonuc']!r}")

    _b8_kaymali_hizli = MK.hesapla({"beyan_hizi": 1.6,
                                    "agirlik_guvenlik_tertibati": "Kaymalı",
                                    "agirlik_ray_profili": "70 x 65 x 9"})["bolumler"][7]
    r.kontrol("B13.2  v > 1,0 iken kaymalı karşı ağırlık tertibatı kabul edilir",
              _b8_kaymali_hizli["sonuc"]["uygun"] is True,
              f"→ {_b8_kaymali_hizli['sonuc']!r}")

    #  ── B16  Regülatör μ'sünün üst sınırı  ( EN 81-20 m.5.6.2.2.1.3 b) )
    _g16 = _MG.tamamla(dict(_MG.varsayilanlar(), reg_surtunme=5))
    r.kontrol("B16  μ > 0,2 reddediliyor",
              any("µmax" in x or "0.2" in x or "0,2" in x
                  for x in _MG.dogrula(_g16)), f"→ {_MG.dogrula(_g16)}")
    r.esit("B16  sınır standardın verdiği değer", _MG.REG_MU_AZAMI, 0.2)

    #  ── B14  C.2.2'de ω YOKTUR — denetimin şüphesi yersizdi
    #  EN 81-50 Ek C.2.2.2:  σv = ( Fv + k3·Maux ) / A.  ω yalnız C.2.1.2'de
    #  geçer.  Motor bunu doğru yapıyor;  burada geri dönmediği denetlenir.
    _sc = MK.hesapla()
    _pc = _MTd.ray("89 x 62 x 15,88", "A")
    _fv = _sc["ozet"]["Mg_kabin"] * 9.81
    _bek = (_fv + 1.2 * 150) / _pc                    # ω YOK
    _b7c = [x for x in _sc["bolumler"] if x["baslik"].startswith("7 ")][0]
    _sv = [a["deger"] for a in _b7c["adimlar"]
           if str(a.get("formul", "")).startswith("σv = ")]
    r.esit("B14  C.2.2'de tek bir σv satırı var", len(_sv), 1)
    r.kontrol("B14  C.2.2'de burkulma ω'sız  ( EN 81-50 Ek C.2.2.2 )",
              bool(_sv) and _yakin(_sv[0], _bek),
              f"→ σv = {_sv!r}, ω'sız beklenen {_bek!r}")
    #  C.2.1'de ω VARDIR — iki durumun ayrıldığı da denetlenir
    _sk = [a["deger"] for a in _b7c["adimlar"]
           if str(a.get("formul", "")).startswith("σk = ")]
    r.kontrol("B14  C.2.1'de ω uygulanıyor  ( iki durum ayrı )",
              bool(_sk) and _sk[0] > _bek, f"→ σk = {_sk!r}")

    #  ══════════════════════════════════════════════════════════════
    #  ÜÇÜNCÜ TUR  —  SAYISAL FİZİK DENETİMİNDE BULUNANLAR
    #  ══════════════════════════════════════════════════════════════
    #  ── C1  σ ve δ BÜYÜKLÜKTÜR;  işaretli karşılaştırma emniyetsizdi
    #  Kabin merkezi ray ekseninin öbür yanına düşünce ( xc < 0 ) Fx negatife
    #  iner;  δ = −5,59 mm iken "δ ≤ 5" SESSİZCE geçiyordu.
    _c1 = MK.hesapla({"kabin_genisligi": 900, "ray_kapi_arasi": 1200,
                      "kabin_konsol_arasi": 3800})
    r.kontrol("C1  negatif geometrili proje hesaplanabiliyor", _c1["aktif"],
              f"→ {_c1.get('hata')}")
    _b7c1 = [x for x in _c1["bolumler"] if x["baslik"].startswith("7 ")][0]
    _sayilar = [a["deger"] for a in _b7c1["adimlar"]
                if isinstance(a["deger"], (int, float))
                and not isinstance(a["deger"], bool)]
    r.kontrol("C1  Fx işaretini koruyor  ( yön bilgisi paftada kalıyor )",
              any(x < 0 for x in _sayilar), "→ hiç negatif kuvvet yok")
    for _ad, _on in (("σ", "σ"), ("δ", "δ")):
        _deg = [a["deger"] for a in _b7c1["adimlar"]
                if str(a.get("formul", "")).startswith(_on)
                and isinstance(a["deger"], (int, float))]
        r.kontrol(f"C1  hiçbir {_ad} negatif yazılmıyor",
                  all(x >= 0 for x in _deg), f"→ {[x for x in _deg if x < 0]}")
    _dx = [a for a in _b7c1["adimlar"]
           if str(a.get("aciklama", "")).startswith("δx")]
    r.kontrol("C1  δ = 5,59 mm  >  5 mm  →  UYGUN DEĞİL",
              any(a["deger"] == "UYGUN DEĞİL" for a in _dx),
              f"→ {[(a['aciklama'][:34], a['deger']) for a in _dx]}")
    r.kontrol("C1  bölüm 7 bu geometride kalıyor",
              _b7c1["sonuc"]["uygun"] is False, f"→ {_b7c1['sonuc']}")
    #  σm artık iki eğilmeyi TOPLUYOR  ( ters işaretliler birbirini götürmüyor )
    _sm = [a["deger"] for a in _b7c1["adimlar"]
           if str(a.get("formul", "")).startswith("σm = ")]
    r.kontrol("C1  σm = |σx| + |σy|  ( götürme yok )",
              bool(_sm) and all(x >= 0 for x in _sm), f"→ {_sm}")

    #  ── C2  Karşı ağırlık tertibatının tepkisi kuyu tabanına gelir
    _far0 = MK.hesapla()["ozet"]["FAR"]
    _mc = MK.hesapla()["girdi"]["karsi_agirlik"]
    _n = MK.hesapla()["girdi"]["agirlik_ray_sayisi"]
    for _tip in ("Kaymalı", "Ani Frenlemeli Makaralı", "Ani Frenlemeli"):
        _k1 = _MTd.darbe_k1(_tip)
        _far = MK.hesapla({"agirlik_guvenlik_tertibati": _tip})["ozet"]["FAR"]
        _bek2 = _far0 + _k1 * MK.SABIT["gn"] * _mc / _n
        r.kontrol(f"C2  '{_tip}' tepkisi FAR'a giriyor  "
                  f"( {_far0:.0f} → {_far:.0f} N )",
                  _yakin(_far, _bek2), f"→ {_far!r} ≠ {_bek2!r}")
    r.kontrol("C2  tertibat yokken FAR değişmiyor",
              _yakin(MK.hesapla({"agirlik_guvenlik_tertibati": "Yok"}
                                )["ozet"]["FAR"], _far0))
    #  RAY KÜTLESİ BURADA DA BİR KEZ SAYILIR.  Bölüm 8'in Fk'si  Mg·gn'i
    #  içerir;  tabana giden tepki  Fk − Mg·gn  olmalıdır — yoksa ray hattının
    #  ağırlığı FAR'da iki kez görünürdü ( kabin tarafında düzeltilen ⑬ ).
    _s2 = MK.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı"})
    _mg_a = _s2["ozet"]["Mg_agirlik"] * MK.SABIT["gn"]
    _tepki = _s2["ozet"]["FAR"] - _far0
    r.kontrol("C2  tepkide ray kütlesi yok  ( Fk − Mg·gn )",
              _yakin(_tepki, 2 * MK.SABIT["gn"] * _mc / _n),
              f"→ tepki {_tepki!r},  Mg·gn = {_mg_a!r}")
    r.kontrol("C2  FAR özet ile hücre aynı", _yakin(_s2["_h"]["AN616"],
                                                   _s2["ozet"]["FAR"]))

    #  ── C3  Karşı ağırlık kütlesi TEK yerden türer  ( ofis q'su )
    for _q in (0.40, 0.45, 0.50, 0.55, 0.60):
        _s3 = MK.hesapla({"kabin_agirligi": 700, "beyan_yuku": 800,
                          "_ofis": {"q_denge": _q}})
        _ga = _s3["_h"]["AQ13"]            # bölüm 1  —  motor · ağırlık tamponu
        _mcwt = _s3["girdi"]["karsi_agirlik"]   # bölüm 6 tahrik · bölüm 8 ray
        r.esit(f"C3  q = {_q}  →  Ga = Mcwt", (_ga, _mcwt),
               (700 + _q * 800, 700 + _q * 800))
        #  Ağırlık tamponu da aynı kütleyi görür
        r.kontrol(f"C3  q = {_q}  ağırlık tamponu aynı kütleyle",
                  _yakin(_s3["ozet"]["Fat"],
                         MK.SABIT["tampon_katsayi"] * MK.SABIT["gn"] * _mcwt),
                  f"→ {_s3['ozet']['Fat']!r}")

    #  ══════════════════════════════════════════════════════════════
    #  DÖRDÜNCÜ TUR  —  SINIR DURUMLARI
    #  ══════════════════════════════════════════════════════════════
    #  ── D1  Sistem verimi η fiziksel olmalı  ( 0 < η ≤ 1 )
    #  Δη KALDIRILDIĞI için η artık kendi başına negatife düşemez;  eski
    #  senaryolar ( η = 0,10 · Δη = 0,10 → sıfıra bölme;  Δη = 0,20 →
    #  η′ = −0,10 ve N = −44,26 kW ) yapısal olarak imkânsızdır.  Kalan risk
    #  ofis sabitinin kendisidir:  aralık dışı değer REDDEDİLİP varsayılana
    #  dönmeli, sessizce kullanılmamalı.
    for _kotu in (0, -0.5, 1.5):
        _d1 = MK.hesapla({"_ofis": {"verim_dislisiz": _kotu}})
        r.kontrol(f"D1  η = {_kotu} reddedilip varsayılana dönüyor",
                  _d1["aktif"] is True
                  and _yakin(_d1["_h"]["AQ22"], _USd.VARSAYILAN["verim_dislisiz"]),
                  f"→ aktif {_d1['aktif']} · η {_d1.get('_h', {}).get('AQ22')!r}")
    r.kontrol("D1  η = 1 sınırı kabul ediliyor",
              MK.hesapla({"_ofis": {"verim_dislisiz": 1.0}})["aktif"] is True)
    #  İKİNCİ KALKAN:  doğrulama ATLANSA ve η yine de sıfır gelse bile
    #  N sıfıra bölünmemeli  ( motor doğrudan çağrıldığında ).
    _dog1, _ver1 = MK.MG.dogrula, MK.US.verim
    try:
        MK.MG.dogrula = lambda g: []
        MK.US.verim = lambda *a, **k: 0.0
        _d1x = MK.hesapla({})
        r.kontrol("D1  doğrulama atlansa bile sıfıra bölünmüyor",
                  _d1x["aktif"] is True
                  and _d1x["ozet"]["tumu_uygun"] is False)
        r.kontrol("D1  bölüm 1 'HESAP YAPILAMADI' diyor",
                  any("HESAP YAPILAMADI" in (x.get("sonuc") or {}).get("metin", "")
                      for x in _d1x["bolumler"]))
    except Exception as _e:                                   # noqa: BLE001
        r.kontrol("D1  doğrulama atlansa bile sıfıra bölünmüyor", False,
                  f"→ {_e!r}")
    finally:
        MK.MG.dogrula, MK.US.verim = _dog1, _ver1

    #  ── D2  Tampon / paten yığını kuyuya sığmalı  ( halat boyu > 0 )
    #  30 m paten arasında lh = −4,82 m, Gh = −5,13 kg;  negatif ağırlık
    #  yükten DÜŞÜLÜYOR — motor gücünü azaltıp Sf'yi yükseltiyordu.
    _d2 = MK.hesapla({"kabin_paten_arasi": 30000})
    r.kontrol("D2  yığın kuyuya sığmıyorsa reddediliyor", _d2["aktif"] is False)
    r.kontrol("D2  hata yığını ve kuyu boyunu sayıyor",
              any("yığını" in x and "kuyu boyundan" in x
                  for x in (_d2.get("hata") or [])), f"→ {_d2.get('hata')}")
    #  SINIRDA da reddedilmeli:  yığın TAM kuyu boyuna eşitken halat boyu
    #  ( paydan önce ) sıfırdır — fiziksel değildir.
    _gv = _MG.tamamla(_MG.varsayilanlar())
    _tam = (_gv["kuyu_boyu"] - _gv["agirlik_tampon_baba"]
            - _gv["agirlik_carpma_arasi"] + _gv["agirlik_tampon_ezilme"]
            - _gv["agirlik_paten_arasi"])
    r.kontrol("D2  sınırda ( yığın = kuyu boyu ) da reddediliyor",
              MK.hesapla({"kabin_paten_arasi": _tam})["aktif"] is False,
              f"→ kabin paten arası {_tam:g} mm")
    r.kontrol("D2  sınırın 1 mm altı kabul ediliyor",
              MK.hesapla({"kabin_paten_arasi": _tam - 1})["aktif"] is True)
    #  Normal geometri geçmeye devam ediyor
    r.kontrol("D2  normal paten arası kabul ediliyor",
              MK.hesapla({"kabin_paten_arasi": 3400})["aktif"] is True)
    _dog2 = MK.MG.dogrula
    try:
        MK.MG.dogrula = lambda g: []
        _d2x = MK.hesapla({"kabin_paten_arasi": 30000})
        r.kontrol("D2  doğrulama atlansa bile negatif halat 'uygun' olmuyor",
                  _d2x["ozet"]["tumu_uygun"] is False)
        r.kontrol("D2  negatif halat boyunda güç hesaplanmıyor",
                  _d2x["_h"].get("AQ23") is None, f"→ {_d2x['_h'].get('AQ23')!r}")
    finally:
        MK.MG.dogrula = _dog2

    #  ══════════════════════════════════════════════════════════════
    #  BEŞİNCİ TUR  —  SAPTIRMA KASNAĞI
    #  ══════════════════════════════════════════════════════════════
    #  ── E1  Dp / dh ≥ 40 denetlenmiyordu  ( TS EN 81-20 m.5.5.2.1 )
    #  Madde oranı "kasnak, makara ve tamburlar" için ister;  kitap yalnız
    #  TAHRİK kasnağını sınıyordu.  Dt/dh = 400/8 = 50 ama Dp/dh = 240/8 = 30
    #  olan tesiste halat bölümü UYGUN çıkıyordu.
    _e_g = {"halat_capi": 8, "tahrik_kasnak_capi": 400, "saptirma_kasnak_capi": 240}

    def _b4(**ek):
        _s = MK.hesapla(dict(_e_g, **ek))
        if not _s["aktif"]:
            return None, _s
        return [x for x in _s["bolumler"] if x["baslik"].startswith("4 ")][0], _s

    _e1b, _e1s = _b4()
    r.kontrol("E1  denetimin girdisi hesaplanabiliyor", _e1b is not None,
              f"→ {_e1s.get('hata')}")
    r.kontrol("E1  Ds/dh = 30 halat bölümünü DÜŞÜRÜYOR",
              _e1b["sonuc"]["uygun"] is False)
    r.kontrol("E1  gerekçe saptırma kasnağını adıyla söylüyor",
              "saptırma kasnağı" in _e1b["sonuc"]["metin"],
              f"→ {_e1b['sonuc']['metin']!r}")
    #  Oran kontrolü artık EN KÜÇÜK kasnak çapına ( Ds ) uygulanır;  Ds
    #  girilmezse ortalamaya düşülür, yani bu senaryoda sonuç değişmez.
    r.kontrol("E1  bölüm başlığı Ds/dh ölçütünü duyuruyor",
              "Ds/dh" in _e1b["sonuc"]["baslik"], f"→ {_e1b['sonuc']['baslik']!r}")
    _dpsat = [a for a in _e1b["adimlar"]
              if "Ds / dh" in str(a.get("aciklama") or "")]
    r.kontrol("E1  paftada Ds/dh kontrol satırı var", bool(_dpsat),
              f"→ {[a.get('aciklama') for a in _e1b['adimlar']][:6]}")
    r.kontrol("E1  o satır UYGUN DEĞİL diyor",
              bool(_dpsat) and _dpsat[0]["deger"] == "UYGUN DEĞİL",
              f"→ {_dpsat[0]['deger'] if _dpsat else None!r}")
    #  SINIR:  tam 40 geçer, 1 mm altı geçmez  ( dh = 8 → Dp = 320 )
    r.kontrol("E1  Ds/dh = 40 tam sınırı kabul ediliyor",
              _b4(saptirma_kasnak_capi=320)[0]["sonuc"]["uygun"] is True)
    r.kontrol("E1  sınırın 1 mm altı reddediliyor",
              _b4(saptirma_kasnak_capi=319)[0]["sonuc"]["uygun"] is False)
    #  Tahrik kasnağı denetimi bozulmadı
    r.kontrol("E1  tahrik kasnağı denetimi yerinde duruyor",
              _b4(tahrik_kasnak_capi=240, saptirma_kasnak_capi=320)[0]
              ["sonuc"]["uygun"] is False)
    #  KASNAK YOKSA denetlenecek kasnak da yoktur
    _e1y = _b4(kasnak_tek_yon=0, kasnak_ters_yon=0)[0]
    r.kontrol("E1  kasnak yokken Ds oranı aranmıyor",
              _e1y["sonuc"]["uygun"] is True and "Ds/dh" not in _e1y["sonuc"]["baslik"],
              f"→ {_e1y['sonuc']['baslik']!r}")
    r.kontrol("E1  kasnak yokken pafta bunu YAZIYOR",
              any("kasnak yok" in str(a.get("deger") or "") for a in _e1y["adimlar"]),
              f"→ {[a.get('deger') for a in _e1y['adimlar']][:4]}")
    #  Varsayılan proje bu yüzden düşmemeli  ( Dt = Dp = 240, dh = 10 → 24 )
    _v = MK.hesapla({})
    _vb4 = [x for x in _v["bolumler"] if x["baslik"].startswith("4 ")][0]
    r.kontrol("E1  varsayılan projede iki oran da AYNI sonucu veriyor",
              ("Dt/dh" in _vb4["sonuc"]["baslik"]) and ("Ds/dh" in _vb4["sonuc"]["baslik"]))
    #  Sapma kaydı bu bulguyu taşıyor
    r.kontrol("E1  sapma kaydında yazılı",
              any("Saptırma kasnağı" in ad for ad, *_ in MK.EXCEL_FARKLARI))

    #  ── E2  xp RAY EKSENİNDEN ölçülmeli  ( TS EN 81-50 Ek C.2.1.1 )
    #  Fx = k1·gn·( Q·xQ + P·xp )/( n·h ) payı ray eksenine göre devirici
    #  momenttir;  xQ ray ekseninden ( xQ = xc + D/8 ), xp ise KABİN
    #  MERKEZİNDEN ölçülüyordu ve ray–kapı arası değişince hiç kımıldamıyordu.
    def _xcxp(**ek):
        _s = MK.hesapla(dict({"kabin_derinligi": 1400, "kabin_agirligi": 650}, **ek))
        if not _s["aktif"]:
            return None, None, _s
        _b = [x for x in _s["bolumler"] if x["baslik"].startswith("7 ")][0]
        _d = {a.get("sembol"): a["deger"] for a in _b["adimlar"] if a.get("sembol")}
        return _d.get("xc"), _d.get("xp"), _s

    #  Kapının kabin merkezine göre katkısı:  mkapı·( D/2 + pay ) / P
    _gv = _MG.tamamla(_MG.varsayilanlar())
    _kapi = _gv["kapi_agirligi"] * (1400 / 2 + _gv["kapi_mekanizma_payi"]) / 650
    _degerler = []
    for _rk in (500, 650, 830, 1000):
        _xc, _xp, _ = _xcxp(ray_kapi_arasi=_rk)
        _degerler.append((_rk, _xc, _xp))
        r.kontrol(f"E2  RK={_rk}: xp = xc − mkapı·(D/2+pay)/P",
                  _xp is not None and abs(_xp - (_xc - _kapi)) < 1e-9,
                  f"→ xc={_xc}, xp={_xp}, beklenen {_xc - _kapi if _xc is not None else None}")
    #  ASIL BULGU:  xp artık ray–kapı arasını İZLİYOR  ( eskiden sabitti )
    r.kontrol("E2  xp ray–kapı arasıyla değişiyor",
              len({round(x[2], 6) for x in _degerler}) == len(_degerler),
              f"→ {[(x[0], x[2]) for x in _degerler]}")
    #  Ray ekseni kabin merkezinden geçerken ( xc = 0 ) xp yalnız kapıdır
    _xc0, _xp0, _ = _xcxp(ray_kapi_arasi=1400 / 2 + MK.SABIT["kabin_merkez_payi"])
    r.kontrol("E2  xc = 0 iken xp = −kapı katkısı", abs(_xc0) < 1e-9
              and abs(_xp0 + _kapi) < 1e-9, f"→ xc={_xc0}, xp={_xp0}")
    #  EMNİYETSİZ YÖN:  ray kapıya yaklaştıkça devirici moment BÜYÜR
    _mom = []
    for _rk in (500, 830):
        _xc, _xp, _s2 = _xcxp(ray_kapi_arasi=_rk)
        _b2 = [x for x in _s2["bolumler"] if x["baslik"].startswith("7 ")][0]
        _mom.append(next(a["deger"] for a in _b2["adimlar"]
                         if (a.get("formul") or "") == "Fx"))
    r.kontrol("E2  ray kapıya yaklaşınca Fx büyüyor", abs(_mom[0]) > abs(_mom[1]),
              f"→ RK=500 Fx={_mom[0]:.1f} , RK=830 Fx={_mom[1]:.1f}")
    r.kontrol("E2  sapma kaydında yazılı",
              any("ağırlık merkezi kabin merkezinden" in ad
                  for ad, *_ in MK.EXCEL_FARKLARI))

    #  ── E3  Yük EN OLUMSUZ konumda  ( TS EN 81-20 m.5.7.2.3.4 )
    #  Kitap xQ'yu her zaman xc + Dx/8 alıyordu.  xc < 0 iken bu, boş kabinin
    #  momentini DENGELER ve gerilmeyi olduğundan küçük gösterir.
    def _b7(**ek):
        _s = MK.hesapla(dict({"kabin_derinligi": 1400, "kabin_agirligi": 650}, **ek))
        _b = [x for x in _s["bolumler"] if x["baslik"].startswith("7 ")][0]
        _xq = next(a["deger"] for a in _b["adimlar"]
                   if str(a.get("formul") or "").startswith("Durum 1"))
        _fx = next(a["deger"] for a in _b["adimlar"] if (a.get("formul") or "") == "Fx")
        _xc = {a.get("sembol"): a["deger"] for a in _b["adimlar"] if a.get("sembol")}["xc"]
        return _xc, _xq, _fx, _b

    #  Yardımcının kendisi:  momenti büyüten yönü seçmeli
    r.esit("E3  merkez pozitifken + yön seçiliyor",
           MK._yuk_merkezi(300.0, 175.0, 630.0, 650.0, 100.0), 475.0)
    r.esit("E3  merkez negatifken − yön seçiliyor",
           MK._yuk_merkezi(-300.0, 175.0, 630.0, 650.0, -100.0), -475.0)
    r.esit("E3  simetrikte ( merkez = 0, kol = 0 ) + yön",
           MK._yuk_merkezi(0.0, 175.0, 630.0, 650.0, 0.0), 175.0)
    #  ASIL BULGU:  xc < 0 iken artık − yön seçiliyor ve Fx BÜYÜYOR
    for _rk, _bek in ((500, +1), (1200, -1)):
        _xc, _xq, _fx, _ = _b7(ray_kapi_arasi=_rk)
        r.kontrol(f"E3  RK={_rk}: xQ, xc'den {'+' if _bek > 0 else '−'} yönde kaydı",
                  (_xq - _xc) * _bek > 0, f"→ xc={_xc}, xQ={_xq}")
    #  Yalnız + yönle karşılaştırma:  kitabın seçimi HER ZAMAN daha küçük
    for _rk in (500, 830, 1000, 1200):
        _xc, _xq, _fx, _ = _b7(ray_kapi_arasi=_rk)
        _gv = _MG.tamamla(_MG.varsayilanlar())
        _kitap_xq = _xc + 1400 / 8
        _kitap = abs(630 * _kitap_xq + 650 * (_xc - _gv["kapi_agirligi"]
                                              * (700 + _gv["kapi_mekanizma_payi"]) / 650))
        _bizim = abs(630 * _xq + 650 * (_xc - _gv["kapi_agirligi"]
                                        * (700 + _gv["kapi_mekanizma_payi"]) / 650))
        r.kontrol(f"E3  RK={_rk}: seçilen yön kitabınkinden küçük DEĞİL",
                  _bizim >= _kitap - 1e-9, f"→ bizim {_bizim:.0f}, kitap {_kitap:.0f}")
    r.kontrol("E3  sapma kaydında yazılı",
              any("yalnız + yönde" in ad for ad, *_ in MK.EXCEL_FARKLARI))

    #  ── E4  Kapı konumu xi RAY EKSENİNDEN  ( TS EN 81-50 Ek C.1.2 )
    #  C.2.3'ün payı  gn·P·(xp−xs) + Fs·(xi−xs)  bir moment toplamıdır;
    #  kitap xi'ye ray–kapı arasını HAM MESAFE ( hep artı ) yazıyordu.
    #  xc < 0 iken eşik kuvveti boş kabinin momentini DENGELİYORDU.
    def _yuk_fx(**ek):
        _s = MK.hesapla(dict({"kabin_derinligi": 1400, "kabin_agirligi": 650}, **ek))
        _b = [x for x in _s["bolumler"] if x["baslik"].startswith("7 ")][0]
        _d = {a.get("sembol"): a["deger"] for a in _b["adimlar"] if a.get("sembol")}
        _fx = next(a["deger"] for a in _b["adimlar"]
                   if str(a.get("formul") or "").startswith("Fx = ( gn"))
        return _d.get("xi"), _d.get("xp"), _fx

    for _rk in (500, 830, 1200):
        _xi, _xp, _fx = _yuk_fx(ray_kapi_arasi=_rk)
        r.esit(f"E4  RK={_rk}: xi ray ekseninden ( −RK )", _xi, -_rk)
    #  ASIL BULGU:  ray ekseni kabin merkezini geçince kuvvet BÜYÜMELİ
    _, _, _f830 = _yuk_fx(ray_kapi_arasi=830)
    _, _, _f1200 = _yuk_fx(ray_kapi_arasi=1200)
    r.kontrol("E4  ray ekseni kabin merkezini geçince yükleme Fx'i büyüyor",
              abs(_f1200) > abs(_f830) > 100,
              f"→ RK=830 {_f830:.1f} N , RK=1200 {_f1200:.1f} N")
    #  Kitabın ham mesafesiyle karşılaştırma:  xc < 0'da onunki KÜÇÜK kalıyordu
    _gv = _MG.tamamla(_MG.varsayilanlar())
    for _rk in (830, 1200):
        _xi, _xp, _fx = _yuk_fx(ray_kapi_arasi=_rk)
        _Fs = 0.4 * 9.81 * _gv["beyan_yuku"]
        _kitap = abs(9.81 * 650 * _xp + _Fs * (+_rk)) / (2 * _gv["kabin_paten_arasi"])
        r.kontrol(f"E4  RK={_rk}: doğrusu kitabınkinden BÜYÜK",
                  abs(_fx) > _kitap, f"→ bizim {abs(_fx):.1f} , kitap {_kitap:.1f}")
    r.kontrol("E4  sapma kaydında yazılı",
              any("Kapı konumu xi" in ad for ad, *_ in MK.EXCEL_FARKLARI))
    return r


def _girdi_yollari(r):
    """Girdi doğrulama ve hata yolları."""
    s = MK.hesapla({"beyan_yuku": 777})
    r.kontrol("geçersiz beyan yükü hesabı durduruyor", not s["aktif"])
    r.kontrol("hata metni alan adını içeriyor",
              any("Beyan yükü" in x for x in (s.get("hata") or [])),
              f"→ {s.get('hata')}")

    s = MK.hesapla({"durak_yukseklikleri": []})
    r.kontrol("boş durak listesi hesabı durduruyor", not s["aktif"])

    s = MK.hesapla({"acil_frenleme_a": 12})
    r.kontrol("a > 1 gn reddediliyor", not s["aktif"])

    #  Tablosunda atalet yarıçapı olmayan NPU seçimi  ( 240 · 280 · 300 )
    s = MK.hesapla({"dikine_kiris": 300})
    r.kontrol("verisi eksik NPU reddediliyor", not s["aktif"])
    r.kontrol("eksik NPU hatası neyin eksik olduğunu söylüyor",
              any("ix" in x for x in (s.get("hata") or [])), f"→ {s.get('hata')}")

    #  Bölen alanlarda sıfır
    for anahtar in ("halat_adedi", "kabin_ray_sayisi", "aski_orani"):
        s = MK.hesapla({anahtar: 0})
        r.kontrol(f"{anahtar} = 0 reddediliyor", not s["aktif"])

    #  Arka karşı ağırlıkta halat arası hesaplanır
    s = MK.hesapla({"agirlik_yeri": "Arka"})
    r.kontrol("arka ağırlıkta hesap koşuyor", s["aktif"], f"→ {s.get('hata')}")
    if s["aktif"]:
        r.esit("arka ağırlıkta halat arası", s["girdi"]["halat_arasi"], 825)

    #  a = 1 gn sınırında T1 sıfırlanır — motor çökmemeli, tahrik yeteneğini
    #  UYGUN DEĞİL saymalı.  ( Kaynak Excel bu noktada #SAYI/0! verir. )
    s = MK.hesapla({"acil_frenleme_a": 9.81})
    r.kontrol("a = 1 gn sınırında hesap çöküyor mu", s["aktif"], f"→ {s.get('hata')}")
    if s["aktif"]:
        r.kontrol("a = 1 gn'de tahrik yeteneği uygun değil",
                  s["bolumler"][5]["sonuc"]["uygun"] is False)

    #  Kaynak Excel 1. bükülgen kabloyu aramaz, sabitler.  Motorda aramanın
    #  gerçekten yapıldığını kanıtla:  1. kablo tipi değişince MTrav değişmeli.
    a1 = MK.hesapla({"kablo_tipi_1": "24 x 0,75"})
    a2 = MK.hesapla({"kablo_tipi_1": "12 x 0,75"})
    r.kontrol("1. bükülgen kablo tipi sonuca giriyor",
              a1["aktif"] and a2["aktif"]
              and not _yakin(a1["_h"]["AH264"], a2["_h"]["AH264"]),
              "→ MTrav 1. kabloya duyarsız; Excel'in sabitlenmiş hâline düşmüş")

    #  Farklı profil / hız ile de çökmeden koşmalı
    for ek in ({"kabin_ray_profili": "127 x 89 x 16"},
               {"dikine_kiris": 200, "yan_yatak": 200},
               {"beyan_hizi": 2.5}, {"aski_orani": 1},
               {"kanal_isleme": "Sertleştirilmiş"},
               {"guvenlik_tertibati": "Ani Frenlemeli"},
               {"agirlik_malzemesi": "Pik Döküm"},
               {"beyan_yuku": 2000, "kabin_genisligi": 2000,
                "kabin_derinligi": 2200, "kabin_agirligi": 1400}):
        s = MK.hesapla(ek)
        r.kontrol(f"varyant koşuyor: {ek}", s["aktif"], f"→ {s.get('hata')}")
        if s["aktif"]:
            r.kontrol(f"varyant 10 bölüm üretti: {list(ek)[0]}",
                      len(s["bolumler"]) == 10)

    #  ── Fiziksel sınır kalkanları ve yeni 4 girdi testleri
    #  1. Balata boyu fiziksel sınırları: 0, 10 mm ve paten aralığını aşanlar reddedilmeli
    r.kontrol("balata boyu = 0 reddediliyor", not MK.hesapla({"paten_balata_boyu": 0})["aktif"])
    r.kontrol("balata boyu < 20 mm reddediliyor", not MK.hesapla({"paten_balata_boyu": 10})["aktif"])
    r.kontrol("balata boyu > paten arası reddediliyor", not MK.hesapla({"paten_balata_boyu": 4000})["aktif"])
    r.kontrol("balata boyu 60 mm geçerli", MK.hesapla({"paten_balata_boyu": 60})["aktif"])

    #  2. Güv. devreye sokma kuvveti sıfır olamaz
    r.kontrol("güv. devreye sokma kuvveti = 0 reddediliyor",
              not MK.hesapla({"guvenlik_devreye_kuvvet": 0})["aktif"])

    #  3. Karşı ağırlıkta güvenlik tertibatı varsa dperm = 5 mm (TS EN 81-20 m.5.7.4.6)
    s_yok = MK.hesapla({"agirlik_guvenlik_tertibati": "Yok"})
    b8_yok = [x for x in s_yok["bolumler"] if x["baslik"].startswith("8 ")][0]
    r.kontrol("güv. tertibatsız karşı ağırlıkta dperm = 10 mm",
              any("δperm = 10" in a.get("aciklama", "") for a in b8_yok["adimlar"]))

    s_var = MK.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı"})
    b8_var = [x for x in s_var["bolumler"] if x["baslik"].startswith("8 ")][0]
    r.kontrol("güv. tertibatlı karşı ağırlıkta dperm = 5 mm (TS EN 81-20 m.5.7.4.6)",
              any("δperm = 5" in a.get("aciklama", "") for a in b8_var["adimlar"]))

    #  4. Yan ağırlıkta (Sağ) bina sehimi rayın yerel eksenlerine göre döner
    s_sag = MK.hesapla({"agirlik_yeri": "Sağ", "yapi_sehim_x": 3.0, "yapi_sehim_y": 1.0})
    b8_sag = [x for x in s_sag["bolumler"] if x["baslik"].startswith("8 ")][0]
    # Yan ağırlıkta ray x'i bina y'sini (1.0), ray y'si bina x'ini (3.0) almalı
    dx_sag = next(a["deger"] for a in b8_sag["adimlar"] if a.get("formul", "").startswith("δx ="))
    dy_sag = next(a["deger"] for a in b8_sag["adimlar"] if a.get("formul", "").startswith("δy ="))
    s_arka = MK.hesapla({"agirlik_yeri": "Arka", "yapi_sehim_x": 3.0, "yapi_sehim_y": 1.0})
    b8_arka = [x for x in s_arka["bolumler"] if x["baslik"].startswith("8 ")][0]
    dx_arka = next(a["deger"] for a in b8_arka["adimlar"] if a.get("formul", "").startswith("δx ="))
    dy_arka = next(a["deger"] for a in b8_arka["adimlar"] if a.get("formul", "").startswith("δy ="))
    r.kontrol("yan ağırlıkta bina sehimi eksen dönüşümü çalışıyor",
              abs((dx_arka - dx_sag) - (3.0 - 1.0)) < 1e-6)

    #  5. Makaralı patende balata adımı ve Bölüm 8 formül adı
    s_mak = MK.hesapla({"paten_tipi": "Makaralı", "agirlik_guvenlik_tertibati": "Kaymalı"})
    b8_mak = [x for x in s_mak["bolumler"] if x["baslik"].startswith("8 ")][0]
    r.kontrol("makaralı patende B8 flanş formülü 1,85 yazıyor",
              any("1,85" in a.get("formul", "") for a in b8_mak["adimlar"]))
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
