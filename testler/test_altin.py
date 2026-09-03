# -*- coding: utf-8 -*-
"""
TEST 7 — ALTIN ÇIKTI  ( refactor kalkanı )

Trafik motorunun TAM çıktısını dondurulmuş bir kopyayla karşılaştırır:
her adım satırı, her uyarı, her not, her pafta cümlesi, sıraları dâhil.

NİÇİN AYRI BİR TEST:  diğer testler BELİRLİ DEĞERLERİ ( TR, adet, Izul )
kontrol eder.  Bir refactor'da asıl risk onlar değildir — uyarıların SIRASI,
bir notun sessizce düşmesi, bir adım satırının kaybolması gibi kimsenin
assert etmediği şeylerdir.  Bu test onların hepsini kilitler.

ÇIKTI KASITLI DEĞİŞTİYSE:
    python3 testler/altin_uret.py     → altın dosyayı yeniden üretir
Bunu çalıştırmadan ÖNCE bu testin gösterdiği farkı gözle onaylayın;
yeniden üretmek "bu davranış değişikliğini kabul ediyorum" demektir.
"""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine import traffic as TR                            # noqa: E402
from testler.altin_uret import DOSYA, senaryolar            # noqa: E402
from testler.ortak import Rapor                             # noqa: E402


def _duz(x, on=""):
    """İç içe çıktıyı 'yol = değer' satırlarına açar — fark tek satırda görünsün."""
    if isinstance(x, dict):
        for k in sorted(x):
            yield from _duz(x[k], f"{on}.{k}" if on else str(k))
    elif isinstance(x, list):
        for i, e in enumerate(x):
            yield from _duz(e, f"{on}[{i}]")
    else:
        yield on, x


def calistir():
    r = Rapor("TEST 7 — ALTIN ÇIKTI (refactor kalkanı)")
    if not os.path.isfile(DOSYA):
        r.atla(f"Altın dosya yok — 'python3 testler/altin_uret.py' ile üretin ({DOSYA})")
        return r
    with gzip.open(DOSYA, "rt", encoding="utf-8") as f:
        altin = json.load(f)

    simdi = list(senaryolar())
    if not r.esit("senaryo sayısı değişmemiş", len(simdi), len(altin)):
        return r

    for kayit, g in zip(altin, simdi):
        no = kayit["no"]
        if not r.esit(f"senaryo {no}: girdi aynı", kayit["girdi"], g):
            continue
        yeni = json.loads(json.dumps(TR.hesapla(json.loads(json.dumps(g))),
                                     ensure_ascii=False, sort_keys=True, default=str))
        eski = kayit["cikti"]
        if yeni == eski:
            r.gecti += 1
            continue
        # farkı SATIR SATIR göster — "sözlükler eşit değil" işe yaramaz
        a, b = dict(_duz(eski)), dict(_duz(yeni))
        farklar = []
        for yol in sorted(set(a) | set(b)):
            if a.get(yol, "<yok>") != b.get(yol, "<yok>"):
                farklar.append(f"{yol}:  {a.get(yol,'<yok>')!r}  →  {b.get(yol,'<yok>')!r}")
        r.kontrol(f"senaryo {no} ({g.get('bina_tipi')}, N={g.get('N')}, "
                  f"{len(g.get('asansorler') or [])} asansör)", False,
                  "\n         ".join(farklar[:4])
                  + (f"\n         … ve {len(farklar)-4} fark daha" if len(farklar) > 4 else ""))
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
