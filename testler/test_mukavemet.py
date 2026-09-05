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
    _kalan = [x["baslik"] for x in b if (x.get("sonuc") or {}).get("uygun") is False]
    r.esit("örnek proje iki bölümden kalıyor", len(_kalan), 2)
    r.kontrol("kalan bölümler motor gücü ve askı halatları",
              sorted(x[:1] for x in _kalan) == ["1", "4"], f"→ {_kalan}")
    r.esit("Dt/dh eşiği standarda göre 40", MK.SABIT["Dt_dh_asgari"], 40)
    _oran = 240 / 6.5
    r.kontrol("örnek proje 40 eşiğini sağlamıyor", _oran < 40, f"→ {_oran}")
    #  İkisi de giderilince bütün bölümler uygun olmalı
    _d = MK.hesapla({"tahrik_kasnak_capi": 280, "saptirma_kasnak_capi": 280,
                     "motor_gucu": 7.5})
    r.kontrol("kasnak 280 mm ve motor 7,5 kW olunca bütün bölümler uygun",
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
    r.kontrol("motor σ(My) için Wx kullanıyor",
              any(_yakin(a["deger"], MK._moment(
                  1.2 * 9.81 * 1100 * 48 / (2 * 3400), 3000) / p)
                  for a in b[7]["adimlar"] if isinstance(a["deger"], (int, float))))
    return _girdi_yollari(_sapmalar(r))


def _sapmalar(r):
    """Standart gereği Excel'den ayrıldığımız noktalar gerçekten uygulanıyor mu."""
    r.esit("sapma kaydı dolu", len(MK.EXCEL_FARKLARI), 8)
    for ad, madde, _ex, _biz, _h in MK.EXCEL_FARKLARI:
        #  Her sapmanın DAYANAĞI yazılı olmalı:  ya TS EN 81-20/50 maddesi,
        #  ya da açıkça ofis standardı  ( ⑨ — verim tablosu;  standart makine
        #  verimi için sayı vermez, ofisin kendi avan tablosu verir ).
        r.kontrol(f"sapma '{ad[:34]}' dayanağı yazılı",
                  bool(madde) and ("81-20" in madde or "81-50" in madde
                                   or "ofis standardı" in madde),
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
    _bek = MK.SABIT["k3"] * 0 + 2 * 9.81 * (800 * _xc + 700 * s["_h"]["AH295"]) / (2 * 3400)
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
    r.esit("⑦ Nps Nequiv'i belirliyor", [_n[1], _n[2], _n[3]], [6.0, 7.0, 8.0])
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

    #  ⑨  motor verimi makine tipine bağlı  ( ofis standardı, TEK KAYNAK )
    from engine.ortak import ofis as _OF
    from engine.uygulama import mukavemet_girdi as _MG
    import engine.avan.tablolar as _AT
    r.kontrol("⑨ verim tablosu avan ile UYGULAMA'da tek kaynak",
              _AT.MAKINE_TIPLERI is _OF.MAKINE_VERIMLERI,
              "→ tablo ikiye ayrılmış;  yeniden ayrışabilir")
    r.esit("⑨ ofis verim tablosu", dict(_OF.MAKINE_VERIMLERI),
           {"Dişlisiz": 0.85, "Dişli": 0.50})
    r.esit("⑨ palanga verim düşüşü  ( MMO/697 §2.4 )", _OF.PALANGA_VERIM_DUSUSU, 0.10)
    r.kontrol("⑨ makine tipi artık girdi ve Excel'de B130'a bağlı",
              ("makine_tipi", "B130") in [(a[0], a[1]) for a in _MG.ALANLAR],
              f"→ {[a[:2] for a in _MG.ALANLAR if a[0] == 'makine_tipi']}")
    _bek9 = {("Dişlisiz", 1): 0.85, ("Dişlisiz", 2): 0.75,
             ("Dişli", 1): 0.50, ("Dişli", 2): 0.40}
    for (_t, _r2), _e in sorted(_bek9.items()):
        _v = MK.hesapla({"makine_tipi": _t, "aski_orani": _r2})["_h"]["AQ22"]
        r.kontrol(f"⑨ η′  {_t} {_r2}:1  = {_e}", _yakin(_v, _e), f"→ {_v!r}")
    _s9 = MK.hesapla({"makine_tipi": "Dişli", "aski_orani": 1})
    _bekN = _s9["_h"]["AQ9"] * _s9["girdi"]["beyan_hizi"] / (0.50 * 102)
    r.kontrol("⑨ N = Gmax·v/(η′·102)", _yakin(_s9["_h"]["AQ23"], _bekN),
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
    r.esit("⑧ sığınma hacimleri  ( Çiz.3 / Çiz.4 tip 2 )",
           [sorted(_S["ust_hacim"]), sorted(_S["dip_hacim"])],
           [[0.5, 0.7, 1.0], [0.5, 0.7, 1.0]])
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
           _S["ust_hacim"][2] * 1000)
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
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
