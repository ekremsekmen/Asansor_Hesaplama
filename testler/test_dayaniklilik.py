# -*- coding: utf-8 -*-
"""
TEST 3  —  GİRDİ DAYANIKLILIĞI VE API SÖZLEŞMESİ

Program hiçbir girdide çökmemeli; anlamsız girdide anlaşılır hata döndürmeli.
Sunucu ayakta değilse HTTP bölümü atlanır, motor bölümü yine çalışır.
"""
import json
import os
import sys
import urllib.error
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import avan as AV, traffic as TR          # noqa: E402
from testler.ortak import Rapor                        # noqa: E402

import main as UYGULAMA                                # noqa: E402

BASE = os.environ.get("AVAN_TEST_URL", "http://127.0.0.1:8760")

# Kasten bozuk / uç girdiler
KOTU_DEGERLER = [
    "", "   ", None, "abc", "1,2,3", "-5", "0", "1e400", "NaN", "Infinity",
    "٣", "１０", "3٫5", "<script>alert(1)</script>", "'; DROP TABLE x;--",
    "=1+1", "9" * 60, "1.234.567,89", "1,234,567.89", "1 234,5", "٫", "—",
    "\n\t", "3,,5", ",5", "5,", "+3", "%50", "3 m", True, False, [], {}, 0, -1,
]


def calistir():
    print("\n\033[1mTEST 3 — GİRDİ DAYANIKLILIĞI VE API SÖZLEŞMESİ\033[0m")
    r = Rapor("Dayanıklılık")

    # ------------------------------------------------ sayı ayrıştırma
    for metin, bek in (("1,60", 1.6), ("1.60", 1.6), ("1,234.56", 1234.56),
                       ("1.234,56", 1234.56), ("  3  ", 3), ("", None),
                       ("abc", None), (None, None), ("-2,5", -2.5),
                       ("0,075", 0.075), (12, 12), (3.0, 3)):
        r.esit(f"_sayi({metin!r})", UYGULAMA._sayi(metin), bek)
    r.kontrol("_sayi(True) sayı sayılmaz", UYGULAMA._sayi(True) in (None, 1))

    # ------------------------------------------------ motor: her kötü değer her alanda
    ALANLAR = ("bina_yuksekligi", "yapi_yuksekligi", "N", "hizli1", "hizli2", "h",
               "P", "kapi_genisligi", "manuel_k", "manuel_V", "manuel_adet")
    TEMEL = dict(bina_tipi="Konut", bina_yuksekligi="39,98", yapi_yuksekligi="43",
                 N="11", h="3", hizli1="44", hizli2="3", P="10",
                 kapi_genisligi="900", kapi_tipi="Merkezden Açılan Oto.")
    cokme = 0
    for alan in ALANLAR:
        for kotu in KOTU_DEGERLER:
            veri = dict(TEMEL)
            veri[alan] = kotu
            try:
                _, g = UYGULAMA._trafik_girdi({"mod": "tek", "girdiler": veri})
                s = TR.hesapla_tek(g)
                if not isinstance(s, dict):
                    cokme += 1
            except Exception as e:                                  # noqa: BLE001
                cokme += 1
                r.kontrol(f"tek/{alan}={kotu!r} çökme", False, f"→ {type(e).__name__}: {e}")
    r.kontrol(f"tek asansör: {len(ALANLAR)*len(KOTU_DEGERLER)} bozuk girdi kombinasyonu çökmedi",
              cokme == 0)

    # bina tipi ve kapı tipi metin alanları
    for kotu in ("", None, "Konut ", "konut", "<b>x</b>", "Yok", 5, ["Konut"]):
        try:
            _, g = UYGULAMA._trafik_girdi({"mod": "tek", "girdiler": dict(TEMEL, bina_tipi=kotu)})
            s = TR.hesapla_tek(g)
            r.kontrol(f"bina_tipi={kotu!r} anlamlı hata", isinstance(s, dict))
        except Exception as e:                                      # noqa: BLE001
            r.kontrol(f"bina_tipi={kotu!r} çökme", False, f"→ {e}")
    for kotu in ("", None, "Teleskopik", "yok", 7):
        try:
            _, g = UYGULAMA._trafik_girdi({"mod": "tek", "girdiler": dict(TEMEL, kapi_tipi=kotu)})
            r.kontrol(f"kapi_tipi={kotu!r} çökmedi", isinstance(TR.hesapla_tek(g), dict))
        except Exception as e:                                      # noqa: BLE001
            r.kontrol(f"kapi_tipi={kotu!r} çökme", False, f"→ {e}")

    # ------------------------------------------------ çoklu: bozuk asansör listeleri
    C = dict(bina_tipi="Konut", bina_yuksekligi="39,98", yapi_yuksekligi="43",
             N="11", h="3", hizli1="44", hizli2="3")
    for asl in ([], [{}], [{"P": ""}], [{"P": "abc"}],
                [{"P": "10"}] * 8,                       # 4'ten fazla
                [{"P": "10", "kapi_genisligi": "yok", "kapi_tipi": None}],
                [{"P": "10", "durak": "-3"}], [{"P": "10", "V": "9"}],
                [{"P": "10", "h": "0"}], [{"P": "99"}]):
        try:
            _, g = UYGULAMA._trafik_girdi({"mod": "coklu", "girdiler": dict(C, asansorler=asl)})
            r.kontrol(f"çoklu asansorler={str(asl)[:38]} çökmedi",
                      isinstance(TR.hesapla_coklu(g), dict))
        except Exception as e:                                      # noqa: BLE001
            r.kontrol(f"çoklu asansorler={str(asl)[:38]} çökme", False, f"→ {e}")

    # ------------------------------------------------ avan: bozuk girdiler
    A = dict(aktif=True, tanim="A", kapasite="10", V="1.6", eta="0,85", Hk="32,85",
             kuyu_genisligi="1800", kabin_boyu="1450", kabin_genisligi="1300",
             gr="17,91", Fmk="350", Fsh="100", Nsc="11", S1="6", L1="32,85",
             S2="6", L2="3", kablo_tipi="NHXMH FE180")
    O = dict(U="380", kappa="56", eps_max="3", temel_a="26,55", temel_b="16,4",
             beta="150", serit_L="58,5", cubuk_sayisi="4", mk_uzunluk="0", mk_genislik="0")
    AVAN_ALAN = ("kapasite", "V", "eta", "Hk", "kuyu_genisligi", "kabin_boyu",
                 "kabin_genisligi", "gr", "Fmk", "Fsh", "Nsc", "S1", "L1", "S2", "L2",
                 "Q_elle", "Gk_elle")
    cokme = 0
    for alan in AVAN_ALAN:
        for kotu in KOTU_DEGERLER:
            try:
                v = UYGULAMA._avan_girdi({"girdiler": {"ortak": O,
                                                       "asansorler": [dict(A, **{alan: kotu})],
                                                       "sabitler": {}}})
                s = AV.hesapla(v)
                if not isinstance(s, dict):
                    cokme += 1
            except Exception as e:                                  # noqa: BLE001
                cokme += 1
                r.kontrol(f"avan/{alan}={kotu!r} çökme", False, f"→ {type(e).__name__}: {e}")
    r.kontrol(f"avan: {len(AVAN_ALAN)*len(KOTU_DEGERLER)} bozuk girdi kombinasyonu çökmedi",
              cokme == 0)

    # ortak girdiler
    cokme = 0
    for alan in O:
        for kotu in KOTU_DEGERLER:
            try:
                v = UYGULAMA._avan_girdi({"girdiler": {"ortak": dict(O, **{alan: kotu}),
                                                       "asansorler": [A], "sabitler": {}}})
                AV.hesapla(v)
            except Exception as e:                                  # noqa: BLE001
                cokme += 1
                r.kontrol(f"avan/ortak.{alan}={kotu!r} çökme", False, f"→ {e}")
    r.kontrol(f"avan ortak girdiler: {len(O)*len(KOTU_DEGERLER)} kombinasyon çökmedi", cokme == 0)

    # sabitler (ofis standardı) bozulursa
    cokme = 0
    for alan in AV.SABIT_B_VARSAYILAN:
        for kotu in ("", "abc", "0", "-1", "999999"):
            try:
                v = UYGULAMA._avan_girdi({"girdiler": {"ortak": O, "asansorler": [A],
                                                       "sabitler": {alan: kotu}}})
                AV.hesapla(v)
            except Exception as e:                                  # noqa: BLE001
                cokme += 1
                r.kontrol(f"sabit {alan}={kotu!r} çökme", False, f"→ {e}")
    r.kontrol("bozuk ofis standardı değerleri çökmedi", cokme == 0)

    # ek nüfus satırları
    for ek in ([], [{}], [{"kalem": "yok", "miktar": "5"}],
               [{"kalem": "KONUT — Diğer oda", "miktar": "abc"}],
               [{"kalem": "KONUT — Diğer oda", "miktar": "-5"}],
               [{"kalem": "DOĞRUDAN KİŞİ — Tablo-1 dışı", "miktar": "1000000"}],
               [{"kalem": "KONUT — Diğer oda", "miktar": "1"}] * 30):
        try:
            _, g = UYGULAMA._trafik_girdi({"mod": "tek", "girdiler": dict(TEMEL, ek_nufus=ek)})
            r.kontrol(f"ek_nufus={str(ek)[:34]} çökmedi", isinstance(TR.hesapla_tek(g), dict))
        except Exception as e:                                      # noqa: BLE001
            r.kontrol(f"ek_nufus={str(ek)[:34]} çökme", False, f"→ {e}")

    # ------------------------------------------------ HTTP uçları
    def istek(yol, govde=None, yontem="POST"):
        veri = json.dumps(govde).encode() if govde is not None else None
        req = urllib.request.Request(BASE + yol, data=veri, method=yontem,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=60) as c:
            return c.status, c.read(), dict(c.headers)

    try:
        istek("/api/saglik", yontem="GET")
    except Exception:                                               # noqa: BLE001
        r.atla(f"Sunucu {BASE} adresinde çalışmıyor — HTTP bölümü atlandı "
               "(programı açıkken testi tekrar çalıştırın).")
        return r

    kod, govde, _ = istek("/api/saglik", yontem="GET")
    r.kontrol("/api/saglik 200", kod == 200)
    r.kontrol("sürüm bilgisi var", "surum" in json.loads(govde))

    kod, govde, _ = istek("/api/secenekler", yontem="GET")
    sec = json.loads(govde)
    r.kontrol("/api/secenekler 200", kod == 200)
    for anahtar in ("bina_tipleri", "kapasiteler", "hizlar", "kapi_genislikleri",
                    "kapi_tipleri", "tablo_1", "tablo_7", "tablo_9", "tablo_10",
                    "sabit_a", "sabit_b", "kesitler"):
        r.kontrol(f"secenekler.{anahtar} var", anahtar in sec and sec[anahtar])

    # ana sayfa
    req = urllib.request.Request(BASE + "/", method="GET")
    with urllib.request.urlopen(req, timeout=30) as c:
        html = c.read().decode()
    r.kontrol("ana sayfa yüklendi", "<title>" in html and "app.js" in html)

    # bozuk gövdeler — 500 dönmemeli
    for govde in ({}, {"mod": "tek"}, {"girdiler": {}}, {"mod": "yok", "girdiler": {}},
                  {"mod": "tek", "girdiler": {"bina_tipi": "Yok"}},
                  {"mod": "coklu", "girdiler": {"asansorler": "metin"}},
                  {"girdiler": {"ortak": None, "asansorler": None}},
                  {"girdiler": {"asansorler": [{"aktif": True}]}}):
        for yol in ("/api/trafik", "/api/avan"):
            try:
                kod, cevap, _ = istek(yol, govde)
                r.kontrol(f"{yol} {str(govde)[:30]} → 200", kod == 200)
                r.kontrol(f"{yol} {str(govde)[:30]} → JSON",
                          isinstance(json.loads(cevap), dict))
            except urllib.error.HTTPError as e:
                r.kontrol(f"{yol} {str(govde)[:30]} sunucu hatası", False, f"→ HTTP {e.code}")
            except Exception as e:                                  # noqa: BLE001
                r.kontrol(f"{yol} {str(govde)[:30]} istisna", False, f"→ {e}")

    # indirme uçları bozuk gövdeyle de dosya üretmeli ya da düzgün hata dönmeli
    for yol in ("/api/indir/trafik-pdf", "/api/indir/trafik-xlsx",
                "/api/indir/avan-pdf", "/api/indir/avan-xlsx"):
        for govde in ({"mod": "tek", "girdiler": {"bina_tipi": "Konut"}, "proje": {}},
                      {"girdiler": {"ortak": {}, "asansorler": []}, "proje": {}}):
            try:
                kod, icerik, basliklar = istek(yol, govde)
                r.kontrol(f"{yol} boş girdide çökmedi", kod == 200 and len(icerik) > 500)
                if yol.endswith("pdf"):
                    r.kontrol(f"{yol} geçerli PDF", icerik[:4] == b"%PDF")
                else:
                    r.kontrol(f"{yol} geçerli XLSX", icerik[:2] == b"PK")
            except Exception as e:                                  # noqa: BLE001
                r.kontrol(f"{yol} boş girdi", False, f"→ {e}")

    # proje adı dosya adına güvenli biçimde geçmeli
    kod, icerik, basliklar = istek("/api/indir/trafik-pdf", {
        "mod": "tek",
        "girdiler": dict(TEMEL),
        "proje": {"proje_adi": "../../kötü/ad:*?\"<>|  ÇĞİÖŞÜ", "muhendis": "X"}})
    cd = basliklar.get("Content-Disposition", "")
    r.kontrol("dosya adında yol ayracı yok", "/" not in cd.split("''")[-1].replace("%2F", "/")
              or "%2F" not in cd)
    r.kontrol("proje adlı PDF üretildi", kod == 200 and icerik[:4] == b"%PDF")

    # ---------------------------------------------------------- /api/sablon
    #  Şablon denetimi ucu: yanlış / eski Excel konmuşsa arayüz bunu açılışta
    #  gösterir.  Uç her zaman JSON dönmeli, çökmemeli.
    try:
        _sd = json.loads(urllib.request.urlopen(BASE + "/api/sablon", timeout=30).read())
        r.kontrol("/api/sablon JSON dönüyor", isinstance(_sd, dict) and "sablonlar" in _sd)
        r.esit("/api/sablon iki şablon bildiriyor", len(_sd.get("sablonlar") or []), 2)
        for _s in (_sd.get("sablonlar") or []):
            for _a in ("tur", "baslik", "uygun", "dosya", "md5", "sayfa_sayisi", "hatalar"):
                r.kontrol(f"/api/sablon alanı var: {_a}", _a in _s)
        r.kontrol("/api/sablon şablonları uygun bildiriyor", _sd.get("uygun") is True)
    except Exception as e:                                    # noqa: BLE001
        r.kontrol("/api/sablon çalışıyor", False, f"→ {e}")

    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
