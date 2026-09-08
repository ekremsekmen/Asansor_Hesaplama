# -*- coding: utf-8 -*-
"""
HÜCRE HARİTASI  —  girdi alanı  ↔  Excel hücresi eşlemesi

Bu harita TEK YERDE tanımlıdır ve hem dışa aktarma (xlsx_export) hem de
geri yükleme (xlsx_import) tarafından kullanılır.  Böylece iki yön
birbirinden ayrışamaz:  bir hücre adresi değişirse iki taraf da değişir.

Şablondaki hücre adresi değişirse yalnız bu dosya güncellenir.
"""

# =====================================================================
#  TRAFİK — TEK ASANSÖR   ( HESAPLAMA sayfası )
# =====================================================================
TEK_SAYFA = "HESAPLAMA"
TEK = {
    "bina_tipi":        "C5",
    "manuel_k":         "E5",
    "bina_yuksekligi":  "E8",
    "N":                "C9",
    "yapi_yuksekligi":  "E9",
    "hizli1":           "C10",
    "manuel_V":         "E10",
    "hizli2":           "C11",
    "h":                "C12",
    "P":                "C13",
    "kapi_genisligi":   "C14",
    "kapi_tipi":        "C16",
    "bodrum":           "E16",
    "manuel_ta":        "E26",
    "manuel_tk":        "E27",
    "manuel_tg":        "E28",
    "manuel_tp":        "E29",
    "manuel_adet":      "C39",
}
# Ek nüfus kalemleri — açıklama / miktar / Tablo-1 kalemi
TEK_EK_NUFUS = {"satirlar": range(53, 64),
                "aciklama": "B", "miktar": "C", "kalem": "D"}

# =====================================================================
#  TRAFİK — ÇOKLU ASANSÖR   ( ÇOKLU ASANSÖR sayfası )
# =====================================================================
COKLU_SAYFA = "ÇOKLU ASANSÖR"
COKLU_ORTAK = {
    "bina_tipi":        "B5",
    "manuel_k":         "E5",
    "bina_yuksekligi":  "D8",
    "N":                "B9",
    "yapi_yuksekligi":  "D9",
    "hizli1":           "B10",
    "manuel_V":         "D10",
    "hizli2":           "B11",
    "h":                "B12",
    "bodrum":           "B13",
}
COKLU_KOLONLAR = ("B", "C", "D", "E")
COKLU_ASANSOR = {          # satır : alan adı
    24: "P",
    25: "kapi_genisligi",
    26: "kapi_tipi",
    56: "V",
    59: "durak",
    62: "h",
    100: "bodrum",
    102: "manuel_ta",
    103: "manuel_tk",
    104: "manuel_tg",
    105: "manuel_tp",
}
COKLU_EK_NUFUS = {"satirlar": range(68, 79),
                  "aciklama": "A", "miktar": "B", "kalem": "C"}

# =====================================================================
#  AVAN HESAPLARI   ( GİRİŞ / SABİTLER / TABLOLAR sayfaları )
# =====================================================================
AVAN_SAYFA = "GİRİŞ"
AVAN_ORTAK = {
    "U":            "C6",
    "kappa":        "C7",
    "eps_max":      "C8",
    "temel_a":      "C10",
    "temel_b":      "C11",
    "beta":         "C12",
    "serit_L":      "C13",
    "cubuk_sayisi": "C14",
    "mk_yok":       "C15",
    "mk_uzunluk":   "C16",
    "mk_genislik":  "C17",
}
AVAN_KOLONLAR = ("C", "D", "E", "F")
AVAN_ASANSOR = {           # satır : alan adı
    23: "tanim",
    24: "kapasite",
    26: "Q_elle",
    28: "V",
    29: "eta",
    31: "Hk",
    32: "kuyu_genisligi",
    33: "kabin_boyu",
    34: "kabin_genisligi",
    37: "Gk_elle",
    39: "gr",
    40: "Fmk",
    41: "Fsh",
    43: "Nsc",
    44: "S1",
    45: "L1",
    46: "S2",
    47: "L2",
    48: "kablo_tipi",
    53: "i_palanga",
    54: "q_denge",
    55: "makine_tipi",
}
AVAN_SABIT_SAYFA = "SABİTLER"
AVAN_SABIT = {
    "i_palanga":          "C22",
    "q_denge":            "C23",
    "n_ray":              "C24",
    "gf":                 "C25",
    "Fmt":                "C26",
    "kabin_armatur_W":    "C27",
    "kabin_armatur_lm":   "C28",
    "kabin_ustu_armatur": "C29",
    "kuyu_armatur_W":     "C30",
    "kuyu_armatur_lm":    "C31",
    "kuyu_Dmax":          "C32",
    "priz_adedi":         "C33",
    "priz_gucu":          "C34",
    "cosfi":              "C35",
    "UL":                 "C36",
    "IDn":                "C37",
    "lc":                 "C38",
    #  ŞEBEKEDEN ÇEKİLEN GÜÇ.  Nsç motorun MİL gücüdür;  kolon ve makine
    #  besleme hatlarında Pşeb = Nsç / ηm akar ve kesitler ondan seçilir.
    #  Şablonun E102 ve E126 hücreleri bu sabite böler.
    "motor_elektrik_verimi": "C39",
}
AVAN_AYD_SUTUN_SAYFA = "TABLOLAR"
AVAN_AYD_SUTUN_HUCRE = "B19"

#  MOTOR KORUMA CİHAZI  —  her asansörün kendi pafta sayfasındaki KURULU GÜÇ
#  cetvelinde sabit metin olarak duran hücre ( şablonda "4 x 25" yazılıydı ).
#  Formül değil, düz metindir; program motor akımından hesapladığı değeri
#  buraya yazar, böylece indirilen Excel ile ekrandaki pafta ayrışmaz.
AVAN_SIGORTA_HUCRE = "G102"


def avan_asansor_sayfasi(no: int) -> str:
    """1 → '1 NOLU ASANSÖR' — asansörün kendi pafta sayfasının adı."""
    return f"{int(no)} NOLU ASANSÖR"

# =====================================================================
#  PROJE BİLGİSİ
#  Şablonda proje antedine ait bir hücre yoktur; bu bilgi dosyanın
#  ÖZELLİKLERİNE (Excel: Dosya → Bilgi → Özellikler) yazılır.  Böylece
#  ofis şablonunun düzenine hiç dokunulmaz, bilgi de dosyayla taşınır.
# =====================================================================
PROJE_ALANLARI = ("proje_adi", "isveren", "pafta_no", "tarih", "muhendis")
IMZA = "Asansör Proje Programı"

#  ESKİ İMZALAR.  Program adı değişti;  daha önce üretilmiş dosyaların
#  "creator" alanında eski ad yazıyor.  İçe aktarma bunları da PROGRAM
#  imzası sayar — yoksa eski bir dosya geri yüklendiğinde program adı
#  mühendis adı sanılıp kapağa yazılırdı.
IMZALAR = (IMZA, "Asansör Avan Hesaplama Programı")

# =====================================================================
#  EVET / HAYIR KUTULARI
#  Excel'de METİN ("Evet" / "Hayır") olarak durur — şablon formülleri bu
#  karşılaştırmayı yapar.  Arayüzde ise işaret kutusudur.  Geri yüklerken
#  metni mantıksal değere çevirmek gerekir; "Hayır" metni doğrudan bir
#  kutuya yazılsaydı doğru sayılıp kutuyu İŞARETLERDİ.
# =====================================================================
EVET_HAYIR_ALANLARI = ("mk_yok",)


def evet_hayir_mi(anahtar):
    return anahtar in EVET_HAYIR_ALANLARI


def evet_mi(metin):
    if isinstance(metin, bool):
        return metin
    return str(metin or "").strip().lower() in ("evet", "e", "var", "true", "1", "yes")


# =====================================================================
#  Arayüz alan adları  ( form alanı kimliği ↔ girdi anahtarı )
# =====================================================================
#  TEK ASANSÖR sayfasının girdileri artık AYNI FORMA yüklenir:  arayüzde
#  ayrı bir "tek hesap" gövdesi kalmadı, 1..4 asansör tek formda tanımlanır.
#  Bu yüzden bina alanları ortak ( c_ ) alanlara, asansöre ait olanlar da
#  1. asansör kolonuna yazılır.
TEK_ASANSOR_ALANLARI = {
    "P": "P", "kapi_genisligi": "kapi_genisligi", "kapi_tipi": "kapi_tipi",
    "manuel_ta": "manuel_ta", "manuel_tk": "manuel_tk",
    "manuel_tg": "manuel_tg", "manuel_tp": "manuel_tp",
}


def tek_alan(anahtar):
    if anahtar in TEK_ASANSOR_ALANLARI:
        return coklu_asansor_alan(TEK_ASANSOR_ALANLARI[anahtar], 1)
    if anahtar == "manuel_adet":
        #  Adet artık tanımlanan kolon sayısıdır; ayrı bir alanı yok.
        return None
    return "c_" + anahtar


def coklu_ortak_alan(anahtar):
    return "c_" + anahtar


def coklu_asansor_alan(anahtar, no):
    kisa = {"P": "P", "kapi_genisligi": "kg", "kapi_tipi": "kt",
            "V": "V", "durak": "durak", "h": "h", "bodrum": "bodrum",
            "manuel_ta": "mta", "manuel_tk": "mtk",
            "manuel_tg": "mtg", "manuel_tp": "mtp"}[anahtar]
    return f"c_{kisa}{no}"


#  Bu alanlar avan panelinden KALDIRILDI ve "Sabitler / Ofis Standardı"
#  sekmesine taşındı;  arayüzdeki id'leri artık of_<ad>.  Harita hâlâ a_<ad>
#  ürettiği için Excel'den okunan değerler HİÇBİR YERE yazılamıyordu:  dosyada
#  U = 220 V yazsa bile geri yüklemede ofis varsayılanı ( 380 V ) devreye
#  giriyor, ε %4,69 "UYGUN DEĞİL" iken %0,98 "UYGUN" oluyordu.
OFIS_SEKMESI_ALANLARI = ("U", "kappa", "eps_max", "beta", "cubuk_sayisi")


def avan_ortak_alan(anahtar):
    if anahtar in OFIS_SEKMESI_ALANLARI:
        return "of_" + anahtar
    return "a_" + anahtar


def avan_asansor_alan(anahtar, no):
    return f"a_{anahtar}{no}"


def sabit_alan(anahtar):
    return "sb_" + anahtar


#  Kapak sekmesindeki alan id'leri  k_<ad>;  harita "p_" üretiyordu ve
#  arayüz zaten `veri.proje`'yi hiç kullanmıyordu — proje adı / işveren
#  geri yüklenmiyor, önceki projenin kimliği formda kalıyordu.
#  `muhendis` ve `tarih` GERİ YÜKLENMEZ:  muhendis, kapaktaki ad + soyad
#  alanlarının BİRLEŞİMİDİR ( bkz. main._proje_kimligi ) — tek alana geri
#  yazmak "Ekrem Şekmen"i ad kutusuna koyardı.  tarih zaten boş üretiliyor.
PROJE_ALAN_ESLESME = {"proje_adi": "k_project_title", "isveren": "k_owner",
                      "pafta_no": "k_sheet_no"}


def proje_alan(anahtar):
    """Geri yüklenecek kapak alanı;  yüklenmeyecekse None."""
    return PROJE_ALAN_ESLESME.get(anahtar)
