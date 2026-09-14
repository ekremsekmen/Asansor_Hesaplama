# -*- coding: utf-8 -*-
"""
Hesap adımı (Step) yapısı ve Türkçe sayı biçimlendirme yardımcıları.

Paftanın "işlem satırı":
    formul   ->  sembolik denklem      (örn. "N = (1−q)·Q·V / (102·η)")
    islem    ->  sayıların yerine konmuş hâli
    deger    ->  sonuç
    birim    ->  birim
    kaynak   ->  standart maddesi / verinin kaynağı
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


# ------------------------------------------------------------ yuvarlama
def yukari_yuvarla(x, basamak=0):
    """Sıfırdan uzağa değil, YUKARI yuvarlar ( `basamak` ondalığa )."""
    if x is None:
        return None
    k = 10 ** basamak
    return math.ceil(x * k - 1e-9) / k


def tavana_yuvarla(x, katsayi):
    """`katsayi`nın bir üst katına yuvarlar — kuvvet hesaplarında 10 N'a yuvarlama."""
    if x is None:
        return None
    return math.ceil(x / katsayi - 1e-9) * katsayi


def yuvarla(x, basamak=0):
    """Yarımı yukarı yuvarlar ( Python'un round()'u bankacı yuvarlaması yapar )."""
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
    """Veri satırı:  sembol · açıklama = değer birim · kaynak."""
    return Step(sembol=sembol, aciklama=aciklama, deger=deger, birim=birim,
                kaynak=kaynak, tip="veri", ondalik=ondalik)


def hesap(formul, islem, deger, birim="", kaynak="", ondalik=2, sembol=""):
    """İki satırlık işlem bloğu ( denklem + sayıların yerine konmuş hâli )."""
    return Step(sembol=sembol, formul=formul, islem=islem, deger=deger,
                birim=birim, kaynak=kaynak, tip="hesap", ondalik=ondalik)


def kontrol(aciklama, uygun, mesaj=""):
    return Step(aciklama=aciklama, deger=mesaj or ("UYGUN" if uygun else "UYGUN DEĞİL"),
                tip="metin", vurgu=True)


def metin(icerik, vurgu=False):
    return Step(deger=icerik, tip="metin", vurgu=vurgu)


#  Bölüm başlığının biçimi:  "4 - ASKI HALATLARININ HESAPLANMASI".
#  Tek yerde durur ki numaralayan taraf ile okuyan taraf ayrışmasın.
BASLIK_BICIMI = "{sira} - {ad}"


def basliktan_ad(baslik):
    """'3 -  KABİN AYDINLATMA HESABI'  →  'KABİN AYDINLATMA HESABI'."""
    metin = str(baslik or "")
    bas, ayrac, son = metin.partition(" - ")
    return son.strip() if ayrac and bas.strip().isdigit() else metin.strip()


def numarala(b, sira):
    """Bölüme sıra numarasını verir ve başlığını yeniden yazar.

    Başlıktaki numara BİÇİMDİR, KİMLİK DEĞİLDİR:  aynı hesap projeden
    projeye başka numara alır ( makine dairesi olmayan binada topraklama bir
    sıra öne kayar ).  Bu yüzden numarayı yalnız burası koyar ve bölüme
    ayrıca ``sira`` diye yazar;  kimliğe ihtiyacı olan ``kimlik`` alanını
    okur ( bkz. Bolum ).
    """
    ad = b.get("ad") or basliktan_ad(b.get("baslik"))
    b["ad"] = ad
    b["sira"] = sira
    b["baslik"] = BASLIK_BICIMI.format(sira=sira, ad=ad)
    return b


class Bolum(dict):
    """
    Numaralı hesap bölümü — paftadaki '1 -  MOTOR GÜCÜ HESABI' başlığı.

    KİMLİK ve NUMARA AYRI ŞEYLERDİR.  ``kimlik`` bölümün değişmez adıdır
    ( "aski_halatlari" ) ve doğduğu yerde verilir;  başlıktaki numara ise
    yalnız BASIM SIRASIDIR ve projeye göre değişir — proje geneli bölümler
    ayrıldığında kalanlar yeniden numaralanır, makine dairesi yoksa
    topraklama bir sıra öne gelir.  Bölümü dışarıdan tanıyan her şey
    ( sonuçtan girdiye atlama gibi ) numaraya değil KİMLİĞE bakmalıdır;
    numaraya bakan eşlemeler sessizce yanlış bölümü gösterir.

    ``kimlik`` verilmezse ``kimlik`` / ``ad`` alanları hiç yazılmaz —
    kimliğe ihtiyacı olmayan bölümlerin çıktısı olduğu gibi kalır.

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
                 aciklamalar=None, kimlik=None):
        super().__init__(baslik=baslik, kaynak=kaynak,
                         adimlar=adimlar or [], sonuc=sonuc, notlar=notlar or [],
                         aciklamalar=aciklamalar or [])
        if kimlik:
            self["kimlik"] = kimlik
            self["ad"] = basliktan_ad(baslik)


#  ---------------------------------------------------------------------
#  ONAY ( EVET / HAYIR ) ALANLARI  —  TEK YERDE
#  ---------------------------------------------------------------------
#  Aynı altı satır birkaç dosyada kopyalanmıştı.  Onay alanı birden çok
#  biçimde gelir:  arayüzden True/False, eski proje dosyalarından
#  "EVET"/"HAYIR" ya da "Var"/"Yok".  Kopyalar zamanla ayrışır ve aynı kutu
#  bir yerde işaretli, öbüründe işaretsiz sayılırdı.
def evet_mi(x):
    """Onay alanı işaretli mi  —  arayüz · eski proje dosyası."""
    if isinstance(x, bool):
        return x
    if x is None:
        return False
    return str(x).strip().lower() in ("evet", "e", "var", "true", "1", "yes",
                                      "x", "✓")
