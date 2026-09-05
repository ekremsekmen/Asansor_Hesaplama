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
        r.esit("taşan sigortada güç değeri bozulmadı", _c["guc"], 400_000)

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
