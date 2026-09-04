# -*- coding: utf-8 -*-
"""
TEST 8  —  MUKAVEMET TABLOLARI + GİRDİ SÖZLEŞMESİ  ( uygulama projesi )

engine/mukavemet_tablolari.py içindeki her tabloyu KAYNAK EXCEL'e karşı
birebir doğrular:  templates/MUKAVEMET_HESABI.xlsx

NİÇİN AYRI TEST:  bu tablolar Excel'den makineyle aktarıldı.  Aktarma
sırasında bir sütun kayması ya da satır atlaması olsa hiçbir hesap testi
bunu göremezdi — motor kendi ( yanlış ) tablosuyla tutarlı çalışırdı.
Bu test, aktarımın kendisini denetler.

Kaynak dosya yoksa test ATLANIR, hata vermez.
"""
import os
import sys
import warnings

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.uygulama import mukavemet_girdi as MG                  # noqa: E402
from engine.uygulama import mukavemet_tablolari as MT              # noqa: E402
from testler.ortak import Rapor                           # noqa: E402

KAYNAK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                      "templates", "MUKAVEMET_HESABI.xlsx")

#  ( modüldeki tablo, Excel sayfası, aralık, Excel'den alınacak sütun sırası )
#  sütun sırası:  Excel aralığındaki 0-tabanlı indisler
ESLESME = (
    ("RAY_PROFILI",       "TABLOLAR",    "I60:S65",  None),
    ("RAY_GEOMETRI",      "TABLOLAR",    "I69:N74",  None),
    ("HALAT",             "TABLOLAR",    "A32:F43",  (0, 1, 2, 4, 5)),
    ("NPU_PROFIL",        "TABLOLAR",    "M36:AH53", (0, 9, 10, 11, 12, 13, 14, 15, 16)),
    ("KABIN_ALANI",       "TABLOLAR",    "H78:K99",  (0, 1, 2, 3)),
    ("KANAL_SEKLI",       "TABLOLAR",    "D47:G52",  (0, 2, 3)),
    ("DARBE_TIPLERI",     "TABLOLAR",    "H32:K35",  (0, 3)),
    ("AGIRLIK_MALZEMESI", "TABLOLAR",    "U61:W62",  (0, 1, 2)),
    ("RAY_CELIGI",        "TEKNİK",      "P2:R4",    (0, 1, 2)),
    ("KANAL_ISLEME",      "Veri Girişi", "T42:W43",  (0, 1, 2, 3)),
    ("BUKULGEN_KABLO",    "TABLOLAR",    "D61:G64",  (0, 1, 2, 3)),
)


def _esit(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return (a if a is not None else "") == (b if b is not None else "")


def calistir():
    print("\n\033[1mTEST 8 — MUKAVEMET TABLOLARI + GİRDİ SÖZLEŞMESİ\033[0m")
    r = Rapor("Mukavemet tabloları")
    if not os.path.isfile(KAYNAK):
        r.atla(f"Kaynak Excel yok — {os.path.basename(KAYNAK)}")
        return r
    warnings.filterwarnings("ignore")
    import openpyxl
    wb = openpyxl.load_workbook(KAYNAK, data_only=True)

    def oku(sayfa, aralik, sutunlar):
        cikti = []
        for satir in wb[sayfa][aralik]:
            v = [c.value for c in satir]
            if v[0] is None:
                continue
            cikti.append(tuple(v[i] for i in sutunlar) if sutunlar else tuple(v))
        return cikti

    for ad, sayfa, aralik, sutunlar in ESLESME:
        tablo = getattr(MT, ad)
        excel = oku(sayfa, aralik, sutunlar)
        if not r.esit(f"{ad}: satır sayısı", len(tablo), len(excel)):
            continue
        for i, (m, e) in enumerate(zip(tablo, excel)):
            if not r.esit(f"{ad}[{i}]: sütun sayısı", len(m), len(e)):
                continue
            for j, (mv, ev) in enumerate(zip(m, e)):
                r.kontrol(f"{ad}[{i}][{j}]", _esit(mv, ev), f"→ modül {mv!r}, Excel {ev!r}")

    #  ω tablosu:  231 satır, λ = 20…250
    om = oku("TABLOLAR", "A47:B277", (0, 1))
    r.esit("OMEGA: satır sayısı", len(MT.OMEGA), len(om))
    r.esit("OMEGA: λ alt sınırı", MT.OMEGA_LAMBDA_MIN, om[0][0])
    r.esit("OMEGA: λ üst sınırı", MT.OMEGA_LAMBDA_MAX, om[-1][0])
    for lam, w in om:
        r.kontrol(f"ω(λ={lam})", _esit(MT.omega(lam), w),
                  f"→ modül {MT.omega(lam)!r}, Excel {w!r}")
    r.kontrol("ω tablo dışı λ için None", MT.omega(19) is None and MT.omega(251) is None)

    #  Ağırlık ray arası — yatay tablo
    yat = [[c.value for c in s] for s in wb["TABLOLAR"]["X59:Z60"]]
    r.esit("AGIRLIK_RAY_ARASI satır", len(MT.AGIRLIK_RAY_ARASI), 2)
    for i in range(len(yat[0])):
        r.kontrol(f"ağırlık ray arası {yat[0][i]} → genişlik",
                  _esit(MT.agirlik_genisligi(yat[0][i]), yat[1][i]),
                  f"→ {MT.agirlik_genisligi(yat[0][i])!r} / {yat[1][i]!r}")

    #  Erişim işlevleri gerçekten doğru sütunu okuyor mu
    p = "89 x 62 x 15,88"
    r.esit("ray() Gr", MT.ray(p, "Gr"), 12.38)
    r.esit("ray() Wx", MT.ray(p, "Wx"), 14350)
    r.esit("ray() ix", MT.ray(p, "ix"), 19.48)
    r.esit("npu() A", MT.npu(120, "A"), 17)
    r.esit("npu() Wx", MT.npu(120, "Wx"), 60.7)
    r.esit("npu() ix", MT.npu(120, "ix"), 4.62)
    r.esit("halat_kopma()", MT.halat_kopma(6.5), 24700)
    r.esit("k2 sabiti", MT.K2_NORMAL_KULLANMA, 1.2)
    r.esit("kablo_agirligi()", MT.kablo_agirligi("24 x 0,75"), 0.642)
    r.kontrol("bilinmeyen anahtar None döner",
              MT.ray("yok", "Gr") is None and MT.halat_kopma(99) is None)

    _girdi_sozlesmesi(r, wb)
    return r


#  Excel'in kendi açılır liste ( veri doğrulama ) aralıkları, girdi
#  alanlarının seçenek listesinin kaynağıdır.  İki alanda bilerek
#  ayrıldık; burada Excel'in HAM listesini kilitliyoruz ki kaynak dosya
#  değişirse fark yeniden gözden geçirilsin.
BILINEN_FARK = {
    #  Excel'in açılır listesi "Döküm" yazıyor, ama VLOOKUP tablosunun
    #  ( TABLOLAR!U61:W62 ) anahtarı "Pik Döküm".  Excel'de "Döküm"
    #  seçilirse arama #YOK verir — kaynaktaki hata.  Modül tablo
    #  anahtarını kullanıyor.
    "agirlik_malzemesi": (["Barit", "Döküm"], ["Barit", "Pik Döküm"]),
    #  Hız listesinin sonunda 5 adet dolgu 0 var; hız 0 anlamsız.
    "beyan_hizi": ([0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6, 0, 0, 0, 0, 0],
                   [0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6]),
}


def _girdi_sozlesmesi(r, wb):
    """engine/mukavemet_girdi.py ↔ 'Veri Girişi' sayfası."""
    from openpyxl.utils import range_boundaries
    ws = wb["Veri Girişi"]

    #  Hücre → veri doğrulama aralığı
    dv_araligi = {}
    for dv in ws.data_validations.dataValidation:
        f1 = str(dv.formula1 or "")
        if not f1.startswith("$"):
            continue
        for rng in dv.sqref.ranges:
            mn, mr, mx, mxr = range_boundaries(str(rng))
            for c in range(mn, mx + 1):
                for w in range(mr, mxr + 1):
                    dv_araligi[ws.cell(row=w, column=c).coordinate] = f1.replace("$", "")

    for anahtar, hucre, etiket, _b, tur, secenekler, varsayilan in MG.ALANLAR:
        if tur == "hesap":
            r.kontrol(f"girdi {anahtar}: seçenek/varsayılan taşımıyor",
                      secenekler is None and varsayilan is None)
            continue
        if tur == "liste":
            excel = [ws[h].value for h in MG.DURAK_HUCRELERI]
            excel = [v for v in excel if v not in (None, "")]
            r.esit(f"girdi {anahtar}: varsayılan", list(varsayilan), excel)
            r.esit("durak hücresi sayısı", len(MG.DURAK_HUCRELERI), 23)
            continue

        r.kontrol(f"girdi {anahtar}: etiket dolu", bool(etiket and etiket.strip()))
        if not hucre:
            #  Kaynak Excel'in "Veri Girişi" sayfasında KARŞILIĞI OLMAYAN alan.
            #  Excel bu değerleri ya hesap sayfasına sabit yazar ( Nps · Npr )
            #  ya da hiç sormaz ( paten balata boyu ).  Varsayılanı Excel'e
            #  karşı denetlenemez;  yalnız açılır liste taşımadığı doğrulanır.
            r.kontrol(f"girdi {anahtar}: hücresiz alan açılır liste taşımıyor",
                      secenekler is None, f"→ {secenekler!r}")
            continue
        r.kontrol(f"girdi {anahtar}: varsayılan Excel'deki değer ({hucre})",
                  _esit(varsayilan, ws[hucre].value),
                  f"→ modül {varsayilan!r}, Excel {ws[hucre].value!r}")

        ar = dv_araligi.get(hucre)
        if secenekler is None:
            r.kontrol(f"girdi {anahtar}: Excel'de de açılır liste yok", ar is None,
                      f"→ Excel'de {ar} listesi var, modülde serbest sayı")
            continue
        if ar is None:
            continue          #  seçenekler bir tablodan geliyor, DV yok
        ex = [c.value for row in ws[ar] for c in row if c.value not in (None, "")]
        if anahtar in BILINEN_FARK:
            ham, modul = BILINEN_FARK[anahtar]
            r.kontrol(f"girdi {anahtar}: Excel listesi bilinen farkla aynı ({ar})",
                      sorted(map(str, ham)) == sorted(map(str, ex)),
                      f"→ beklenen {ham}, Excel {ex}")
            r.kontrol(f"girdi {anahtar}: modül belgelenen listeyi kullanıyor",
                      sorted(map(str, modul)) == sorted(map(str, secenekler)),
                      f"→ modül {list(secenekler)}, belgelenen {modul}")
            continue
        r.kontrol(f"girdi {anahtar}: seçenekler ≡ Excel açılır listesi ({ar})",
                  sorted(map(str, secenekler)) == sorted(map(str, ex)),
                  f"→ modül {list(secenekler)}, Excel {ex}")

    #  Hesaplanan üç alan Excel formülüyle aynı sonucu veriyor mu
    v = wb  # data_only=True yüklendi
    g = MG.varsayilanlar()
    for anahtar, hucre in (("karsi_agirlik", "C80"), ("kuyu_boyu", "F80"),
                           ("halat_arasi", "F109")):
        r.kontrol(f"hesaplanan {anahtar} ≡ Excel {hucre}",
                  _esit(g[anahtar], v["Veri Girişi"][hucre].value),
                  f"→ modül {g[anahtar]!r}, Excel {v['Veri Girişi'][hucre].value!r}")
    r.kontrol("varsayılan girdiler doğrulamadan temiz geçiyor", MG.dogrula(g) == [],
              f"→ {MG.dogrula(g)}")
    r.esit("toplam ray boyu (m)", MG.toplam_ray_boyu(g), 26.6)


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
