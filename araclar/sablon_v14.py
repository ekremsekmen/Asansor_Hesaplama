# -*- coding: utf-8 -*-
"""
ŞABLON GÜNCELLEME  —  v1.4

Avan şablonuna dört yeni girdi ekler; satır/sütun KAYDIRMAZ.

  GİRİŞ!C15                Makine dairesi yok ( MRL )        Evet / Hayır
  GİRİŞ!C55:F55            Makine tipi                        Dişlisiz / Dişli
  GİRİŞ!C56:F56            Girilen η toplam sistem verimi mi  Evet / Hayır
  ( GİRİŞ!C53:F53 askı oranı ve C54:F54 denge faktörü v1.3'te eklenmişti )

ve 1-4 NOLU ASANSÖR sayfalarında η′ zincirini koşullu hâle getirir:
"toplam verim" işaretliyse MMO/697 §2.4'teki Δη = 0,10 palanga düşüşü
İKİNCİ KEZ uygulanmaz — askı kaybı zaten o değerin içindedir.

Çalıştırma:  python3 araclar/sablon_v14.py
"""
import os
import sys
from copy import copy

import openpyxl
from openpyxl.worksheet.datavalidation import DataValidation

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AVAN = os.path.join(KOK, "templates", "ASANSOR_AVAN_HESAPLARI.xlsx")


def stil_kopyala(ws, kaynak, hedef):
    ws[hedef]._style = copy(ws[kaynak]._style)


def satir_stili(ws, kaynak, hedef, sutunlar):
    for c in sutunlar:
        stil_kopyala(ws, f"{c}{kaynak}", f"{c}{hedef}")
    if ws.row_dimensions[kaynak].height:
        ws.row_dimensions[hedef].height = ws.row_dimensions[kaynak].height


def kaydir(ws, adres, yukseklik=None):
    h = ws[adres]
    a = copy(h.alignment)
    a.wrap_text = True
    a.vertical = "top"
    h.alignment = a
    if yukseklik:
        ws.row_dimensions[h.row].height = yukseklik


def dv_ekle(ws, aralik, **kw):
    for dv in list(ws.data_validations.dataValidation):
        if str(dv.sqref) == aralik:
            ws.data_validations.dataValidation.remove(dv)
    dv = DataValidation(**kw)
    ws.add_data_validation(dv)
    dv.add(aralik)


def birlesimi_kaldir(ws, aralik):
    if aralik in [str(m) for m in ws.merged_cells.ranges]:
        ws.unmerge_cells(aralik)


def main():
    wb = openpyxl.load_workbook(AVAN)
    ws = wb["GİRİŞ"]

    # ---------------------------------------- 1) MRL işaret kutusu  (C15)
    satir_stili(ws, 16, 15, list("ABCDEFGH"))
    ws["A15"] = "—"
    ws["B15"] = "Makine dairesi YOK  ( MRL — makine kuyu içinde )"
    ws["C15"] = "Hayır"
    ws["D15"] = "—"
    ws["E15"] = ("'Evet' ise makine dairesi aydınlatma hesabı yapılmaz. 'Hayır' ise "
                 "aşağıdaki A ve B ölçüleri zorunludur.")
    if "E16:H16" in [str(m) for m in ws.merged_cells.ranges]:
        ws.merge_cells("E15:H15")
    dv_ekle(ws, "C15", type="list", formula1='"Hayır,Evet"',
            allow_blank=True, showErrorMessage=True, errorTitle="Makine dairesi",
            error="Listeden seçin: Hayır / Evet")
    ws["E16"] = "Makine dairesi yoksa üstteki kutuyu 'Evet' yapın; ölçü aranmaz."
    ws["E17"] = "Makine dairesi yoksa üstteki kutuyu 'Evet' yapın; ölçü aranmaz."
    print("  · GİRİŞ!C15   →  Makine dairesi yok ( MRL ) kutusu")

    # ------------------------- 2) makine tipi (55) ve toplam verim (56)
    birlesimi_kaldir(ws, "A55:H55")
    not_metni = ws["A55"].value
    ws["A55"] = None
    ws["A52"] = ("  3)   ASKI, DENGE VE MAKİNE   —   asansör bazında   "
                 "( boş bırakılırsa SABİTLER B ofis standardı )")
    for r, (sembol, ad, birim, aciklama) in (
        (55, ("—", "Makine tipi", "—",
              "Dişlisiz  η = 0,85   /   Dişli  η = 0,50   ( MMO/697 s.21 ). "
              "Seçim yalnız kaynağı belgeler; η yukarıdaki 29. satırdan gelir.")),
        (56, ("—", "Girilen η TOPLAM sistem verimi mi ?", "—",
              "'Evet' ise MMO/697 §2.4'teki palanga verim düşüşü ( Δη = 0,10 ) AYRICA "
              "uygulanmaz — askı kaybı zaten girilen değerin içindedir. İmalatçı "
              "kataloğundan toplam verim giriyorsanız 'Evet' seçin.")),
    ):
        satir_stili(ws, 53, r, list("ABCDEFGH"))
        ws[f"A{r}"], ws[f"B{r}"] = sembol, ad
        for c in "CDEF":
            ws[f"{c}{r}"] = None
        ws[f"G{r}"] = birim
        ws[f"H{r}"] = aciklama
    dv_ekle(ws, "C55:F55", type="list", formula1='"Dişlisiz,Dişli"',
            allow_blank=True, showErrorMessage=True, errorTitle="Makine tipi",
            error="Listeden seçin: Dişlisiz / Dişli")
    dv_ekle(ws, "C56:F56", type="list", formula1='"Hayır,Evet"',
            allow_blank=True, showErrorMessage=True, errorTitle="Toplam verim",
            error="Listeden seçin: Hayır / Evet")
    #  askı oranı artık liste olarak seçilir
    dv_ekle(ws, "C53:F53", type="list", formula1='"1,2"',
            allow_blank=True, showErrorMessage=True, errorTitle="Askı oranı",
            error="1 ( doğrudan askı, 1:1 )  ya da  2 ( palangalı, 2:1 )")
    ws["B53"] = "i  —  Askı ( palanga ) oranı   ( 1 = 1:1  ·  2 = 2:1 )"
    ws["H53"] = ("Asansörün kendi özelliğidir. Motor GÜCÜ askı oranından bağımsızdır; "
                 "askı oranı hesaba yalnız VERİM üzerinden girer ( MMO/697 §2.4 ). "
                 "Boş = SABİTLER B")
    ws["A58"] = (not_metni or "") + ("   Makine tipi ve askı oranı asansöre özeldir; "
                 "bir projede dişlili + dişlisiz ya da 1:1 + 2:1 birlikte olabilir. "
                 "MMO/697 değerleri ( dişli 1:1 = 0,50 · dişlisiz 2:1 = 0,75 ) makine "
                 "verimidir ve emniyetli taraftadır; imalatçı katalogları genellikle "
                 "daha yüksek TOPLAM sistem verimi verir — o değerleri kullanacaksanız "
                 "56. satırı 'Evet' yapın, yoksa palanga kaybı iki kez düşülür.")
    stil_kopyala(ws, "A50", "A58")
    ws.merge_cells("A58:H58")
    kaydir(ws, "A58", 58)
    ws.print_area = "'GİRİŞ'!$A$1:$H$58"
    print("  · GİRİŞ!55-56 →  Makine tipi ve toplam-verim kutusu")

    # ---------------------------------------- 3) η′ zinciri koşullu
    for no, kol in ((1, "C"), (2, "D"), (3, "E"), (4, "F")):
        a = wb[f"{no} NOLU ASANSÖR"]
        pal = f'IF(ISNUMBER(GİRİŞ!${kol}$53),GİRİŞ!${kol}$53,SABİTLER!$C$22)'
        eski = (f'=IF(GİRİŞ!${kol}$27="","",IF({pal}>1,GİRİŞ!${kol}$29-SABİTLER!$C$11,'
                f'GİRİŞ!${kol}$29))')
        mevcut = a["E11"].value
        assert mevcut == eski, f"{no} NOLU ASANSÖR!E11 beklenenden farklı:\n{mevcut}"
        a["E11"] = (f'=IF(GİRİŞ!${kol}$27="","",IF(GİRİŞ!${kol}$56="Evet",GİRİŞ!${kol}$29,'
                    f'IF({pal}>1,GİRİŞ!${kol}$29-SABİTLER!$C$11,GİRİŞ!${kol}$29)))')
        a["C11"] = (f'=IF(GİRİŞ!${kol}$27="","",IF(GİRİŞ!${kol}$56="Evet",'
                    f'"Girilen değer TOPLAM sistem verimidir — palanga düşüşü uygulanmaz",'
                    f'"Palangalı sistemde verim ( i > 1 ise η − 0,10 )"))')
        a["G11"] = (f'=IF(GİRİŞ!${kol}$56="Evet","GİRİŞ — toplam sistem verimi",'
                    f'"SABİTLER A  /  MMO/697 §2.4")')
        print(f"  · {no} NOLU ASANSÖR!E11  →  η′ koşullu")

    # ---------------------------------------- 4) MK.DAİRESİ AYD. — MRL kutusu
    mk = wb["MK.DAİRESİ AYD."]
    n = 0
    for row in mk.iter_rows(min_row=1, max_row=mk.max_row, max_col=8):
        for cell in row:
            v = cell.value
            if isinstance(v, str) and "OR(GİRİŞ!$C$16=0,GİRİŞ!$C$17=0)" in v:
                cell.value = v.replace("OR(GİRİŞ!$C$16=0,GİRİŞ!$C$17=0)",
                                       'OR(GİRİŞ!$C$15="Evet",GİRİŞ!$C$16=0,GİRİŞ!$C$17=0)')
                n += 1
    print(f"  · MK.DAİRESİ AYD.  →  {n} formülde MRL kutusu dikkate alındı")

    s = wb["SABİTLER"]
    s["E22"] = ("Yedek değer.   ASKI ORANI asansörün kendi özelliğidir — GİRİŞ sayfası "
                "53. satırdan asansör bazında seçilir; burası yalnız boş bırakılan kolon "
                "için kullanılır.")
    kaydir(s, "E22", 34)
    wb.calculation.fullCalcOnLoad = True
    wb.save(AVAN)
    print("\nTamam.")


if __name__ == "__main__":
    sys.exit(main())
