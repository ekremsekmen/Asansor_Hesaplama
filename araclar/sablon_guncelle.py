# -*- coding: utf-8 -*-
"""
ŞABLON GÜNCELLEME  —  v1.3

İki Excel şablonuna, Python motoruyla BİREBİR aynı davranışı verecek
değişiklikleri uygular.  Satır/sütun KAYDIRMAZ; yalnız boş hücrelere yazar ve
belirli formülleri yeniden yazar — böylece mevcut hiçbir formül bozulmaz.

Yapılanlar
  1  Tablo-4'e 1000 ve 1200 mm satırları (komşulardan enterpolasyon)
  2  Tablo-8'e 700 mm sütunu (800→900 eğiminden dış değerleme)
  3  Tablo-7 karşılıklarına 15 kişi / 1125 kg örnek istisnası
  4  Bodrum durak adedi girdisi (tek + çoklu, ortak + asansör bazında)
  5  Çoklu sayfada asansör bazında manuel ta / tk / tg / tp
  6  Avan GİRİŞ'te asansör bazında palanga (i) ve denge faktörü (q)
  7  Pafta sayfalarına bodrum ve seyahat mesafesi bilgisi

Çalıştırma:  python3 araclar/sablon_guncelle.py
"""
import os
import shutil
import sys
from copy import copy

import openpyxl
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.datavalidation import DataValidation

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TRAFIK = os.path.join(KOK, "templates", "ASANSOR_TRAFIK_HESABI_v2_1.xlsx")
AVAN = os.path.join(KOK, "templates", "ASANSOR_AVAN_HESAPLARI.xlsx")


# ------------------------------------------------------------------ yardımcı
def stil_kopyala(ws, kaynak, hedef):
    k, h = ws[kaynak], ws[hedef]
    h._style = copy(k._style)


def satir_stili(ws, kaynak_satir, hedef_satir, sutunlar):
    for c in sutunlar:
        stil_kopyala(ws, f"{c}{kaynak_satir}", f"{c}{hedef_satir}")
    if kaynak_satir in ws.row_dimensions:
        ws.row_dimensions[hedef_satir].height = ws.row_dimensions[kaynak_satir].height


def birlesimi_kaldir(ws, aralik):
    if aralik in [str(m) for m in ws.merged_cells.ranges]:
        ws.unmerge_cells(aralik)


def dv_ekle(ws, aralik, **kw):
    """Aynı aralığa daha önce eklenmiş doğrulamayı temizleyip yenisini kurar."""
    for dv in list(ws.data_validations.dataValidation):
        if str(dv.sqref) == aralik:
            ws.data_validations.dataValidation.remove(dv)
    dv = DataValidation(**kw)
    ws.add_data_validation(dv)
    dv.add(aralik)
    return dv


def degistir(ws, hucre, eski, yeni, zorunlu=True):
    """Bir formülün içindeki metin parçasını değiştirir."""
    v = ws[hucre].value
    if not isinstance(v, str) or eski not in v:
        if zorunlu:
            raise AssertionError(f"{ws.title}!{hucre} içinde bulunamadı: {eski[:60]}")
        return False
    ws[hucre] = v.replace(eski, yeni)
    return True


# ==================================================================
#  1)  TRAFİK  —  TABLO-4  :  1000 ve 1200 mm satırları
# ==================================================================
def tablo4_guncelle(wb):
    ws = wb["TABLO-4"]
    not_metni = ws["A9"].value
    birlesimi_kaldir(ws, "A9:G9")
    ws["A9"] = None

    #  genişlik : (tel_ta, tel_tk, mrk_ta, mrk_tk, kab_ta, kab_tk)
    satirlar = [
        (700,  2.5, 3.0, 2.0, 2.5, 5.0, 5.0),
        (800,  2.5, 3.0, 2.0, 2.5, 5.0, 5.0),
        (900,  2.5, 3.8, 2.3, 2.9, 5.0, 5.0),
        (1000, 2.75, 3.9, 2.4, 3.2, 5.5, 5.5),      # ara değer
        (1100, 3.0, 4.0, 2.5, 3.5, 6.0, 6.0),
        (1200, 3.35, 4.5, 2.6, 3.6, None, None),    # ara değer
        (1300, 3.7, 5.0, 2.7, 3.7, None, None),
    ]

    def tr_sayi(x):
        if x is None:
            return "YOK"
        return str(x).replace(".", ",") if x != int(x) else str(int(x))

    for i, (g, *v) in enumerate(satirlar):
        r = 4 + i
        if r > 8:                                   # yeni satır — stil kopyala
            satir_stili(ws, 5, r, list("ABCDEFGHIJKLMN"))
        ws[f"A{r}"] = g
        for j, deger in enumerate(v):               # görünen (metin) sütunlar B..G
            ws[f"{get_column_letter(2 + j)}{r}"] = ("YOK" if deger is None
                                                    else tr_sayi(deger))
        for j, deger in enumerate(v):               # sayısal sütunlar I..N
            ws[f"{get_column_letter(9 + j)}{r}"] = "YOK" if deger is None else deger

    ws["A11"] = (not_metni + "   |   1000 ve 1200 mm satırları MMO/697 Tablo-4'te "
                 "BASILI DEĞİLDİR; komşu satırlar arasında doğrusal enterpolasyonla "
                 "türetilmiştir ( 1000 = (900+1100)/2 ,  1200 = (1100+1300)/2 ) — "
                 "Tablo-6'daki 1,75 ve 3,00 m/s ara değerleriyle aynı yöntem. "
                 "'Kabin İçi Oto. Kat K.Ç.' sütunu 1300 mm'de tabloda bulunmadığından "
                 "1200 mm için de üretilememiştir; bu iki hücrede imalatçı değeri "
                 "elle girilmelidir.")
    stil_kopyala(ws, "A9", "A11")
    ws.merge_cells("A11:G11")
    ws.row_dimensions[11].height = 60
    print("  · TABLO-4  →  1000 ve 1200 mm satırları eklendi (7 satır, A4:N10)")


# ==================================================================
#  2)  TRAFİK  —  TABLO-8  :  700 mm sütunu
# ==================================================================
def tablo8_guncelle(wb):
    ws = wb["TABLO-8"]
    genislikler = [700, 800, 900, 1000, 1100, 1200, 1300]
    tp = [1.3, 1.2, 1.1, 1.0, 1.0, 0.9, 0.9]
    stil_kopyala(ws, "G1", "H1")
    stil_kopyala(ws, "G2", "H2")
    for i, (g, t) in enumerate(zip(genislikler, tp)):
        c = get_column_letter(2 + i)
        ws[f"{c}1"] = g
        ws[f"{c}2"] = t
    ws["A8"] = ("700 mm ISO 8100-32:2020 Tablo 6'da ve Barney/Peters tablolarında YOKTUR "
                "(tablo 800 mm'de başlar, ayrıca 700 mm TS EN 81-70 erişilebilirlik "
                "asgarisi olan 800 mm'nin altındadır). Buradaki 1,3 s değeri 800→900 mm "
                "eğiminden ( −0,1 s / 100 mm ) DOĞRUSAL DIŞ DEĞERLEME ile bulunmuştur; "
                "büyük tp, TR'yi büyüttüğü için emniyetli taraftadır. İmalatçı verisi "
                "varsa manuel tp girilmelidir.")
    print("  · TABLO-8  →  700 mm sütunu eklendi (B1:H2)")


# ==================================================================
#  3)  TRAFİK  —  HESAPLAMA sayfası
# ==================================================================
def hesaplama_guncelle(wb):
    ws = wb["HESAPLAMA"]

    # ---- ⑪ bodrum durak adedi girdisi  (D16 etiket / E16 girdi)
    ws["D16"] = "⑪ Bodrum durak adedi (ana giriş altı) — boş bırakırsanız 0"
    stil_kopyala(ws, "D10", "D16")
    ws["E16"] = None
    stil_kopyala(ws, "E10", "E16")
    dv_ekle(ws, "E16", type="whole", operator="between", formula1=0, formula2=10,
            allow_blank=True, showErrorMessage=True,
            errorTitle="Bodrum durak adedi",
            error="Ana giriş altında hizmet verilen durak adedi: 0 – 10 arası tam sayı "
                  "ya da boş.")

    # ---- gizli yardımcılar (H sütunu)
    ws["H15"] = ("yardımcı (gizli): H16 = efektif bodrum durak adedi   ·   "
                 "H17 = toplam seyahat mesafesi = (N + Nb) · h")
    ws["H16"] = ('=IF(AND(ISNUMBER($E$16),$E$16>=0,$E$16<=10,$E$16=INT($E$16)),$E$16,0)')
    ws["H17"] = ('=IF(AND(ISNUMBER($C$9),ISNUMBER($C$12)),($C$9+$H$16)*$C$12,"")')

    # ---- Tablo-2 asgari hızı : durak = N + 1 + Nb
    v = ws["I68"].value
    assert v.count("($C$9+1)") == 11, v.count("($C$9+1)")
    ws["I68"] = v.replace("($C$9+1)", "($C$9+1+$H$16)")
    ws["B23"] = "V = Kabin hızı (durak adedi = N + 1 + bodrum)"

    # ---- Tablo-4 aralığı 8 → 10 satır  /  Tablo-8 aralığı G → H sütunu
    for r in range(70, 84):
        for c in ("X", "Y"):
            degistir(ws, f"{c}{r}", "'TABLO-4'!$I$4:$N$8", "'TABLO-4'!$I$4:$N$10")
            degistir(ws, f"{c}{r}", "'TABLO-4'!$A$4:$A$8", "'TABLO-4'!$A$4:$A$10")
        degistir(ws, f"Z{r}", "'TABLO-8'!$B$2:$G$2", "'TABLO-8'!$B$2:$H$2")
        degistir(ws, f"Z{r}", "'TABLO-8'!$B$1:$G$1", "'TABLO-8'!$B$1:$H$1")
    for h in ("C26", "C27", "H26", "H27"):
        degistir(ws, h, "'TABLO-4'!$I$4:$N$8", "'TABLO-4'!$I$4:$N$10")
        degistir(ws, h, "'TABLO-4'!$A$4:$A$8", "'TABLO-4'!$A$4:$A$10")
    for h in ("C29", "H29"):
        degistir(ws, h, "'TABLO-8'!$B$2:$G$2", "'TABLO-8'!$B$2:$H$2")
        degistir(ws, h, "'TABLO-8'!$B$1:$G$1", "'TABLO-8'!$B$1:$H$1")

    # ---- Tablo-7 : 15 kişi / 1125 kg örnek istisnası
    degistir(ws, "E13", "IF(C13=13,1000,", "IF(C13=13,1000,IF(C13=15,1125,")
    degistir(ws, "E13", "IF(C13=30,2500,C13*75)))))))))", "IF(C13=30,2500,C13*75))))))))))")
    ws["D13"] = "Yük (kg; 15 kişi = 1125 kg örnek istisnasıdır)"

    # ---- doğrulama zinciri : bodrum + güncel kapı mesajları
    h45 = ws["H45"].value
    eski_ta = ("mm / \"&$C$16&\" için MMO Tablo-4'te ta-tk değeri yok. E26 ve E27 "
               "hücrelerine imalatçı katalog değerini girin veya 800/900/1100/1300 mm seçin.")
    yeni_ta = ("mm / \"&$C$16&\" için Tablo-4'te ta-tk karşılığı yok — 'Kabin İçi Oto. "
               "Kat K.Ç.' sütunu 1200 ve 1300 mm'de tabloda bulunmaz. E26 ve E27 hücrelerine "
               "imalatçı katalog değerini girin ya da kapı tipini değiştirin.")
    assert eski_ta in h45, "H45 ta-tk mesajı bulunamadı"
    h45 = h45.replace(eski_ta, yeni_ta)
    eski_tp = ("mm için Tablo-8'de tp değeri yok (tabloda 800/900/1000/1100/1200/1300 mm "
               "var). E29 hücresine imalatçı değerini girin veya 800/900/1100/1300 mm seçin.")
    yeni_tp = "mm için tp değeri bulunamadı. E29 hücresine imalatçı değerini girin."
    assert eski_tp in h45, "H45 tp mesajı bulunamadı"
    h45 = h45.replace(eski_tp, yeni_tp)
    ws["H45"] = ('=IF(AND($E$16<>"",OR(NOT(ISNUMBER($E$16)),$E$16<0,$E$16>10,'
                 '$E$16<>INT($E$16))),"HESAP HATASI: ⑪ bodrum durak adedi 0 ile 10 arasında '
                 'tam sayı olmalıdır (ana giriş altında hizmet verilen durak adedi).",'
                 + h45.lstrip("=") + ")")

    # ---- kapı genişliği kapsam notu
    ws["E14"] = ("Tüm genişlikler ( 700 – 1300 mm ) hesaplanabilir. MMO Tablo-4'te 1000 ve "
                 "1200 mm, ISO 8100-32 Tablo 6'da 700 mm BASILI DEĞİLDİR; bu değerler komşu "
                 "satırlardan enterpolasyon / dış değerleme ile türetilir ve paftada kaynağı "
                 "'ara değer' olarak yazılır. 'Kabin İçi Oto. Kat K.Ç.' kapı tipi 1200 ve "
                 "1300 mm'de tabloda yoktur — bu ikisinde E26/E27'ye imalatçı değeri girin.")

    # ---- bodrum açıklaması (boş satır 19)
    ws["B19"] = ("Bodrum durağı, MMO/697 tanımı gereği H (Tablo-3) ve S (Tablo-5) değerlerini "
                 "DEĞİŞTİRMEZ — bu iki büyüklük ana giriş üstündeki kat adedi N üzerinden "
                 "tanımlıdır ve yukarı yoğun trafikte tur ana giriş katından başlar. Bodrum "
                 "durağı yalnız (a) Tablo-2 asgari hız seçimindeki durak adedine ve "
                 "(b) toplam seyahat mesafesine girer.")
    stil_kopyala(ws, "B3", "B19")
    ws.merge_cells("B19:E19")
    ws.row_dimensions[19].height = 42
    print("  · HESAPLAMA →  ⑪ bodrum girdisi (E16), Tablo-4/7/8 aralıkları, doğrulama")


# ==================================================================
#  4)  TRAFİK  —  ÇOKLU ASANSÖR sayfası
# ==================================================================
def coklu_guncelle(wb):
    ws = wb["ÇOKLU ASANSÖR"]

    # ---- ortak bodrum  (A13 etiket / B13 girdi)
    ws["A13"] = "⑪ Bodrum durak adedi (ortak, ana giriş altı) — boş = 0"
    stil_kopyala(ws, "A12", "A13")
    ws["B13"] = None
    stil_kopyala(ws, "B12", "B13")
    ws["C13"] = ("Asansör bazında farklıysa 100. satırdan girin. Bodrum, H ve S'yi "
                 "değiştirmez; yalnız Tablo-2 hız seçimine ve seyahat mesafesine girer.")
    stil_kopyala(ws, "C12", "C13")
    ws.merge_cells("C13:E13")
    dv_ekle(ws, "B13", type="whole", operator="between", formula1=0, formula2=10,
            allow_blank=True, showErrorMessage=True, errorTitle="Bodrum durak adedi",
            error="0 – 10 arası tam sayı ya da boş.")
    ws["H12"] = "yardımcı (gizli): H13 = efektif ortak bodrum durak adedi"
    ws["H13"] = '=IF(AND(ISNUMBER($B$13),$B$13>=0,$B$13<=10,$B$13=INT($B$13)),$B$13,0)'

    # ---- grup Tablo-2 minimumu : durak = N + 1 + Nb
    v = ws["H98"].value
    assert v.count("($B$9+1)") == 11, v.count("($B$9+1)")
    ws["H98"] = v.replace("($B$9+1)", "($B$9+1+$H$13)")
    ws["A18"] = "V = Kabin hızı (durak = N+1+bodrum, Tablo-2)"

    # ---- asansör bazında ek girdiler bloğu  (99 – 106)
    ws["A21"] = ("→ Asansör bazında BODRUM DURAĞI ve İMALATÇI SÜRELERİ (ta/tk/tg/tp) "
                 "girişleri 99. satırdaki blokta yer alır; normal projede boş bırakılır.")
    stil_kopyala(ws, "A55", "A21")
    ws.merge_cells("A21:F21")

    ws["A99"] = ("ASANSÖR BAZINDA EK GİRDİLER  —  bodrum durağı ve imalatçı süreleri "
                 "(boş bırakılırsa ortak değer / MMO tablosu kullanılır)")
    stil_kopyala(ws, "A22", "A99")
    ws.merge_cells("A99:F99")

    etiketler = {
        100: "Bodrum durak adedi (ana giriş altı) — GİRDİ (boş = ortak)",
        101: "→ Kullanılan bodrum durak adedi (efektif)",
        102: "Manuel ta (sn) — boş = Tablo-4",
        103: "Manuel tk (sn) — boş = Tablo-4",
        104: "Manuel tg (sn) — boş = Tablo-6",
        105: "Manuel tp (sn) — boş = Tablo-8",
    }
    for r, metin in etiketler.items():
        kaynak = 60 if r == 101 else 59
        satir_stili(ws, kaynak, r, list("ABCDEF"))
        ws[f"A{r}"] = metin
    for i, c in enumerate("BCDE"):
        ws[f"{c}100"] = None
        ws[f"{c}101"] = (f'=IF({c}24="","",IF({c}100="",$H$13,'
                         f'IF(AND(ISNUMBER({c}100),{c}100>=0,{c}100<=10,{c}100=INT({c}100)),'
                         f'{c}100,"Bodrum geçersiz")))')
        for r in (102, 103, 104, 105):
            ws[f"{c}{r}"] = None
    ws["F100"] = "durak"
    ws["F102"] = ws["F103"] = ws["F104"] = ws["F105"] = "s"
    ws["A106"] = ("Bodrum durağı H (Tablo-3) ve S (Tablo-5) değerlerini değiştirmez; yalnız "
                  "Tablo-2 asgari hız seçimindeki durak adedine ve toplam seyahat mesafesine "
                  "girer (MMO/697 s.14 ve s.16, N'i ana giriş üstündeki kat adedi olarak "
                  "tanımlar). Manuel süre girildiğinde paftada marka-model ve teknik föy "
                  "referansı belirtilmelidir.")
    stil_kopyala(ws, "A81", "A106")
    ws.merge_cells("A106:F106")
    ws.row_dimensions[106].height = 46
    dv_ekle(ws, "B100:E100", type="whole", operator="between", formula1=0, formula2=10,
            allow_blank=True, showErrorMessage=True, errorTitle="Bodrum durak adedi",
            error="0 – 10 arası tam sayı ya da boş (boş = ortak değer).")
    dv_ekle(ws, "B102:E105", type="decimal", operator="between", formula1=0.3, formula2=60,
            allow_blank=True, showErrorMessage=True, errorTitle="İmalatçı süresi",
            error="0,3 – 60 saniye arası bir değer ya da boş.")

    # ---- asansör bazında V minimumu : durak = Ni + 1 + Nbi
    for c in "BCDE":
        v = ws[f"{c}61"].value
        assert v.count(f"({c}60+1)") == 11, (c, v.count(f"({c}60+1)"))
        ws[f"{c}61"] = v.replace(f"({c}60+1)", f"({c}60+1+{c}101)")

    # ---- süreler : imalatçı verisi tablo değerini ezer
    def govde_ayikla(formul, kosul_hucre):
        """=IF(<kosul>="","",<govde>)  →  <govde>"""
        onek = f'=IF({kosul_hucre}="","",'
        assert formul.startswith(onek) and formul.endswith(")"), formul[:60]
        return formul[len(onek):-1]

    for c in "BCDE":
        for satir, manuel, kosul in ((30, 102, f"{c}25"), (31, 103, f"{c}25"),
                                     (32, 104, f"{c}24"), (33, 105, f"{c}25")):
            govde = govde_ayikla(ws[f"{c}{satir}"].value, kosul)
            ws[f"{c}{satir}"] = (f'=IF({c}24="","",IF(ISNUMBER({c}{manuel}),'
                                 f'{c}{manuel},{govde}))')
        # Tablo aralıkları
        degistir(ws, f"{c}30", "'TABLO-4'!$I$4:$N$8", "'TABLO-4'!$I$4:$N$10")
        degistir(ws, f"{c}30", "'TABLO-4'!$A$4:$A$8", "'TABLO-4'!$A$4:$A$10")
        degistir(ws, f"{c}31", "'TABLO-4'!$I$4:$N$8", "'TABLO-4'!$I$4:$N$10")
        degistir(ws, f"{c}31", "'TABLO-4'!$A$4:$A$8", "'TABLO-4'!$A$4:$A$10")
        degistir(ws, f"{c}33", "'TABLO-8'!$B$2:$G$2", "'TABLO-8'!$B$2:$H$2")
        degistir(ws, f"{c}33", "'TABLO-8'!$B$1:$G$1", "'TABLO-8'!$B$1:$H$1")
        # Tablo-7 : 15 kişi
        degistir(ws, f"{c}38", f"IF({c}24=13,1000,", f"IF({c}24=13,1000,IF({c}24=15,1125,")
        degistir(ws, f"{c}38", f"IF({c}24=30,2500,{c}24*75)))))))))",
                 f"IF({c}24=30,2500,{c}24*75))))))))))")

    # ---- imalatçı süresi uyarısı
    ws["A49"] = ('=IF(COUNT(B102:E105)=0,"","⚠ "&COUNT(B102:E105)&" adet süre imalatçı '
                 'verisiyle değiştirildi (MMO Tablo-4/6/8 yerine). Paftada marka-model ve '
                 'teknik föy referansı belirtilmelidir.")')
    stil_kopyala(ws, "A55", "A49")
    ws.merge_cells("A49:F49")

    # ---- doğrulama zinciri : bodrum
    h47 = ws["H47"].value.lstrip("=")
    assert "tam hesaplanabilen genişlikler: 800 / 900 / 1100 / 1300 mm." in h47
    h47 = h47.replace("tam hesaplanabilen genişlikler: 800 / 900 / 1100 / 1300 mm.",
                      "'Kabin İçi Oto. Kat K.Ç.' kapı tipi 1200 ve 1300 mm'de tabloda "
                      "bulunmaz; bu durumda 102-103. satırlara imalatçı değerini girin.")
    h47 = h47.replace("(tabloda 800/900/1000/1100/1200/1300 mm var). 25. satırı k",
                      "105. satıra imalatçı değerini girin. 25. satırı k")
    kosul = ('OR(AND($B$13<>"",OR(NOT(ISNUMBER($B$13)),$B$13<0,$B$13>10,$B$13<>INT($B$13))),'
             'COUNTIF($B$101:$E$101,"Bodrum geçersiz")>0)')
    ws["H47"] = ('=IF(' + kosul + ',"HESAP HATASI: bodrum durak adedi 0 ile 10 arasında tam '
                 'sayı olmalıdır (ana giriş altında hizmet verilen durak adedi).",'
                 + h47 + ")")
    print("  · ÇOKLU     →  ortak+asansör bodrumu, manuel ta/tk/tg/tp (99-106), Tablo aralıkları")


# ==================================================================
#  5)  TRAFİK  —  PAFTA sayfaları
# ==================================================================
def pafta_guncelle(wb):
    ws = wb["PAFTA"]
    ws["A4"] = "Kat sayısı N (ana giriş üstü) / bodrum durağı"
    ws["B4"] = ('=IFERROR(HESAPLAMA!C9&IF(HESAPLAMA!$H$16>0," + "&HESAPLAMA!$H$16&'
                '" bodrum durağı",""),"—")')
    ws["D12"] = ('=IFERROR("Projeden — toplam seyahat "&INT(ROUND(HESAPLAMA!$H$17,2))&","&'
                 'TEXT(MOD(ROUND(HESAPLAMA!$H$17*100,0),100),"00")&" m","Projeden")')
    ws["D13"] = ('=IF(HESAPLAMA!$H$16>0,"Tablo-2  (durak = N+1+bodrum)","Tablo-2")')
    ws["D18"] = ('=IFERROR(IF(HESAPLAMA!C13=15,"MMO örneği s.53-54 (Tablo-7 dışı)","Tablo-7"),"—")')
    ws["D21"] = ('=IF(ISNUMBER(HESAPLAMA!$E$26),"İmalatçı verisi",'
                 'IF(OR(HESAPLAMA!$C$14=1000,HESAPLAMA!$C$14=1200),'
                 '"Tablo-4 (ara değer — enterpolasyon)","Tablo-4"))')
    ws["D22"] = ('=IF(ISNUMBER(HESAPLAMA!$E$27),"İmalatçı verisi",'
                 'IF(OR(HESAPLAMA!$C$14=1000,HESAPLAMA!$C$14=1200),'
                 '"Tablo-4 (ara değer — enterpolasyon)","Tablo-4"))')
    ws["D20"] = ('=IF(ISNUMBER(HESAPLAMA!$E$29),"İmalatçı verisi",'
                 'IF(HESAPLAMA!$C$14=700,"ISO 8100-32:2020 Tablo 6 (kapsam dışı — dış değerleme)",'
                 '"ISO 8100-32:2020, Tablo 6"))')

    ws = wb["PAFTA-COKLU"]
    ws["A4"] = "Kat sayısı N (ana giriş üstü) / bodrum — grup maksimumu"
    ws["B4"] = ("=IFERROR('ÇOKLU ASANSÖR'!B9&IF('ÇOKLU ASANSÖR'!$H$13>0,\" + \"&"
                "'ÇOKLU ASANSÖR'!$H$13&\" bodrum durağı\",\"\"),\"—\")")
    ws["F20"] = ('=IF(COUNT(\'ÇOKLU ASANSÖR\'!B102:E103)>0,"Tablo-4 / imalatçı verisi","Tablo-4")')
    ws["F21"] = ('=IF(COUNT(\'ÇOKLU ASANSÖR\'!B104:E105)>0,'
                 '"MMO T-6 / ISO 8100-32 T-6 / imalatçı","MMO T-6 / ISO 8100-32 T-6")')
    print("  · PAFTA     →  bodrum, seyahat mesafesi ve kaynak etiketleri")


# ==================================================================
#  6)  AVAN  —  GİRİŞ  :  asansör bazında palanga ve denge faktörü
# ==================================================================
def avan_guncelle(wb):
    ws = wb["GİRİŞ"]
    ws["A52"] = ("  3)   ASKI VE DENGE   —   asansör bazında   ( boş bırakılırsa "
                 "SABİTLER B ofis standardı kullanılır )")
    stil_kopyala(ws, "A20", "A52")
    ws.merge_cells("A52:H52")
    if ws.row_dimensions[20].height:
        ws.row_dimensions[52].height = ws.row_dimensions[20].height

    ws["A53"], ws["B53"] = "i", "Palanga ( askı ) katsayısı  —  asansör bazında"
    ws["A54"], ws["B54"] = "q", "Denge faktörü  —  asansör bazında"
    for r, (birim, aciklama) in ((53, ("—", "Doğrudan askı 1  /  Palangalı 2.  Boş = SABİTLER B "
                                            "( dişlili + dişlisiz karışık projede doldurun )")),
                                 (54, ("—", "Karşı ağırlığın dengelediği anma yükü oranı. "
                                            "Boş = SABİTLER B"))):
        satir_stili(ws, 39, r, list("ABCDEFGH"))
        for c in "CDEF":
            ws[f"{c}{r}"] = None
        ws[f"G{r}"] = birim
        ws[f"H{r}"] = aciklama
    dv_ekle(ws, "C53:F53", type="whole", operator="between", formula1=1, formula2=4,
            allow_blank=True, showErrorMessage=True, errorTitle="Palanga katsayısı",
            error="1 – 4 arası tam sayı ya da boş (boş = SABİTLER B).")
    dv_ekle(ws, "C54:F54", type="decimal", operator="between", formula1=0, formula2=1,
            allow_blank=True, showErrorMessage=True, errorTitle="Denge faktörü",
            error="0 – 1 arası bir değer ya da boş (boş = SABİTLER B).")
    ws["A55"] = ("Bir projede dişlili ve dişlisiz makine ya da 1:1 ve 2:1 askı birlikte "
                 "kullanılabildiği için bu iki değer — makine verimi η gibi — asansöre "
                 "özeldir. Boş bırakılan kolon SABİTLER B'deki ofis standardını kullanır.")
    stil_kopyala(ws, "A50", "A55")
    ws.merge_cells("A55:H55")
    ws.row_dimensions[55].height = 30
    ws.print_area = "'GİRİŞ'!$A$1:$H$55"

    # ---- SABİTLER notları
    s = wb["SABİTLER"]
    s["E22"] = ("Doğrudan askı 1  /  Palangalı 2.   Ofis uygulaması: MRL 2:1.   "
                "→ Asansör bazında GİRİŞ!53. satırdan ezilebilir.")
    s["E23"] = ("Karşı ağırlığın dengelediği anma yükü oranı — pratikte 0,50.   "
                "→ Asansör bazında GİRİŞ!54. satırdan ezilebilir.")
    s["A40"] = ("Bu SARI hücreler proje geneli için ORTAKTIR. Palanga katsayısı (i) ve denge "
                "faktörü (q) asansör bazında farklı olabildiğinden GİRİŞ sayfasının 53-54. "
                "satırından asansöre özel değer girilebilir; boş bırakılırsa buradaki değer "
                "kullanılır.")

    # ---- 1-4 NOLU ASANSÖR : palanga / denge asansör bazına
    for no, kol in ((1, "C"), (2, "D"), (3, "E"), (4, "F")):
        a = wb[f"{no} NOLU ASANSÖR"]
        pal = f'IF(ISNUMBER(GİRİŞ!${kol}$53),GİRİŞ!${kol}$53,SABİTLER!$C$22)'
        den = f'IF(ISNUMBER(GİRİŞ!${kol}$54),GİRİŞ!${kol}$54,SABİTLER!$C$23)'
        n = 0
        for row in a.iter_rows(min_row=1, max_row=a.max_row, max_col=8):
            for cell in row:
                v = cell.value
                if not isinstance(v, str) or "SABİTLER!$C$2" not in v:
                    continue
                yeni = v.replace("SABİTLER!$C$22", pal).replace("SABİTLER!$C$23", den)
                if yeni != v:
                    cell.value = yeni
                    n += 1
        a["G8"] = f'=IF(ISNUMBER(GİRİŞ!${kol}$54),"GİRİŞ — asansör bazında","SABİTLER B")'
        a["G9"] = f'=IF(ISNUMBER(GİRİŞ!${kol}$53),"GİRİŞ — asansör bazında","SABİTLER B")'
        a["G28"] = a["G8"].value
        print(f"  · {no} NOLU ASANSÖR  →  {n} formülde palanga/denge asansör bazına alındı")
    print("  · GİRİŞ     →  3) ASKI VE DENGE bloğu (53-54. satır)")


# ==================================================================
def main():
    for yol in (TRAFIK, AVAN):
        yedek = yol + ".yedek"
        if not os.path.exists(yedek):
            shutil.copy2(yol, yedek)

    print("TRAFİK şablonu:")
    wb = openpyxl.load_workbook(TRAFIK)
    tablo4_guncelle(wb)
    tablo8_guncelle(wb)
    hesaplama_guncelle(wb)
    coklu_guncelle(wb)
    pafta_guncelle(wb)
    wb.calculation.fullCalcOnLoad = True
    wb.save(TRAFIK)

    print("\nAVAN şablonu:")
    wb = openpyxl.load_workbook(AVAN)
    avan_guncelle(wb)
    wb.calculation.fullCalcOnLoad = True
    wb.save(AVAN)
    print("\nTamam.")


if __name__ == "__main__":
    sys.exit(main())
