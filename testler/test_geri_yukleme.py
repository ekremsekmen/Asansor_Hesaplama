# -*- coding: utf-8 -*-
"""
TEST 6  —  PROJE DOSYASI GERİ YÜKLEME  ( revizyon akışı )

Projenin tek geri dönüş noktası proje dosyasıdır  ( .avan · .uygulama ).
Bu test gidiş-dönüşün KAYIPSIZ olduğunu doğrular:

    form  →  "Projeyi kaydet"  →  program sıfırlanır  →  dosya yüklenir
          →  AYNI form  ·  AYNI hesap sonucu

Formdaki BÜTÜN alanlar ( seçim · onay kutusu · metin · sayı ) varsayılan dışı
bir değere çekilir;  dosyaya yazılmayan ya da geri okunmayan tek bir alan
testi kırar.  Uygulama projesinde iki asansör farklı değerlerle doldurulur —
aktif olmayan asansörün kaybolması da görünür.

Sunucu ( baslat.command ) ve Playwright gerekir;  yoksa test atlanır.
"""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from testler.ortak import Rapor                  # noqa: E402

BASE = os.environ.get("AVAN_TEST_URL", "http://127.0.0.1:8760")

#  Moddaki her alanı varsayılan dışı bir değere çeker;  değişen alan sayısını döner.
_DEGISTIR = """(mod) => {
  let i = 0, adet = 0;
  document.querySelectorAll('input,select').forEach(e => {
    if(!e.id || e.id.indexOf('_goster') >= 0 || e.type === 'file') return;
    if(alanModu(e.id) !== mod) return;
    i++;
    //  Asansör kartlarının "etkin" kutuları trafik adedinden TÜRETİLİR
    //  ( avanKartlariGoster );  elle ters çevrilmeleri ekranın ulaşamayacağı
    //  bir durum yaratır, o yüzden dokunulmaz.
    if(/^a_aktif/.test(e.id)) return;
    if(e.type === 'checkbox'){ e.checked = !e.checked; adet++; return; }
    if(e.tagName === 'SELECT'){
      const ops = [...e.options].map(o => o.value).filter(v => v !== '' && v !== e.value);
      if(ops.length){ e.value = ops[i % ops.length]; adet++; }
      return;
    }
    const v = String(e.value || '').trim();
    if(v === '') e.value = String(2 + (i % 9));
    else if(/^[-+]?[0-9]+([.,][0-9]+)?$/.test(v))
      e.value = String(parseFloat(v.replace(',', '.')) + 1).replace('.', ',');
    else e.value = v + ' ' + i;
    adet++;
  });
  return adet;
}"""

#  Ekranın sunucuya yolladığı hesap istekleri ve yanıtları  ( mod başına )
_SONUC = {
    "avan": """async () => {
      const iste = async (uc, govde) => await (await fetch(uc, {method:'POST',
        headers:{'Content-Type':'application/json'}, body: JSON.stringify(govde)})).json();
      return {trafik: await iste('/api/trafik', {girdiler: trafikGirdi()}),
              avan: await iste('/api/avan', {girdiler: avanGirdi()})};
    }""",
    "uygulama": """async () => {
      return await (await fetch('/api/uygulama/coklu', {method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify(mukavemetIstek())})).json();
    }""",
}


def _sunucu_var():
    try:
        urllib.request.urlopen(BASE + "/api/saglik", timeout=5).read()
        return True
    except Exception:                                    # noqa: BLE001
        return False


def _ac(pg, mod):
    """Sayfayı sıfırdan açıp ilgili projeye girer."""
    pg.goto(BASE, wait_until="networkidle")
    pg.wait_for_timeout(600)
    if pg.is_visible("#giris"):
        pg.click("#gk_" + mod)
    pg.wait_for_timeout(2500)


def _kaydet(pg, mod):
    """"Projeyi kaydet" düğmesiyle inen dosyanın içeriği  ( ad , sözlük )."""
    sekme = "uygproje" if mod == "uygulama" else "proje"
    pg.click(f'.sekme[data-sekme="{sekme}"]')
    pg.wait_for_timeout(300)
    if mod == "avan":
        pg.evaluate("document.querySelector('details.proje-araclari').open = true;")
        pg.wait_for_timeout(200)
    with pg.expect_download(timeout=20000) as bilgi:
        pg.click(f'#s-{sekme} button:has-text("Projeyi kaydet")')
    indirilen = bilgi.value
    with open(indirilen.path(), encoding="utf-8") as f:
        return indirilen.suggested_filename, json.load(f)


def _farkli_anahtarlar(a, b):
    return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def _hesap_hatasi(mod, sonuc):
    """Ekranın hesabı YAPILDIYSA None, yapılmadıysa sebebi."""
    if mod == "avan":
        h = sonuc["trafik"].get("hata") or sonuc["avan"].get("hata")
        if h:
            return h
        return None if any(a.get("aktif") for a in sonuc["avan"].get("asansorler") or []) \
            else "aktif asansör yok"
    if not sonuc.get("aktif"):
        return sonuc.get("hata") or "hesap yapılmadı"
    kalan = [a.get("hata") for a in sonuc.get("asansorler") or [] if not a.get("aktif")]
    return kalan or None


#  Bir alanı kimliğiyle doldurur ve ekranın dinlediği olayları tetikler.
#  Olmayan kimlik testi durdurur — yazım hatası sessizce "geçti" sayılmasın.
_DOLDUR = """(d) => {
  for(const [id, v] of Object.entries(d)){
    const e = document.getElementById(id);
    if(!e) throw new Error('alan yok: ' + id);
    if(e.type === 'checkbox') e.checked = v; else e.value = v;
    e.dispatchEvent(new Event('input', {bubbles: true}));
    e.dispatchEvent(new Event('change', {bubbles: true}));
  }
  return Object.keys(d).length;
}"""


def _gidis_donus(r, pg, mod, hazirla, gecerli=False):
    """Kaydet → sıfırla → yükle.

    ``gecerli``:  proje HESAPLANABİLİR olmalıdır ve bu, kaydetmeden önce
    denetlenir.  Her alanı varsayılan dışına çeken tur ( gecerli=False )
    alan kaybını yakalar ama değerleri fiziksel olarak tutarsızdır;  hesap
    orada hata verir ve "aynı sonuç" iki HATA MESAJININ eşitliğine iner.
    Hesabın gidiş-dönüşü ancak geçerli bir projeyle kanıtlanır.
    """
    etiket = f"[{mod}{' · geçerli proje' if gecerli else ''}]"
    _ac(pg, mod)
    pg.evaluate("localStorage.clear()")
    _ac(pg, mod)
    degisen = hazirla(pg)
    r.kontrol(f"{etiket} formdaki alanlar değiştirildi", degisen > (10 if gecerli else 20),
              f"→ {degisen} alan")
    #  Ekranın bir hesabı yapması:  hesaptan türeyen form durumu ( trafikten
    #  gelen avan kartları gibi ) kaydetmeden önce oturmuş olmalı.
    pg.evaluate("async () => { yaz(); " + ("await hesapMukavemet();" if mod == "uygulama"
                                           else "await hesaplaHepsi();") + " yaz(); }")
    pg.wait_for_timeout(1500)

    ad, dosya = _kaydet(pg, mod)
    r.kontrol(f"{etiket} proje dosyası uzantısı", ad.endswith("." + mod), f"→ {ad}")
    r.esit(f"{etiket} dosya kendi modunu yazıyor", dosya.get("__mod"), mod)
    once_alan = pg.evaluate(f"projeGovdesi('{mod}').alanlar")
    once_sonuc = pg.evaluate(_SONUC[mod])
    if gecerli:
        _h = _hesap_hatasi(mod, once_sonuc)
        r.kontrol(f"{etiket} kaydetmeden önce hesap GERÇEKTEN yapıldı  ( ölçüt boş değil )",
                  _h is None, f"→ {str(_h)[:160]}")
    for k in sorted(once_alan):
        r.kontrol(f"{etiket} dosyada {k}", dosya["alanlar"].get(k) == once_alan[k],
                  f"→ form {once_alan[k]!r}, dosya {dosya['alanlar'].get(k)!r}")

    #  Program sıfırlanır — dosya yüklenmeden form gerçekten farklı olmalı
    pg.evaluate("localStorage.clear()")
    _ac(pg, mod)
    bos_alan = pg.evaluate(f"projeGovdesi('{mod}').alanlar")
    r.kontrol(f"{etiket} sıfırlanan form dosyadakinden farklı  ( ölçüt boş değil )",
              len(_farkli_anahtarlar(bos_alan, once_alan)) > (10 if gecerli else 20),
              f"→ {len(_farkli_anahtarlar(bos_alan, once_alan))} alan farklı")

    pg.evaluate("d => projeUygula(d, 'deneme')", dosya)
    pg.wait_for_timeout(3000)
    r.kontrol(f"{etiket} yükleme bildiriliyor", "Proje açıldı" in pg.inner_text("#durum"),
              f"→ {pg.inner_text('#durum')[:80]!r}")
    sonra_alan = pg.evaluate(f"projeGovdesi('{mod}').alanlar")
    for k in sorted(set(once_alan) | set(sonra_alan)):
        r.kontrol(f"{etiket} geri geldi {k}", once_alan.get(k) == sonra_alan.get(k),
                  f"→ kaydedilen {once_alan.get(k)!r}, yüklenen {sonra_alan.get(k)!r}")
    if mod == "uygulama":
        #  EKRAN DA DEĞERİ GÖSTERMELİ:  veri doğru gelip form başka bir yerleşimi
        #  göstermemeli ( düğme · yerleşime göre gizlenen alanlar ).
        r.kontrol(f"{etiket} makine dairesi düğmesi yüklenen değeri gösteriyor",
                  pg.evaluate("""() => { const k = $('m_mk_yok');
                      const s = document.querySelector('.secim-ikili[data-icin="m_mk_yok"] .secim-dg.secili');
                      return !!s && (s.dataset.deger === '1') === k.checked; }"""))
        r.kontrol(f"{etiket} yerleşime göre gizlenen alanlar yüklenen değere uyuyor",
                  pg.evaluate("""() => { const k = $('m_mk_yok').checked, g = MUK.yerlesime_gore_gizli;
                      const gizli = a => $('m_' + a).closest('.alan').classList.contains('kural-disi');
                      return g.mrl.every(a => gizli(a) === k) && g.daireli.every(a => gizli(a) === !k); }"""))
    sonra_sonuc = pg.evaluate(_SONUC[mod])
    r.kontrol(f"{etiket} geri yüklenen proje AYNI hesap sonucunu veriyor"
              + ("" if gecerli else "  ( ya da aynı hatayı )"),
              json.dumps(once_sonuc, sort_keys=True) == json.dumps(sonra_sonuc, sort_keys=True))

    #  Dosyada olmayan alan sessizce varsayılana dönmemeli — söylenmeli
    eksik = json.loads(json.dumps(dosya))
    silinen = next(k for k in eksik["alanlar"] if not k.startswith("__"))
    del eksik["alanlar"][silinen]
    pg.evaluate("d => projeUygula(d, 'eksik')", eksik)
    pg.wait_for_timeout(1500)
    r.kontrol(f"{etiket} eksik alanlı dosyada uyarı çıkıyor",
              "VARSAYILANA döndü" in pg.inner_text("#durum"),
              f"→ {pg.inner_text('#durum')[:90]!r}")


def _avan_hazirla(pg):
    pg.evaluate("ornekYukle()")
    pg.wait_for_timeout(1500)
    pg.evaluate("trafikAdedi(3)")
    pg.evaluate("""() => ekNufusEkle('c', {aciklama: 'Zemin kat "A" dükkân',
                                          miktar: '14', kalem: 'DOĞRUDAN KİŞİ — Tablo-1 dışı'})""")
    pg.wait_for_timeout(500)
    return pg.evaluate(_DEGISTIR, "avan")


def _uygulama_hazirla(pg):
    pg.evaluate("mAdetDegisti(2)")
    pg.wait_for_timeout(800)
    pg.evaluate("mAsansorSekmesi(0)")
    pg.wait_for_timeout(600)
    adet = pg.evaluate(_DEGISTIR, "uygulama")
    pg.evaluate("mAsansorSekmesi(1)")
    pg.wait_for_timeout(800)
    #  İkinci asansör birinciden farklı olsun:  alanları bir tur daha değiştir.
    #  Tur iki asansöre AYNI dönüşümü uygular ( ikincisi birincinin değişmemiş
    #  kopyasıdır );  ayrışmaları için ikincinin seyir mesafesi ayrıca değişir.
    adet += pg.evaluate(_DEGISTIR, "uygulama")
    pg.evaluate("document.getElementById('m_seyir_mesafesi').value = '37,5'")
    adet += 1
    #  MAKİNE DAİRELİ PROJE.  İki tur onay kutularını İKİ KEZ çevirdiği için
    #  proje geneli "makine dairesiz" kutusu varsayılana ( MRL ) dönüyordu:
    #  test hiç makine daireli bir dosya kaydetmiyordu.  Varsayılanın tersi
    #  açıkça verilir ( tabliye · şase · makine dairesi ölçüleri o zaman
    #  hesaba girer ve ekranda görünmeleri gerekir ).
    pg.evaluate("document.getElementById('m_mk_yok').checked = false")
    pg.evaluate("mAsansorSekmesi(0)")
    pg.wait_for_timeout(800)
    return adet


def _avan_gecerli(pg):
    """HESAPLANABİLİR avan projesi:  örnek proje + ofis sabitlerinde ve ek
    nüfusta varsayılan dışı ( ama aralıkta ) değerler."""
    pg.evaluate("ornekYukle()")
    pg.wait_for_timeout(1500)
    pg.evaluate("""() => ekNufusEkle('c', {aciklama: 'Zemin kat dükkân',
                                          miktar: '14', kalem: 'DOĞRUDAN KİŞİ — Tablo-1 dışı'})""")
    pg.wait_for_timeout(500)
    return pg.evaluate(_DOLDUR, {"of_beta": "220", "sb_cosfi": "0,86", "of_S1": "10",
                                 "sb_priz_adedi": "4", "of_goz_araligi": "15"}) + \
        pg.evaluate("Object.keys(projeGovdesi('avan').alanlar).filter(k => !k.startsWith('__')"
                    " && String(projeGovdesi('avan').alanlar[k]).trim() !== '').length")


def _uygulama_gecerli(pg):
    """HESAPLANABİLİR iki asansörlü uygulama projesi.

    Asansörler birbirinden farklıdır;  birinin kabin ağırlığı tablodan
    ( kendiliğinden ), öbürününki elle gelir.  Gelişmiş alanlar, proje
    geneli ( makine daireli ) ve ofis sabitleri de varsayılan dışıdır.
    """
    pg.evaluate("mAdetDegisti(2)")
    pg.wait_for_timeout(800)
    pg.evaluate("mTumGruplariAc()")
    pg.evaluate("mAsansorSekmesi(0)")
    pg.wait_for_timeout(600)
    n = pg.evaluate(_DOLDUR, {
        "m_asansor_adi": "A1 — ana hol", "m_sarilma_acisi": "180",
        "m_kasnak_belgesi": "Var", "m_seyir_mesafesi": "24,5",
        "m_kabin_konsol_arasi": "2500", "m_kabin_paten_arasi": "3400",
        "m_reg_gergi_agirligi": "80", "m_denge_zinciri": "Var",
        "m_kanal_isleme": "Sertleştirilmiş"})
    pg.evaluate("mAsansorSekmesi(1)")
    pg.wait_for_timeout(800)
    n += pg.evaluate(_DOLDUR, {
        "m_asansor_adi": "A2 — servis", "m_sarilma_acisi": "170",
        "m_kasnak_belgesi": "Var", "m_seyir_mesafesi": "37,5",
        "m_beyan_yuku": "1000", "m_kabin_agirligi": "990",
        "m_agirlik_yeri": "Sol", "m_halat_adedi": "8"})
    pg.evaluate("mAsansorSekmesi(0)")
    pg.wait_for_timeout(800)
    n += pg.evaluate(_DOLDUR, {
        "m_temel_a": "26,55", "m_temel_b": "16,4", "m_mk_yok": False,
        "m_mk_uzunluk": "3200", "m_mk_genislik": "2600",
        "uof_beta": "220", "uof_cosfi": "0,86"})
    pg.wait_for_timeout(800)
    return n


def calistir():
    print("\n\033[1mTEST 6 — PROJE DOSYASI GERİ YÜKLEME (revizyon akışı)\033[0m")
    r = Rapor("Proje dosyası geri yükleme")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        r.atla("Playwright kurulu değil — proje dosyası testi atlandı")
        return r
    if not _sunucu_var():
        r.atla(f"Sunucu {BASE} adresinde çalışmıyor — proje dosyası testi atlandı")
        return r

    with sync_playwright() as pw:
        try:
            tarayici = pw.chromium.launch()
        except Exception as e:                           # noqa: BLE001
            r.atla(f"Chromium başlatılamadı: {e}")
            return r
        pg = tarayici.new_page(viewport={"width": 1440, "height": 1000},
                               accept_downloads=True)
        konsol = []
        pg.on("console", lambda m: konsol.append(m.text) if m.type == "error" else None)
        pg.on("pageerror", lambda e: konsol.append("PAGEERROR " + str(e)))
        pg.on("dialog", lambda d: d.dismiss())

        _gidis_donus(r, pg, "avan", _avan_hazirla)
        _gidis_donus(r, pg, "avan", _avan_gecerli, gecerli=True)
        _gidis_donus(r, pg, "uygulama", _uygulama_gecerli, gecerli=True)
        #  Bu tur EN SON koşar:  aşağıdaki iki asansör denetimleri onun
        #  yüklediği projeye bakar.
        _gidis_donus(r, pg, "uygulama", _uygulama_hazirla)
        #  İki asansörün ikisi de dosyada ve birbirinden farklı
        _asl = pg.evaluate("MUK_ASANSORLER.slice(0, MUK_ADET)")
        r.esit("[uygulama] iki asansör geri geldi", len(_asl), 2)
        r.kontrol("[uygulama] iki asansörün girdileri ayrı kaldı",
                  len(_asl) == 2 and _asl[0] != _asl[1])

        #  Excel artık açılmıyor:  arayüzde .xlsx seçen dosya girişi yok
        r.esit("Excel yükleme girişi yok",
               pg.eval_on_selector_all("input[type=file]",
                                       "e=>e.filter(x=>/xlsx/i.test(x.accept)).length"), 0)
        r.kontrol("konsol hatası yok", not konsol, f"→ {konsol[:4]}")
        tarayici.close()
    return r


if __name__ == "__main__":
    sys.exit(0 if calistir().yazdir() else 1)
