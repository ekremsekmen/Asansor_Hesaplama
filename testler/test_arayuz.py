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

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, KOK)

from exports import xlsx_export as XE           # noqa: E402
from testler.ortak import Rapor      # noqa: E402

BASE = os.environ.get("AVAN_TEST_URL", "http://127.0.0.1:8760")


def _sunucu_var():
    try:
        urllib.request.urlopen(BASE + "/api/saglik", timeout=5).read()
        return True
    except Exception:                                    # noqa: BLE001
        return False


def uygulamayaGir(pg):
    """
    AÇILIŞ EKRANI ( 2.6 ):  program önce hangi projenin hazırlanacağını
    sorar.  Sayfa her yüklendiğinde / yenilendiğinde tekrar oraya döner,
    bu yüzden hesap ekranına geçmek için Avan Proje seçilir.
    """
    if pg.is_visible("#giris"):
        pg.click("#gk_avan")
        pg.wait_for_timeout(350)


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


def _mrl_sec(pg, mrl):
    """Makine dairesi seçimi — İKİ DÜĞMELİ görünüm.

    Alan veri modelinde hâlâ bir onay kutusudur ama ekranda iki düğmeyle
    gösterilir ve kutu görsel olarak saklanır ( .gorsel-gizli ).  Playwright
    saklı kutuya dokunamaz;  test de KULLANICI GİBİ düğmeye basar — zaten
    doğrusu budur, ekranda olmayan bir şeyi sürmek gerçek kullanımı sınamaz.
    """
    #  Düğme kapalı bir akordeonun içindeyse tıklanamaz;  gruplar açılır.
    pg.evaluate("mTumGruplariAc()")
    pg.click(f'.secim-ikili[data-icin="m_mk_yok"] .secim-dg[data-deger="{1 if mrl else 0}"]')
    pg.wait_for_timeout(300)


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

        r.kontrol("sayfa başlığı doğru", "Asansör Proje" in pg.title(),
                  f"→ {pg.title()!r}")

        # ---------------------------------------------------------------
        #  AÇILIŞ EKRANI  ( 2.6 )
        #  Program doğrudan hesap ekranına düşmez:  önce hangi projenin
        #  hazırlanacağı seçilir.  İki mod da hazırdır ve ŞERİTLERİ AYRIDIR —
        #  avan sekmeleri uygulama modunda, mukavemet sekmesi avan modunda
        #  görünmemelidir;  yoksa iki ayrı hesap birbirine karışır.
        # ---------------------------------------------------------------
        pg.on("dialog", lambda d: d.dismiss())
        r.kontrol("açılışta proje seçim ekranı görünüyor", pg.is_visible("#giris"))
        r.kontrol("açılışta hesap sekmeleri gizli",
                  not pg.is_visible('.sekme[data-sekme="avan"]'))
        r.esit("açılışta iki seçenek var",
               pg.eval_on_selector_all(".giris-kart", "e=>e.length"), 2)
        r.kontrol("avan seçeneği hazır işaretli", "HAZIR" in (pg.inner_text("#gk_avan") or ""))
        r.kontrol("uygulama projesi hazır işaretli",
                  "HAZIR" in (pg.inner_text("#gk_uygulama") or ""))

        #  --- uygulama projesi ( mukavemet ) ---
        pg.click("#gk_uygulama")
        pg.wait_for_timeout(2000)
        r.kontrol("uygulama projesi açılıyor",
                  (not pg.is_visible("#giris"))
                  and pg.is_visible('.sekme[data-sekme="mukavemet"]'))
        r.kontrol("uygulama modunda avan sekmeleri gizli",
                  not pg.is_visible('.sekme[data-sekme="avan"]')
                  and not pg.is_visible('.sekme[data-sekme="trafik"]'))
        #  Sabitler / Ofis Standardı İKİ MODA DA aittir:  elektrik ve
        #  topraklama hesapları oradaki değerleri kullanır.
        r.kontrol("uygulama modunda Sabitler sekmesi görünür",
                  pg.is_visible('.sekme[data-sekme="sabitler"]'))

        #  ── PROJE SEKMESİ / ASANSÖR SEKMELERİ
        #  Uygulama modu artık doğrudan girdi formuna düşmez.  Bir PROJE'de
        #  dörde kadar asansör olabilir;  PROJE sekmesinde binaya ait olan
        #  şeyler ( kapak · asansör adedi · proje geneli girdiler · çıktılar )
        #  BİR KEZ durur, her asansörün kendi hesabı KENDİ SEKMESİNDEDİR.
        r.kontrol("uygulama modu PROJE sekmesiyle açılıyor",
                  pg.is_visible("#s-uygproje") and not pg.is_visible("#s-mukavemet"))
        #  PROJE GENELİ ALANLAR ASANSÖR FORMUNDA, kendi grubunun içinde ve
        #  HER sekmede.  Bir süre ayrı bir karta çekilmişlerdi;  topraklamayı
        #  girmek için sekme değiştirmek gerekiyordu.  Değer TEKTİR — rozet
        #  bunu söyler, mAsansorKaydet de onları asansöre kopyalamaz.
        r.kontrol("proje geneli alanlar asansör formunda",
                  pg.evaluate("MUK.proje_geneli.every(a=>"
                              "!!document.querySelector('#m_form #'+M_ID(a)))"))
        r.esit("proje geneli alanların hepsi rozetli",
               pg.eval_on_selector_all("#m_form .pg-rozet", "e=>e.length"),
               pg.evaluate("MUK.proje_geneli.length"))
        r.kontrol("ayrı proje geneli kartı kalmadı",
                  pg.query_selector("#p_form") is None)
        r.esit("asansör adedi seçmeli  ( 1 - 4 )",
               pg.eval_on_selector_all("#m_adet option", "e=>e.map(x=>x.value)"),
               ["1", "2", "3", "4"])
        r.esit("açılışta tek asansör sekmesi",
               pg.eval_on_selector_all("#m_asansor_sekmeleri .sekme", "e=>e.length"), 1)
        #  Girdi formu asansör sekmesindedir — sonraki kontroller oradan okur.
        pg.evaluate("mAsansorSekmesi(0)")
        pg.wait_for_timeout(1200)
        r.kontrol("asansör sekmesi hesap formunu açıyor",
                  pg.is_visible("#s-mukavemet") and not pg.is_visible("#s-uygproje"))
        #  FORMUN BAŞINDAKİ AÇIKLAMA KUTULARI KALDIRILDI.  Ortak girdi
        #  köprüsü ve "bu bölüm uygulama projesine aittir" metni her açılışta
        #  girdilerin önünü kapatıyordu;  köprü zaten görünmez çalışıyor.
        #  Excel hücre adresleri de ( "· B132" ) etiketten çıkarıldı — Excel
        #  eşleşmesi SÖZLEŞMEDE duruyor, TEST 6 onu ayrıca doğruluyor.
        r.kontrol("form açıklama kutusuyla başlamıyor",
                  "Ortak girdiler bir kez girilir" not in pg.inner_text("#m_form")
                  and "uygulama projesine" not in pg.inner_text("#m_form"))
        r.esit("etiketlerde Excel hücre adresi yok",
               pg.eval_on_selector_all(
                   "#m_form label",
                   "e=>e.filter(x=>/·\\s*[A-Z]{1,2}[0-9]{1,4}\\b/.test(x.textContent))"
                   ".map(x=>x.textContent.trim())"), [])
        r.kontrol("başlık uygulama projesini gösteriyor",
                  "UYGULAMA" in pg.inner_text("#ust_ad"),
                  f"→ {pg.inner_text('#ust_ad')!r}")
        #  GRUP SAYISI MOTORDAN OKUNUR.  Çivili sayı, forma bir grup
        #  eklendiğinde ( "Makine yerleşimi" ) sessizce eskiyordu.
        from engine.uygulama import girdi as _UGrp
        _grup_sayisi = len(_UGrp.arayuz_alanlari()["gruplar"])
        r.esit(f"uygulama formu {_grup_sayisi} grup üretti",
               pg.eval_on_selector_all("#m_form .m-grup", "e=>e.length"),
               _grup_sayisi)

        #  ── GİRDİ AKORDEONU  ( 86 girdi tek sütunda bulunamıyordu )
        #  Kapalı grup DOM'da KALIR;  yalnız görünmez.  Hesabın okuduğu alan
        #  kümesi açık/kapalı durumdan ETKİLENMEMELİ — asıl kontrol budur.
        r.esit("akordeon: tek grup açık başlıyor",
               pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length"), 1)
        _ga = pg.evaluate("Object.keys(mukavemetGirdi()).length")
        pg.evaluate("mGrupAc(6)")
        _gb = pg.evaluate("Object.keys(mukavemetGirdi()).length")
        pg.evaluate("document.getElementById('m_ara').value='halat';mAramaUygula()")
        _gc = pg.evaluate("Object.keys(mukavemetGirdi()).length")
        _bulunan = pg.eval_on_selector_all(
            "#m_form .alan", "e=>e.filter(x=>!x.hidden).length")
        pg.evaluate("document.getElementById('m_ara').value='';mAramaUygula()")
        _gd = pg.evaluate("Object.keys(mukavemetGirdi()).length")
        r.kontrol("akordeon: okunan girdi kümesi HİÇ değişmiyor",
                  len({_ga, _gb, _gc, _gd}) == 1,
                  f"→ {_ga} · {_gb} · {_gc} · {_gd}")
        r.kontrol("akordeon: arama alanları süzüyor",
                  0 < _bulunan < _ga, f"→ {_bulunan} alan kaldı")
        r.kontrol("akordeon: arama temizlenince sayaçlar geri geliyor",
                  pg.eval_on_selector_all(
                      "#m_form .m-grup-adet",
                      "e=>e.every(x=>x.textContent.trim()===x.dataset.toplam)"),
                  "→ arama sayaçları başlıkta kaldı")
        #  SONUÇTAN GİRDİYE ATLAMA — eşleme motordan gelir ( BOLUM_GRUBU ).
        #  Bir hesap bölümü İKİ girdi grubundan beslenebilir ve kalan
        #  kontrolün alanı ikincisinde olabilir:  4. bölüm "tahrik kasnağı
        #  çapını büyütün" der ama Dt alanı MAKİNE VE MOTOR grubundadır,
        #  10. bölümün kuyu dibi sığınma yüksekliği ise TAMPONLAR'daki baba
        #  yüksekliğinden gelir.  Eskiden tek grup açılıyordu ve mühendis
        #  aradığı alanı açılan grupta bulamıyordu.
        #  ANAHTAR BÖLÜMÜN KİMLİĞİDİR, NUMARASI DEĞİL:  numara projeye göre
        #  kayıyor ve proje geneli bölümler hiç eşlenemiyordu.
        for _k in ("motor_gucu", "makine_konstruksiyonu", "aski_halatlari",
                   "kabin_raylari", "siginma_alanlari", "kabin_aydinlatma",
                   "kuyu_aydinlatma", "gerilim_dusumu"):
            pg.evaluate(f"mGirdiyeGit('{_k}')")
            r.esit(f"bölüm {_k} → girdi grupları",
                   sorted(pg.eval_on_selector_all(
                       "#m_form .m-grup.acik", "e=>e.map(x=>x.dataset.ad)")),
                   sorted(pg.evaluate(f"mBolumGruplari('{_k}')")))
        #  Sonuç satırı kimliği taşımalı — numaradan ayıklamıyoruz artık
        r.kontrol("sonuç bölümleri kimlik taşıyor",
                  pg.evaluate("SON.m.bolumler.every(b=>!!b.kimlik)"),
                  f"→ {pg.evaluate('SON.m.bolumler.map(b=>b.kimlik)')}")
        r.esit("aynı bölüm numarası kaysa da kimliği duruyor",
               pg.evaluate("SON.m.bolumler.map(b=>b.kimlik)")[:4],
               ["motor_gucu", "makine_konstruksiyonu", "kabin_alani",
                "aski_halatlari"])
        pg.evaluate("mGirdiyeGit('aski_halatlari')")
        r.kontrol("halat bölümü hem halatı hem tahrik kasnağını açıyor",
                  pg.is_visible("#m_halat_capi")
                  and pg.is_visible("#m_tahrik_kasnak_capi"))
        pg.evaluate("mGirdiyeGit('siginma_alanlari')")
        r.kontrol("sığınma bölümü hem kuyuyu hem tampon babasını açıyor",
                  pg.is_visible("#m_son_kat_yuksekligi")
                  and pg.is_visible("#m_kabin_tampon_baba"))
        #  ÜÇ GRUP AÇILMAZ — akordeon listeye dönerse aranan alan yine kaybolur
        r.esit("atlama en çok iki grup açıyor",
               pg.evaluate("Math.max(...Object.values(MUK.bolum_grubu)"
                           ".map(v=>v.length))"), 2)
        #  Öteki gruplar KAPANIR:  atlama akordeonu açık bırakmaz
        r.esit("atlamadan sonra yalnız eşlemedeki gruplar açık",
               pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length"),
               len(pg.evaluate("mBolumGruplari('siginma_alanlari')")))
        #  BAŞLIK AÇ/KAPADIR.  Açık gruba yeniden tıklamak eskiden hiçbir şey
        #  yapmıyordu — grup bir açıldı mı kapanmıyordu.
        pg.evaluate("mGrupAc(5)")
        _ac1 = pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length")
        pg.click('#m_form .m-grup[data-grup="5"] .m-grup-bas')
        pg.wait_for_timeout(300)
        _ac2 = pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length")
        pg.click('#m_form .m-grup[data-grup="5"] .m-grup-bas')
        pg.wait_for_timeout(300)
        _ac3 = pg.eval_on_selector_all("#m_form .m-grup.acik", "e=>e.length")
        r.esit("başlığa tıklamak grubu açıp kapatıyor", [_ac1, _ac2, _ac3], [1, 0, 1])
        #  Kapalıyken de okunan girdi kümesi AYNI kalmalı  ( görünüm ≠ hesap )
        pg.evaluate("mGruplariKapat()")
        r.esit("hepsi kapalıyken okunan girdi kümesi değişmiyor",
               pg.evaluate("Object.keys(mukavemetGirdi()).length"), _ga)
        #  BÖLÜMLERİN HEPSİ TIKLANABİLİR.  Elektrik bölümleri bir süre
        #  eşlemede yoktu:  mukavemet satırları girdisine götürüyor,
        #  aydınlatma ve gerilim düşümü satırları ölü duruyordu.
        #  SAYI ELLE YAZILMAZ — motora bölüm eklenince ( ör. TAMPONLAR )
        #  test kendiliğinden takip etsin;  aranan şey "hepsi gidilebilir".
        _satir = pg.eval_on_selector_all(
            "#m_sonuc tr.m-gidilir td.etiket",
            "e=>e.map(x=>x.textContent.trim().split(' ')[0])")
        r.esit("sonuç tablosunda bölüm satırlarının hepsi tıklanabilir",
               _satir,
               [str(_i) for _i in
                range(1, pg.evaluate("SON.m.bolumler.length") + 1)])

        #  ── ÇOKLU ASANSÖR  ( 1 - 4 asansör, tek proje )
        #  Asansör adedi SEÇİLİR ( ekle/sil değil ):  bir binada kaç asansör
        #  olduğu baştan bellidir, mühendis onu sayar — sırayla ekleyip
        #  silmez.  Form TEK KOPYADIR;  aktif asansörün değerleri onda durur.
        #  Asansör değişince değerler kaybolmamalı — asıl kontrol budur.
        #  Denemede BAĞIMSIZ bir alan kullanılır:  seyir mesafesi ve son kat
        #  yüksekliği durak listesinden TÜRETİLİR ( mTuretilenleriDoldur ),
        #  asansör değişince yeniden hesaplanırlar — taşınmadıkları için
        #  değil, türetildikleri için.
        r.esit("çoklu: açılışta tek asansör", pg.evaluate("MUK_ADET"), 1)
        pg.evaluate("mTumGruplariAc()")
        pg.fill("#m_asansor_adi", "İnsan 1")
        pg.fill("#m_motor_gucu", "7.5")
        pg.evaluate("mAdetDegisti(2)")
        pg.wait_for_timeout(1400)
        r.esit("çoklu: adet 2 seçildi", pg.evaluate("MUK_ADET"), 2)
        r.esit("çoklu: şeritte iki asansör sekmesi",
               pg.eval_on_selector_all("#m_asansor_sekmeleri .sekme", "e=>e.length"), 2)
        #  Adet seçmek AKTİF ASANSÖRÜ DEĞİŞTİRMEZ — mühendis 1'i doldururken
        #  adedi 3 yapınca formu altından çekilmiş olmaz.
        r.esit("çoklu: adet seçimi aktif asansörü değiştirmiyor",
               pg.evaluate("MUK_AKTIF"), 0)
        r.kontrol("çoklu: 1. asansörün değerleri yerinde",
                  pg.input_value("#m_asansor_adi") == "İnsan 1")
        pg.evaluate("mAsansorSekmesi(1)")
        pg.wait_for_timeout(1400)
        r.esit("çoklu: sekmeyle 2. asansöre geçiliyor", pg.evaluate("MUK_AKTIF"), 1)
        r.kontrol("çoklu: yeni asansör 1 nolunun kopyası olarak açılıyor",
                  pg.input_value("#m_motor_gucu") == "7.5",
                  f"→ {pg.input_value('#m_motor_gucu')!r}")
        r.esit("çoklu: kopyanın adı boş", pg.input_value("#m_asansor_adi"), "")
        pg.evaluate("mTumGruplariAc()")
        pg.fill("#m_asansor_adi", "Yük")
        pg.fill("#m_motor_gucu", "15")
        pg.evaluate("mAsansorSec(0)")
        pg.wait_for_timeout(1400)
        r.kontrol("çoklu: 1. asansöre dönünce KENDİ değerleri geliyor",
                  pg.input_value("#m_asansor_adi") == "İnsan 1"
                  and pg.input_value("#m_motor_gucu") == "7.5",
                  f"→ {pg.input_value('#m_asansor_adi')!r} · "
                  f"{pg.input_value('#m_motor_gucu')!r}")
        pg.evaluate("mAsansorSec(1)")
        pg.wait_for_timeout(1400)
        r.kontrol("çoklu: 2. asansörün değerleri korunmuş",
                  pg.input_value("#m_asansor_adi") == "Yük"
                  and pg.input_value("#m_motor_gucu") == "15")
        #  Hesap İKİ asansörü birden döner ve özet tablosu çizilir
        pg.evaluate("hesapMukavemet()")
        pg.wait_for_timeout(2200)
        r.esit("çoklu: sunucu iki asansör hesapladı",
               pg.evaluate("SON.mc && SON.mc.adet"), 2)
        r.kontrol("çoklu: SON.m aktif asansörün sonucu  ( geriye dönük )",
                  pg.evaluate("!!(SON.m && SON.m.bolumler && SON.m.bolumler.length)"))
        r.esit("çoklu: özet iki asansörü listeliyor",
               pg.evaluate("SON.mc.ozet.asansorler.length"), 2)
        r.esit("çoklu: özetteki adlar",
               pg.evaluate("SON.mc.ozet.asansorler.map(a=>a.tanim)"),
               ["İnsan 1", "Yük"])
        #  ASANSÖR LİSTESİ YALNIZ PROJE SEKMESİNDE.  Bir süre her asansörün
        #  sonuç panelinin başına da basılıyordu;  ASANSÖR 2 sekmesinde "1 · 2"
        #  listesi görmek, o sekmenin zaten 2 nolu asansöre ait olduğunu bile
        #  bile tekrar söylemekti — hangi sekmede olunduğu üstteki şeritte yazılı.
        r.kontrol("asansör listesi hesap sayfasında YOK",
                  "ASANSÖRLER" not in pg.inner_text("#m_sonuc"))
        r.esit("hesap panelinin ilk şeridi bölüm sonuçları",
               pg.eval_on_selector("#m_sonuc .serit span", "e=>e.textContent.trim()"),
               "BÖLÜM SONUÇLARI")
        r.kontrol("asansör listesi PROJE sekmesinde duruyor",
                  "PROJE ÖZETİ" in pg.inner_text("#p_ozet"),
                  f"→ {pg.inner_text('#p_ozet')[:60]!r}")
        r.esit("proje özeti iki asansörü listeliyor",
               pg.eval_on_selector_all("#p_ozet table tr", "e=>e.length"), 3)
        #  ── KARŞI AĞIRLIĞIN ÖLÇÜLERİ  ( TS EN 81-50 Ek C.2.2 · Gx · Gy )
        #  Eskiden ikisi de türetiliyordu:  genişlik RAY ARASINDAN ( üç
        #  değere kilitli açılır liste ), derinlik MALZEMEDEN.  Standart
        #  karşı ağırlığın KENDİ ölçülerini veri olarak ister;  türetme
        #  kaldırıldı.  Malzeme seçimi artık yalnız kutuyu DOLDURUR — hesap
        #  her hâlükârda kutudaki sayıyı okur.
        pg.evaluate("mTumGruplariAc()")
        r.esit("ray arası serbest kutu",
               pg.eval_on_selector("#m_agirlik_ray_arasi", "e=>e.tagName"), "INPUT")
        r.kontrol("karşı ağırlık ölçüleri formda",
                  pg.eval_on_selector_all("#m_agirlik_genisligi", "e=>e.length") == 1
                  and pg.eval_on_selector_all("#m_agirlik_derinligi", "e=>e.length") == 1)
        pg.select_option("#m_agirlik_malzemesi", "Pik Döküm")
        pg.wait_for_timeout(1800)
        r.esit("malzeme seçimi derinlik kutusunu dolduruyor",
               pg.input_value("#m_agirlik_derinligi"), "100")
        r.esit("hesap kutudaki derinliği kullanıyor",
               pg.evaluate("SON.m.girdi.agirlik_derinligi"), 100)
        pg.fill("#m_agirlik_derinligi", "180")
        pg.wait_for_timeout(1800)
        r.esit("elle girilen ölçü tabloyu eziyor",
               pg.evaluate("SON.m.girdi.agirlik_derinligi"), 180)
        #  Tablo dışı bir ray arası artık hesabı ETKİLEMEZ ve UYARI ÜRETMEZ
        _once = pg.evaluate("SON.m.bolumler.find(b=>b.kimlik==='agirlik_raylari')"
                            ".adimlar.map(a=>a.deger)")
        pg.fill("#m_agirlik_ray_arasi", "1234")
        pg.wait_for_timeout(1800)
        _sonra = pg.evaluate("SON.m.bolumler.find(b=>b.kimlik==='agirlik_raylari')"
                             ".adimlar.map(a=>a.deger)")
        r.esit("ray arası ray gerilmesini değiştirmiyor",
               [x for x in _once if x != 1050], [x for x in _sonra if x != 1234])
        #  TEMİZLİK — sonraki kontrolleri bozmasın
        pg.select_option("#m_agirlik_malzemesi", "Barit")
        pg.wait_for_timeout(600)
        pg.fill("#m_agirlik_ray_arasi", "1050")
        pg.fill("#m_agirlik_genisligi", "960")
        pg.wait_for_timeout(1800)

        #  ── FORM ALANLARININ TEK GEZİNTİSİ
        #  "Alan nedir, nasıl okunur, nasıl yazılır" bilgisi BİR YERDE
        #  durmalı.  Bir süre aynı gezinti beş ayrı yerde elle yazılıydı ve
        #  hepsi "checkbox ise checked, değilse value" kuralının kendi
        #  kopyasını taşıyordu:  yeni bir alan türü eklendiğinde birinde
        #  unutulur ve asansör değiştirince o alan SESSİZCE kaybolurdu.
        #  Ayrıca ikisi ayrışmıştı — kovadan geri yükleme alanaYaz()
        #  kullanıyor ( seçim kutusunda "6.5" ile "6,5"i eşleştirir ),
        #  asansör yükleme ise ham `e.value =` yapıyordu.
        _js = open(os.path.join(KOK, "static", "uygulama.js"),
                   encoding="utf-8").read()
        for _fn in ("mukavemetGirdi", "mAsansorKaydet", "mAsansorYukle",
                    "mukavemetIstek"):
            _bas = _js.index(f"function {_fn}(")
            _govde = _js[_bas:_js.index("\n}\n", _bas)]
            r.kontrol(f"{_fn} okuma/yazma kuralını KENDİ kopyasında taşımıyor",
                      "checkbox" not in _govde, f"→ {_fn} hâlâ elle okuyor")
        for _yardimci in ("mAlanlar", "mAlanOku", "mAlanYaz",
                          "mFormOku", "mFormaYaz"):
            r.kontrol(f"ortak yardımcı var: {_yardimci}",
                      pg.evaluate(f"typeof {_yardimci} === 'function'"))
        #  KAYDEDİLEN küme = OKUNAN küme − durak listesi − proje geneli.
        #  İkisi ayrışırsa asansör değiştirince alan sessizce kaybolur.
        r.esit("kaydedilen ve okunan alan kümeleri tutarlı",
               pg.evaluate("""() => {
                   mAsansorKaydet();
                   const tum = Object.keys(mukavemetGirdi());
                   const kayit = Object.keys(MUK_ASANSORLER[MUK_AKTIF])
                                       .filter(k => k[0] !== '_');
                   const liste = mAlanlar(f => f.tur === 'liste')
                                       .map(f => f.anahtar);
                   const bek = tum.filter(k => !liste.includes(k)
                                               && !mProjeGeneliMi(k));
                   return {eksik: bek.filter(k => !kayit.includes(k)),
                           fazla: kayit.filter(k => !bek.includes(k))};
               }"""), {"eksik": [], "fazla": []})
        #  SEÇİM KUTUSU asansörler arasında korunuyor mu — ham `e.value =`
        #  ile yazılırken seçenekle birebir eşleşmeyen değer sessizce düşerdi.
        pg.evaluate("mTumGruplariAc()")
        pg.select_option("#m_halat_capi", "8")
        pg.select_option("#m_makine_tipi", "Dişli")
        pg.evaluate("mAsansorSec(0)")
        pg.wait_for_timeout(1400)
        pg.evaluate("mAsansorSec(1)")
        pg.wait_for_timeout(1400)
        r.esit("seçim kutuları asansör değişince korunuyor",
               [pg.input_value("#m_halat_capi"), pg.input_value("#m_makine_tipi")],
               ["8", "Dişli"])
        pg.evaluate("mTumGruplariAc()")
        pg.select_option("#m_halat_capi", "6,5")
        pg.select_option("#m_makine_tipi", "Dişlisiz")
        pg.wait_for_timeout(1200)

        #  PROJE GENELİ HESAPLAR:  girdi asansör formunda, SONUÇ PROJE
        #  sekmesinde ve paftanın en sonunda — asansör sekmelerinde
        #  tekrarlanmaz.  Makine dairesi ve temel girilince bölümler doğar.
        pg.evaluate("mTumGruplariAc()")
        _mrl_sec(pg, False)
        for _a, _d in (("m_mk_uzunluk", "4"), ("m_mk_genislik", "3"),
                       ("m_temel_a", "20"), ("m_temel_b", "12"),
                       ("m_serit_L", "64")):
            pg.fill(f"#{_a}", _d)
        pg.wait_for_timeout(2500)
        r.esit("proje geneli bölümler üst seviyede",
               pg.evaluate("(SON.mc.proje_geneli||[]).length"), 4)
        r.esit("proje geneli bölüm hiçbir asansörde kalmıyor",
               pg.evaluate("SON.mc.asansorler.map(a=>a.bolumler.filter("
                           "b=>b.proje_geneli).length)"), [0, 0])
        r.kontrol("proje geneli hesaplar asansörün bölüm listesinde YOK",
                  "TOPRAKLAYICI" not in pg.inner_text("#m_sonuc"))
        #  BLOK ASANSÖR SEKMESİNDEDİR, Proje sayfasında değil:  girdileri
        #  ( MRL · temel ölçüleri · şerit boyu ) da bu sekmede duruyor.
        r.kontrol("proje geneli hesaplar kendi bloğunda",
                  "TOPRAKLAYICI" in pg.inner_text("#p_geneli")
                  and "PROJE GENELİ HESAPLAR" in pg.inner_text("#p_geneli"))
        r.esit("proje geneli bloğu asansör sayfasında",
               pg.eval_on_selector("#p_geneli", "e=>e.closest('section').id"),
               "s-mukavemet")
        #  MRL İŞARETLİYKEN MAKİNE DAİRESİ ÖLÇÜLERİ GİZLENİR.  Ortada duran
        #  ve doldurulabilen kutular "hesap yapılacak" izlenimi veriyordu.
        _gor = ("e=>{const a=e.closest('.alan')||e;"
                " return !(a.hidden||getComputedStyle(a).display==='none');}")
        r.kontrol("MRL kaldırılınca makine dairesi ölçüleri görünür",
                  pg.eval_on_selector("#m_mk_uzunluk", _gor))
        _mrl_sec(pg, True)
        pg.wait_for_timeout(1800)
        r.kontrol("MRL işaretlenince makine dairesi ölçüleri gizlenir",
                  not pg.eval_on_selector("#m_mk_uzunluk", _gor))
        r.kontrol("MRL'de makine dairesi bölümü hesaba girmiyor",
                  pg.evaluate("(SON.mc.proje_geneli||[]).every("
                              "b=>b.baslik.indexOf('MAKİNE DAİRESİ')<0)"),
                  f"→ {pg.evaluate('(SON.mc.proje_geneli||[]).map(b=>b.baslik)')}")
        #  MAKİNE YÜKÜNÜN YOLU YALNIZ MRL'DE SORULUR  ( TS EN 81-20 m.5.7.2.3.7 ).
        #  Makine dairesi varsa makine kendi kaidesindedir;  aynı yükü raya da
        #  bindirmek onu iki kez saymak olur.
        r.kontrol("MRL'de makine yükü yolu soruluyor",
                  pg.eval_on_selector("#m_makine_raya_biniyor", _gor)
                  and pg.eval_on_selector("#m_raya_binen_yuk", _gor))
        _mrl_sec(pg, False)
        pg.wait_for_timeout(1800)
        r.kontrol("makine dairesi varken makine yükü yolu SORULMUYOR",
                  not pg.eval_on_selector("#m_makine_raya_biniyor", _gor)
                  and not pg.eval_on_selector("#m_raya_binen_yuk", _gor))
        #  KURAL GİZLEMESİ ARAMA SÜZGECİYLE KAVGA ETMEMELİ.
        #  mTumGruplariAc() ve mAramaUygula() [hidden] üzerinde çalışır;  kural
        #  gizlemesi aynı niteliği kullanırsa grupları açmak gizlenen alanı
        #  GERİ GETİRİYORDU — bu, mk_uzunluk için de geçerli eski bir hataydı.
        pg.evaluate("mTumGruplariAc()")
        pg.wait_for_timeout(900)
        r.kontrol("tüm grupları aç, kural gizlemesini BOZMUYOR",
                  not pg.eval_on_selector("#m_makine_raya_biniyor", _gor),
                  "→ mTumGruplariAc() gizli alanı geri getirdi")
        pg.fill("#m_ara", "makine")
        pg.wait_for_timeout(900)
        r.kontrol("arama süzgeci de kural gizlemesini bozmuyor",
                  not pg.eval_on_selector("#m_makine_raya_biniyor", _gor))
        pg.fill("#m_ara", "")
        pg.wait_for_timeout(900)
        #  Arama temizlenince YALNIZ son seçili grup açık kalır;  kutuya
        #  ulaşabilmek için gruplar yeniden açılır.
        pg.evaluate("mTumGruplariAc()")
        pg.wait_for_timeout(600)
        _mrl_sec(pg, True)
        pg.wait_for_timeout(1500)
        pg.evaluate("mTumGruplariAc()")
        pg.wait_for_timeout(900)
        r.kontrol("MRL'de tüm grupları aç, ölçüleri geri getirmiyor",
                  not pg.eval_on_selector("#m_mk_uzunluk", _gor))
        #  İKİ DÜĞMELİ SEÇİM:  düğme, alttaki kutuyu ve hesabı sürmeli.
        r.kontrol("MRL düğmesi seçili görünüyor",
                  pg.eval_on_selector(
                      '.secim-ikili[data-icin="m_mk_yok"] .secim-dg[data-deger="1"]',
                      "e=>e.classList.contains('secili')"))
        r.kontrol("düğme alttaki onay kutusunu sürüyor",
                  pg.evaluate("document.getElementById('m_mk_yok').checked"))
        #  SEÇİM KUTUSU BOŞA DÜŞMEZ.  Listede olmayan bir değer yazılırsa
        #  ( eski proje dosyası · tablodan kalkan profil ) varsayılan korunur;
        #  boşalan bir <select> "" gönderip motoru "boş bırakılamaz" dedirtiyordu.
        _onceki = pg.input_value("#m_makine_raya_biniyor")
        pg.evaluate("alanaYaz(document.getElementById('m_makine_raya_biniyor'),"
                    " 'artik-olmayan-bir-secenek')")
        r.esit("listede olmayan değer seçim kutusunu BOŞALTMIYOR",
               pg.input_value("#m_makine_raya_biniyor"), _onceki)
        _mrl_sec(pg, False)
        pg.wait_for_timeout(1800)
        #  Girdi hangi asansör sekmesinde yazılırsa yazılsın TEK değerdir
        pg.evaluate("mAsansorSec(0)")
        pg.wait_for_timeout(1600)
        r.esit("proje geneli girdi asansör değişince duruyor",
               pg.input_value("#m_temel_a"), "20")
        pg.evaluate("mAsansorSec(1)")
        pg.wait_for_timeout(1600)
        #  Temizlik — sonraki koşuyu bozmasın
        pg.evaluate("mTumGruplariAc()")
        #  ÖNCE ölçüler boşaltılır, SONRA MRL işaretlenir:  MRL işaretliyken
        #  makine dairesi kutuları gizlenir ve doldurulamaz.
        for _a in ("m_mk_uzunluk", "m_mk_genislik", "m_temel_a",
                   "m_temel_b", "m_serit_L"):
            pg.fill(f"#{_a}", "")
        _mrl_sec(pg, True)
        pg.wait_for_timeout(2000)
        #  HER ASANSÖR KENDİ GİRDİSİYLE hesaplanır:  sonuçta girdi de dönüyor,
        #  aktif asansörün girdisi ikisine birden gönderilmiş olsa iki motor
        #  gücü aynı görünürdü.
        r.esit("çoklu: her asansör KENDİ girdisiyle hesaplandı",
               pg.evaluate("SON.mc.asansorler.map(a=>a.girdi.motor_gucu)"),
               [7.5, 15.0])
        #  Sekme rozeti ASANSÖRE ÖZELDİR — dördünde aynı rozet çıkmamalı
        r.esit("çoklu: her sekme kendi rozetini taşıyor",
               pg.eval_on_selector_all(
                   "#m_asansor_sekmeleri .sekme",
                   "e=>e.map(x=>x.textContent.trim().slice(0,9))"),
               ["ASANSÖR 1", "ASANSÖR 2"])
        #  PROJE GENELİ alanlar asansörden asansöre TAŞINMAZ
        r.kontrol("çoklu: proje geneli alanlar asansör haritasında yok",
                  pg.evaluate("MUK.proje_geneli.every(a=>"
                              "MUK_ASANSORLER.every(d=>!(a in d)))"),
                  "→ topraklama/makine dairesi asansöre kopyalanmış")
        #  ADEDİ AZALTMAK VERİYİ SİLMEZ:  3→2→3 yapan mühendis girdilerini
        #  geri bulmalı.  Harita dizide kalır, yalnız hesaba girmez.
        pg.evaluate("mAdetDegisti(1)")
        pg.wait_for_timeout(1400)
        r.esit("çoklu: adet 1'e indi", pg.evaluate("MUK_ADET"), 1)
        r.esit("çoklu: tek asansör sekmesi kaldı",
               pg.eval_on_selector_all("#m_asansor_sekmeleri .sekme", "e=>e.length"), 1)
        r.esit("çoklu: azaltmak 2. asansörün verisini SİLMİYOR",
               pg.evaluate("(MUK_ASANSORLER[1]||{}).asansor_adi"), "Yük")
        r.esit("çoklu: hesap yalnız seçilen adedi kapsıyor",
               pg.evaluate("SON.mc && SON.mc.adet"), 1)
        pg.evaluate("mAdetDegisti(2)")
        pg.wait_for_timeout(1400)
        r.esit("çoklu: geri artırınca eski girdi geliyor",
               pg.evaluate("SON.mc.ozet.asansorler.map(a=>a.tanim)"), ["İnsan 1", "Yük"])
        #  TEMİZLİK.  Girdiler tarayıcıda saklanıyor ve testler arasında
        #  silinmiyor;  bu blok motor gücünü değiştirdiği için bırakıldığı
        #  gibi kalırsa BİR SONRAKİ KOŞUDA daha erken bir kontrolü
        #  ( "varsayılanda üç bölüm kalıyor" ) bozar.  Dokunulan alanlar
        #  varsayılanına döndürülür ve ikinci asansör atılır.
        pg.evaluate("mAdetDegisti(1); MUK_ASANSORLER = [{}]; MUK_AKTIF = 0;")
        pg.wait_for_timeout(1200)
        pg.evaluate("mTumGruplariAc()")
        pg.fill("#m_motor_gucu", "4,9")
        pg.fill("#m_asansor_adi", "")
        pg.evaluate("mAsansorKaydet(); yaz()")
        pg.wait_for_timeout(700)
        r.esit("varsayılan durak sayısı", pg.evaluate("MUK_DURAK.length"), 8)

        #  DURAK DÜĞMELERİ ALTTAKİ ALANIN ÜSTÜNE TAŞMAMALI.
        #  Bir kez taştılar:  trafikteki 31×29 px SABİT KARE ".adet-dg"
        #  sınıfıyla yazılmışlardı, uzun Türkçe metin kutuya sığmayıp
        #  "Son kat yüksekliği" etiketinin üzerine biniyordu.  Ölçü hem geniş
        #  hem dar ekranda alınır — dar ekranda düğmeler alt alta sarar.
        for _ad, _en in (("geniş ekran", 1440), ("dar ekran", 380)):
            pg.set_viewport_size({"width": _en, "height": 950})
            pg.wait_for_timeout(400)
            _o = pg.evaluate("""() => {
                const q = id => document.getElementById(id);
                const kutu = e => e.getBoundingClientRect();
                const ekle = q('m_durak_ekle'), sil = q('m_durak_sil');
                const et = [...document.querySelectorAll('#m_form label')]
                    .find(l => l.textContent.includes('Son kat yüksekliği'));
                const alt = Math.max(kutu(ekle).bottom, kutu(sil).bottom);
                return {bosluk: Math.round(kutu(et).top - alt),
                        tasan: ekle.scrollWidth > ekle.clientWidth + 1
                            || sil.scrollWidth > sil.clientWidth + 1,
                        yukseklik: Math.round(kutu(ekle).height),
                        genislik: Math.round(kutu(ekle).width)};
            }""")
            r.kontrol(f"durak düğmeleri alttaki alana taşmıyor ( {_ad} )",
                      _o["bosluk"] >= 0, f"→ {_o['bosluk']} px örtüşme")
            r.kontrol(f"durak düğmesi metni kutusuna sığıyor ( {_ad} )",
                      not _o["tasan"], f"→ {_o}")
            r.kontrol(f"durak düğmesi tek satır ( {_ad} )",
                      _o["yukseklik"] <= 42, f"→ {_o['yukseklik']} px yüksek")
        pg.set_viewport_size({"width": 1440, "height": 1000})
        pg.wait_for_timeout(400)
        #  VARSAYILAN PROJE İKİ BÖLÜMDEN KALIR — ikisi de kaynak kitabın
        #  gizlediği gerçek yetersizliklerdir:
        #    · ASKI HALATLARI — TS EN 81-20 m.5.5.2.1 kasnak/halat oranını en
        #      az 40 ister, örnekte 240 / 6,5 = 36,9  ( sapma ① ).
        #    · MOTOR GÜCÜ — verim makine tipine bağlı;  dişlisiz + 2:1'de
        #      η′ = 0,75 → 5,90 kW gerekir, seçilen motor 4,9 kW  ( sapma ⑨ ).
        #  Beklenen davranış budur.
        r.kontrol("uygulama hesabı koştu", pg.evaluate("SON.m && SON.m.aktif"),
                  f"→ {pg.evaluate('SON.m && SON.m.hata')}")
        #    · HIZ REGÜLATÖRÜ — m.5.6.2.2.1.1 d)'nin ikinci sınırı imalatçının
        #      "devreye sokma kuvveti"ni ister;  kitabın örneğinde yoktur, o
        #      yüzden madde denetlenemez ve bölüm HESAP EKSİK der ( sapma ⑲ ).
        _kalan = pg.evaluate("SON.m.bolumler.filter(b=>b.sonuc && "
                             "b.sonuc.uygun===false).map(b=>b.baslik)")
        #    · TAHRİK YETENEĞİ — acil frenlemede ivme işaretleri Ek D'ye göre
        #      düzeltilince ( sapma ㊳ ) oran %36 büyüdü;  kitabın örneği
        #      139°'lik sarılma ve sertleştirilmemiş kanalla sınırı aşıyor.
        r.esit("varsayılanda dört bölüm kalıyor", len(_kalan), 4)
        r.kontrol("kalanlar motor gücü, askı halatları, regülatör ve tahrik",
                  sorted(x[:1] for x in _kalan) == ["1", "4", "5", "6"], f"→ {_kalan}")
        #  GİRDİ AKORDEONU.  Alanlar artık gruplara ayrıldı ve kapalı gruptaki
        #  alan "görünür değil" sayılır — Playwright dolduramaz.  Test alanları
        #  id ile doldurduğu için bütün grupları açıyoruz;  akordeonun kendi
        #  davranışı aşağıda ayrıca denetleniyor.
        pg.evaluate("mTumGruplariAc()")
        #  Üçü de giderilince hepsi geçmeli
        pg.fill("#m_tahrik_kasnak_capi", "280")
        pg.fill("#m_saptirma_kasnak_capi", "280")
        pg.fill("#m_motor_gucu", "7.5")
        pg.fill("#m_guvenlik_devreye_kuvvet", "200")
        #  Tahrik için iki bileşen bilgisi daha:  sertleştirilmiş kanal
        #  ( f = μ / sin(γ/2) ) ve denge zinciri.
        pg.select_option("#m_kanal_isleme", "Sertleştirilmiş")
        pg.select_option("#m_denge_zinciri", "Var")
        pg.wait_for_timeout(1500)
        r.kontrol("kasnak 280 mm · motor 7,5 kW · imalatçı kuvveti · "
                  "sertleştirilmiş kanal · denge zinciri girilince "
                  "bütün bölümler uygun",
                  pg.evaluate("SON.m.ozet.tumu_uygun === true"),
                  f"→ {pg.evaluate('SON.m.bolumler.filter(b=>b.sonuc && b.sonuc.uygun===false).map(b=>b.baslik)')}")
        r.esit("on dört hesap bölümü çizildi",
               pg.eval_on_selector_all("#m_sonuc .serit", "e=>e.length") >= 14, True)
        #  Ekranda gerçekten SAYI var mı — boş tablo "geçti" sayılmasın.
        #  Sayı ELLE yazılmaz:  hesap değişince test sessizce eskiyor.
        _ng = pg.evaluate("SON.m.ozet.N_hesap").__format__(".2f").replace(".", ",")
        r.kontrol(f"motor gücü ekrana yazıldı  ( {_ng} )",
                  _ng in pg.inner_text("#m_sonuc"),
                  f"→ {pg.inner_text('#m_sonuc')[:120]!r}")
        #  Makine tipi seçimi ekranda gerçekten hesabı değiştiriyor mu
        pg.select_option("#m_makine_tipi", "Dişli")
        pg.wait_for_timeout(1400)
        _nd = pg.evaluate("SON.m.ozet.N_hesap")
        pg.select_option("#m_makine_tipi", "Dişlisiz")
        pg.wait_for_timeout(1400)
        r.kontrol("makine tipi ekranda motor gücünü değiştiriyor",
                  _nd > pg.evaluate("SON.m.ozet.N_hesap"),
                  f"→ dişli {_nd}, dişlisiz {pg.evaluate('SON.m.ozet.N_hesap')}")
        pg.fill("#m_motor_gucu", "7.5")
        pg.wait_for_timeout(1200)

        #  Girdi değişince yeniden hesaplanmalı ve sonuç DÖNMELİ
        #  50'lik rayda λ = 3000 / 10,51 = 285 > 250:  ω tanımsız kalır,
        #  BURKULMA kontrolü düşer ama hesap durmaz ( uyarı verilir ).
        pg.select_option("#m_kabin_ray_profili", "50 x 50 x 5")
        pg.wait_for_timeout(1400)
        r.kontrol("küçük ray profili hesabı DURDURMUYOR",
                  pg.evaluate("SON.m && SON.m.aktif === true"),
                  f"→ {pg.evaluate('SON.m && SON.m.hata')}")
        r.kontrol("küçük ray profili narinlik uyarısı veriyor",
                  pg.evaluate("(SON.m.uyarilar||[]).some(u=>u.indexOf('narin')>=0)"),
                  f"→ {pg.evaluate('SON.m.uyarilar')}")
        r.kontrol("küçük ray profili uygunsuz sonuç veriyor",
                  pg.evaluate("SON.m.ozet.tumu_uygun === false"))
        r.kontrol("takılan bölüm kılavuz raylar",
                  pg.evaluate("SON.m.bolumler.filter(b=>b.sonuc && "
                              "b.sonuc.uygun===false).map(b=>b.baslik).join('|')")
                  .find("KILAVUZ RAY") >= 0)
        pg.select_option("#m_kabin_ray_profili", "89 x 62 x 15,88")
        pg.wait_for_timeout(1400)
        r.kontrol("geri alınınca kılavuz ray bölümü yeniden uygun",
                  pg.evaluate("SON.m.bolumler.filter(b=>b.sonuc && "
                              "b.sonuc.uygun===false && "
                              "b.baslik.includes('KILAVUZ RAY')).length === 0"),
                  f"→ {pg.evaluate('SON.m.bolumler.filter(b=>b.sonuc && b.sonuc.uygun===false).map(b=>b.baslik)')}")

        #  Durak düzenleyici + türetilen alanlar
        pg.click("#m_durak_ekle")
        pg.wait_for_timeout(1400)
        r.esit("durak eklendi", pg.evaluate("MUK_DURAK.length"), 9)
        r.esit("seyir mesafesi kendiliğinden güncellendi",
               pg.input_value("#m_seyir_mesafesi"), "24,75")
        pg.click("#m_durak_sil")
        pg.wait_for_timeout(1400)
        r.esit("durak silindi", pg.evaluate("MUK_DURAK.length"), 8)
        r.esit("seyir mesafesi geri döndü",
               pg.input_value("#m_seyir_mesafesi"), "21")

        #  BOŞ KABİN AĞIRLIĞI ARTIK ZORUNLU DEĞİL — boş bırakılırsa ofis
        #  tablosundan dolar ( beyan yükü 800 kg → 800 kg ) ve paftada
        #  kaynağı "OFİS TABLOSU" yazar.
        pg.fill("#m_kabin_agirligi", "")
        pg.wait_for_timeout(1400)
        r.kontrol("boş kabin ağırlığı hesabı durdurmuyor",
                  pg.evaluate("SON.m.aktif === true"),
                  f"→ {pg.evaluate('SON.m && SON.m.hata')}")
        r.esit("boş bırakılan kabin ağırlığı tablodan doluyor",
               pg.evaluate("SON.m.girdi.kabin_agirligi"), 800)
        r.kontrol("paftada kaynağı ofis tablosu yazıyor",
                  "OFİS TABLOSU" in pg.evaluate(
                      "SON.m.girdi.kabin_agirligi_kaynak"),
                  f"→ {pg.evaluate('SON.m.girdi.kabin_agirligi_kaynak')!r}")

        #  Boş ZORUNLU alan → hesap durmalı, sebebi ekranda yazmalı
        pg.fill("#m_makine_agirligi", "")
        pg.wait_for_timeout(1400)
        r.kontrol("boş makine ağırlığı hesabı durduruyor",
                  pg.evaluate("SON.m.aktif === false"))
        r.kontrol("hata ekranda görünüyor",
                  "boş bırakılamaz" in pg.inner_text("#m_sonuc"),
                  f"→ {pg.inner_text('#m_sonuc')[:140]!r}")
        pg.fill("#m_makine_agirligi", "300")      # sözleşmenin varsayılanı
        pg.fill("#m_kabin_agirligi", "700")
        pg.wait_for_timeout(1400)
        r.kontrol("düzeltilince hesap geri geliyor",
                  pg.evaluate("SON.m.aktif === true"))

        #  BEYAN YÜKÜ DEĞİŞİNCE KABİN AĞIRLIĞI TABLODAN YENİLENİR
        #  ( avandaki trafik → kapasite izlemesinin aynısı )
        pg.select_option("#m_beyan_yuku", "1275")
        pg.wait_for_timeout(1600)
        r.esit("beyan yükü değişince kabin ağırlığı tablodan geliyor",
               pg.input_value("#m_kabin_agirligi"), "1100")
        #  Elle girilen değer, beyan yükü değişmedikçe korunur
        pg.fill("#m_kabin_agirligi", "1150")
        pg.wait_for_timeout(1400)
        r.esit("elle girilen kabin ağırlığı korunuyor",
               pg.input_value("#m_kabin_agirligi"), "1150")
        pg.select_option("#m_beyan_yuku", "800")
        pg.wait_for_timeout(1600)
        r.esit("beyan yükü yeniden değişince tablo yine izliyor",
               pg.input_value("#m_kabin_agirligi"), "800")
        pg.fill("#m_kabin_agirligi", "700")
        pg.wait_for_timeout(1400)
        #  Standarda uyan kasnak korunuyor — testin geri kalanı temiz koşsun
        r.kontrol("kasnak 280 mm hâlâ yerinde",
                  pg.input_value("#m_tahrik_kasnak_capi") == "280")

        #  Çıktı düğmeleri:  varlıkları YETMEZ, gerçekten dosya dönmeli.
        #  PROJE sekmesindedirler — çıktı bütün asansörleri kapsar, tek bir
        #  asansörün sekmesine ait değildir.
        r.esit("uygulama çıktı ve proje dosyası düğmeleri",
               pg.eval_on_selector_all(
                   "#s-uygproje .dugmeler .dg",
                   "e=>e.map(x=>x.textContent.trim())"),
               ["Projeyi kaydet", "Proje aç (.uygulama)", "Tümünü temizle",
                "Uygulama Projesi PDF", "Uygulama Projesi Excel",
                "Projeyi paketle (ZIP)"])
        _ind = pg.evaluate("""async () => {
            const dene = async uc => {
              const r = await fetch('/api/indir/'+uc, {method:'POST',
                headers:{'Content-Type':'application/json'},
                body: JSON.stringify({kapak: kapakGirdi(), girdiler: mukavemetGirdi()})});
              const b = await r.arrayBuffer();
              return {tur: (r.headers.get('Content-Type')||'').split(';')[0],
                      boyut: b.byteLength};
            };
            return {pdf: await dene('uygulama-pdf'),
                    xlsx: await dene('uygulama-xlsx')};
        }""")
        r.esit("arayüzden uygulama PDF iniyor", _ind["pdf"]["tur"], "application/pdf")
        r.kontrol("inen PDF boş değil", _ind["pdf"]["boyut"] > 20_000,
                  f"→ {_ind['pdf']['boyut']} bayt")
        r.kontrol("arayüzden uygulama Excel iniyor",
                  "spreadsheetml" in _ind["xlsx"]["tur"], f"→ {_ind['xlsx']['tur']}")
        r.kontrol("inen Excel boş değil", _ind["xlsx"]["boyut"] > 100_000,
                  f"→ {_ind['xlsx']['boyut']} bayt")

        #  Proje kimliği dosya adına giriyor mu  ( avan kapağı BASILMAMALI )
        #  Kimlik PROJE sekmesindedir:  bir kapak dört asansörü birden
        #  taşır, tek asansörün sekmesine ait değildir.
        pg.click('.sekme[data-sekme="uygproje"]')
        pg.wait_for_timeout(400)
        pg.fill("#mk_proje_adi", "Güneş Apartmanı")
        pg.evaluate("mAsansorSekmesi(0)")
        pg.wait_for_timeout(900)
        _ad = pg.evaluate("""async () => {
            const r = await fetch('/api/indir/uygulama-pdf', {method:'POST',
              headers:{'Content-Type':'application/json'},
              body: JSON.stringify({kapak: mukavemetKimlik(),
                                    girdiler: mukavemetGirdi(),
                                    sabitler: ofisSabitleri()})});
            const cd = r.headers.get('Content-Disposition')||'';
            await r.arrayBuffer();
            const m = cd.match(/filename\*=UTF-8''(.+)$/);
            return m ? decodeURIComponent(m[1]) : null;
        }""")
        r.esit("proje adı dosya adına giriyor", _ad,
               "Güneş Apartmanı - Uygulama Projesi Hesaplari.pdf")
        r.kontrol("mukavemet indirmesi avan kapağını göndermiyor",
                  pg.evaluate("Object.keys(mukavemetKimlik()).sort().join(',')")
                  == "owner,project_title,sheet_no")

        #  REVİZYON AKIŞI:  Excel al → formu boz → dosyayı geri yükle
        pg.select_option("#m_beyan_yuku", "1000")
        pg.fill("#m_kabin_agirligi", "950")
        pg.click("#m_durak_ekle")
        pg.wait_for_timeout(1600)
        _once = pg.evaluate("({yuk: SON.m.girdi.beyan_yuku, "
                            "ag: SON.m.girdi.kabin_agirligi, "
                            "durak: MUK_DURAK.length, ray: SON.m.ozet.ray_boyu})")
        _geri = pg.evaluate("""async () => {
            const r = await fetch('/api/indir/uygulama-xlsx', {method:'POST',
              headers:{'Content-Type':'application/json'},
              body: JSON.stringify({kapak: mukavemetKimlik(),
                                    girdiler: mukavemetGirdi(),
                                    sabitler: ofisSabitleri()})});
            const blob = await r.blob();
            //  formu boz
            document.getElementById('m_beyan_yuku').value = '450';
            document.getElementById('m_kabin_agirligi').value = '500';
            mDurakSil(); mDurakSil();
            await new Promise(x=>setTimeout(x, 1500));
            const bozuk = {yuk: SON.m.girdi.beyan_yuku, durak: MUK_DURAK.length};
            //  dosyayı geri yükle
            await xlsxYukle([new File([blob], 'muk.xlsx',
              {type:'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'})]);
            await new Promise(x=>setTimeout(x, 2000));
            return {bozuk, sonra: {yuk: SON.m.girdi.beyan_yuku,
                    ag: SON.m.girdi.kabin_agirligi, durak: MUK_DURAK.length,
                    ray: SON.m.ozet.ray_boyu},
                    ozet: document.getElementById('m_yukleme_ozeti').textContent};
        }""")
        r.kontrol("form gerçekten bozulmuştu",
                  _geri["bozuk"]["yuk"] == 450 and _geri["bozuk"]["durak"] != _once["durak"],
                  f"→ {_geri['bozuk']}")
        r.esit("Excel'den geri yükleme girdileri aynen döndürüyor",
               _geri["sonra"], _once)
        r.kontrol("yükleme özeti uygulama bölümünde görünüyor",
                  "Mukavemet" in _geri["ozet"], f"→ {_geri['ozet'][:90]!r}")

        #  Sayfa yenilenince girdiler duruyor mu  ( tarayıcıda saklama )
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(600)
        pg.click("#gk_uygulama")
        pg.wait_for_timeout(2200)
        r.esit("yenilemeden sonra beyan yükü duruyor",
               pg.input_value("#m_beyan_yuku"), "1000")
        r.esit("yenilemeden sonra durak sayısı duruyor",
               pg.evaluate("MUK_DURAK.length"), _once["durak"])
        r.esit("yenilemeden sonra proje adı duruyor",
               pg.input_value("#mk_proje_adi"), "Güneş Apartmanı")
        #  ─────────── AVAN VE UYGULAMA AYRI KOVALARDA ───────────
        #  Tek kova varken iki proje yan yana yaşıyordu:  avan üzerinde
        #  çalışıp uygulamaya geçince avan verisi orada duruyordu ve
        #  "Tümünü temizle" ikisini birden siliyordu.
        _kovalar = pg.evaluate(
            "Object.keys(localStorage).filter(k=>/program_v1/.test(k)).sort()")
        r.kontrol("uygulama kendi kovasına yazıyor",
                  "uygulama_program_v1" in _kovalar, f"→ {_kovalar}")
        _uk = pg.evaluate(
            "JSON.parse(localStorage.getItem('uygulama_program_v1')||'{}')")
        r.esit("uygulama kovası kendi modunu yazıyor", _uk.get("__mod"), "uygulama")
        r.esit("uygulama kovasında AVAN alanı yok",
               [k for k in _uk if k[:2] in ("c_", "a_", "k_") or k[:3] in ("of_", "sb_")], [])
        r.kontrol("uygulama kovasında mukavemet alanları var",
                  any(k.startswith("m_") for k in _uk), f"→ {sorted(_uk)[:6]}")
        r.kontrol("uygulamanın kendi ofis sabitleri de kovada",
                  any(k.startswith("uof_") for k in _uk), f"→ {sorted(_uk)[:6]}")

        #  Testin geri kalanı temiz girdiyle koşsun
        pg.evaluate("localStorage.removeItem(KOVA[MOD])")
        pg.reload(wait_until="networkidle")
        pg.wait_for_timeout(600)
        pg.click("#gk_uygulama")
        pg.wait_for_timeout(2200)

        #  ─────────── UYGULAMANIN KENDİ OFİS SABİTLERİ ───────────
        #  Avanınkinden AYRI:  avan ön tasarımdır, uygulama kesin tasarım.
        #  σem ve k1 bugüne kadar KODDA GÖMÜLÜYDÜ, ekrana çıkarıldı.
        pg.click(".sekme[data-sekme='sabitler']")
        pg.wait_for_timeout(500)
        r.kontrol("uygulamada KENDİ sabitler gövdesi görünüyor",
                  pg.is_visible("#sabitler_uygulama"))
        r.kontrol("uygulamada AVAN sabitleri görünmüyor",
                  not pg.is_visible("#sabitler_avan"))
        _uof = pg.eval_on_selector_all("[id^='uof_']", "e=>e.length")
        r.kontrol("uygulama ofis sabitleri çizildi", _uof >= 40, f"→ {_uof} alan")
        for _a in ("uof_sigma_em", "uof_k1_kaymali", "uof_verim_dislisiz",
                   "uof_verim_disli", "uof_tavan_payi"):
            r.kontrol(f"ofis sabiti ekranda: {_a}", pg.is_visible(f"#{_a}"))

        #  Ekrandan değiştirilen sabit HESABI değiştirmeli
        pg.click(".sekme[data-sekme='mukavemet']")
        pg.wait_for_timeout(400)
        _n0 = pg.evaluate("SON.m.ozet.N_hesap")
        pg.click(".sekme[data-sekme='sabitler']")
        pg.wait_for_timeout(300)
        pg.fill("#uof_verim_dislisiz", "0,95")
        pg.wait_for_timeout(2200)
        _n1 = pg.evaluate("SON.m.ozet.N_hesap")
        r.kontrol("ofis verimi motor gücünü değiştiriyor", _n1 < _n0,
                  f"→ önce {_n0}, sonra {_n1}")
        pg.fill("#uof_sigma_em", "100")
        #  KAİDE HESABI MAKİNE DAİRESİ İSTER.  Varsayılan proje MRL'dir ve
        #  bölüm 2 orada uygunluk beyan etmez ( "UYGULANMAZ" ) — σem'i
        #  düşürmenin etkisini görebilmek için makine dairesi açılır.
        #  ( Kutu akordeon içindedir;  gruplar önce açılır. )
        pg.click(".sekme[data-sekme='mukavemet']")
        pg.wait_for_timeout(300)
        pg.evaluate("mTumGruplariAc()")
        _mrl_sec(pg, False)
        #  MAKİNE DAİRESİ AÇILINCA ÖLÇÜSÜ ZORUNLU OLUR ( girdi doğrulaması );
        #  doldurulmazsa hesap hiç koşmaz ve SON.m boş kalır.
        pg.fill("#m_mk_uzunluk", "4000")
        pg.fill("#m_mk_genislik", "3000")
        pg.wait_for_timeout(2200)
        _b2 = pg.evaluate("SON.m.bolumler.find(b=>b.baslik.startsWith('2')).sonuc")
        r.kontrol("σem düşürülünce makine kaidesi kalıyor",
                  _b2.get("uygun") is False, f"→ {_b2}")
        #  MRL'ye dönünce kaide hesabı uygunluk beyan etmemeli
        _mrl_sec(pg, True)
        pg.wait_for_timeout(2200)
        _b2m = pg.evaluate("SON.m.bolumler.find(b=>b.baslik.startsWith('2')).sonuc")
        r.kontrol("MRL'de makine kaidesi uygunluk beyan etmiyor",
                  _b2m.get("uygun") is None and "UYGULANMAZ" in _b2m.get("metin", ""),
                  f"→ {_b2m}")
        #  Kutu VARSAYILAN durumunda ( MRL ) bırakılır ve SABİTLER sekmesine
        #  dönülür — aşağıdaki "Tümünü varsayılana döndür" düğmesi oradadır.
        pg.click(".sekme[data-sekme='sabitler']")
        pg.wait_for_timeout(600)
        r.kontrol("σem satırı kaynağını OFİS STANDARDI diye yazıyor",
                  "OFİS STANDARDI" in pg.evaluate(
                      "SON.m.bolumler.find(b=>b.baslik.startsWith('2'))"
                      ".adimlar.find(a=>a.sembol==='σem').kaynak"))
        pg.click("button:has-text('Tümünü varsayılana döndür')")
        pg.wait_for_timeout(2200)
        r.kontrol("sabitler varsayılana dönüyor",
                  abs(pg.evaluate("SON.m.ozet.N_hesap") - _n0) < 1e-9,
                  f"→ {pg.evaluate('SON.m.ozet.N_hesap')} ≠ {_n0}")

        #  ─────────── UYGULAMANIN KENDİ TABLOLARI ───────────
        #  Bugüne kadar YOKTU:  Tablolar sekmesi yalnız avan modundaydı,
        #  uygulama yapan mühendis kullandığı ray tablosuna bakamıyordu.
        pg.click(".sekme[data-sekme='tablolar']")
        pg.wait_for_timeout(600)
        r.kontrol("uygulamada KENDİ tablolar gövdesi görünüyor",
                  pg.is_visible("#tablolar_uygulama"))
        r.kontrol("uygulamada AVAN tabloları görünmüyor",
                  not pg.is_visible("#tablolar_avan"))
        _tb = pg.eval_on_selector_all("#utablolar_ic table", "e=>e.length")
        r.kontrol("uygulama tabloları çizildi", _tb >= 12, f"→ {_tb} tablo")
        #  BAŞLIKLAR CSS İLE BÜYÜK HARFE ÇEVRİLİYOR ve Türkçede bu dönüşüm
        #  geri alınamaz ( KILAVUZ → kilavuz, PROFİLLERİ → profi̇lleri̇ ).
        #  Bu yüzden görüntülenen metin değil, DOM'daki textContent okunur —
        #  text-transform onu değiştirmez.
        _tm = pg.eval_on_selector("#utablolar_ic", "e=>e.textContent")
        for _ara in ("Kılavuz ray profilleri", "NPU profilleri", "Askı halatları",
                     "burkulma", "Kabin alanı"):
            r.kontrol(f"uygulama tablosu: {_ara}", _ara in _tm,
                      f"→ {_tm[:130]!r}")
        #  Tablo İÇERİĞİ de basılmalı — boş başlık listesi "geçti" sayılmasın
        r.kontrol("ray tablosunda gerçek profil var", "50 x 50 x 5" in _tm)
        r.kontrol("halat tablosunda TS 12385-5 yazılı", "12385" in _tm)

        #  ─────────── PROJE DOSYASI  (.uygulama) ───────────
        pg.click('.sekme[data-sekme="uygproje"]')
        pg.wait_for_timeout(400)
        _pd = pg.evaluate("projeGovdesi('uygulama')")
        r.esit("proje dosyası modunu yazıyor", _pd.get("__mod"), "uygulama")
        r.kontrol("proje dosyası SÜRÜM taşıyor", bool(_pd.get("__surum")),
                  f"→ {_pd.get('__surum')}")
        r.esit("proje dosyasında AVAN alanı yok",
               [k for k in _pd["alanlar"]
                if k[:2] in ("c_", "a_", "k_") or k[:3] in ("of_", "sb_")], [])
        r.kontrol("proje dosyası ofis sabitlerini de taşıyor",
                  any(k.startswith("uof_") for k in _pd["alanlar"]))
        pg.fill("#mk_proje_adi", "Jan Mühendislik")
        pg.wait_for_timeout(300)
        r.esit("dosya adı proje adından üretiliyor",
               pg.evaluate("projeDosyaAdi('uygulama')"), "Jan Mühendislik.uygulama")
        #  YANLIŞ MODA yükleme reddedilmeli
        pg.evaluate("projeUygula({__mod:'avan',__surum:1,alanlar:{c_N:'11'}}, 'x.avan')")
        pg.wait_for_timeout(400)
        r.kontrol("avan dosyası uygulamaya yüklenmiyor",
                  "AVAN projesine ait" in pg.inner_text("#durum"),
                  f"→ {pg.inner_text('#durum')[:80]}")
        r.esit("reddedilen dosya girdiyi bozmadı",
               pg.input_value("#mk_proje_adi"), "Jan Mühendislik")

        pg.click("#dg_ana_ekran")
        pg.wait_for_timeout(300)
        r.kontrol("ana ekran düğmesi seçim ekranına döndürüyor", pg.is_visible("#giris"))

        #  --- avan moduna geçiş ---
        pg.click("#gk_avan")
        pg.wait_for_timeout(600)
        r.kontrol("avan seçilince uygulama açılıyor",
                  (not pg.is_visible("#giris")) and pg.is_visible('.sekme[data-sekme="avan"]'))
        r.kontrol("avan modunda mukavemet sekmesi gizli",
                  not pg.is_visible('.sekme[data-sekme="mukavemet"]'))
        r.kontrol("başlık avan programına döndü",
                  "AVAN" in pg.inner_text("#ust_ad"))
        pg.click("#dg_ana_ekran")
        pg.wait_for_timeout(300)
        pg.click("#gk_avan")
        pg.wait_for_timeout(300)
        r.kontrol("geri dönülüp yeniden girilebiliyor", not pg.is_visible("#giris"))

        # ---------------------------------------------------------------
        #  SEKME SIRASI  ( 2.7 )
        #  Şerit işlem sırasını anlatır:  1 trafik · 2 avan · 3 proje kapağı.
        #  "Sabitler" ve "Tablolar" birer adım değil, gerektikçe bakılan
        #  kaynaklardır — akışın ortasında değil, şeridin sağ ucundadırlar.
        # ---------------------------------------------------------------
        #  Şeritte HER İKİ MODUN sekmeleri durur, moda ait olmayanlar
        #  gizlenir;  sıra kontrolü GÖRÜNENLER üzerinden yapılır.
        r.esit("sekme sırası işlem sırası",
               pg.eval_on_selector_all(
                   ".sekme", "e=>e.filter(x=>!x.hidden).map(x=>x.dataset.sekme)"),
               ["trafik", "avan", "proje", "sabitler", "tablolar"])
        r.esit("açılışta 1. adım etkin",
               pg.eval_on_selector(".sekme.etkin", "e=>e.dataset.sekme"), "trafik")
        r.kontrol("açılışta trafik gövdesi görünür", pg.is_visible("#s-coklu"))
        r.kontrol("proje kapağı 3. adım olarak yazılı",
                  "3" in (pg.inner_text('.sekme[data-sekme="proje"]') or ""))
        _yer = pg.evaluate("""() => {
            const q = s => document.querySelector(s).getBoundingClientRect();
            return {kapak: q('.sekme[data-sekme="proje"]').right,
                    sabit: q('.sekme[data-sekme="sabitler"]').left,
                    serit: q('.sekmeler-ic').right,
                    tablo: q('.sekme[data-sekme="tablolar"]').right};
        }""")
        r.kontrol("başvuru sekmeleri sağ uca itildi",
                  _yer["sabit"] - _yer["kapak"] > 100, f"→ {_yer}")
        r.kontrol("son sekme şeridin sağ ucunda",
                  _yer["serit"] - _yer["tablo"] < 40, f"→ {_yer}")

        # örnek proje yüklensin
        pg.evaluate("ornekYukle()")
        pg.wait_for_timeout(1800)

        # --- her sekme açılıyor ve içerik üretiyor
        r.esit("avan modunda görünen sekme sayısı 5",
               pg.eval_on_selector_all(".sekme", "e=>e.filter(x=>!x.hidden).length"), 5)
        r.esit("şeritteki toplam sekme 6  ( + uygulama projesi )",
               pg.eval_on_selector_all(".sekme", "e=>e.length"), 6)
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
        r.kontrol("1:1 askıda η aynen kullanılıyor", "0,85" in _m)
        pg.select_option("#a_i_palanga1", "2")
        pg.wait_for_timeout(1300)
        _m = pg.inner_text("#a_sonuc")
        r.kontrol("2:1 askıda da η = 0,85  ( Δη kaldırıldı )", "0,85" in _m)
        r.kontrol("ekranda artık η′ = 0,75 yok", "0,75" not in _m)
        r.kontrol("toplam sistem verimi kutusu ekrandan kalktı",
                  not pg.is_visible("#a_toplam_verim1"))
        pg.fill("#a_eta1", "0,82")
        pg.wait_for_timeout(1400)
        _m = pg.inner_text("#a_sonuc")
        r.kontrol("girilen η aynen kullanılıyor ( 0,82 )", "0,82" in _m)
        r.kontrol("toplam sistem verimi notu paftada", "TOPLAM SİSTEM VERİMİ" in _m)
        pg.fill("#a_eta1", "0,85")
        pg.wait_for_timeout(1300)

        #  MRL işaret kutusu
        r.kontrol("MRL kutusu var", pg.is_visible("#a_mk_yok"))
        pg.check("#a_mk_yok")
        pg.wait_for_timeout(1300)
        r.kontrol("MRL işaretliyken ölçüler kapanıyor",
                  pg.evaluate("document.getElementById('a_mk_uzunluk').disabled"))
        #  MRL işaretliyse makine dairesi bölümü EKRANDA DA hiç görünmez —
        #  makine dairesi yoksa aydınlatma hesabının konusu da yoktur.
        r.kontrol("MRL işaretliyken makine dairesi bölümü hiç görünmüyor",
                  "MAKİNE DAİRESİ" not in pg.inner_text("#a_sonuc"))
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
                   "priz_adedi", "cosfi", "motor_elektrik_verimi",
                   "UL", "IDn", "lc", "ayd_sutun"):
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
        uygulamayaGir(pg)
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
        uygulamayaGir(pg)
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

        # ==============================================================
        #  v2.9 — YÜKLEMEDE ÖNCEKİ PROJENİN ARTIKLARI
        #  uygula() yalnız GELEN alanları yazıyordu;  dosyada olmayan alanlar
        #  önceki projeden kalıyordu.  Tek asansörlük bir dosya, formda duran
        #  eski 2. ve 3. kolonlar yüzünden ÜÇLÜ GRUP olarak hesaplanabiliyordu.
        # ==============================================================
        pg.set_viewport_size({"width": 1440, "height": 900})
        pg.wait_for_timeout(400)
        pg.evaluate("trafikAdedi(3)")
        pg.wait_for_timeout(400)
        for _i, (_P, _kg) in enumerate((("10", "900"), ("16", "1100"), ("20", "1100")), 1):
            pg.select_option(f"#c_P{_i}", _P)
            pg.select_option(f"#c_kg{_i}", _kg)
        pg.wait_for_timeout(700)
        _once = pg.evaluate("[1,2,3,4].map(i=>(document.getElementById('c_P'+i)||{}).value)")
        r.kontrol("üç kolon dolduruldu", _once[:3] == ["10", "16", "20"], f"→ {_once}")

        _tekx = os.path.join(_D, "tek_tek.xlsx")
        with open(_tekx, "wb") as _f:
            _f.write(XE.trafik_xlsx("tek", {
                "bina_tipi": "Konut", "bina_yuksekligi": 39.98, "yapi_yuksekligi": 43,
                "N": 11, "h": 3, "hizli1": 44, "hizli2": 3, "P": 10,
                "kapi_genisligi": 900, "kapi_tipi": "Teleskopik Otomatik"}, {}))
        pg.set_input_files("#xlsx_ac", _tekx)
        pg.wait_for_timeout(3000)
        _sonra = pg.evaluate("[1,2,3,4].map(i=>(document.getElementById('c_P'+i)||{}).value)")
        r.kontrol("tek asansörlük dosya eski kolonları temizliyor",
                  not any(_sonra[1:]), f"→ {_sonra}")
        r.esit("tek asansörlük dosyada adet 1", pg.evaluate("TRAFIK_ADET"), 1)

        #  Avan dosyasındaki kapasite / hız, formdaki eski trafikle EZİLMEMELİ
        _avx = os.path.join(_D, "avan_16.xlsx")
        with open(_avx, "wb") as _f:
            _f.write(XE.avan_xlsx({
                "ortak": {"temel_a": 26.55, "temel_b": 16.4, "mk_yok": True},
                "asansorler": [{"tanim": "A", "kapasite": 16, "V": 2.5, "eta": 0.85,
                                "Hk": 32.85, "kuyu_genisligi": 2000, "kabin_boyu": 1700,
                                "kabin_genisligi": 1300, "makine_tipi": "Dişlisiz"}],
                "sabitler": {}}, {}))
        pg.set_input_files("#xlsx_ac", _avx)
        pg.wait_for_timeout(3500)
        r.esit("yüklenen avan kapasitesi korunuyor",
               pg.evaluate("(document.getElementById('a_kapasite1')||{}).value"), "16")
        r.kontrol("yüklenen avan hızı korunuyor",
                  pg.evaluate("(document.getElementById('a_V1')||{}).value")
                  in ("2,5", "2.5"))

        #  v2.9 — TIRNAK İÇEREN METİN KESİLMEMELİ.  kacis() yalnız & < >
        #  kaçırıyordu;  value="${kacis(...)}" özniteliğinde çift tırnak
        #  özniteliği erken kapatıyor, `Daire "A" bloğu` yazıp yeniden açınca
        #  alanda yalnız `Daire ` kalıyordu.
        pg.evaluate("""() => {
            document.getElementById('c_eknufus_liste').innerHTML = '';
            ekNufusEkle('c', {aciklama: 'Daire "A" bloğu & <ek>', miktar: '12',
                              kalem: 'DOĞRUDAN KİŞİ — Tablo-1 dışı'});
        }""")
        pg.wait_for_timeout(400)
        _ac = pg.evaluate(
            "(document.querySelector('#c_eknufus_liste .en-ac')||{}).value")
        r.esit("tırnak içeren açıklama korunuyor", _ac, 'Daire "A" bloğu & <ek>')
        _mi = pg.evaluate(
            "(document.querySelector('#c_eknufus_liste .en-mi')||{}).value")
        r.esit("miktar korunuyor", _mi, "12")

        r.kontrol("konsol hatası yok", not konsol, f"→ {konsol[:4]}")
        tarayici.close()
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
