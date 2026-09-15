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


def _gidis_donus(r, pg, mod, hazirla):
    etiket = f"[{mod}]"
    _ac(pg, mod)
    pg.evaluate("localStorage.clear()")
    _ac(pg, mod)
    degisen = hazirla(pg)
    r.kontrol(f"{etiket} formdaki alanlar değiştirildi", degisen > 20, f"→ {degisen} alan")
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
    for k in sorted(once_alan):
        r.kontrol(f"{etiket} dosyada {k}", dosya["alanlar"].get(k) == once_alan[k],
                  f"→ form {once_alan[k]!r}, dosya {dosya['alanlar'].get(k)!r}")

    #  Program sıfırlanır — dosya yüklenmeden form gerçekten farklı olmalı
    pg.evaluate("localStorage.clear()")
    _ac(pg, mod)
    bos_alan = pg.evaluate(f"projeGovdesi('{mod}').alanlar")
    r.kontrol(f"{etiket} sıfırlanan form dosyadakinden farklı  ( ölçüt boş değil )",
              len(_farkli_anahtarlar(bos_alan, once_alan)) > 20,
              f"→ {len(_farkli_anahtarlar(bos_alan, once_alan))} alan farklı")

    pg.evaluate("d => projeUygula(d, 'deneme')", dosya)
    pg.wait_for_timeout(3000)
    r.kontrol(f"{etiket} yükleme bildiriliyor", "Proje açıldı" in pg.inner_text("#durum"),
              f"→ {pg.inner_text('#durum')[:80]!r}")
    sonra_alan = pg.evaluate(f"projeGovdesi('{mod}').alanlar")
    for k in sorted(set(once_alan) | set(sonra_alan)):
        r.kontrol(f"{etiket} geri geldi {k}", once_alan.get(k) == sonra_alan.get(k),
                  f"→ kaydedilen {once_alan.get(k)!r}, yüklenen {sonra_alan.get(k)!r}")
    sonra_sonuc = pg.evaluate(_SONUC[mod])
    r.kontrol(f"{etiket} geri yüklenen proje AYNI hesap sonucunu veriyor",
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
    pg.evaluate("mAsansorSekmesi(0)")
    pg.wait_for_timeout(800)
    return adet


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
