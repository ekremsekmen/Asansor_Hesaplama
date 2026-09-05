# -*- coding: utf-8 -*-
"""
MUKAVEMET XLSX ÇIKTISI            ( UYGULAMA PROJESİ — avandan ayrı )

Avan tarafı çıktı Excel'ini SIFIRDAN kurar ( exports/xlsx_export ).  Burada
öyle yapılmaz:  kaynak çalışma kitabının kendisi teslim edilir, yalnız
"Veri Girişi" sayfası kullanıcının girdileriyle doldurulur.

NİÇİN:
  · Kitapta 1115 formül var; yeniden yazmak ikinci bir doğruluk kaynağı
    yaratır ve ikisi zamanla ayrışır.
  · Teslim edilen dosya AÇILDIĞINDA Excel kendi hesabını yapar — projeci
    programın sonucunu kitabın kendi formülleriyle karşılaştırabilir.
  · Girdiler dosyanın içinde kaldığı için revizyonda dosya yeniden açılıp
    tek değer düzeltilebilir ( avan tarafındaki alışkanlığın aynısı ).

Şablon yoksa açık bir hata verilir;  sessizce boş dosya üretilmez.
"""
import io
import os

import openpyxl

from engine.uygulama import mukavemet as MK
from engine.uygulama import mukavemet_girdi as MG
from engine.uygulama import mukavemet_tablolari as MT

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SABLON = os.path.join(KOK, "templates", "MUKAVEMET_HESABI.xlsx")
GIRDI_SAYFASI = "Veri Girişi"


def sablon_var():
    return os.path.isfile(SABLON)


def mukavemet_xlsx(girdi: dict, proje: dict = None) -> bytes:
    """Girdileri şablona yazıp çalışma kitabını bayt olarak döndürür.

    ``proje`` verilirse ( proje adı · işveren · pafta no ) dosyanın
    ÖZELLİKLERİNE yazılır — şablonun düzenine dokunulmaz, bilgi yine de
    dosyayla taşınır.  Avan çıktısındaki davranışın aynısıdır.
    """
    if not sablon_var():
        raise FileNotFoundError(
            f"Mukavemet şablonu bulunamadı: templates/{os.path.basename(SABLON)}")
    g = MG.tamamla(dict(MG.varsayilanlar(), **(girdi or {})))
    wb = openpyxl.load_workbook(SABLON)
    ws = wb[GIRDI_SAYFASI]
    for anahtar, hucre, _e, _b, tur, _s, _v in MG.ALANLAR:
        #  "hesap" alanları şablonda FORMÜLDÜR ( C80 · F80 · F108 ).
        #  Üzerine değer yazmak formülü silerdi — dosya bir daha kendi
        #  kendini hesaplayamaz hâle gelirdi.
        if tur == "hesap":
            continue
        #  Kaynak Excel'de KARŞILIĞI OLMAYAN alanlar ( ör. paten balata boyu )
        #  boş hücre adresi taşır — yazılacak/okunacak yerleri yoktur.
        if not hucre:
            continue
        if tur == "liste":
            durak = g.get(anahtar) or []
            for i, h in enumerate(MG.DURAK_HUCRELERI):
                ws[h] = durak[i] if i < len(durak) else None
            continue
        ws[hucre] = g.get(anahtar)
    p = proje or {}
    if any(p.get(k) for k in ("proje_adi", "isveren", "pafta_no", "muhendis")):
        oz = wb.properties
        oz.title = p.get("proje_adi") or None
        oz.subject = p.get("isveren") or None
        oz.category = p.get("pafta_no") or None
        if p.get("muhendis"):
            oz.creator = oz.lastModifiedBy = p["muhendis"]
    _standarda_uydur(wb, g)
    #  Dosya açılır açılmaz bütün formüller yeniden hesaplansın —  openpyxl
    #  önbelleğe alınmış değerleri düşürür, bayrak olmazsa Excel eski
    #  değerleri gösterebiliyor.
    wb.calculation.fullCalcOnLoad = True
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


# =====================================================================
#  GERİ YÜKLEME  —  revizyon
# =====================================================================
def mukavemet_dosyasi_mi(icerik: bytes) -> bool:
    """Bırakılan dosya mukavemet çalışma kitabı mı?

    Ayırt edici işaret hesap sayfasının adıdır;  avan ve trafik çıktılarında
    böyle bir sayfa yoktur.
    """
    try:
        wb = openpyxl.load_workbook(io.BytesIO(icerik), read_only=True)
        try:
            return ("11-Muk. Hesapları" in wb.sheetnames
                    and GIRDI_SAYFASI in wb.sheetnames)
        finally:
            wb.close()
    except Exception:                                         # noqa: BLE001
        return False


def xlsx_oku(icerik: bytes) -> dict:
    """Mukavemet çalışma kitabından girdileri geri okur."""
    return xlsx_oku_ayrintili(icerik)[0]


def xlsx_oku_ayrintili(icerik: bytes):
    """( girdiler, ek_blok_var )  döndürür.

    ``ek_blok_var``:  dosyada programın eklediği girdi bloğu var mı.  Yoksa
    dosya ELDEN GELEN ÖZGÜN kitaptır ve o alanlar hiç taşınmamıştır — arayüz
    bunu ayrıca söyler.  Blok VARSA boş hücre "girilmemiş" demektir;  kayıp
    değildir ve uyarı üretmemelidir.

    Program kendi ürettiği dosyayı da, elden gelen özgün kitabı da okur:
    her ikisinde de girdiler aynı hücrelerdedir.  Formülle üretilen üç alan
    ( karşı ağırlık · kuyu boyu · halat arası ) OKUNMAZ — motor onları
    kendisi türetir, yoksa dosyadaki eski değer yeni girdilerle çelişirdi.
    """
    wb = openpyxl.load_workbook(io.BytesIO(icerik), data_only=True)
    if GIRDI_SAYFASI not in wb.sheetnames:
        raise ValueError(f"Dosyada '{GIRDI_SAYFASI}' sayfası yok — "
                         "bu bir mukavemet çalışma kitabı değil.")
    ws = wb[GIRDI_SAYFASI]
    g = {}
    for anahtar, hucre, _e, _b, tur, _s, _v in MG.ALANLAR:
        if tur == "hesap":
            continue
        if tur == "liste":
            durak = [ws[h].value for h in MG.DURAK_HUCRELERI]
            g[anahtar] = [d for d in durak if d not in (None, "")]
            continue
        if not hucre:
            continue                     # Excel'de karşılığı yok
        deger = ws[hucre].value
        if deger not in (None, ""):
            g[anahtar] = deger
    #  Hesap sayfasına yazılan girdiler  ( Nps · Npr )
    if HESAP in wb.sheetnames:
        hs = wb[HESAP]
        for anahtar, hucre in HESAP_SAYFASI_GIRDILERI:
            deger = hs[hucre].value
            if deger not in (None, ""):
                g[anahtar] = deger
    #  Programın eklediği girdiler.  Elden gelen özgün kitapta bu satırlar
    #  YOKTUR;  o durumda hücreler boş okunur ve alan geri gelmez — davranış
    #  eskisiyle aynı kalır, program kendi ürettiği dosyada ise tamamını
    #  geri yükler.
    ek_blok = (str(ws[f"A{EK_GIRDI_BASLIK}"].value or "").strip()
               == EK_GIRDI_BASLIK_METNI)
    for anahtar, satir, _et, _b in EK_GIRDI_HUCRELERI:
        deger = _ek_deger_oku(anahtar, ws[f"B{satir}"].value)
        if deger is not None:
            g[anahtar] = deger
    return g, ek_blok


# =====================================================================
#  TESLİM EDİLEN KİTABI STANDARDA UYDURMA
# =====================================================================
#  NİÇİN GEREKLİ:  program TS EN 81-20 / TS EN 81-50 gereği kaynak kitabın
#  altı hesabından ayrılıyor ( engine.mukavemet.EXCEL_FARKLARI ).  Kitap
#  olduğu gibi teslim edilirse AYNI PROJENİN İKİ BELGESİ ÇELİŞİR:  pafta
#  "uygun değil" derken Excel "uygundur" der.  Bu yüzden teslim edilen
#  kopyada ilgili FORMÜLLER düzeltilir — değerler değil, formüller;  böylece
#  kitap kendi kendini hesaplamaya devam eder ve Excel'de girdi
#  değiştirildiğinde doğru sonucu verir.
#
#  ŞABLON DOSYASINA DOKUNULMAZ.  templates/MUKAVEMET_HESABI.xlsx özgün
#  hâlinde kalır;  doğrulama testleri programı ona karşı denetlemeye devam
#  eder ( bkz. testler/test_mukavemet_excel.py ).
HESAP = "11-Muk. Hesapları"

#  "Veri Girişi" sayfasında karşılığı olmayan, HESAP SAYFASINA yazılan
#  girdiler.  Kaynak kitap bunları hücreye sabit yazar;  program girdi
#  yaptığı için hem yazılır hem de geri okunur ( revizyon akışı ).
HESAP_SAYFASI_GIRDILERI = (("kasnak_tek_yon", "AH105"),
                           ("kasnak_ters_yon", "AH106"))
GIRDI = GIRDI_SAYFASI

#  ---------------------------------------------------------------------
#  PROGRAMIN EKLEDİĞİ GİRDİ HÜCRELERİ
#  ---------------------------------------------------------------------
#  Kaynak kitapta karşılığı OLMAYAN girdiler:  paten balatası uzunluğu ve
#  uygulama projesinin elektrik / topraklama alanları.  Bunlar yalnız
#  programın belleğinde dursaydı revizyonda ( "Excel'den proje aç" ) SESSİZCE
#  kaybolur, kesitler ve temel ölçüleri varsayılana dönerdi.  Bu yüzden
#  teslim kopyasına, "Veri Girişi" sayfasının sonundaki boş alana açıkça
#  yazılır ve oradan geri okunur.
#
#  ŞABLONA DOKUNULMAZ:  hücreler yalnız teslim edilen kopyaya yazılır,
#  bu yüzden MG.ALANLAR'daki "hucre" alanı boş kalır — orası KAYNAK kitabın
#  hücre haritasıdır ve doğrulama testlerinin dayanağıdır.
EK_GIRDI_BASLIK = 226
EK_GIRDI_BASLIK_METNI = ("PROGRAMIN EKLEDİĞİ GİRDİLER  "
                        "( kaynak kitapta karşılığı yoktur )")
EK_GIRDI_HUCRELERI = (
    #  (anahtar,            satır, etiket,                          birim)
    ("paten_balata_boyu",     228, "Paten balatası uzunluğu  ( ℓ )", "mm"),
    ("kuyu_genisligi",        229, "Kuyu genişliği  ( KG )",         "mm"),
    ("kolon_kesit",           230, "S1 — Kolon hattı kesiti",        "mm²"),
    ("kolon_uzunluk",         231, "L1 — Kolon hattı uzunluğu",      "m"),
    ("makine_kesit",          232, "S2 — Makine besleme kesiti",     "mm²"),
    ("makine_uzunluk",        233, "L2 — Makine besleme uzunluğu",   "m"),
    ("temel_a",               234, "Temel uzunluğu",                 "m"),
    ("temel_b",               235, "Temel genişliği",                "m"),
    ("serit_L",               236, "Topraklama şeridi boyu",         "m"),
    ("mk_yok",                237, "Makine dairesiz  ( MRL )",       "EVET / HAYIR"),
    ("mk_uzunluk",            238, "Makine dairesi uzunluğu",        "m"),
    ("mk_genislik",           239, "Makine dairesi genişliği",       "m"),
)
EK_GIRDI_ANAHTARLARI = tuple(a for a, *_x in EK_GIRDI_HUCRELERI)
#  Onay kutuları Excel'de metin olarak durur — projeci hücreyi elle de
#  düzeltebilsin diye "EVET / HAYIR" yazılır, geri okunurken çözülür.
EK_ONAY_ALANLARI = ("mk_yok",)
_EVET = ("evet", "e", "var", "true", "1", "x", "✓")


def _ek_deger_yaz(anahtar, deger):
    if anahtar in EK_ONAY_ALANLARI:
        return None if deger is None else ("EVET" if deger else "HAYIR")
    return deger


def _ek_deger_oku(anahtar, deger):
    """Hücredeki ham değeri alan türüne çevirir;  okunamazsa None döner."""
    if deger in (None, ""):
        return None
    if anahtar in EK_ONAY_ALANLARI:
        if isinstance(deger, bool):
            return deger
        return str(deger).strip().lower() in _EVET
    if isinstance(deger, bool):
        return None
    if isinstance(deger, (int, float)):
        return deger
    try:
        return float(str(deger).strip().replace(",", "."))
    except ValueError:
        return None

#  Flanş eğilmesi paydası:  ℓ + 2·( h1 − f )   [ EN 81-50 m.5.10.5 ]
FLANS_HUCRELERI = (("Q380", "E73"), ("Q385", "E73"), ("Q477", "E73"),
                   ("Q482", "E73"), ("Q538", "E73"), ("Q596", "F73"))


def _omega_formulu(lam_hucre, rm_hucre):
    """EN 81-50 m.5.10.3 ω'sının Excel karşılığı  ( Rm ara değerlemeli )."""
    #  Katsayılar ÜSTEL GÖSTERİMLE yazılmamalı:  Python "4.627e-05" üretir,
    #  Excel formül içinde küçük harfli e'yi kabul etmez.
    def sayi(x):
        return f"{x:.12f}".rstrip("0").rstrip(".") or "0"

    def egri(bantlar):
        ust, kat, us, ek = bantlar[-1]
        ic = f"{sayi(kat)}*{lam_hucre}^{sayi(us)}+{sayi(ek)}"
        for ust, kat, us, ek in reversed(bantlar[:-1]):
            ic = (f"IF({lam_hucre}<={sayi(ust)},"
                  f"{sayi(kat)}*{lam_hucre}^{sayi(us)}+{sayi(ek)},{ic})")
        return ic
    a = egri(MT.OMEGA_370)
    b = egri(MT.OMEGA_520)
    oran = (f"MEDIAN(0,({rm_hucre}-{MT.OMEGA_RM_ALT})/"
            f"{MT.OMEGA_RM_UST - MT.OMEGA_RM_ALT},1)")
    return f"=({a})+(({b})-({a}))*{oran}"


def _standarda_uydur(wb, g):
    """Kaynak kitabın standarttan sapan formüllerini teslim kopyasında düzeltir."""
    ws, vg = wb[HESAP], wb[GIRDI]

    #  ①  Tahrik kasnağı / halat oranı eşiği  —  EN 81-20 m.5.5.2.1
    ws["Q97"] = MK.SABIT["Dt_dh_asgari"]

    #  ③  Durum 2'de xQ = xc  —  EN 81-50 Ek C.2.1.1
    ws["AO312"] = "=AH293"

    #  ②  Karşı ağırlık rayı σ(My):  Wy → Wx  ( sütun 7 → 6 )
    ws["AU575"] = ("=AB575/VLOOKUP('Veri Girişi'!$F$73,"
                   "TABLOLAR!$I$60:$S$65,6,0)")

    #  ⑥  Acil frenlemede μ HALAT hızına bağlı  —  EN 81-50 m.5.11.2.3.2
    ws["AK190"] = "='Veri Girişi'!C61*'Veri Girişi'!B100"

    #  ⑦  Nps / Npr artık girdi  ( kitapta hücreye sabit yazılıydı )
    for anahtar, hucre in HESAP_SAYFASI_GIRDILERI:
        if g.get(anahtar) is not None:
            ws[hucre] = g[anahtar]

    #  ④  Flanş eğilmesinde ℓ  —  EN 81-50 m.5.10.5
    #  Kullanıcı ℓ girdiyse o sayı, girmediyse ray tablosundaki balata yarı
    #  genişliğinden 2·b olarak türetilir  ( ray Excel'de değiştirilirse
    #  formül de takip etsin diye VLOOKUP olarak yazılır ).
    l_girdi = g.get("paten_balata_boyu")
    for hucre, profil in FLANS_HUCRELERI:
        eski = ws[hucre].value
        if not (isinstance(eski, str) and "(1+2*" in eski.replace(" ", "")):
            continue
        if isinstance(l_girdi, (int, float)) and not isinstance(l_girdi, bool) \
                and l_girdi > 0:
            l = repr(float(l_girdi))
        else:
            l = f"2*VLOOKUP('Veri Girişi'!{profil},TABLOLAR!I69:N74,3,0)"
        ws[hucre] = eski.replace("(1+2*", f"({l}+2*")

    #  ⑤  ω ray çeliğine bağlı  —  EN 81-50 m.5.10.3
    ws["AD354"] = _omega_formulu("AV355", "'Veri Girişi'!B131")
    #  Makine kaidesi ST 37'dir ( Rm = 370 ).  Kitabın tablosu 2 haneye
    #  yuvarlı olduğu için burada da standardın formülü yazılır — yoksa
    #  pafta ile kitap binde ikilik bir farkla ayrışırdı.
    ws["AB39"] = _omega_formulu("Z71", str(MT.OMEGA_RM_ALT))

    #  ⑧  Sığınma açıklıklarının iki alt sınırı  —  EN 81-20 m.5.2.5.7.3 ve
    #  m.5.2.5.8.2 a) 2).  Kitap 1200 / 150 mm ister;  standartta bu sayılar
    #  yoktur.  Kabin üstü sınırı seçilen sığınma hacminin yüksekliğidir
    #  ( P639 = 1,00 m ), ray dibi sınırı ise Şekil 7'den 0,10 m'dir.
    ws["AD636"] = "=P639*1000"
    ws["AD647"] = MK.SIGINMA["min_ray_alt"]

    #  Kaynak kitapta karşılığı olmayan girdiler teslim kopyasına açıkça
    #  yazılır  ( bkz. EK_GIRDI_HUCRELERI ):  projeci hangi değerin
    #  kullanıldığını görür, revizyonda da dosyadan geri okunur.
    vg[f"A{EK_GIRDI_BASLIK}"] = EK_GIRDI_BASLIK_METNI
    for anahtar, satir, etiket, birim in EK_GIRDI_HUCRELERI:
        vg[f"A{satir}"] = etiket
        vg[f"B{satir}"] = _ek_deger_yaz(anahtar, g.get(anahtar))
        vg[f"C{satir}"] = birim
