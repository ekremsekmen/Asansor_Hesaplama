# -*- coding: utf-8 -*-
"""
ASANSÖR TRAFİK HESABI  —  MMO/697, 2. Baskı, Ocak 2020, s.11-17

ASANSOR_TRAFIK_HESABI_v2_1.xlsx dosyasındaki
  · HESAPLAMA      sayfası  ->  hesapla_tek()      (çıktı: PAFTA)
  · ÇOKLU ASANSÖR  sayfası  ->  hesapla_coklu()    (çıktı: PAFTA-COKLU)
formüllerinin birebir Python karşılığıdır.
"""
from . import tables as T
from .steps import (Bolum, veri, hesap, metin, tr, trn, yukari_yuvarla,
                    excel_round, sayi_mi)


# =====================================================================
#  ORTAK YARDIMCILAR
# =====================================================================
def _bodrum_oku(deger):
    """
    Bodrum (ana giriş altı) durak adedini okur.
    Dönen: (Nb, hata)   —  boş / None  →  (0, None)
    """
    if deger is None or deger == "":
        return 0, None
    if not sayi_mi(deger):
        return 0, ("HESAP HATASI: ⑪ bodrum durak adedi sayı olmalıdır "
                   f"(0 – {T.BODRUM_AZAMI} arası tam sayı ya da boş).")
    if float(deger) != int(deger) or deger < 0 or deger > T.BODRUM_AZAMI:
        return 0, (f"HESAP HATASI: ⑪ bodrum durak adedi 0 ile {T.BODRUM_AZAMI} arasında "
                   "tam sayı olmalıdır (ana giriş altında hizmet verilen durak adedi).")
    return int(deger), None


def _hesap_standardi(bina_yuksekligi, yapi_yuksekligi):
    """BYKHY md.4 — yüksek yapı ölçütü."""
    by = bina_yuksekligi or 0
    yy = yapi_yuksekligi or 0
    return "Yükseltilmiş" if (by > T.YUKSEK_BINA_YUKSEKLIK or yy > T.YUKSEK_YAPI_YUKSEKLIK) else "Standart"


def _nufus_satirlari(bina_tipi, hizli1, hizli2, ek_satirlar=None):
    """
    ⑤/⑥ hızlı giriş kutularını Tablo-1 kalemlerine çevirir.
    Dönen: (satırlar, b)   satır = {aciklama, miktar, kalem, birim, katsayi, c}
    """
    satirlar = []

    def kalem_ekle(aciklama, miktar, kalem):
        if kalem and sayi_mi(miktar):
            t = T.TABLO_1[kalem]
            satirlar.append({
                "aciklama": aciklama, "miktar": miktar, "kalem": kalem,
                "birim": t["birim"], "katsayi": t["katsayi"],
                "c": miktar * t["katsayi"],
            })

    bt = bina_tipi or ""
    if bt == "Konut":
        kalem_ekle("↑ ⑤ hızlı girişinden (daire adedi)", hizli1, "KONUT — İlk yatak odası")
        if sayi_mi(hizli1) and sayi_mi(hizli2):
            kalem_ekle("↑ ⑥ hızlı girişinden (daire × diğer oda)", hizli1 * hizli2, "KONUT — Diğer oda")
    elif bt.startswith("İş Merkezi"):
        kalem_ekle("↑ ⑤ toplam çalışma alanı", hizli1, "İŞ MERKEZİ — Çalışma alanı")
    elif bt.startswith("Kamu"):
        kalem_ekle("↑ ⑤ toplam çalışma alanı", hizli1, "RESMİ BİNA — Çalışma alanı")
    elif bt.startswith("Otel"):
        kalem_ekle("↑ ⑤ toplam yatak sayısı", hizli1, "OTEL — Yatak")
    elif bt == "Hastane":
        kalem_ekle("↑ ⑤ toplam yatak sayısı", hizli1, "HASTANE — Yatak")
    elif bt == "Katlı Otopark":
        kalem_ekle("↑ ⑤ özel amaçlı araç adedi", hizli1, "OTOPARK — Özel araç")
        kalem_ekle("↑ ⑥ ticari amaçlı araç adedi", hizli2, "OTOPARK — Ticari araç")

    for s in (ek_satirlar or []):
        kalem = s.get("kalem")
        miktar = s.get("miktar")
        if kalem in T.TABLO_1 and sayi_mi(miktar):
            t = T.TABLO_1[kalem]
            satirlar.append({
                "aciklama": s.get("aciklama") or "Ek nüfus kalemi", "miktar": miktar,
                "kalem": kalem, "birim": t["birim"], "katsayi": t["katsayi"],
                "c": miktar * t["katsayi"],
            })

    b = excel_round(sum(s["c"] for s in satirlar), 6)
    return satirlar, b


def _nufus_bolunmus(bina_tipi, hizli1, hizli2, b):
    """
    (aciklamalar, notlar) — ilk satır Tablo-1 KURALIDIR (yöntem açıklaması,
    ekranda ⓘ içinde), kalanlar bu projenin türetimidir (ekranda görünür).
    """
    satirlar = [x for x in _nufus_aciklamasi(bina_tipi, hizli1, hizli2, b) if x]
    if not satirlar:
        return [], []
    return satirlar[:1], satirlar[1:]


def _nufus_aciklamasi(bina_tipi, hizli1, hizli2, b):
    """PAFTA sayfasındaki nüfus cümlesi."""
    bt = bina_tipi or ""
    if bt == "Konut":
        t1 = ("Tablo-1: Her dairenin ilk yatak odası için 2 kişi, diğer odaların her biri için "
              "1 kişi alınır; mutfak ve ıslak hacimler hesaba katılmaz.")
        if sayi_mi(hizli2):
            if float(hizli2).is_integer():
                t2 = (f"Daireler {trn(hizli2,0)}+1 olup bir dairede sayılan oda adedi "
                      f"{trn(hizli2+1,0)} olarak alınmıştır (1 ilk yatak odası + {trn(hizli2,0)} diğer oda). "
                      f"Bir dairedeki kişi sayısı = 2 + ({trn(hizli2,0)} × 1) = {trn(2+hizli2,0)} kişi.")
            else:
                t2 = (f"Daire başına ortalama diğer oda adedi {tr(hizli2)} alınmıştır. "
                      f"Bir dairedeki ortalama kişi sayısı = 2 + {tr(hizli2)} = {tr(2+hizli2)} kişi.")
            t3 = f"Daire adedi {trn(hizli1,0)}  →  b = {trn(hizli1,0)} × {trn(2+hizli2,2)} = {trn(b,2)} kişi"
        else:
            t2, t3 = "", f"b = Σc = {trn(b,2)} kişi"
        return [t1, t2, t3]
    if bt.startswith("İş Merkezi") or bt.startswith("Kamu"):
        return ["Tablo-1: Çalışma alanının her 12 m²si için 1 kişi alınır.",
                f"Binadaki toplam çalışma alanı {trn(hizli1,2)} m² olarak alınmıştır.",
                f"b = {trn(hizli1,2)} ÷ 12 = {trn(b,2)} kişi"]
    if bt.startswith("Otel"):
        return ["Tablo-1: Her yatak için 1 kişi alınır.",
                f"Binadaki toplam yatak sayısı {trn(hizli1,0)} olarak alınmıştır.",
                f"b = {trn(hizli1,0)} × 1 = {trn(b,2)} kişi"]
    if bt == "Hastane":
        return ["Tablo-1: Her yatak için 3 kişi alınır.",
                f"Binadaki toplam yatak sayısı {trn(hizli1,0)} olarak alınmıştır.",
                f"b = {trn(hizli1,0)} × 3 = {trn(b,2)} kişi"]
    if bt == "Katlı Otopark":
        return ["Tablo-1: Özel amaçlı araç başına 1 kişi, ticari amaçlı araç başına 1,5 kişi alınır.",
                f"Özel amaçlı araç adedi {trn(hizli1,0)}, ticari amaçlı araç adedi {trn(hizli2 or 0,0)} olarak alınmıştır.",
                f"b = ({trn(hizli1,0)} × 1) + ({trn(hizli2 or 0,0)} × 1,5) = {trn(b,2)} kişi"]
    return ["Nüfus MMO/697 Tablo-1'e göre hesaplanmıştır.",
            "Nüfus, ayrıntılı nüfus tablosundan alınmıştır.",
            f"b = Σc = {trn(b,2)} kişi  (ayrıntılı nüfus tablosundan)"]


# =====================================================================
#  TEK ASANSÖR   —   HESAPLAMA sayfası  ->  PAFTA
# =====================================================================
def hesapla_tek(g: dict) -> dict:
    """
    g (girdiler):
      bina_tipi, bina_yuksekligi, yapi_yuksekligi, N, hizli1, hizli2, h, P,
      kapi_genisligi, kapi_tipi
      opsiyonel: bodrum, manuel_k, manuel_V, manuel_ta, manuel_tk, manuel_tg,
                 manuel_tp, manuel_adet, ek_nufus[], proje_adi, isveren,
                 pafta_no, tarih
    """
    U = []                       # uyarılar
    hata = None

    bina_tipi = g.get("bina_tipi")
    if not isinstance(bina_tipi, str):
        bina_tipi = str(bina_tipi) if bina_tipi is not None else ""
    t10 = T.TABLO_10.get(bina_tipi)
    if t10 is None:
        return {"hata": "HESAP HATASI: Bina tipi listeden seçilmelidir."}

    N   = g.get("N")
    P   = g.get("P")
    h   = g.get("h")
    kg_ = g.get("kapi_genisligi")
    kt  = g.get("kapi_tipi")
    by  = g.get("bina_yuksekligi")
    yy  = g.get("yapi_yuksekligi")

    # ---- Nb : ana giriş ALTINDA hizmet verilen durak adedi (bodrum)
    Nb, Nb_hata = _bodrum_oku(g.get("bodrum"))
    if Nb_hata:
        hata = Nb_hata

    standart = _hesap_standardi(by, yy)                       # C8
    hiz_grubu = t10["hiz_grubu"]                              # C17
    k_tipi    = t10["k_tipi"]                                 # C6
    yuk_kg    = T.tablo7_yuk(P)                               # E13
    p         = 0.8 * P if sayi_mi(P) else None               # C15

    # ---- nüfus
    nufus_satirlari, b = _nufus_satirlari(bina_tipi, g.get("hizli1"), g.get("hizli2"),
                                          g.get("ek_nufus"))
    n_artis = 0.3 if (b or 0) < 200 else 0.25                 # C21
    B = yukari_yuvarla(b * (1 + n_artis), 0) if sayi_mi(b) else None   # C22

    # ---- k (taşınacak insan yüzdesi)
    manuel_k = g.get("manuel_k")
    k_notu = ""
    if bina_tipi.startswith("Kamu") and sayi_mi(manuel_k) and 0 < manuel_k <= 1:
        k = manuel_k
        k_notu = "Manuel giriş"
    elif k_tipi is None:
        if sayi_mi(manuel_k) and 0 < manuel_k <= 1:
            k, k_notu = manuel_k, "Manuel giriş (Tablo-9'da bu bina tipi yok)"
        else:
            k, k_notu = None, "Manuel k gerekli"
    else:
        k = T.TABLO_9[k_tipi][standart]
        k_notu = "Tablo-9"
        if bina_tipi.startswith("Kamu"):
            k_notu = "Tablo-9'da kamu yok → İş Merkezi %k varsayıldı"
            U.append("Kamu binaları MMO/697 Tablo-9'da yoktur; %k için İŞ MERKEZİ "
                     "satırı varsayılmıştır. Farklı bir oran gerekiyorsa manuel k girin.")
    if bina_tipi.startswith("Kamu"):
        U.append("Kamu binaları MMO/697 Tablo-2'de de yoktur; asgari hız için "
                 "BÜRO VE İŞ MERKEZİ grubu varsayılmıştır. Bu iki varsayım paftaya "
                 "yazılmıştır.")

    # ---- V (kabin hızı)
    #  Tablo-2 asgari hızı, asansörün DURDUĞU toplam kat adedine göre seçilir:
    #  ana giriş üstü N kat + ana giriş + bodrumdaki Nb durak.
    durak = (N + 1 + Nb) if sayi_mi(N) else None
    V_min = T.tablo2_min_hiz(hiz_grubu, durak) if (hiz_grubu and durak) else None   # I68
    manuel_V = g.get("manuel_V")
    if sayi_mi(manuel_V) and manuel_V not in T.GECERLI_HIZLAR:
        hata = ("HESAP HATASI: Manuel hız geçersiz — listeden seçin "
                "(0,63 / 1 / 1,6 / 1,75 / 2 / 2,5 / 3 / 3,5 / 5 / 6 m/s)")
        V = None
    elif sayi_mi(manuel_V):
        V = manuel_V
    else:
        V = V_min

    V_notu = ""
    if V is None:
        V_notu = "Tablo-2'de bu bina tipi yok — hız proje kararıdır; gerekçesini paftaya yazın."
    elif V_min is None:
        V_notu = "Tablo-2'de bu bina tipi yok — hız tümüyle proje kararıdır; gerekçesini paftaya yazın."
    elif V < V_min:
        V_notu = (f"⚠ Tablo-2 minimumu {tr(V_min)} m/s — seçilen {tr(V)} m/s bunun ALTINDA. "
                  f"Bekleme süresi sağlandığı için hesap geçerlidir; gerekçeyi paftaya yazın.")
        U.append(V_notu)
    elif V > V_min:
        V_notu = f"Tablo-2 minimumu {tr(V_min)} m/s — seçilen {tr(V)} m/s (üstü)."
    else:
        V_notu = f"Tablo-2 minimumu uygulandı: {tr(V)} m/s."

    # ---- tablo değerleri
    H = T.tablo3_H(N, P) if (sayi_mi(N) and sayi_mi(P)) else None
    S = T.tablo5_S(N, P) if (sayi_mi(N) and sayi_mi(P)) else None

    t4_ta, t4_tk = T.tablo4_ta_tk(kg_, kt)
    t6_tg = T.tablo6_tg(V)
    t8_tp = T.tablo8_tp(kg_)

    mta, mtk, mtg, mtp = (g.get("manuel_ta"), g.get("manuel_tk"),
                          g.get("manuel_tg"), g.get("manuel_tp"))
    ta = mta if sayi_mi(mta) else t4_ta
    tk = mtk if sayi_mi(mtk) else t4_tk
    tg = mtg if sayi_mi(mtg) else t6_tg
    tp = mtp if sayi_mi(mtp) else t8_tp
    elle_sure = sum(1 for x in (mta, mtk, mtg, mtp) if sayi_mi(x))
    if elle_sure:
        U.append(f"⚠ {elle_sure} adet süre imalatçı verisiyle değiştirildi (MMO Tablo-4/6/8 yerine). "
                 "Paftada marka-model ve teknik föy referansı belirtilmelidir.")
    if kg_ in T.TABLO_4_ARA and not (sayi_mi(mta) and sayi_mi(mtk)):
        U.append(f"⚠ {kg_} mm MMO/697 Tablo-4'te basılı değildir; ta/tk komşu satırlar "
                 "arasında doğrusal enterpolasyonla bulunmuştur. İmalatçı katalog "
                 "değeri varsa manuel ta/tk girilmesi tercih edilir.")
    if kg_ in T.TABLO_8_ARA and not sayi_mi(mtp):
        U.append(f"⚠ {kg_} mm ISO 8100-32:2020 Tablo 6 kapsamı dışındadır (tablo 800 mm'de "
                 "başlar); tp = 1,3 s, 800→900 mm eğiminden dış değerlemeyle alınmıştır "
                 "(emniyetli taraf). İmalatçı verisi varsa manuel tp girin.")
    U += T.erisilebilirlik_uyarilari(P, kg_)

    # ---- doğrulama (E45 / H45 karşılığı)
    if hata is None:
        hata = _dogrula_tek(g, b, N, P, kg_, kt, ta, tk, tg, tp, k, V, h, by, yy, k_tipi)

    # ---- toplam seyahat mesafesi (avan Hk için) — bodrum dâhil
    toplam_seyahat = ((N + Nb) * h) if (sayi_mi(N) and sayi_mi(h)) else None

    # ---- tur süresi
    tv = h / V if (sayi_mi(h) and sayi_mi(V) and V) else None                 # C33
    ts = (ta + tk + tg - tv) if all(sayi_mi(x) for x in (ta, tk, tg, tv)) else None  # C34
    TR = (2 * H * tv + (S + 1) * ts + 2 * p * tp) \
        if all(sayi_mi(x) for x in (H, tv, S, ts, p, tp)) else None           # C35
    R = (300 * p / TR) if (sayi_mi(TR) and TR and sayi_mi(p)) else None       # C36

    Izul = t10["yukseltilmis"] if standart == "Yükseltilmiş" else t10["standart"]  # K68

    # ---- asansör adedi
    adet_hesap = None
    tasima_adedi = bekleme_adedi = None
    if all(sayi_mi(x) for x in (B, k, R, TR, Izul)) and R and Izul:
        tasima_adedi = yukari_yuvarla(B * k / R, 0)
        bekleme_adedi = yukari_yuvarla(TR / Izul, 0)
        adet_hesap = int(max(1, tasima_adedi, bekleme_adedi))
    manuel_adet = g.get("manuel_adet")
    adet = int(manuel_adet) if (sayi_mi(manuel_adet) and manuel_adet >= 1) else adet_hesap
    Ieer = (TR / adet) if (sayi_mi(TR) and adet) else None                    # C38

    sartli = t10["sartli"]
    esik_standart = t10["standart"]
    esik_yukseltilmis = t10["yukseltilmis"]

    # ---- SONUÇ (C44)
    if hata:
        sonuc = hata
    elif all(sayi_mi(x) for x in (adet, R, B, k, Ieer)) and \
            adet * R >= B * k and Ieer <= Izul:
        sonuc = f"{standart} kriteri karşılanıyor"
    elif sayi_mi(sartli) and sartli and all(sayi_mi(x) for x in (adet, R, B, k, Ieer)) and \
            adet * R >= B * k and Ieer <= sartli:
        sonuc = (f"Şartlı Kabul (taahhütname ile) — Standart için "
                 f"{int(yukari_yuvarla(TR/esik_standart,0))} adet gerekir")
    elif sayi_mi(manuel_adet):
        sonuc = (f"Kabul Edilmez — seçilen {int(manuel_adet)} adet asansör bu bina için "
                 f"UYGUN DEĞİLDİR; en az {adet_hesap} adet gerekir")
    else:
        sonuc = "Kabul Edilmez — girdileri/kriteri kontrol edin"

    if hata:
        sonuc_cumlesi = hata
    elif sonuc.startswith("Kabul"):
        sonuc_cumlesi = ("Bekleme süresi kriteri sağlanmıyor; kabin kapasitesi, hız veya "
                         "asansör adedi gözden geçirilmelidir.")
    elif sonuc.startswith("Şartlı"):
        sonuc_cumlesi = (f"Toplamda {adet} adet {trn(P,0)} kişilik ({trn(yuk_kg,0)} kg), {tr(V)} m/s "
                         f"hızında asansör önerilmektedir. Bekleme süresi {tr(Ieer,1)} sn olup "
                         f"MMO/697 Tablo-10 şartlı kabul sınırı {trn(sartli,0)} sn içindedir; taahhütname ile "
                         f"uygundur. Standart sınır ({trn(esik_standart,0)} sn) için "
                         f"{int(yukari_yuvarla(TR/esik_standart,0))} adet gerekir.")
    else:
        sonuc_cumlesi = (f"Toplamda {adet} adet {trn(P,0)} kişilik ({trn(yuk_kg,0)} kg), {tr(V)} m/s "
                         f"hızında asansör yapılması uygundur.")

    # ================================================================
    #  PAFTA BÖLÜMLERİ
    # ================================================================
    b1 = Bolum("BİNADA BULUNAN İNSAN SAYISININ TESPİTİ (B)", "MMO/697 Tablo-1")
    b1["adimlar"] = [
        veri("", "Bina tipi / hesap standardı", f"{bina_tipi} / {standart}", "", "MMO Tablo-9/10"),
        veri("N", "Kat sayısı (ana giriş üstü)", N, "kat", "Projeden", 0),
        veri("Nb", "Bodrum durak adedi (ana giriş altı)", Nb, "durak", "Projeden", 0),
        veri("", "Toplam durak adedi  =  N + 1 + Nb", durak, "durak", "MMO/697 Tablo-2", 0),
        veri("", "Bina / yapı yüksekliği", f"{tr(by)} / {tr(yy)}", "m", "BYKHY md.4"),
    ]
    if Nb:
        b1["aciklamalar"].append(T.BODRUM_NOTU)
    _ac, _no = _nufus_bolunmus(bina_tipi, g.get("hizli1"), g.get("hizli2"), b)
    b1["aciklamalar"] += _ac
    b1["notlar"] += _no
    b1["adimlar"] += [
        veri("b", "Binada sürekli bulunan kişi (Σc)", b, "kişi", "Tablo-1"),
        veri("n", "Nüfus artış oranı (b<200 → 0,30 / b≥200 → 0,25)", n_artis, "—", "MMO/697"),
        hesap("B  =  b + ( n · b )",
              f"=  {trn(b,1)} + ( {tr(n_artis)} · {trn(b,1)} )", B, "kişi", "MMO/697", 0),
    ]

    b2 = Bolum("HESAP DEĞERLERİ", "MMO/697 Tablo-2 … Tablo-8")
    b2["adimlar"] = [
        veri("h", "Katlar arası mesafe", h, "m", "Projeden"),
        veri("", "Toplam seyahat mesafesi  =  ( N + Nb ) · h", toplam_seyahat, "m",
             "Projeden — avan kuyu yüksekliği bu değerden türer"),
        veri("V", "Kabin hızı", V, "m/s",
             f"Tablo-2 (durak = {durak})" if durak else "Tablo-2"),
        veri("H", "Ortalama en yüksek dönüş katı", H, "—", "Tablo-3", 4),
        hesap("tv  =  h / V", f"=  {tr(h)} / {tr(V)}", tv, "s", "h/V"),
        veri("S", "Ortalama durak adedi", S, "—", "Tablo-5", 4),
        hesap("ts  =  ta + tk + tg − tv",
              f"=  {tr(ta)} + {tr(tk)} + {tr(tg)} − {tr(tv)}", ts, "s", "MMO/697"),
        veri("P", "Kabin kişi adedi", P, "kişi", T.tablo7_kaynagi(P), 0),
        veri("p", "İndirgenmiş kişi sayısı  p = 0,8·P", p, "kişi", "MMO/697", 1),
        veri("tp", "Kişi transfer zamanı", tp, "s",
             "İmalatçı verisi" if sayi_mi(mtp) else T.tablo8_kaynagi(kg_)),
        veri("ta", "Kapı açılma zamanı", ta, "s",
             "İmalatçı verisi" if sayi_mi(mta) else T.tablo4_kaynagi(kg_)),
        veri("tk", "Kapı kapanma zamanı", tk, "s",
             "İmalatçı verisi" if sayi_mi(mtk) else T.tablo4_kaynagi(kg_)),
        veri("tg", "Tek katı geçme zamanı", tg, "s",
             "İmalatçı verisi" if sayi_mi(mtg) else T.tg_kaynagi(V)),
    ]
    b2["notlar"] = [x for x in [V_notu] if x]

    b3 = Bolum("ASANSÖRÜN BİR SEFERİ İÇİN GEREKLİ SEYİR ZAMANI (TR)", "MMO/697 s.11-12")
    b3["adimlar"] = [
        hesap("TR  =  2·H·tv  +  ( S + 1 )·ts  +  2·p·tp",
              (f"=  2·{tr(H)}·{tr(tv)} + ( {tr(S)}+1 )·{tr(ts)} + 2·{tr(p,1)}·{tr(tp,1)}"
               if all(sayi_mi(x) for x in (H, tv, S, ts, p, tp)) else "—"),
              TR, "s", "MMO/697 s.11"),
    ]

    b4 = Bolum("GEREKLİ ASANSÖR SAYISININ HESABI", "MMO/697 s.12")
    b4["adimlar"] = [
        hesap("R  =  5 · 60 · p  /  TR",
              f"=  5·60·{tr(p,1)} / {tr(TR)}" if all(sayi_mi(x) for x in (p, TR)) else "—",
              R, "kişi / 5 dk", "MMO/697", 1),
        veri("k", "Taşınacak insan yüzdesi", k, "—", k_notu, 4),
    ]
    if all(sayi_mi(x) for x in (tasima_adedi, bekleme_adedi)):
        satir = (f"Taşıma adedi = {int(tasima_adedi)};  Bekleme adedi = {int(bekleme_adedi)}  "
                 f"(uygulanan sınır Izul = {trn(Izul,0)} sn — Tablo-10 {standart})"
                 f"  →  Nihai gerekli sayı = {adet_hesap} adet")
        if sayi_mi(sartli) and sartli:
            satir += (f"   |   Şartlı Kabul sınırı ({trn(sartli,0)} sn) için "
                      f"{int(yukari_yuvarla(TR/sartli,0))} adet yeterli olurdu (taahhütname gerekir)")
        b4["notlar"].append(satir)
    b4["adimlar"].append(veri("n", "Uygulanan asansör adedi", adet, "adet",
                              "Elle seçildi" if sayi_mi(manuel_adet) else "MAX[taşıma; bekleme]", 0))

    b5 = Bolum("BEKLEME ZAMANI (Izul) KONTROLÜ", "MMO/697 Tablo-10")
    b5["adimlar"] = [
        hesap("Ieer  =  TR / n", f"=  {tr(TR)} / {adet}" if (sayi_mi(TR) and adet) else "—",
              Ieer, "s", "MMO/697", 1),
        veri("Izul", f"İzin verilen bekleme süresi ({standart})", Izul, "s", "Tablo-10", 0),
    ]
    if sayi_mi(Ieer) and sayi_mi(Izul):
        b5["notlar"].append(
            f"{standart} sınır {trn(Izul,0)} sn: "
            + ("SAĞLANIYOR" if Ieer <= Izul else "AŞILIYOR")
            + (f"      |      Şartlı Kabul sınırı {trn(sartli,0)} sn: "
               + ("sağlanıyor" if Ieer <= sartli else "aşılıyor")
               if sayi_mi(sartli) and sartli else "      |      bu bina sınıfında şartlı kabul yoktur"))

    return {
        "tip": "tek",
        "hata": hata,
        "uyarilar": U,
        "girdiler": g,
        "ozet": {
            "bina_tipi": bina_tipi, "standart": standart, "N": N, "P": P, "yuk_kg": yuk_kg,
            "bodrum": Nb, "durak": durak, "toplam_seyahat": toplam_seyahat,
            "p": p, "V": V, "V_min": V_min, "h": h, "b": b, "n_artis": n_artis, "B": B, "k": k,
            "H": H, "S": S, "ta": ta, "tk": tk, "tg": tg, "tp": tp, "tv": tv, "ts": ts,
            "TR": TR, "R": R, "Izul": Izul, "adet": adet, "adet_hesap": adet_hesap,
            "Ieer": Ieer, "sonuc": sonuc, "sonuc_cumlesi": sonuc_cumlesi,
            "esik_sartli": sartli, "esik_standart": esik_standart,
            "esik_yukseltilmis": esik_yukseltilmis,
            "kapi_genisligi": kg_, "kapi_tipi": kt,
            "tasima_adedi": tasima_adedi, "bekleme_adedi": bekleme_adedi,
            "pafta_satiri": (hata if hata else
                             f"  {trn(P,0)} kişilik, {tr(V)} m/s hızında, {adet} adet asansör → {sonuc}"),
        },
        "nufus": nufus_satirlari,
        "bolumler": [b1, b2, b3, b4, b5],
        "oneriler": _oneri_tablosu(g, N, B, k, Izul, standart, sartli,
                                   esik_standart, V_min, h, kg_, kt, P, ta, tk, tp, mtg, V),
    }


#  MANUEL SÜRELERİN FİZİKSEL SINIRLARI
#  ta / tk / tg / tp bir SÜREdir: sıfır ya da negatif olamaz.  Denetimsizken
#  dördü de 0 girilince TR = 24,5 sn çıkıyor, ts = −1,88 sn gibi imkânsız bir
#  ara değer oluşuyor ve program 44 daireli binaya 2 yerine 1 asansör
#  yetiyor diyordu.  Üst sınırlar da imalatçı katalog aralığının çok
#  üstündeki yazım hatalarını ( 999 sn ) yakalar.
MANUEL_SURE_SINIRI = {
    "manuel_ta": (0.1, 30, "ta — kapı açılma süresi"),
    "manuel_tk": (0.1, 30, "tk — kapı kapanma süresi"),
    "manuel_tg": (0.1, 60, "tg — tek katı geçme süresi"),
    "manuel_tp": (0.1, 20, "tp — kişi transfer süresi"),
}


def _manuel_sure_hatasi(g, on_ek=""):
    """Elle girilmiş ta/tk/tg/tp değerlerini fiziksel sınırlara göre denetler."""
    for anahtar, (alt, ust, ad) in MANUEL_SURE_SINIRI.items():
        deger = (g or {}).get(anahtar)
        if deger in (None, ""):
            continue
        if not sayi_mi(deger) or not (alt <= deger <= ust):
            return (f"HESAP HATASI: {on_ek}{ad} elle {tr(deger)} s girilmiş — "
                    f"süre {tr(alt)} - {tr(ust)} s aralığında olmalıdır. "
                    "Sıfır ya da negatif bir süre fiziksel olarak imkânsızdır; "
                    "boş bırakırsanız tablo değeri kullanılır.")
    return None


#  BİNA GİRDİLERİ  —  tek ve çoklu hesapta AYNI kural.  ( Çoklu hesap bu
#  denetimleri hiç yapmıyordu: h = −3 m ile "Yükseltilmiş kriteri
#  karşılanıyor" sonucu üretiyordu. )
def _bina_hatasi(g, N, h, by, yy):
    if not (sayi_mi(N) and 1 <= N <= 30):
        return "HESAP HATASI: Kat sayısı N 1 - 30 aralığında olmalıdır."
    if not sayi_mi(h) or not (0 < h <= 10):
        return (f"HESAP HATASI: ⑦ kat yüksekliği h = {tr(h)} m — "
                "0 ile 10 m arasında olmalıdır.")
    if not (sayi_mi(by) and by >= 0):
        return ("HESAP HATASI: ② bina yüksekliği girilmedi ya da geçersiz — "
                "hesap standardı ( Standart / Yükseltilmiş ) buna göre seçilir.")
    if not (sayi_mi(yy) and yy >= 0):
        return ("HESAP HATASI: ③ yapı yüksekliği girilmedi ya da geçersiz — "
                "hesap standardı ( Standart / Yükseltilmiş ) buna göre seçilir.")
    return None


def _dogrula_tek(g, b, N, P, kg_, kt, ta, tk, tg, tp, k, V, h, by, yy, k_tipi):
    """HESAPLAMA!E45 + H45 doğrulama zinciri."""
    if kg_ not in T.KAPI_GENISLIKLERI:
        return ("HESAP HATASI: ⑨ kapı genişliği listeden seçilmelidir "
                "(700/800/900/1000/1100/1200/1300 mm).")
    if sayi_mi(N) and N > 30:
        return (f"HESAP HATASI: N = {int(N)} > 30. MMO/697 Tablo-3 ve Tablo-5 en fazla 30 katı "
                "kapsar; bu yükseklikte tek bölgeli hesap geçerli değildir, bölgeli (zoned) "
                "trafik hesabı yapılmalıdır.")
    if not sayi_mi(ta) or not sayi_mi(tk):
        return (f"HESAP HATASI: {kg_} mm / {kt} için Tablo-4'te ta-tk karşılığı yok — "
                "'Kabin İçi Oto. Kat K.Ç.' sütunu 1200 ve 1300 mm'de tabloda bulunmaz. "
                "İmalatçı katalog değerini manuel ta/tk alanlarına girin ya da kapı tipini "
                "'Teleskopik Otomatik' / 'Merkezden Açılan Oto.' olarak seçin.")
    if not sayi_mi(tp):
        return (f"HESAP HATASI: {kg_} mm için tp değeri bulunamadı. "
                "İmalatçı değerini manuel tp alanına girin.")
    if not sayi_mi(tg):
        return f"HESAP HATASI: V = {tr(V)} m/s için Tablo-6'da tg değeri yok. tg'yi elle girin."
    bt = g.get("bina_tipi") or ""
    h1, h2 = g.get("hizli1"), g.get("hizli2")
    if ((bt == "Konut" and ((sayi_mi(h1) and h1 > 2000) or (sayi_mi(h2) and h2 > 20)))
            or ((bt.startswith("Otel") or bt == "Hastane") and sayi_mi(h1) and h1 > 20000)
            or (bt == "Katlı Otopark" and ((sayi_mi(h1) and h1 > 20000) or (sayi_mi(h2) and h2 > 20000)))):
        return ("HESAP HATASI: ⑤/⑥ değeri olağandışı — girdiyi kontrol edin "
                "(ondalık ayracı olarak virgül kullanın).")
    if not sayi_mi(b) or b <= 0:
        return "HESAP HATASI: Nüfus girilmedi — ⑤ (ve gerekiyorsa ⑥) kutusunu doldurun"
    if k_tipi is not None and not bt.startswith("Kamu") and sayi_mi(g.get("manuel_k")):
        return "HESAP HATASI: Tablo-9 varken manuel k girilemez"
    if T.kapsam_disi(N, P):
        return "HESAP HATASI: P/N aralık dışı (P: 6-34 kişi, N: 1-30 kat)"
    nb = g.get("bodrum")
    if nb not in (None, "") and _bodrum_oku(nb)[1]:
        return _bodrum_oku(nb)[1]
    bina = _bina_hatasi(g, N, h, by, yy)
    if bina:
        return bina
    sure = _manuel_sure_hatasi(g)
    if sure:
        return sure
    kontroller = [
        (P in T.GECERLI_KAPASITELER),
        (sayi_mi(k) and 0 < k <= 1), (sayi_mi(V) and V > 0),
    ]
    if not all(kontroller):
        return "HESAP HATASI: girdileri ve tablo eşleşmelerini kontrol edin"
    if sayi_mi(h) and not (2 <= h <= 6):
        pass  # yalnız uyarı — hesabı durdurmaz
    return None


def _oneri_tablosu(g, N, B, k, Izul, standart, esik_sartli, esik_standart,
                   V_min, h, kg_, kt, P_secili, ta_secili, tk_secili, tp_secili,
                   manuel_tg, V_secili):
    """
    HESAPLAMA 6) OTOMATİK ÖNERİ bloğu (satır 70-83).
    7 kapasite × 2 hız (Tablo-2 minimumu + bir üst hız).
    """
    if not all(sayi_mi(x) for x in (N, B, k, Izul, h)) or V_min is None:
        return []
    V_ust = T.bir_ust_hiz(V_min)
    satirlar = []
    for kap in (6, 8, 10, 13, 16, 20, 25):
        for V, etiket in ((V_min, "Tablo-2 min"), (V_ust, "bir üst hız")):
            # kapasiteye uygun kapı genişliği — ISO 8100-32:2020 Ek C, Tablo 8
            W = kg_ if kap == P_secili else (800 if kap <= 8 else 900 if kap <= 10
                                             else 1100 if kap <= 20 else 1300)
            if W == kg_:
                ta, tk, tp = ta_secili, tk_secili, tp_secili
            else:
                ta, tk = T.tablo4_ta_tk(W, kt)
                tp = T.tablo8_tp(W)
            tg = manuel_tg if (sayi_mi(manuel_tg) and V == V_secili) else T.tablo6_tg(V)
            H = T.tablo3_H(N, kap)
            S = T.tablo5_S(N, kap)
            if not all(sayi_mi(x) for x in (H, S, ta, tk, tg, tp, V)) or not V:
                continue
            tv = h / V
            ts = ta + tk + tg - tv
            TR = 2 * H * tv + (S + 1) * ts + 2 * (0.8 * kap) * tp
            if TR <= 0:
                continue
            R = 300 * 0.8 * kap / TR
            adet = int(max(1, yukari_yuvarla(B * k / R, 0), yukari_yuvarla(TR / Izul, 0)))
            Ieer = TR / adet
            if Ieer <= Izul:
                sinif = f"{standart} ✔"
                anahtar = 0
            elif sayi_mi(esik_sartli) and esik_sartli and Ieer <= esik_sartli:
                sinif, anahtar = "Şartlı kabul", 100_000_000
            else:
                sinif, anahtar = "Kriteri aşıyor", 100_000_000
            # TS EN 81-70 / TS 9111 erişilebilirlik ölçütünü karşılamayan seçenek
            # (630 kg altı kabin veya 800 mm altı kapı) sıralamaya alınmaz.
            erisim = T.erisilebilir_mi(kap, W)
            siralama = 999_999_999 if not erisim else anahtar + adet * 10_000 + kap * 10
            satirlar.append({
                "secenek": (f"{kap} kişilik ({trn(T.tablo7_yuk(kap),0)} kg) — {tr(V)} m/s"
                            f"  ·  {W} mm kapı ({etiket})"
                            + ("" if erisim else "  ⚠ TS EN 81-70 erişilebilirlik ölçütü dışı")),
                "kapasite": kap, "V": V, "kapi": W, "adet": adet, "Ieer": Ieer,
                "sinif": sinif, "TR": TR, "R": R, "_siralama": siralama,
                "erisilebilir": erisim,
            })
    if satirlar:
        en_iyi = min(satirlar, key=lambda s: s["_siralama"])
        if en_iyi["_siralama"] < 999_999_999:
            en_iyi["onerilen"] = True
    return satirlar


# =====================================================================
#  ÇOKLU ASANSÖR   —   ÇOKLU ASANSÖR sayfası  ->  PAFTA-COKLU
# =====================================================================
def hesapla_coklu(g: dict) -> dict:
    """
    g: bina_tipi, bina_yuksekligi, yapi_yuksekligi, N, hizli1, hizli2, h,
       bodrum (ortak), manuel_k, manuel_V (ortak), ek_nufus[],
       asansorler: [{P, kapi_genisligi, kapi_tipi, V, durak, h, bodrum,
                     manuel_ta, manuel_tk, manuel_tg, manuel_tp}, ...]  (1-4 adet)
    """
    U, hata = [], None
    bina_tipi = g.get("bina_tipi")
    if not isinstance(bina_tipi, str):
        bina_tipi = str(bina_tipi) if bina_tipi is not None else ""
    t10 = T.TABLO_10.get(bina_tipi)
    if t10 is None:
        return {"hata": "HESAP HATASI: Bina tipi listeden seçilmelidir."}

    N  = g.get("N")
    h  = g.get("h")
    by = g.get("bina_yuksekligi")
    yy = g.get("yapi_yuksekligi")
    Nb_ortak, Nb_hata = _bodrum_oku(g.get("bodrum"))
    if Nb_hata:
        hata = Nb_hata

    #  BİNA GİRDİLERİ  —  tek asansör hesabıyla AYNI denetim zinciri.
    #  ( Bu blok yokken h = −3 m, h = 0, h = 99 ya da boş bırakılmış bina /
    #    yapı yüksekliği çokluda hata vermeden geçiyordu: yükseklikler boşken
    #    hesap sessizce "Standart" sınıfına düşüyordu. )
    bina = _bina_hatasi(g, N, h, by, yy)
    if bina:
        return {"hata": bina}
    #  Ortak manuel süreler + asansör bazında girilenler
    sure = _manuel_sure_hatasi(g)
    if sure:
        return {"hata": sure}
    for i, a in enumerate(g.get("asansorler") or [], 1):
        sure = _manuel_sure_hatasi(a, on_ek=f"ASANSÖR-{i} — ")
        if sure:
            return {"hata": sure}

    standart = _hesap_standardi(by, yy)
    hiz_grubu = t10["hiz_grubu"]
    k_tipi = t10["k_tipi"]

    nufus_satirlari, b = _nufus_satirlari(bina_tipi, g.get("hizli1"), g.get("hizli2"),
                                          g.get("ek_nufus"))
    n_artis = 0.3 if (b or 0) < 200 else 0.25
    B = yukari_yuvarla(b * (1 + n_artis), 0) if sayi_mi(b) else None

    manuel_k = g.get("manuel_k")
    if bina_tipi.startswith("Kamu") and sayi_mi(manuel_k) and 0 < manuel_k <= 1:
        k, k_notu = manuel_k, "Manuel giriş"
    elif k_tipi is None:
        if sayi_mi(manuel_k) and 0 < manuel_k <= 1:
            k, k_notu = manuel_k, "Manuel giriş (Tablo-9'da bu bina tipi yok)"
        else:
            k, k_notu = None, "Manuel k gerekli"
    else:
        #  Tablo-9'da değeri olan bir bina tipinde manuel k SESSİZCE yok
        #  sayılmamalıdır — tek asansör hesabında olduğu gibi burada da
        #  açıkça reddedilir.  ( Aksi hâlde kullanıcı bir değer yazar, program
        #  onu görmezden gelir ve hiçbir şey söylemezdi. )
        if sayi_mi(manuel_k):
            return {"hata": "HESAP HATASI: Tablo-9 varken manuel k girilemez"}
        k, k_notu = T.TABLO_9[k_tipi][standart], "Tablo-9"
        if bina_tipi.startswith("Kamu"):
            k_notu = "Tablo-9'da kamu yok → İş Merkezi %k varsayıldı"
            U.append("Kamu binaları MMO/697 Tablo-9'da yoktur; %k için İŞ MERKEZİ "
                     "satırı varsayılmıştır. Farklı bir oran gerekiyorsa manuel k girin.")
    if bina_tipi.startswith("Kamu"):
        U.append("Kamu binaları MMO/697 Tablo-2'de de yoktur; asgari hız için "
                 "BÜRO VE İŞ MERKEZİ grubu varsayılmıştır. Bu iki varsayım paftaya "
                 "yazılmıştır.")

    durak_ortak = (N + 1 + Nb_ortak) if sayi_mi(N) else None
    V_grup_min = T.tablo2_min_hiz(hiz_grubu, durak_ortak) if (hiz_grubu and durak_ortak) else None
    manuel_V = g.get("manuel_V")
    V_ortak = manuel_V if sayi_mi(manuel_V) else V_grup_min

    girisler = [a for a in (g.get("asansorler") or []) if sayi_mi(a.get("P"))]
    if not girisler:
        hata = "HESAP HATASI: en az bir asansör girin"

    asansorler = []
    for i, a in enumerate(girisler, 1):
        P = a.get("P")
        kg_ = a.get("kapi_genisligi")
        kt = a.get("kapi_tipi")
        # durak sayısı (ana giriş dâhil) — boşsa ortak N+1
        d_in = a.get("durak")
        if sayi_mi(d_in):
            if not (float(d_in).is_integer() and 2 <= d_in <= (N or 0) + 1):
                hata = hata or ("HESAP HATASI: durak sayısı geçersiz — 2 ile ortak durak sayısı "
                                "(N+1) arasında tam sayı girin veya boş bırakın")
                Ni = None
            else:
                Ni = int(d_in) - 1
        else:
            Ni = N
        hi = a.get("h") if sayi_mi(a.get("h")) else h
        # bodrum: asansör bazında; boş bırakılırsa ortak değer kullanılır
        if a.get("bodrum") in (None, ""):
            Nbi = Nb_ortak
        else:
            Nbi, nb_h = _bodrum_oku(a.get("bodrum"))
            if nb_h:
                hata = hata or f"HESAP HATASI: ASANSÖR-{i} — " + nb_h.split(": ", 1)[-1]
        Vmin_i = (T.tablo2_min_hiz(hiz_grubu, (Ni + 1 + Nbi))
                  if (hiz_grubu and sayi_mi(Ni)) else None)
        Vi_in = a.get("V")
        if sayi_mi(Vi_in) and Vi_in not in T.GECERLI_HIZLAR:
            hata = hata or "HESAP HATASI: Manuel V geçersiz — geçerli hız listesinden seçin"
            Vi = None
        else:
            Vi = Vi_in if sayi_mi(Vi_in) else (Vmin_i if sayi_mi(Vmin_i) else V_ortak)
        if sayi_mi(Vi) and sayi_mi(Vmin_i) and Vi < Vmin_i:
            U.append(f"⚠ ASANSÖR-{i}: seçilen {tr(Vi)} m/s, Tablo-2 minimumu {tr(Vmin_i)} m/s "
                     "altındadır — bekleme kriteri esas alındı, gerekçeyi paftaya yazın.")

        # ---- süreler: tablo değeri, imalatçı verisi varsa onunla ezilir
        t4_ta, t4_tk = T.tablo4_ta_tk(kg_, kt)
        t6_tg = T.tablo6_tg(Vi)
        t8_tp = T.tablo8_tp(kg_)
        mta_i, mtk_i = a.get("manuel_ta"), a.get("manuel_tk")
        mtg_i, mtp_i = a.get("manuel_tg"), a.get("manuel_tp")
        ta = mta_i if sayi_mi(mta_i) else t4_ta
        tk = mtk_i if sayi_mi(mtk_i) else t4_tk
        tg = mtg_i if sayi_mi(mtg_i) else t6_tg
        tp = mtp_i if sayi_mi(mtp_i) else t8_tp
        elle_i = sum(1 for x in (mta_i, mtk_i, mtg_i, mtp_i) if sayi_mi(x))
        if elle_i:
            U.append(f"⚠ ASANSÖR-{i}: {elle_i} adet süre imalatçı verisiyle değiştirildi "
                     "(MMO Tablo-4/6/8 yerine). Paftada marka-model ve teknik föy "
                     "referansı belirtilmelidir.")
        if kg_ in T.TABLO_4_ARA and not (sayi_mi(mta_i) and sayi_mi(mtk_i)):
            U.append(f"⚠ ASANSÖR-{i}: {kg_} mm MMO/697 Tablo-4'te basılı değildir; ta/tk "
                     "komşu satırlar arasında doğrusal enterpolasyonla bulunmuştur.")
        if kg_ in T.TABLO_8_ARA and not sayi_mi(mtp_i):
            U.append(f"⚠ ASANSÖR-{i}: {kg_} mm ISO 8100-32:2020 Tablo 6 kapsamı dışındadır; "
                     "tp = 1,3 s dış değerlemeyle alınmıştır (emniyetli taraf).")
        U += T.erisilebilirlik_uyarilari(P, kg_, on_ek=f"ASANSÖR-{i}: ")
        H = T.tablo3_H(Ni, P) if (sayi_mi(Ni) and sayi_mi(P)) else None
        S = T.tablo5_S(Ni, P) if (sayi_mi(Ni) and sayi_mi(P)) else None
        p = 0.8 * P if sayi_mi(P) else None
        tv = hi / Vi if (sayi_mi(hi) and sayi_mi(Vi) and Vi) else None
        ts = (ta + tk + tg - tv) if all(sayi_mi(x) for x in (ta, tk, tg, tv)) else None
        TR = (2 * H * tv + (S + 1) * ts + 2 * p * tp) \
            if all(sayi_mi(x) for x in (H, tv, S, ts, p, tp)) else None
        R = (300 * p / TR) if (sayi_mi(TR) and TR) else None

        if not sayi_mi(ta) or not sayi_mi(tk):
            hata = hata or (f"HESAP HATASI: ASANSÖR-{i} — {kg_} mm / {kt} için Tablo-4'te ta-tk "
                            "karşılığı yok ('Kabin İçi Oto. Kat K.Ç.' sütunu 1200 ve 1300 mm'de "
                            "tabloda bulunmaz). İmalatçı değerini manuel ta/tk alanlarına girin.")
        if not sayi_mi(tp):
            hata = hata or (f"HESAP HATASI: ASANSÖR-{i} — {kg_} mm için tp değeri bulunamadı; "
                            "imalatçı değerini manuel tp alanına girin.")
        if not sayi_mi(tg):
            hata = hata or (f"HESAP HATASI: ASANSÖR-{i} — hızı için Tablo-6'da tg değeri yok; "
                            "manuel tg girin.")
        if T.kapsam_disi(Ni, P):
            hata = hata or f"HESAP HATASI: ASANSÖR-{i} — P/N aralık dışı (P: 6-34, N: 1-30)"

        asansorler.append({
            "no": i, "ad": f"ASANSÖR-{i}", "P": P, "yuk_kg": T.tablo7_yuk(P),
            "kapi_genisligi": kg_, "kapi_tipi": kt, "N": Ni,
            "durak": (Ni + 1) if sayi_mi(Ni) else None,
            "bodrum": Nbi,
            "durak_toplam": (Ni + 1 + Nbi) if sayi_mi(Ni) else None,
            "toplam_seyahat": ((Ni + Nbi) * hi) if (sayi_mi(Ni) and sayi_mi(hi)) else None,
            "h": hi, "V": Vi, "V_min": Vmin_i, "p": p, "H": H, "S": S,
            "ta": ta, "tk": tk, "tg": tg, "tp": tp, "tv": tv, "ts": ts, "TR": TR, "R": R,
            "elle_sure": elle_i,
            "kaynak_ta": "İmalatçı verisi" if sayi_mi(mta_i) else T.tablo4_kaynagi(kg_),
            "kaynak_tk": "İmalatçı verisi" if sayi_mi(mtk_i) else T.tablo4_kaynagi(kg_),
            "kaynak_tg": "İmalatçı verisi" if sayi_mi(mtg_i) else T.tg_kaynagi(Vi),
            "kaynak_tp": "İmalatçı verisi" if sayi_mi(mtp_i) else T.tablo8_kaynagi(kg_),
            "kaynak_P": T.tablo7_kaynagi(P),
        })

    if sayi_mi(N) and N > 30:
        hata = (f"HESAP HATASI: N = {int(N)} > 30. MMO/697 Tablo-3 ve Tablo-5 en fazla 30 katı "
                "kapsar; bu yükseklikte bölgeli (zoned) trafik hesabı gerekir.")
    if not sayi_mi(b) or b <= 0:
        hata = hata or "HESAP HATASI: Nüfus girilmedi — ⑤/⑥ kutularını doldurun"
    if not sayi_mi(k) or not (0 < k <= 1):
        hata = hata or "HESAP HATASI: k değeri geçersiz — Tablo-9'da yoksa manuel k girin"
    if asansorler and sayi_mi(N):
        en_yuksek = max((a["N"] for a in asansorler if sayi_mi(a["N"])), default=None)
        if en_yuksek is not None and en_yuksek != N:
            hata = hata or ("HESAP HATASI: kat sayısı N, aktif asansörlerin en yüksek durak "
                            "sayısına göre girilmelidir")

    # ---- grup kontrolü (MMO/697 s.12)
    Res = sum(a["R"] for a in asansorler if sayi_mi(a["R"])) if not hata else None
    gereken = (B * k) if all(sayi_mi(x) for x in (B, k)) else None
    ters_toplam = sum(1 / a["TR"] for a in asansorler if sayi_mi(a["TR"]) and a["TR"]) if not hata else None
    TRes = (1 / ters_toplam) if (sayi_mi(ters_toplam) and ters_toplam) else None
    Izul = t10["yukseltilmis"] if standart == "Yükseltilmiş" else t10["standart"]
    sartli = t10["sartli"]

    if hata:
        sonuc = hata
    elif not all(sayi_mi(x) for x in (Res, gereken, TRes)):
        sonuc = "HESAP HATASI: grup değerleri hesaplanamadı"
    elif Res < gereken:
        sonuc = "YETERSİZ — taşıma kapasitesi düşük (Reş<B·k)"
    elif TRes <= Izul:
        sonuc = f"{standart} kriteri karşılanıyor"
    elif sayi_mi(sartli) and sartli and TRes <= sartli:
        sonuc = "Şartlı Kabul (taahhütname ile)"
    else:
        sonuc = "Kabul Edilmez — bekleme süresi şartlı sınırı aşıyor"

    pafta_satiri = hata or ("  " + "  +  ".join(
        f"1 adet {trn(a['P'],0)} kişilik {tr(a['V'])} m/s" for a in asansorler)
        + f"  →  {len(asansorler)} adet asansör  →  {sonuc}")

    # ---- bölümler
    b1 = Bolum("ORTAK BİNA BİLGİLERİ", "MMO/697 Tablo-1")
    b1["adimlar"] = [
        veri("", "Bina tipi / hesap standardı", f"{bina_tipi} / {standart}", "", "MMO Tablo-9/10"),
        veri("N", "Kat sayısı (ana giriş üstü) — grup maksimumu", N, "kat", "Projeden", 0),
        veri("Nb", "Bodrum durak adedi (ana giriş altı) — ortak", Nb_ortak, "durak", "Projeden", 0),
        veri("", "Bina / yapı yüksekliği", f"{tr(by)} / {tr(yy)}", "m", "BYKHY md.4"),
        veri("b", "Binada sürekli bulunan kişi (Σc)", b, "kişi", "Tablo-1"),
        veri("n", "Nüfus artış oranı", n_artis, "—", "MMO/697"),
        hesap("B  =  b + ( n · b )", f"=  {trn(b,1)} + ( {tr(n_artis)} · {trn(b,1)} )",
              B, "kişi", "MMO/697", 0),
        veri("k", "Taşınacak insan yüzdesi", k, "—", k_notu, 4),
    ]
    _ac, _no = _nufus_bolunmus(bina_tipi, g.get("hizli1"), g.get("hizli2"), b)
    b1["aciklamalar"] = _ac
    b1["notlar"] = _no
    if Nb_ortak or any(a.get("bodrum") for a in asansorler):
        b1["aciklamalar"].insert(0, T.BODRUM_NOTU)

    b3 = Bolum("GRUP KONTROLÜ", "MMO/697 s.12 — farklı kapasiteli asansörler")
    b3["aciklamalar"] = ["Reş = ΣRi ≥ B·k    ve    1/TReş = Σ(1/TRi),  TReş ≤ Izul"]
    if not hata and all(sayi_mi(x) for x in (Res, gereken, TRes)):
        b3["notlar"] = [
            "Reş = " + " + ".join(f"R{a['no']}={tr(a['R'],1)}" for a in asansorler)
            + f" = {tr(Res,1)}  ≥  B·k = {tr(gereken,1)}  →  "
            + ("SAĞLANIYOR" if Res >= gereken else "SAĞLANMIYOR"),
            "1/TReş = " + " + ".join(f"1/TR{a['no']} (1/{tr(a['TR'],1)})" for a in asansorler)
            + f"  →  TReş = {tr(TRes,1)} s  ≤  Izul = {trn(Izul,0)} s  →  "
            + ("SAĞLANIYOR" if TRes <= Izul else "SAĞLANMIYOR"),
        ]
    b3["adimlar"] = [
        veri("Reş", "Grubun 5 dk taşıma kapasitesi = ΣR", Res, "kişi/5dk", "MMO/697 s.12", 1),
        veri("B·k", "Gerekli taşıma kapasitesi", gereken, "kişi/5dk", "MMO/697", 1),
        veri("1/TReş", "Ters tur süreleri toplamı = Σ(1/TR)", ters_toplam, "1/s", "MMO/697 s.12", 6),
        veri("TReş", "Grup efektif tur süresi ( = Ieer )", TRes, "s", "MMO/697 s.12", 1),
        veri("Izul", f"İzin verilen bekleme süresi ({standart})", Izul, "s", "Tablo-10", 0),
        veri("n", "Kullanılan asansör adedi", len(asansorler), "adet", "Projeden", 0),
    ]

    return {
        "tip": "coklu",
        "hata": hata,
        "uyarilar": U,
        "girdiler": g,
        "ozet": {
            "bina_tipi": bina_tipi, "standart": standart, "N": N, "h": h,
            "bodrum": Nb_ortak, "durak": durak_ortak,
            "b": b, "n_artis": n_artis, "B": B, "k": k,
            "Res": Res, "gereken": gereken, "TRes": TRes, "Izul": Izul,
            "esik_sartli": sartli, "esik_standart": t10["standart"],
            "esik_yukseltilmis": t10["yukseltilmis"],
            "adet": len(asansorler), "sonuc": sonuc, "pafta_satiri": pafta_satiri,
            "V_grup_min": V_grup_min,
        },
        "asansorler": asansorler,
        "nufus": nufus_satirlari,
        "bolumler": [b1, b3],
    }


# =====================================================================
#  TRAFİK  →  AVAN  KÖPRÜSÜ
# =====================================================================
def trafik_ozeti(sonuc: dict) -> dict:
    """
    Trafik hesabının avan tarafını ilgilendiren küçük özeti.
    Avan hesabı bunu alıp kapasite / hız / kuyu yüksekliği tutarlılığını
    denetler; böylece trafikte yapılan bir revizyon avan sekmesinde sessizce
    eski değerle kalmaz.
    """
    if not isinstance(sonuc, dict) or sonuc.get("hata"):
        return {}
    o = sonuc.get("ozet") or {}
    if sonuc.get("tip") == "tek":
        n = o.get("adet") or 1
        bir = {"P": o.get("P"), "V": o.get("V"), "toplam_seyahat": o.get("toplam_seyahat")}
        return {"tip": "tek", "N": o.get("N"), "bodrum": o.get("bodrum"), "h": o.get("h"),
                "adet": n, "asansorler": [dict(bir) for _ in range(int(n) if sayi_mi(n) else 1)]}
    if sonuc.get("tip") == "coklu":
        return {"tip": "coklu", "N": o.get("N"), "bodrum": o.get("bodrum"), "h": o.get("h"),
                "adet": o.get("adet"),
                "asansorler": [{"P": a.get("P"), "V": a.get("V"),
                                "toplam_seyahat": a.get("toplam_seyahat")}
                               for a in (sonuc.get("asansorler") or [])]}
    return {}
