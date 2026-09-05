# -*- coding: utf-8 -*-
"""
UYGULAMA PROJESİ HESAP MOTORU        ( orkestratör )

Kendi başına HESAP YAPMAZ.  İki mevcut motoru tek girdi setiyle koşturur ve
sonuçlarını tek çıktıda birleştirir:

    engine/mukavemet.py     10 bölüm  —  mukavemet
    engine/avan.py          3-6. bölümler  —  kabin ve kuyu aydınlatması,
                            kurulu güç cetveli, gerilim düşümü ve kesit
                            kontrolü;  ayrıca makine dairesi aydınlatması
                            ve temel topraklama

NİÇİN AVAN MOTORU YENİDEN YAZILMADI:  bu dört hesap avan projesinde zaten
var ve doğrulanmış durumda ( TEST 1 · 6 · 7 ).  Kopyalamak ikinci bir
doğruluk kaynağı yaratır ve ikisi zamanla ayrışır.  Burada yapılan tek şey
ORTAK GİRDİYİ KÖPRÜLEMEK ( engine/uygulama_girdi.kopru ).

AVANIN 1. VE 2. BÖLÜMÜ ALINMAZ:
  · Motor gücü — mukavemet bölüm 1 aynı hesabı MMO 208/7 §2.4'e göre yapar.
    İkisini birden basmak paftada iki farklı motor gücü gösterirdi.
  · Kuvvet hesapları — mukavemet bölüm 9 kuyu tabanı yüklerini TS EN 81-20
    m.5.2.1.8'e göre, ray kuvvetlerini de bölüm 7-8'de ayrıntılı verir.
"""
from engine.avan import hesap as E_AVAN
from engine.uygulama import mukavemet as E_MUK
from engine.avan import tablolar as T
from engine.uygulama import girdi as UG

#  Avanın uygulama projesine giren bölümleri  ( 0-tabanlı sıra )
ELEKTRIK_BOLUMLERI = (2, 3, 4, 5)          # kabin ayd. · kuyu ayd. · TAS · ε

#  AVAN METNİNİN UYGULAMA KARŞILIĞI.  Bu iki not avan paftasında doğrudur —
#  "kesin seçim uygulama projesinde yapılır" der.  Uygulama paftasında ise
#  kendi kendisiyle çelişir:  okuyucunun elindeki belge ZATEN uygulama
#  projesidir.  Bölüm alınırken metin değiştirilir, hesap aynen kalır.
NOT_KARSILIGI = {
    T.SIGORTA_NOTU: T.SIGORTA_NOTU_UYGULAMA,
    ("Aydınlatma ve priz devrelerinde izin verilen gerilim düşümü %1,5'tir; "
     "bu devrelerin uç noktalara kadar düşümü uygulama projesinde kontrol "
     "edilecektir."): T.GERILIM_UC_NOKTA_NOTU_UYGULAMA,
}


#  Kurulu güç cetvelinde sigorta kademesi tablonun dışına taşarsa avan
#  "uygulama projesinde" yazar — burada aynı çelişki.
CETVEL_KARSILIGI = {"uygulama projesinde": "imalatçı verisiyle"}


def _notlari_uyarla(b):
    """Avandan alınan bölümün proje adı geçen metinlerini uygulamaya çevirir.

    Yalnız METİN değişir;  hiçbir sayı ya da kontrol sonucu etkilenmez.
    """
    b = dict(b)
    for alan in ("notlar", "aciklamalar", "ekran_notlari"):
        if b.get(alan):
            b[alan] = [NOT_KARSILIGI.get(x, x) for x in b[alan]]
    if b.get("cetvel"):
        b["cetvel"] = [dict(c, sigorta=CETVEL_KARSILIGI.get(c.get("sigorta"),
                                                            c.get("sigorta")))
                       for c in b["cetvel"]]
    return b


def hesapla(veriler=None):
    """Uygulama projesinin tamamı  —  mukavemet + elektrik + topraklama."""
    eksik = []          # yapılamayan ZORUNLU hesaplar
    g = UG.varsayilanlar()
    g.update(veriler or {})
    g = UG.tamamla(g)
    hata = UG.dogrula(g)
    if hata:
        return {"aktif": False, "hata": hata, "girdi": g}

    muk = E_MUK.hesapla(g)
    if not muk.get("aktif"):                       # olmamalı — dogrula geçti
        return {"aktif": False, "hata": muk.get("hata") or [], "girdi": g}

    av = E_AVAN.hesapla(UG.kopru(g))
    asansor = (av.get("asansorler") or [{}])[0]
    uyarilar = list(muk.get("uyarilar") or [])

    elektrik = []
    if asansor.get("aktif"):
        tum = asansor.get("bolumler") or []
        elektrik = [tum[i] for i in ELEKTRIK_BOLUMLERI if i < len(tum)]
        uyarilar += [u for u in (asansor.get("uyarilar") or [])
                     #  Avanın trafik karşılaştırması uygulama projesinde
                     #  anlamsızdır — burada trafik hesabı yoktur.
                     if "TRAFİK" not in u.upper()]
    else:
        uyarilar.append("⚠ ELEKTRİK HESAPLARI YAPILAMADI: "
                        + str(asansor.get("uyari") or "girdiler eksik"))

    #  Bölüm numaraları uygulama projesinin kendi sırasına göre yeniden yazılır;
    #  avandan gelen "3 - ..." başlığı burada 11. sıradadır.
    bolumler = list(muk.get("bolumler") or [])
    sira = len(bolumler)
    for b in elektrik:
        sira += 1
        b = _notlari_uyarla(b)
        b["baslik"] = f"{sira} - " + _basliktan_ad(b.get("baslik", ""))
        bolumler.append(b)

    mk = av.get("makine_dairesi") or {}
    if mk.get("aktif"):
        sira += 1
        b = _notlari_uyarla(mk["bolum"])
        b["baslik"] = f"{sira} - " + _basliktan_ad(b.get("baslik", ""))
        bolumler.append(b)
    elif mk.get("mk_yok") is False:
        #  Makine dairesi VAR denmiş ama aydınlatması hesaplanamamış:  zorunlu
        #  bir hesap eksiktir, proje "uygun" sayılamaz.
        eksik.append("MAKİNE DAİRESİ AYDINLATMA HESABI YAPILAMADI: "
                     + str(mk.get("uyari") or ""))

    tp = av.get("topraklama") or {}
    if tp.get("aktif"):
        for b in (tp.get("bolumler") or []):
            sira += 1
            b = _notlari_uyarla(b)
            b["baslik"] = f"{sira} - " + _basliktan_ad(b.get("baslik", ""))
            bolumler.append(b)
    elif g.get("temel_a") or g.get("temel_b"):
        #  Temel ölçüsü girilmiş ama topraklama hesaplanamamış — eksik hesap.
        eksik.append("TOPRAKLAMA HESABI YAPILAMADI: "
                     + str(tp.get("uyari") or ""))

    #  GENEL SONUÇ:  bölüm sonuçları + ENGELLEYİCİ uyarılar + EKSİK hesaplar.
    #  Bilgilendirici uyarılar ( reddedilen ofis girdisi, kabin alanı uyarısı … )
    #  uygunluğu engellemez;  engelleyici olanlar ve yapılamayan zorunlu
    #  hesaplar engeller.  Yoksa "bütün bölümler uygun" diye bir proje, içinde
    #  yapılamamış bir hesapla ya da kurulamaz bir geometriyle teslim edilirdi.
    engelleyici = list(av.get("engelleyici") or [])
    uyarilar += [x for x in engelleyici if x not in uyarilar]
    uyarilar += [f"⚠ {x}" for x in eksik]
    uygunlar = [b["sonuc"]["uygun"] for b in bolumler
                if b.get("sonuc") and b["sonuc"].get("uygun") is not None]
    uygunlar += [False] * (len(engelleyici) + len(eksik))
    ozet = dict(muk.get("ozet") or {})
    ao = asansor.get("ozet") or {}
    ozet.update({
        "P_kurulu": ao.get("P_kurulu"), "eps": ao.get("eps"),
        "eps_uygun": ao.get("eps_uygun"), "I": ao.get("I"), "Iz": ao.get("Iz"),
        "akim_uygun": ao.get("akim_uygun"),
        "n_kabin": ao.get("n_kabin"), "n_kuyu": ao.get("n_kuyu"),
        #  Yuvarlanmamış armatür sayıları:  ekranda gösterilmez ama ortak
        #  girdi köprüsünün kopmadığını YUVARLAMA GİZLEMESİN diye özete girer
        #  ( bkz. testler/test_uygulama.py ).
        "Z_kabin": ao.get("Z_kabin"), "Z_kuyu": ao.get("Z_kuyu"),
        "Re": (av.get("ozet") or {}).get("Re"),
        "topraklama_uygun": (av.get("ozet") or {}).get("topraklama_uygun"),
        "elektrik_var": bool(elektrik),
        "tumu_uygun": all(uygunlar),
        "engelleyici": engelleyici, "eksik_hesap": eksik,
    })
    return {
        "aktif": True,
        "baslik": "ASANSÖR UYGULAMA PROJESİ HESAPLARI",
        "girdi": g,
        "bolumler": bolumler,
        "mukavemet_bolum_sayisi": len(muk.get("bolumler") or []),
        "sabitler": muk.get("sabitler"),
        "ozet": ozet,
        "uyarilar": uyarilar,
        "_h": muk.get("_h", {}),
    }


def _basliktan_ad(baslik):
    """'3 -  KABİN AYDINLATMA HESABI'  →  'KABİN AYDINLATMA HESABI'."""
    metin = str(baslik)
    if " - " in metin:
        return metin.split(" - ", 1)[1].strip()
    return metin.strip()
