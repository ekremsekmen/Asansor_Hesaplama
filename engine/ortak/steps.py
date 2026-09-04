# -*- coding: utf-8 -*-
"""
Hesap adımı (Step) yapısı ve Türkçe sayı biçimlendirme yardımcıları.

Excel'deki "işlem satırı" mantığı burada birebir korunur:
    formul   ->  C sütunundaki sembolik denklem      (örn. "N = (1−q)·Q·V / (102·η′)")
    islem    ->  C sütunundaki sayıların yerine konmuş hâli
    deger    ->  E sütunundaki sonuç
    birim    ->  F sütunu
    kaynak   ->  G sütunu
"""
import math


# ----------------------------------------------------------------- biçimleme
def tr(x, ondalik=2):
    """Türkçe sayı biçimi: 1234.5 -> '1.234,50'  (binlik ayracı nokta)."""
    if x is None:
        return "—"
    if isinstance(x, str):
        return x
    if isinstance(x, bool):
        return "Evet" if x else "Hayır"
    try:
        s = f"{float(x):,.{ondalik}f}"
    except (TypeError, ValueError):
        return str(x)
    return s.replace(",", " ").replace(".", ",").replace(" ", ".")


def trn(x, ondalik=2):
    """Tam sayıysa ondalıksız, değilse `ondalik` haneli Türkçe biçim."""
    if x is None:
        return "—"
    if isinstance(x, str):
        return x
    try:
        f = float(x)
    except (TypeError, ValueError):
        return str(x)
    if abs(f - round(f)) < 1e-9:
        return tr(int(round(f)), 0)
    return tr(f, ondalik)


# ------------------------------------------------------- Excel eşleniği fn.
def yukari_yuvarla(x, basamak=0):
    """Excel ROUNDUP."""
    if x is None:
        return None
    k = 10 ** basamak
    return math.ceil(x * k - 1e-9) / k


def tavana_yuvarla(x, katsayi):
    """Excel CEILING(x; katsayi) — kuvvet hesaplarında 10 N'a yuvarlama."""
    if x is None:
        return None
    return math.ceil(x / katsayi - 1e-9) * katsayi


def excel_round(x, basamak=0):
    """Excel ROUND — yarımı yukarı (Python'un banker's rounding'i DEĞİL)."""
    if x is None:
        return None
    k = 10 ** basamak
    y = x * k
    return (math.floor(y + 0.5) if y >= 0 else math.ceil(y - 0.5)) / k


def sayi_mi(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


# ------------------------------------------------------------------- Step
class Step(dict):
    """Tek bir hesap satırı / veri satırı."""

    def __init__(self, sembol="", aciklama="", deger=None, birim="", kaynak="",
                 formul="", islem="", tip="deger", ondalik=2, vurgu=False):
        super().__init__(
            sembol=sembol, aciklama=aciklama, deger=deger, birim=birim,
            kaynak=kaynak, formul=formul, islem=islem, tip=tip,
            metin=trn(deger, ondalik) if tip != "metin" else (deger if deger is not None else "—"),
            vurgu=vurgu,
        )


def veri(sembol, aciklama, deger, birim="", kaynak="", ondalik=2):
    """Excel'in 'A: B : C = E F  G' satırı — girdi/ara veri."""
    return Step(sembol=sembol, aciklama=aciklama, deger=deger, birim=birim,
                kaynak=kaynak, tip="veri", ondalik=ondalik)


def hesap(formul, islem, deger, birim="", kaynak="", ondalik=2, sembol=""):
    """Excel'in iki satırlık işlem bloğu (denklem + sayıların yerine konmuş hâli)."""
    return Step(sembol=sembol, formul=formul, islem=islem, deger=deger,
                birim=birim, kaynak=kaynak, tip="hesap", ondalik=ondalik)


def kontrol(aciklama, uygun, mesaj=""):
    return Step(aciklama=aciklama, deger=mesaj or ("UYGUN" if uygun else "UYGUN DEĞİL"),
                tip="metin", vurgu=True)


def metin(icerik, vurgu=False):
    return Step(deger=icerik, tip="metin", vurgu=vurgu)


class Bolum(dict):
    """
    Numaralı hesap bölümü — Excel'deki '1 -  MOTOR GÜCÜ HESABI' başlığı.

    İki ayrı not listesi vardır:

      notlar       Bu bölümün SONUCUNA ait satırlar — taşıma/bekleme adedi,
                   sınır sağlanıyor mu, seçilen hızın gerekçesi gibi.  Ekranda
                   doğrudan görünür, paftaya da basılır.

      aciklamalar  Yöntemi anlatan, hesabı değiştirmeyen bilgi metinleri —
                   Tablo-1 kuralı, bodrumun H ve S'ye neden girmediği, MMO
                   formülündeki ray kütlesi terimi gibi.  Ekranda başlığın
                   yanındaki ⓘ simgesinde toplanır (üzerine gelince açılır),
                   paftada ise aynen basılır — çıktı hiçbir şey kaybetmez.
    """

    def __init__(self, baslik, kaynak="", adimlar=None, sonuc=None, notlar=None,
                 aciklamalar=None):
        super().__init__(baslik=baslik, kaynak=kaynak,
                         adimlar=adimlar or [], sonuc=sonuc, notlar=notlar or [],
                         aciklamalar=aciklamalar or [])
