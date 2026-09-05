# -*- coding: utf-8 -*-
"""
OFİSİN ANA EXCEL'İNİ DÜZELT

Program teslim ettiği her mukavemet dosyasını zaten düzeltiyor;  ama ofisin
masasındaki ANA kitap düzelmiyordu — onu açıp elle hesap yapan eski, bazıları
emniyetsiz sonuçları alıyordu.  Bu araç o kitabın düzeltilmiş bir kopyasını
üretir.

ŞABLON DOSYASINA DOKUNULMAZ.  templates/MUKAVEMET_HESABI.xlsx özgün hâlinde
kalır — doğrulama paketinin tamamı motoru ONA karşı denetler ve sapmaların
gerekçesi kitabın o hücrelerde ne yaptığıdır.  Düzeltilmiş kitap ayrı bir
dosyadır ve içinde neyin niçin değiştiğini anlatan bir DÜZELTMELER sayfası
taşır.

Kullanım:
    python3 araclar/kaynak_excel_duzelt.py [hedef.xlsx]
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.uygulama import mukavemet as MK          # noqa: E402
from exports import mukavemet_xlsx as MX             # noqa: E402

VARSAYILAN = "MUKAVEMET_HESABI_DUZELTILMIS.xlsx"


def main(argv):
    hedef = argv[1] if len(argv) > 1 else VARSAYILAN
    try:
        icerik = MX.duzeltilmis_kaynak()
    except FileNotFoundError as e:
        print(f"HATA: {e}")
        return 1
    with open(hedef, "wb") as f:
        f.write(icerik)

    print(f"Düzeltilmiş kitap yazıldı:  {hedef}   ({len(icerik):,} bayt)")
    print(f"Özgün şablona dokunulmadı:  {os.path.relpath(MX.SABLON)}")
    print()
    print(f"{len(MK.EXCEL_FARKLARI)} düzeltme uygulandı:")
    for i, (ad, madde, _eski, _yeni, hucreler) in enumerate(MK.EXCEL_FARKLARI, 1):
        yer = ", ".join(hucreler) if hucreler else "—"
        print(f"  {i}. {ad}")
        print(f"     dayanak : {madde}")
        print(f"     hücre   : {yer}")
    print()
    print(f"Kitabın içindeki '{MX.DUZELTME_SAYFASI}' sayfasında da aynı liste "
          "hücre adresleriyle birlikte durur.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
