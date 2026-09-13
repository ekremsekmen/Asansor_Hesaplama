# -*- coding: utf-8 -*-
"""
TEST 6  —  EXCEL'DEN GERİ YÜKLEME  (revizyon akışı)

Programın ürettiği XLSX girdileri de taşır.  Bu test, gidiş-dönüşün
kayıpsız olduğunu doğrular:

    girdiler  →  XLSX  →  geri okuma  →  AYNI girdiler

Böylece revizyonda proje klasöründeki Excel'i yükleyip yalnız değişen
değeri düzeltmek yeterlidir; hiçbir girdi kaybolmaz.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.avan import hesap as AV
from engine.uygulama import mukavemet_tablolari as MT   # noqa: E402
from exports import hucre_haritasi as H          # noqa: E402
from exports import xlsx_export as XE            # noqa: E402
from exports import xlsx_import as XI            # noqa: E402
from testler.ortak import Rapor                  # noqa: E402
from testler.test_excel_uyumu import (avan_senaryolar, coklu_senaryolar,   # noqa: E402
                                      tek_senaryolar)

PROJE = {"proje_adi": "Yıldız Konutları A Blok", "isveren": "ÇAĞDAŞ İnşaat A.Ş.",
         "pafta_no": "EL-04", "tarih": "27.08.2026", "muhendis": "Ekrem Sekmen"}


def _bekle_alan(anahtar, x):
    """
    Alan adını bilerek bekleneni üretir.  Evet/Hayır kutuları Excel'de METİN
    olarak durur ama geri okumada MANTIKSAL değere çevrilir — bu yüzden onlar
    için metin değil True/False beklenir.
    """
    if H.evet_hayir_mi(anahtar):
        return H.evet_mi(x)
    return _bekle(x)


def _bekle(x):
    """Girdiyi, geri okumanın üreteceği metin biçimine çevirir."""
    if x is None or x == "":
        return ""
    if isinstance(x, bool):
        return ""
    if isinstance(x, int):
        return str(x)
    if isinstance(x, float):
        if float(x).is_integer():
            return str(int(x))
        return ("%.6f" % x).rstrip("0").rstrip(".").replace(".", ",")
    return str(x).strip()


def calistir():
    print("\n\033[1mTEST 6 — EXCEL'DEN GERİ YÜKLEME (revizyon akışı)\033[0m")
    r = Rapor("Geri yükleme")

    # ---------------------------------------------------------- TEK TRAFİK
    for ad, g in tek_senaryolar():
        d = XI.xlsx_oku(XE.trafik_xlsx("tek", g, PROJE))
        r.esit(f"[tek] {ad} · tür", d["tur"], "tek")
        #  Arayüzde ayrı "tek hesap" gövdesi kalmadı: TEK sayfasının girdileri
        #  tek forma yüklenir — bina alanları c_*, asansöre ait olanlar 1.
        #  kolona.  manuel_adet'in karşılığı yok ( adet = kolon sayısı ).
        for anahtar in H.TEK:
            alan = H.tek_alan(anahtar)
            if alan is None:
                continue
            r.esit(f"[tek] {ad} · {anahtar}",
                   d["alanlar"].get(alan), _bekle(g.get(anahtar)))
        beklenen_ek = [s for s in (g.get("ek_nufus") or []) if s.get("kalem")]
        r.esit(f"[tek] {ad} · ek nüfus satır sayısı",
               len(d.get("ek_nufus") or []), len(beklenen_ek))
        for i, s in enumerate(beklenen_ek):
            okunan = (d.get("ek_nufus") or [])[i]
            r.esit(f"[tek] {ad} · ek nüfus {i} kalem", okunan["kalem"], s["kalem"])
            r.esit(f"[tek] {ad} · ek nüfus {i} miktar", okunan["miktar"], _bekle(s["miktar"]))

    # ---------------------------------------------------------- ÇOKLU TRAFİK
    for ad, g in coklu_senaryolar():
        d = XI.xlsx_oku(XE.trafik_xlsx("coklu", g, PROJE))
        r.esit(f"[çoklu] {ad} · tür", d["tur"], "coklu")
        for anahtar in H.COKLU_ORTAK:
            r.esit(f"[çoklu] {ad} · {anahtar}",
                   d["alanlar"].get(H.coklu_ortak_alan(anahtar)), _bekle(g.get(anahtar)))
        for i, a in enumerate((g.get("asansorler") or [])[:4], start=1):
            for anahtar in H.COKLU_ASANSOR.values():
                r.esit(f"[çoklu] {ad} · A{i}.{anahtar}",
                       d["alanlar"].get(H.coklu_asansor_alan(anahtar, i)),
                       _bekle(a.get(anahtar)))
        # kullanılmayan kolonlar boş dönmeli
        for i in range(len(g.get("asansorler") or []) + 1, 5):
            r.esit(f"[çoklu] {ad} · A{i} boş",
                   d["alanlar"].get(H.coklu_asansor_alan("P", i)), "")

    # ---------------------------------------------------------- AVAN
    for ad, v in avan_senaryolar():
        d = XI.xlsx_oku(XE.avan_xlsx(v, PROJE))
        r.esit(f"[avan] {ad} · tür", d["tur"], "avan")
        #  Dosyaya ÇÖZÜLMÜŞ girdi yazılır: boş bırakılan ofis varsayılanları ve
        #  otomatik seçilen Nsç / L1 hücrelere açıkça konur ki Excel kendi
        #  başına aynı sonucu versin.  Beklenen değer de bu yüzden çözülmüş
        #  girdidir — dosyada boş hücre kalmamalıdır.
        c = AV.girdileri_coz(v)
        for anahtar in H.AVAN_ORTAK:
            beklenen = c["ortak"].get(anahtar)
            if anahtar in ("mk_uzunluk", "mk_genislik"):
                beklenen = beklenen or 0
            r.esit(f"[avan] {ad} · {anahtar}",
                   d["alanlar"].get(H.avan_ortak_alan(anahtar)),
                   _bekle_alan(anahtar, beklenen))
        for i, a in enumerate((c.get("asansorler") or [])[:4], start=1):
            for anahtar in H.AVAN_ASANSOR.values():
                r.esit(f"[avan] {ad} · A{i}.{anahtar}",
                       d["alanlar"].get(H.avan_asansor_alan(anahtar, i)),
                       _bekle_alan(anahtar, a.get(anahtar)))
            r.kontrol(f"[avan] {ad} · A{i} etkin işaretlendi",
                      d["alanlar"].get(f"a_aktif{i}") is True)
        for i in range(len(v.get("asansorler") or []) + 1, 5):
            r.kontrol(f"[avan] {ad} · A{i} etkin değil",
                      d["alanlar"].get(f"a_aktif{i}") is False)
        # Ofis standardı ( SABİTLER sayfasında hücresi olanlar ) geri gelmeli.
        # C ) OFİS VARSAYILANLARI'nın SABİTLER'de hücresi YOKTUR — etkileri
        # GİRİŞ hücrelerine yazılır ve yukarıdaki döngülerde zaten sınanır.
        for anahtar, deger in (v.get("sabitler") or {}).items():
            if anahtar not in H.AVAN_SABIT:
                continue
            alan = H.sabit_alan(anahtar)
            r.esit(f"[avan] {ad} · sabit {anahtar}", d["alanlar"].get(alan), _bekle(deger))

    # ---------------------------------------------------------- proje antedi
    for etiket, icerik in (("tek", XE.trafik_xlsx("tek", tek_senaryolar()[0][1], PROJE)),
                           ("çoklu", XE.trafik_xlsx("coklu", coklu_senaryolar()[0][1], PROJE)),
                           ("avan", XE.avan_xlsx(avan_senaryolar()[0][1], PROJE))):
        p = XI.xlsx_oku(icerik)["proje"]
        for anahtar, deger in PROJE.items():
            r.esit(f"[{etiket}] proje.{anahtar}", p.get(anahtar), deger)
    # proje bilgisi verilmezse boş dönmeli, çökmemeli
    p = XI.xlsx_oku(XE.trafik_xlsx("tek", tek_senaryolar()[0][1], None))["proje"]
    r.kontrol("projesiz dosyada ad boş", p.get("proje_adi") in ("", None))

    # ---------------------------------------------------------- revizyon senaryosu
    # Excel'de ELLE değiştirilmiş bir girdi de geri okunmalı.
    import io
    import openpyxl
    g = dict(tek_senaryolar()[0][1])
    ham = XE.trafik_xlsx("tek", g, PROJE)
    wb = openpyxl.load_workbook(io.BytesIO(ham))
    wb[H.TEK_SAYFA][H.TEK["N"]] = 17                 # mühendis Excel'de kat ekledi
    wb[H.TEK_SAYFA][H.TEK["kapi_genisligi"]] = 1100  # ve kapıyı büyüttü
    buf = io.BytesIO(); wb.save(buf)
    d = XI.xlsx_oku(buf.getvalue())
    r.esit("elle değiştirilen N okundu", d["alanlar"]["c_N"], "17")
    r.esit("elle değiştirilen kapı okundu", d["alanlar"]["c_kg1"], "1100")

    # ---------------------------------------------------------- hatalı dosyalar
    for ad, icerik in (("boş", b""), ("metin", b"bu bir excel degil"),
                       ("bozuk zip", b"PK\x03\x04bozuk")):
        hata = False
        try:
            XI.xlsx_oku(icerik)
        except XI.YuklemeHatasi:
            hata = True
        except Exception:                                    # noqa: BLE001
            hata = True
        r.kontrol(f"{ad} dosya anlaşılır şekilde reddedildi", hata)
    # bizim olmayan geçerli bir xlsx
    yb = openpyxl.Workbook(); yb.active["A1"] = "başka bir tablo"
    buf = io.BytesIO(); yb.save(buf)
    hata_metni = ""
    try:
        XI.xlsx_oku(buf.getvalue())
    except XI.YuklemeHatasi as e:
        hata_metni = str(e)
    r.kontrol("ilgisiz Excel açıklayıcı hata veriyor",
              "hesap dosyas" in hata_metni, f"→ {hata_metni[:60]!r}")

    # ---------------------------------------------------------- ondalıklı değerler
    # Açılır liste değerleri (hız, kesit) ondalıklı olabilir; geri okumada
    # bu değerlerin kaybolmaması gerekir.
    ORT = {"U": 380, "kappa": 56, "eps_max": 3, "temel_a": 26.55, "temel_b": 16.4,
           "beta": 150, "serit_L": 58.5, "cubuk_sayisi": 4,
           "mk_uzunluk": 0, "mk_genislik": 0}
    for V, S1, S2 in ((1.6, 1.5, 2.5), (2.5, 4, 6), (0.63, 2.5, 1.5),
                      (1.75, 10, 16), (3.5, 25, 35)):
        a = {"tanim": "A", "kapasite": 10, "V": V, "eta": 0.85, "Hk": 32.85,
             "kuyu_genisligi": 1800, "kabin_boyu": 1450, "kabin_genisligi": 1300,
             "gr": 17.91, "Fmk": 350, "Fsh": 100, "Nsc": 11, "S1": S1,
             "L1": 32.85, "S2": S2, "L2": 3, "kablo_tipi": "X"}
        d = XI.xlsx_oku(XE.avan_xlsx({"ortak": ORT, "asansorler": [a]}, PROJE))
        r.esit(f"ondalıklı V={V} geri geldi", d["alanlar"]["a_V1"], _bekle(V))
        r.esit(f"ondalıklı S1={S1} geri geldi", d["alanlar"]["a_S11"], _bekle(S1))
        r.esit(f"ondalıklı S2={S2} geri geldi", d["alanlar"]["a_S21"], _bekle(S2))
    for V in (0.63, 1.6, 1.75, 2.5, 3.5, 6):
        g = dict(tek_senaryolar()[0][1], manuel_V=V)
        d = XI.xlsx_oku(XE.trafik_xlsx("tek", g, PROJE))
        r.esit(f"trafik manuel V={V} geri geldi", d["alanlar"]["c_manuel_V"], _bekle(V))

    # ---------------------------------------------------------- ikinci tur
    # Geri yüklenen girdilerle yeniden üretilen dosya, tekrar yüklenince
    # aynı sonucu vermeli (revizyon zinciri kapalı olmalı).
    g0 = tek_senaryolar()[0][1]
    d1 = XI.xlsx_oku(XE.trafik_xlsx("tek", g0, PROJE))
    g1 = {a: d1["alanlar"][H.tek_alan(a)] for a in H.TEK if H.tek_alan(a)}
    g1["ek_nufus"] = d1.get("ek_nufus") or []
    d2 = XI.xlsx_oku(XE.trafik_xlsx("tek", g1, PROJE))
    r.kontrol("ikinci tur aynı girdileri veriyor", d1["alanlar"] == d2["alanlar"])


    # ==================================================================
    #  v2.9 — GERİ YÜKLEMEDE VERİ KAYBI
    #  Bu üç kontrol, gidiş-dönüşün "aynı alanlar" olmasının YETMEDİĞİNİ
    #  gösteriyor:  alan adı arayüzde YOKSA değer hiçbir yere yazılamaz.
    # ==================================================================
    #  1) Elektrik / topraklama değerleri:  bu alanlar avan panelinden
    #     "Sabitler / Ofis Standardı" sekmesine taşındı ( of_<ad> ), harita
    #     hâlâ a_<ad> üretiyordu.  Dosyada U = 220 V yazsa bile geri yüklemede
    #     ofis varsayılanı ( 380 V ) devreye giriyor, ε %4,69 "UYGUN DEĞİL"
    #     iken %0,98 "UYGUN" oluyordu — uygunluk kararı TERSİNE dönüyordu.
    _av = {"ortak": {"U": 220, "kappa": 35, "eps_max": 2, "temel_a": 26.55,
                     "temel_b": 16.4, "beta": 300, "cubuk_sayisi": 8, "mk_yok": True},
           "asansorler": [{"tanim": "A", "kapasite": 10, "V": 1.6, "eta": 0.85,
                           "Hk": 32.85, "kuyu_genisligi": 1800, "kabin_boyu": 1450,
                           "kabin_genisligi": 1300, "makine_tipi": "Dişlisiz"}],
           "sabitler": {}}
    _al = XI.xlsx_oku(XE.avan_xlsx(_av, PROJE))["alanlar"]
    for _k, _bek in (("U", "220"), ("kappa", "35"), ("eps_max", "2"),
                     ("beta", "300"), ("cubuk_sayisi", "8")):
        r.esit(f"ofis alanı of_{_k} geri geliyor", _al.get("of_" + _k), _bek)
        r.kontrol(f"{_k} artık a_ alanına yazılmıyor", ("a_" + _k) not in _al)
    #  Aynı değerlerle hesap DEĞİŞMEMELİ
    _sabit = {_k: float(str(_al["of_" + _k]).replace(",", "."))
              for _k in ("U", "kappa", "eps_max", "beta", "cubuk_sayisi")}
    _o1 = AV.hesapla(_av)
    _o2 = AV.hesapla({"ortak": {"temel_a": 26.55, "temel_b": 16.4, "mk_yok": True},
                      "asansorler": _av["asansorler"], "sabitler": _sabit})
    r.esit("geri yüklemede ε değişmiyor",
           round(_o2["asansorler"][0]["ozet"]["eps"], 6),
           round(_o1["asansorler"][0]["ozet"]["eps"], 6))
    r.esit("geri yüklemede uygunluk kararı değişmiyor",
           _o2["asansorler"][0]["ozet"]["eps_uygun"], _o1["asansorler"][0]["ozet"]["eps_uygun"])
    r.esit("geri yüklemede Re değişmiyor",
           round(_o2["ozet"]["Re"], 6), round(_o1["ozet"]["Re"], 6))

    #  2) Özdeş grup adedi:  HESAPLAMA sayfası ortak değerleri TEK kolonda
    #     tutar, adet ayrı hücrededir.  Adet okunmadığı için 4 asansörlük
    #     proje tek kolona düşüyor, sonuç "4 adet uygun değil"den
    #     "11 adet gerekir"e kayıyordu.
    _gt = {"bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
           "N": 11, "h": 3, "hizli1": 300, "hizli2": 3, "P": 10,
           "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik", "manuel_adet": 4}
    _d = XI.xlsx_oku(XE.trafik_xlsx("tek", _gt, PROJE))
    r.esit("grup adedi geri geliyor", _d["alanlar"].get("__trafik_adet"), 4)
    for _i in range(1, 5):
        r.esit(f"özdeş kolon {_i} dolduruluyor",
               _d["alanlar"].get(f"c_P{_i}"), "10")
    _tek = XI.xlsx_oku(XE.trafik_xlsx("tek", dict(_gt, manuel_adet=None), PROJE))
    r.esit("tek asansörde adet 1", _tek["alanlar"].get("__trafik_adet"), 1)
    r.kontrol("tek asansörde 2. kolon boş kalıyor",
              not _tek["alanlar"].get("c_P2"))

    #  3) Proje kimliği:  yalnız `proje` altında dönüyor, arayüz kullanmıyordu;
    #     yeni dosya açılınca ÖNCEKİ projenin adı kapakta kalıyordu.
    r.esit("proje adı kapağa geri geliyor",
           _d["alanlar"].get("k_project_title"), PROJE["proje_adi"])
    r.esit("işveren kapağa geri geliyor", _d["alanlar"].get("k_owner"), PROJE["isveren"])
    r.esit("pafta no kapağa geri geliyor", _d["alanlar"].get("k_sheet_no"), PROJE["pafta_no"])
    r.kontrol("mühendis geri yüklenmiyor ( ad+soyad birleşimi )",
              not any(k.startswith("k_elec") or k.startswith("k_mech")
                      for k in _d["alanlar"]))


    # ================================================================
    #  MUKAVEMET  —  gidiş-dönüş  ( uygulama projesi )
    # ================================================================
    import base64
    import warnings

    import main as _MM
    from engine.uygulama import mukavemet as _MK
    from engine.uygulama import mukavemet_girdi as _MG
    from exports import mukavemet_xlsx as _MX

    warnings.filterwarnings("ignore")
    if not _MX.sablon_var():
        r.atla("Mukavemet şablonu yok — geri yükleme denenmedi")
        return r

    #  Girdi uzayının farklı köşelerinden senaryolar:  her biri XLSX'e yazılıp
    #  geri okunacak ve HEM GİRDİ HEM SONUÇ birebir aynı çıkmalı.
    _senaryolar = [
        ("varsayılan", {}),
        ("küçük kabin", {"beyan_yuku": 450, "kabin_agirligi": 500,
                         "kabin_genisligi": 1000, "kabin_derinligi": 1250,
                         "kapi_genisligi": 800}),
        ("büyük kabin", {"beyan_yuku": 2000, "kabin_agirligi": 1400,
                         "kabin_genisligi": 2000, "kabin_derinligi": 2200,
                         "kabin_ray_profili": "127 x 89 x 16",
                         "agirlik_ray_profili": "90 x 75 x 16"}),
        ("1:1 askı · sertleştirilmiş kanal",
         {"aski_orani": 1, "kanal_isleme": "Sertleştirilmiş",
          "kanal_sekli": "Yarım Daire Kanal", "halat_capi": 10}),
        ("arka ağırlık · pik döküm",
         {"agirlik_yeri": "Arka", "agirlik_malzemesi": "Pik Döküm",
          "agirlik_ray_arasi": 1400, "guvenlik_tertibati": "Ani Frenlemeli"}),
        ("2 durak", {"durak_yukseklikleri": [2800, 3100],
                     "son_kat_yuksekligi": 3100, "seyir_mesafesi": 2.8}),
        ("20 durak", {"durak_yukseklikleri": [3000] * 19 + [4200],
                      "son_kat_yuksekligi": 4200, "seyir_mesafesi": 57}),
        #  reg_surtunme, TS EN 81-20 m.5.6.2.2.1.3 b)'nin µmax = 0,2 sınırına
        #  bağlıdır;  ondalık taşıma sınırın ALTINDA bir değerle sınanır.
        ("ondalıklı değerler", {"beyan_hizi": 1.6, "reg_surtunme": 0.15,
                                "acil_frenleme_a": 1.25, "halat_capi": 6.5}),
    ]
    for _ad, _ek in _senaryolar:
        _once = _MK.hesapla(_ek)
        if not r.kontrol(f"[muk] {_ad} senaryosu geçerli", _once["aktif"],
                         f"→ {_once.get('hata')}"):
            continue
        _xl = _MX.mukavemet_xlsx(_once["girdi"])
        _geri = _MX.xlsx_oku(_xl)
        #  Girdi karşılaştırması:  formülle üretilen üç alan hariç hepsi
        for _a, _h, _et, _b, _t, _s2, _v in _MG.ALANLAR:
            if _t == "hesap":
                continue
            _bek = _once["girdi"][_a]
            _bul = _geri.get(_a)
            if _t == "liste":
                r.esit(f"[muk] {_ad} · {_et}", list(_bul or []), list(_bek))
                continue
            r.esit(f"[muk] {_ad} · {_et} ({_h})", _bul, _bek)
        #  Sonuç karşılaştırması:  aynı girdi, aynı hesap
        _sonra = _MK.hesapla(_geri)
        r.kontrol(f"[muk] {_ad} · geri yüklenen hesap koşuyor", _sonra["aktif"],
                  f"→ {_sonra.get('hata')}")
        if _sonra["aktif"]:
            r.esit(f"[muk] {_ad} · özet birebir aynı", _sonra["ozet"], _once["ozet"])
            r.esit(f"[muk] {_ad} · Excel hücre haritası aynı",
                   _sonra["_h"], _once["_h"])

    #  Arayüzün gördüğü uç:  dosya → form alanları
    _xl = _MX.mukavemet_xlsx(_MK.hesapla({"beyan_yuku": 1000,
                                          "kabin_agirligi": 900})["girdi"])
    r.kontrol("mukavemet dosyası tanınıyor", _MX.mukavemet_dosyasi_mi(_xl))
    _y = _MM.api_xlsx_yukle({"icerik": base64.b64encode(_xl).decode()})
    import json as _js
    _d = _js.loads(_y.body)
    r.esit("içe aktarma türü", _d.get("tur"), "mukavemet")
    r.esit("form alanı m_beyan_yuku", _d["alanlar"].get("m_beyan_yuku"), 1000)
    r.esit("form alanı m_kabin_agirligi", _d["alanlar"].get("m_kabin_agirligi"), 900)
    r.esit("durak listesi ayrı taşınıyor", len(_d.get("muk_durak") or []), 8)
    r.kontrol("hesaplanan alanlar forma GERİ YAZILMIYOR",
              not any(k in _d["alanlar"] for k in
                      ("m_karsi_agirlik", "m_kuyu_boyu", "m_halat_arasi")),
              f"→ {[k for k in _d['alanlar'] if 'agirlik' in k]}")

    #  ---------------------------------------------------------------
    #  UYGULAMA PROJESİNİN EK GİRDİLERİ  ( elektrik · topraklama · balata )
    #  ---------------------------------------------------------------
    #  Bunların kaynak kitapta hücresi YOKTUR;  program teslim kopyasına
    #  kendi açtığı satırlara yazar.  Yazılıp okunmazsa revizyonda SESSİZCE
    #  kaybolur ve kesitler / temel ölçüleri varsayılana dönerdi.
    from engine.uygulama import girdi as _UG
    _ug = _UG.tamamla(_UG.varsayilanlar())
    _EK = {"paten_balata_boyu": 66, "kuyu_genisligi": 1900, "kolon_kesit": 25,
           "kolon_uzunluk": 33, "makine_kesit": 10, "makine_uzunluk": 44,
           "temel_a": 12.5, "temel_b": 8.5, "serit_L": 40, "mk_yok": False,
           "mk_uzunluk": 3.5, "mk_genislik": 2.5,
           #  Bağımsız denetimden sonra eklenen iki girdi
           #  ( "toplam_verim" Δη ile birlikte kaldırıldı )
           "agirlik_guvenlik_tertibati": "Kaymalı",
           "guvenlik_devreye_kuvvet": 850,
           #  Standardın metnine karşı denetimden sonra eklenen dört girdi
           #  ( TS EN 81-50 m.5.10.5 · Ek C.2.1.2 · Ek C.2.1.5 )
           "paten_tipi": "Makaralı", "klips_itme_kuvveti": 275,
           "yapi_sehim_x": 1.5, "yapi_sehim_y": 0.8,
           "reg_devreye_hizi": 1.25,
           #  Sığınma hacmi duruşu  ( TS EN 81-20 m.5.2.5.7.1 · m.5.2.5.8.1 )
           "siginma_tipi_ust": "Dik duruş", "siginma_tipi_dip": "Yatarak",
           #  Tst — makinenin azami kasnak statik yükü ( imalatçı )
           "makine_tst": 3400,
           #  Katalog halat verisi  ( TS 12385-5 tablosunu ezer )
           "halat_birim_kutle": 0.179, "halat_kopma_kN": 31.5,
           #  λ — denge ( kompanzasyon ) zinciri
           "denge_zinciri": "Var",
           #  Ds — saptırma kasnaklarının EN KÜÇÜK çapı  ( m.5.5.2.1 )
           "saptirma_kasnak_min_capi": 320,
           #  Asansör adı — çoklu projede paftaları ayırt eder
           "asansor_adi": "İnsan 1",
           #  Karşı ağırlığın KENDİ ölçüleri  ( TS EN 81-50 Ek C.2.2 · Gx · Gy )
           #  Eskiden türetiliyorlardı:  genişlik ray arasından, derinlik
           #  malzemeden.  İkisi de kaldırıldı, ölçüler artık girdi.
           "agirlik_genisligi": 850, "agirlik_derinligi": 130,
           #  Tampon tipi ve adedi  ( TS EN 81-20 m.5.8.1 · m.5.2.1.8.5 ).
           #  Kitap tamponu yalnız yerleşim ölçüsü olarak tanır;  tip ve adet
           #  teslim kopyasına ek blokta yazılır ve geri okunur.
           "tampon_tipi": MT.TAMPON_TIPLERI_ADLARI[2],
           "kabin_tampon_adedi": 2, "agirlik_tampon_adedi": 2,
           #  Askı noktası ( S ) — kabin kaçıklığından AYRI bir nokta
           #  ( TS EN 81-50 Ek C.1.2 );  C.2.2 ve C.2.3'ün moment koluna girer.
           "aski_kaciklik_x": 40, "aski_kaciklik_y": -25,
           #  Regülatör halatı katalog verisi  —  askı halatında vardı,
           #  regülatörde yoktu ( TS 12385-5 yalnız lif özlüyü kapsar ).
           "reg_halat_birim_kutle": 0.14, "reg_halat_kopma_kN": 28,
           #  Makine yükünün yolu  ( TS EN 81-20 m.5.7.2.3.7 ):  makine
           #  raylara biniyorsa Maux 150 N değildir.
           "makine_raya_biniyor": MT.MAKINE_YUK_YOLU[1], "raya_binen_yuk": 1000,
           #  α — sarılma açısı.  Kitap onu geometriden türetir ve kendi
           #  girdi sayfasında karşılığı yoktur;  beyan edilen açı ek blokta
           #  yazılıp geri okunur ( bkz. mukavemet_xlsx.EK_GIRDI_HUCRELERI ).
           "sarilma_acisi": 165,
           #  D/d < 40 için onaylanmış kuruluş belgesi  ( m.5.5.2.1 sapması )
           "kasnak_belgesi": "Var"}
    _ug.update(_EK)
    r.esit("ek girdi haritası bütün alanları kapsıyor",
           sorted(_MX.EK_GIRDI_ANAHTARLARI), sorted(_EK))
    _ekxl = _MX.mukavemet_xlsx(_ug)
    _geri = _MX.xlsx_oku(_ekxl)
    for _a, _bek in sorted(_EK.items()):
        r.esit(f"ek girdi geri geliyor: {_a}", _geri.get(_a), _bek)
    r.kontrol("ek girdiler mukavemet alanlarını bozmadı",
              _geri.get("beyan_yuku") == _ug["beyan_yuku"]
              and _geri.get("beyan_hizi") == _ug["beyan_hizi"],
              f"→ {_geri.get('beyan_yuku')!r} / {_geri.get('beyan_hizi')!r}")
    #  Onay kutusu iki yönde de doğru çözülmeli
    r.esit("mk_yok = True geri geliyor",
           _MX.xlsx_oku(_MX.mukavemet_xlsx(dict(_ug, mk_yok=True))).get("mk_yok"), True)

    #  Forma da ulaşmalı  —  api katmanı bu alanları m_ önekiyle taşır
    _ekd = _js.loads(_MM.api_xlsx_yukle(
        {"icerik": base64.b64encode(_ekxl).decode()}).body)
    for _a, _bek in sorted(_EK.items()):
        r.esit(f"forma taşınıyor: m_{_a}", _ekd["alanlar"].get(f"m_{_a}"), _bek)
    r.kontrol("program kopyasında gereksiz kayıp uyarısı ÇIKMIYOR",
              "VARSAYILANA" not in (_ekd.get("ozet") or ""), f"→ {_ekd.get('ozet')}")
    #  BOŞ bırakılmış alan KAYIP DEĞİLDİR — blok varsa uyarı çıkmamalı
    _bos = _MX.mukavemet_xlsx(dict(_ug, temel_a=None, serit_L=None,
                                   kolon_uzunluk=None))
    _bosd = _js.loads(_MM.api_xlsx_yukle(
        {"icerik": base64.b64encode(_bos).decode()}).body)
    r.kontrol("boş bırakılan alan 'kayıp' sayılmıyor",
              "VARSAYILANA" not in (_bosd.get("ozet") or ""), f"→ {_bosd.get('ozet')}")
    _g2, _blok = _MX.xlsx_oku_ayrintili(_bos)
    r.kontrol("program kopyasında ek girdi bloğu bulunuyor", _blok)
    r.kontrol("boş bırakılan alan geri de gelmiyor",
              not any(k in _g2 for k in ("temel_a", "serit_L", "kolon_uzunluk")),
              f"→ {[k for k in ('temel_a','serit_L','kolon_uzunluk') if k in _g2]}")

    #  ELDEN GELEN ÖZGÜN KİTAPTA bu satırlar yoktur:  program sessiz kalmamalı,
    #  hangi alanların varsayılana döndüğünü SAYMALI.
    _ozgun = _js.loads(_MM.api_xlsx_yukle(
        {"icerik": base64.b64encode(open(_MX.SABLON, "rb").read()).decode()}).body)
    r.kontrol("özgün kitap yine mukavemet olarak açılıyor",
              _ozgun.get("tur") == "mukavemet", f"→ {_ozgun.get('tur')}")
    r.kontrol("özgün kitapta taşınmayan alanlar AÇIKÇA bildiriliyor",
              "VARSAYILANA" in (_ozgun.get("ozet") or ""), f"→ {_ozgun.get('ozet')}")
    r.kontrol("özgün kitapta ek girdi bloğu YOK",
              not _MX.xlsx_oku_ayrintili(open(_MX.SABLON, "rb").read())[1])
    for _a, _et in (("kolon_kesit", "S1 — Kolon hattı kesiti"),
                    ("paten_balata_boyu", "Paten balatası uzunluğu  ( ℓ )"),
                    ("mk_genislik", "Makine dairesi genişliği")):
        r.kontrol(f"kayıp listesi {_a} etiketini içeriyor",
                  _et in (_ozgun.get("ozet") or ""), f"→ {_ozgun.get('ozet')}")

    #  ŞABLONA DOKUNULMADI:  ek satırlar yalnız teslim kopyasında olmalı
    import openpyxl as _op2
    _sb = _op2.load_workbook(_MX.SABLON)[_MX.GIRDI_SAYFASI]
    r.kontrol("şablonda ek girdi satırları YOK",
              all(_sb[f"B{_s}"].value in (None, "")
                  for _a, _s, _e2, _b2 in _MX.EK_GIRDI_HUCRELERI),
              "→ şablon kirlenmiş")

    #  Avan / trafik dosyaları mukavemet sanılmamalı  ( ve tersi )
    r.kontrol("trafik dosyası mukavemet sanılmıyor",
              not _MX.mukavemet_dosyasi_mi(XE.trafik_xlsx("tek", _gt)))
    _ay = _js.loads(_MM.api_xlsx_yukle(
        {"icerik": base64.b64encode(XE.trafik_xlsx("tek", _gt)).decode()}).body)
    r.esit("trafik dosyası hâlâ trafik olarak açılıyor", _ay.get("tur"), "tek")

    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
