# -*- coding: utf-8 -*-
"""
TEST 8  —  MUKAVEMET TABLOLARI + GİRDİ SÖZLEŞMESİ  ( uygulama projesi )

engine/uygulama/mukavemet_tablolari.py içindeki her tabloyu KAYNAĞINA karşı
birebir doğrular:  testler/referans_tablolar.json

NİÇİN AYRI TEST:  bu tablolar ofisin mukavemet hesabından makineyle
aktarıldı.  Aktarma sırasında bir sütun kayması ya da satır atlaması olsa
hiçbir hesap testi bunu göremezdi — motor kendi ( yanlış ) tablosuyla tutarlı
çalışırdı.  Kaynak tablolar bir kez okunup JSON olarak donduruldu;  bu test
aktarımın kendisini ve standarda göre yapılan genişletmeleri denetler.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.uygulama import mukavemet_girdi as MG                  # noqa: E402
from engine.uygulama import mukavemet_tablolari as MT              # noqa: E402
from testler.ortak import Rapor                           # noqa: E402

REFERANS = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "referans_tablolar.json")

#  Kaynaktan aktarılan tablolar  ( modüldeki ad )
TABLOLAR = ("RAY_PROFILI", "RAY_GEOMETRI", "HALAT", "NPU_PROFIL", "KABIN_ALANI",
            "DARBE_TIPLERI", "AGIRLIK_MALZEMESI", "RAY_CELIGI", "BUKULGEN_KABLO")


#  KAYNAKTAN GENİŞLETİLEN TABLOLAR.  Kaynağın satırlarına dokunulmaz;
#  yalnız standardın gerektirdiği satırlar EKLENİR.  Burada hem "kaynağın
#  hiçbir satırı değişmedi" hem de "eklenenler beklenenlerdir" denetlenir —
#  yoksa genişletme, sessizce kaynak veriyi değiştirmenin kapısı olurdu.
GENISLETILEN = {
    #  T75/B ( 75 x 62 x 10 ) kaynak listede yoktu.  Orta kapasiteli
    #  asansörlerin en yaygın rayıdır.  Kesit değerleri ISO 7465'ten;
    #  iki bağımsız kaynak doğruluyor ( bkz. mukavemet_tablolari ).
    "RAY_PROFILI":  {"eklenen": ("75 x 62 x 10",), "degisen": {}},
    "RAY_GEOMETRI": {"eklenen": ("75 x 62 x 10",), "degisen": {}},
    #  EN 81-20 Çizelge 6'da olup kaynakta olmayan beyan yükleri.
    "KABIN_ALANI": {
        "eklenen": (100, 1050, 1250, 1350, 1425, 1500, 2500),
        #  320 kg Çizelge 6'da YOKTUR;  standardın ara değer notu 300/375
        #  arası 0,953 m² verir, kaynak 0,97 yazar ( emniyetsiz taraf ).
        "degisen": {320: (4, 0.953, 0.79)},
    },
    #  EN 81-20 m.5.7.4.5:  σperm = Rm / St.  Kaynak oranları tam sayıya
    #  yuvarlıyordu;  Rm 370'te normal işletme 165 ( kesin 164,44 ) emniyetsiz
    #  yöndeydi.  Satırlar değişti.  450 EKLENDİ:  ISO 7465 m.5 aralığında
    #  ( 370 – 520 ) ELEport örneğinin işlenmiş ray çeliği;  ω EN 81-50
    #  m.5.10.3 ara değerinden, σperm aynı bağıntıdan.
    "RAY_CELIGI": {
        "eklenen": (450,),
        "degisen": {rm: (rm / 2.25, rm / 1.8) for rm in (370, 440, 520)},
    },
}


def _kanal_tablosu(r, kaynak):
    """Nequiv(t) OFİS AÇILARINDAN türetilir;  varsayılan açılarda kaynakla birebir.

    Kaynak tablo her kanal şeklinin karşısına tek bir açı ve tek bir
    Nequiv(t) yazar.  Modül TS EN 81-50 Çizelge 2'yi kullanıp değeri γ / β'dan
    hesaplar;  ofisin varsayılan açılarında türetilen değer kaynakla AYNI
    olmalıdır.
    """
    from engine.uygulama import sabitler as US
    O = US.sabitler(None)
    satir = {ad: tuple(v) for ad, v in kaynak.items()}
    r.esit("kaynak kanal tablosu satır sayısı", len(satir), len(MT.KANAL_SEKLI))
    for ad, _tur, _gecis in MT.KANAL_SEKLI:
        aci_x, neq_x = satir.get(ad, (None, None))
        #  Kaynağın "açı" sütunu iki büyüklüğü karıştırır:  V kanalda γ,
        #  altı kesik kanalda β.  Karşılaştırma buna göre yapılır.
        _tur = MT.kanal_turu(ad)
        bizim_aci = (O["kanal_beta"] if _tur == "UK"
                     else (None if _tur == "U" else O["kanal_gama_v"]))
        bizim = MT.kanal_nequiv_t(ad, O["kanal_gama_v"], O["kanal_beta"])
        if _tur == "VK":
            #  ALTI KESİK V'DE BİLEREK AYRILIYORUZ:  kaynak onu Çizelge 2'nin
            #  β satırından okur ( 5,0 ), standart ise V satırındadır
            #  ( γ = 38° → 12 ).
            r.esit(f"kanal '{ad}' kaynakta β satırından okunuyor", neq_x, 5)
            r.esit(f"kanal '{ad}' bizde V satırından  ( standart )", bizim, 12.0)
            continue
        r.kontrol(f"kanal '{ad}' açısı kaynakla aynı  ( varsayılan ofis )",
                  _esit(bizim_aci, aci_x), f"→ modül {bizim_aci!r}, kaynak {aci_x!r}")
        r.kontrol(f"kanal '{ad}' Nequiv(t) kaynakla aynı  ( varsayılan ofis )",
                  _esit(bizim, neq_x), f"→ modül {bizim!r}, kaynak {neq_x!r}")
    #  ÇİZELGE 2'NİN KENDİSİ  —  TS EN 81-50 m.5.12.2.2
    for aci, bek in MT.NEQUIV_V:
        r.esit(f"Çizelge 2  V kanal γ = {aci}°",
               MT.kanal_nequiv_t("V Kanal", aci, 90), bek)
    #  β SATIRI "U-Undercut grooves" SATIRIDIR:  altı kesik YARIM DAİRE.
    #  Altı kesik V, Çizelge 2'nin V satırındadır.
    for aci, bek in MT.NEQUIV_U_ALTI_KESIK:
        r.esit(f"Çizelge 2  altı kesik yarım daire β = {aci}°",
               MT.kanal_nequiv_t("Altı Kesik Yarım Daire Kanal", 38, aci), bek)
    for aci, bek in MT.NEQUIV_V:
        r.esit(f"Çizelge 2  altı kesik V γ = {aci}°  ( V satırı )",
               MT.kanal_nequiv_t("Altı Kesik V Kanal", aci, 90), bek)
    r.esit("altı kesik V'de β Nequiv'i değiştirmez",
           MT.kanal_nequiv_t("Altı Kesik V Kanal", 38, 105), 12.0)
    # ------------------------------------------------------------------
    #  TS EN 81-50 Ek E  —  STANDARDIN KENDİ ÇÖZÜMLÜ ÖRNEKLERİ
    #  Ek E üç sayısal örnek verir;  üçü de burada yeniden üretilir.
    #  E.1'de standart Kp'yi 2,07'ye YUVARLAYIP çarpar ( 2,07 × 2 = 4,14 );
    #  tam değer 2,0736 → 4,1472'dir.  Program yuvarlamaz, bu yüzden
    #  karşılaştırma standardın kendi yuvarlamasına tolerans tanır.
    # ------------------------------------------------------------------
    for _ad, _kanal, _g, _b, _Dt, _Dp, _nps, _npr, _nt, _neq in (
            ("E.1  2:1 · V kanal", "V Kanal", 40, 90, 600, 500, 2, 0, 10.0, 14.14),
            ("E.2  1:1 · altı kesik U", "Altı Kesik Yarım Daire Kanal",
             38, 90, 600, 400, 1, 0, 5.0, 10.06),
            ("E.3  1:1 çift sarım · U", "Yarım Daire Kanal (Çift Sarım)",
             38, 90, 600, 600, 2, 0, 2.0, 4.0)):
        _t = MT.kanal_nequiv_t(_kanal, _g, _b)
        r.esit(f"Ek E {_ad}: Nequiv(t)", _t, _nt)
        _kp = (_Dt / _Dp) ** 4
        _n = _t + _kp * (_nps + 4 * _npr)
        r.kontrol(f"Ek E {_ad}: Nequiv = {_neq}", abs(_n - _neq) <= 0.01,
                  f"→ program {_n:.4f}, standart {_neq}")
        r.esit("Çizelge 2  alt kesilmesiz yarım daire",
           MT.kanal_nequiv_t("Yarım Daire Kanal", 38, 90), 1.0)
    r.esit("çift sarımda iki geçiş",
           MT.kanal_nequiv_t("Yarım Daire Kanal (Çift Sarım)", 38, 90), 2.0)
    #  Ara değer:  çizelgenin kendi notu doğrusal ara değere izin verir
    r.esit("Çizelge 2  ara değer β = 87,5°  ( altı kesik yarım daire )",
           MT.kanal_nequiv_t("Altı Kesik Yarım Daire Kanal", 38, 87.5), 4.4)
    r.esit("Çizelge 2  ara değer γ = 39°",
           MT.kanal_nequiv_t("V Kanal", 39, 90), 11.0)
    r.esit("Çizelge 2  ara değer γ = 43,5°  ( altı kesik V, V satırı )",
           MT.kanal_nequiv_t("Altı Kesik V Kanal", 43.5, 90), 7.25)


def _genisletilen_tablo(r, ad, tablo, kaynak):
    ex = {satir[0]: tuple(satir[1:]) for satir in kaynak}
    mo = {satir[0]: tuple(satir[1:]) for satir in tablo}
    kural = GENISLETILEN[ad]
    r.esit(f"{ad}: kaynağın satırlarının hepsi duruyor",
           sorted(set(ex) - set(mo)), [])
    r.esit(f"{ad}: eklenenler beklenenlerle aynı",
           sorted(set(mo) - set(ex)), sorted(kural["eklenen"]))
    for anahtar, deger in sorted(ex.items()):
        beklenen = kural["degisen"].get(anahtar, deger)
        r.kontrol(f"{ad}[{anahtar}]",
                  all(_esit(a, b) for a, b in zip(mo[anahtar], beklenen)),
                  f"→ modül {mo[anahtar]!r}, beklenen {beklenen!r}")


def _esit(a, b):
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return abs(float(a) - float(b)) < 1e-9
    return (a if a is not None else "") == (b if b is not None else "")


def calistir():
    print("\n\033[1mTEST 8 — MUKAVEMET TABLOLARI + GİRDİ SÖZLEŞMESİ\033[0m")
    r = Rapor("Mukavemet tabloları")
    with open(REFERANS, encoding="utf-8") as f:
        kaynak = json.load(f)

    for ad in TABLOLAR:
        tablo = getattr(MT, ad)
        ref = [tuple(x) for x in kaynak["tablolar"][ad]]
        if ad in GENISLETILEN:
            _genisletilen_tablo(r, ad, tablo, ref)
            continue
        if not r.esit(f"{ad}: satır sayısı", len(tablo), len(ref)):
            continue
        for i, (m, e) in enumerate(zip(tablo, ref)):
            if not r.esit(f"{ad}[{i}]: sütun sayısı", len(m), len(e)):
                continue
            for j, (mv, ev) in enumerate(zip(m, e)):
                r.kontrol(f"{ad}[{i}][{j}]", _esit(mv, ev), f"→ modül {mv!r}, kaynak {ev!r}")

    #  KANAL TABLOSU:  modül Nequiv(t)'yi ofis açılarından ve TS EN 81-50
    #  Çizelge 2'den türetiyor.
    _kanal_tablosu(r, kaynak["kanal"])

    #  ω:  kaynak tablo λ = 20 … 250, Rm = 370 eğrisidir.  Modül standardın
    #  iki eğrisini ( 370 · 520 ) formülle kurar;  370 eğrisi tabloyu üretmeli.
    om = [tuple(x) for x in kaynak["omega"]]
    r.esit("OMEGA: satır sayısı", MT.OMEGA_LAMBDA_MAX - MT.OMEGA_LAMBDA_MIN + 1, len(om))
    r.esit("OMEGA: λ alt sınırı", MT.OMEGA_LAMBDA_MIN, om[0][0])
    r.esit("OMEGA: λ üst sınırı", MT.OMEGA_LAMBDA_MAX, om[-1][0])
    for lam, w in om:
        r.kontrol(f"ω(λ={lam}, Rm 370)", abs(MT.omega_en8150(lam, 370) - w) <= 0.006,
                  f"→ modül {MT.omega_en8150(lam, 370)!r}, kaynak {w!r}")
    r.kontrol("ω tablo dışı λ için None",
              MT.omega_en8150(19) is None and MT.omega_en8150(251) is None)

    #  AĞIRLIK RAY ARASI → GENİŞLİK TABLOSU KALDIRILDI:  TS EN 81-50 Ek C.2.2
    #  karşı ağırlığın KENDİ ölçülerini ( Gx · Gy ) veri olarak ister.
    #  Türetme işlevlerinin GERİ GELMEDİĞİ denetlenir.
    for _kalkti in ("AGIRLIK_RAY_ARASI", "RAY_ARALARI", "agirlik_genisligi",
                    "agirlik_derinlik", "OMEGA", "omega", "KANAL_ISLEME", "surtunme"):
        r.kontrol(f"kaldırılan tablo / türetme geri gelmedi: {_kalkti}",
                  not hasattr(MT, _kalkti))
    r.kontrol("karşı ağırlık ölçüleri GİRDİ",
              all(a in MG.ALAN for a in ("agirlik_genisligi", "agirlik_derinligi")))

    #  Erişim işlevleri gerçekten doğru sütunu okuyor mu
    p = "89 x 62 x 15,88"
    r.esit("ray() Gr", MT.ray(p, "Gr"), 12.38)
    r.esit("ray() Wx", MT.ray(p, "Wx"), 14350)
    r.esit("ray() ix", MT.ray(p, "ix"), 19.48)
    r.esit("npu() A", MT.npu(120, "A"), 17)
    r.esit("npu() Wx", MT.npu(120, "Wx"), 60.7)
    r.esit("npu() ix", MT.npu(120, "ix"), 4.62)
    r.esit("halat_kopma()", MT.halat_kopma(6.5), 24700)
    r.esit("k2 sabiti", MT.K2_NORMAL_KULLANMA, 1.2)
    r.esit("kablo_agirligi()", MT.kablo_agirligi("24 x 0,75"), 0.642)
    r.kontrol("bilinmeyen anahtar None döner",
              MT.ray("yok", "Gr") is None and MT.halat_kopma(99) is None)

    _girdi_sozlesmesi(r, kaynak)
    _gelismis_sozlesmesi(r)
    return r


#  SEÇENEK LİSTELERİ.  Arayüzün sunduğu listeler standardın tablolarıyla
#  aynı olmalı:  beyan yükleri EN 81-20 Çizelge 6'nın 28 yükü, ray listesi
#  T75/B dâhil yedi profil, hızlar 0,63 … 6 m/s.
SECENEKLER = {
    "beyan_hizi": [0.63, 0.8, 1, 1.2, 1.6, 2, 2.5, 3, 4, 5, 6],
    "agirlik_malzemesi": ["Barit", "Pik Döküm"],
    "kabin_ray_profili": ["50 x 50 x 5", "70 x 65 x 9", "75 x 62 x 10",
                          "89 x 62 x 15,88", "90 x 75 x 16", "125 x 82 x 16",
                          "127 x 89 x 16"],
    "agirlik_ray_profili": ["50 x 50 x 5", "70 x 65 x 9", "75 x 62 x 10",
                            "89 x 62 x 15,88", "90 x 75 x 16", "125 x 82 x 16",
                            "127 x 89 x 16"],
    "beyan_yuku": [100, 180, 225, 300, 320, 375, 400, 450, 525, 600, 630, 675,
                   750, 800, 825, 900, 975, 1000, 1050, 1125, 1200, 1250, 1275,
                   1350, 1425, 1500, 1600, 2000, 2500],
}


#  KAYNAK ÖRNEKTEN BİLEREK AYRILAN VARSAYILANLAR  ( anahtar → ( değer , neden ) ).
BILEREK_DEGISEN_VARSAYILAN = {
    "yan_yatak": (140, "makine kirişi — sahada genelde NPU 140 ( kullanıcı kararı )"),
}


def _girdi_sozlesmesi(r, kaynak):
    """engine/uygulama/mukavemet_girdi.py  —  varsayılanlar ve seçenekler."""
    for anahtar, etiket, _b, tur, secenekler, varsayilan in MG.ALANLAR:
        if tur == "hesap":
            r.kontrol(f"girdi {anahtar}: seçenek/varsayılan taşımıyor",
                      secenekler is None and varsayilan is None)
            continue
        r.kontrol(f"girdi {anahtar}: etiket dolu", bool(etiket and etiket.strip()))
        #  Örnek projenin varsayılanları kaynaktaki örnekle aynı:  TEST 9'un
        #  örnek değerleri ve TEST 10'un taraması bu girdilere dayanır.
        if anahtar in kaynak["varsayilanlar"]:
            bek = BILEREK_DEGISEN_VARSAYILAN.get(anahtar, (kaynak["varsayilanlar"][anahtar],))[0]
            r.kontrol(f"girdi {anahtar}: varsayılan örnek projeyle aynı",
                      _esit(varsayilan, bek),
                      f"→ modül {varsayilan!r}, kaynak {bek!r}")
        if secenekler is not None:
            r.kontrol(f"girdi {anahtar}: varsayılan seçenek listesinde",
                      varsayilan is None or varsayilan in secenekler,
                      f"→ {varsayilan!r} ∉ {secenekler!r}")
        if anahtar in SECENEKLER:
            r.esit(f"girdi {anahtar}: seçenekler", sorted(map(str, secenekler)),
                   sorted(map(str, SECENEKLER[anahtar])))

    #  Hesaplanan iki alan kaynaktaki örnekle aynı sonucu veriyor mu
    g = MG.varsayilanlar()
    for anahtar in ("karsi_agirlik", "kuyu_boyu"):
        r.kontrol(f"hesaplanan {anahtar} örnek projeyle aynı",
                  _esit(g[anahtar], kaynak["hesaplanan"][anahtar]),
                  f"→ modül {g[anahtar]!r}, kaynak {kaynak['hesaplanan'][anahtar]!r}")
    r.kontrol("varsayılan girdiler doğrulamadan temiz geçiyor", MG.dogrula(g) == [],
              f"→ {MG.dogrula(g)}")
    #  Örnek projenin tabliyesi 750 mm'dir ( varsayılan artık 1.200 ).
    r.esit("toplam ray boyu (m)  ( örnek proje, tabliye 750 )",
           MG.toplam_ray_boyu(dict(g, tabliye_yuksekligi=750)), 26.6)
    #  MAKİNE DAİRESİZ TESİSTE TABLİYE YOKTUR:  girilen değer ray boyuna girmez.
    r.esit("toplam ray boyu (m)  ( MRL — tabliye yok )",
           MG.toplam_ray_boyu(dict(g, mk_yok=True, tabliye_yuksekligi=750)), 26.6 - 0.75)


#  GÖRÜNÜR KALMASI GEREKEN GİRDİLER.  Her projede değişenler ( bina ve
#  asansörün kendi ölçüleri ) ve yanlış kaldığında sonucu çok değiştiren
#  beyanlar.  Gelişmiş'e taşınırlarsa bir projenin değeri öbür projeden
#  sessizce devralınırdı.
GORUNUR_KALMALI = (
    "beyan_yuku", "beyan_hizi", "seyir_mesafesi", "aski_orani",
    "kabin_genisligi", "kabin_derinligi", "kat_kapisi_tipi", "kapi_genisligi",
    #  Makine daireli projede sorulur ( MRL'de gizli ).
    "tabliye_yuksekligi",
    #  Kaçıklıklar çizime bağlıdır;  gizli bir 0 kaçık yerleşimde unutulur.
    "kabin_kaciklik", "aski_kaciklik_x", "aski_kaciklik_y",
    "son_kat_yuksekligi", "kuyu_dibi", "ray_kapi_arasi",
    "motor_gucu", "makine_agirligi", "makine_tipi", "tahrik_kasnak_capi",
    "saptirma_kasnak_capi", "makine_tst", "makine_raya_biniyor",
    "halat_adedi", "halat_capi", "sarilma_acisi",
    "kabin_ray_profili", "agirlik_ray_profili", "kabin_konsol_arasi",
    "agirlik_konsol_arasi", "guvenlik_tertibati", "agirlik_guvenlik_tertibati",
    "kabin_tampon_baba", "agirlik_tampon_baba",
)
#  BÜTÜN ALANLARI GELİŞMİŞ'TE OLAN GRUPLAR  ( kullanıcı kararı ).  Hız
#  regülatörünün hepsi ürün / imalatçı verisidir;  devreye sokma kuvveti ve
#  devreye girme hızı boşsa paftaya standardın şartı yazılır.
TAMAMI_GELISMIS_GRUPLAR = ("Hız regülatörü",)
#  Hiçbir hesaba / paftaya girmediği ya da tek seçeneği olduğu için kaldırılanlar.
#  reg_surtunme ( µ ) KALKMADI, OFİS SABİTİNE TAŞINDI ( sabitler.reg_mu ):
#  standart hesaba katılacak değeri kendisi verir ve asansör bazında
#  küçültülünce halatın emniyet katsayısı olduğundan iyi çıkıyordu.
KALDIRILAN_ALANLAR = ("kuyu_derinligi", "agirlik_ray_duvar",
                      "dikine_kiris_tipi", "yan_yatak_tipi", "agirlik_ray_arasi",
                      "reg_surtunme")


def _gelismis_sozlesmesi(r):
    """Formun "Gelişmiş" bölümleri  ( MG.GELISMIS_ALANLAR · girdi.EK_GELISMIS )."""
    from engine.uygulama import girdi as UG
    for a in sorted(MG.GELISMIS_ALANLAR):
        r.kontrol(f"gelişmiş {a}: sözleşmede var ve kullanıcıdan alınıyor",
                  a in MG.ALAN and MG.ALAN[a][3] != "hesap")
        #  Gizli bir alan boş ve zorunluysa proje görünmeyen bir kutu yüzünden
        #  durur:  ya varsayılanı olmalı ya da boş bırakılabilmeli.
        if a in MG.ALAN:
            r.kontrol(f"gelişmiş {a}: varsayılanı var ya da boş bırakılabilir",
                      MG.ALAN[a][5] is not None or a in MG.OPSIYONEL_ALANLAR)
    for a in GORUNUR_KALMALI:
        r.kontrol(f"görünür kalır: {a}",
                  a in MG.ALAN and a not in MG.GELISMIS_ALANLAR)
    for a in KALDIRILAN_ALANLAR:
        r.kontrol(f"kaldırıldı: {a}", a not in MG.ALAN)
    for anahtar, _e, _b, tur, secenekler, _v in MG.ALANLAR:
        if secenekler is not None:
            r.kontrol(f"girdi {anahtar}: tek seçenekli kutu sorulmuyor",
                      len(secenekler) > 1, f"→ {secenekler!r}")
    veri = UG.arayuz_alanlari()
    for gr in veri["gruplar"]:
        if gr["ad"] in TAMAMI_GELISMIS_GRUPLAR:
            r.kontrol(f"grup '{gr['ad']}': bütün alanlar gelişmiş",
                      bool(gr["alanlar"]) and all(f["gelismis"] for f in gr["alanlar"]))
            continue
        r.kontrol(f"grup '{gr['ad']}': en az bir görünür alan",
                  any(not f["gelismis"] for f in gr["alanlar"]))
        for f in gr["alanlar"]:
            bek = f["anahtar"] in (MG.GELISMIS_ALANLAR | UG.EK_GELISMIS)
            if f["gelismis"] != bek:
                r.kontrol(f"arayüz {f['anahtar']}: gelişmiş işareti", False,
                          f"→ {f['gelismis']!r}, beklenen {bek!r}")
    _hepsi = [f for gr in veri["gruplar"] for f in gr["alanlar"]]
    r.esit("arayüz: gelişmiş alan sayısı",
           sum(f["gelismis"] for f in _hepsi),
           len(MG.GELISMIS_ALANLAR) + len(UG.EK_GELISMIS))

    #  ── ALAN AÇIKLAMALARI  ( formdaki ⓘ )  ────────────────────────────
    #  SÖZLEŞMENİN PARÇASIDIR.  Açıklamasız bir girdi, kullanıcının ne
    #  yazacağını bilemediği bir kutudur;  yeni alan eklenirken metni
    #  yazmak unutulmasın diye burada zorunlu tutulur.  Özellikle üç
    #  kaçıklık birbirine karıştırılmaya çok açıktır.
    for f in _hepsi:
        r.kontrol(f"açıklama {f['anahtar']}: var ve boş değil",
                  bool(str(f.get("bilgi") or "").strip()))
        _b = str(f.get("bilgi") or "")
        r.kontrol(f"açıklama {f['anahtar']}: kısa  ( ≤ 320 karakter )",
                  len(_b) <= 320, f"→ {len(_b)} karakter")
    #  ÜÇ KAÇIKLIK AYIRT EDİLİR.  Metinleri birbirinin kopyası olmamalı ve
    #  her biri ÖLÇÜM ORİJİNİNİ ( ray ekseni ) söylemeli — asıl karışma
    #  sebebi "neye göre kaçık" sorusunun cevapsız kalmasıydı.
    _kacik = ("kabin_kaciklik", "aski_kaciklik_x", "aski_kaciklik_y",
              "kabin_agirlik_merkezi_x", "kabin_agirlik_merkezi_y")
    _metin = {a: MG.ACIKLAMA[a] for a in _kacik}
    r.kontrol("kaçıklık açıklamaları birbirinden farklı",
              len(set(_metin.values())) == len(_kacik))
    for a, m in _metin.items():
        r.kontrol(f"kaçıklık {a}: ölçüm orijinini söylüyor",
                  "ray ekseni" in m or "ray ekseninden" in m, f"→ {m[:60]}")


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
