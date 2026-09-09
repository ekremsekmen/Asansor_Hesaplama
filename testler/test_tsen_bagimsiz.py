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
        expected = (2 * 9.81 * (g["beyan_yuku"] * (200 + g["kabin_genisligi"] / 8)
                    + g["kabin_agirligi"] * 200) / g["kabin_paten_arasi"])
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
        Fkt = 4 * gn * (g["kabin_agirligi"] + g["beyan_yuku"])
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
