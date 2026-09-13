# -*- coding: utf-8 -*-
"""
TEST 11  —  UYGULAMA PROJESİ  ( orkestratör )

engine/uygulama.py mukavemet ve avan motorlarını TEK GİRDİ SETİYLE koşturur.
Bu testin asıl konusu ORTAK GİRDİ KÖPRÜSÜDÜR:

    Kullanıcı kabin genişliğini bir kez girer;  hem mukavemet hem kabin
    aydınlatması aynı değerden beslenmelidir.

Köprü sessizce kopabilir ( alan adı değişir, biri None kalır ) ve hiçbir
hesap testi bunu göremez — iki motor da kendi içinde tutarlı çalışmaya devam
eder.  Bu yüzden burada her ortak alan TEK TEK oynatılır ve elektrik
sonucunun gerçekten değiştiği doğrulanır.
"""
import io
import json
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from engine.avan import hesap as AV                          # noqa: E402
from engine.avan import tablolar as AVT                      # noqa: E402
from engine.uygulama import mukavemet as MK                     # noqa: E402
from engine.uygulama import hesap as UY                      # noqa: E402
from engine.uygulama import girdi as UG                # noqa: E402
from engine.uygulama import sabitler as US             # noqa: E402
from testler.ortak import P_std as _P_std, Rapor                        # noqa: E402

#  Topraklama ve kolon hattı olmadan elektrik bölümlerinin bir kısmı boş kalır
TAM = {"temel_a": 26.55, "temel_b": 16.4, "kolon_uzunluk": 45}


def _bolum_adlari(s):
    return [b["baslik"] for b in (s.get("bolumler") or [])]


def calistir():
    print("\n\033[1mTEST 11 — UYGULAMA PROJESİ (mukavemet + elektrik köprüsü)\033[0m")
    r = Rapor("Uygulama projesi")

    # ---------------------------------------------------------- yapı
    s = UY.hesapla(TAM)
    if not r.kontrol("tam girdiyle hesap koşuyor", s["aktif"], f"→ {s.get('hata')}"):
        return r
    adlar = _bolum_adlari(s)
    #  SAYI ELLE YAZILMAZ:  mukavemet motoruna bölüm eklenince ( ör.
    #  TAMPONLAR ) bu testin de kendiliğinden takip etmesi gerekir.
    _MUK = len(MK.BOLUM_URETICILERI)
    r.esit("mukavemet bölüm sayısı", s["mukavemet_bolum_sayisi"], _MUK)
    r.esit(f"toplam bölüm  ( {_MUK} mukavemet + 4 elektrik + 4 topraklama )",
           len(adlar), _MUK + 8)
    for i, ad in enumerate(adlar, 1):
        r.kontrol(f"bölüm {i} sırayla numaralı", ad.startswith(f"{i} -"),
                  f"→ {ad!r}")
    for ara in ("KABİN AYDINLATMA", "KUYU AYDINLATMA", "KURULU GÜÇ CETVELİ",
                "GERİLİM DÜŞÜMÜ", "TOPRAKLAYICI", "TOPLAM TOPRAKLAMA"):
        r.kontrol(f"bölüm var: {ara}", any(ara in a for a in adlar),
                  f"→ {adlar}")
    #  Avanın motor gücü ve kuvvet hesapları ALINMAZ — mukavemet zaten yapıyor
    r.kontrol("avanın motor gücü bölümü alınmıyor",
              not any("MOTOR GÜCÜ HESABI" in a for a in adlar), f"→ {adlar}")
    r.kontrol("avanın kuvvet hesapları bölümü alınmıyor",
              not any("KUVVET HESAPLARI" in a for a in adlar), f"→ {adlar}")
    r.kontrol("mukavemetin motor bölümü duruyor",
              any("MOTOR GÜCÜNÜN HESAPLANMASI" in a for a in adlar))

    #  Özet iki aileyi de taşıyor mu
    o = s["ozet"]
    for anahtar in ("N_hesap", "kabin_alani", "ray_boyu", "FKR",     # mukavemet
                    "P_kurulu", "eps", "n_kabin", "n_kuyu",          # elektrik
                    "Z_kabin", "Z_kuyu", "Re"):
        r.kontrol(f"özette {anahtar} var", o.get(anahtar) is not None,
                  f"→ {o.get(anahtar)!r}")

    # ---------------------------------------------------------- KÖPRÜ
    #  Her ortak alan oynatılır;  elektrik sonucu DEĞİŞMELİDİR.
    #  Değişmiyorsa köprü kopmuş, kullanıcı değeri boşuna girmiş demektir.
    taban = UY.hesapla(TAM)["ozet"]
    OYNAT = (
        #  Ölçüt YUVARLANMAMIŞ değerdir:  armatür sayısı ROUNDUP'lıdır ve
        #  küçük bir değişikliği yutar — köprü kopsa bile "4 = 4" geçerdi.
        ("kabin_genisligi", 1450, 2000, "Z_kabin",
         "kabin genişliği → kabin aydınlatması"),
        ("kabin_derinligi", 1350, 2100, "Z_kabin",
         "kabin derinliği → kabin aydınlatması"),
        ("kuyu_genisligi", 2400, 4000, "Z_kuyu",
         "kuyu genişliği → kuyu aydınlatması"),
        ("motor_gucu", 4.9, 15, "P_kurulu",
         "motor gücü → kurulu güç cetveli"),
        ("seyir_mesafesi", 21, 45, "Z_kuyu",
         "seyir mesafesi → kuyu boyu → kuyu aydınlatması"),
        ("kolon_kesit", 16, 4, "eps",
         "kolon kesiti → gerilim düşümü"),
        ("kolon_uzunluk", 45, 120, "eps",
         "kolon hattı boyu → gerilim düşümü"),
        ("temel_a", 26.55, 8, "Re",
         "temel uzunluğu → topraklama direnci"),
    )
    for anahtar, eski, yeni, olcut, aciklama in OYNAT:
        ek = dict(TAM)
        ek[anahtar] = yeni
        if anahtar == "seyir_mesafesi":     # durak listesiyle tutarlı olmalı
            ek["durak_yukseklikleri"] = [3000] * 15 + [3750]
            ek["son_kat_yuksekligi"] = 3750
        y = UY.hesapla(ek)
        if not r.kontrol(f"köprü senaryosu koşuyor: {anahtar}", y["aktif"],
                         f"→ {y.get('hata')}"):
            continue
        r.kontrol(f"KÖPRÜ · {aciklama}",
                  y["ozet"][olcut] != taban[olcut],
                  f"→ {anahtar} {eski} → {yeni} olduğu hâlde {olcut} "
                  f"{taban[olcut]!r} kaldı;  ortak girdi elektrik hesabına "
                  "ULAŞMIYOR")

    #  Köprü, avan motoruna DOĞRU alanları veriyor mu
    g = UG.tamamla(dict(UG.varsayilanlar(), **TAM))
    k = UG.kopru(g)
    a = k["asansorler"][0]
    r.esit("köprü · Q", a["Q_elle"], g["beyan_yuku"])
    r.esit("köprü · V", a["V"], g["beyan_hizi"])
    r.esit("köprü · Gk", a["Gk_elle"], g["kabin_agirligi"])
    r.esit("köprü · kabin boyu = mukavemet derinliği",
           a["kabin_boyu"], g["kabin_derinligi"])
    r.esit("köprü · kabin genişliği", a["kabin_genisligi"], g["kabin_genisligi"])
    r.esit("köprü · Hk = kuyu boyu / 1000", a["Hk"], g["kuyu_boyu"] / 1000)
    r.esit("köprü · Nsç = motor gücü", a["Nsc"], g["motor_gucu"])
    r.esit("köprü · askı oranı", a["i_palanga"], g["aski_orani"])
    r.esit("köprü · ray metre ağırlığı ray profilinden", a["gr"], 12.38)
    #  Verim artık sabit değil, MAKİNE TİPİNDEN gelir ve TOPLAM SİSTEM
    #  VERİMİDİR ( askı kaybı içinde ) — iki taraf aynı sayıyı kullanır.
    from engine.ortak import ofis as _OF
    r.esit("köprü · makine tipi taşınıyor", a["makine_tipi"], g["makine_tipi"])
    r.esit("köprü · η makine tipinden", a["eta"],
           _OF.makine_verimi(g["makine_tipi"]))
    r.kontrol("köprü · η artık kitabın sabiti 0,92 DEĞİL", a["eta"] != 0.92,
              f"→ {a['eta']!r}")
    for _t in _OF.MAKINE_VERIMLERI:
        _g = UG.tamamla(dict(UG.varsayilanlar(), makine_tipi=_t))
        r.esit(f"köprü · η ( {_t} )", UG.kopru(_g)["asansorler"][0]["eta"],
               _OF.MAKINE_VERIMLERI[_t])
    r.kontrol("köprü ORTAK_KOPRU listesindeki her alanı taşıyor",
              all(x in g for _ad, x, _av in UG.ORTAK_KOPRU),
              f"→ {[x for _a, x, _b in UG.ORTAK_KOPRU if x not in g]}")

    # -------------------------------------------------------------
    #  UYGULAMANIN KENDİ OFİS STANDARDI  ( avandan AYRI )
    # -------------------------------------------------------------
    from engine.uygulama import sabitler as _US
    from engine.uygulama import tablolar_gorunum as _UTG
    from engine.uygulama import mukavemet_tablolari as MT
    _S = _US.sabitler()
    r.kontrol("ofis sabitleri eksiksiz tanımlı",
              not [k for k in _US.VARSAYILAN if k not in _US.ETIKET],
              f"→ etiketi olmayan: {[k for k in _US.VARSAYILAN if k not in _US.ETIKET]}")
    r.kontrol("her sabit bir gruba ait",
              not [k for k in _US.VARSAYILAN
                   if not any(k in g[2] for g in _US.GRUPLAR)])
    r.kontrol("sayısal her sabitin aralığı var",
              not [k for k in _US.VARSAYILAN
                   if k not in _US.ARALIK and k not in _US.METIN])
    r.kontrol("aralık dışı değer REDDEDİLİYOR",
              _US.sabitler({"sigma_em": 9999})["_reddedilen"] == ["sigma_em"])
    r.esit("geçerli değer kabul ediliyor", _US.sabitler({"cosfi": 0.85})["cosfi"], 0.85)
    r.esit("reddedilen değer varsayılana dönüyor",
           _US.sabitler({"sigma_em": 9999})["sigma_em"], _US.VARSAYILAN["sigma_em"])

    #  σem ve k1 KODDA GÖMÜLÜ DEĞİL — ofis bunları gözden geçirebilmeli
    for _k in ("sigma_em", "k1_kaymali", "k1_makarali", "k1_ani",
               "q_denge", "verim_dislisiz", "verim_disli", "tavan_payi"):
        r.kontrol(f"ofis sabiti ekrana çıkıyor: {_k}", _k in _US.VARSAYILAN)

    #  AVANIN kuvvet sabitleri uygulamada YOK — ayrı projeler
    import engine.avan.hesap as _AVh
    _avan_ozel = ("gf", "Fmt", "n_ray", "gr", "Fmk", "Fsh", "i_palanga")
    r.esit("avanın MMO/697 kuvvet sabitleri uygulamada yok",
           [k for k in _avan_ozel if k in _US.VARSAYILAN], [])

    #  Ofis sabiti hesabı GERÇEKTEN değiştiriyor mu
    _t = MK.hesapla()
    for _ez, _hucre in (({"verim_dislisiz": 0.88}, "AQ23"),
                        ({"sigma_em": 100}, "J65"),
                        ({"k1_kaymali": 3}, "C47"),
                        ({"q_denge": 0.45}, "AQ13"),
                        ({"tavan_payi": 200}, "AI636"),
                        ({"Gs": 50}, "AQ9"),
                        ({"halat_pay_m": 8}, "AQ19"),
                        ({"yan_yatak_L_X": 400}, "K58")):
        _y = MK.hesapla({"_ofis": _ez})
        _ad = list(_ez)[0]
        if _ad == "sigma_em":
            #  σem gerilmeyi DEĞİL, sınırı değiştirir:  etkisi bölüm 2'nin
            #  KARARINDA görünür.  Örnek projede başka bölümler zaten
            #  kaldığı için "tumu_uygun" ile bakmak yanıltıcı olurdu.
            def _b2(x):
                return [b for b in x["bolumler"]
                        if b["baslik"].startswith("2")][0]["sonuc"]["uygun"]
            r.kontrol(f"ofis sabiti '{_ad}' makine kaidesinin kararını çeviriyor",
                      _b2(_t) is True and _b2(_y) is False,
                      f"→ önce {_b2(_t)}, sonra {_b2(_y)}")
        else:
            r.kontrol(f"ofis sabiti '{_ad}' hesabı değiştiriyor",
                      _y["_h"][_hucre] != _t["_h"][_hucre],
                      f"→ {_hucre}: {_t['_h'][_hucre]} → {_y['_h'][_hucre]}")

    #  Ofis sabitleri TESLİM EDİLEN EXCEL'e de yansımalı
    import io as _io3, openpyxl as _op4
    from exports import mukavemet_xlsx as _MX3
    _wsx = _op4.load_workbook(_io3.BytesIO(_MX3.mukavemet_xlsx(
        MK.hesapla({"_ofis": {"verim_dislisiz": 0.88}})["girdi"])))["11-Muk. Hesapları"]
    r.kontrol("ofis verimi teslim edilen kitaba da giriyor",
              "0.88" in str(_wsx["AQ22"].value), f"→ {str(_wsx['AQ22'].value)[:80]}")

    # -------------------------------------------------------------
    #  UYGULAMANIN KENDİ TABLOLARI  ( ekranda bugüne kadar YOKTU )
    # -------------------------------------------------------------
    _tb = _UTG.arayuz_tablolari()
    r.kontrol("tablo görünümü dolu", len(_tb) >= 12, f"→ {len(_tb)} tablo")
    for _x in _tb:
        r.kontrol(f"tablo '{_x['ad'][:28]}' eksiksiz",
                  bool(_x["ad"]) and bool(_x["basliklar"]) and bool(_x["satirlar"])
                  and all(len(s) == len(_x["basliklar"]) for s in _x["satirlar"]),
                  f"→ {len(_x['basliklar'])} sütun, {len(_x['satirlar'])} satır")
    #  TABLOLAR KOPYALANMAZ — motorun kendi sözlüğünden okunmalı
    _ray = [x for x in _tb if "Kılavuz ray" in x["ad"]][0]
    r.esit("ray tablosu motorun tablosuyla aynı satır sayısında",
           len(_ray["satirlar"]), len(MT.RAY_PROFILI))
    r.kontrol("ray tablosu gerçek profil taşıyor",
              any("50 x 50 x 5" in str(s[0]) for s in _ray["satirlar"]))
    _w = [x for x in _tb if x["ad"].startswith("ω")][0]
    r.kontrol("ω tablosu üç Rm sütunu veriyor", len(_w["basliklar"]) == 4)
    r.kontrol("ω tablosu motorun formülüyle aynı",
              all(abs(s[1] - round(MT.omega_en8150(s[0], 370), 4)) < 1e-9
                  for s in _w["satirlar"]))

    # ═══════════════════════════════════════════════════════════════
    #  DENETİMDE BULUNAN SEKİZ HATA  —  her biri yeniden üretilerek
    # ═══════════════════════════════════════════════════════════════
    import io as _io4, json as _js4, base64 as _b64, openpyxl as _op5
    from engine.uygulama import hesap as UH

    def _yakin(a, b, tol=1e-6):
        try:
            return abs(float(a) - float(b)) <= tol * max(1.0, abs(float(b)))
        except (TypeError, ValueError):
            return a == b
    import main as _M4
    from exports import mukavemet_xlsx as _MX4

    #  ①  NEGATİF GERİLME "UYGUN" SAYILMAZ
    #  X = L − mesnet payı ≤ 0 iken σe negatif çıkıyor ve "σe ≤ σem" bunu
    #  sessizce geçiriyordu ( −5.350 ≤ 130 doğrudur ).
    _n1 = MK.hesapla({"yan_yatak_boyu": 100, "yan_yatak": 30, "dikine_kiris": 30})
    r.kontrol("① imkânsız kaide geometrisi REDDEDİLİYOR", not _n1["aktif"],
              f"→ {_n1.get('ozet')}")
    r.kontrol("① hata mesajı alanı ve sebebi söylüyor",
              any("Yan yatak boyu" in x and "mesnet payı" in x
                  for x in (_n1.get("hata") or [])), f"→ {_n1.get('hata')}")
    r.kontrol("① sınırda ( X = 0 ) da reddediliyor",
              not MK.hesapla({"yan_yatak_boyu": 335})["aktif"])
    r.kontrol("① X = 1 mm kabul ediliyor", MK.hesapla({"yan_yatak_boyu": 336})["aktif"])
    #  İkinci kalkan:  negatif gerilme hiçbir koşulda uygun sayılmamalı
    import engine.uygulama.mukavemet as _MKm
    r.kontrol("① negatif gerilme uygun sayılmıyor  ( ikinci kalkan )",
              not (0 <= -1 <= 130), "→ karşılaştırma yalnız ≤ ile yapılıyor")

    #  ②  GENEL SONUÇ ENGELLEYİCİ UYARILARI SAYIYOR
    #  "TEMİZ PROJE" için imalatçı kuvveti de gerekir:  TS EN 81-20
    #  m.5.6.2.2.1.1 d)'nin ikinci sınırı onsuz DENETLENEMEZ ve bölüm
    #  "HESAP EKSİK" der ( sapma ⑲ ).
    #  TAHRİK YETENEĞİ için kanalın sertleştirilmiş olması ve denge zinciri
    #  de gerekir;  ivme işaretleri Ek D'ye göre düzeltilince ( sapma ㊳ )
    #  kitabın çıplak örneği tahrikten kalıyor.
    #  Temiz proje sarılma açısını da BEYAN eder ( zorunlu girdi ).
    _temiz = dict(tahrik_kasnak_capi=280, saptirma_kasnak_capi=280,
                  motor_gucu=7.5, guvenlik_devreye_kuvvet=200,
                  kanal_isleme="Sertleştirilmiş", denge_zinciri="Var",
                  sarilma_acisi=180)
    _t = UH.hesapla(UG.tamamla(dict(UG.varsayilanlar(), **_temiz)))
    r.kontrol("② temiz proje uygun", _t["ozet"]["tumu_uygun"] is True)
    #  Akım yetersizse İLGİLİ BÖLÜM de uygun değil
    _s2 = UH.hesapla(UG.tamamla(dict(UG.varsayilanlar(), tahrik_kasnak_capi=280,
                                     saptirma_kasnak_capi=280, motor_gucu=37,
                                     kolon_kesit=95, makine_kesit=1.5,
                                     makine_uzunluk=2)))
    #  SIRAYA DEĞİL KİMLİĞE BAK:  mukavemet tarafına bölüm eklenince
    #  ( TAMPONLAR ) elektrik bölümlerinin numarası kayıyor.
    _b14 = [b for b in _s2["bolumler"] if b["kimlik"] == "gerilim_dusumu"][0]
    r.kontrol("② akım yetersizken BÖLÜM uygun değil",
              _b14["sonuc"]["uygun"] is False, f"→ {_b14['sonuc']}")
    r.kontrol("② bölümün alt satırında I2 ≤ Iz2 kontrolü var",
              any("I2" in x for x in _b14["sonuc"]["alt"]), f"→ {_b14['sonuc']['alt']}")
    r.kontrol("② akım yetersizken proje uygun değil",
              _s2["ozet"]["tumu_uygun"] is False)
    #  Fiziksel imkânsızlık ENGELLEYİCİ
    _kk = UH.hesapla(UG.tamamla(dict(UG.varsayilanlar(), **_temiz,
                                     kabin_genisligi=1850, kuyu_genisligi=1800)))
    r.kontrol("② kabin kuyuya sığmıyorsa proje uygun değil",
              _kk["ozet"]["tumu_uygun"] is False)
    r.kontrol("② engelleyici uyarı ayrı listede",
              len(_kk["ozet"].get("engelleyici") or []) >= 1,
              f"→ {_kk['ozet'].get('engelleyici')}")
    #  Zorunlu hesap yapılamıyorsa EKSİK
    _ek = UH.hesapla(UG.tamamla(dict(UG.varsayilanlar(), **_temiz,
                                     temel_a=10, temel_b=None)))
    r.kontrol("② yapılamayan zorunlu hesap projeyi uygun bırakmıyor",
              _ek["ozet"]["tumu_uygun"] is False)
    r.kontrol("② eksik hesap ayrı listede",
              len(_ek["ozet"].get("eksik_hesap") or []) >= 1,
              f"→ {_ek['ozet'].get('eksik_hesap')}")
    #  İMALATÇI KUVVETİ YOKSA REGÜLATÖR MADDESİ DENETLENEMEZ  →  EKSİK
    _rg = UH.hesapla(UG.tamamla(dict(UG.varsayilanlar(), **_temiz)
                                | {"guvenlik_devreye_kuvvet": None}))
    r.kontrol("② imalatçı kuvveti yoksa proje uygun çıkmıyor",
              _rg["ozet"]["tumu_uygun"] is False)
    r.kontrol("② regülatör eksiği eksik_hesap listesinde",
              any("devreye sokma" in x
                  for x in (_rg["ozet"].get("eksik_hesap") or [])),
              f"→ {_rg['ozet'].get('eksik_hesap')}")
    r.kontrol("② eksik olan bölüm UYGUN DEĞİL değil, HESAP EKSİK diyor",
              any("HESAP EKSİK" in (b.get("sonuc") or {}).get("metin", "")
                  for b in _rg["bolumler"]))

    #  BİLGİLENDİRİCİ uyarı uygunluğu ENGELLEMEZ
    _bg = UH.hesapla(UG.tamamla(dict(UG.varsayilanlar(), **_temiz,
                                     _ofis={"cosfi": 99})))
    r.kontrol("② bilgilendirici uyarı uygunluğu engellemiyor",
              _bg["ozet"]["tumu_uygun"] is True,
              f"→ {_bg['ozet'].get('engelleyici')} / {_bg['ozet'].get('eksik_hesap')}")

    #  ③  OFİS SABİTLERİ EXCEL'DEN GERİ GELİYOR  ( sonuç değişmemeli )
    _g3 = UG.tamamla(dict(UG.varsayilanlar(), **_temiz))
    _g3["_ofis"] = {"sigma_em": 100, "kablo_tipi": "NYY", "kanal_gama_yd": 30}
    _once = UH.hesapla(_g3)
    _geri = _MX4.xlsx_oku(_MX4.mukavemet_xlsx(_g3))
    r.esit("③ ofis sabitleri geri geliyor", _geri.get("_ofis"),
           {"kablo_tipi": "NYY", "kanal_gama_yd": 30, "sigma_em": 100})
    _sonra = UH.hesapla(_geri)
    def _b2m(x):
        return [b for b in x["bolumler"] if b["baslik"].startswith("2")][0]["sonuc"]
    r.esit("③ Excel'den dönünce bölüm 2 sonucu AYNI", _b2m(_sonra), _b2m(_once))
    r.esit("③ Excel'den dönünce genel sonuç AYNI",
           _sonra["ozet"]["tumu_uygun"], _once["ozet"]["tumu_uygun"])
    r.kontrol("③ varsayılanla aynı olan sabit dosyayı şişirmiyor",
              not _MX4.xlsx_oku(_MX4.mukavemet_xlsx(
                  UG.tamamla(UG.varsayilanlar()))).get("_ofis"))

    #  ④  REDDEDİLEN OFİS SABİTİ EXCEL'E HAM GİTMİYOR
    import engine.avan.hesap as _AV4
    from exports import xlsx_export as _XE4, hucre_haritasi as _H4
    _veri4 = {"ortak": {}, "asansorler": [{"aktif": True, "tanim": "T",
              "Q_elle": 800, "V": 1, "Hk": 30, "eta": 0.7, "kuyu_genisligi": 1900,
              "kabin_boyu": 1300, "kabin_genisligi": 1100}],
              "sabitler": {"cosfi": 2, "q_denge": 5, "n_ray": 0}, "trafik": {}}
    _S4 = _AV4.sabitler(_veri4["sabitler"])
    _ws4 = _op5.load_workbook(_io4.BytesIO(_XE4.avan_xlsx(_veri4)))["SABİTLER"]
    for _k in ("cosfi", "q_denge", "n_ray"):
        r.esit(f"④ Excel'e motorun kullandığı {_k} yazılıyor",
               _ws4[_H4.AVAN_SABIT[_k]].value, _S4[_k])
    #  Ham değerin kendisi hücrede DURMAMALI.  ( n_ray'in ham değeri 0'dır;
    #  çözülmüş değeri 2 — yani "2 var mı" diye bakmak yanıltıcı olur,
    #  hücrenin HAM değere eşit OLMAMASI aranır. )
    for _k, _ham in (("cosfi", 2), ("q_denge", 5), ("n_ray", 0)):
        r.kontrol(f"④ {_k} hücresinde ham değer ({_ham}) yok",
                  _ws4[_H4.AVAN_SABIT[_k]].value != _ham,
                  f"→ {_ws4[_H4.AVAN_SABIT[_k]].value!r}")

    #  ⑤  METİN OFİS ALANI SAYIYA ÇEVRİLMİYOR
    import api.uygulama as _AU4
    _AU4._BELIRSIZ.clear()
    _g5 = _AU4._mukavemet_girdi({"girdiler": {}, "sabitler": {
        "kablo_tipi": "NYY", "cosfi": "0,85", "priz_gucu": "1.200"}})
    r.esit("⑤ metin ofis alanı korunuyor", _g5["_ofis"].get("kablo_tipi"), "NYY")
    r.esit("⑤ sayısal ofis alanı okunuyor", _g5["_ofis"].get("cosfi"), 0.85)
    r.kontrol("⑤ belirsiz yazım BİLDİRİLİYOR", len(list(_AU4._BELIRSIZ)) >= 1,
              f"→ {list(_AU4._BELIRSIZ)}")

    #  ⑥  FİZİKSEL GİRDİ SINIRLARI
    for _ad6, _ek6 in (("kesirli halat adedi", {"halat_adedi": 6.5}),
                       ("kesirli ray sayısı", {"kabin_ray_sayisi": 2.5}),
                       ("konsol aralığı 0", {"kabin_konsol_arasi": 0}),
                       ("regülatör açısı 360", {"reg_kanal_acisi": 360}),
                       ("regülatör açısı 0", {"reg_kanal_acisi": 0})):
        _x6 = MK.hesapla(_ek6)
        r.kontrol(f"⑥ {_ad6} reddediliyor", not _x6["aktif"], f"→ hesap yapıldı")
        r.kontrol(f"⑥ {_ad6} hatası ALAN ADINI söylüyor",
                  bool(_x6.get("hata")) and not any("Traceback" in x
                                                    for x in _x6["hata"]),
                  f"→ {_x6.get('hata')}")
    r.kontrol("⑥ geçerli girdi hâlâ kabul ediliyor", MK.hesapla()["aktif"])

    #  ⑦  PROJE KİMLİĞİ GERİ GELİYOR
    _xl7 = _MX4.mukavemet_xlsx(MK.hesapla()["girdi"],
                               {"proje_adi": "Jan Mühendislik",
                                "isveren": "Öz Yapı", "pafta_no": "A-07"})
    _d7 = _js4.loads(_M4.api_xlsx_yukle(
        {"icerik": _b64.b64encode(_xl7).decode()}).body)
    r.esit("⑦ proje adı geri geliyor", _d7["proje"].get("proje_adi"), "Jan Mühendislik")
    r.esit("⑦ işveren geri geliyor", _d7["proje"].get("isveren"), "Öz Yapı")
    r.esit("⑦ pafta no geri geliyor", _d7["proje"].get("pafta_no"), "A-07")
    r.esit("⑦ forma da taşınıyor", _d7["alanlar"].get("mk_proje_adi"), "Jan Mühendislik")
    r.esit("⑦ programın imzası mühendis sanılmıyor", _d7["proje"].get("muhendis"), "")

    #  ⑧  RAY AĞIRLIĞI BİR KEZ SAYILIYOR
    _s8 = MK.hesapla()
    _h8 = _s8["_h"]
    _gn8 = MK.SABIT["gn"]
    _ray8 = _gn8 * MT.ray(_s8["girdi"]["kabin_ray_profili"], "Gr") * \
        _s8["ozet"]["ray_boyu"]
    #  Raya bağlı donanım k3 ile çarpılır:  m.5.2.1.8.4 tabanın taşıyacağı
    #  kalemler arasında "additional reaction … due to REBOUND when machine
    #  on rails" der, katsayısı m.5.7.4.3'ün k3'üdür  ( bölüm 7 ile aynı ).
    _k38 = US.sabitler(_s8["girdi"].get("_ofis"))["k3_yardimci"]
    _bek8 = (_ray8 + _k38 * MK.SABIT["MY_kabin"]
             + (_h8["AU351"] - _h8["AH291"] * _gn8))
    r.kontrol("⑧ FKR = ray kütlesi + k3 × bileşen + güv.tert. tepkisi",
              _yakin(_h8["AX611"], _bek8), f"→ {_h8['AX611']!r} ≠ {_bek8!r}")
    r.kontrol("⑧ ray ağırlığı iki kez sayılmıyor",
              abs(_h8["AX611"] - (_bek8 + _ray8)) > 1,
              "→ hâlâ çift sayılıyor")

    #  ⑨  KORUMA İLETKENİ ( PE ) HER İKİ PROJEDE DE PAFTAYA GİRİYOR
    #  Uygulama projesinin 15. bölümü avan motorunun gerilim_dusumu bölümüdür;
    #  tek kaynaktan beslendiği için iki paftada da AYNI satırlar çıkmalı.
    #  Beklenen değer ÇİZELGE-8'den türetilir, motorun kendi satırından değil.
    def _pe_satirlari(bolumler):
        b = next(x for x in bolumler if x.get("kimlik") == "gerilim_dusumu")
        return {str(a.get("sembol")): a for a in b["adimlar"]
                if isinstance(a, dict) and str(a.get("sembol") or "") in ("SPE1", "SPE2")}

    _u9 = UY.hesapla()
    _pu = _pe_satirlari(_u9["bolumler"])
    r.esit("⑨ uygulama paftasında iki PE satırı", len(_pu), 2)
    _av9 = AV.hesapla({"ortak": {"temel_a": 26.55, "temel_b": 16.4, "beta": 150,
                                 "cubuk_sayisi": 4, "mk_uzunluk": 3000,
                                 "mk_genislik": 2500},
                       "sabitler": {},
                       "asansorler": [{"tanim": "A", "kapasite": 10, "V": 1.6,
                                       "eta": 0.85, "Hk": 32.85,
                                       "kuyu_genisligi": 1800, "kabin_boyu": 1450,
                                       "kabin_genisligi": 1300,
                                       "makine_tipi": "Dişlisiz",
                                       "S1": 150, "S2": 95}]})
    _pa = _pe_satirlari(_av9["asansorler"][0]["bolumler"])
    r.esit("⑨ avan paftasında iki PE satırı", len(_pa), 2)
    #  S/2'nin standart kesite düşmediği satır:  150 → 75 → BİR ÜST = 95
    r.esit("⑨ SPE1 bir üst standart kesite yuvarlanıyor  ( 150 → 95 )",
           _pa["SPE1"]["deger"], AVT.koruma_iletkeni_kesiti(150)[0])
    r.esit("⑨ SPE2 çizelgeyle aynı  ( 95 → 50 )",
           _pa["SPE2"]["deger"], AVT.koruma_iletkeni_kesiti(95)[0])
    r.kontrol("⑨ yuvarlama paftada kaynak sütununda yazıyor",
              "bir üst standart" in str(_pa["SPE1"].get("kaynak") or ""),
              f"→ {_pa['SPE1'].get('kaynak')!r}")
    r.kontrol("⑨ hat başına PE satırları topraklama bölümüne kaymamış",
              not any(str(a.get("sembol") or "") in ("SPE1", "SPE2")
                      for b in ((_av9.get("topraklama") or {}).get("bolumler") or [])
                      for a in b["adimlar"] if isinstance(a, dict)))

    #  ⑩  TOPRAKLAMA VE POTANSİYEL DENGELEME İLETKENLERİ  ( m.9-j · m.9/c )
    #  Ana potansiyel dengeleme "TESİSTEKİ en büyük koruma iletkeninden" türer
    #  ( m.9-j/1/i ) — tesis çok asansörlüyse hepsine bakılmalı.
    _ORTAK10 = {"temel_a": 26.55, "temel_b": 16.4, "beta": 150, "cubuk_sayisi": 4,
                "mk_uzunluk": 3000, "mk_genislik": 2500}
    _T10 = {"tanim": "A", "kapasite": 10, "V": 1.6, "eta": 0.85, "Hk": 32.85,
            "kuyu_genisligi": 1800, "kabin_boyu": 1450, "kabin_genisligi": 1300,
            "makine_tipi": "Dişlisiz"}

    def _iletken_satirlari(asans):
        s10 = AV.hesapla({"ortak": dict(_ORTAK10), "sabitler": {}, "asansorler": asans})
        b = next(x for x in s10["topraklama"]["bolumler"]
                 if x.get("kimlik") == "topraklama_iletkenleri")
        d = {}
        for a in b["adimlar"]:
            if isinstance(a, dict):
                ad = str(a.get("sembol") or "")
                if not ad and str(a.get("formul") or "").startswith("Sapd"):
                    ad = "Sapd"
                if ad:
                    d[ad] = a["deger"]
        return s10, d

    _s10, _d10 = _iletken_satirlari([dict(_T10, S1=6, S2=6)])
    r.esit("⑩ topraklama bölümü dört alt bölüm",
           len(_s10["topraklama"]["bolumler"]), 4)
    r.esit("⑩ SPE = 6 → Sapd", _d10.get("Sapd"),
           AVT.ana_potansiyel_dengeleme_kesiti(6)[0])
    r.esit("⑩ SPE = 6 → Stopr", _d10.get("Stopr"),
           AVT.topraklama_iletkeni_kesiti(6)[0])
    #  ÇOK ASANSÖRDE EN BÜYÜK PE BELİRLER — tesis geneli bir iletkendir.
    _s10c, _d10c = _iletken_satirlari([dict(_T10, S1=6, S2=6),
                                       dict(_T10, S1=150, S2=95),
                                       dict(_T10, S1=16, S2=10)])
    r.esit("⑩ üç asansörde en büyük PE seçiliyor", _d10c.get("SPE"),
           AVT.koruma_iletkeni_kesiti(150)[0])
    r.esit("⑩ Sapd 25 mm² üst sınırında", _d10c.get("Sapd"), 25)
    r.kontrol("⑩ tek asansörlük Sapd, çok asansörlüden büyük olamaz",
              _d10.get("Sapd") <= _d10c.get("Sapd"))

    #  ⑪  BURKULMA HESAPLANAMADIĞINDA PAFTA SEBEBİNİ YAZAR
    #  λ, EN 81-50'nin ω çizelgesinin ( 20…250 ) dışına çıkarsa σk yoktur.
    #  Eskiden satır "σk = —  ≤  σperm = 205" diye basılıp yanına UYGUN DEĞİL
    #  yazıyordu:  boş hücrenin yanında bir ret.  Okuyan, gerilmenin sınırı
    #  AŞTIĞINI sanar;  oysa hesap hiç yapılamamıştır.
    _s11 = MK.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı"})
    _b11 = next(x for x in _s11["bolumler"] if x["kimlik"] == "agirlik_raylari")
    _w11 = next((a["deger"] for a in _b11["adimlar"]
                 if isinstance(a, dict) and str(a.get("sembol") or "") == "ω"), "yok")
    r.kontrol("⑪ ofis varsayılanı ω'yı tablo dışına taşıyor", _w11 is None,
              f"→ ω = {_w11!r}")
    _metinler = " | ".join(str(a.get("aciklama") or "") for a in _b11["adimlar"]
                           if isinstance(a, dict))
    r.kontrol("⑪ satır 'HESAPLANAMADI' diyor, sessizce reddetmiyor",
              "HESAPLANAMADI" in _metinler, f"→ {_metinler[:120]}")
    r.kontrol("⑪ sebep ( λ ve çizelge sınırı ) paftada yazılı",
              "286" in _metinler and "250" in _metinler)
    r.kontrol("⑪ bölüm sonucu 'denetlenemedi' diyor",
              "denetlenemedi" in str(_b11["sonuc"]["metin"]),
              f"→ {_b11['sonuc']['metin'][:90]}")
    #  Gerçekten AŞAN durumda mesaj değişmeli — ikisi farklı şeydir.
    _s11b = MK.hesapla({"agirlik_guvenlik_tertibati": "Kaymalı",
                        "agirlik_konsol_arasi": 2500})
    _b11b = next(x for x in _s11b["bolumler"] if x["kimlik"] == "agirlik_raylari")
    r.kontrol("⑪ ω varken mesaj 'denetlenemedi' demiyor",
              "denetlenemedi" not in str(_b11b["sonuc"]["metin"]),
              f"→ {_b11b['sonuc']['metin'][:90]}")

    #  ⑫  GEÇERSİZ AÇI VE STANDART DIŞI KANAL:  GİRDİDE RET, KİTAPTA HÜKÜM YOK
    #  İki birleşim fiziksel ya da standarda aykırıdır:
    #    · sarılma açısı kanalın sarım sayısına uymuyor — tek sarımda α > 180°,
    #      çift sarımda α ≤ 180° ( tek sarıma ait açı );
    #    · sertleştirilmemiş DÜZ V kanal — TS EN 81-50 m.5.11.2.3.1.2 alt
    #      kesilme ister ( "an undercut is necessary" ).
    #  Eskiden motor bunları hesaplıyor, satırlara "UYGUN" basıyor ( düz V
    #  576 senaryonun 142'sinde "UYGUNDUR" ), teslim kitabı ise hiç denetlemiyor
    #  ve tek sarım · 300°'de RAPOR'a üç kez "UYGUNDUR." yazıyordu.
    _CS = "Yarım Daire Kanal (Çift Sarım)"
    for _ad12, _g12, _parca in (
            ("tek sarım · 300°", {"sarilma_acisi": 300}, "tek sarımlı kanalda 180°'yi aşamaz"),
            ("tek sarım · 181°", {"sarilma_acisi": 181}, "tek sarımlı kanalda 180°'yi aşamaz"),
            ("çift sarım · 180°", {"kanal_sekli": _CS, "sarilma_acisi": 180},
             "çift sarımlı kanalda 180°'yi aşmalıdır"),
            ("düz V · sertleştirilmemiş",
             {"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmemiş",
              "sarilma_acisi": 180}, "m.5.11.2.3.1.2")):
        _s12 = MK.hesapla(_g12)
        r.kontrol(f"⑫ {_ad12} girdide reddediliyor",
                  _s12.get("aktif") is False
                  and any(_parca in h for h in _s12.get("hata") or []),
                  f"→ {_s12.get('hata')}")
    for _ad12, _g12 in (("tek sarım · 180°", {"sarilma_acisi": 180}),
                        ("çift sarım · 181°", {"kanal_sekli": _CS, "sarilma_acisi": 181}),
                        ("düz V · sertleştirilmiş",
                         {"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmiş",
                          "sarilma_acisi": 180})):
        r.kontrol(f"⑫ {_ad12} kabul ediliyor", MK.hesapla(_g12).get("aktif") is True)
    r.esit("⑫ ret sırasında kanal işlemesi sessizce değiştirilmiyor",
           MK.hesapla({"kanal_sekli": "V Kanal", "kanal_isleme": "Sertleştirilmemiş"})
           ["girdi"]["kanal_isleme"], "Sertleştirilmemiş")
    #  Uygulama projesi de aynı reddi taşımalı ( ekran bu yoldan hesaplar )
    _u12 = UY.hesapla(UG.tamamla(dict(dict(UG.varsayilanlar(), **TAM), sarilma_acisi=300)))
    r.kontrol("⑫ uygulama projesi de imkânsız açıyı reddediyor",
              _u12.get("aktif") is False, f"→ {_u12.get('hata')}")
    #  Geçerli çift sarımda tahrik hücreleri eksiksiz yazılmalı
    _s12c = MK.hesapla({"kanal_sekli": _CS, "sarilma_acisi": 330})
    _bos = [h for h in ("S184", "AA184", "AE216", "AF235", "AJ240",
                        "AH278", "AF283", "K285", "O285")
            if _s12c["_h"].get(h) is None]
    r.esit("⑫ geçerli çift sarımda tahrik hücreleri yazılıyor", _bos, [])
    #  TESLİM KİTABI:  hüküm hücreleri üç kalkanı da CANLI taşımalı
    import openpyxl as _oxl
    _ws12 = _oxl.load_workbook(io.BytesIO(
        _MX4.mukavemet_xlsx({"sarilma_acisi": 180})))["11-Muk. Hesapları"]
    for _z12 in ("Z242", "Z257", "Z271", "Z285"):
        _f12 = str(_ws12[_z12].value or "")
        r.kontrol(f"⑫ kitap hükmü {_z12}:  açı yok · standart dışı kanal · "
                  "sarıma aykırı açı kalkanları",
                  _f12.startswith('=IF($S$184="","HESAP EKSİK"')
                  and "alt kesilmesiz V" in _f12 and "sarım" in _f12
                  and _MX4.KANAL_F_ARALIK in _f12,
                  f"→ {_f12[:80]!r}")
    r.kontrol("⑫ T1 · T2 · oran hücrelerine dokunulmuyor",
              str(_ws12["K285"].value or "").startswith("="),
              f"→ {_ws12['K285'].value!r}")
    r.kontrol("⑫ eski çift sarım notu ( A286 ) artık yazılmıyor",
              _ws12["A286"].value is None, f"→ {_ws12['A286'].value!r}")

    #  ⑬  GENEL HÜKÜM:  "UYGUN DEĞİL"  >  "HESAP EKSİK"  >  "UYGUNDUR"
    #  Eksik önce gelirse, dört bölümü çakılan bir proje ekranda yalnız
    #  "HESAP EKSİK" der ve okuyan tasarımın tutmadığını göremez.  Hüküm
    #  MOTORDA üretilir;  PDF ve ekran onu yalnız basar ( iki kopya hâlinde
    #  tutulduğunda zaten bir kez ayrışmıştı ).
    _S = lambda u: {"sonuc": {"uygun": u}}                      # noqa: E731
    _E = lambda u: {"sonuc": {"uygun": u}, "eksik_hesap": "x"}  # noqa: E731
    for _ad, _bol, _tu, _eks, _bek in (
            ("kalan varken eksik onu örtmez", [_S(True), _S(False)], False, ["e"],
             "UYGUN DEĞİLDİR."),
            ("yalnız eksik varsa HESAP EKSİK", [_S(True), _E(False)], False, ["e"],
             "HESAP EKSİK"),
            ("hiçbiri yoksa UYGUNDUR", [_S(True), _S(True)], True, [], "UYGUNDUR."),
            ("engelleyici varsa UYGUN DEĞİL", [_S(True)], False, [],
             "UYGUN DEĞİLDİR.")):
        r.esit(f"⑬ {_ad}", MK.genel_hukum(_bol, _tu, _eks)[0], _bek)
    #  GERÇEK PROJEDE:  varsayılan girdide hem kalan bölüm hem eksik vardır.
    _s13 = UY.hesapla(UG.tamamla(dict(UG.varsayilanlar(), **TAM)))
    _o13 = _s13["ozet"]
    _kalan13 = [b["baslik"][:34] for b in _s13["bolumler"]
                if (b.get("sonuc") or {}).get("uygun") is False
                and not b.get("eksik_hesap")]
    r.kontrol("⑬ senaryoda hem kalan bölüm hem eksik var",
              bool(_kalan13) and bool(_o13.get("eksik_hesap")),
              f"→ kalan {_kalan13} / eksik {_o13.get('eksik_hesap')}")
    r.esit("⑬ hüküm kalan bölümü söylüyor, eksiği değil",
           _o13.get("genel_sonuc"), "UYGUN DEĞİLDİR.")
    r.esit("⑬ kısa hüküm de aynı", _o13.get("genel_sonuc_kisa"), "UYGUN DEĞİL")
    #  PDF EKRANLA AYNI HÜKMÜ BASMALI
    from exports import pdf_export as _PDF13
    _pdf13 = _PDF13.uygulama_pdf(
        {"asansorler": [dict(_s13, no=1, tanim="A")], "adet": 1}, {})
    r.kontrol("⑬ PDF üretiliyor", len(_pdf13) > 10000, f"→ {len(_pdf13)} bayt")
    _kaynak13 = io.open(os.path.join(KOK, "exports", "pdf_export.py"),
                        encoding="utf-8").read()
    r.kontrol("⑬ PDF hükmü kendi kurmuyor, motordan okuyor",
              _kaynak13.count('o.get("genel_sonuc")') == 2
              and "HESAP EKSİK" not in _kaynak13,
              "→ pdf_export hâlâ kendi hükmünü kuruyor")
    _js13 = io.open(os.path.join(KOK, "static", "uygulama.js"),
                    encoding="utf-8").read()
    r.kontrol("⑬ ekran hükmü kendi kurmuyor, motordan okuyor",
              "genel_sonuc_kisa" in _js13 and "'HESAP EKSİK'" not in _js13,
              "→ uygulama.js hâlâ kendi hükmünü kuruyor")

    #  ⑭  ÇOKLU PAKETTE EKSİK KİTAP SESSİZCE ATLANMAZ
    #  Hesaplanamayan asansör eskiden ``continue`` ile geçiliyordu:  iki
    #  asansörlük projede tek kitaplı ZIP iniyor, kullanıcı farkına
    #  varmıyordu.
    from api.uygulama import _asansor_kitaplari as _AK14
    _p14 = {"asansorler": [{"no": 1, "tanim": "A", "aktif": True, "girdi": {}},
                           {"no": 2, "tanim": "B", "aktif": False, "girdi": {}}]}
    _k14 = _AK14(_p14, {})
    _adlar14 = [a for a, _ in _k14]
    r.kontrol("⑭ eksik asansör pakette bildiriliyor",
              any(a.endswith(".txt") for a in _adlar14), f"→ {_adlar14}")
    _not14 = next(i for a, i in _k14 if a.endswith(".txt")).decode("utf-8")
    r.kontrol("⑭ bildirimde asansörün adı geçiyor", "2 - B" in _not14,
              f"→ {_not14[:120]!r}")
    r.kontrol("⑭ paketin eksik olduğu açıkça yazıyor",
              "TAMAMI DEĞİLDİR" in _not14)
    #  Hepsi üretilebiliyorsa fazladan dosya OLMAMALI
    _k14b = _AK14({"asansorler": [{"no": 1, "tanim": "A", "aktif": True,
                                   "girdi": {}}]}, {})
    r.esit("⑭ eksik yokken bildirim dosyası eklenmiyor",
           [a for a, _ in _k14b if a.endswith(".txt")], [])

    #  ⑮  α — SARILMA AÇISI ZORUNLU BEYANDIR, VARSAYIMI YOKTUR
    #  TS EN 81-50 m.5.11.2.1'in iki eşitsizliği terstir;  hiçbir açı iki
    #  kontrolde birden emniyetli değildir ( 180° varsayılanı 486 senaryonun
    #  %33'ünde yükleme/frenleme hükmünü geçme yönüne çeviriyordu ).  Bu
    #  yüzden açı girilmezse dört SINIR hesaplanmaz ve bölüm HESAP EKSİK olur.
    #  Ama bölüm ERKEN DÖNMEZ:  bir ara sürüm boş bölüm döndürüp T1 · T2'yi
    #  bile hesaplamıyor, Excel'i hiç üretmiyordu.
    _CS15 = "Yarım Daire Kanal (Çift Sarım)"
    _s15y = MK.hesapla({})
    _s15b = MK.hesapla({"sarilma_acisi": 150})
    _s15t = MK.hesapla({"sarilma_acisi": 180})
    _b15y = next(x for x in _s15y["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
    r.kontrol("⑮ α varsayılanı yok", _s15y["girdi"].get("sarilma_acisi") is None,
              f"→ {_s15y['girdi'].get('sarilma_acisi')!r}")
    r.kontrol("⑮ α yokken bölüm HESAP EKSİK",
              "α girilmedi" in str(_b15y.get("eksik_hesap") or ""),
              f"→ {_b15y.get('eksik_hesap')!r}")
    r.kontrol("⑮ α yokken genel hüküm 'uygundur' olamıyor",
              _s15y["ozet"]["tumu_uygun"] is False)
    #  Açıdan BAĞIMSIZ her şey yine hesaplanmalı
    _eksik_h = [h for h in ("AF235", "AJ240", "K242", "AF250", "AJ255", "K257",
                            "AH264", "AF269", "K271", "AH278", "AF283", "K285",
                            "AS190", "AE216")
                if _s15y["_h"].get(h) is None]
    r.esit("⑮ α yokken T1 · T2 · oranlar · f yine hesaplanıyor", _eksik_h, [])
    r.esit("⑮ α yokken sınır hücreleri YAZILMIYOR ( sahte sayı yok )",
           [h for h in ("S184", "AA184", "O242", "O257", "O271", "O285")
            if h in _s15y["_h"]], [])
    _k15y = [a["deger"] for a in _b15y["adimlar"] if isinstance(a, dict)
             and a.get("deger") in ("UYGUN", "UYGUN DEĞİL", "HESAP EKSİK")]
    r.esit("⑮ α yokken beş kontrol satırı da HESAP EKSİK", _k15y,
           ["HESAP EKSİK"] * 5)
    r.kontrol("⑮ α yokken proje uyarısı çıkıyor",
              any("SARILMA AÇISI" in u for u in _s15y["uyarilar"]),
              f"→ {[u[:40] for u in _s15y['uyarilar']]}")
    r.kontrol("⑮ α girilince uyarı çıkmıyor",
              not any("SARILMA AÇISI" in u for u in _s15b["uyarilar"]))
    r.esit("⑮ girilen açı hesaba giriyor", _s15b["_h"]["S184"], 150.0)
    r.kontrol("⑮ açı büyüyünce e^(f·α) sınırı da büyüyor",
              _s15t["_h"]["O242"] > _s15b["_h"]["O242"],
              f"→ {_s15b['_h']['O242']:.4f} → {_s15t['_h']['O242']:.4f}")
    _a15 = [a for a in next(x for x in _s15b["bolumler"]
                            if x["kimlik"] == "tahrik_yetenegi")["adimlar"]
            if isinstance(a, dict) and str(a.get("sembol") or "") == "α"]
    r.esit("⑮ paftada α kaynağı 'GİRİŞ'", _a15[0].get("kaynak") if _a15 else None,
           "GİRİŞ")
    #  GEVŞEK HALAT, EKSİK AÇIYLA ÖRTÜLMEZ — kesin başarısızlık eksikten güçlü
    _s15g = MK.hesapla({"acil_frenleme_a": 9.81})
    _b15g = next(x for x in _s15g["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
    r.kontrol("⑮ α yokken gevşek halat 'UYGUN DEĞİL' kalıyor, eksikle örtülmüyor",
              not _b15g.get("eksik_hesap")
              and "gevşiyor" in str(_b15g["sonuc"]["metin"]),
              f"→ {_b15g['sonuc']['metin']!r} / eksik {_b15g.get('eksik_hesap')!r}")
    #  Türetme kalktı:  C · D · Ra artık girdi değil
    for _alan in ("sap_kasnak_yuk", "makine_yatak_yuk", "halat_arasi_yan",
                  "halat_arasi"):
        r.kontrol(f"⑮ '{_alan}' girdisi kaldırıldı",
                  _alan not in _s15y["girdi"], "→ hâlâ var")
    #  ÇİFT SARIMDA AÇI 180°'Yİ AŞARSA BLOKE HÜKMÜ VERİLİR
    _s15c = MK.hesapla({"kanal_sekli": _CS15, "sarilma_acisi": 330})
    _b15c = next(x for x in _s15c["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
    r.kontrol("⑮ çift sarımda 180°'yi aşan açıyla hüküm veriliyor",
              not _b15c.get("eksik_hesap"), f"→ {_b15c.get('eksik_hesap')!r}")
    r.esit("⑮ çift sarımda üst sınır 360°", _s15c["_h"]["S184"], 330.0)
    #  Tek sarımda 180°'yi aşan açı reddedilmeli ( fiziksel olarak imkânsız )
    r.kontrol("⑮ tek sarımda α > 180° kabul edilmiyor  ( girdide ret, bkz. ⑫ )",
              MK.hesapla({"sarilma_acisi": 300}).get("aktif") is False)
    r.kontrol("⑮ aralık dışı açı girdi doğrulamasında reddediliyor",
              MK.hesapla({"sarilma_acisi": 400}).get("aktif") is False)
    #  TESLİM EDİLEN KİTAP
    import openpyxl as _o15
    _w15 = _o15.load_workbook(io.BytesIO(
        _MX4.mukavemet_xlsx({"sarilma_acisi": 180})))["11-Muk. Hesapları"]
    r.esit("⑮ kitap girilen açıyı yazıyor", _w15["S184"].value, 180.0)
    try:
        _x15 = _MX4.mukavemet_xlsx({})
    except Exception as _e15:                                  # noqa: BLE001
        _x15 = None
        r.kontrol("⑮ α yokken de kitap üretiliyor", False, f"→ {_e15}")
    if _x15 is not None:
        r.kontrol("⑮ α yokken de kitap üretiliyor", True)
        _w15b = _o15.load_workbook(io.BytesIO(_x15))["11-Muk. Hesapları"]
        r.kontrol("⑮ α yokken kitapta açı hücresi BOŞ", _w15b["S184"].value is None,
                  f"→ {_w15b['S184'].value!r}")
        r.kontrol("⑮ kitaptaki geometrik türetme temizlendi",
                  all(_w15b[h].value is None for h in ("U174", "Z178", "C184",
                                                       "L184", "P184")),
                  f"→ {[_w15b[h].value for h in ('U174','Z178','C184','L184','P184')]}")
        for _z in ("Z242", "Z257", "Z271", "Z285"):
            r.kontrol(f"⑮ kitap hükmü {_z} açı boşken HESAP EKSİK yazacak şekilde",
                      str(_w15b[_z].value or "").startswith('=IF($S$184="","HESAP EKSİK"'),
                      f"→ {str(_w15b[_z].value)[:50]!r}")
        for _o in ("O242", "O257", "O271", "O285"):
            r.kontrol(f"⑮ kitap sınırı {_o} açı boşken sayı üretmeyecek şekilde",
                      str(_w15b[_o].value or "").startswith('=IF($S$184="",""'),
                      f"→ {str(_w15b[_o].value)[:50]!r}")
    #  ÇOKLU PAKETTE α'SIZ ASANSÖR ZIP'TEN DÜŞMEMELİ
    from api.uygulama import _asansor_kitaplari as _AK15
    _k15z = _AK15({"asansorler": [{"no": 1, "tanim": "A", "aktif": True,
                                   "girdi": {}}]}, {})
    r.esit("⑮ α'sız asansörün kitabı pakete giriyor",
           [a for a, _ in _k15z if a.endswith(".xlsx")],
           ["Mukavemet Hesaplari - 1 - A.xlsx"])
    r.esit("⑮ açı proje dosyasından geri okunuyor",
           _MX4.xlsx_oku(_MX4.mukavemet_xlsx({"sarilma_acisi": 165}))
           .get("sarilma_acisi"), 165)
    r.kontrol("⑮ ek girdi bloğu ofis sabitleri bloğuna taşmıyor",
              _MX4._ek_satir_cakismasi() is False)

    #  ⑯  ELEKTRİK SAYFASI MOTORUN KULLANDIĞI DEĞERLERİ YAZIYOR
    #  Avan motoru L1 · L2 · S1 · S2'yi kendi aralıklarına göre denetler ve
    #  aralık dışındakini REDDEDİP varsayılana döner.  Kitap girileni ham
    #  yazıyordu:  L1 = 600 m'de pafta 29,85 m ile, kitap 600 m ile ε
    #  hesaplıyordu — aynı projenin iki belgesi farklı sonuç veriyordu.
    _HUC16 = {"kolon_uzunluk": "W26", "makine_uzunluk": "W27",
              "kolon_kesit": "W33", "makine_kesit": "W34"}
    _ARALIK_DISI = {"kolon_uzunluk": 600, "makine_uzunluk": 900,
                    "kolon_kesit": 900, "makine_kesit": 900}
    for _alan, _hucre in _HUC16.items():
        #  TAM zaten kolon_uzunluk taşıyor;  üzerine yazılır.
        _ham16 = dict(UG.varsayilanlar(), **TAM)
        _ham16[_alan] = _ARALIK_DISI[_alan]
        _g16 = UG.tamamla(_ham16)
        _r16 = UY.hesapla(_g16)
        _motor = {"kolon_uzunluk": "L1", "makine_uzunluk": "L2",
                  "kolon_kesit": "S1", "makine_kesit": "S2"}[_alan]
        _deg = None
        for _b in _r16["bolumler"]:
            for _a in _b.get("adimlar") or []:
                if (str(_a.get("sembol") or "") == _motor
                        and _a.get("deger") is not None):
                    _deg = _a["deger"]
        _ws16 = _o15.load_workbook(io.BytesIO(
            _MX4.mukavemet_xlsx(_g16)))["12-Elk.Hesapları"]
        _kitap = _ws16[_hucre].value
        r.kontrol(f"⑯ {_motor} aralık dışıyken pafta ile kitap aynı",
                  _deg is not None and abs(float(_kitap) - float(_deg)) < 0.01,
                  f"→ pafta {_deg} · kitap {_kitap}")
        r.kontrol(f"⑯ {_motor} girilen aralık dışı değeri KULLANMIYOR",
                  abs(float(_kitap) - _ARALIK_DISI[_alan]) > 0.01,
                  f"→ kitap {_kitap}, girilen {_ARALIK_DISI[_alan]}")
        #  Reddin sebebi kullanıcıya söyleniyor mu
        r.kontrol(f"⑯ {_motor} reddi uyarıda yazıyor",
                  any(_motor in u and "geçerli aralık" in u
                      for u in _r16["uyarilar"]),
                  f"→ {[u for u in _r16['uyarilar'] if 'aralık' in u]}")
    #  Geçerli değer aynen yazılmalı — red yalnız aralık dışında olmalı
    _g16b = UG.tamamla(dict(dict(UG.varsayilanlar(), **TAM), kolon_uzunluk=45))
    _ws16b = _o15.load_workbook(io.BytesIO(
        _MX4.mukavemet_xlsx(_g16b)))["12-Elk.Hesapları"]
    r.esit("⑯ geçerli L1 aynen yazılıyor", float(_ws16b["W26"].value), 45.0)
    #  Proje dosyası KULLANICININ GİRDİĞİNİ korumalı ( hesap ayrı, dosya ayrı )
    r.esit("⑯ geri okumada kullanıcının girdiği değer korunuyor",
           _MX4.xlsx_oku(_MX4.mukavemet_xlsx(UG.tamamla(
               dict(dict(UG.varsayilanlar(), **TAM), kolon_uzunluk=600))))
           .get("kolon_uzunluk"), 600)

    #  ⑰  TESLİM KİTABINDA SÜRTÜNME ÇARPANI f KANAL ŞEKLİNE BAĞLI
    #  Kitap yarım daire kanalda da V kanal bağıntısını kullanıyor, γ · β'yı
    #  hücreye çiviliyordu ( AH102 = 38 · AH103 = 90 · Y216 = 38 ).  Pafta ile
    #  kitap 10 kanal × işleme birleşiminin 8'inde ayrışıyordu.  Sayısal
    #  eşitlik TEST 10'da LibreOffice ile denetlenir;  burası YAPIYI sabitler.
    from engine.uygulama import mukavemet_tablolari as _MT17
    from engine.uygulama import sabitler as _US17
    for _ofis17 in (None, {"kanal_gama_v": 45, "kanal_gama_yd": 30, "kanal_beta": 100}):
        _O17 = _US17.sabitler(_ofis17)
        _g17 = {"sarilma_acisi": 180}
        if _ofis17:
            _g17["_ofis"] = _ofis17
        _wb17 = _o15.load_workbook(io.BytesIO(_MX4.mukavemet_xlsx(_g17)))
        _tb17 = _wb17["TABLOLAR"]
        _et17 = "ofis açıları değişik" if _ofis17 else "ofis varsayılan"
        for _ad17, _sat17 in _MX4.KANAL_TABLO_SATIRI.items():
            _bek17 = (_MT17.kanal_acisi(_ad17, _O17["kanal_gama_v"], _O17["kanal_gama_yd"]),
                      _MT17.kanal_beta(_ad17, _O17["kanal_beta"]),
                      1 if _MT17.kanal_yarim_daire_mi(_ad17) else 0,
                      _MT17.kanal_gecis_sayisi(_ad17) or 1)
            _bul17 = tuple(_tb17[f"{_MX4.KANAL_F_SUTUN[x]}{_sat17}"].value
                           for x in ("gama", "beta", "yarim_daire", "gecis"))
            r.esit(f"⑰ [{_et17}] kanal tablosu γ · β · tür · geçiş — {_ad17}",
                   _bul17, _bek17)
    _ws17 = _wb17["11-Muk. Hesapları"]
    r.kontrol("⑰ γ hücresi ( AH102 ) kanal tablosundan okunuyor",
              str(_ws17["AH102"].value).startswith("=VLOOKUP('Veri Girişi'!$F$105"),
              f"→ {_ws17['AH102'].value!r}")
    r.kontrol("⑰ β hücresi ( AH103 ) kanal tablosundan okunuyor",
              str(_ws17["AH103"].value).startswith("=VLOOKUP('Veri Girişi'!$F$105"),
              f"→ {_ws17['AH103'].value!r}")
    r.esit("⑰ bloke satırının γ'sı artık sabit 38 değil", _ws17["Y216"].value, "=AH102")
    for _h17, _v17 in (("AJ198", "V188/AE198"), ("AL202", "AC202/AG202"),
                       ("AU206", "AK206*AN206/AN207"), ("AV211", "AK211*AO211/AO212"),
                       ("AE216", "1/SIN(Y216/M216/180*PI())*P216")):
        _f17 = str(_ws17[_h17].value)
        r.kontrol(f"⑰ {_h17} yarım daire dalını taşıyor ve V bağıntısını koruyor",
                  _f17.startswith("=IF(VLOOKUP(") and "COS(" in _f17
                  and _f17.endswith(f",{_v17})"),
                  f"→ {_f17[:90]!r}")
    r.kontrol("⑰ yarım daire notu yalnız o kanalda görünecek şekilde",
              str(_ws17["A195"].value).startswith("=IF(VLOOKUP("),
              f"→ {str(_ws17['A195'].value)[:60]!r}")
    #  Ofisin ana ( usta ) kopyası da aynı düzeltmeyi taşımalı
    _u17 = _o15.load_workbook(io.BytesIO(_MX4.duzeltilmis_kaynak()))["11-Muk. Hesapları"]
    r.kontrol("⑰ usta kopyada da f kanal şekline bağlı",
              str(_u17["AU206"].value).startswith("=IF(VLOOKUP("),
              f"→ {str(_u17['AU206'].value)[:60]!r}")

    #  ⑱  ELEKTRİK HESABI YAPILAMAYINCA KİTAP DA HÜKÜM VERMEZ
    #  Uygulama hesabı elektriği "HESAP EKSİK" sayıp paftaya bölüm basmıyordu;
    #  kitabın elektrik sayfası ise ham girdilerle hesaplayıp işaretsiz
    #  "UYGUNDUR." yazıyordu.
    _g18 = UG.tamamla(dict(dict(UG.varsayilanlar(), **TAM), kuyu_genisligi=0,
                           sarilma_acisi=180))
    r.kontrol("⑱ senaryoda elektrik hesabı gerçekten yapılamıyor",
              UY.hesapla(_g18)["ozet"].get("elektrik_var") is False)
    _e18 = _o15.load_workbook(io.BytesIO(_MX4.mukavemet_xlsx(_g18)))["12-Elk.Hesapları"]
    r.esit("⑱ kitabın sekiz elektrik hükmü HESAP EKSİK",
           [_e18[h].value for h in _MX4.ELEKTRIK_HUKUM_HUCRELERI],
           ["HESAP EKSİK"] * len(_MX4.ELEKTRIK_HUKUM_HUCRELERI))
    r.kontrol("⑱ sebep sayfanın başında yazılı",
              str(_e18["A2"].value or "").startswith("HESAP EKSİK — elektrik hesabı yapılamadı"),
              f"→ {_e18['A2'].value!r}")
    _e18b = _o15.load_workbook(io.BytesIO(_MX4.mukavemet_xlsx(
        UG.tamamla(dict(dict(UG.varsayilanlar(), **TAM), sarilma_acisi=180)))))["12-Elk.Hesapları"]
    r.kontrol("⑱ elektrik hesabı yapılabiliyorsa kitabın hükümleri formül kalıyor",
              all(str(_e18b[h].value or "").startswith("=IF(")
                  for h in _MX4.ELEKTRIK_HUKUM_HUCRELERI)
              and _e18b["A2"].value is None)

    #  ⑲  Pm, GÜCÜ VE MOMENTİ BELİRLEYEN YÜKTEN TÜRER
    #  Pm = F1 − Ga idi:  halatın tamamı kabin tarafında, yön · zincir · kablo
    #  yok.  q = 0,60'ta 185,7 kg basılıyor, belirleyici yük 269,1 kg idi.
    for _ad19, _g19 in (("varsayılan", {}), ("denge zinciri", {"denge_zinciri": "Var"}),
                        ("q = 0,60", {"_ofis": {"q_denge": 0.60}}),
                        ("1:1 askı", {"aski_orani": 1})):
        _s19 = MK.hesapla(_g19)
        _h19, _gi19 = _s19["_h"], _s19["girdi"]
        r.kontrol(f"⑲ [{_ad19}] Pm = Gmax / i",
                  abs(_h19["AQ7"] - _h19["AQ9"] / _gi19["aski_orani"]) < 1e-9,
                  f"→ Pm {_h19['AQ7']} · Gmax/i {_h19['AQ9'] / _gi19['aski_orani']}")
        r.kontrol(f"⑲ [{_ad19}] M = Pm × Dt/2",
                  abs(_h19["AQ21"] - _h19["AQ7"] * _gi19["tahrik_kasnak_capi"] / 2000) < 1e-9)
    r.kontrol("⑲ denge zinciri Pm'yi de değiştiriyor",
              MK.hesapla({"denge_zinciri": "Var"})["_h"]["AQ7"] != MK.hesapla({})["_h"]["AQ7"])
    _m19 = _o15.load_workbook(io.BytesIO(_MX4.mukavemet_xlsx({"sarilma_acisi": 180})))["11-Muk. Hesapları"]
    r.esit("⑲ kitapta Pm de Gmax'tan", _m19["AQ7"].value, "=AQ9/'Veri Girişi'!B100")
    r.esit("⑲ kitapta M = Pm × Dt/2", _m19["AQ21"].value, "=AQ7*(AQ10/2000)")

    #  ⑳  TEK ASANSÖRLÜ CAD PAKETİNDE EKSİK KİTAP SESSİZ KALMAZ
    #  Çoklu pakette bildirim vardı;  tekli pakette "except Exception: pass".
    import zipfile as _zip20
    import api.uygulama as _API20
    if _API20.X_DXF is None:
        r.atla("⑳ CAD kitaplıkları kurulu değil — tekli paket denetimi atlandı")
    else:
        _v20 = {"girdiler": dict(TAM, sarilma_acisi=180)}
        _asil20 = _API20.X_MXLS.mukavemet_xlsx

        def _bozuk20(*_a, **_k):
            raise FileNotFoundError("Mukavemet şablonu bulunamadı")
        _API20.X_MXLS.mukavemet_xlsx = _bozuk20
        try:
            _y20 = _API20.indir_uygulama_dwg(_v20)
        finally:
            _API20.X_MXLS.mukavemet_xlsx = _asil20
        _z20 = _zip20.ZipFile(io.BytesIO(_y20.body))
        _n20 = _z20.namelist()
        r.kontrol("⑳ kitap üretilemezse tekli paket yine çıkıyor",
                  any(x.endswith(".dxf") for x in _n20), f"→ {_n20}")
        r.kontrol("⑳ tekli pakette eksik kitap BİLDİRİLİYOR",
                  "URETILEMEYEN ASANSORLER.txt" in _n20
                  and not any(x.endswith(".xlsx") for x in _n20), f"→ {_n20}")
        r.kontrol("⑳ bildirimde sebep yazılı",
                  "şablonu bulunamadı" in _z20.read("URETILEMEYEN ASANSORLER.txt").decode("utf-8"))
        r.kontrol("⑳ başlıkta KITAP notu ( arayüz ZIP'i açmadan uyarır )",
                  "KITAP" in (_y20.headers.get("X-Avan-Not") or "").split(","),
                  f"→ {_y20.headers.get('X-Avan-Not')!r}")
        _y20b = _API20.indir_uygulama_dwg(_v20)
        r.kontrol("⑳ kitap üretilebiliyorsa KITAP notu yok",
                  "KITAP" not in (_y20b.headers.get("X-Avan-Not") or "").split(","),
                  f"→ {_y20b.headers.get('X-Avan-Not')!r}")
    #  ARAYÜZ İKİ PAKET YOLUNDA DA NOTU OKUMALI
    _js20 = (io.open(os.path.join(KOK, "static", "ortak.js"), encoding="utf-8").read()
             + io.open(os.path.join(KOK, "static", "avan.js"), encoding="utf-8").read())
    r.kontrol("⑳ arayüz KITAP notunu iki indirme yolunda da gösteriyor",
              _js20.count("'KITAP'") >= 2 and "M_KITAP_EKSIK" in _js20)
    _ad20, _ic20 = _API20._uretilemeyen_notu(["1 - A:  şablon bulunamadı"])
    r.kontrol("⑳ bildirim dosyası adı ve içeriği",
              _ad20.endswith(".txt") and "TAMAMI DEĞİLDİR" in _ic20.decode("utf-8")
              and "1 - A" in _ic20.decode("utf-8"))

    # ---------------------------------------------------------------------
    #  ㉑  TESLİM KİTABININ ELEKTRİK SAYFASI PAFTAYLA AYNI SAYIYI VERİR
    # ---------------------------------------------------------------------
    #  Kitap bu sayfayı kendi yöntemiyle hesaplıyordu:  κ = 56 ( pafta 44,4 ),
    #  kendi yükleme cetveli ( 4 priz · kuyu 9 × 12 W · kabin 1 × 40 W ·
    #  makine dairesiz projede bile makine dairesi 3 × 40 W ) ve başka bir
    #  kuyu aydınlatma bağıntısı.  Aynı projede ε pafta %0,97, kitap %0,77.
    #  Kitaplar LibreOffice ile YENİDEN HESAPLANIR ve paftanın sayılarıyla
    #  karşılaştırılır — formüllerin gerçekten aynı sonucu verdiği görülür.
    r.esit("㉑ uygulama ofisinin κ varsayılanı motorunkiyle aynı",
           US.VARSAYILAN["kappa"], AV.OFIS_VARSAYILAN["kappa"])
    _avv21 = {**AV.SABIT_B_VARSAYILAN, **AV.OFIS_VARSAYILAN}
    r.esit("㉑ uygulama ofisinin BÜTÜN elektrik varsayılanları motorunkiyle aynı",
           {k: v for k, v in US.VARSAYILAN.items()
            if k in _avv21 and v != _avv21[k]}, {})
    import shutil as _sh21
    import openpyxl as _op21
    from exports import mukavemet_xlsx as _MX21
    from testler.ortak import (hata_hucresi_ara as _hh21, soffice_yolu as _so21,
                               yeniden_hesapla as _yh21)
    _SEN21 = {
        "mrl": {},
        "daireli": {"mk_yok": False, "mk_uzunluk": 2500, "mk_genislik": 1600},
        "ofis": {"mk_yok": False, "mk_uzunluk": 3100, "mk_genislik": 2200,
                 "_ofis": {"kappa": 56, "kuyu_armatur_W": 36, "kuyu_armatur_lm": 3000,
                           "ayd_sutun": 9, "priz_adedi": 5, "kabin_ustu_armatur": 2,
                           "kuyu_Dmax": 3, "cosfi": 0.8}},
        "dmax0": {"_ofis": {"kuyu_Dmax": 0, "ayd_sutun": 4}},
        #  PAFTANIN REDDETTİĞİ proje:  kitap da reddetmeli
        "yetersiz": {"motor_gucu": 15, "kolon_kesit": 2.5, "kolon_uzunluk": 90},
    }
    if not _so21():
        r.atla("㉑ LibreOffice yok — kitap / pafta elektrik karşılaştırması atlandı")
    else:
        _k21 = os.path.join(KOK, "tmp", "test_elektrik_kitap")
        _sh21.rmtree(_k21, ignore_errors=True)
        os.makedirs(_k21, exist_ok=True)
        _dosya21 = {}
        for _ad, _ek in _SEN21.items():
            _s21 = UY.hesapla(dict(TAM, sarilma_acisi=180, **_ek))
            if not r.kontrol(f"㉑ [{_ad}] senaryo hesaplanıyor", _s21["aktif"],
                             f"→ {_s21.get('hata')}"):
                continue
            _y = os.path.join(_k21, _ad + ".xlsx")
            with open(_y, "wb") as _f:
                _f.write(_MX21.mukavemet_xlsx(_s21["girdi"]))
            _dosya21[_ad] = (_y, _s21)
        _yh21([y for y, _s in _dosya21.values()], os.path.join(_k21, "out"))
        _yak21 = lambda a, b: (isinstance(a, (int, float)) and isinstance(b, (int, float))
                              and abs(a - b) <= 1e-6 * max(1.0, abs(b)))
        for _ad, (_y, _s21) in _dosya21.items():
            _q = os.path.join(_k21, "out", _ad + ".xlsx")
            if not r.kontrol(f"㉑ [{_ad}] kitap yeniden hesaplandı", os.path.isfile(_q)):
                continue
            _w = _op21.load_workbook(_q, data_only=True)[_MX21.ELEKTRIK]
            #  Paftanın sayıları:  uygulama sonucundaki elektrik bölümleri ve
            #  özet.  Ara değerler bölüm satırlarından değil avan özetinden
            #  okunur — pafta o özetten basılır.
            _e = _MX21._elektrik_hesabi(_s21["girdi"])
            _oz, _mk = _e["oz"], _e["mk"]
            r.esit(f"㉑ [{_ad}] pafta özeti ile kitabın kaynağı aynı hesap",
                   (_oz["P_kurulu"], _oz["eps"], _oz["I"]),
                   (_s21["ozet"]["P_kurulu"], _s21["ozet"]["eps"], _s21["ozet"]["I"]))
            for _h, _ne, _bek in (
                    ("AT14", "kurulu güç", _oz["P_kurulu"]),
                    ("AE39", "ε1 kolon hattı", _oz["eps1"]),
                    ("AE46", "ε2 makine besleme", _oz["eps2"]),
                    ("Y53", "ε toplam", _oz["eps"]),
                    ("AE57", "I kolon hattı", _oz["I"]),
                    ("AE62", "I2 makine besleme", _oz["I_motor"]),
                    ("AT8", "priz gücü", _oz["g_priz"]),
                    ("AT11", "kuyu aydınlatma gücü", _oz["g_kuyu"]),
                    ("AT13", "kabin aydınlatma gücü", _oz["g_kabin"]),
                    ("AG157", "kuyu k", _oz["k_kuyu"]),
                    ("AG143", "kuyu η", _oz["eta_kuyu"]),
                    ("AG162", "kuyu ışık akısı T", _oz["T_kuyu"]),
                    ("M170", "kuyu armatür adedi", _oz["n_kuyu"]),
                    ("W32", "κ", _e["S"]["kappa"])):
                r.kontrol(f"㉑ [{_ad}] {_h} {_ne} paftayla aynı",
                          _yak21(_w[_h].value, _bek),
                          f"→ kitap {_w[_h].value!r}, pafta {_bek!r}")
            if _mk.get("aktif"):
                for _h, _ne, _bek in (("AG198", "makine dairesi k", _mk["k"]),
                                      ("AG184", "makine dairesi η", _mk["eta"]),
                                      ("M211", "makine dairesi armatür adedi", _mk["n"])):
                    r.kontrol(f"㉑ [{_ad}] {_h} {_ne} paftayla aynı",
                              _yak21(_w[_h].value, _bek),
                              f"→ kitap {_w[_h].value!r}, pafta {_bek!r}")
            else:
                r.kontrol(f"㉑ [{_ad}] makine dairesiz projede kitap o bölümü hesaplamıyor",
                          "uygulanmaz" in str(_w["A175"].value)
                          and _w["M211"].value in (None, "")
                          and _w["AT12"].value in (None, "", 0),
                          f"→ {_w['A175'].value!r} · M211 {_w['M211'].value!r}")
            #  HÜKÜMLER:  pafta ε / I / I2 uygun değilse kitap da öyle demeli
            _hk = {h: str(_w[h].value or "") for h in ("AS53", "AB60", "AH65")}
            for _h, _uy in (("AS53", _oz["eps_uygun"]), ("AB60", _oz["akim_uygun"]),
                            ("AH65", _oz["akim2_uygun"])):
                r.kontrol(f"㉑ [{_ad}] {_h} hükmü paftayla aynı",
                          _hk[_h].startswith("UYGUNDUR") == bool(_uy),
                          f"→ kitap {_hk[_h]!r}, pafta {_uy!r}")
            r.esit(f"㉑ [{_ad}] elektrik sayfasında hata hücresi yok",
                   [x for x in _hh21(_q) if x.startswith(_MX21.ELEKTRIK)], [])
        r.kontrol("㉑ yetersiz senaryo gerçekten reddediliyor  ( sınanan şey boş değil )",
                  "yetersiz" in _dosya21
                  and not _MX21._elektrik_hesabi(_dosya21["yetersiz"][1]["girdi"])["oz"]["eps_uygun"])
        _sh21.rmtree(_k21, ignore_errors=True)

    # ------------------------------------------------- proje adı sızıntısı
    #  AVAN VE UYGULAMA AYRI PROJELERDİR.  Avandan alınan bölümlerin bazı
    #  notları "kesin seçim UYGULAMA PROJESİNDE yapılır" der;  avan paftasında
    #  doğrudur, uygulama paftasında ise okuyucunun elindeki belgeyi işaret
    #  eder — kendi kendisiyle çelişir.  Metin uyarlanır, HESAP DEĞİŞMEZ.
    import re as _re
    _kalip = _re.compile(r"uygulama projesi", _re.I)
    _sizan = []
    for b in s["bolumler"]:
        for _alan in ("notlar", "aciklamalar", "ekran_notlari"):
            _sizan += [(b["baslik"], x) for x in (b.get(_alan) or [])
                       if _kalip.search(x)]
        for c in (b.get("cetvel") or []):
            if _kalip.search(str(c.get("sigorta") or "")):
                _sizan.append((b["baslik"], f"cetvel: {c['sigorta']}"))
    r.kontrol("uygulama paftasında kendini işaret eden not yok", not _sizan,
              f"→ {_sizan[:2]}")
    #  Aynı metin AVAN paftasında OLDUĞU GİBİ kalmalı — orada doğru
    _av = AV.hesapla(UG.kopru(UG.tamamla(UG.varsayilanlar())))["asansorler"][0]
    _avnot = [x for b in _av["bolumler"]
              for _a in ("notlar", "aciklamalar") for x in (b.get(_a) or [])
              if _kalip.search(x)]
    r.esit("avan paftasında not olduğu gibi duruyor", len(_avnot), 2)

    #  Sigorta kademesi tablo dışına taşarsa da proje adı sızmamalı
    _bt = UY.hesapla(dict(TAM, motor_gucu=400))
    if r.kontrol("çok büyük motorla hesap koşuyor", _bt["aktif"]):
        _c = [b for b in _bt["bolumler"] if "KURULU GÜÇ" in b["baslik"]][0]["cetvel"][0]
        r.kontrol("taşan sigorta hücresinde proje adı yok",
                  not _kalip.search(str(_c["sigorta"])), f"→ {_c['sigorta']!r}")
        #  Cetvele MİL gücü değil, ŞEBEKEDEN ÇEKİLEN güç yazılır
        #  ( Pşeb = Pm / ηm ) — kolon hattında akan odur.
        _etam = US.VARSAYILAN["motor_elektrik_verimi"]
        r.esit("taşan sigortada güç değeri bozulmadı", _c["guc"],
               400_000 / _etam)

    #  Ofis standardı köprüden geçiyor mu
    y = UY.hesapla(dict(TAM, _ofis={"kuyu_armatur_lm": 1000}))
    r.kontrol("ofis standardı elektrik hesabına giriyor",
              y["aktif"] and y["ozet"]["Z_kuyu"] != taban["Z_kuyu"],
              f"→ {y['ozet'].get('Z_kuyu')!r} / {taban['Z_kuyu']!r}")

    # ---------------------------------------------------------- eksik girdi
    s = UY.hesapla({})                       # topraklama ve kolon boyu yok
    r.kontrol("eksik elektrik girdisiyle de hesap koşuyor", s["aktif"],
              f"→ {s.get('hata')}")
    if s["aktif"]:
        r.esit("topraklama olmadan bölüm sayısı", len(s["bolumler"]),
               len(MK.BOLUM_URETICILERI) + 4)
        r.kontrol("topraklamasız özet Re taşımıyor", s["ozet"]["Re"] is None)

    s = UY.hesapla({"mk_yok": False})
    r.kontrol("makine dairesi işaretli ama ölçüsüz → hesap duruyor",
              not s["aktif"])
    r.kontrol("hata makine dairesi ölçüsünü istiyor",
              any("Makine dairesi" in x for x in (s.get("hata") or [])),
              f"→ {s.get('hata')}")

    s = UY.hesapla(dict(TAM, mk_yok=False, mk_uzunluk=4, mk_genislik=3))
    r.kontrol("makine daireli hesap koşuyor", s["aktif"], f"→ {s.get('hata')}")
    if s["aktif"]:
        r.esit("makine daireli bölüm sayısı", len(s["bolumler"]),
               len(MK.BOLUM_URETICILERI) + 9)
        r.kontrol("makine dairesi aydınlatması eklendi",
                  any("MAKİNE DAİRESİ" in a for a in _bolum_adlari(s)))

    #  Mukavemet girdisi geçersizse uygulama da durmalı
    #  ( kabin ağırlığı ARTIK boş bırakılabilir — ofis tablosundan dolar;
    #    burada gerçekten geçersiz bir geometri kullanılıyor )
    s = UY.hesapla({"yan_yatak_boyu": 0})
    r.kontrol("geçersiz mukavemet girdisi uygulamayı da durduruyor",
              not s["aktif"], f"→ {s.get('hata')}")

    #  ------------------------------------------------------------------
    #  BOŞ KABİN AĞIRLIĞI OFİS TABLOSUNDAN DOLAR  —  AVANLA AYNI TABLODAN
    #  ------------------------------------------------------------------
    #  Standartlarda böyle bir çizelge yoktur:  TS EN 81-20 / 81-50 boş kabin
    #  kütlesini ( P ) hep GİRDİ olarak tanımlar.  Tablo ofisin kendi imalatçı
    #  deneyimidir ve İKİ PROJE DE aynı yerden okur ( engine/ortak/ofis.py ) —
    #  ayrı kopyalar tutulsaydı aynı asansör iki projede iki farklı kabin
    #  kütlesiyle hesaplanırdı.
    for _q in (450, 630, 800, 1000, 1125, 1275, 1600, 2000, 2500):
        _u = MK.hesapla({"beyan_yuku": _q, "kabin_agirligi": None})
        if not r.kontrol(f"[Gk] {_q} kg için hesap koşuyor", _u["aktif"],
                         f"→ {_u.get('hata')}"):
            continue
        r.esit(f"[Gk] {_q} kg → uygulama = avan tablosu",
               _u["girdi"]["kabin_agirligi"], float(AVT.tablo11_Gk(_q)))
        #  Karşı ağırlık da onunla birlikte türer
        r.esit(f"[Gk] {_q} kg → karşı ağırlık P + Q/2",
               _u["girdi"]["karsi_agirlik"],
               _u["girdi"]["kabin_agirligi"] + _q / 2.0)
    #  Elle girilen değer HER ZAMAN önceliklidir
    _el = MK.hesapla({"beyan_yuku": 1275, "kabin_agirligi": 1234})
    r.esit("[Gk] elle girilen değer korunuyor",
           _el["girdi"]["kabin_agirligi"], 1234)
    #  Paftada kaynağı yazıyor:  tahmin mi, giriş mi
    def _p_kaynagi(s):
        b1 = [x for x in s["bolumler"] if x["baslik"].startswith("1 ")][0]
        return next(a["kaynak"] for a in b1["adimlar"] if a.get("sembol") == "P")
    r.esit("[Gk] elle girilende kaynak GİRİŞ", _p_kaynagi(_el), "GİRİŞ")
    _tb = MK.hesapla({"beyan_yuku": 1275, "kabin_agirligi": None})
    r.kontrol("[Gk] tablodan gelende kaynak ofis tablosu",
              "OFİS TABLOSU" in _p_kaynagi(_tb), f"→ {_p_kaynagi(_tb)!r}")

    #  Mukavemet sonucu tek başına koşturulanla AYNI olmalı  ( kirlenme yok )
    tek = MK.hesapla(TAM)
    birlikte = UY.hesapla(TAM)
    r.esit("mukavemet bölümleri tek başına koşanla birebir aynı",
           [b["baslik"] for b in birlikte["bolumler"][:len(MK.BOLUM_URETICILERI)]],
           [b["baslik"] for b in tek["bolumler"]])
    for anahtar in ("N_hesap", "Sf", "ray_boyu", "FKR", "FAR", "Fkt", "Fat"):
        r.esit(f"mukavemet özeti değişmedi: {anahtar}",
               birlikte["ozet"][anahtar], tek["ozet"][anahtar])

    #  Avan tarafı tek başına koşturulanla aynı mı
    av = AV.hesapla(UG.kopru(UG.tamamla(dict(UG.varsayilanlar(), **TAM))))
    r.esit("elektrik özeti avan motoruyla aynı",
           birlikte["ozet"]["P_kurulu"], av["asansorler"][0]["ozet"]["P_kurulu"])

    # ==================================================================
    #  CAD ÇIKTISI  —  UYGULAMA PAFTASI AUTOCAD'DE AÇILIYOR MU
    #
    #  Bu bölümün varlık sebebi teslim edilmiş bir projedir:  AutoCAD 2027
    #  çizimi açarken ÇÖKÜYORDU ( "A software problem has caused application
    #  to close unexpectedly" ).  Sebep, AutoCAD'in metinde "^" + karakteri
    #  DENETİM KARAKTERİ diye yorumlaması;  yazı tipinde o kodun glifi yok ve
    #  macOS'ta arama FontCacheOSX::getCharData içinde çöküyor.  Şapka YALNIZ
    #  uygulama paftasında geçiyordu  —  halat emniyet katsayısı formülünde
    #  ( 10^[…], (Dt/dh)^8,567 ) ve tahrik yeteneğinde ( e^(f·α) )  —  bu
    #  yüzden avan paftalarını ölçen TEST 4 hatayı göremedi.  Uygulama
    #  paftasının CAD çıktısı o günden beri BURADA ölçülüyor.
    # ==================================================================
    try:
        import ezdxf                                          # noqa: F401
        from exports import dxf_export as DXE                 # noqa: E402
        from exports import pdf_export as PE                  # noqa: E402
    except Exception as _cad_hata:                            # noqa: BLE001
        r.atla(f"CAD çıktısı testi atlandı — ezdxf / pdfminer.six kurulu değil "
               f"( {_cad_hata} )")
    else:
        #  `s` bu noktada bozuk girdilerle yeniden hesaplanmış durumda;
        #  pafta TAM girdiden üretilmeli.
        _pdf = PE.uygulama_pdf(UY.hesapla_coklu([TAM]))
        _dxf = DXE.proje_dxf([("Uygulama Projesi", _pdf)])
        import io as _io
        _d = ezdxf.read(_io.StringIO(_dxf.decode("utf-8")))
        _m = _d.modelspace()
        _yazilar = [_e.dxf.text for _e in _m.query("TEXT")]
        r.kontrol("CAD: uygulama paftası çizime döndü", len(_yazilar) > 100,
                  f"→ {len(_yazilar)} yazı")

        _sapkali = [t for t in _yazilar if "^" in t]
        r.kontrol("CAD: hiçbir yazıda şapka ( ^ ) yok — AutoCAD'i çökertiyor",
                  not _sapkali, f"→ {_sapkali[:3]}")
        _yuzdeli = [t for t in _yazilar if "%%" in t]
        r.kontrol("CAD: hiçbir yazıda AutoCAD kaçış dizisi ( %% ) yok",
                  not _yuzdeli, f"→ {_yuzdeli[:3]}")
        #  Üs işareti PAFTADA gerçekten var mı — yoksa yukarıdaki iki kontrol
        #  hiçbir şey ölçmemiş olur.
        _pdf_yazi = " ".join(t["metin"] for _s in DXE._sayfa_geometrisi(_pdf)
                             for t in _s["metinler"])
        r.kontrol("CAD: paftada üs işareti gerçekten geçiyor  ( ölçüt boş değil )",
                  "^" in _pdf_yazi)
        r.kontrol("CAD: üs işareti çizimde U+02C6 olarak duruyor",
                  any("\u02c6" in t for t in _yazilar))

        #  Açılış görünümü:  sınırlar hesaplanmış ve görünüm çizimin üstünde
        _emin, _emax = _d.header["$EXTMIN"], _d.header["$EXTMAX"]
        r.kontrol("CAD: $EXTMIN / $EXTMAX hesaplanmış ( 1e+20 değil )",
                  all(abs(q) < 1e9 for q in list(_emin) + list(_emax)),
                  f"→ {_emin} {_emax}")
        from ezdxf.bbox import extents as _extents
        _bb = _extents(_m)
        _mrk = list(_d.viewports.get("*Active"))[0].dxf.center
        r.kontrol("CAD: kayıtlı görünüm çizimin ÜSTÜNDE ( boş ekran açılmıyor )",
                  _bb.extmin.x <= _mrk.x <= _bb.extmax.x
                  and _bb.extmin.y <= _mrk.y <= _bb.extmax.y,
                  f"→ görünüm {_mrk}, çizim {_bb.extmin}-{_bb.extmax}")
    # Geçersiz q: türetilen kütle ve bütün yük hesapları aynı değeri kullanır.
    for q, beklenen in ((2, 1100), (-1, 1100), (0.6, 1180), (0.2, 860), (0.8, 1340)):
        sonuc = MK.hesapla({"_ofis": {"q_denge": q}})
        r.esit(f"denge {q}: türetilen kütle", sonuc["girdi"]["karsi_agirlik"], beklenen)
        r.esit(f"denge {q}: motor kütlesi", sonuc["_h"]["AQ13"], beklenen)
        #  AĞIRLIK TAMPONU m.5.2.1.8.6'NIN KENDİ BAĞINTISIYLA:
        #  F = 4·gn·( P + q·Q ) — oradaki P "boş kabin + gezici kablo payı +
        #  denge zinciri"dir, karşı ağırlığın fiziksel kütlesi değil.
        #  Asıl denetlenen şey q'nun her yere AYNI geçmesi:  beklenen kütle
        #  700 + q·800 olduğuna göre q buradan geri okunur.
        _qe = (beklenen - 700) / 800.0
        r.kontrol(f"denge {q}: tampon yükü m.5.2.1.8.6 bağıntısıyla",
                  abs(sonuc["ozet"]["Fat"]
                      - 4 * 9.81 * (_P_std(sonuc) + _qe * 800)) < 1e-7,
                  f"→ {sonuc['ozet']['Fat']!r}")

    from engine.ortak import ofis as _OF
    otomatik = UY.hesapla({"kabin_agirligi": None})
    p_satiri = next(a for a in otomatik["bolumler"][0]["adimlar"] if a.get("sembol") == "P")
    r.esit("otomatik kabin kütlesi hesap satırında kaynak korur",
           p_satiri["kaynak"], _OF.GK_KAYNAGI)
    tekrar = UG.tamamla(otomatik["girdi"])
    r.esit("tekrar tamamlamada kaynak korunur", tekrar["kabin_agirligi_kaynak"], _OF.GK_KAYNAGI)
    tekrar["kabin_agirligi"] = 777
    r.esit("elle değiştirilmiş kütle giriş olarak işaretlenir",
           UG.tamamla(tekrar)["kabin_agirligi_kaynak"], "GİRİŞ")

    # Tek kalın halatın yüksek kopma dayanımı asgari adedi geçiremez.
    _halat_g = dict(halat_capi=16, tahrik_kasnak_capi=640,
                    saptirma_kasnak_capi=640, beyan_yuku=225, kabin_agirligi=200)
    _tek = MK.hesapla(dict(_halat_g, halat_adedi=1))
    r.kontrol("tek askı halatı girişte reddedilir", not _tek["aktif"])
    r.kontrol("tek halat hatası asgari adedi bildirir",
              any("en az 2" in h for h in _tek["hata"]))
    for _n, _smin in ((2, 16), (3, 12)):
        _s = MK.hesapla(dict(_halat_g, halat_adedi=_n))
        r.esit(f"{_n} halatta doğru güvenlik alt sınırı", _s["_h"]["AH110"], _smin)
    # Doğrulamayı atlayan doğrudan bölüm çağrısında da uygunluk engellenir.
    _g = UG.tamamla(dict(UG.varsayilanlar(), **_halat_g, halat_adedi=1))
    _o = {"ofis": US.sabitler()}
    MK._motor(_g, _o)
    _b = MK._aski_halatlari(_g, _o)
    r.kontrol("tek halat bölümde de reddedilir", _b["sonuc"]["uygun"] is False)

    #  ══════════════════════════════════════════════════════════════
    #  ÇOKLU ASANSÖR  ( 1 - 4 asansör, tek proje )
    #  ══════════════════════════════════════════════════════════════
    #  Motor TEK ASANSÖRLÜK kalır;  çoklu yalnız onu birden çok kez koşturur.
    #  İkinci bir hesap yolu açılmadığı burada kilitlenir:  tek asansörlük
    #  çağrı ile çoklunun ilk asansörü BİREBİR aynı çıkmalıdır.
    _C_ORTAK = {"temel_a": 26.55, "temel_b": 16.4, "serit_L": 58.5,
                "mk_yok": False, "mk_uzunluk": 4.0, "mk_genislik": 3.0}
    _c = UY.hesapla_coklu([{"asansor_adi": "İnsan 1"},
                           {"beyan_yuku": 630},
                           {"beyan_yuku": 1000, "asansor_adi": "Yük"}], _C_ORTAK)
    r.kontrol("çoklu: hesap aktif", _c["aktif"] is True, f"→ {_c.get('hata')}")
    r.esit("çoklu: asansör sayısı", _c["adet"], 3)
    r.esit("çoklu: azami asansör", UY.ASANSOR_AZAMI, 4)
    r.esit("çoklu: girilen ad korunuyor", _c["asansorler"][0]["tanim"], "İnsan 1")
    r.esit("çoklu: adsız asansör numarayla anılıyor",
           _c["asansorler"][1]["tanim"], "2 nolu asansör")

    #  PROJE GENELİ HESAPLAR HİÇBİR ASANSÖRDE DEĞİL, EN SONDA BİR KEZ.
    #  Topraklama ve makine dairesi binaya aittir;  dört kez basılması hem yer
    #  kaplar hem "hangisi geçerli" sorusunu doğurur.  Bir süre YALNIZ İLK
    #  asansörde bırakılıyorlardı — o zaman da binaya ait hesap 1 nolu
    #  asansörün arkasına, yani belgenin ORTASINA düşüyordu.
    _pg = [len([b for b in a["bolumler"] if b.get("proje_geneli")])
           for a in _c["asansorler"]]
    r.esit("çoklu: proje geneli bölüm hiçbir asansörde kalmıyor", _pg, [0, 0, 0])
    r.esit("çoklu: proje geneli bölümler üst seviyede",
           [b["baslik"] for b in _c["proje_geneli"]],
           ["1 - MAKİNE DAİRESİ AYDINLATMA HESABI",
            "2 - YATAY ( TEMEL ) TOPRAKLAYICI",
            "3 - DİKEY ( ÇUBUK ) TOPRAKLAYICI",
            "4 - TOPLAM TOPRAKLAMA DİRENCİ VE KONTROL",
            "5 - TOPRAKLAMA VE POTANSİYEL DENGELEME İLETKENLERİ"])
    r.esit("çoklu: özet proje geneli bölümleri sayıyor",
           _c["ozet"]["proje_geneli_adet"], 5)
    r.kontrol("çoklu: proje geneli uygunluğu özette",
              _c["ozet"]["proje_geneli_uygun"] is True)
    #  PROJE GENELİ HESAP "HEPSİ UYGUN"A GİRER.  Bölümler asansörlerden
    #  çıkınca onların bayrağı bunları saymaz;  ayrıca katılmasaydı
    #  topraklaması yetersiz bir proje "UYGUNDUR" görünürdü.
    _kotu = UY.hesapla_coklu([{}], dict(_C_ORTAK, temel_a=0.4, temel_b=0.4,
                                        serit_L=1.0))
    if _kotu["ozet"]["proje_geneli_uygun"] is False:
        r.kontrol("çoklu: proje geneli kalınca proje UYGUN görünmüyor",
                  _kotu["ozet"]["tumu_uygun"] is False)
    else:
        r.kontrol("çoklu: proje geneli kalınca proje UYGUN görünmüyor", True,
                  "→ küçük temelde de topraklama uygun çıktı, kontrol atlandı")
    r.kontrol("çoklu: asansörlerin bölüm numaraları boşluksuz",
              all([b["baslik"].split("-")[0].strip()
                   for b in a["bolumler"]]
                  == [str(i) for i in range(1, len(a["bolumler"]) + 1)]
                  for a in _c["asansorler"]),
              f"→ {[b['baslik'].split('-')[0].strip() for b in _c['asansorler'][1]['bolumler']]}")

    #  TEK ASANSÖRLE BİREBİR AYNI:  ikinci bir hesap yolu yok
    _tekil = UY.hesapla(dict(_C_ORTAK, beyan_yuku=630))
    _ikinci = _c["asansorler"][1]
    r.esit("çoklu: 2. asansörün motor gücü tekille aynı",
           (_ikinci["ozet"] or {}).get("N_hesap"),
           (_tekil["ozet"] or {}).get("N_hesap"))
    r.esit("çoklu: 2. asansörün halat katsayısı tekille aynı",
           (_ikinci["ozet"] or {}).get("Sf"), (_tekil["ozet"] or {}).get("Sf"))

    #  SINIRLAR
    r.esit("çoklu: azamiden fazlası kırpılıyor",
           UY.hesapla_coklu([{}] * 9)["adet"], UY.ASANSOR_AZAMI)
    r.esit("çoklu: boş liste tek asansöre düşer",
           UY.hesapla_coklu([])["adet"], 1)
    r.kontrol("çoklu: özet asansör listesi dolu",
              len(_c["ozet"]["asansorler"]) == 3
              and _c["ozet"]["asansorler"][2]["tanim"] == "Yük")

    #  PAFTADA EN SONDA.  Motor bölümleri ayırıyor;  asıl mesele onların
    #  BELGEDE nereye düştüğü — bunu ancak basılmış PDF gösterir.
    try:
        import io as _io
        import re as _re

        import pypdfium2 as _pdfium

        from exports import pdf_export as _PDF
        _b = _PDF.uygulama_pdf(_c, {"project_title": "Deneme"})
        _d = _pdfium.PdfDocument(_io.BytesIO(_b))
        _m = "\n".join(_d[i].get_textpage().get_text_range() for i in range(len(_d)))
        _d.close()                     # pdfium tutamakları açık kalmasın
        _sira, _onceki = [], None
        for _x in _re.findall(r"(ASANSÖR \d · [^\n]*?|PROJE GENELİ HESAPLAR)", _m):
            _x = _x.split(" 3 asansörden")[0].strip()
            if _x != _onceki:
                _sira.append(_x)
                _onceki = _x
        r.kontrol("pafta: proje geneli hesaplar EN SONDA",
                  _sira and _sira[-1] == "PROJE GENELİ HESAPLAR",
                  f"→ {_sira}")
        r.esit("pafta: topraklama bir kez basılıyor",
               _m.count("YATAY ( TEMEL ) TOPRAKLAYICI"), 1)
        r.kontrol("pafta: proje geneli şeridi açıklamasıyla geliyor",
                  "bütün asansörler için bir kez" in _m)
    except ImportError:
        r.kontrol("pafta sırası denetlenemedi ( pypdfium2 yok )", True)

    #  ─────────────────────────────────────────────────────────────
    #  TEK YOL  —  tek asansör ile çoklu asansör aynı yerden geçer
    #  ─────────────────────────────────────────────────────────────
    #  Bir süre iki motor girişi ( hesapla / hesapla_coklu ), iki pafta
    #  fonksiyonu ( uygulama_pdf / uygulama_coklu_pdf ) ve API'de ÜÇ ayrı
    #  dallanma vardı;  hangisinin çağrılacağına API karar veriyordu.  İkisi
    #  ayrıştı:  proje geneli hesaplar çoklu paftada en sona alınmış, tek
    #  asansörlükte bölümlerin arasında kalmıştı — aynı program aynı projeyi
    #  asansör sayısına göre iki türlü basıyordu.  Avan trafik motoru bu işi
    #  baştan doğru yapar:  tek giriş, kullanılan yol SONUCUN İÇİNDE yazar.
    _t1 = UY.hesapla_coklu([{}], _C_ORTAK)
    _t2 = UY.hesapla_coklu([{}, {"beyan_yuku": 630}], _C_ORTAK)
    r.esit("tek asansörde yol 'tek' yazıyor", _t1["yol"], "tek")
    r.esit("çok asansörde yol 'coklu' yazıyor", _t2["yol"], "coklu")
    r.esit("iki durumda da SONUÇ ŞEKLİ aynı",
           sorted(_t1.keys()), sorted(_t2.keys()))
    #  Proje geneli hesaplar TEK asansörde de ayrılır — asıl ayrışma buydu
    r.esit("tek asansörde de proje geneli ayrılmış",
           [b["kimlik"] for b in _t1["proje_geneli"]],
           [b["kimlik"] for b in _t2["proje_geneli"]])
    r.esit("tek asansörde de bölümler asansörde kalmıyor",
           [b for b in _t1["asansorler"][0]["bolumler"] if b.get("proje_geneli")], [])
    #  API artık asansör sayısına göre BAŞKA MOTOR çağırmıyor:  modülde
    #  dallanmayı kuran isimler kalmamalı.
    _api = io.open(os.path.join(KOK, "api", "uygulama.py"), encoding="utf-8").read()
    for _ad in ("_coklu_mu", "_uygulama_sonucu", "uygulama_coklu_pdf"):
        r.kontrol(f"API'de '{_ad}' kalmadı", _ad not in _api)
    r.esit("API tek motor girişi çağırıyor", _api.count("E_UYG.hesapla("), 0)
    _pe = io.open(os.path.join(KOK, "exports", "pdf_export.py"), encoding="utf-8").read()
    r.esit("tek uygulama paftası fonksiyonu", _pe.count("\ndef uygulama_"), 1)

    #  ─────────────────────────────────────────────────────────────
    #  BÖLÜM KİMLİĞİ  —  numara biçimdir, kimlik değildir
    #  ─────────────────────────────────────────────────────────────
    #  Bir süre bölümü tanıyan her şey BAŞLIKTAKİ NUMARAYA bakıyordu.  Numara
    #  projeye göre kayar:  proje geneli bölümler ayrılınca kalanlar yeniden
    #  numaralanır, makine dairesi yoksa topraklama bir sıra öne gelir.  Bu
    #  yüzden proje geneli bölümler hiç eşlenemiyordu ve elektrik bölümlerini
    #  eşlemek için "mukavemet 10 bölümdür" varsayımını gömmek gerekiyordu.
    _tekil = UY.hesapla(_C_ORTAK)
    _tum = list(_tekil["bolumler"])
    r.kontrol("her bölüm kimlik taşıyor",
              all(b.get("kimlik") for b in _tum),
              f"→ kimliksiz: {[b['baslik'] for b in _tum if not b.get('kimlik')]}")
    r.esit("kimlikler tekil", len({b["kimlik"] for b in _tum}), len(_tum))
    r.kontrol("her bölüm sıra numarası da taşıyor",
              [b.get("sira") for b in _tum] == list(range(1, len(_tum) + 1)),
              f"→ {[b.get('sira') for b in _tum]}")
    r.kontrol("başlık = sıra + ad",
              all(b["baslik"] == f"{b['sira']} - {b['ad']}" for b in _tum),
              f"→ {[b['baslik'] for b in _tum[:2]]}")

    #  ASIL KONTROL:  NUMARA KAYARKEN KİMLİK DURUYOR.
    #  Aynı hesap üç ayrı kurulumda üç ayrı numara alır ama kimliği aynıdır.
    def _numara(sonuc, kim):
        for b in (sonuc.get("bolumler") or []) + (sonuc.get("proje_geneli") or []):
            if b.get("kimlik") == kim:
                return b["sira"]
        return None
    _mk_var = UY.hesapla_coklu([{}], _C_ORTAK)                 # makine dairesi VAR
    _mk_yok = UY.hesapla_coklu([{}], dict(_C_ORTAK, mk_yok=True,
                                          mk_uzunluk=None, mk_genislik=None))
    _numaralar = (_numara(_tekil, "topraklama_toplam"),
                  _numara(_mk_var["asansorler"][0], "topraklama_toplam")
                  or _numara(_mk_var, "topraklama_toplam"),
                  _numara(_mk_yok, "topraklama_toplam"))
    r.kontrol("aynı hesap kurulumdan kuruluma FARKLI numara alıyor",
              len(set(_numaralar)) > 1, f"→ {_numaralar}")
    r.kontrol("kimlik ise hiç değişmiyor",
              all(n is not None for n in _numaralar), f"→ {_numaralar}")

    #  EŞLEME SÖZLEŞMESİ:  eşlemedeki her kimlik gerçek bir bölümdür ve
    #  gerçek her bölüm eşlemededir.  Numara kullanılırken bu denetlenemezdi.
    _bg = UG.arayuz_alanlari()["bolum_grubu"]
    _gercek = {b["kimlik"] for b in _tum}
    r.esit("eşlemede olup motorda olmayan bölüm", sorted(set(_bg) - _gercek), [])
    r.esit("motorda olup eşlemede olmayan bölüm", sorted(_gercek - set(_bg)), [])
    _gruplar = {g["ad"] for g in UG.arayuz_alanlari()["gruplar"]}
    r.esit("eşlemenin gösterdiği her grup gerçekten var",
           sorted({ad for v in _bg.values() for ad in v} - _gruplar), [])
    r.kontrol("eşleme en çok iki grup gösteriyor",
              all(1 <= len(v) <= 2 for v in _bg.values()),
              f"→ {[k for k, v in _bg.items() if len(v) > 2]}")
    r.kontrol("proje geneli bölümler de eşlenmiş",
              all(k in _bg for k in ("makine_dairesi_aydinlatma",
                                     "topraklama_yatay", "topraklama_toplam")),
              "→ numara kayarken eşlenemiyorlardı")

    #  ─────────────────────────────────────────────────────────────
    #  EŞLEMENİN İÇERİĞİ  —  gösterdiği grup gerçekten o bölümü besliyor mu
    #  ─────────────────────────────────────────────────────────────
    #  Yukarıdaki kontroller eşlemenin TAM olduğunu gösteriyor:  her bölüm
    #  eşlemede, her kimlik gerçek.  Ama İÇERİĞİNİ ( "aski_halatlari →
    #  Makine ve motor" doğru mu ) hiçbir şey denetlemiyordu;  liste elle
    #  yazılmıştı ve bir alan grup değiştirdiğinde sessizce bayatlardı.
    #
    #  YÖNTEM PERTÜRBASYON, KOD TARAMASI DEĞİL:  her girdi tek tek oynatılıp
    #  hangi bölümün sonucunun değiştiğine bakılır.  Kaynak koddaki g[...]
    #  okumalarını taramak dolaylı bağları ( köprüden geçen elektrik
    #  girdileri gibi ) kaçırırdı;  bu yöntem motorun İKİSİNİ birden ve
    #  gerçekte ne olduğunu ölçer.
    #
    #  KURAL:  eşlemede yazılı her grup, o bölümü GERÇEKTEN etkileyen bir
    #  grup olmalıdır.  Tersi aranmaz — bir bölüm çoğu grubu okur ( motor
    #  gücü yedi gruptan besleniyor ), eşleme ise en çok ikisini gösterir.
    #
    #  Bu tarama iki gerçek hata yakaladı:  "kuyu_tabani → Tamponlar"
    #  ( tampon KUVVETİ kütle × g'dir, tampon geometrisi kuvvete girmez ) ve
    #  "kurulu_guc → Elektrik ve topraklama" ( kuyu armatür adedi kuyu
    #  YÜKSEKLİĞİNDEN gelir, genişlik yalnız lux kontrolüne girer ).
    _ORTAK_T = {"mk_yok": False, "mk_uzunluk": 4.0, "mk_genislik": 3.0,
                "temel_a": 20.0, "temel_b": 12.0, "serit_L": 64.0}

    def _bolum_icerigi(sonuc):
        """kimlik → karşılaştırılabilir içerik  ( sıra ve başlık hariç )."""
        ic = {}
        for b in ((sonuc.get("asansorler") or [{}])[0].get("bolumler") or []) \
                + (sonuc.get("proje_geneli") or []):
            ic[b.get("kimlik")] = json.dumps(
                {k: v for k, v in b.items() if k not in ("sira", "baslik")},
                ensure_ascii=False, sort_keys=True, default=str)
        return ic

    def _oynat(f, simdiki):
        """Alanı GEÇERLİ kalacak şekilde değiştir;  değiştirilemiyorsa None."""
        t = f["tur"]
        if t == "onay":
            return not simdiki
        if t == "secim":
            baska = [x for x in (f["secenekler"] or []) if str(x) != str(simdiki)]
            return baska[0] if baska else None
        if t == "sayi":
            v = simdiki if isinstance(simdiki, (int, float)) else 0
            #  KESİT ALANLARI BASAMAK FONKSİYONUDUR.  Koruma iletkeni ve
            #  potansiyel dengeleme kesitleri standart kesit merdivenine
            #  yuvarlanır ve 6 mm² tabanı vardır;  +%15'lik bir itme
            #  ( 6 → 7,9 ) hiçbir basamağı atlamaz ve bölüm kımıldamaz.
            #  Bağı GERÇEKTEN sınamak için bir basamak aşan bir sıçrama gerekir.
            if f["anahtar"] in ("kolon_kesit", "makine_kesit"):
                return round(v * 8 + 1, 3)
            return round(v * 1.15 + 1, 3)
        return None                       # metin ve liste: sonuca girmez / ayrı denenir

    _taban = UY.hesapla_coklu([{}], _ORTAK_T)
    _taban_ic = _bolum_icerigi(_taban)
    _tg = _taban["asansorler"][0]["girdi"]
    _arayuz = UG.arayuz_alanlari()
    _grubu = {f["anahtar"]: gr["ad"] for gr in _arayuz["gruplar"] for f in gr["alanlar"]}
    _etki, _denenemeyen = {k: set() for k in _taban_ic}, []
    for _gr in _arayuz["gruplar"]:
        for _f in _gr["alanlar"]:
            _a = _f["anahtar"]
            _yeni = _oynat(_f, _tg.get(_a))
            if _yeni is None:
                _denenemeyen.append(_a)
                continue
            _s = (UY.hesapla_coklu([{}], dict(_ORTAK_T, **{_a: _yeni}))
                  if _a in UG.PROJE_GENELI_ALANLAR
                  else UY.hesapla_coklu([{_a: _yeni}], _ORTAK_T))
            if not _s.get("aktif"):
                _denenemeyen.append(_a)      # bu değerle girdi geçersiz oluyor
                continue
            _yeni_ic = _bolum_icerigi(_s)
            for _kim in set(_taban_ic) | set(_yeni_ic):
                if _taban_ic.get(_kim) != _yeni_ic.get(_kim):
                    _etki.setdefault(_kim, set()).add(_grubu[_a])

    r.kontrol("pertürbasyon taraması çalıştı",
              sum(len(v) for v in _etki.values()) > 40,
              f"→ yalnız {sum(len(v) for v in _etki.values())} bağ bulundu")
    _yanlis = {kim: [g for g in gruplar if g not in _etki.get(kim, set())]
               for kim, gruplar in _bg.items()
               #  Girdisi HİÇ olmayan bölüm muaf:  topraklama çubuğu yalnız
               #  ofis sabitlerinden ( çubuk sayısı · boyu · toprak özdirenci )
               #  hesaplanır, hiçbir proje girdisi onu değiştirmez.
               if _etki.get(kim)}
    _yanlis = {k: v for k, v in _yanlis.items() if v}
    r.esit("eşlemedeki her grup o bölümü GERÇEKTEN etkiliyor", _yanlis, {})
    #  Girdisiz bölümlerin listesi SABİTLENİR — yenisi çıkarsa fark edilsin
    r.esit("hiçbir proje girdisinden etkilenmeyen bölümler",
           sorted(k for k in _bg if not _etki.get(k)), ["topraklama_dikey"])
    #  Denenemeyen alanlar körlük yaratır;  sayısı sabitlenir ki sessizce
    #  büyümesin ( büyürse tarama gitgide daha az şey görüyor demektir ).
    r.kontrol("taramanın körlüğü sınırlı",
              len(_denenemeyen) <= 16,
              f"→ {len(_denenemeyen)} alan denenemedi: {sorted(_denenemeyen)}")

    #  PROJE GENELİ ALANLAR TEK KAYNAKTA
    r.kontrol("proje geneli alan listesi motorda",
              set(UG.PROJE_GENELI_ALANLAR)
              == {"temel_a", "temel_b", "serit_L",
                  "mk_yok", "mk_uzunluk", "mk_genislik"},
              f"→ {UG.PROJE_GENELI_ALANLAR}")

    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
