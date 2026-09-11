"""Bağımsız EN 81-50 sayısal denetimi, 2026-09-09.

Çalıştırma: .venv/bin/python -m unittest testler.test_tsen_bagimsiz -v
Kaynak: https://liftescalatorlibrary.org/paper_indexing/papers/00000063.pdf
Bu yayın standardın kendisi değildir; 2014 baskısını açıklayan örneklerdir.
Tam TS baskısı doğrulaması yerine geçmez. Üretim kodunu değiştirmez.
Beklenen değerler Excel/altın çıktıdan alınmaz. Kalan testler açık bulgudur.
"""
import math
import unittest

from engine.uygulama import mukavemet as M
from engine.uygulama import mukavemet_tablolari as T
from engine.uygulama import sabitler as U
from testler.ortak import P_std


class BagimsizDenetim(unittest.TestCase):
    def test_yayin_halat_guvenligi(self):
        # Yayın §5: aynı halat/kasnak girdileri; diğer proje alanları varsayılan.
        s = M.hesapla({
            "beyan_yuku": 1000, "kabin_agirligi": 1250,
            "tahrik_kasnak_capi": 320, "saptirma_kasnak_capi": 320,
            "halat_capi": 8, "halat_adedi": 5, "halat_kopma_kN": 43,
            "kasnak_tek_yon": 2, "kanal_sekli": "V Kanal",
            "kanal_isleme": "Sertleştirilmiş", "halat_arasi_yan": 320,
            "_ofis": {"kanal_gama_v": 50, "q_denge": 0.45},
        })
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertAlmostEqual(s["_h"]["V116"], 7)
        # Yayında Sf tam sayıya yuvarlanarak 16 verilmiş.
        self.assertAlmostEqual(s["ozet"]["Sf"], 16, delta=0.5)
        self.assertAlmostEqual(s["ozet"]["S_gercek"], 19, delta=0.1)
        # Yayın §4.2: sürtünme katsayısı ve kritik oran; 1.87 yuvarlatılmıştır.
        self.assertAlmostEqual(s["_h"]["AS190"], 1 / 12)
        self.assertAlmostEqual(s["_h"]["O257"], 1.87, delta=0.02)

    def test_yayin_ray_egilmesi_cekirdegi(self):
        # Yayının T127-1/B kesiti katalogda yok: yalnız sayısal çekirdek testi.
        # Bu kontrol, uygulamanın bu rayı seçebildiği anlamına gelmez.
        fx = 3 * 9.81 * 1000 * 175 / (2 * 2800)
        fy = 3 * 9.81 * 1000 * 200 / 2800
        self.assertAlmostEqual(M._moment(fx, 4000) / 23610, 29, delta=0.5)
        self.assertAlmostEqual(M._moment(fy, 4000) / 30650, 51, delta=0.5)

    def test_yayin_flans_cekirdegi(self):
        p = {"c": 10, "h1_b_f": 89 - 19 - 11, "h1_f": 89 - 11}
        self.assertAlmostEqual(M._flans(7951, p, 140, True), 147, delta=0.5)
        # Yayındaki 96, yazılı girdiler ve formülle tutarsızdır (95.08966).
        # Kaynak baskı hatasını motor hatası saymamak için aritmetik kullanılır.
        self.assertAlmostEqual(M._flans(7951, p, 140, False),
                               6 * 7951 * 59 / (100 * (140 + 156)), places=8)

    def test_yayin_omega_cekirdegi(self):
        # Yayın §3.1. Program narinliği yukarı tam sayıya yuvarlar.
        lam, omega = M._burkulma_omega(4000, 23.61, 370)
        self.assertEqual(lam, 170)
        self.assertAlmostEqual(omega, 4.85, delta=0.04)

    def test_burkulmada_en_kucuk_atalet_yaricapi(self):
        s = M.hesapla()
        g, h = s["girdi"], s["_h"]
        p = g["kabin_ray_profili"]
        imin = min(T.ray(p, "ix"), T.ray(p, "iy"))
        lam = math.ceil(g["kabin_konsol_arasi"] / imin)
        # Bu test yarıçap seçimini ayırır; yukarı yuvarlama aynen korunur.
        omega = 0.00016887 * lam ** 2
        expected = h["AL354"] / h["AD354"] * omega
        self.assertAlmostEqual(h["AL354"], expected, places=6)

    def test_narinlik_250_sinirinin_asimi_burkulmayi_dusurmeli(self):
        # ix=20.9; iy=14.0. Gerçek narinlik 3600/14 = 257.143 > 250.
        # m.5.10.3'ün ω tablosu 20 ≤ λ ≤ 250 arasında tanımlıdır: dışında ω
        # yoktur, dolayısıyla σk hesaplanamaz ve BURKULMA kontrolü düşer.
        # Hesabın tamamı durmaz — eğilme, birleşik gerilme, flanş ve sehim
        # bağıntıları ω'ya bağlı değildir ve geçerliliğini korur.
        g = {"kabin_ray_profili": "70 x 65 x 9", "kabin_konsol_arasi": 3600}
        s = M.hesapla(g)
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertTrue(any("narin" in u for u in s["uyarilar"]), s["uyarilar"])
        b7 = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
        self.assertFalse(b7["sonuc"]["uygun"],
                         "Tablo dışı narinlikte bölüm uygun çıkmamalı")
        # ω gerçekten üretilmemiş olmalı; σk None kalmalı.
        lam, omega = M._burkulma_omega(3600, min(T.ray("70 x 65 x 9", "ix"),
                                                 T.ray("70 x 65 x 9", "iy")), 370)
        self.assertEqual(lam, 258)
        self.assertIsNone(omega)

    def test_kabin_y_kacikligi_guvenlik_yukune_girmeli(self):
        # Girdinin ilan edilen anlamı kabin merkezinin y kaçıklığıdır.
        # Kabin ve merkezlenmiş kapı birlikte +200 mm ötelenmiştir.
        s = M.hesapla({"kabin_kaciklik": 200})
        self.assertTrue(s["aktif"], s.get("hata"))
        g = s["girdi"]
        #  P, m.5.7.2.3.2'nin tanımıyla:  boş kabin + gezici kablo payı +
        #  denge zinciri.  Eklenen kütleler kabin merkezinde kabul edilir,
        #  yani onların da y kolu 200 mm'dir.
        expected = (2 * 9.81 * (g["beyan_yuku"] * (200 + g["kabin_genisligi"] / 8)
                    + P_std(s) * 200) / g["kabin_paten_arasi"])
        self.assertAlmostEqual(s["_h"]["K344"], expected, places=6)

    #  ------------------------------------------------------------------
    #  ACİL FRENLEME  —  EN 81-50 Ek D'nin ÇÖZÜMLÜ ÖRNEĞİ  ( 2:1, dengeleme
    #  yok, makine üstte ).  Ek D, m.5.11.2.2'nin genel formülünün bu
    #  düzenek için sadeleşmiş hâlidir ve ± işaretlerini AÇIK yazar:
    #
    #    a) yüklü kabin en alt durakta   ( kabin AŞAĞI yavaşlıyor )
    #         T1 = (P+Q)/2·(gn+a) + MSRcar·(gn+2a) + mPcar·2·a/2 − FRcar/2
    #         T2 = Mcwt/2·(gn−a)                   − mPcwt·1·a/2 + FRcwt/2
    #    b) boş kabin en üst durakta     ( kabin YUKARI yavaşlıyor )
    #         T1 = Mcwt/2·(gn+a) + MSRcwt·(gn+2a)  + mPcwt·1·a/2 − FRcwt/2
    #         T2 = (P+MTrav)/2·(gn−a)              − mPcar·2·a/2 + FRcar/2
    #
    #  KASNAK SAYILARI EK D'NİN KENDİSİNDEDİR:  kabin tarafında "·2·",
    #  ağırlık tarafında "·1·" yazar.  Ofis sabitleri bu iki sayıyı
    #  varsayılan olarak taşır ( kasnak_adet_kabin · kasnak_adet_agirlik ).
    #
    #  NOT 1 gereği b'de etiketler yer değiştirir;  oran max/min alındığı
    #  için bu karşılaştırmayı etkilemez.  Kasnak ataletleri ( mPcar, mPcwt )
    #  motorda modellenmediği için sıfırdır.
    #  ------------------------------------------------------------------
    def _ekD(self, durum):
        s = M.hesapla()
        g = s["girdi"]
        o = {"ofis": U.sabitler(g.get("_ofis"))}
        M._motor(g, o)
        t = M._terimler(g, o, durum)
        self.assertEqual(t["r"], 2, "Ek D örneği 2:1 askı içindir")
        for sifir in ("MComp", "iPDT", "mPTD", "mDP", "MCRcar", "MCRcwt"):
            self.assertEqual(t[sifir], 0.0, f"{sifir} Ek D örneğinde yoktur")
        gn, a = t["gn"], t["a"]
        #  Sürtünme kuvveti motorun kendi kuralıdır ( o taraftaki
        #  sürtünmesiz kuvvetin yüzdesi );  burada denetlenen İŞARETİN YERİ.
        fr_car = M.SABIT["FRcar_katsayi"]
        fr_cwt = M.SABIT["FRcwt_katsayi"]
        #  Ek D'nin kasnak atalet terimleri  ( r = 2 olduğu için "/2" )
        kas_car = t["mPcar"] * t["iPcar"] * a / 2
        kas_cwt = t["mPcwt"] * t["iPcwt"] * a / 2
        if durum == "fren_alt":
            ham1 = (t["P"] + t["Q"]) / 2 * (gn + a) + t["MSRcar"] * (gn + 2 * a)
            ham2 = t["Mcwt"] / 2 * (gn - a)
            #  Sürtünme, o taraftaki SÜRTÜNMESİZ kuvvetin yüzdesidir —
            #  kasnak atalet terimi de o kuvvetin içindedir.
            T1 = (ham1 + kas_car) * (1 - fr_car / 2)
            T2 = (ham2 - kas_cwt) * (1 + fr_cwt / 2)
        else:
            ham1 = t["Mcwt"] / 2 * (gn + a) + t["MSRcwt"] * (gn + 2 * a)
            ham2 = (t["P"] + t["MTrav"]) / 2 * (gn - a) + t["MSRcar"] * (gn - 2 * a)
            T1 = (ham1 + kas_cwt) * (1 - fr_cwt / 2)
            T2 = (ham2 - kas_car) * (1 + fr_car / 2)
        hucre = "K257" if durum == "fren_alt" else "K271"
        return s["_h"][hucre], max(T1, T2) / min(T1, T2)

    def test_fren_alt_ek_D_ile_ayni(self):
        motor, ek_d = self._ekD("fren_alt")
        self.assertAlmostEqual(motor, ek_d, places=6)

    def test_fren_ust_ek_D_ile_ayni(self):
        motor, ek_d = self._ekD("fren_ust")
        self.assertAlmostEqual(motor, ek_d, places=6)

    def test_frenlemede_kabin_tarafi_agirlasir(self):
        """Yüklü kabin aşağı yavaşlarken kabin tarafı halat DAHA ÇOK gerilir."""
        s = M.hesapla()
        g = s["girdi"]
        o = {"ofis": U.sabitler(g.get("_ofis"))}
        M._motor(g, o)
        t = M._terimler(g, o, "fren_alt")
        durgun = M._T1(dict(t, a=0.0), 0.0, +1)
        frenli = M._T1(t, 0.0, +1)
        self.assertGreater(frenli, durgun,
                           "Aşağı yavaşlayan yüklü kabinde T1 artmalıdır")
        durgun2 = M._T2(dict(t, a=0.0), 0.0, +1)
        frenli2 = M._T2(t, 0.0, +1)
        self.assertLess(frenli2, durgun2,
                        "Yukarı yavaşlayan karşı ağırlıkta T2 azalmalıdır")

    #  ------------------------------------------------------------------
    #  TAMPONLAR            TS EN 81-20 m.5.8.1 / m.5.8.2
    #  ------------------------------------------------------------------
    def _tampon(self, tip, v, strok=None):
        g = {"tampon_tipi": tip, "beyan_hizi": v}
        if strok is not None:
            g["kabin_tampon_ezilme"] = strok
            g["agirlik_tampon_ezilme"] = strok
        s = M.hesapla(g)
        self.assertTrue(s["aktif"], s.get("hata"))
        return next(b for b in s["bolumler"] if b["kimlik"] == "tamponlar")

    def test_biriktirmeli_tampon_1_m_s_ustunde_kullanilamaz(self):
        """m.5.8.1.5:  enerji biriktirmeli tampon yalnız v ≤ 1 m/s."""
        for tip in (T.TAMPON_TIPLERI[0][0], T.TAMPON_TIPLERI[1][0]):
            self.assertTrue(self._tampon(tip, 1.0, 900)["sonuc"]["uygun"], tip)
            self.assertFalse(self._tampon(tip, 1.2, 900)["sonuc"]["uygun"], tip)
        #  m.5.8.1.6:  enerji yutmalıda hız sınırı yoktur.
        yut = T.TAMPON_TIPLERI[2][0]
        self.assertTrue(self._tampon(yut, 2.5, 900)["sonuc"]["uygun"])

    def test_lineer_tampon_stroku(self):
        """m.5.8.2.1.1.1:  strok ≥ 0,135·v² , en az 65 mm."""
        lin = T.TAMPON_TIPLERI[0][0]
        #  v = 1 m/s  →  135 mm.  134 düşer, 135 geçer.
        self.assertFalse(self._tampon(lin, 1.0, 134)["sonuc"]["uygun"])
        self.assertTrue(self._tampon(lin, 1.0, 135)["sonuc"]["uygun"])
        #  Düşük hızda 65 mm ALT SINIRI devreye girer:  0,135·0,63² = 53,6 mm
        #  ama madde 65 mm'nin altına inilemeyeceğini söyler.
        self.assertFalse(self._tampon(lin, 0.63, 64)["sonuc"]["uygun"])
        self.assertTrue(self._tampon(lin, 0.63, 65)["sonuc"]["uygun"])

    def test_enerji_yutmali_tampon_stroku(self):
        """m.5.8.2.2.1:  strok ≥ 0,0674·v².  Alt sınır YOKTUR."""
        yut = T.TAMPON_TIPLERI[2][0]
        #  v = 2,5 m/s  →  0,0674 · 6,25 = 0,42125 m = 421,25 mm
        self.assertFalse(self._tampon(yut, 2.5, 421)["sonuc"]["uygun"])
        self.assertTrue(self._tampon(yut, 2.5, 422)["sonuc"]["uygun"])
        #  65 mm alt sınırı burada uygulanmaz:  0,0674·0,63² = 26,8 mm
        self.assertTrue(self._tampon(yut, 0.63, 27)["sonuc"]["uygun"])

    def test_lineer_olmayan_tamponda_strok_bagintisi_yok(self):
        """m.5.8.2.1.2:  yavaşlama ölçütleri tip deneyine bırakılmıştır."""
        pol = T.TAMPON_TIPLERI[1][0]
        b = self._tampon(pol, 1.0, 1)          # 1 mm bile olsa bağıntı yok
        self.assertTrue(b["sonuc"]["uygun"])
        self.assertIn("tip inceleme", b["sonuc"]["metin"].lower())

    def test_kuyu_tabani_kuvveti_tampon_adedine_bolunur(self):
        """m.5.2.1.8.5:  kuvvet tampon sayısına eşit dağılır."""
        s = M.hesapla({"kabin_tampon_adedi": 2, "agirlik_tampon_adedi": 4})
        h = s["_h"]
        g, gn = s["girdi"], 9.81
        #  m.5.2.1.8.5:  F = 4·gn·( P + Q ) — oradaki P boş kabin DEĞİL,
        #  "empty car and components supported by the car, i.e. part of the
        #  travelling cable, compensating ropes/chains (if any)".
        Fkt = 4 * gn * (P_std(s) + g["beyan_yuku"])
        self.assertAlmostEqual(h["AF621"], Fkt, places=6)
        b9 = next(b for b in s["bolumler"] if b["kimlik"] == "kuyu_tabani")
        tekil = [a["deger"] for a in b9["adimlar"]
                 if "Fkt1" in str(a.get("formul") or "")]
        self.assertEqual(len(tekil), 1)
        self.assertAlmostEqual(tekil[0], Fkt / 2, places=6)

    #  ------------------------------------------------------------------
    #  KASNAK ATALETİ       TS EN 81-50 m.5.11.2.2 a)  ( koşul III )
    #  ------------------------------------------------------------------
    def test_kasnak_atalet_eleport_ornegiyle_ayni(self):
        """ELEport'un yayımlanmış paftası:  Dp=294 · 7 × 6,5 mm → J = 0,29."""
        mP, J, A = M._kasnak_atalet(
            {"saptirma_kasnak_capi": 294, "halat_adedi": 7, "halat_capi": 6.5},
            U.sabitler(None))
        self.assertAlmostEqual(J, 0.29, delta=0.005)
        self.assertAlmostEqual(A * 1000, 92.4, delta=0.5)   # paftada 0,09 m
        self.assertAlmostEqual(mP, J / 0.147 ** 2, delta=0.05)

    def test_kasnak_atalet_terimi_orani_buyutur(self):
        """Terim T1'i büyütüp T2'yi küçültür → T1/T2 oranı ARTAR."""
        s = M.hesapla()
        g = s["girdi"]
        o = {"ofis": U.sabitler(g.get("_ofis"))}
        M._motor(g, o)
        t = M._terimler(g, o, "fren_alt")
        self.assertGreater(t["mPcar"], 0, "2:1 askıda terim sıfır olmamalı")
        self.assertEqual(t["iPcar"], 2)
        self.assertEqual(t["iPcwt"], 1)
        terimli = M._T1(t, 0.0, +1)
        terimsiz = M._T1(dict(t, mPcar=0.0), 0.0, +1)
        self.assertGreater(terimli, terimsiz)
        #  Büyüklüğü:  mP · iP · a / r
        self.assertAlmostEqual(terimli - terimsiz,
                               t["mPcar"] * t["iPcar"] * t["a"] / t["r"],
                               places=6)

    def test_kasnak_atalet_1_1_askida_sifir(self):
        """m.5.11.2.2 koşul III:  terim yalnız askı oranı > 1 içindir."""
        s = M.hesapla({"aski_orani": 1})
        g = s["girdi"]
        o = {"ofis": U.sabitler(g.get("_ofis"))}
        M._motor(g, o)
        t = M._terimler(g, o, "fren_alt")
        self.assertEqual(t["r"], 1)
        self.assertEqual(t["mPcar"], 0.0)
        self.assertEqual(t["iPcar"], 0)

    def test_kasnak_atalet_ofis_sabitine_baglidir(self):
        """Yoğunluk ofis kabulüdür;  değişince terim de değişmeli."""
        _, J1, _ = M._kasnak_atalet(
            {"saptirma_kasnak_capi": 240, "halat_adedi": 7, "halat_capi": 6.5},
            U.sabitler(None))
        _, J2, _ = M._kasnak_atalet(
            {"saptirma_kasnak_capi": 240, "halat_adedi": 7, "halat_capi": 6.5},
            U.sabitler({"kasnak_yogunluk": 3700}))
        self.assertAlmostEqual(J2, J1 / 2, places=6)

    def test_negatif_halat_kuvveti_uygun_sayilmamali(self):
        """Halat gevşerse tahrik bağıntısı geçersizdir.

        T1/T2 oranı max(a/b, b/a) olduğu için kuvvetlerden biri negatife
        düşünce oran da NEGATİF çıkar ve "oran ≤ e^(f·α)" karşılaştırması
        sessizce geçer.  Sürtünme bağıntısı GERGİN halat varsayar;  T ≤ 0
        fiziksel olarak halatın gevşemesi demektir ve o noktada hiçbir
        tahrik hükmü verilemez.
        """
        s = M.hesapla({"acil_frenleme_a": 9.81})       # a = 1 gn
        self.assertTrue(s["aktif"], s.get("hata"))
        h = s["_h"]
        self.assertLess(h["AJ255"], 0, "bu girdide T2 negatife düşmeli")
        self.assertLess(h["K257"], 0, "oran da negatif çıkmalı")
        b6 = next(x for x in s["bolumler"] if x["kimlik"] == "tahrik_yetenegi")
        self.assertFalse(b6["sonuc"]["uygun"],
                         "negatif halat kuvvetiyle bölüm uygun sayılamaz")
        #  Sebep paftada YAZILI olmalı — sessiz düşme olmaz.
        self.assertTrue(
            any("GEVŞ" in str(a.get("aciklama") or "") for a in b6["adimlar"]),
            "gevşek halat sebebi adımlarda görünmüyor")




class UcDuzeltmeDenetimi(unittest.TestCase):
    """2026-09-10'da bulunan üç hatanın standart tarafından doğrulanması.

    Beklenen değerler kaynak Excel'den ya da altın çıktıdan ALINMAZ;  her
    test standardın kendi cümlesinden ya da fizikten türetilir.
    """

    #  ── 1)  MOTOR GÜCÜ İKİ HAREKET YÖNÜNDEN ────────────────────────
    def _motor_gucu(self, q):
        s = M.hesapla({"_ofis": {"q_denge": q}})
        self.assertTrue(s["aktif"], s.get("hata"))
        return s["ozet"]["N_hesap"]

    def test_motor_gucu_q_ekseninde_simetriktir(self):
        """q ve ( 1−q ) aynayı verir:  dengesizliğin BÜYÜKLÜĞÜ aynıdır.

        Dolu kabin yukarı  → ( 1−q )·Q ,  boş kabin aşağı → q·Q.
        q = 0,40'ta birincisi 0,60·Q, q = 0,60'ta ikincisi 0,60·Q'dur;
        motorun görmesi gereken güç ikisinde de aynı olmalıdır.
        """
        for q in (0.30, 0.35, 0.40, 0.45):
            self.assertAlmostEqual(self._motor_gucu(q), self._motor_gucu(1 - q),
                                   places=9, msg=f"q = {q}")

    def test_motor_gucu_en_kucuk_q_yarimda(self):
        """Denge q = 0,50'de tamdır;  iki yana da sapınca güç ARTMALIDIR."""
        yarim = self._motor_gucu(0.50)
        for q in (0.30, 0.40, 0.45, 0.55, 0.60, 0.70):
            self.assertGreater(self._motor_gucu(q), yarim, f"q = {q}")

    def test_bos_kabin_yonu_q_buyukken_belirleyicidir(self):
        """q > 0,50'de dengesizlik q·Q'dur;  Gmax bunu içermelidir."""
        Q = 800.0
        for q in (0.60, 0.70):
            s = M.hesapla({"beyan_yuku": Q, "_ofis": {"q_denge": q}})
            self.assertTrue(s["aktif"], s.get("hata"))
            #  Gmax = Gden + Gs + MSR − MCR + MTrav;  Gden = q·Q olmalı
            Gmax = s["_h"]["AQ9"]
            self.assertGreaterEqual(Gmax, q * Q, f"q = {q}")
            self.assertLess(Gmax, q * Q + 200, f"q = {q}  ( artık terimler )")

    #  ── 2)  KABİN AÇIKLIKLARI EN ÜST KONUMDA  ( Çizelge 2 ) ────────
    def _ust_acikliklar(self, **ek):
        s = M.hesapla(dict(ek))
        self.assertTrue(s["aktif"], s.get("hata"))
        h = s["_h"]
        return [h["AI635"], h["AI636"], h["AI637"], h["AI638"]]

    def test_agirlik_tampon_acikligi_ust_bosluktan_dusulur(self):
        """Çizelge 2:  kabinin en üst konumu = ağırlık TAM EZİLMİŞ tampon üzerinde.

        Karşı ağırlığın tampona inişi artarsa kabin o kadar daha yükselir;
        kabin üstü açıklıkları AYNI kadar AZALMALIDIR.
        """
        taban = self._ust_acikliklar()
        artan = self._ust_acikliklar(agirlik_carpma_arasi=150 + 60)
        for a, b in zip(taban, artan):
            self.assertAlmostEqual(b, a - 60, places=6)

    def test_tampon_ezilmesi_ust_bosluktan_dusulur(self):
        taban = self._ust_acikliklar()
        artan = self._ust_acikliklar(agirlik_tampon_ezilme=90 + 40)
        for a, b in zip(taban, artan):
            self.assertAlmostEqual(b, a - 40, places=6)

    def test_hiz_payi_ust_bosluktan_dusulur(self):
        """Çizelge 2 dipnot a:  0,035·v²  ( 1,15·v'de durma yolunun yarısı )."""
        v1, v2 = 1.0, 1.6
        taban = self._ust_acikliklar(beyan_hizi=v1)
        hizli = self._ust_acikliklar(beyan_hizi=v2)
        fark = 0.035 * (v2 ** 2 - v1 ** 2) * 1000
        for a, b in zip(taban, hizli):
            self.assertAlmostEqual(b, a - fark, places=6)

    def test_kuyu_dibi_acikliklari_yukselmeden_etkilenmez(self):
        """Kuyu dibi ölçüleri KABİN tampon üzerindeyken alınır — ağırlık tamponu girmez."""
        s1 = M.hesapla()
        s2 = M.hesapla({"agirlik_carpma_arasi": 260, "agirlik_tampon_ezilme": 140})
        for hucre in ("AI645", "AI646", "AI647", "AI648"):
            self.assertAlmostEqual(s1["_h"][hucre], s2["_h"][hucre], places=9,
                                   msg=hucre)

    def test_paten_tavan_siniri_standardin_yazdigi_gibi(self):
        """m.5.2.5.7.2 b):  0,10 m.  Hız payı sınıra değil ÖLÇÜYE girer."""
        for v in (0.63, 1.0, 1.6, 2.5):
            s = M.hesapla({"beyan_hizi": v})
            self.assertTrue(s["aktif"], s.get("hata"))
            self.assertEqual(s["_h"]["AD638"], 100, f"v = {v}")

    #  ── 3)  BURKULMA ZAYIF EKSENDE ─────────────────────────────────
    def test_kaide_burkulmasi_en_kucuk_atalet_yaricapindan(self):
        """Çubuk en küçük atalet yarıçapına sahip eksende burkulur."""
        for olcu in T.NPU_OLCULERI:
            ix, iy = T.npu(olcu, "ix"), T.npu(olcu, "iy")
            if ix is None or iy is None:
                continue
            s = M.hesapla({"dikine_kiris": olcu})
            self.assertTrue(s["aktif"], f"{olcu}: {s.get('hata')}")
            self.assertAlmostEqual(s["_h"]["AB38"], min(ix, iy) * 10, places=9,
                                   msg=f"NPU {olcu}")

    def test_zayif_eksende_narinlik_buyur(self):
        """iy < ix olan profilde λ, güçlü eksenden bulunandan BÜYÜK olmalı."""
        s = M.hesapla({"dikine_kiris": 120})
        L1 = s["girdi"]["sase_yuksekligi"]
        self.assertGreater(s["_h"]["O71"], L1 / (T.npu(120, "ix") * 10))
        self.assertAlmostEqual(s["_h"]["O71"], L1 / (T.npu(120, "iy") * 10),
                               places=9)

    def test_mesnet_beyani_gucli_eksene_dondurur(self):
        """Şase zayıf ekseni bağlıyorsa burkulma o eksende olamaz — ix geçerli."""
        s = M.hesapla({"dikine_kiris": 120,
                       "_ofis": {"kaide_zayif_eksen_mesnetli": 1}})
        self.assertTrue(s["aktif"], s.get("hata"))
        self.assertAlmostEqual(s["_h"]["AB38"], T.npu(120, "ix") * 10, places=9)

    def test_zayif_eksen_kucuk_profilde_karari_cevirir(self):
        """NPU 40x20 ve 50x25:  güçlü eksende 'uygun', zayıf eksende değil."""
        for olcu in ("40x20", "50x25"):
            zayif = M.hesapla({"dikine_kiris": olcu})
            gucli = M.hesapla({"dikine_kiris": olcu,
                               "_ofis": {"kaide_zayif_eksen_mesnetli": 1}})
            b_z = next(x for x in zayif["bolumler"]
                       if x.get("kimlik") == "makine_konstruksiyonu")
            b_g = next(x for x in gucli["bolumler"]
                       if x.get("kimlik") == "makine_konstruksiyonu")
            self.assertTrue(b_g["sonuc"]["uygun"], f"NPU {olcu} güçlü eksen")
            self.assertFalse(b_z["sonuc"]["uygun"], f"NPU {olcu} zayıf eksen")




class PveMRLDenetimi(unittest.TestCase):
    """2026-09-10 · ikinci tur:  P'nin tanımı, regülatör kataloğu, MRL.

    Beklenen değerler kaynak Excel'den ya da altın çıktıdan ALINMAZ;  her
    test standardın kendi cümlesinden türetilir.
    """

    #  ── P'NİN TANIMI  ( m.5.2.1.8.5 · m.5.2.1.8.6 · m.5.7.2.3.2 ) ──────
    def test_kuyu_tabani_P_gezici_kablo_ve_zinciri_icerir(self):
        for zincir in ("Yok", "Var"):
            s = M.hesapla({"denge_zinciri": zincir})
            self.assertTrue(s["aktif"], s.get("hata"))
            Q = s["girdi"]["beyan_yuku"]
            self.assertAlmostEqual(s["_h"]["AF621"],
                                   4 * 9.81 * (P_std(s) + Q), places=6,
                                   msg=f"zincir {zincir}")

    def test_agirlik_tamponu_da_ayni_P_ile(self):
        """m.5.2.1.8.6:  F = 4·gn·( P + q·Q ) — sembol listesi aynı P'yi tanımlar."""
        q = U.VARSAYILAN["q_denge"]
        s = M.hesapla()
        Q = s["girdi"]["beyan_yuku"]
        self.assertAlmostEqual(s["_h"]["AI627"], 4 * 9.81 * (P_std(s) + q * Q),
                               places=6)

    def test_denge_zinciri_ray_kuvvetini_buyutur(self):
        """Zincir P'ye girdiğine göre ray ve kuyu tabanı kuvveti ARTMALI."""
        yok = M.hesapla({"denge_zinciri": "Yok"})
        var = M.hesapla({"denge_zinciri": "Var"})
        self.assertGreater(P_std(var), P_std(yok))
        for hucre in ("AU351", "AF621", "AX611"):
            self.assertGreater(var["_h"][hucre], yok["_h"][hucre], msg=hucre)

    def test_motor_bolumu_P_std_KULLANMAZ(self):
        """Bölüm 1'in F1'i kabin tarafındaki GERÇEK yüktür — zincir oraya
        Gmax ile ayrı girer, P'ye ikinci kez eklenmez."""
        s = M.hesapla({"denge_zinciri": "Var"})
        g = s["girdi"]
        b1 = next(x for x in s["bolumler"] if x["kimlik"] == "motor_gucu")
        P = next(a["deger"] for a in b1["adimlar"] if a.get("sembol") == "P")
        self.assertAlmostEqual(P, g["kabin_agirligi"], places=9)
        self.assertGreater(P_std(s), P)   # ray tarafı gerçekten farklı

    #  ── REGÜLATÖR HALATI KATALOG VERİSİ ────────────────────────────────
    def test_regulator_katalog_kopma_yuku_tabloyu_ezer(self):
        tablo = M.hesapla({"reg_halat_capi": 6})
        katalog = M.hesapla({"reg_halat_capi": 6, "reg_halat_kopma_kN": 28})
        self.assertAlmostEqual(tablo["_h"]["AI136"], T.halat_kopma(6), places=6)
        self.assertAlmostEqual(katalog["_h"]["AI136"], 28_000.0, places=6)
        self.assertGreater(katalog["_h"]["AI136"], tablo["_h"]["AI136"])

    def test_regulator_katalog_birim_kutlesi_tabloyu_ezer(self):
        tablo = M.hesapla({"reg_halat_capi": 6})
        katalog = M.hesapla({"reg_halat_capi": 6, "reg_halat_birim_kutle": 0.30})
        self.assertGreater(katalog["_h"]["AI134"], tablo["_h"]["AI134"])

    #  ── MAKİNE YÜKÜNÜN YOLU  ( m.5.7.2.3.7 · m.5.2.1.8.4 ) ─────────────
    def test_makine_raya_binince_Maux_turetilir(self):
        """m.5.7.2.3.7:  Maux "per guide rail" — toplam ray sayısına bölünür.

        Seçim YALNIZ makine dairesiz tesiste uygulanır;  makine dairesi varsa
        makine kendi kaidesindedir ve yük iki kez sayılmamalıdır.
        """
        s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertTrue(s["aktif"], s.get("hata"))
        g = s["girdi"]
        Gm, Tst, n = g["makine_agirligi"], s["ozet"]["Tst_hesap"], g["kabin_ray_sayisi"]
        self.assertAlmostEqual(s["_h"]["AH292"], (Gm + Tst) * 9.81 / n, places=6)

    def test_Maux_ray_sayisina_bolunur(self):
        """Ray sayısı iki katına çıkınca bir raya düşen yük YARIYA iner."""
        iki = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY, "kabin_ray_sayisi": 2})
        dort = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY, "kabin_ray_sayisi": 4})
        self.assertAlmostEqual(dort["_h"]["AH292"] * 2, iki["_h"]["AH292"], places=6)

    def test_imalatci_degeri_ray_basina_okunur(self):
        """Elle girilen sayı ZATEN bir raya düşen yüktür — bölünmez."""
        for n in (2, 4):
            s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY,
                           "raya_binen_yuk": 800, "kabin_ray_sayisi": n})
            self.assertAlmostEqual(s["_h"]["AH292"], 800 * 9.81, places=6,
                                   msg=f"n = {n}")

    def test_makine_raya_binmezse_ofis_kabulu_kalir(self):
        s = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU[0]})
        self.assertAlmostEqual(s["_h"]["AH292"], M.SABIT["MY_kabin"], places=9)

    def test_imalatci_degeri_turetmeyi_ezer(self):
        turetilen = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        elle = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY, "raya_binen_yuk": 1000})
        self.assertAlmostEqual(elle["_h"]["AH292"], 1000 * 9.81, places=6)
        self.assertNotAlmostEqual(elle["_h"]["AH292"], turetilen["_h"]["AH292"])

    def test_makine_raya_binince_kuyu_tabani_da_buyur(self):
        """m.5.2.1.8.4 kalemi adıyla anar:  'load on traction sheave due to
        rebound when machine on rails'."""
        yok = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU[0]})
        var = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertGreater(var["_h"]["AX611"], yok["_h"]["AX611"])
        self.assertGreater(var["_h"]["AL354"], yok["_h"]["AL354"])

    def test_MRL_de_kaide_bolumu_uygunluk_beyan_etmez(self):
        for mrl, beklenen in ((False, True), (True, None)):
            s = M.hesapla({"mk_yok": mrl})
            b = next(x for x in s["bolumler"]
                     if x["kimlik"] == "makine_konstruksiyonu")
            self.assertIs(b["sonuc"]["uygun"], beklenen, msg=f"mk_yok={mrl}")

    def test_makine_dairesi_varken_secim_yok_sayilir(self):
        """Makine dairesi varsa makine kendi kaidesindedir ( bölüm 2 );  aynı
        yükü bir de raya bindirmek onu İKİ KEZ saymaktır."""
        md = M.hesapla({"mk_yok": False, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertAlmostEqual(md["_h"]["AH292"], M.SABIT["MY_kabin"], places=9)
        mrl = M.hesapla({"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        self.assertGreater(mrl["_h"]["AH292"], md["_h"]["AH292"])

    def test_yok_sayilan_secim_sessiz_kalmaz(self):
        from engine.uygulama import mukavemet_girdi as MG
        u = MG.uyarilar(MG.tamamla({"mk_yok": False, "mk_uzunluk": 4000,
                                    "mk_genislik": 3000,
                                    "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY}))
        self.assertTrue(any("YOK SAYILDI" in x for x in u), f"→ {u}")

    def test_bina_yapisina_giden_yuk_bildirilir(self):
        """m.5.2.1.8.1 · Ek E:  yapı makinenin yükünü taşıyacak;  hesabı
        inşaat projesindedir ama SAYIYI pafta vermelidir."""
        from engine.uygulama import mukavemet_girdi as MG
        bina = MG.uyarilar(MG.tamamla({"mk_yok": True}))
        ray = MG.uyarilar(MG.tamamla({"mk_yok": True,
                                      "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY}))
        self.assertTrue(any("BİNA YAPISINA" in u for u in bina), f"→ {bina}")
        self.assertFalse(any("BİNA YAPISINA" in u for u in ray))
        #  Sayı da verilmeli — inşaat mühendisine gidecek değer
        s = M.hesapla({"mk_yok": True})
        Gm, Tst = s["girdi"]["makine_agirligi"], s["ozet"]["Tst_hesap"]
        b = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
        satir = next(a for a in b["adimlar"]
                     if a.get("aciklama") == "Bina yapısına aktarılan makine yükü")
        self.assertAlmostEqual(satir["deger"], (Gm + Tst) * 9.81, places=6)

    def test_raya_binerken_bina_satiri_yazilmaz(self):
        s = M.hesapla({"mk_yok": True,
                       "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        b = next(x for x in s["bolumler"] if x["kimlik"] == "kabin_raylari")
        self.assertFalse(any(a.get("aciklama") == "Bina yapısına aktarılan makine yükü"
                             for a in b["adimlar"]))

    def test_eski_onay_bicimi_okunmaya_devam_eder(self):
        """Eski .uygulama dosyaları ve Excel kitapları True / 'EVET' taşır."""
        from engine.uygulama import mukavemet_girdi as MG
        for eski, beklenen in ((True, True), ("EVET", True),
                               (False, False), ("HAYIR", False)):
            g = MG.tamamla({"mk_yok": True, "makine_raya_biniyor": eski})
            self.assertEqual(T.makine_raya_mi(g["makine_raya_biniyor"]), beklenen,
                             msg=f"{eski!r}")
            self.assertIn(g["makine_raya_biniyor"], T.MAKINE_YUK_YOLU)


class KuyuTabaniK3Denetimi(unittest.TestCase):
    """m.5.2.1.8.4 · m.5.7.4.3  —  raya bağlı donanım kuyu tabanına k3 ile iner.

    Madde kalemleri sayarken  "any load due to components fixed or linked to
    the guide(s) AND/OR any additional reaction (N) occurring during emergency
    stopping ( e.g. load on traction sheave due to REBOUND when machine on
    rails )"  der.  Geri tepmenin katsayısı m.5.7.4.3'ün k3'üdür.
    """

    #  Ray tarafı ( bölüm 7 · 8 ) ile taban tarafı ( bölüm 9 ) hücreleri
    KABIN = ("AX611", "AH292")      # FKR  ·  MY_kabin
    AGIRLIK = ("AN616", "AH555")    # FAR  ·  MY_agirlik

    def _bilesenler(self, s, kimlik):
        b = next(x for x in s["bolumler"] if x["kimlik"] == kimlik)
        ilk = {}
        for a in b["adimlar"]:
            if isinstance(a, dict):
                ilk.setdefault(str(a.get("sembol") or a.get("formul") or ""), a)
        return ilk

    def test_FKR_k3_ile_kurulur(self):
        """FKR, MY'yi çarpansız değil k3 ile toplamalı."""
        for ek in ({"mk_yok": False},
                   {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU[0]},
                   {"mk_yok": True, "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY}):
            with self.subTest(**ek):
                s = M.hesapla(dict(ek))
                a = self._bilesenler(s, "kuyu_tabani")
                k3, MY, Fgt = a["k3"]["deger"], a["MY"]["deger"], a["Fgt"]["deger"]
                LR, Gr = a["LR"]["deger"], T.ray(s["girdi"]["kabin_ray_profili"], "Gr")
                bek = M.SABIT["gn"] * Gr * LR / 1000.0 + k3 * MY + Fgt
                self.assertAlmostEqual(s["_h"]["AX611"], bek, places=6)
                #  çarpansız hâl artık YANLIŞ olmalı  ( k3 > 1 olduğu sürece )
                self.assertNotAlmostEqual(s["_h"]["AX611"], bek - (k3 - 1) * MY,
                                          places=3)

    def test_bolum_7_ile_bolum_9_ayni_k3_ve_MY(self):
        """Aynı donanım rayın gövdesinde ve tabanında aynı sayıyı görmeli."""
        s = M.hesapla({"mk_yok": True,
                       "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        ray = self._bilesenler(s, "kabin_raylari")
        taban = self._bilesenler(s, "kuyu_tabani")
        self.assertAlmostEqual(ray["MY"]["deger"], taban["MY"]["deger"], places=9)
        self.assertAlmostEqual(ray["k3"]["deger"], taban["k3"]["deger"], places=12)

    def test_k3_ofis_sabitini_izler(self):
        """k3 ofis sabitidir;  değişince hem ray hem taban takip etmeli."""
        bir = M.hesapla({"mk_yok": True,
                         "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY,
                         "_ofis": {"k3_yardimci": 1.2}})
        iki = M.hesapla({"mk_yok": True,
                         "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY,
                         "_ofis": {"k3_yardimci": 2.0}})
        MY = bir["_h"]["AH292"]
        self.assertAlmostEqual(iki["_h"]["AX611"] - bir["_h"]["AX611"],
                               (2.0 - 1.2) * MY, places=6)
        self.assertGreater(iki["_h"]["AL354"], bir["_h"]["AL354"])

    def test_FAR_da_k3_tasir(self):
        """Karşı ağırlık rayının tabanı da aynı maddeye tabidir."""
        s = M.hesapla({})
        a = self._bilesenler(s, "kuyu_tabani")
        k3 = a["k3"]["deger"]
        Gr = T.ray(s["girdi"]["agirlik_ray_profili"], "Gr")
        LR = a["LR"]["deger"]
        taban_ray = M.SABIT["gn"] * Gr * LR / 1000.0
        self.assertAlmostEqual(s["_h"]["AN616"],
                               taban_ray + k3 * M.SABIT["MY_agirlik"], places=6)

    def test_pafta_islemi_kendi_sonucunu_verir(self):
        """FKR satırının gösterilen işlemi, basılan sonuca eşit olmalı.

        Eskiden işlem metni ofis sabitini ( 150 N ) yazıyor, sonuç türetilen
        MY ile hesaplanıyordu:  toplamı tutmayan bir pafta satırı.
        """
        s = M.hesapla({"mk_yok": True,
                       "makine_raya_biniyor": T.MAKINE_YUK_YOLU_RAY})
        a = self._bilesenler(s, "kuyu_tabani")["FKR = gn × Gr × LR / 1000 + k3 × MY + Fgt"]
        sayi = a["islem"].replace(".", "").replace(",", ".").replace("×", "*")
        self.assertAlmostEqual(eval(sayi), a["deger"], delta=1.0)   # noqa: S307


if __name__ == "__main__":
    unittest.main(verbosity=2)
