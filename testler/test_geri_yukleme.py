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

from engine import avan as AV
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

    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
