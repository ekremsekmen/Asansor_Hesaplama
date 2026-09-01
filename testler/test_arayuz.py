# -*- coding: utf-8 -*-
"""
TEST 5  —  ARAYÜZ (tarayıcı)

Playwright kurulu değilse ya da sunucu kapalıysa zarifçe atlanır.
Kurmak için:  pip install playwright  &&  python3 -m playwright install chromium
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testler.ortak import Rapor      # noqa: E402

BASE = os.environ.get("AVAN_TEST_URL", "http://127.0.0.1:8760")


def _sunucu_var():
    try:
        urllib.request.urlopen(BASE + "/api/saglik", timeout=5).read()
        return True
    except Exception:                                    # noqa: BLE001
        return False


def adetSec(pg, n):
    """
    Trafik sekmesinde KAÇ ASANSÖR TANIMLANDIĞINI seçer.
    Gövde tektir ( #s-coklu ); yöntemi ( PAFTA / PAFTA-COKLU ) program
    asansörlerin aynı tip olup olmamasına bakarak kendisi seçer.
    Dönen: o an açık olan gövdenin kimliği ( her zaman "s-coklu" ).
    """
    pg.click('.sekme[data-sekme="trafik"]')
    pg.wait_for_timeout(250)
    if pg.evaluate("TRAFIK_ADET") != n:
        pg.click(f'.sayfa:not([hidden]) .adet-dg:nth-child({n})')
        pg.wait_for_timeout(1500)
    acik = pg.evaluate("[...document.querySelectorAll('.sayfa')]"
                       ".filter(s=>!s.hidden).map(s=>s.id)")
    return acik[0] if acik else None


def calistir():
    print("\n\033[1mTEST 5 — ARAYÜZ (tarayıcı)\033[0m")
    r = Rapor("Arayüz")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        r.atla("Playwright kurulu değil — arayüz testi atlandı "
               "(pip install playwright && python3 -m playwright install chromium)")
        return r
    if not _sunucu_var():
        r.atla(f"Sunucu {BASE} adresinde çalışmıyor — arayüz testi atlandı")
        return r

    with sync_playwright() as pw:
        try:
            tarayici = pw.chromium.launch()
        except Exception as e:                           # noqa: BLE001
            r.atla(f"Chromium başlatılamadı: {e}")
            return r
        pg = tarayici.new_page(viewport={"width": 1440, "height": 1000})
        konsol = []
        pg.on("console", lambda m: konsol.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: konsol.append("PAGEERROR " + str(e)))
        pg.goto(BASE, wait_until="networkidle")
        pg.wait_for_timeout(800)

        r.kontrol("sayfa başlığı doğru", "Avan" in pg.title(), f"→ {pg.title()!r}")

        # örnek proje yüklensin
        pg.evaluate("ornekYukle()")
        pg.wait_for_timeout(1800)

        # --- her sekme açılıyor ve içerik üretiyor
        r.esit("sekme sayısı 5", pg.eval_on_selector_all(".sekme", "e=>e.length"), 5)
        r.kontrol("ayrı 'çoklu' sekmesi kalmadı",
                  pg.query_selector('.sekme[data-sekme="coklu"]') is None)
        for sekme, ic_id in (("proje", None), ("trafik", None),
                             ("avan", "a_sonuc"), ("sabitler", "sabit_b_form"),
                             ("tablolar", "tablolar_ic")):
            pg.click(f'.sekme[data-sekme="{sekme}"]')
            pg.wait_for_timeout(450)
            if sekme == "trafik":
                acik = pg.evaluate("[...document.querySelectorAll('.sayfa')]"
                                   ".filter(s=>!s.hidden).map(s=>s.id)")
                r.kontrol("trafik sekmesinde tek gövde açık", len(acik) == 1, f"→ {acik}")
                r.esit("trafik gövdesi tek ( yöntem seçimi kalktı )",
                       acik and acik[0], "s-coklu")
                hedef = "c_sonuc"
                uzunluk = pg.eval_on_selector(f"#{hedef}", "e => e.innerText.length")
                r.kontrol("trafik sekmesi içerik üretti", uzunluk > 200, f"→ {uzunluk} karakter")
                continue
            r.kontrol(f"sekme '{sekme}' görünür", not pg.is_hidden(f"#s-{sekme}"))
            if ic_id:
                uzunluk = pg.eval_on_selector(f"#{ic_id}", "e => e.innerText.length")
                r.kontrol(f"sekme '{sekme}' içerik üretti", uzunluk > 200, f"→ {uzunluk} karakter")

        # --- trafik sonucu doğru mu (sunucudaki motorla aynı olmalı)
        adetSec(pg, 1)
        pg.wait_for_timeout(400)
        ekran = pg.inner_text("#c_sonuc")
        istek = urllib.request.Request(
            BASE + "/api/trafik", method="POST",
            data=json.dumps({"mod": "tek", "girdiler": {
                "bina_tipi": "Konut", "bina_yuksekligi": "39,98", "yapi_yuksekligi": "43",
                "N": "11", "h": "3", "hizli1": "44", "hizli2": "3", "P": "10",
                "kapi_genisligi": "900", "kapi_tipi": "Merkezden Açılan Oto."}}).encode(),
            headers={"Content-Type": "application/json"})
        api = json.loads(urllib.request.urlopen(istek, timeout=30).read())
        r.kontrol("ekrandaki sonuç API ile aynı", api["ozet"]["sonuc"] in ekran,
                  f"→ {api['ozet']['sonuc']!r}")
        r.kontrol("adım adım işlem gösteriliyor", "TR = 2·H·tv" in ekran)
        r.kontrol("kaynak referansları gösteriliyor", "Tablo-3" in ekran and "Tablo-5" in ekran)

        # --- canlı yeniden hesap
        pg.fill("#c_N", "25")
        pg.wait_for_timeout(900)
        a = pg.inner_text("#c_sonuc .olcut .k:first-child .dg2")
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(900)
        b = pg.inner_text("#c_sonuc .olcut .k:first-child .dg2")
        r.kontrol("girdi değişince sonuç güncelleniyor", a != b, f"→ N=25:{a}  N=11:{b}")

        # --- hata mesajı görünür
        pg.fill("#c_hizli1", "")
        pg.wait_for_timeout(900)
        r.kontrol("nüfus silinince hata kutusu çıkıyor",
                  "HESAP HATASI" in pg.inner_text("#c_sonuc"))
        pg.fill("#c_hizli1", "44")
        pg.wait_for_timeout(900)
        r.kontrol("girdi geri gelince hata kalkıyor",
                  "HESAP HATASI" not in pg.inner_text("#c_sonuc"))

        # --- trafikten avana OTOMATİK aktarım  ( v1.5 )
        #     Örnek proje 10 + 16 kişilik iki asansörlük bir gruptur.  Avandaki
        #     kapasite ve hız alanları BOŞALTILIP hiçbir düğmeye basılmadan
        #     trafikten geri gelmelidir; adet de kendiliğinden eşitlenmelidir.
        adetSec(pg, 2)
        pg.wait_for_timeout(900)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)
        pg.evaluate("['a_kapasite1','a_kapasite2','a_V1','a_V2']"
                    ".forEach(i=>{document.getElementById(i).value='';}); planla();")
        pg.wait_for_timeout(1800)
        r.esit("otomatik: 1. asansör kapasitesi", pg.input_value("#a_kapasite1"), "10")
        r.esit("otomatik: 2. asansör kapasitesi", pg.input_value("#a_kapasite2"), "16")
        r.kontrol("otomatik: kabin hızı da doldu",
                  pg.input_value("#a_V1") not in ("", None), f"→ {pg.input_value('#a_V1')!r}")
        r.esit("avan adedi trafik adediyle eşitlendi",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "2")
        r.kontrol("1. asansör 'trafik grubundan' etiketli",
                  "trafik grubundan" in pg.evaluate(
                      "document.getElementById('a_etiket1').textContent"))
        r.kontrol("3. asansör kartı kapalı",
                  "pasif" in (pg.get_attribute("#a_kutu3", "class") or ""))
        r.kontrol("'kullan' kutuları artık gizli",
                  pg.is_hidden("#a_aktif1"))
        adetSec(pg, 1)
        pg.wait_for_timeout(700)

        # --- avan sonucu
        avan_ekran = pg.inner_text("#a_sonuc")
        for beklenen in ("SONUÇ ÖZETİ", "MOTOR GÜCÜ HESABI", "KUVVET HESAPLARI",
                         "KABİN AYDINLATMA", "KUYU AYDINLATMA", "KURULU GÜÇ",
                         "GERİLİM DÜŞÜMÜ", "TEMEL TOPRAKLAMA"):
            r.kontrol(f"avan ekranında '{beklenen}' bölümü var", beklenen in avan_ekran)

        # ===================================================================
        #  v1.3 — bodrum, imalatçı süreleri, askı/denge, tutarlılık köprüsü
        # ===================================================================
        adetSec(pg, 1)
        pg.wait_for_timeout(400)
        r.kontrol("⑪ bodrum alanı var", pg.is_visible("#c_bodrum"))
        pg.fill("#c_N", "13"); pg.fill("#c_h", "3")
        pg.fill("#c_bodrum", "")
        pg.wait_for_timeout(1100)
        _v0 = pg.inner_text("#c_sonuc")
        pg.fill("#c_bodrum", "2")
        pg.wait_for_timeout(1100)
        _v2 = pg.inner_text("#c_sonuc")
        r.kontrol("bodrum girilince hesap değişiyor", _v0 != _v2)
        r.kontrol("bodrum satırı paftada görünüyor",
                  "Bodrum durak adedi" in _v2)
        r.kontrol("toplam durak adedi paftada",
                  "Toplam durak adedi" in _v2)
        r.kontrol("bodrum açıklaması ( ! ) balonunda",
                  "H (Tablo-3)" in pg.eval_on_selector_all(
                      "#c_sonuc .bilgi-balon", "e=>e.map(x=>x.textContent).join(' ')"))
        r.kontrol("toplam seyahat mesafesi paftada",
                  "Toplam seyahat mesafesi" in _v2)
        pg.fill("#c_bodrum", "99")
        pg.wait_for_timeout(1100)
        r.kontrol("geçersiz bodrum hata veriyor",
                  "HESAP HATASI" in pg.inner_text("#c_sonuc"))
        pg.fill("#c_bodrum", "")
        #  N'yi örnek projedeki değere geri al: adet değişince ortak girdiler
        #  çoklu gövdeye aynalanıyor, sonraki adımlar örnek projeyi bekliyor.
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(1000)

        # sekme uyarı rozeti — 6 kişilik kabin erişilebilirlik uyarısı üretir
        pg.select_option("#c_P1", "6")
        pg.wait_for_timeout(1100)
        r.kontrol("uyarıda sekme rozeti çıkıyor",
                  pg.is_visible('.sekme[data-sekme="trafik"] .sekme-rozet'))
        r.kontrol("6 kişi erişilebilirlik uyarısı ekranda GÖRÜNÜR (balonda değil)",
                  "81-70" in pg.inner_text("#c_sonuc"))
        pg.select_option("#c_P1", "10")
        pg.wait_for_timeout(1100)
        r.kontrol("uyarı bitince rozet kalkıyor",
                  not pg.is_visible('.sekme[data-sekme="trafik"] .sekme-rozet'))

        # ara değerli kapı genişlikleri artık hesaplanıyor
        for _kg in ("700", "1000", "1200"):
            pg.select_option("#c_kg1", _kg)
            pg.wait_for_timeout(1000)
            r.kontrol(f"kapı {_kg} mm hesaplanıyor",
                      "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        pg.select_option("#c_kg1", "900")
        pg.wait_for_timeout(900)

        # çoklu: asansör bazında bodrum ve imalatçı süreleri
        adetSec(pg, 2)
        r.kontrol("çoklu ortak bodrum alanı var", pg.is_visible("#c_bodrum"))
        pg.click('#s-coklu .katla:has-text("İleri seçenekler") >> nth=0')
        pg.wait_for_timeout(300)
        for _id in ("#c_bodrum1", "#c_mta1", "#c_mtk1", "#c_mtg1", "#c_mtp1"):
            r.kontrol(f"çoklu {_id} alanı açıldı", pg.is_visible(_id))
        _c0 = pg.inner_text("#c_sonuc")
        pg.fill("#c_mta1", "2,9")
        pg.wait_for_timeout(1200)
        _c1 = pg.inner_text("#c_sonuc")
        r.kontrol("çoklu manuel ta hesabı değiştiriyor", _c0 != _c1)
        r.kontrol("çoklu manuel süre uyarısı çıkıyor", "imalatçı verisiyle" in _c1)
        r.kontrol("uyarı balona girmedi, açıkta",
                  "imalatçı verisiyle" not in pg.eval_on_selector_all(
                      "#c_sonuc .bilgi-balon", "e=>e.map(x=>x.textContent).join(' ')"))
        pg.fill("#c_mta1", "")
        pg.wait_for_timeout(1000)
        adetSec(pg, 1)

        # avan: asansör bazında askı ve denge
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)
        #  v1.4: askı oranı artık normal girdi ( açılır liste ), denge faktörü
        #  ise ofis standardında kalıp katlanır bölümden ezilebiliyor.
        r.kontrol("askı oranı doğrudan görünür", pg.is_visible("#a_i_palanga1"))
        _a0 = pg.inner_text("#a_sonuc")
        pg.select_option("#a_i_palanga1", "1")
        pg.wait_for_timeout(1300)
        _a1 = pg.inner_text("#a_sonuc")
        r.kontrol("askı oranı değişince avan hesabı değişiyor", _a0 != _a1)
        pg.select_option("#a_i_palanga1", "2")
        pg.wait_for_timeout(1200)
        pg.click('#s-avan .katla:has-text("Ofis standardından farklı") >> nth=0')
        pg.wait_for_timeout(300)
        r.kontrol("denge faktörü alanı açıldı", pg.is_visible("#a_q_denge1"))
        _b0 = pg.inner_text("#a_sonuc")
        pg.fill("#a_q_denge1", "0,45")
        pg.wait_for_timeout(1300)
        _b1 = pg.inner_text("#a_sonuc")
        r.kontrol("denge faktörü değişince hesap değişiyor", _b0 != _b1)
        r.kontrol("asansör bazı kaynağı görünüyor", "asansör bazında" in _b1)
        pg.fill("#a_q_denge1", "")
        pg.wait_for_timeout(1200)

        # trafik ↔ avan tutarlılık köprüsü
        #  Örnek proje kendi doğal hâlinde ( 2 asansörlük grup ) sınanır.
        adetSec(pg, 2)
        pg.wait_for_timeout(900)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(300)
        pg.select_option("#a_kapasite1", "25")
        pg.wait_for_timeout(1400)
        r.kontrol("kapasite tutarsızlığı uyarısı çıkıyor",
                  "kapasite trafik hesabında" in pg.inner_text("#a_sonuc"))
        pg.click('#s-avan button:has-text("Trafikten güncelle")')
        pg.wait_for_timeout(1600)
        r.kontrol("güncellemeden sonra tutarsızlık uyarısı kalkıyor",
                  "kapasite trafik hesabında" not in pg.inner_text("#a_sonuc"))
        #  örnek proje kendi içinde tutarlı olmalı — hiç uyarı üretmemeli
        r.kontrol("örnek projede tutarlılık uyarısı yok",
                  "NOLU ASANSÖR:" not in pg.inner_text("#a_sonuc"))
        #  blok başında değiştirilen girdiyi geri al (sonraki adımlar N=11 bekler)
        adetSec(pg, 1)
        pg.wait_for_timeout(300)
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(1100)

        # ===================================================================
        #  ( ! ) açıklama simgesi — uzun yöntem metinleri balonda
        # ===================================================================
        adetSec(pg, 1)
        pg.wait_for_timeout(500)
        _n = pg.eval_on_selector_all(".bilgi", "e=>e.length")
        r.kontrol("sayfada ( ! ) simgeleri var", _n >= 8, f"→ {_n} adet")
        _bilgi = pg.query_selector('label:has-text("Bodrum durağı") .bilgi')
        r.kontrol("bodrum alanında ( ! ) var", _bilgi is not None)
        _balon = _bilgi.query_selector(".bilgi-balon")
        r.kontrol("balon kapalıyken görünmüyor", not _balon.is_visible())
        _bilgi.hover()
        pg.wait_for_timeout(400)
        r.kontrol("üzerine gelince balon açılıyor", _balon.is_visible())
        r.kontrol("balonda bodrum açıklaması var", "H (Tablo-3)" in _balon.inner_text())
        #  balon kırpılmıyor / ekrandan taşmıyor
        _k = _balon.bounding_box()
        _vp = pg.viewport_size
        r.kontrol("balon ekranın sağına taşmıyor",
                  _k["x"] + _k["width"] <= _vp["width"] - 4,
                  f"→ sağ kenar {_k['x']+_k['width']:.0f} / {_vp['width']}")
        r.kontrol("balon ekranın soluna taşmıyor", _k["x"] >= 4)
        r.kontrol("balon alta taşmıyor",
                  _k["y"] + _k["height"] <= _vp["height"] - 4)
        pg.mouse.move(0, 0)
        pg.wait_for_timeout(350)
        r.kontrol("mouse çekilince balon kapanıyor", not _balon.is_visible())
        #  dokunmatik: tıklayınca fare çekilse bile açık kalır, Esc kapatır
        _bilgi.click()
        pg.mouse.move(0, 0)
        pg.wait_for_timeout(350)
        r.kontrol("tıklayınca fare çekilse de balon açık kalıyor", _balon.is_visible())
        pg.keyboard.press("Escape")
        pg.wait_for_timeout(300)
        r.kontrol("Esc balonu kapatıyor", not _balon.is_visible())
        #  klavye ile de açılmalı (erişilebilirlik)
        _bilgi.focus()
        pg.wait_for_timeout(300)
        r.kontrol("klavye odağıyla balon açılıyor", _balon.is_visible())
        pg.mouse.click(5, 5)
        pg.wait_for_timeout(250)
        #  sağ paneldeki bölüm başlığında da olmalı
        r.kontrol("bölüm başlığında ( ! ) var",
                  pg.query_selector("#c_sonuc .serit .bilgi") is not None)

        # ===================================================================
        #  v1.4 — birleşik trafik sekmesi, makine tipi, MRL kutusu
        # ===================================================================
        #  Adet seçici iki gövdeyi doğru değiştiriyor ve ortak girdiler duruyor
        r.esit("adet 1 → aynı gövde ( tek ekran )", adetSec(pg, 1), "s-coklu")
        r.esit("adet 1: N korundu", pg.input_value("#c_N"), "11")
        r.esit("adet 1: nüfus korundu", pg.input_value("#c_hizli1"), "44")
        r.kontrol("adet 1: hesap yapıldı", "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        #  Tek hesap "n adet gerekir" diyorsa tek tıkla gruba geçilebilmeli
        _ekran = pg.inner_text("#c_sonuc")
        r.kontrol("gerekli adet > 1 iken geçiş düğmesi çıkıyor",
                  "asansör olarak tanımla" in _ekran, f"→ {_ekran[:60]!r}")
        r.esit("adet 3 → grup gövdesi", adetSec(pg, 3), "s-coklu")
        r.esit("adet 3: ortak N aynalandı", pg.input_value("#c_N"), "11")
        r.esit("adet 3: nüfus aynalandı", pg.input_value("#c_hizli1"), "44")
        r.esit("adet 3: görünen kolon sayısı",
               pg.evaluate("[1,2,3,4].filter(i=>!document.getElementById('c_kutu'+i).hidden).length"), 3)
        r.kontrol("adet 3: kolonlar dolduruldu",
                  all(pg.input_value(f"#c_P{i}") for i in (1, 2, 3)))
        r.esit("adet 3: 4. kolon boşaltıldı", pg.input_value("#c_P4"), "")
        r.kontrol("adet 3: grup hesabı yapıldı",
                  "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        r.esit("adet 1'e dönüş", adetSec(pg, 1), "s-coklu")
        r.esit("dönüşte N hâlâ duruyor", pg.input_value("#c_N"), "11")

        #  Avan: makine tipi η'yı dolduruyor, askı oranı ayrı girdi
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(600)
        r.kontrol("makine tipi alanı var", pg.is_visible("#a_makine_tipi1"))
        r.kontrol("askı oranı alanı var", pg.is_visible("#a_i_palanga1"))
        pg.select_option("#a_makine_tipi1", "Dişli")
        pg.wait_for_timeout(1300)
        r.esit("dişli seçilince η = 0,50", pg.input_value("#a_eta1"), "0,50")
        pg.select_option("#a_makine_tipi1", "Dişlisiz")
        pg.wait_for_timeout(1300)
        r.esit("dişlisiz seçilince η = 0,85", pg.input_value("#a_eta1"), "0,85")
        #  askı oranı yalnız verim üzerinden etkili: 1:1 → η′ = η
        pg.select_option("#a_i_palanga1", "1")
        pg.wait_for_timeout(1300)
        _m = pg.inner_text("#a_sonuc")
        r.kontrol("1:1 seçilince palanga düşüşü uygulanmıyor", "0,85" in _m)
        pg.select_option("#a_i_palanga1", "2")
        pg.wait_for_timeout(1300)
        r.kontrol("2:1 seçilince η′ = 0,75", "0,75" in pg.inner_text("#a_sonuc"))
        #  toplam sistem verimi: palanga düşüşü İKİNCİ KEZ uygulanmamalı
        pg.check("#a_toplam_verim1")
        pg.fill("#a_eta1", "0,82")
        pg.wait_for_timeout(1400)
        _m = pg.inner_text("#a_sonuc")
        r.kontrol("toplam verim: η′ = η ( 0,82 )", "0,82" in _m)
        r.kontrol("toplam verim uyarısı çıkıyor", "TOPLAM SİSTEM VERİMİ" in _m)
        pg.uncheck("#a_toplam_verim1")
        pg.fill("#a_eta1", "0,85")
        pg.wait_for_timeout(1300)

        #  MRL işaret kutusu
        r.kontrol("MRL kutusu var", pg.is_visible("#a_mk_yok"))
        pg.check("#a_mk_yok")
        pg.wait_for_timeout(1300)
        r.kontrol("MRL işaretliyken ölçüler kapanıyor",
                  pg.evaluate("document.getElementById('a_mk_uzunluk').disabled"))
        r.kontrol("MRL işaretliyken hesap yapılmıyor",
                  "MRL" in pg.inner_text("#a_sonuc"))
        pg.uncheck("#a_mk_yok")
        pg.wait_for_timeout(1300)
        r.kontrol("MRL kapalı + ölçü yok → açık uyarı",
                  "ÖLÇÜLERİ GİRİLMEDİ" in pg.inner_text("#a_sonuc"))
        pg.fill("#a_mk_uzunluk", "4200")
        pg.fill("#a_mk_genislik", "3100")
        pg.wait_for_timeout(1400)
        r.kontrol("ölçü girilince makine dairesi hesaplanıyor",
                  "MAKİNE DAİRESİ AYDINLATMA HESABI" in pg.inner_text("#a_sonuc"))
        pg.check("#a_mk_yok")
        pg.wait_for_timeout(1200)

        # ===================================================================
        #  v1.5 — asansör adedi TEK YERDE: avan trafiği takip eder
        # ===================================================================
        pg.check("#a_mk_yok")
        adetSec(pg, 2)
        pg.wait_for_timeout(1000)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(700)
        r.esit("avan adedi 2'ye eşitlendi",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "2")

        # ===================================================================
        #  v1.6 — ofis varsayılanları: değişmeyenler bir kez ayarlanır
        # ===================================================================
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(500)
        r.kontrol("ofis standardı paneli var",
                  pg.query_selector("#sabit_b_form") is not None)
        #  Sabitler HESAP BAZINDA gruplu olmalı ( v1.7 )
        _gruplar = pg.eval_on_selector_all(
            "#sabit_b_form .bolum-bas",
            "e=>e.map(x=>x.textContent.split('—')[0].trim())")
        for _g in ("MOTOR GÜCÜ VE KUVVETLER", "AYDINLATMA",
                   "KURULU GÜÇ VE GERİLİM DÜŞÜMÜ", "TEMEL TOPRAKLAMA"):
            r.kontrol(f"sabit grubu var: {_g}",
                      any(_g in x for x in _gruplar), f"→ {_gruplar}")
        r.kontrol("gruba yazılmamış sabit kalmadı",
                  "DİĞER" not in pg.inner_text("#sabit_b_form"))
        for _k in ("q_denge", "n_ray", "gf", "Fmt", "kabin_armatur_W", "kuyu_armatur_W",
                   "priz_adedi", "cosfi", "UL", "IDn", "lc", "ayd_sutun"):
            r.kontrol(f"SABİTLER alanı yerinde: {_k}",
                      pg.query_selector("#sb_" + _k) is not None)
        for _k in ("U", "kappa", "eps_max", "gr", "Fmk", "Fsh", "S1", "S2",
                   "L2", "kablo_tipi", "L1_pay", "beta", "cubuk_sayisi"):
            r.kontrol(f"ofis varsayılanı alanı var: {_k}",
                      pg.query_selector("#of_" + _k) is not None)
        #  Kat yüksekliği ve kapı tipi ofis sabiti DEĞİL — her projede değişirler
        for _k in ("h", "kapi_tipi"):
            r.kontrol(f"ofis sabitlerinde YOK: {_k}",
                      pg.query_selector("#of_" + _k) is None)
        r.kontrol("kat yüksekliği trafik sekmesinde",
                  pg.query_selector("#c_h") is not None
                  and pg.query_selector("#c_h") is not None)
        r.kontrol("kapı tipi trafik sekmesinde",
                  pg.query_selector("#c_kt1") is not None)
        r.kontrol("taşındı bilgi bandı kaldırıldı",
                  pg.query_selector("#sabit_tasindi") is None)
        r.esit("U ofis varsayılanı 380", pg.input_value("#of_U"), "380")
        r.esit("çubuk adedi 4 ( Excel ile aynı )", pg.input_value("#of_cubuk_sayisi"), "4")

        #  Avan ortak panelinden kalkmış olmalı
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(500)
        for _k in ("a_U", "a_kappa", "a_eps_max"):
            r.kontrol(f"{_k} avan panelinden kalktı", pg.query_selector("#" + _k) is None)
        #  v1.7: β ve çubuk adedi de ofis standardına taşındı
        for _k in ("a_beta", "a_cubuk_sayisi"):
            r.kontrol(f"{_k} avan panelinden kalktı", pg.query_selector("#" + _k) is None)
        r.kontrol("şerit boyu ( L ) avan panelinde kaldı — projeye özel",
                  pg.query_selector("#a_serit_L") is not None)

        #  Asansör kartı: malzeme alanları katlanır bölüme indi
        pg.evaluate("document.getElementById('a_ozel1').style.display='none';")
        pg.wait_for_timeout(200)
        r.kontrol("ray kütlesi kartta doğrudan görünmüyor", pg.is_hidden("#a_gr1"))
        r.esit("ray kütlesi boş ( ofis standardından gelecek )",
               pg.input_value("#a_gr1"), "")
        r.esit("ray kütlesi yer tutucusu ofis değeri",
               pg.get_attribute("#a_gr1", "placeholder"), "17,91")
        _s = pg.inner_text("#a_sonuc")
        r.kontrol("paftada kaynak 'OFİS VARSAYILANI' yazıyor", "OFİS VARSAYILANI" in _s)
        r.kontrol("hesap yapılıyor ( eksik girdi uyarısı yok )",
                  "girdi tamamlanmadı" not in _s)

        #  Nsç otomatik: 16 kişilik asansör 11 kW ile UYGUN DEĞİL çıkıyordu
        r.kontrol("motor gücü otomatik seçildi",
                  "otomatik — standart kademe" in _s)
        r.kontrol("16 kişilik asansöre 15 kW seçildi", "15,00" in _s)
        r.kontrol("motor kontrolü uygun", "UYGUN DEĞİL" not in _s)
        r.esit("Nsç alanı boş, yer tutucu otomatik",
               pg.get_attribute("#a_Nsc1", "placeholder"), "otomatik")

        #  L1 = Hk + ofis payı
        r.kontrol("L1 Hk + ofis payından türetildi", "Hk + ofis payı" in _s)

        #  Ofis değeri değişince asansör hesabı da değişir ( tek yerden )
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(300)
        pg.fill("#of_gr", "23,7")
        pg.wait_for_timeout(1500)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(600)
        r.kontrol("ofis ray kütlesi değişince hesap değişti",
                  "23,70" in pg.inner_text("#a_sonuc"))
        r.esit("yer tutucu da güncellendi",
               pg.get_attribute("#a_gr1", "placeholder"), "23,7")

        #  Asansör bazında ezme + rozet
        #  ( katlanır bölüm önceki bloklarda açılmış olabilir — tıklamak yerine
        #    doğrudan açık duruma getiriyoruz ki tekrar kapanmasın )
        pg.evaluate("document.getElementById('a_ozel1').style.display='';")
        pg.wait_for_timeout(250)
        pg.fill("#a_gr1", "17,91")
        pg.wait_for_timeout(1500)
        r.kontrol("özel değer rozeti çıktı",
                  "özel" in pg.evaluate(
                      "document.getElementById('a_ozel_rozet1').textContent"))
        r.kontrol("ezilen değer paftada asansör bazında görünüyor",
                  "GİRİŞ — asansör bazında" in pg.inner_text("#a_sonuc"))
        pg.fill("#a_gr1", "")
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(300)
        pg.fill("#of_gr", "17,91")
        pg.wait_for_timeout(1400)

        #  Q ve Gk artık GİRDİ değil, türetilen değer  ( v1.7 )
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(600)
        r.kontrol("Q alanı salt okunur",
                  pg.get_attribute("#a_Q_goster1", "readonly") is not None)
        r.kontrol("Gk alanı salt okunur",
                  pg.get_attribute("#a_Gk_goster1", "readonly") is not None)
        r.kontrol("Q alanı sarı ( girdi ) değil, gri gösterilir",
                  "salt" in (pg.get_attribute("#a_Q_goster1", "class") or ""))
        #  ( katlanır bölüm önceki bloklarda açılmış olabilir — kapalı duruma
        #    getirip "ana kartta görünmüyor" iddiasını sınıyoruz )
        pg.evaluate("document.getElementById('a_ozel1').style.display='none';")
        pg.wait_for_timeout(200)
        r.kontrol("Q elle ana kartta görünmüyor", pg.is_hidden("#a_Q_elle1"))
        r.kontrol("Gk elle ana kartta görünmüyor", pg.is_hidden("#a_Gk_elle1"))
        _kap = pg.input_value("#a_kapasite1")
        r.kontrol("Q kapasiteden geliyor",
                  pg.input_value("#a_Q_goster1") not in ("", None),
                  f"→ kapasite {_kap}, Q {pg.input_value('#a_Q_goster1')!r}")
        pg.select_option("#a_kapasite1", "25")
        pg.wait_for_timeout(1600)
        r.esit("kapasite 25 kişi → Q = 2.000 kg", pg.input_value("#a_Q_goster1"), "2.000")
        r.esit("Q = 2.000 kg → Gk = 1.600 kg ( Tablo-11 )",
               pg.input_value("#a_Gk_goster1"), "1.600")
        pg.select_option("#a_kapasite1", "10")
        pg.wait_for_timeout(1600)
        r.esit("kapasite 10 kişi → Q = 800 kg", pg.input_value("#a_Q_goster1"), "800")
        #  Tablo dışına çıkmak: katlanır bölümdeki Q elle
        pg.evaluate("document.getElementById('a_ozel1').style.display='';")
        pg.wait_for_timeout(250)
        pg.fill("#a_Q_elle1", "1500")
        pg.wait_for_timeout(1700)
        r.esit("Q elle girilince gösterim onu yansıtıyor",
               pg.input_value("#a_Q_goster1"), "1.500")
        r.kontrol("Q elle rozette sayılıyor",
                  "özel" in pg.evaluate(
                      "document.getElementById('a_ozel_rozet1').textContent"))
        pg.fill("#a_Q_elle1", "")
        pg.wait_for_timeout(1700)
        r.esit("Q elle silinince tablo değerine dönüyor",
               pg.input_value("#a_Q_goster1"), "800")
        r.kontrol("türetilen alanlar proje dosyasına yazılmıyor",
                  pg.evaluate("!('a_Q_goster1' in tumGirdiler()) "
                              "&& !('a_Gk_goster1' in tumGirdiler())"))

        #  L1 yer tutucusu hesaplanan değeri gösteriyor ( "Hk + pay" görünür olsun )
        r.kontrol("L1 yer tutucusu Hk + payı gösteriyor",
                  "Hk +" in (pg.get_attribute("#a_L11", "placeholder") or ""),
                  f"→ {pg.get_attribute('#a_L11', 'placeholder')!r}")
        pg.fill("#a_Hk1", "45")
        pg.wait_for_timeout(1700)
        r.kontrol("Hk değişince L1 yer tutucusu izliyor",
                  "48,50" in (pg.get_attribute("#a_L11", "placeholder") or ""),
                  f"→ {pg.get_attribute('#a_L11', 'placeholder')!r}")
        pg.fill("#a_Hk1", "38,50")
        pg.wait_for_timeout(1500)
        #  Topraklama L'si ile asansör L1'i karışmasın — çevre karşılaştırması
        r.kontrol("temel çevresi karşılaştırma notu çıkıyor",
                  "çevresi" in pg.evaluate(
                      "document.getElementById('a_temel_cevre').textContent"))
        r.kontrol("şerit boyu alanı topraklama diye etiketli",
                  "topraklama" in pg.eval_on_selector(
                      "#a_serit_L", "e=>e.closest('.alan').querySelector('label').textContent"))

        # ------------------------------------------------------------------
        #  v1.8 — ŞERİT BOYU TEMEL ÖLÇÜLERİNDEN TÜRETİLİR
        #  Ofiste yalnız uzunluk ve genişlik giriliyor; alan boş kalınca
        #  kullanılan boy YER TUTUCUDA ve açılımıyla görünmeli.
        # ------------------------------------------------------------------
        r.esit("örnek projede şerit boyu boş bırakılmış",
               pg.input_value("#a_serit_L"), "")
        _yt = pg.get_attribute("#a_serit_L", "placeholder")
        r.kontrol("şerit boyu yer tutucusu türetilen değeri gösteriyor",
                  "102,30" in (_yt or ""), f"→ {_yt!r}")
        _ac = pg.evaluate("document.getElementById('a_serit_tahmin').textContent")
        r.kontrol("türetme açılımı ekranda", "ring" in _ac and "102,30" in _ac,
                  f"→ {_ac!r}")
        #  Elle yazılan boy türetileni ezer ve açılım kaybolur
        pg.fill("#a_serit_L", "140")
        pg.wait_for_timeout(1500)
        _ac2 = pg.evaluate("document.getElementById('a_serit_tahmin').textContent")
        r.kontrol("elle girilince türetme açılımı kalkıyor", _ac2.strip() == "",
                  f"→ {_ac2!r}")
        pg.fill("#a_serit_L", "")
        pg.wait_for_timeout(1500)
        r.kontrol("alan boşaltılınca türetme geri geliyor",
                  "102,30" in (pg.get_attribute("#a_serit_L", "placeholder") or ""))
        #  Göz aralığı ofis standardında olmalı
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(500)
        r.kontrol("karelaj gözü ofis standardında",
                  pg.query_selector("#of_goz_araligi") is not None)
        r.esit("karelaj gözü varsayılanı 20", pg.input_value("#of_goz_araligi"), "20")
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)

        #  Şablon durumu — yanlış / eski Excel konmuşsa burada görünür
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(700)
        _sd = pg.inner_text("#sablon_durumu")
        r.kontrol("şablon durumu kartı dolu", len(_sd) > 100, f"→ {len(_sd)} karakter")
        r.kontrol("iki şablon da doğrulandı", "doğrulandı" in _sd)
        r.kontrol("şablon parmak izi gösteriliyor", "md5" in _sd)
        r.kontrol("şablon dosya adları yazıyor",
                  "ASANSOR_TRAFIK_HESABI" in _sd and "ASANSOR_AVAN_HESAPLARI" in _sd)

        #  Manuel k / manuel V ana akıştan kalktı — katlanır bölümde
        adetSec(pg, 2)
        pg.wait_for_timeout(900)
        r.kontrol("çokluda manuel k doğrudan görünmüyor", pg.is_hidden("#c_manuel_k"))
        r.kontrol("çokluda manuel V doğrudan görünmüyor", pg.is_hidden("#c_manuel_V"))
        pg.click('#s-coklu .katla:has-text("Manuel değerler")')
        pg.wait_for_timeout(400)
        r.kontrol("manuel değerler bölümü açıldı", pg.is_visible("#c_manuel_k"))
        pg.fill("#c_manuel_k", "0,08")
        pg.wait_for_timeout(1300)
        r.kontrol("elle girilen değer rozette görünüyor",
                  "elle" in pg.evaluate(
                      "document.getElementById('c_manuel_rozet').textContent"))
        #  Tablo-9'da değeri olan bina tipinde manuel k reddedilmeli
        r.kontrol("Tablo-9 varken manuel k reddediliyor",
                  "manuel k girilemez" in pg.inner_text("#c_sonuc"))
        pg.fill("#c_manuel_k", "")
        pg.wait_for_timeout(1300)
        r.kontrol("manuel k silinince hesap düzeliyor",
                  "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        r.esit("rozet de temizlendi",
               pg.evaluate("document.getElementById('c_manuel_rozet').textContent"), "")
        adetSec(pg, 1)
        pg.wait_for_timeout(700)

        #  Askı oranı OFİS SABİTİ DEĞİL — B) panelinden kalkmış olmalı
        pg.click('.sekme[data-sekme="sabitler"]')
        pg.wait_for_timeout(500)
        r.kontrol("askı oranı ofis standardı panelinde YOK",
                  pg.query_selector("#sb_i_palanga") is None)
        r.kontrol("denge faktörü ofis standardında duruyor",
                  pg.query_selector("#sb_q_denge") is not None)
        r.kontrol("diğer ofis sabitleri yerinde",
                  all(pg.query_selector("#sb_" + k) is not None
                      for k in ("n_ray", "gf", "Fmt", "cosfi", "UL")))
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)
        r.kontrol("askı oranı asansör kartında", pg.is_visible("#a_i_palanga1"))

        #  TRAFİK DEĞİŞİRSE AVAN İZLER  —  hiçbir düğmeye basmadan
        adetSec(pg, 2)
        pg.select_option("#c_P1", "13")
        pg.wait_for_timeout(1700)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(800)
        r.esit("trafikte kapasite değişince avan kendiliğinden izliyor",
               pg.input_value("#a_kapasite1"), "13")
        r.kontrol("izlediği için tutarsızlık uyarısı yok",
                  "kapasite trafik hesabında" not in pg.inner_text("#a_sonuc"))

        #  Elle girilen değer, TRAFİK DEĞİŞMEDİKÇE korunur ( ezilmez )
        pg.select_option("#a_kapasite1", "16")
        pg.wait_for_timeout(1600)
        r.esit("elle girilen değer korunuyor", pg.input_value("#a_kapasite1"), "16")
        r.kontrol("elle değiştirilince uyarı çıkıyor",
                  "kapasite trafik hesabında" in pg.inner_text("#a_sonuc"))
        pg.wait_for_timeout(900)
        r.esit("ikinci hesapta da ezilmedi", pg.input_value("#a_kapasite1"), "16")

        #  Trafik yeniden değişince avan yine izler ( elle girilen değer aşılır )
        adetSec(pg, 2)
        pg.select_option("#c_P1", "10")
        pg.wait_for_timeout(1700)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(800)
        r.esit("trafik yeniden değişince avan tekrar izliyor",
               pg.input_value("#a_kapasite1"), "10")
        r.kontrol("izleme sonrası uyarı kalmadı",
                  "kapasite trafik hesabında" not in pg.inner_text("#a_sonuc"))

        #  Trafik adedi artınca avan kartı kendiliğinden açılır
        adetSec(pg, 3)
        pg.wait_for_timeout(1200)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(800)
        r.esit("trafik 3 olunca avan adedi de 3",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "3")
        r.kontrol("3. asansör kartı kendiliğinden açıldı", pg.is_checked("#a_aktif3"))
        r.esit("3. asansörün kapasitesi trafikten doldu",
               pg.input_value("#a_kapasite3"),
               pg.evaluate("document.getElementById('c_P3').value") or "10")
        r.kontrol("açılan kart 'trafik grubundan' etiketli",
                  "trafik grubundan" in pg.evaluate(
                      "document.getElementById('a_etiket3').textContent"))
        r.kontrol("eksik girdi uyarısı görünür ( sessiz kalmıyor )",
                  "3 NOLU ASANSÖR" in pg.inner_text("#a_sonuc"))

        #  Trafik adedinin ALTINA inilemez
        pg.evaluate("avanAdediSec(1)")
        pg.wait_for_timeout(700)
        r.esit("avan adedi trafiğin altına inmedi",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "3")
        r.kontrol("1 ve 2 düğmeleri kilitli görünüyor",
                  pg.evaluate("[...document.querySelectorAll('#adet_dugmeler_a .adet-dg')]"
                              ".slice(0,2).every(b=>b.classList.contains('kilitli'))"))

        #  Trafik grubu DIŞI asansör: adedi elle artır → not çıkar, uyarı değil
        pg.evaluate("avanAdediSec(4)")
        pg.wait_for_timeout(900)
        r.esit("elle 4'e çıkarıldı",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "4")
        r.kontrol("4. asansör 'trafik grubu dışı' etiketli",
                  "trafik grubu dışı" in pg.evaluate(
                      "document.getElementById('a_etiket4').textContent"))
        pg.select_option("#a_kapasite4", "6")
        pg.wait_for_timeout(1500)
        _s = pg.inner_text("#a_sonuc")
        r.kontrol("trafik dışı asansör NOT olarak bildiriliyor",
                  "trafik grubunda olmayan" in _s, f"→ {_s[:80]!r}")
        r.kontrol("bu bir uyarı değil, mavi not kutusunda",
                  pg.evaluate("[...document.querySelectorAll('#a_sonuc .uyari.mavi')]"
                              ".some(e=>e.textContent.includes('trafik grubunda olmayan'))"))

        #  Trafik grubu küçülünce DOLU kart kapanmaz — trafik dışına alınır
        adetSec(pg, 2)
        pg.wait_for_timeout(1200)
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(800)
        r.kontrol("dolu 4. asansör kapanmadı", pg.is_checked("#a_aktif4"))
        r.kontrol("3. asansör hâlâ açık ( kapasitesi dolu )", pg.is_checked("#a_aktif3"))

        #  Temizlik: sonraki bloklar 2 asansörlük örnek projeyi bekler
        pg.evaluate("['a_kapasite3','a_kapasite4'].forEach(i=>{"
                    "const e=document.getElementById(i); e.value='';}); AVAN_EK=0; planla();")
        pg.wait_for_timeout(1400)
        r.esit("boşaltılınca avan adedi 2'ye döndü",
               pg.inner_text("#adet_dugmeler_a .adet-dg.secili").strip(), "2")
        adetSec(pg, 1)
        pg.wait_for_timeout(800)
        pg.fill("#c_N", "11")
        pg.wait_for_timeout(1100)

        # --- kalıcılık: sayfa yenilenince girdiler duruyor
        #  Proje kimliği artık PROJE KAPAĞI sekmesindedir ( k_* alanları );
        #  eski "Proje Bilgileri" kartı ( p_proje_adi … ) kaldırıldı.
        #  Kalıcılık kapak alanı üzerinden denetlenir.
        pg.click('.sekme[data-sekme="proje"]')
        pg.wait_for_timeout(250)
        pg.fill("#k_owner", "Kalıcılık Denemesi A.Ş.")
        pg.fill("#k_city", "İstanbul")
        pg.wait_for_timeout(700)
        pg.click('.sekme[data-sekme="trafik"]')
        pg.wait_for_timeout(250)
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(1500)
        r.esit("yenileme sonrası N korundu", pg.input_value("#c_N"), "11")
        r.esit("yenileme sonrası kapak alanı korundu",
               pg.input_value("#k_owner"), "Kalıcılık Denemesi A.Ş.")
        r.esit("yenileme sonrası kapak alanı korundu ( il )",
               pg.input_value("#k_city"), "İstanbul")

        # --- indirme düğmeleri gerçekten dosya veriyor
        #  Trafik tek gövdedir; 1 ve 2 asansör tanımıyla iki kez denenir —
        #  ilki PAFTA, ikincisi PAFTA-COKLU yolunu üretmelidir.
        for adet, govde, metin, uzanti in ((1, "coklu", "PDF indir  (pafta)", ".pdf"),
                                           (1, "coklu", "XLSX indir  (şablon)", ".xlsx"),
                                           (2, "coklu", "PDF indir  (pafta)", ".pdf"),
                                           (2, "coklu", "XLSX indir  (şablon)", ".xlsx"),
                                           (0, "avan", "PDF indir", ".pdf"),
                                           (0, "avan", "XLSX indir  (şablon)", ".xlsx")):
            sekme = "trafik" if govde == "coklu" else govde
            if adet:
                adetSec(pg, adet)
            else:
                pg.click(f'.sekme[data-sekme="{sekme}"]')
            pg.wait_for_timeout(300)
            try:
                with pg.expect_download(timeout=45000) as bilgi:
                    pg.click(f'#s-{govde} button:has-text("{metin}")')
                d = bilgi.value
                ad = d.suggested_filename
                r.kontrol(f"[{sekme}/{adet or 'avan'}] '{metin}' indirdi → {ad}",
                          ad.lower().endswith(uzanti))
            except Exception as e:                       # noqa: BLE001
                r.kontrol(f"[{sekme}/{adet or 'avan'}] '{metin}' indirme", False, f"→ {e}")

        # --- proje dosyası kaydet
        pg.click('.sekme[data-sekme="proje"]')
        pg.wait_for_timeout(200)
        pg.evaluate("document.querySelector('details.proje-araclari').open = true;")
        pg.wait_for_timeout(200)
        r.kontrol("proje araçları katlanır bölümde",
                  pg.query_selector("details.proje-araclari") is not None)
        try:
            with pg.expect_download(timeout=20000) as bilgi:
                pg.click('button:has-text("Projeyi kaydet")')
            r.kontrol("proje dosyası kaydedildi",
                      bilgi.value.suggested_filename.endswith(".avan"))
        except Exception as e:                           # noqa: BLE001
            r.kontrol("proje dosyası kaydetme", False, f"→ {e}")

        # --- REVİZYON: Excel'den geri yükleme
        #     Program sıfırlanır, indirilen Excel'ler geri yüklenir,
        #     girdilerin yerine oturduğu doğrulanır.
        import json as _json
        import tempfile as _tempfile
        import urllib.request as _urlreq
        _D = _tempfile.mkdtemp(prefix="avan_arayuz_")
        _proje = {"proje_adi": "Geri Yukleme Denemesi", "muhendis": "Test"}
        _gt = {"bina_tipi": "Konut", "bina_yuksekligi": "39,98", "yapi_yuksekligi": "43",
               "N": "11", "h": "3", "hizli1": "44", "hizli2": "3", "P": "10",
               "bodrum": "2",
               "kapi_genisligi": "900", "kapi_tipi": "Merkezden Açılan Oto."}
        _ga = {"ortak": {"U": "380", "kappa": "56", "eps_max": "3", "temel_a": "26,55",
                         "temel_b": "16,4", "beta": "150", "serit_L": "58,5",
                         "cubuk_sayisi": "4", "mk_uzunluk": "0", "mk_genislik": "0"},
               "asansorler": [{"aktif": True, "tanim": "İnsan", "kapasite": "10", "V": "1.6",
                               "eta": "0,85", "Hk": "32,85", "kuyu_genisligi": "1800",
                               "kabin_boyu": "1450", "kabin_genisligi": "1300", "gr": "17,91",
                               "Fmk": "350", "Fsh": "100", "Nsc": "11", "S1": "6",
                               "L1": "32,85", "S2": "6", "L2": "3", "kablo_tipi": "NHXMH FE180",
                               "i_palanga": "1", "q_denge": "0,45"},
                              {"aktif": False}, {"aktif": False}, {"aktif": False}],
               "sabitler": {}}

        def _indir(uc, govde, ad):
            q = _urlreq.Request(BASE + "/api/indir/" + uc, data=_json.dumps(govde).encode(),
                                headers={"Content-Type": "application/json"})
            icerik = _urlreq.urlopen(q, timeout=60).read()
            yol = os.path.join(_D, ad)
            open(yol, "wb").write(icerik)
            return yol

        _tx = _indir("trafik-xlsx", {"mod": "tek", "girdiler": _gt, "proje": _proje}, "t.xlsx")
        _ax = _indir("avan-xlsx", {"girdiler": _ga, "proje": _proje}, "a.xlsx")

        pg.evaluate("localStorage.clear()")
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(1200)
        adetSec(pg, 1)
        pg.wait_for_timeout(300)
        r.esit("sıfırlandıktan sonra N boş", pg.input_value("#c_N"), "")

        pg.click('.sekme[data-sekme="proje"]')
        pg.wait_for_timeout(200)
        #  "Proje araçları" katlanır bölümü kapalı gelir — içindeki düğme ve
        #  özet alanı ancak açıkken görünür.
        pg.evaluate("document.querySelector('details.proje-araclari').open = true;")
        pg.wait_for_timeout(200)
        #  Sıfırlama kapağı da temizledi ( doğrusu bu ).  "XLSX yüklemesi
        #  kapağı silmiyor" kontrolü anlamlı olsun diye alan yeniden dolduruluyor.
        pg.fill("#k_owner", "Kalıcılık Denemesi A.Ş.")
        pg.wait_for_timeout(500)
        pg.set_input_files("#xlsx_ac", [_tx, _ax])
        pg.wait_for_timeout(3200)
        r.kontrol("yükleme özeti göründü",
                  "yüklendi" in pg.inner_text("#yukleme_ozeti"))
        #  XLSX geri yükleme HESAP GİRDİLERİNİ tazeler; proje kimliği artık
        #  kapak sekmesindedir ve dosyadan gelmez.  Kritik olan, hesap
        #  yüklemenin kapağı SİLMEMESİDİR — kullanıcı kapağı yeniden yazmak
        #  zorunda kalmamalı.
        r.esit("XLSX yüklemesi kapak alanını silmedi",
               pg.input_value("#k_owner"), "Kalıcılık Denemesi A.Ş.")
        adetSec(pg, 1)
        pg.wait_for_timeout(400)
        for alan, beklenen in (("#c_N", "11"), ("#c_hizli1", "44"), ("#c_hizli2", "3"),
                               ("#c_bina_yuksekligi", "39,98"), ("#c_P1", "10"),
                               ("#c_bodrum", "2"), ("#c_kg1", "900")):
            r.esit(f"trafik girdisi geri geldi {alan}", pg.input_value(alan), beklenen)
        r.kontrol("hesap yeniden yapıldı", "HESAP HATASI" not in pg.inner_text("#c_sonuc"))
        pg.click('.sekme[data-sekme="avan"]')
        pg.wait_for_timeout(400)
        for alan, beklenen in (("#a_kuyu_genisligi1", "1800"), ("#a_Hk1", "32,85"),
                               ("#a_kapasite1", "10"), ("#a_temel_a", "26,55"),
                               ("#a_i_palanga1", "1"), ("#a_q_denge1", "0,45")):
            r.esit(f"avan girdisi geri geldi {alan}", pg.input_value(alan), beklenen)
        r.kontrol("1. asansör etkin", pg.is_checked("#a_aktif1"))
        #  v1.5: adet trafikten gelir — trafik birden çok asansör istiyorsa
        #  eksik kart kendiliğinden açılır, tek asansör istiyorsa açılmaz.
        _taban = pg.evaluate("avanTaban()")
        r.esit("avan adedi trafik grubuyla en az eşit",
               pg.evaluate("avanAdedi() >= avanTaban()"), True)
        r.esit("2. asansör kartı trafik adedine göre",
               pg.is_checked("#a_aktif2"), _taban >= 2)
        # Açılır listelerde ondalık ayracı tuzağı: Excel "1,6" verir, seçeneğin
        # değeri "1.6"dır.  Eşleşmezse seçim boş kalır ve panel sessizce boşalır.
        r.kontrol("ondalıklı hız açılır listeye oturdu",
                  pg.input_value("#a_V1") not in ("", None),
                  f"→ {pg.input_value('#a_V1')!r}")
        r.kontrol("avan paneli hesap gösteriyor (boş kalmadı)",
                  "MOTOR GÜCÜ HESABI" in pg.inner_text("#a_sonuc"))

        # revizyon: bir girdiyi değiştir, sonuç güncellensin
        pg.fill("#a_kuyu_genisligi1", "2400")
        pg.wait_for_timeout(1200)
        _avan_metin = pg.inner_text("#a_sonuc")
        r.kontrol("revizyon sonrası avan hesabı güncellendi",
                  "2,40" in _avan_metin, "→ kuyu genişliği 2400 mm = 2,40 m görünmeli")

        # ilgisiz dosya anlaşılır hata vermeli
        # (bu adımda sunucunun 422 dönmesi BEKLENEN davranıştır — konsol
        #  denetimi bu noktadan öncesini kapsar)
        _konsol_once = len(konsol)
        _kotu = os.path.join(_D, "ilgisiz.xlsx")
        open(_kotu, "wb").write(b"PK\x03\x04 bu bir excel degil")
        pg.click('.sekme[data-sekme="proje"]')
        pg.wait_for_timeout(200)
        pg.set_input_files("#xlsx_ac", [_kotu])
        pg.wait_for_timeout(2000)
        r.kontrol("ilgisiz dosya için hata gösterildi",
                  "uyari kirmizi" in pg.inner_html("#yukleme_ozeti"))
        _yeni = [k for k in konsol[_konsol_once:] if "422" not in k]
        r.kontrol("bozuk dosya beklenmedik konsol hatası üretmedi", not _yeni, f"→ {_yeni[:3]}")
        del konsol[_konsol_once:]        # beklenen 422 kaydını temizle

        # --- dar ekran (telefon) düzeni bozulmuyor
        pg.set_viewport_size({"width": 390, "height": 844})
        pg.wait_for_timeout(600)
        tasma = pg.evaluate("document.documentElement.scrollWidth - window.innerWidth")
        r.kontrol("dar ekranda yatay taşma yok", tasma <= 2, f"→ {tasma} px taşma")

        r.kontrol("konsol hatası yok", not konsol, f"→ {konsol[:4]}")
        tarayici.close()
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
