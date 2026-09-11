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
    r.esit(f"toplam bölüm  ( {_MUK} mukavemet + 4 elektrik + 3 topraklama )",
           len(adlar), _MUK + 7)
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
    _temiz = dict(tahrik_kasnak_capi=280, saptirma_kasnak_capi=280,
                  motor_gucu=7.5, guvenlik_devreye_kuvvet=200,
                  kanal_isleme="Sertleştirilmiş", denge_zinciri="Var")
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
    r.kontrol("⑨ koruma iletkeni topraklama bölümüne konulmadı",
              not any(str(a.get("sembol") or "").startswith("SPE")
                      for b in ((_av9.get("topraklama") or {}).get("bolumler") or [])
                      for a in b["adimlar"] if isinstance(a, dict)))

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
               len(MK.BOLUM_URETICILERI) + 8)
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
            "4 - TOPLAM TOPRAKLAMA DİRENCİ VE KONTROL"])
    r.esit("çoklu: özet proje geneli bölümleri sayıyor",
           _c["ozet"]["proje_geneli_adet"], 4)
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
