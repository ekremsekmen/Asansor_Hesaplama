# -*- coding: utf-8 -*-
"""
API ORTAK KATMANI

İki proje türünün de kullandığı yardımcılar:  metin → sayı çevirme, belirsiz
yazım denetimi, proje kimliği, dosya adı ve indirme yanıtı.

Buradaki hiçbir şey hesap YAPMAZ;  hesap motorları engine/ altındadır.
"""
import json
import math
import os
import re
import threading

from fastapi.responses import JSONResponse, Response

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BELIRSIZ_SAYI = re.compile(r"^[+-]?[1-9]\d{0,2}[.,]\d{3}$")

def belirsiz_sayi_mi(x) -> bool:
    if not isinstance(x, str):
        return False
    return bool(BELIRSIZ_SAYI.match(x.strip().replace(" ", "").replace("\u00a0", "")))


def _sayi(x):
    """
    Metni sayıya çevirir.  Kabul edilen biçimler:
        "1,60"  "1.60"  "1.234,56"  "1,234.56"  "  3  "  12  3.0
    Geçersiz, boş, sonsuz, NaN veya BELİRSİZ değerlerde None döner —
    bu sayede bozuk girdi hesabı çökertmez, "eksik girdi" olarak işlenir.
    """
    if x is None or isinstance(x, bool):
        return None
    if isinstance(x, (int, float)):
        return x if math.isfinite(x) else None
    if not isinstance(x, str):
        return None
    s = x.strip().replace(" ", "").replace("\u00a0", "")
    if s == "":
        return None
    if BELIRSIZ_SAYI.match(s):        # "1.200" / "1,200" → hangisi belli değil
        return None
    # Hangi ayraç SONDA ise ondalık ayracıdır; diğeri binlik ayracıdır.
    son_virgul, son_nokta = s.rfind(","), s.rfind(".")
    if son_virgul >= 0 and son_nokta >= 0:
        if son_virgul > son_nokta:                    # 1.234,56  → TR biçimi
            s = s.replace(".", "").replace(",", ".")
        else:                                         # 1,234.56  → EN biçimi
            s = s.replace(",", "")
    elif son_virgul >= 0:
        s = s.replace(",", ".")                       # 1,60
    try:
        f = float(s)
    except ValueError:
        return None
    if not math.isfinite(f):                          # inf / -inf / nan
        return None
    if abs(f) > 1e12:                                 # anlamsız büyüklükler
        return None
    return int(f) if f.is_integer() else f


#  Belirsiz yazılmış alanların adları burada toplanır ki kullanıcıya
#  "eksik girdi" yerine gerçek sebep söylenebilsin.
#
#  İSTEK BAŞINA AYRI LİSTE:  FastAPI'de `def` ( async olmayan ) uç noktalar bir
#  iş parçacığı havuzunda koşar, yani İKİ İSTEK AYNI ANDA çalışabilir.  Ortak
#  bir liste kullanılsaydı biri listeyi temizlerken diğeri okuyabilir ve
#  geçerli bir indirme "belirsiz sayı" diye reddedilebilir ya da tersi, bozuk
#  bir girdi denetimden kaçabilirdi.  ( Ekran her tuş vuruşunda hesap
#  isterken indirmeye basılması bu iki isteği gerçekten çakıştırır. )
class _BelirsizListesi(threading.local):
    def __init__(self):
        self.kalemler = []

    def clear(self):
        self.kalemler = []

    def append(self, x):
        self.kalemler.append(x)

    def __bool__(self):
        return bool(self.kalemler)

    def __iter__(self):
        return iter(self.kalemler)


_BELIRSIZ = _BelirsizListesi()
#  BELİRSİZLİKTEN BAŞKA SEBEPLE REDDEDİLEN GİRDİLER ( negatif miktar, seçilmemiş
#  kalem, şablon sınırını aşan satır … ).  Ayrı tutulur çünkü belirsiz-sayı
#  açıklaması ( "binlik ayracı mı ondalık mı" ) bunlar için YANLIŞ olur.
_RED = _BelirsizListesi()


def _temiz(d: dict, sayisal: tuple, on_ek: str = "") -> dict:
    out = dict(d or {})
    for k in sayisal:
        ham = out.get(k)
        if belirsiz_sayi_mi(ham):
            _BELIRSIZ.append(f"{on_ek}{k} = {str(ham).strip()}")
        out[k] = _sayi(ham)
    return out


def _belirsiz_hata():
    """Reddedilen girdi varsa açık hata metni, yoksa None."""
    if _BELIRSIZ:
        liste = "  ·  ".join(sorted(set(_BELIRSIZ.kalemler))[:6])
        return ("HESAP HATASI: Belirsiz sayı yazımı  —  " + liste +
                "   ·   Bu yazımda binlik ayracı mı ondalık ayracı mı olduğu "
                "anlaşılmıyor ( Türkçede 1.200 = bin iki yüz, 1,200 = bir virgül iki; "
                "program ikisini de ondalık kabul ediyor ). Binlik ayracı KULLANMAYIN: "
                "bin iki yüz için 1200, bir virgül iki için 1,2 yazın.")
    if _RED:
        return ("HESAP HATASI: Girdi kabul edilmedi  —  "
                + "  ·  ".join(sorted(set(_RED.kalemler))[:6])
                + "   ·   Satırı düzeltin ya da kaldırın; sessizce yok sayılmaz.")
    return None

TRAFIK_SAYISAL = ("bina_yuksekligi", "yapi_yuksekligi", "N", "hizli1", "hizli2", "h", "P",
                  "kapi_genisligi", "bodrum", "manuel_k", "manuel_V", "manuel_ta",
                  "manuel_tk", "manuel_tg", "manuel_tp", "manuel_adet")
ASANSOR_SAYISAL = ("P", "kapi_genisligi", "V", "durak", "h", "bodrum",
                   "manuel_ta", "manuel_tk", "manuel_tg", "manuel_tp")
AVAN_ORTAK_SAYISAL = ("U", "kappa", "eps_max", "temel_a", "temel_b", "beta", "serit_L",
                      "cubuk_sayisi", "mk_uzunluk", "mk_genislik")
AVAN_AS_SAYISAL = ("i_palanga", "q_denge",
                   "kapasite", "Q_elle", "V", "eta", "Hk", "kuyu_genisligi", "kabin_boyu",
                   "kabin_genisligi", "Gk_elle", "gr", "Fmk", "Fsh", "Nsc",
                   "S1", "L1", "S2", "L2")


#  EK NÜFUS SATIRLARI  —  BOZUK GİRDİ SESSİZCE SİLİNMEZ.
#  Eskiden okunamayan miktar ( "1.200", "abc" ) satırı hesaptan tamamen
#  çıkarıyordu:  1200 yazınca 11 asansör, 1.200 yazınca 2 asansör çıkıyor ve
#  aradaki fark hiçbir yerde söylenmiyordu.  Belirsiz yazım zaten _BELIRSIZ
#  listesine düşer ( ekran ve indirme aynı kapıdan geçer ); geri kalan bozuk
#  ya da negatif satırlar için açık hata üretilir.
EK_NUFUS_AZAMI = 11          # şablondaki satır adedi ( bkz. hucre_haritasi )


def _sozluk_listesi(x):
    """Yalnız sözlük öğelerini geçiren güvenli liste — bozuk gövdede çökmez."""
    if not isinstance(x, (list, tuple)):
        return []
    return [e for e in x if isinstance(e, dict)]


def _proje_kimligi(veri):
    """
    KAPAK SEKMESİNDEKİ PROJE KİMLİĞİ  →  indirilen dosyanın adı ve XLSX'in
    dosya özellikleri.

    Bu bağlanmadan önce her indirme "Asansor - Avan Hesaplari.xlsx" adıyla
    iniyordu:  aynı klasördeki iki projenin dosyaları birbirinden ayırt
    edilemiyor, ikincisi "(1)" olarak kaydediliyordu.  Pafta içeriği
    değişmez — proje adı yalnız KAPAK sayfasında yazılıdır.
    """
    k = veri.get("kapak") if isinstance(veri.get("kapak"), dict) else {}

    def _birlestir(*alanlar):
        return " ".join(str(k.get(x) or "").strip() for x in alanlar).strip()

    return {"proje_adi": str(k.get("project_title") or "").strip(),
            "isveren": str(k.get("owner") or k.get("contractor") or "").strip(),
            "pafta_no": str(k.get("sheet_no") or "").strip(),
            "tarih": "",
            "muhendis": _birlestir("elec_name", "elec_surname")
            or _birlestir("mech_name", "mech_surname")}


def _dosya_adi(proje, ek, uzanti):
    ad = (proje or {}).get("proje_adi") or "Asansor"
    ad = "".join(c for c in str(ad) if c.isalnum() or c in " -_")[:48].strip() or "Asansor"
    return f"{ad} - {ek}.{uzanti}"


def _indir(icerik: bytes, ad: str, tur: str):
    from urllib.parse import quote
    return Response(icerik, media_type=tur, headers={
        "Content-Disposition": f"attachment; filename*=UTF-8''{quote(ad)}"})


XLSX_TUR = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _uretilemedi(e: Exception):
    """
    Dosya üretilemediğinde JSON hata döndürür.  Arayüz Content-Type'a bakarak
    bunu bozuk bir dosya olarak indirmek yerine ekranda mesaj olarak gösterir.
    """
    ileti = str(e)
    if isinstance(e, FileNotFoundError) or "No such file" in ileti:
        ileti = ("Excel şablonu bulunamadı. XLSX çıktısı ofisin kendi Excel dosyasını "
                 "şablon olarak kullanır — 'templates' klasöründeki iki dosya yerinde "
                 "olmalıdır. (Ekrandaki hesap ve PDF çıktısı şablon olmadan da çalışır.)")
    return JSONResponse({"hata": f"DOSYA ÜRETİLEMEDİ — {ileti}"}, status_code=422)


