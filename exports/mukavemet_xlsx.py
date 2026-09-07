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
from datetime import date

import openpyxl

from engine.ortak import ofis as OFIS
from exports.hucre_haritasi import IMZA, IMZALAR
from engine.uygulama import mukavemet as MK
from engine.uygulama import mukavemet_girdi as MG
from engine.avan import tablolar as AV_TAB
from engine.uygulama import sabitler as US
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
    #  PROJE KİMLİĞİ dosya ÖZELLİKLERİNE yazılır ( şablonda hücresi yok ).
    #  YAZAN ALANI HER ZAMAN DAMGALANIR:  şablonun özgün yazarı ( başka bir
    #  kişi ) dosyada kalırsa, geri okurken onu "mühendis" sanıyorduk.
    oz = wb.properties
    if any(p.get(k) for k in ("proje_adi", "isveren", "pafta_no", "muhendis")):
        oz.title = p.get("proje_adi") or None
        oz.subject = p.get("isveren") or None
        oz.category = p.get("pafta_no") or None
    oz.creator = oz.lastModifiedBy = p.get("muhendis") or IMZA
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


def proje_kimligi_oku(icerik: bytes) -> dict:
    """Dosya ÖZELLİKLERİNDEN proje adı · işveren · pafta no · mühendis.

    Program bu üçünü yazarken kullanıyor ( mukavemet_xlsx ) ama geri
    okumuyordu:  revizyonda ekranda ÖNCEKİ projenin kimliği kalıyor ve
    bir sonraki çıktı yanlış adla iniyordu.
    """
    try:
        wb = openpyxl.load_workbook(io.BytesIO(icerik), read_only=True)
        try:
            oz = wb.properties
        finally:
            wb.close()
    except Exception:                                         # noqa: BLE001
        return {}
    yazan = str(oz.creator or "").strip()
    return {"proje_adi": str(oz.title or "").strip(),
            "isveren": str(oz.subject or "").strip(),
            "pafta_no": str(oz.category or "").strip(),
            #  Programın kendi imzası mühendis adı DEĞİLDİR.
            "muhendis": "" if yazan in IMZALAR else yazan}


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
    ofis = _ofis_oku(ws)
    if ofis:
        g["_ofis"] = ofis
    for anahtar, satir, _et, _b in EK_GIRDI_HUCRELERI:
        ham = ws[f"B{satir}"].value
        deger = (str(ham).strip() if anahtar in EK_METIN_ALANLARI and ham not in (None, "")
                 else _ek_deger_oku(anahtar, ham))
        if deger not in (None, ""):
            g[anahtar] = deger
    return g, ek_blok


# =====================================================================
#  OFİSİN ANA KİTABININ DÜZELTİLMİŞ KOPYASI
# =====================================================================
DUZELTME_SAYFASI = "DÜZELTMELER"


def duzeltilmis_kaynak() -> bytes:
    """Ofisin ana çalışma kitabının DÜZELTİLMİŞ kopyasını üretir.

    Program teslim ettiği her dosyayı zaten düzeltir ( _standarda_uydur ), ama
    ofisin masasındaki ana kitap düzelmiyordu:  onu açıp elle hesap yapan
    eski sonuçları alıyordu.  Bu işlev o boşluğu kapatır.

    ŞABLON DOSYASINA DOKUNULMAZ.  templates/MUKAVEMET_HESABI.xlsx özgün
    hâlinde kalmalıdır — doğrulama paketinin tamamı ( TEST 9 · TEST 10 )
    motoru ONA karşı denetler ve sapmalarımızın gerekçesi kitabın o
    hücrelerde ne yaptığıdır.  Düzeltilmiş kitap AYRI bir dosyadır.

    Teslim kopyasından farkı:  buraya HİÇBİR projenin girdisi yazılmaz.
    Yalnız FORMÜLLER düzeltilir;  kitap kendi örnek girdileriyle kendi
    kendini hesaplamaya devam eder ve ofis onu boş bir usta kopya olarak
    kullanabilir.
    """
    if not sablon_var():
        raise FileNotFoundError(
            f"Mukavemet şablonu bulunamadı: templates/{os.path.basename(SABLON)}")
    wb = openpyxl.load_workbook(SABLON)
    #  g = {} :  ⑦'nin girdi yazması ve ek girdi bloğunun dolması engellenir;
    #  ④'te ℓ, sayı yerine ray tablosunu okuyan VLOOKUP olur.
    _standarda_uydur(wb, {})
    #  KAYIT, ÖZGÜNLE FARK ALINARAK ÜRETİLİR.  Elle tutulan bir liste zamanla
    #  koddan ayrışır;  fark almak neyin gerçekten değiştiğini gösterir.
    _duzeltme_kaydi(wb, _fark(openpyxl.load_workbook(SABLON), wb))
    wb.calculation.fullCalcOnLoad = True
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf.read()


def _fark(ozgun, yeni):
    """İki kitabı hücre hücre karşılaştırır  →  [ (sayfa, hücre, eski, yeni) ]."""
    degisen = []
    for sayfa in yeni.sheetnames:
        if sayfa == DUZELTME_SAYFASI or sayfa not in ozgun.sheetnames:
            continue
        a, b = ozgun[sayfa], yeni[sayfa]
        satir = max(a.max_row, b.max_row)
        sutun = max(a.max_column, b.max_column)
        for r in range(1, satir + 1):
            for c in range(1, sutun + 1):
                x, y = a.cell(row=r, column=c), b.cell(row=r, column=c)
                if x.value != y.value:
                    degisen.append((sayfa, y.coordinate, x.value, y.value))
    return degisen


def _duzeltme_kaydi(wb, degisen):
    """Kitabın içine, NEYİN NİÇİN değiştiğini anlatan bir sayfa ekler.

    Dosya elden ele dolaşacağı için kaydın dosyanın DIŞINDA durması yetmez;
    açan herkes hangi hücrenin niçin değiştiğini görebilmelidir.
    """
    if DUZELTME_SAYFASI in wb.sheetnames:
        del wb[DUZELTME_SAYFASI]
    ws = wb.create_sheet(DUZELTME_SAYFASI)
    ws.column_dimensions["A"].width = 4
    ws.column_dimensions["B"].width = 38
    ws.column_dimensions["C"].width = 34
    ws.column_dimensions["D"].width = 30
    ws.column_dimensions["E"].width = 76
    ws.column_dimensions["F"].width = 76
    ws["A1"] = "BU KİTAP DÜZELTİLMİŞTİR"
    ws["A2"] = (f"Üreten: {IMZA}   ·   Tarih: {date.today():%d.%m.%Y}   ·   "
                "Kaynak: templates/MUKAVEMET_HESABI.xlsx ( özgün hâli korunur )")
    ws["A3"] = ("Aşağıdaki hücrelerin FORMÜLLERİ değiştirilmiştir;  değerleri "
                "değil.  Kitap kendi kendini hesaplamaya devam eder.")
    #  1)  NİÇİN  —  sapmaların gerekçesi
    ws["A5"] = "NİÇİN DEĞİŞTİ"
    basliklar = ("#", "Konu", "Dayanak", "Sonucu değişen hücreler",
                 "Kitabın yaptığı", "Düzeltilmiş hâli")
    for j, b in enumerate(basliklar, start=1):
        ws.cell(row=6, column=j, value=b)
    satir = 7
    for i, (ad, madde, eski, yeni, hucreler) in enumerate(MK.EXCEL_FARKLARI, 1):
        ws.cell(row=satir, column=1, value=i)
        ws.cell(row=satir, column=2, value=ad)
        ws.cell(row=satir, column=3, value=madde)
        ws.cell(row=satir, column=4,
                value=", ".join(hucreler) if hucreler else "—")
        ws.cell(row=satir, column=5, value=eski.replace("\n", " "))
        ws.cell(row=satir, column=6, value=yeni.replace("\n", " "))
        satir += 1

    #  2)  NE  —  gerçekten düzenlenen hücreler  ( özgünle fark alınarak )
    satir += 2
    ws.cell(row=satir, column=1,
            value=f"DÜZENLENEN HÜCRELER  ( {len(degisen)} adet )")
    satir += 1
    for j, b in enumerate(("Sayfa", "Hücre", "Kitapta", "Şimdi"), start=1):
        ws.cell(row=satir, column=j, value=b)
    satir += 1
    for sayfa, hucre, eski, yeni in degisen:
        ws.cell(row=satir, column=1, value=sayfa)
        ws.cell(row=satir, column=2, value=hucre)
        ws.cell(row=satir, column=3, value=_kisalt(eski))
        ws.cell(row=satir, column=4, value=_kisalt(yeni))
        satir += 1
    return ws


def _kisalt(v, n=900):
    """Hücreye yazılabilir hâle getirir  ( ω formülleri çok uzundur )."""
    if v is None:
        return "( boş )"
    m = str(v)
    return m if len(m) <= n else m[:n] + " …"


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
TABLOLAR = "TABLOLAR"
ASKI = "Askı Tipleri"

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
    #  Kaynak kitapta karşılığı olmayan üç yeni girdi
    ("toplam_verim",          240, "Ofis verimi η toplam sistem verimidir",
     "EVET / HAYIR"),
    ("agirlik_guvenlik_tertibati", 241, "Karşı ağırlıkta güvenlik tertibatı", "—"),
    ("guvenlik_devreye_kuvvet", 242,
     "Güv. tertibatını devreye sokma kuvveti  ( imalatçı )", "N"),
    #  TS EN 81-50'nin Ek C bağıntılarında bulunup kitapta hiç olmayanlar
    ("paten_tipi",            243, "Paten tipi  ( m.5.10.5 flanş formülü )", "—"),
    ("klips_itme_kuvveti",    244,
     "Fp — konsol klipslerinin itme kuvveti  ( Ek C.2.1.2 )", "N"),
    ("yapi_sehim_x",          245, "δstr-x — bina yapısının x sehimi", "mm"),
    ("yapi_sehim_y",          246, "δstr-y — bina yapısının y sehimi", "mm"),
    ("reg_devreye_hizi",      247, "Regülatör devreye girme hızı  ( imalatçı )", "m/s"),
)
EK_GIRDI_ANAHTARLARI = tuple(a for a, *_x in EK_GIRDI_HUCRELERI)

#  PROJENİN OFİS SABİTLERİ.  Bunlar da kaynak kitapta yoktur ve proje
#  dosyasının bir parçasıdır:  σem = 100 ile "UYGUN DEĞİL" çıkan bir proje,
#  Excel'e aktarılıp geri okunduğunda varsayılan 130'a dönüyor ve "UYGUN"
#  oluyordu — aynı projenin sonucu dosyadan geçince değişiyordu.
OFIS_BASLIK = 249
OFIS_BAS = 251
#  Blok, başlık metni ARANARAK bulunur:  yukarıdaki ek girdi listesi büyürse
#  başlık aşağı kayar ve konuma çivili bir okuyucu ESKİ dosyaları okuyamaz
#  olurdu.  Arama penceresi iki yönde de yeterince geniştir.
OFIS_ARAMA = range(230, 275)
OFIS_BASLIK_ONEK = "PROJENİN OFİS SABİTLER"
#  Onay kutuları Excel'de metin olarak durur — projeci hücreyi elle de
#  düzeltebilsin diye "EVET / HAYIR" yazılır, geri okunurken çözülür.
EK_ONAY_ALANLARI = ("mk_yok",)
#  Metin olarak yazılıp okunan ek girdiler ( sayıya çevrilmemeli )
EK_METIN_ALANLARI = ("toplam_verim", "agirlik_guvenlik_tertibati",
                     "paten_tipi")
_EVET = ("evet", "e", "var", "true", "1", "x", "✓")


def _ofis_yaz(vg, g):
    """Projenin ofis sabitlerini teslim kopyasına yazar.

    YALNIZ VARSAYILANDAN FARKLI OLANLAR yazılır:  dosya kalabalıklaşmasın ve
    ofis varsayılanını değiştirdiğinde eski projeler yeni varsayılanı değil,
    KENDİ değerlerini kullanmaya devam etsin — ama dokunulmamış alanlar
    ofisin güncel kabulünü izlesin.
    """
    ofis = g.get("_ofis") if isinstance(g.get("_ofis"), dict) else {}
    ozel = {k: v for k, v in ofis.items()
            if k in US.VARSAYILAN and v is not None and v != US.VARSAYILAN[k]}
    vg[f"A{OFIS_BASLIK}"] = ("PROJENİN OFİS SABİTLERİ  ( yalnız varsayılandan "
                             "FARKLI olanlar yazılır )")
    for i, (anahtar, deger) in enumerate(sorted(ozel.items())):
        satir = OFIS_BAS + i
        vg[f"A{satir}"] = US.ETIKET.get(anahtar, (anahtar,))[0]
        vg[f"B{satir}"] = deger
        vg[f"C{satir}"] = anahtar


def _ofis_basligi(vg):
    """Ofis sabitleri bloğunun başlık satırını bulur  ( yoksa None )."""
    for r in OFIS_ARAMA:
        if str(vg[f"A{r}"].value or "").strip().startswith(OFIS_BASLIK_ONEK):
            return r
    return None


def _ofis_oku(vg):
    """Teslim kopyasındaki proje sabitlerini geri okur."""
    baslik = _ofis_basligi(vg)
    if baslik is None:
        return {}
    bas = baslik + (OFIS_BAS - OFIS_BASLIK)
    d = {}
    for r in range(bas, bas + len(US.VARSAYILAN) + 2):
        anahtar = vg[f"C{r}"].value
        if anahtar in (None, ""):
            continue
        anahtar = str(anahtar).strip()
        if anahtar not in US.VARSAYILAN:
            continue
        deger = vg[f"B{r}"].value
        if deger in (None, ""):
            continue
        d[anahtar] = deger if anahtar in US.METIN else _ek_deger_oku(anahtar, deger)
    return {k: v for k, v in d.items() if v is not None}


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


#  Beyan yükü açılır listesinin kitaptaki kaynağı ve ilk boş satırı.
BEYAN_LISTE_SUTUN = "S"
BEYAN_LISTE_BAS = 2
BEYAN_LISTE_HUCRE = "C59"


ELEKTRIK = "12-Elk.Hesapları"


#  TABLOLAR!D47:G52  —  kanal şekli · açı · Nequiv(t)
KANAL_TABLO_SATIRI = {
    "V Kanal": 47, "Altı Kesik V Kanal": 48, "Yarım Daire Kanal": 49,
    "Altı Kesik Yarım Daire Kanal": 50, "Yarım Daire Kanal (Çift Sarım)": 52,
}


def _kanal_tablosu(wb, O):
    """Kanal tablosunu projenin kendi γ / β açılarıyla yeniden yazar."""
    if TABLOLAR not in wb.sheetnames:
        return
    tb = wb[TABLOLAR]
    for ad, satir in KANAL_TABLO_SATIRI.items():
        #  Çizelge 2'de belirleyici açı:  V ve altı kesik V'de γ, altı kesik
        #  yarım dairede β, alt kesilmesiz yarım dairede yok.
        _tur = MT.kanal_turu(ad)
        aci = (O["kanal_beta"] if _tur == "UK"
               else (None if _tur == "U" else O["kanal_gama_v"]))
        tb[f"F{satir}"] = aci
        tb[f"G{satir}"] = MT.kanal_nequiv_t(ad, O["kanal_gama_v"], O["kanal_beta"])


#  'Askı Tipleri' sayfasında MSR'nin ± işaretini taşıyan hücreler.
#  ( hücre , kitaptaki parça , doğrusu )
MSR_DUZELTME = (
    ("M119", "0.5*M130-M131", "0.5*M130+M131"),   # %125 yüklü kabin EN ALTTA
    ("M120", "0.5*M130+M132", "0.5*M130-M132"),
    ("N119", "0.5*N130-N131", "0.5*N130+N131"),   # yüklü kabin tampona oturmuş
    ("N120", "0.5*N130+N132", "0.5*N130-N132"),
    ("P119", "0.5*P130-P131", "0.5*P130+P131"),   # %100 yüklü kabin EN ALTTA
    ("P120", "0.5*P130+P132", "0.5*P130-P132"),
    ("Q119", "0.5*Q130+Q131", "0.5*Q130-Q131"),   # boş kabin EN ÜSTTE
    ("Q120", "0.5*Q130-Q132", "0.5*Q130+Q132"),
)


def _msr_dagilimi(wb):
    """Halat kütlesinin taraf dağılımındaki ters ± işaretlerini düzeltir."""
    if ASKI not in wb.sheetnames:
        return
    at = wb[ASKI]
    for hucre, eski, yeni in MSR_DUZELTME:
        d = at[hucre].value
        if isinstance(d, str) and eski in d:
            at[hucre] = d.replace(eski, yeni)


def _elektrik_sayfasi(wb, g):
    """Kitabın elektrik sayfasını programın girdileriyle doldurur.

    Kitap bu sayfayı kendi sabitleriyle hesaplıyordu;  programın ekrandaki
    sonucuyla ilgisi yoktu.  Hangi hücrenin ne olduğu W26…W35 blokunda
    yazılıdır ( "L1 · L2 · U · e · Pm · PTAS · K · S1 · S2 · ηm" ).
    """
    if ELEKTRIK not in wb.sheetnames:
        return
    ws = wb[ELEKTRIK]
    O = US.sabitler(g.get("_ofis"))
    S1, S2 = g.get("kolon_kesit"), g.get("makine_kesit")
    L1, L2 = g.get("kolon_uzunluk"), g.get("makine_uzunluk")
    for hucre, deger in (("W27", L2), ("W28", O["U"]), ("W29", O["eps_max"]),
                         ("W32", O["kappa"]), ("W33", S1), ("W34", S2),
                         ("W35", O["motor_elektrik_verimi"]),
                         ("X58", O["cosfi"]), ("X63", O["cosfi"])):
        if deger is not None:
            ws[hucre] = deger
    #  L1 boş bırakılmışsa kitabın kendi formülü kalsın:  o da kuyu boyundan
    #  türetir.  Girilmişse programın kullandığı değer yazılır.
    if L1 is not None:
        ws["W26"] = L1
    #  KABLO TAŞIMA KAPASİTELERİ hücreye sabit yazılıydı ( 43 / 34 A ) ve
    #  seçilen kesitle ilgisi yoktu;  AB60 ve AH65'teki UYGUN / UYGUN DEĞİL
    #  kararları bu sabitlerden çıkıyordu.
    tip = O.get("kablo_tipi") or ""
    for hucre, ad_hucre, kesit, etiket in (
            ("S60", "A60", S1, "AT-TAS arası"),
            ("Y65", "A65", S2, "TAS - Asansör motoru arası")):
        if kesit is None:
            continue
        iz, kesin = AV_TAB.kablo_iz_sinir(kesit)
        if iz is not None:
            ws[hucre] = iz
            ws[ad_hucre] = (f"{etiket} seçilen {kesit} mm² {tip} kablo"
                            + ("" if kesin else "  ( kesit tablo dışı — alt sınır )"))


def _liste_tamamla(wb):
    """Beyan yükü açılır listesini EN 81-20 Çizelge 6'ya tamamlar.

    Kitaptaki liste KAPALIDIR:  içinde olmayan bir yük Excel'de seçilemez.
    Standardın 28 yükünden 7'si listede yoktu ( 100 · 1050 · 1250 · 1350 ·
    1425 · 1500 · 2500 kg ) — 1250 ve 1500 yaygın asansörlerdir.

    Listenin ilk 17 satırı TEKNİK sayfasına BAĞLIDIR ( "=TEKNİK!A2" … );
    okunabilmesi için o başvurular çözülür.  Blok ilk boş satırda biter —
    aşağıda S42/S43'te BAŞKA bir liste vardır, ona dokunulmamalıdır.
    """
    vg = wb[GIRDI]
    var, satir = set(), BEYAN_LISTE_BAS
    while True:
        d = vg[f"{BEYAN_LISTE_SUTUN}{satir}"].value
        if d in (None, ""):
            break
        if isinstance(d, str) and d.startswith("="):
            sayfa, _, hucre = d[1:].partition("!")
            if sayfa in wb.sheetnames:
                d = wb[sayfa][hucre].value
        if isinstance(d, (int, float)) and not isinstance(d, bool):
            var.add(float(d))
        satir += 1
    eksik = [q for q in (k[0] for k in MT.KABIN_ALANI) if float(q) not in var]
    if not eksik:
        return
    for i, q in enumerate(eksik):
        vg[f"{BEYAN_LISTE_SUTUN}{satir + i}"] = q
    aralik = (f"${BEYAN_LISTE_SUTUN}${BEYAN_LISTE_BAS}:"
              f"${BEYAN_LISTE_SUTUN}${satir + len(eksik) - 1}")
    for dv in list(vg.data_validations.dataValidation):
        if BEYAN_LISTE_HUCRE in str(dv.sqref):
            dv.formula1 = aralik


def _verim_formulu(O):
    """η′  =  makine tipi tablosu  −  palangalı sistemde düşüş.

    Tablo ve düşüş PROJENİN ofis sabitlerinden okunur ( uygulama projesinin
    kendi Sabitler sekmesi ) — böylece ekranda değiştirilen verim teslim
    edilen kitapta da geçerli olur, pafta ile kitap ayrışmaz.
    """
    tip, askı = "'Veri Girişi'!B130", "'Veri Girişi'!B100"
    #  Tablo iki satırlık olduğu için iç içe IF yeterli;  tanınmayan tipte
    #  ortak fabrika ayarına düşülür.
    ic = repr(float(OFIS.VARSAYILAN_VERIM))
    for ad, anahtar in (("Dişli", "verim_disli"), ("Dişlisiz", "verim_dislisiz")):
        ic = f'IF({tip}="{ad}",{float(O[anahtar])!r},{ic})'
    return f"=({ic})-IF({askı}>1,{float(O['palanga_verim_dususu'])!r},0)"


def _standarda_uydur(wb, g):
    """Kaynak kitabın standarttan sapan formüllerini teslim kopyasında düzeltir."""
    ws, vg = wb[HESAP], wb[GIRDI]
    #  Projenin KENDİ ofis sabitleri:  ekranda değiştirilen verim, σem ve
    #  paylar teslim edilen kitaba da yansımalı.
    O = US.sabitler(g.get("_ofis"))

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

    #  ㉔  BOŞ KABİNİN AĞIRLIK MERKEZİ RAY EKSENİNDEN ÖLÇÜLÜR
    #  EN 81-50 Ek C.1.2:  "xp, yp is the position of the car mass (P) in
    #  relation to the guide rail cross coordinates" — xC ve xQ ile AYNI
    #  orijin.  Kitap xp'yi kabin merkezinden ölçüyor ( yalnız kapı kütlesi ),
    #  gövdenin ray eksenine göre kaçıklığını ( AH293 = xc ) saymıyordu.
    #  Formül CANLI bırakılır:  kitapta kabin derinliği ya da ray–kapı arası
    #  değiştirildiğinde xp de takip etsin.
    ws["AH295"] = ("=AH293-(('Veri Girişi'!F127*(('Veri Girişi'!C74/2)"
                   "+'Veri Girişi'!F128))/'Veri Girişi'!C75)")

    #  ㉜ ( devamı )  YÜKLEME DURUMUNDA σ VE δ BÜYÜKLÜKTÜR
    #  xi işaretli hâle gelince Fx negatife düşebiliyor.  Gerilme ve sehim
    #  YÖNDEN BAĞIMSIZ büyüklüklerdir ( üçüncü denetim, motorda abs ile );
    #  kitabın hücreleri işaretli hesaplıyordu:  "δ ≤ 5 mm" karşılaştırması
    #  negatif bir sehimi SESSİZCE geçirirdi.  Kuvvet satırları ( L508 · L516 )
    #  işaretini korur — yön bilgisi paftada kalsın diye.
    #  ÜÇ YÜK DURUMUNUN DA σ ve δ HÜCRELERİ.  Kuvvet ve moment satırları
    #  ( AY321 · L415 · L508 … ) işaretini KORUR — yön bilgisi paftada
    #  kalsın diye;  yalnız büyüklük olan satırlar sarılır.
    for _h in (
            #  C.2.1  güvenlik tertibatı  ( Durum 1 · Durum 2 )
            "AU324", "AU330", "Z360", "AJ362", "AE365", "Z379", "AH393", "AH396",
            "AU338", "AU347", "Z369", "AJ371", "AE374", "Z384", "AH401", "AH404",
            #  C.2.2  normal işletme
            "AU418", "AU427", "Z461", "AC463", "Z476", "AH487", "AH490",
            "AU438", "AU447", "Z468", "AH470", "Z481", "AH495", "AH498",
            #  C.2.3  yükleme
            "AU511", "AU519", "Z530", "AF532", "Z537", "AH542", "AH545",
            #  karşı ağırlık rayı
            "AU575", "Z588", "AF590", "AH603", "AH606"):
        _f = ws[_h].value
        if isinstance(_f, str) and _f.startswith("=") and not _f.startswith("=ABS("):
            ws[_h] = "=ABS(" + _f[1:] + ")"

    #  ㉜  KAPI KONUMU xi RAY EKSENİNDEN ÖLÇÜLÜR  —  EN 81-50 Ek C.1.2
    #  Kitap oraya ray–kapı arasını HAM MESAFE yazar;  oysa aynı toplamdaki
    #  xp işaretli bir konumdur ve kapı, ray ekseninin ters tarafındadır.
    ws["AH299"] = "=-'Veri Girişi'!F112"

    #  ㉛  YÜK EN OLUMSUZ KONUMDA  —  EN 81-20 m.5.7.2.3.4
    #  Kitap yükü yalnız + yönde kaydırır ( xQ = xc + D/8 ).  Madde normatif
    #  olarak "most unfavourable position" der;  kabin merkezi ray ekseninin
    #  öbür yanındaysa + yön boş kabinin momentini DENGELER ve gerilmeyi
    #  olduğundan küçük gösterir.  Formül CANLI kalır:  kitapta kabin ölçüsü
    #  ya da ray–kapı arası değişince yön kendiliğinden yeniden seçilir.
    _Q, _P, _xp = "'Veri Girişi'!C59", "'Veri Girişi'!C75", "AH295"
    _xc, _yc = "AH293", "0"
    _dx, _dy = "('Veri Girişi'!C74/8)", "('Veri Girişi'!C73/8)"
    ws["Z309"] = (f"=IF(ABS({_Q}*({_xc}+{_dx})+{_P}*{_xp})"
                  f">=ABS({_Q}*({_xc}-{_dx})+{_P}*{_xp}),"
                  f"{_xc}+{_dx},{_xc}-{_dx})")
    #  Durum 2'de yc = 0 ve yp = 0'dır;  yük momenti simetriktir, iki yön de
    #  aynı büyüklüğü verir — kitabın + yönü olduğu gibi kalır.

    #  ㉖  Fy'NİN PAYDASI  ( n / 2 ) · h
    #  EN 81-50 Ek C.2.1.1 b) · C.2.2.1 b) · C.2.3.1 b) üçünde de Fy'yi
    #  ( n/2 )·h'ye böler.  Kitap yalnız güvenlik tertibatı durumunda doğru
    #  paydayı kullanıyor, normal işletme · yükleme ve karşı ağırlıkta n·h
    #  yazıyordu:  Fy gerçeğin YARISI çıkıyordu ( emniyetsiz ).
    for _h in ("C425", "C445", "C517"):
        ws[_h] = ws[_h].value.replace("=", "=(", 1).replace("*", "/2)*", 1)
    ws["AP572"] = "=(T572*W572*AA572*(AF572-AI572))/((Y573/2)*AB573)"

    #  ⑭  Kuyu tabanı yükünde ray ağırlığı bir kez sayılır
    #  Kitap  AX611 = gn·Gr·LR/1000 + MY + AU351  yazar;  AU351 ( bölüm 7'nin
    #  Fv'si ) zaten  AK351·AM351 = Mg·gn  içerir, yani ray hattının ağırlığı
    #  aynı toplamda İKİ KEZ sayılır.  TS EN 81-20 m.5.2.1.8.4 kalemleri tek
    #  tek sayar:  ray kütlesi ayrı, güvenlik tertibatı tepkisi ayrıdır.
    ws["AO611"] = "=AU351-AK351*AM351"

    #  ㉜  Fp ( KLİPS İTME KUVVETİ ) CANLI HÜCRELERE BAĞLANIR
    #  Ek C.2.1.2 / C.2.2.2 / C.2.3.2 uyarınca Fv = Mg·gn + Fp'dir.  Şablonda
    #  bu hücreler ( AP351, X452, X580 ) sabit 0 yazılıydı.  Artık Veri Girişi'ndeki
    #  B244 hücresine canlı bağlanır.
    ws["AP351"] = "='Veri Girişi'!B244"
    ws["X452"] = "='Veri Girişi'!B244"
    ws["X580"] = "='Veri Girişi'!B244"

    #  ㉝  KARŞI AĞIRLIKTA GÜVENLİK TERTİBATI VARSA δperm = 5 mm
    #  TS EN 81-20 m.5.7.4.6 a) uyarınca karşı ağırlıkta güvenlik tertibatı
    #  varsa izin verilen sehim 10 mm değil 5 mm'dir.
    ws["AL600"] = "=IF('Veri Girişi'!B241=\"Yok\",10,5)"
    ws["AL603"] = "=IF('Veri Girişi'!B241=\"Yok\",10,5)"

    #  ⑬  ELEKTRİK SAYFASI PROGRAMIN GİRDİLERİNİ KULLANIR
    #  Kitabın '12-Elk.Hesapları' sayfası kendi sabitleriyle çalışıyordu:
    #  L2 = 5 m · U = 400 V · S1 = 6 · S2 = 4 mm² · cosφ = 0,8 ve kablo
    #  taşıma kapasiteleri 43 / 34 A olarak HÜCREYE YAZILIYDI.  Programın
    #  girdileriyle hiçbiri aynı değildi;  ekran ile teslim edilen kitap
    #  farklı hesap yapıyordu.  Artık aynı sayıları kullanırlar.
    _elektrik_sayfasi(wb, g)

    #  ⑩  Beyan yükü listesi EN 81-20 Çizelge 6'ya tamamlanır
    #  Kitabın açılır listesi ( 'Veri Girişi'!$S$2:$S$23 ) standardın 28
    #  yükünden 7'sini içermiyordu;  o yüklerde kitapla hesap yapılamıyordu.
    #  Eksik yükler listenin sonuna yazılır ve doğrulama aralığı genişletilir.
    _liste_tamamla(wb)

    #  ⑨  Motor verimi makine tipine bağlanır  —  ofis standardı
    #  Kitap 11!AQ22'ye sabit 0,92 yazar ve 'Veri Girişi'!B130'daki makine
    #  tipini hiç okumaz.  Teslim kopyasında AQ22 bir FORMÜL olur:  Excel'de
    #  makine tipi ya da askı oranı değiştirilirse verim de takip eder.
    ws["AQ22"] = _verim_formulu(O)

    #  ⑮  KABİN ÖNÜ GİRİNTİSİ TAMAMEN SAYILIR  —  EN 81-20 m.5.4.2.1.3
    #  Kitap ( 11!X84 ) girintiye kapı genişliğinin YARISINI katıyor ve eşiği
    #  "≥ 100 mm" tutuyordu.  Standart:  ≤ 100 mm hariç, > 100 mm ise
    #  "the TOTAL available area shall be included".
    ws["X84"] = ("=IF('Veri Girişi'!F69>100,"
                 "(('Veri Girişi'!C73*'Veri Girişi'!C74)"
                 "+('Veri Girişi'!C71*'Veri Girişi'!F69))/1000000,"
                 "('Veri Girişi'!C73*'Veri Girişi'!C74)/1000000)")

    #  ⑯  "Sf ≥ Smin" BİR GEÇME ÖLÇÜTÜ DEĞİLDİR  —  EN 81-20 m.5.5.2.2
    #  Kitap ( 11!AH125 ) bunu UYGUN / UYGUN DEĞİL diye yazıyor ve standarda
    #  uyan tasarımları reddediyordu.  Tek ölçüt bir altındaki satırdır:
    #  S ≥ MAX( Sf ; Smin ) — o zaten AH126'da doğru kurulu.
    ws["AH125"] = ('=IF(T125>=X125,"Sf belirleyicidir  ( ölçüt: S ≥ Sf ).",'
                   '"Smin belirleyicidir  ( ölçüt: S ≥ Smin ).")')

    # Asgari adet, kopma güvenliğinden bağımsızdır. Excel'deki elle
    # değişiklikler de tek halatı uygun gösterememeli.
    ws["AH110"] = '=IF(AQ20=2,16,12)'
    ws["AH126"] = '=IF(OR(AQ20<2,AQ20<>INT(AQ20)),"UYGUN DEĞİLDİR — en az 2 tam adet askı halatı",IF(T126>=X126,"UYGUNDUR.","UYGUN DEĞİLDİR."))'

    #  ⑰  Nequiv(t) OFİS AÇILARINI İZLER  —  EN 81-50 Çizelge 2
    #  Kitabın tablosu ( TABLOLAR!D47:G52 ) her kanal şeklinin karşısına tek
    #  bir açı ve tek bir Nequiv(t) çiviler;  ofis sabiti γ ya da β
    #  değiştiğinde kımıldamaz.  Teslim kopyasında satırlar projenin kendi
    #  açılarıyla yeniden yazılır.
    _kanal_tablosu(wb, O)

    #  ⑱  HALAT KÜTLESİNİN TARAF DAĞILIMI  —  EN 81-50 m.5.11.2.2
    #  Kitap dört yük durumunun üçünde ± işaretini ters yazıyordu:  kabin en
    #  altta iken halat kütlesinin tamamını karşı ağırlık tarafına koyuyordu.
    _msr_dagilimi(wb)

    #  ⑲  Mil kuvveti ve moment askı oranına göre indirgenir
    #  2:1 palangada tahrik kasnağının gördüğü kuvvet Gmax değil Gmax/i'dir.
    ws["AQ7"] = "=(AQ11-AQ13)/'Veri Girişi'!B100"
    ws["AQ21"] = "=(AQ9/'Veri Girişi'!B100)*(AQ10/2000)"

    #  ⑳  REGÜLATÖR:  ÇEKME KUVVETİ VE İKİNCİ SINIR
    #      m.5.6.2.2.1.1 d)  regülatörün ÜRETTİĞİ kuvveti sınırlar — kasnağın
    #                        iki yanındaki gerginlik FARKI:  F'reg − Freg.
    #                        Güvenlik tertibatını çeken odur;  halatın statik
    #                        gergisi Freg zaten oradadır ve bir şey çekmez.
    #      m.5.6.2.2.1.3 b)  halattaki EN BÜYÜK gerginliği ( F'reg ) emniyet
    #                        katsayısına sokar.
    #  Kitap ikisini de F'reg ile yapıyor ( U156 = J156 ) ve sınıra "2 × Freg"
    #  koyuyordu.  Devreye sokma kuvveti İMALATÇI VERİSİDİR;  girilmezse madde
    #  denetlenemez ve kitap da "HESAP EKSİK" yazar.
    #
    #  SINIR DA FORMÜLDÜR:  kitabı Excel'de açıp B242'yi dolduran biri doğru
    #  sonucu görsün — sabit yazılsaydı karar satırı değişir, sınır 300'de
    #  kalırdı.
    _B242 = "'Veri Girişi'!B242"
    _eksik = f'OR({_B242}="",{_B242}<=0)'
    ws["Q156"] = "Fçekme"
    ws["U156"] = "=J156-W151"
    ws["G161"] = "=AI136/J156"
    ws["AA156"] = (f'=IF({_eksik},{MK.SABIT["reg_kuvvet_asgari"]},'
                   f'MAX({MK.SABIT["reg_kuvvet_asgari"]},2*{_B242}))')
    ws["AM156"] = (f'=IF({_eksik},"HESAP EKSİK",'
                   'IF(U156>=AA156,"UYGUNDUR.","UYGUN DEĞİLDİR."))')

    #  ㉑  KARŞI AĞIRLIK DENGE ORANI  —  ofis sabiti q
    #  Kitabın C80 formülü "C75 + C59/2" diye ÇİVİLİDİR;  ofis q'yu
    #  değiştirse bile 0,50 kalır ve teslim edilen kitap ekrandan başka bir
    #  karşı ağırlık kullanır.  Formül projenin q'suyla yazılır — sayı değil
    #  FORMÜL, kitap kendi kendini hesaplamaya devam etsin diye.
    vg["C80"] = f"=C75+(C59*{repr(float(O['q_denge']))})"

    #  ㉒  KARŞI AĞIRLIK GÜVENLİK TERTİBATININ TABAN TEPKİSİ
    #  Kitapta karşı ağırlık güvenlik tertibatı diye bir girdi yoktur;  bu
    #  yüzden AN616 ( FAR ) tepkiyi hiç saymaz.  Tertibat seçilmişse tepki
    #  ayrı bir kalem olarak eklenir ( EN 81-20 m.5.2.1.8.4 ).
    _agt = MK.US.darbe_k1(O, g.get("agirlik_guvenlik_tertibati")) \
        if (g.get("agirlik_guvenlik_tertibati") or "Yok") != "Yok" else None
    if _agt:
        #  k1 · gn · Mcwt / n   —  ray kütlesi bu kalemde YOKTUR
        ws["AN616"] = ("=(U616*Y616*AC616/U617)+AG616+"
                       f"({repr(float(_agt))}*{MK.SABIT['gn']}"
                       "*'Veri Girişi'!C80/'Veri Girişi'!B116)")

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
    _ofis_yaz(vg, g)
