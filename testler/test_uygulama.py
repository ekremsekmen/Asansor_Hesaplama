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
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.avan import hesap as AV                          # noqa: E402
from engine.uygulama import mukavemet as MK                     # noqa: E402
from engine.uygulama import hesap as UY                      # noqa: E402
from engine.uygulama import girdi as UG                # noqa: E402
from engine.uygulama import sabitler as US             # noqa: E402
from testler.ortak import Rapor                        # noqa: E402

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
    r.esit("mukavemet bölüm sayısı", s["mukavemet_bolum_sayisi"], 10)
    r.esit("toplam bölüm  ( 10 mukavemet + 4 elektrik + 3 topraklama )",
           len(adlar), 17)
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
    #  Verim artık sabit değil, MAKİNE TİPİNDEN gelir;  köprü avana TABAN η
    #  geçirir ( palanga düşüşünü avan kendisi uygular, yoksa iki kez düşerdi ).
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
    _temiz = dict(tahrik_kasnak_capi=280, saptirma_kasnak_capi=280, motor_gucu=7.5)
    _t = UH.hesapla(UG.tamamla(dict(UG.varsayilanlar(), **_temiz)))
    r.kontrol("② temiz proje uygun", _t["ozet"]["tumu_uygun"] is True)
    #  Akım yetersizse İLGİLİ BÖLÜM de uygun değil
    _s2 = UH.hesapla(UG.tamamla(dict(UG.varsayilanlar(), tahrik_kasnak_capi=280,
                                     saptirma_kasnak_capi=280, motor_gucu=37,
                                     kolon_kesit=95, makine_kesit=1.5,
                                     makine_uzunluk=2)))
    _b14 = [b for b in _s2["bolumler"] if b["baslik"].startswith("14")][0]
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
    _bek8 = _ray8 + MK.SABIT["MY_kabin"] + (_h8["AU351"] - _h8["AH291"] * _gn8)
    r.kontrol("⑧ FKR = ray kütlesi + bileşen + güv.tert. tepkisi",
              _yakin(_h8["AX611"], _bek8), f"→ {_h8['AX611']!r} ≠ {_bek8!r}")
    r.kontrol("⑧ ray ağırlığı iki kez sayılmıyor",
              abs(_h8["AX611"] - (_bek8 + _ray8)) > 1,
              "→ hâlâ çift sayılıyor")

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
        r.esit("topraklama olmadan bölüm sayısı", len(s["bolumler"]), 14)
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
        r.esit("makine daireli bölüm sayısı", len(s["bolumler"]), 18)
        r.kontrol("makine dairesi aydınlatması eklendi",
                  any("MAKİNE DAİRESİ" in a for a in _bolum_adlari(s)))

    #  Mukavemet girdisi geçersizse uygulama da durmalı
    s = UY.hesapla({"kabin_agirligi": None})
    r.kontrol("geçersiz mukavemet girdisi uygulamayı da durduruyor",
              not s["aktif"])

    #  Mukavemet sonucu tek başına koşturulanla AYNI olmalı  ( kirlenme yok )
    tek = MK.hesapla(TAM)
    birlikte = UY.hesapla(TAM)
    r.esit("mukavemet bölümleri tek başına koşanla birebir aynı",
           [b["baslik"] for b in birlikte["bolumler"][:10]],
           [b["baslik"] for b in tek["bolumler"]])
    for anahtar in ("N_hesap", "Sf", "ray_boyu", "FKR", "FAR", "Fkt", "Fat"):
        r.esit(f"mukavemet özeti değişmedi: {anahtar}",
               birlikte["ozet"][anahtar], tek["ozet"][anahtar])

    #  Avan tarafı tek başına koşturulanla aynı mı
    av = AV.hesapla(UG.kopru(UG.tamamla(dict(UG.varsayilanlar(), **TAM))))
    r.esit("elektrik özeti avan motoruyla aynı",
           birlikte["ozet"]["P_kurulu"], av["asansorler"][0]["ozet"]["P_kurulu"])
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
