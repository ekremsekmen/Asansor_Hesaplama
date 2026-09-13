/* ═══════════════════════════════════════════════════════════════════
   UYGULAMA PROJESİ  —  arayüz

   Mukavemet + elektrik + topraklama.  Avan tarafından BAĞIMSIZDIR;
   ortak kısım için bkz. ortak.js
   ═══════════════════════════════════════════════════════════════════ */

/* ═══════════════════════════════════════════════════════════════════════
   UYGULAMA PROJESİ  ·  MUKAVEMET HESABI
   Form kendini SUNUCUDAN gelen girdi sözleşmesinden üretir
   ( /api/mukavemet/alanlar → engine/mukavemet_girdi.GRUPLAR ).  Böylece
   alan eklemek / çıkarmak için arayüze dokunmak gerekmez;  tek doğruluk
   kaynağı motorun yanındaki sözleşmedir.
   ═══════════════════════════════════════════════════════════════════════ */
const M_ID = a => 'm_' + a;

/*  ÇOKLU ASANSÖR.  Bir binada farklı kuyularda 1-4 asansör olabilir;  hesap
    her biri için AYNIDIR, değişen yalnız girdilerdir.

    FORM TEK KOPYADIR.  Dört kopya DOM ( 4 × 86 alan ) hem ağır olurdu hem de
    akordeonu dörde katlardı.  Bunun yerine aktif asansörün değerleri formda
    durur;  asansör değişince form kaydedilip ötekinin değerleri yüklenir.
    MUK_ASANSORLER[i] = { alan anahtarı: değer , __durak: [ … ] } */
//  MUK_ASANSORLER her zaman 4 haritaya kadar tutar;  MUK_ADET kaçının
//  KULLANILDIĞINI söyler.  Adedi azaltmak veri SİLMEZ — 3→2→3 yapan mühendis
//  girdilerini geri bulur.
let MUK_ASANSORLER = [{}];
let MUK_AKTIF = 0;
let MUK_ADET = 1;

/*  Proje geneli alanlar asansörden asansöre TAŞINMAZ:  topraklama ve makine
    dairesi binaya aittir.  Liste sunucudan gelir ( MUK.proje_geneli ). */
const mProjeGeneliMi = a => !!(MUK && (MUK.proje_geneli||[]).includes(a));

/*  Sayı biçimi:  sözleşme 0,63 gibi ondalıkları nokta ile taşır, kullanıcı
    virgül görür.  Seçenek listesinde DEĞER değişmez, yalnız etiket çevrilir. */
const mSayi = x => (typeof x === 'number')
  ? String(x).replace('.', ',') : String(x ?? '');

async function mukavemetKur(){
  if(MUK) return;                       // bir kez kurulur
  try{
    MUK = await (await fetch('/api/uygulama/alanlar')).json();
  }catch(e){
    $('m_form').innerHTML = `<div class="uyari kirmizi">Girdi tanımları alınamadı: ${kacis(e)}</div>`;
    return;
  }
  let h = '';
  //  ORTAK GİRDİ KÖPRÜSÜ ( MUK.ortak_kopru ) BURADA YAZILMAZ.  Bir süre
  //  formun başında "beyan yükü → Q · beyan hızı → V …" diye duruyordu;
  //  köprü zaten görünmez çalışıyor ( alan zaten formda, ikinci kez
  //  sorulmuyor ) ve o kutu her açılışta okunacak bir şey değil, girdilerin
  //  önünü kapatan sabit bir metindi.  Sözleşme API'de duruyor.
  //  AKORDEON.  86 girdi tek sütunda alt alta durunca aranan alanı bulmak
  //  zorlaşıyordu.  Girdi sütunu 440 px'tir — yatay sekme şeridi sığmaz;
  //  akordeon bu genişliğe oturur ve KAPALIYKEN DE bütün bölüm adları
  //  görünür, yani harita hep ortadadır.
  //  Alanlar DOM'dan SİLİNMEZ, yalnız gizlenir:  mukavemetGirdi() bütün
  //  grupları dolaşıp okur ve kapalı gruptaki alan da okunur.  Görünüm
  //  değişikliği hesabın hiçbir noktasına dokunmaz.
  h += `<div class="m-ara-satir">
          <input id="m_ara" class="m-ara" type="search" placeholder="alan ara…"
                 oninput="mAramaUygula()" autocomplete="off">
        </div>`;
  //  PROJE GENELİ ALANLAR AKORDEONDA, kendi grubunun ( Elektrik ve
  //  topraklama ) içinde durur ve HER asansör sekmesinde görünür.  Bir süre
  //  ayrı bir PROJE sekmesine çekilmişlerdi;  topraklamayı girmek için sekme
  //  değiştirmek gerekiyordu ve alanlar zaten ait oldukları grubun dışına
  //  düşüyordu.  Karışmasınlar diye üzerlerinde "proje geneli" etiketi var:
  //  değer TEKTİR, hangi sekmede yazılırsa yazılsın aynı yere gider ve
  //  asansörden asansöre kopyalanmaz ( mAsansorKaydet onları atlar ).
  for(const [i, g] of MUK.gruplar.entries()){
    let ic = '', acik = [];
    for(const f of g.alanlar){
      if(f.tur === 'liste'){
        if(acik.length){ ic += mSatir(acik); acik = []; }
        ic += mDurakKutusu(f);
        continue;
      }
      acik.push(mAlan(f));
      if(acik.length === 2){ ic += mSatir(acik); acik = []; }
    }
    if(acik.length) ic += mSatir(acik);
    if(!ic) continue;                       // bütün alanları proje geneli olan grup
    h += `<div class="m-grup" data-grup="${i}" data-ad="${kacis(g.ad)}">
            <button type="button" class="m-grup-bas" onclick="mGrupDegistir(${i})">
              <span class="m-grup-ok">▸</span>
              <span class="m-grup-ad">${kacis(g.ad)}</span>
              <span class="m-grup-adet" data-toplam="${g.alanlar.length}"
                    >${g.alanlar.length}</span>
            </button>
            <div class="m-grup-ic" hidden>${ic}</div>
          </div>`;
  }
  $('m_form').innerHTML = h;
  //  Varsayılan durak listesi
  const d = MUK.gruplar.flatMap(g=>g.alanlar).find(f=>f.tur==='liste');
  MUK_DURAK = (d && d.varsayilan ? d.varsayilan : [3000]).map(mSayi);
  //  Uygulamanın KENDİ ofis sabitleri ve KENDİ tabloları — avanınkinden ayrı.
  uygulamaSabitFormuKur();
  uygulamaTablolariKur();
  mukavemetGeriYukle();
  mDurakCiz();
  //  Son bakılan grup açık gelsin — sayfa yenilenince baştan başlamasın.
  let _g0 = 0; try{ _g0 = Number(localStorage.getItem('m_grup')) || 0; }catch(e){}
  mGrupAc(_g0 < MUK.gruplar.length ? _g0 : 0, true);
  //  Asansör durumu:  geri yükleme diziyi doldurmuşsa aktif olanı forma bas.
  if(!Array.isArray(MUK_ASANSORLER) || !MUK_ASANSORLER.length) MUK_ASANSORLER = [{}];
  if(MUK_AKTIF >= MUK_ASANSORLER.length) MUK_AKTIF = 0;
  if(MUK_ASANSORLER.length > 1 || Object.keys(MUK_ASANSORLER[0]||{}).length)
    mAsansorYukle(MUK_AKTIF);
  if($('m_adet')) $('m_adet').value = String(MUK_ADET);
  mMakineDairesiKutulari();
  mIkiliTazele();
  mKanalUyumu();
  mAsansorSekmeleriTazele();
  //  Kovaya İLK AÇILIŞTA da yazılır:  yoksa kullanıcı hiçbir alana dokunmadan
  //  sayfayı yenilediğinde uygulama projesi boş açılırdı ( avan tarafında bu
  //  sorun yok, orada form açılışta kuruluyor ).
  yaz();
  hesapMukavemet();
}

/*  Form SONRADAN kurulduğu için açılıştaki uygula() bu alanları bulamaz;
    saklanan değerler burada, form ayağa kalktıktan sonra yerine oturur.
    Yoksa uygulama projesi her açılışta varsayılanlara dönüyordu. */
function mukavemetGeriYukle(){
  //  Uygulamanın KENDİ kovası okunur — avanınki ayrı dosyadadır.
  let o; try{ o = JSON.parse(localStorage.getItem(KOVA.uygulama)||'null'); }catch(e){ o = null; }
  if(!o) return;
  //  KOVA ALAN KİMLİĞİYLE ( "m_beyan_yuku" ) anahtarlanır, sözleşme
  //  anahtarıyla değil;  o yüzden burada mFormaYaz kullanılamaz.  Gezinti
  //  yine ortak, yalnız kaynağı ve boş-değer kuralı farklı:  kovada boş
  //  duran alan formdakini EZMEZ.
  for(const f of mAlanlar(f => f.tur !== 'liste')){
    const e = $(M_ID(f.anahtar));
    if(!e || o[e.id] === undefined) continue;
    //  Kovada BOŞ duran alan formdakini ezmez ( onay kutusu hariç:  orada
    //  "false" geçerli bir değerdir ).
    if(e.type !== 'checkbox' && o[e.id] === '') continue;
    mAlanYaz(f, o[e.id]);
  }
  //  UYGULAMAYA AİT HER ALAN geri yazılır — yalnız sözleşmedekiler değil.
  //  Proje kimliği ( mk_… ) ve ofis sabitleri ( uof_… ) de buradadır;
  //  yoksa sayfa yenilendiğinde proje adı ve ofis ayarları kayboluyordu.
  document.querySelectorAll('input,select').forEach(e=>{
    if(!e.id || e.id.indexOf('_goster') >= 0) return;
    if(alanModu(e.id) !== 'uygulama') return;
    if(o[e.id] === undefined) return;
    if(e.type === 'checkbox') e.checked = !!o[e.id];
    else alanaYaz(e, o[e.id]);
  });
  if(Array.isArray(o.__muk_durak) && o.__muk_durak.length)
    MUK_DURAK = o.__muk_durak.slice(0, MUK.durak_azami).map(mSayi);
  //  Çoklu asansör dizisi.  Form kurulduktan SONRA aktif olan basılır
  //  ( bkz. mukavemetKur ) — burada yalnız durum geri alınır.
  if(Array.isArray(o.__muk_asansorler) && o.__muk_asansorler.length){
    MUK_ASANSORLER = o.__muk_asansorler
      .slice(0, (MUK && MUK.asansor_azami) || 4)
      .map(x => (x && typeof x === 'object') ? x : {});
    MUK_ADET = Math.min(Math.max(1, Number(o.__muk_adet) || MUK_ASANSORLER.length),
                        MUK_ASANSORLER.length);
    MUK_AKTIF = Math.min(Math.max(0, Number(o.__muk_aktif) || 0), MUK_ADET - 1);
  }
}

const mSatir = alanlar => `<div class="satir i${alanlar.length}">${alanlar.join('')}</div>`;

/*  UYGULAMA PROJESİNİN KAPAĞI AYRI BİR MMO KİTABINDADIR — elimizde yok.
    Bu yüzden avan kapağı buraya BASILMAZ;  sunucuya yalnız dosya adı ve
    belge özellikleri için gereken proje kimliği gönderilir. */
/*  Sabitler / Ofis Standardı sekmesindeki değerler.  Avan tarafında
    avanGirdi() aynı işi yapar;  uygulama projesinin elektrik ve topraklama
    hesapları da bunları kullanır. */
/* ═════════════ UYGULAMANIN KENDİ OFİS STANDARDI ═════════════
   Avanınkinden AYRIDIR ( ön ek uof_ ).  Avan ön tasarımdır ve genel
   kabullerle çalışır;  uygulama kesin tasarımdır ve imalatçı verisi vardır.
   İkisinin aynı sayıyı tutma zorunluluğu yoktur — ama ikisi de ekranda
   durur, paftaya kaynağıyla basılır ve bilerek ayrışır.                  */
const UOF = k => 'uof_' + k;

function ofisSabitleri(){
  const o = {}, S = (MUK && MUK.sabitler) || {};
  Object.keys(S.varsayilan || {}).forEach(k=>{
    const x = v(UOF(k)); if(x !== '') o[k] = x; });
  return o;
}

function uygulamaSabitFormuKur(){
  const S = (MUK && MUK.sabitler) || {}, kutu = $('usabit_form');
  if(!kutu || !S.gruplar) return;
  const metin = new Set(S.metin || []);
  let h = '';
  (S.gruplar || []).forEach(gr=>{
    h += `<div class="bolum-bas">${kacis(gr.baslik)}`
       + (gr.aciklama ? ` <span class="ipucu">— ${kacis(gr.aciklama)}</span>` : '')
       + `</div>`;
    const alanlar = gr.alanlar.map(k=>{
      const [et, ip] = S.etiket[k] || [k, ''];
      const d = String(S.varsayilan[k]).replace('.', ',');
      //  Boş bırakılan alan varsayılanı kullanır;  yer tutucu o değeri gösterir.
      const giris = `<input id="${UOF(k)}" class="girdi" placeholder="${kacis(d)}"${metin.has(k) ? '' : ' inputmode="decimal"'}>`;
      return `<div class="alan"><label>${kacis(et)}`
        + (ip ? ` <span class="ipucu">${kacis(ip)}</span>` : '')
        + `</label>${giris}</div>`;
    });
    for(let i=0; i<alanlar.length; i+=3)
      h += `<div class="satir i3">${alanlar.slice(i, i+3).join('')}</div>`;
  });
  kutu.innerHTML = h;
}
function uygulamaSabitleriSifirla(){
  const S = (MUK && MUK.sabitler) || {};
  Object.keys(S.varsayilan || {}).forEach(k=>{ const e=$(UOF(k)); if(e) e.value=''; });
  yaz(); hesapMukavemet();
  durum('Uygulama projesinin ofis sabitleri varsayılana döndürüldü.');
}

/* ═════════════ UYGULAMANIN TABLOLARI ═════════════
   Bugüne kadar yalnız motorun içindeydiler:  hesaba giriyorlardı ama
   ekranda görünmüyorlardı.  Tablolar KOPYALANMAZ — sunucu motorun kendi
   sözlüklerinden üretir ( engine/uygulama/tablolar_gorunum.py ).       */
function uygulamaTablolariKur(){
  const kutu = $('utablolar_ic'); if(!kutu) return;
  const t = (MUK && MUK.tablolar) || [];
  kutu.innerHTML = t.map(x=>{
    const bas = x.basliklar.map(b=>`<th>${kacis(b)}</th>`).join('');
    const sat = x.satirlar.map(r=>
      `<tr>${r.map(c=>`<td>${kacis(String(c))}</td>`).join('')}</tr>`).join('');
    return `<div class="bolum-bas">${kacis(x.ad)}`
      + (x.kaynak ? ` <span class="ipucu">— ${kacis(x.kaynak)}</span>` : '') + `</div>`
      + (x.aciklama ? `<div class="yardim">${kacis(x.aciklama)}</div>` : '')
      + `<div class="kaydir"><table class="veri"><thead><tr>${bas}</tr></thead>`
      + `<tbody>${sat}</tbody></table></div>`;
  }).join('');
}

function mukavemetKimlik(){
  const al = id => ($(id)?.value || '').trim();
  return {project_title: al('mk_proje_adi'), owner: al('mk_isveren'),
          sheet_no: al('mk_pafta_no')};
}

/*  EXCEL HÜCRE ADRESİ ETİKETTE YAZILMAZ.  Bir süre her alanın yanında
    "· B132" gibi duruyordu;  hesabı yapan mühendisin işine yaramıyor, yalnız
    etiketi uzatıp okumayı zorlaştırıyordu.  Adres SÖZLEŞMEDE duruyor
    ( mukavemet_girdi.ALANLAR ) ve Excel'e yazma / Excel'den geri okuma onu
    oradan kullanmaya devam ediyor — görünümden kalkması o eşleşmeye
    dokunmaz. */
/*  ONAY ALANLARININ İKİ DÜĞMELİ GÖRÜNÜMÜ.
    { etiket , [ kapalı şıkkı , açık şıkkı ] }

    ETİKET DE DEĞİŞİR:  alanın kendi adı olumsuz kurulmuştur ( "Makine
    dairesiz" ) ve düğmelerin üstünde tekrar edince kafa karıştırıyordu —
    "Makine dairesiz" başlığı altında "Makine daireli" düğmesi.  Başlık
    SORUYU sorar ( "Makine dairesi" ), düğmeler CEVABI verir ( "Var" / "Yok" ).
    Kısa şıklar ayrıca satır sarmaz, düğmeler tek satırda durur.

    Yalnız GÖRÜNÜMdür;  alanın türü ve kaydedilen değer değişmez.           */
const IKILI_ETIKET = {
  mk_yok: { etiket: 'Makine dairesi', secenek: ['Var', 'Yok  ( MRL )'] },
};

/*  Düğmeye basılınca alttaki checkbox'ı günceller ve hesabı tetikler.
    Kutu tek doğruluk kaynağıdır;  düğmeler yalnız onu gösterir.            */
function mIkiliSec(id, deger){
  const e = $(id); if(!e) return;
  e.checked = !!deger;
  e.dispatchEvent(new Event('change', {bubbles:true}));
  mIkiliTazele();
}

/*  SERTLEŞTİRİLMEMİŞ DÜZ V KANAL SEÇTİRİLMEZ  ( TS EN 81-50 m.5.11.2.3.1.2 ).
    Sertleştirilmemiş V kanalın ALT KESİLMESİ olmalıdır.  Kanal şekli ile
    kanal işlemesi iki ayrı listedir ve birbirini görmüyordu:  kullanıcı
    ikisini ayrı ayrı değiştirip standart dışı birleşimi kurabiliyordu.
    Karşı listedeki uyumsuz seçenek KAPATILIR ve sebebi üstüne yazılır.
    Mevcut seçim SESSİZCE DEĞİŞTİRİLMEZ — o, gerçek kasnağın özelliğini
    değiştirmek olurdu;  eski bir dosyadan böyle gelirse motor açık hata verir. */
const M_KANAL_NEDEN = 'TS EN 81-50 m.5.11.2.3.1.2 — sertleştirilmemiş V kanalın alt kesilmesi olmalıdır';
function mKanalUyumu(){
  const k = $(M_ID('kanal_sekli')), i = $(M_ID('kanal_isleme'));
  if(!k || !i) return;
  const kapat = (o, kosul) => {
    o.disabled = !!kosul;
    o.title = kosul ? M_KANAL_NEDEN : '';
  };
  for(const o of i.options) kapat(o, k.value === 'V Kanal' && o.value === 'Sertleştirilmemiş');
  for(const o of k.options) kapat(o, i.value === 'Sertleştirilmemiş' && o.value === 'V Kanal');
}

/*  Checkbox nereden değişirse değişsin ( düğme · geri yükleme · test )
    düğmelerin işaretli olanı ona uydurulur.                                */
function mIkiliTazele(){
  document.querySelectorAll('#m_form .secim-ikili').forEach(k=>{
    const e = $(k.dataset.icin); if(!e) return;
    k.querySelectorAll('.secim-dg').forEach(d=>{
      const secili = (d.dataset.deger === '1') === !!e.checked;
      d.classList.toggle('secili', secili);
      d.setAttribute('aria-checked', secili ? 'true' : 'false');
    });
  });
}

function mAlan(f){
  //  PROJE GENELİ ROZETİ.  Alan asansöre değil BİNAYA aitse söylenir:  dört
  //  asansörün sekmesinde de aynı kutu görünür ve aynı değeri taşır.
  const pg = mProjeGeneliMi(f.anahtar)
    ? ` <span class="pg-rozet" title="Binaya aittir: bütün asansörlerde tek`
      + ` değer, hesaba bir kez girer">proje geneli</span>` : '';
  const et = kacis(f.etiket)
    + (f.birim && f.birim !== '—' ? ` <span class="ipucu">(${kacis(f.birim)})</span>` : '')
    + pg;
  if(f.tur === 'onay'){
    //  İKİLİ SEÇİM GÖRÜNÜMÜ.  Bazı onay alanları aslında İKİ ŞIKLI bir
    //  tercihtir ( makine daireli / dairesiz ) ve işaretsiz bir kutu
    //  "seçim yapılmadı" gibi durur.  İki düğme olarak gösterilir;  VERİ
    //  MODELİ DEĞİŞMEZ — altta gerçek bir checkbox durur, kaydetme, geri
    //  yükleme ve testler ona bakmaya devam eder.  Kutu ekrandan kalkmaz,
    //  yalnız görsel olarak saklanır ( .gorsel-gizli ):  klavye ve ekran
    //  okuyucu erişimi korunur.
    const ik = IKILI_ETIKET[f.anahtar];
    if(ik){
      const id = M_ID(f.anahtar), a = f.varsayilan ? 1 : 0;
      return `<div class="alan"><label>${kacis(ik.etiket)}${pg}</label>`
        + `<input type="checkbox" class="gorsel-gizli" id="${id}"${f.varsayilan?' checked':''}>`
        + `<div class="secim-ikili" role="group" aria-label="${kacis(ik.etiket)}"`
        + ` data-icin="${id}">`
        + ik.secenek.map((m, i)=>
            `<button type="button" class="secim-dg${i===a?' secili':''}"`
            + ` role="radio" aria-checked="${i===a}"`
            + ` data-deger="${i}" onclick="mIkiliSec('${id}',${i})">${kacis(m)}</button>`
          ).join('')
        + `</div></div>`;
    }
    return `<div class="alan"><label class="kutu-satir">`
      + `<input type="checkbox" id="${M_ID(f.anahtar)}"${f.varsayilan?' checked':''}>`
      + `<span>${kacis(f.etiket)}${pg}</span></label></div>`;
  }
  let giris;
  if(f.secenekler){
    giris = `<select id="${M_ID(f.anahtar)}" class="girdi">`
      + f.secenekler.map(o=>
          `<option value="${kacis(o)}"${o===f.varsayilan?' selected':''}>${kacis(mSayi(o))}</option>`
        ).join('') + '</select>';
  }else{
    //  Varsayılanı olmayan alan BOŞ açılır ( temel ölçüleri, kolon boyu … );
    //  "0" yazmak kullanıcıyı yanıltırdı.
    const v = (f.varsayilan===null||f.varsayilan===undefined) ? '' : mSayi(f.varsayilan);
    giris = `<input id="${M_ID(f.anahtar)}" class="girdi" value="${kacis(v)}">`;
  }
  return `<div class="alan"><label>${et}</label>${giris}</div>`;
}

/* ---- durak yükseklikleri ---- */
function mDurakKutusu(f){
  return `<div class="alan" style="grid-column:1/-1">
      <label>${kacis(f.etiket)} <span class="ipucu">(${kacis(f.birim)} — en çok ${MUK.durak_azami} durak)</span>
        ${bilgiSimgesi([
          'Her durağın kat yüksekliği. Toplamları kılavuz ray boyuna, son durağınki ise kuyu üst boşluğu ve sığınma alanı hesaplarına girer.',
          'Seyir mesafesi ve son kat yüksekliği bu listeden kendiliğinden doldurulur; elle değiştirirseniz program tutarsızlığı bildirir.'])}</label>
      <div id="m_durak_kutu"></div>
      <div class="dugmeler" style="margin-top:2px">
        <button type="button" class="dg" id="m_durak_ekle"
                onclick="mDurakEkle()">+ durak ekle</button>
        <button type="button" class="dg" id="m_durak_sil"
                onclick="mDurakSil()">− son durağı sil</button>
      </div>
    </div>`;
}

function mDurakCiz(){
  const k = $('m_durak_kutu'); if(!k) return;
  k.innerHTML = '<div class="satir i4">' + MUK_DURAK.map((d,i)=>
    `<div class="alan"><label>${i+1}. durak</label>
      <input id="m_durak_${i}" class="girdi" value="${kacis(d)}"
             oninput="mDurakYaz(${i}, this.value)"></div>`).join('') + '</div>';
  mTuretilenleriDoldur();
}

function mDurakYaz(i, deger){
  MUK_DURAK[i] = deger;
  mTuretilenleriDoldur();
}

function mDurakEkle(){
  if(MUK_DURAK.length >= MUK.durak_azami){
    durum(`En çok ${MUK.durak_azami} durak girilebilir.`, true); return;
  }
  MUK_DURAK.push(MUK_DURAK[MUK_DURAK.length-1] || '3000');
  mDurakCiz(); mukavemetPlanla();
}

function mDurakSil(){
  if(MUK_DURAK.length <= 1){ durum('En az bir durak kalmalı.', true); return; }
  MUK_DURAK.pop();
  mDurakCiz(); mukavemetPlanla();
}

/*  Seyir mesafesi ve son kat yüksekliği durak listesinden TÜRETİLİR.  Excel'de
    ikisi de elle giriliyor ve sessizce çelişebiliyordu;  burada listeden
    dolduruluyor, kullanıcı yine de üzerine yazabilir ( motor tutarsızlığı
    bildirir ). */
function mTuretilenleriDoldur(){
  const say = MUK_DURAK.map(x=>Number(String(x).replace(',', '.')))
                       .filter(x=>isFinite(x));
  if(say.length !== MUK_DURAK.length || !say.length) return;
  const son = $('m_son_kat_yuksekligi'), seyir = $('m_seyir_mesafesi');
  if(son)   son.value   = mSayi(say[say.length-1]);
  if(seyir) seyir.value = mSayi((say.reduce((a,b)=>a+b,0) - say[say.length-1]) / 1000);
}

/* ---- hesap ---- */
/*  BOŞ KABİN AĞIRLIĞI BEYAN YÜKÜNÜ İZLER.
    Beyan yükü değiştiğinde kabin ağırlığı ofis tablosundan yenilenir
    ( engine/ortak/ofis.py — avan tarafının da okuduğu tablo ).  Avandaki
    "trafik → kapasite" izlemesinin aynısıdır:  türetilen alan kaynağını
    izler, elle girilen değer beyan yükü değişmediği sürece korunur.

    TABLO TARAYICIDA TUTULMAZ.  Alan boş gönderilir, sunucu doldurur ve
    dönen değer alana yazılır;  yoksa aynı tablonun ikinci bir kopyası
    JS'de durur ve motorunkiyle ayrışırdı. */
let MUK_GK_TAZELE = false;

/* ==========================================================================
   FORM ALANLARININ TEK GEZİNTİSİ

   "Alan nedir, nasıl okunur, nasıl yazılır" bilgisi BİR YERDE durur.  Bir
   süre aynı gezinti dört ayrı yerde elle yazılıydı — hesaba gönderilecek
   girdiyi toplarken, asansör değiştirirken kaydederken, yüklerken ve
   tarayıcı kovasından geri yüklerken.  Dördü de "checkbox ise checked,
   değilse value" kuralını kendi kopyasında taşıyordu:  yeni bir alan türü
   ( radyo · çoklu seçim ) eklendiğinde birinde unutulur ve asansör
   değiştirince o alan SESSİZCE kaybolurdu.

   Ayrıca ikisi ayrışmıştı:  kovadan geri yükleme alanaYaz() kullanıyor —
   seçim kutusunda "6.5" ile "6,5"i eşleştiren ortak yardımcı — asansör
   yükleme ise ham `e.value =` yapıyordu, yani o eşleştirmeyi atlıyordu.
   ========================================================================== */

/*  Sözleşmedeki alanlar, isteğe bağlı süzgeçle.  Sıra GRUP SIRASIDIR. */
function mAlanlar(sec){
  const c = [];
  for(const gr of ((MUK && MUK.gruplar) || [])) for(const f of gr.alanlar)
    if(!sec || sec(f)) c.push(f);
  return c;
}

/*  ASANSÖRE AİT alan:  durak listesi ayrı taşınır ( __durak ), proje geneli
    alanlar binaya aittir ve asansörden asansöre kopyalanmaz. */
const M_ASANSOR_ALANI = f => f.tur !== 'liste' && !mProjeGeneliMi(f.anahtar);

/*  Tek alanın değeri.  Alan formda yoksa undefined döner — çağıran o
    anahtarı hiç yazmaz, "boş string" ile karıştırmasın. */
function mAlanOku(f){
  if(f.tur === 'liste') return MUK_DURAK.slice();
  const e = $(M_ID(f.anahtar));
  if(!e) return undefined;
  return (e.type === 'checkbox') ? e.checked : e.value;
}

/*  Tek alana değer basar.  Yazma her yerde alanaYaz() üzerinden gider. */
function mAlanYaz(f, deger){
  if(f.tur === 'liste'){
    if(!Array.isArray(deger) || !deger.length) return;
    MUK_DURAK = deger.slice();
    if($('m_durak_kutu')) mDurakCiz();
    return;
  }
  const e = $(M_ID(f.anahtar));
  if(e) alanaYaz(e, deger);
}

function mFormOku(sec){
  const g = {};
  for(const f of mAlanlar(sec)){
    const deger = mAlanOku(f);
    if(deger !== undefined) g[f.anahtar] = deger;
  }
  return g;
}

/*  Haritadaki değerleri forma basar.  Haritada OLMAYAN alana dokunulmaz —
    yeni açılan asansör, kopyalandığı asansörün değerleriyle kalır. */
function mFormaYaz(harita, sec){
  for(const f of mAlanlar(sec)){
    if(harita[f.anahtar] === undefined) continue;
    mAlanYaz(f, harita[f.anahtar]);
  }
  mKanalUyumu();
}

function mukavemetGirdi(){
  const g = mFormOku();
  if(MUK_GK_TAZELE) g.kabin_agirligi = '';      // sunucu tablodan doldursun
  return g;
}

let mZaman = null;
/*  MALZEME SEÇİNCE DERİNLİK KUTUSU DOLAR — hesabı bu doldurmaz.
    Motor yalnız kutudaki sayıyı okur ( TS EN 81-50 Ek C.2.2 karşı ağırlığın
    KENDİ ölçüsünü ister ).  Ama malzeme seçince ekranda hiçbir şeyin
    değişmemesi sessiz bir tuzaktı:  eskiden derinliği malzeme belirliyordu,
    "Pik Döküm" seçen biri 100 mm ile hesaplandığını sanmaya devam ederdi. */
function mMalzemeDerinligi(){
  const tablo = (MUK && MUK.malzeme_derinligi) || {};
  const m = $(M_ID('agirlik_malzemesi')), d = $(M_ID('agirlik_derinligi'));
  if(!m || !d) return;
  const v = tablo[m.value];
  if(v !== undefined && v !== null) d.value = mSayi(v);
}

/*  MAKİNE DAİRESİ ÖLÇÜLERİ MRL'DE GİZLENİR.
    Avan sayfası bunu zaten yapıyordu ( a_mk_olculer );  uygulama sayfasında
    kutular MRL işaretliyken de duruyordu.  Ortada duran ve doldurulabilen
    iki kutu, "makine dairesi hesabı yapılacak" izlenimi veriyor;  hesap ise
    -doğru olarak- MRL'de o bölümü hiç üretmiyor.  Kutuyu gizlemek çelişkiyi
    kaynağında bitirir.  Değer SİLİNMEZ:  MRL kaldırılırsa geri gelir. */
function mMakineDairesiKutulari(){
  const k = $(M_ID('mk_yok'));
  if(!k) return;
  //  SINIF KULLANILIR, [hidden] DEĞİL.  Arama süzgeci ( mAramaUygula ) ve
  //  "tüm grupları aç" ( mTumGruplariAc ) [hidden] üzerinde çalışır;  kural
  //  gizlemesi de aynı niteliği kullanırsa ikisi birbirini siler — grupları
  //  açmak MRL'de gizlenmesi gereken kutuyu geri getiriyordu.
  const gizle = (ad, nezaman) => {
    const e = $(M_ID(ad));
    const kap = e && (e.closest('.alan') || e);
    if(kap) kap.classList.toggle('kural-disi', !!nezaman);
  };
  //  Ölçüler MRL'de gizlenir — makine dairesi yoksa hesap da yok.
  for(const a of ['mk_uzunluk', 'mk_genislik']) gizle(a, k.checked);
  //  MAKİNE YÜKÜNÜN YOLU İSE TERSİ:  yalnız MRL'de sorulur.  Makine dairesi
  //  varsa makine kendi kaidesinde durur ( bölüm 2 ) ve yükü raya bindirmek
  //  onu İKİ KEZ saymak olur.  Motor bu seçimi zaten makine daireli projede
  //  yok sayar;  kutuyu gizlemek kullanıcıyı yanıltmamak içindir.
  for(const a of ['makine_raya_biniyor', 'raya_binen_yuk']) gizle(a, !k.checked);
}

function mukavemetPlanla(hedef){
  if(hedef && hedef.id === 'm_beyan_yuku') MUK_GK_TAZELE = true;
  if(hedef && hedef.id === M_ID('agirlik_malzemesi')) mMalzemeDerinligi();
  mMakineDairesiKutulari();
  mIkiliTazele();
  mKanalUyumu();
  yaz();                              // girdiler tarayıcıda saklansın
  clearTimeout(mZaman);
  mZaman = setTimeout(hesapMukavemet, 220);
}

async function hesapMukavemet(){
  if(!MUK) return;
  const sira = ++ISTEK.mukavemet;
  try{
    const c = await (await fetch('/api/uygulama/coklu', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify(mukavemetIstek())})).json();
    if(sira !== ISTEK.mukavemet) return;      // daha yeni istek var
    SON.mc = c;
    //  SON.m AKTİF ASANSÖRÜN sonucudur.  Tek asansörlük kodun ( ve testlerin )
    //  baktığı yer burasıdır;  çoklu sonuç SON.mc'de durur.
    const aktif = (c.asansorler || [])[MUK_AKTIF] || (c.asansorler || [])[0] || c;
    SON.m = aktif;
    if(MUK_GK_TAZELE){
      MUK_GK_TAZELE = false;
      const gk = $('m_kabin_agirligi');
      const yeni = aktif.girdi && aktif.girdi.kabin_agirligi;
      if(gk && yeni !== null && yeni !== undefined){ gk.value = mSayi(yeni); yaz(); }
    }
    cizMukavemet(aktif);
    //  Asansör listesi YALNIZ PROJE sekmesindedir.  Bir süre her asansörün
    //  sonuç panelinin başına da basılıyordu;  ASANSÖR 1 sekmesinde "1 · 2"
    //  listesi görmek, o sekmenin zaten 1 nolu asansöre ait olduğunu bile
    //  bile tekrar söylemektir — hangi sekmede olduğun üstteki şeritte yazılı.
    mProjeOzetiCiz(c);
    mProjeGeneliCiz(c);
    //  Genel rozet PROJE sekmesindedir:  asansör sekmelerininki kendilerine
    //  aittir ( bkz. mAsansorSekmeleriTazele ).
    const hatali = !c.aktif;
    sekmeRozeti('uygproje', hatali, hatali ? 0 : (aktif.uyarilar||[]).length);
    mAsansorSekmeleriTazele();
  }catch(e){
    $('m_sonuc').innerHTML =
      `<div class="kart-ic"><div class="uyari kirmizi">Bağlantı hatası: ${kacis(e)}</div></div>`;
  }
}

function cizMukavemet(r){
  let h = `<div class="pafta-bas"><h2>ASANSÖR UYGULAMA PROJESİ HESAPLARI</h2>
    <div class="alt">TS EN 81-20 · TS EN 81-50 · TS 12385-5 · ISO 7465 · MMO 208
      · IEEE Std 80 · IEC 60364-5-52</div>
    </div><div class="kart-ic">`;
  if(!r.aktif){
    h += (r.hata||['Hesap yapılamadı.']).map(x=>
      `<div class="uyari kirmizi">${kacis(x)}</div>`).join('');
    $('m_sonuc').innerHTML = h + '</div>';
    return;
  }
  (r.uyarilar||[]).forEach(u=>h+=`<div class="uyari ${uyariSinifi(u)}">${kacis(u)}</div>`);
  const o = r.ozet || {};
  h += '<div class="olcut">'
     + kutu('N — Hesaplanan motor gücü', tr(o.N_hesap), 'kW', o.motor_uygun?'ok':'hata')
     + kutu('Kabin alanı', tr(o.kabin_alani), 'm²')
     + kutu('Kılavuz ray boyu', tr(o.ray_boyu), 'm')
     + (o.P_kurulu!=null ? kutu('Asansörün kurulu gücü', trn(o.P_kurulu,0), 'W') : '')
     + (o.eps!=null ? kutu('ε — Gerilim düşümü', tr(o.eps,3), '%', o.eps_uygun?'ok':'hata') : '')
     + (o.Re!=null ? kutu('Re — Topraklama', tr(o.Re,3), 'Ω', o.topraklama_uygun?'ok':'hata') : '')
     /* hüküm MOTORDAN gelir ( mukavemet.genel_hukum ) — burada yeniden
        kurulursa PDF ile ayrışır */
     + kutu('Sonuç', o.genel_sonuc_kisa || (o.tumu_uygun?'UYGUN':'UYGUN DEĞİL'), '', o.tumu_uygun?'ok':'hata')
     + '</div>';

  /* bölüm sonuçları — hangi bölüm takıldı, bir bakışta görünsün */
  h += `<div class="serit"><span>BÖLÜM SONUÇLARI</span>
        <span class="kaynak">${(r.bolumler||[]).length} hesap bölümü</span></div>
        <div class="kaydir"><table class="veri"><tr><th>Bölüm</th><th>Kaynak</th><th>Sonuç</th></tr>`;
  (r.bolumler||[]).forEach(b=>{
    const sn = b.sonuc || {};
    const sinif = sn.uygun === true ? 'ok' : (sn.uygun === false ? 'hata' : '');
    //  Bölüm satırı GİRDİLERİNE bir kısayoldur:  revizyonda insan "4. bölüm
    //  kaldı" diye düşünür ve doğrudan onun girdilerini arar.
    //  BÖLÜMÜ KİMLİĞİYLE TANIYORUZ.  Eskiden başlıktan numara ayıklanıyordu
    //  ( "4 - ASKI…" → "4" );  numara projeye göre kaydığı için proje geneli
    //  bölümler hiç eşlenemiyordu.  Kimlik bölümün doğduğu yerde verilir.
    const kim = b.kimlik || '';
    const gidilir = mBolumGruplari(kim).join('  ·  ');
    h += `<tr${gidilir ? ` class="m-gidilir" onclick="mGirdiyeGit('${kacis(kim)}')"
              title="Girdilerine git — ${kacis(gidilir)}"` : ''}>
            <td class="etiket">${kacis(b.baslik)}</td>
            <td>${kacis(b.kaynak||'')}</td>
            <td class="${sinif}">${kacis(sn.metin||'—')}</td></tr>`;
  });
  h += '</table></div>';

  /* kuyu tabanı yükleri — inşaat projesine bildirilecek değerler */
  if(o.FKR != null){
    h += `<div class="serit"><span>KUYU TABANINA GELEN YÜKLER</span>
          <span class="kaynak">inşaat projesine bildirilir</span></div>
          <div class="olcut">`
       + kutu('FKR — Kabin rayları', trn(o.FKR,0), 'N')
       + kutu('FAR — Ağırlık rayları', trn(o.FAR,0), 'N')
       + kutu('Fkt — Kabin tamponları', trn(o.Fkt,0), 'N')
       + kutu('Fat — Ağırlık tamponları', trn(o.Fat,0), 'N')
       + '</div>';
  }

  (r.bolumler||[]).forEach(b=>{ h += bolumCiz(b); });
  $('m_sonuc').innerHTML = h + '</div>';
}


/* ═══════════════════════════════════════════════════════════════════
   BAŞLATMA  —  en sonda, üç dosya da yüklendikten sonra
   ═══════════════════════════════════════════════════════════════════ */
kur();


/* ==========================================================================
   GİRDİ AKORDEONU
   Kapalı grup DOM'da durur, yalnız görünmez.  mukavemetGirdi() alanları
   id ile okur;  açık/kapalı olması okunan değeri DEĞİŞTİRMEZ.
   ========================================================================== */
/*  i  tek bir grup numarası ya da NUMARA DİZİSİ olabilir.  Dizi verilince
    hepsi birden açılır ve İLKİNE kaydırılır:  bir hesap bölümü iki gruptan
    besleniyorsa ( ör. 4. bölüm — halat + kasnak ) ikisini de görmek gerekir.
    Öteki bütün gruplar yine kapanır;  akordeon listeye dönüşmez. */
function mGrupAc(i, sessiz){
  const ac = (Array.isArray(i) ? i : [i]).map(Number).filter(x=>x >= 0);
  if(!ac.length) return;
  i = ac[0];
  const ara = $('m_ara');
  if(ara && ara.value){ ara.value = ''; }        // arama açıkken gruba geçilirse temizle
  document.querySelectorAll('#m_form .m-grup').forEach(gr=>{
    const bu = ac.includes(Number(gr.dataset.grup));
    gr.classList.toggle('acik', bu);
    gr.querySelector('.m-grup-ic').hidden = !bu;
    gr.querySelector('.m-grup-ok').textContent = bu ? '▾' : '▸';
    //  Arama tek tek alanları gizlemiş olabilir — gruba dönerken geri aç.
    gr.querySelectorAll('.alan[hidden]').forEach(a=>{ a.hidden = false; });
    //  ve sayaç aramanın bıraktığı değerde kalmasın
    const sy = gr.querySelector('.m-grup-adet');
    if(sy) sy.textContent = sy.dataset.toplam;
  });
  try{ localStorage.setItem('m_grup', String(i)); }catch(e){}
  if(!sessiz){
    const gr = document.querySelector(`#m_form .m-grup[data-grup="${i}"]`);
    if(gr) gr.scrollIntoView({block:'nearest', behavior:'smooth'});
  }
}

/*  BAŞLIĞA TIKLAMA AÇ/KAPADIR.  Açık gruba yeniden tıklamak eskiden hiçbir
    şey yapmıyordu ( mGrupAc her zaman AÇIYORDU ) — üç kez tıklayıp "bozuk mu"
    diye bakılıyordu.  Kapatmak son seçili grubu DEĞİŞTİRMEZ:  sayfa
    yenilendiğinde aynı grup yine açık gelir, hepsi kapalı bir form değil. */
function mGrupDegistir(i){
  const gr = document.querySelector(`#m_form .m-grup[data-grup="${i}"]`);
  if(gr && gr.classList.contains('acik')){ mGruplariKapat(); return; }
  mGrupAc(i);
}

function mGruplariKapat(){
  const ara = $('m_ara');
  if(ara && ara.value){ ara.value = ''; }
  document.querySelectorAll('#m_form .m-grup').forEach(gr=>{
    gr.classList.remove('acik');
    gr.querySelector('.m-grup-ic').hidden = true;
    gr.querySelector('.m-grup-ok').textContent = '▸';
    gr.querySelectorAll('.alan[hidden]').forEach(a=>{ a.hidden = false; });
    const sy = gr.querySelector('.m-grup-adet');
    if(sy) sy.textContent = sy.dataset.toplam;
  });
}

/*  BÜTÜN grupları açar.  Otomatik testler alanları id ile doldurur;
    kapalı gruptaki alan "görünür değil" sayılıp doldurulamaz. */
function mTumGruplariAc(){
  document.querySelectorAll('#m_form .m-grup').forEach(gr=>{
    gr.classList.add('acik');
    gr.querySelector('.m-grup-ic').hidden = false;
    gr.querySelector('.m-grup-ok').textContent = '▾';
    gr.querySelectorAll('.alan[hidden]').forEach(a=>{ a.hidden = false; });
    const sy = gr.querySelector('.m-grup-adet');
    if(sy) sy.textContent = sy.dataset.toplam;
  });
}

/*  Alan etiketinde geçen metne göre süzer;  eşleşme olan gruplar açılır.
    Boşaltılınca son seçili gruba dönülür. */
function mAramaUygula(){
  const q = ($('m_ara').value || '').trim().toLocaleLowerCase('tr');
  if(!q){
    let i = 0; try{ i = Number(localStorage.getItem('m_grup')) || 0; }catch(e){}
    mGrupAc(i, true);
    return;
  }
  document.querySelectorAll('#m_form .m-grup').forEach(gr=>{
    let bulunan = 0;
    gr.querySelectorAll('.alan').forEach(a=>{
      //  Kural gereği kapalı alan aramada da sayılmaz:  görünmeyen bir alanı
      //  "1 sonuç" diye göstermek kullanıcıyı boş yere gruba sokar.
      const kural = a.classList.contains('kural-disi');
      const es = !kural && (a.textContent || '').toLocaleLowerCase('tr').includes(q);
      a.hidden = !es;
      if(es) bulunan++;
    });
    gr.classList.toggle('acik', bulunan > 0);
    gr.querySelector('.m-grup-ic').hidden = bulunan === 0;
    gr.querySelector('.m-grup-ok').textContent = bulunan ? '▾' : '▸';
    gr.querySelector('.m-grup-adet').textContent = bulunan || gr.querySelectorAll('.alan').length;
  });
}

/*  SONUÇTAN GİRDİYE ATLAMA.  Sonuç tablosundaki bölüme tıklanınca o bölümü
    besleyen girdi grubu açılır.  Eşleme motordan gelir
    ( mukavemet_girdi.BOLUM_GRUBU ) — arayüzde tutulsaydı motor değişince
    sessizce bayatlardı. */
function mGirdiyeGit(kimlik){
  if(!MUK || !MUK.bolum_grubu) return;
  const no = mBolumGruplari(kimlik).map(ad=>MUK.gruplar.findIndex(g=>g.ad === ad))
                                   .filter(i=>i >= 0);
  if(!no.length) return;
  mGrupAc(no);
}

/*  Bir bölümü besleyen grup adları.  Anahtar bölümün KİMLİĞİDİR
    ( "aski_halatlari" ) — başlıktaki numara değil.  Motor eskiden tek ad
    döndürüyordu;  dizi gelmeyen ( eski ) sunucuya karşı ikisi de kabul edilir. */
function mBolumGruplari(kimlik){
  const g = (MUK && MUK.bolum_grubu || {})[String(kimlik || '')];
  return !g ? [] : (Array.isArray(g) ? g : [g]);
}


/* ==========================================================================
   ÇOKLU ASANSÖR
   Form tek kopyadır;  aktif asansörün değerleri onda durur.  Asansör
   değişince form MUK_ASANSORLER'e kaydedilir ve ötekinin değerleri yüklenir.
   Proje geneli alanlar ( topraklama · makine dairesi ) TAŞINMAZ — binaya
   aittir, dört asansörde de aynıdır.
   ========================================================================== */
function mAsansorSekmeleriTazele(){
  const k = $('m_asansor_sekmeleri'); if(!k) return;
  if(MOD !== 'uygulama'){ k.innerHTML = ''; return; }
  let h = '';
  for(let i = 0; i < MUK_ADET; i++){
    const ad = ((MUK_ASANSORLER[i] || {}).asansor_adi || '').trim();
    const etkin = i === MUK_AKTIF && !$('s-mukavemet').hidden;
    //  ROZET ASANSÖRE ÖZELDİR.  sekmeRozeti() querySelector ile İLK eşleşeni
    //  bulur;  dört sekmede hepsine aynı rozeti basardı ve hangi asansörün
    //  kaldığı görünmezdi.  Her sekme kendi sonucundan okur.
    const d = ((SON.mc && SON.mc.ozet && SON.mc.ozet.asansorler) || [])[i];
    let rozet = '';
    if(d && d.aktif === false)
      rozet = `<span class="sekme-rozet kirmizi" title="Hesap yapılamadı">!</span>`;
    else if(d && d.tumu_uygun === false)
      rozet = `<span class="sekme-rozet kirmizi" title="Bir ya da daha çok bölüm uygun değil">✕</span>`;
    h += `<button class="sekme${etkin ? ' etkin' : ''}" data-sekme="mukavemet"
                  data-asansor="${i}" onclick="mAsansorSekmesi(${i})"
                  title="${kacis(ad || (i + 1) + ' nolu asansör')}"
          >ASANSÖR ${i + 1}${ad ? ' · ' + kacis(ad.slice(0, 12)) : ''}${rozet}</button>`;
  }
  k.innerHTML = h;
}

/*  Sekmeye tıklamak hem gövdeyi açar hem aktif asansörü değiştirir.
    Dört ayrı sayfa yerine TEK gövde kullanılır ( 4 × 86 alanlık DOM olmasın );
    sekmeler yalnız hangi asansörün formda olduğunu belirler. */
function mAsansorSekmesi(i){
  if(i >= MUK_ADET) i = 0;
  const gecis = i !== MUK_AKTIF;
  if(gecis){ mAsansorKaydet(); MUK_AKTIF = i; mAsansorYukle(i); }
  sekmeGoster('mukavemet');
  mAsansorSekmeleriTazele();
  if(gecis){ yaz(); hesapMukavemet(); }
}

/*  ADET SEÇİMİ.  Azaltmak veriyi SİLMEZ:  haritalar dizide kalır, yalnız
    hesaba ve paftaya girmezler.  3→2→3 yapan mühendis girdilerini geri bulur.
    Artırırken eksik haritalar 1 NOLU ASANSÖRÜN kopyası olarak açılır — bir
    binanın asansörleri çoğunlukla benzerdir, sıfırdan 86 alan doldurtmak
    işkence olurdu. */
function mAdetDegisti(n){
  const azami = (MUK && MUK.asansor_azami) || 4;
  n = Math.max(1, Math.min(azami, parseInt(n, 10) || 1));
  mAsansorKaydet();
  while(MUK_ASANSORLER.length < n){
    const kopya = JSON.parse(JSON.stringify(MUK_ASANSORLER[0] || {}));
    kopya.asansor_adi = '';               // ad kopyalanmaz, karışmasın
    MUK_ASANSORLER.push(kopya);
  }
  MUK_ADET = n;
  if(MUK_AKTIF >= MUK_ADET){ MUK_AKTIF = MUK_ADET - 1; mAsansorYukle(MUK_AKTIF); }
  if($('m_adet')) $('m_adet').value = String(n);
  mAsansorSekmeleriTazele();
  yaz();
  hesapMukavemet();
}

function mAsansorKaydet(){
  if(!MUK || !Array.isArray(MUK_ASANSORLER) || !MUK_ASANSORLER[MUK_AKTIF]) return;
  const d = mFormOku(M_ASANSOR_ALANI);
  d.__durak = (typeof MUK_DURAK !== 'undefined' ? MUK_DURAK : []).slice();
  MUK_ASANSORLER[MUK_AKTIF] = d;
}

function mAsansorYukle(i){
  const d = MUK_ASANSORLER[i]; if(!d) return;
  mFormaYaz(d, M_ASANSOR_ALANI);
  if(Array.isArray(d.__durak) && d.__durak.length){
    MUK_DURAK = d.__durak.slice();
    if($('m_durak_kutu')) mDurakCiz();
  }
}

function mAsansorSec(i){
  if(i < 0 || i >= MUK_ADET) return;
  mAsansorSekmesi(i);
}



/*  Sunucuya gidecek istek:  bütün asansörler + proje geneli.
    Aktif asansör formdan TAZE okunur;  ötekiler haritadan gelir. */
function mukavemetIstek(){
  mAsansorKaydet();
  const pg = mFormOku(f => mProjeGeneliMi(f.anahtar));
  //  Adedin ÜSTÜNDEKİ haritalar dizide durur ama hesaba GİRMEZ.
  const asansorler = MUK_ASANSORLER.slice(0, MUK_ADET).map(d=>{
    const g = {...d};
    delete g.__durak;
    g.durak_yukseklikleri = (d.__durak || []).slice();
    return g;
  });
  //  Boş kabin kütlesi sunucudan tazelenecekse aktif asansörde boşaltılır.
  if(MUK_GK_TAZELE && asansorler[MUK_AKTIF]) asansorler[MUK_AKTIF].kabin_agirligi = '';
  return {asansorler, proje_geneli: pg, sabitler: ofisSabitleri()};
}


/*  PROJE GENELİ HESAPLAR.  Temel topraklama ve makine dairesi aydınlatması
    binaya aittir;  motor bunları her asansörden ayırıp tek listede döndürür
    ( hesap.hesapla_coklu ) ve pafta en sona basar.  Ekranda da asansör
    sekmelerinde değil, PROJE sekmesinde bir kez görünürler. */
function mProjeGeneliCiz(c){
  const kutu = $('p_geneli'); if(!kutu) return;
  const bolumler = (c && c.proje_geneli) || [];
  if(!bolumler.length){ kutu.innerHTML = ''; kutu.parentElement.hidden = true; return; }
  kutu.parentElement.hidden = false;
  const o = (c.ozet || {});
  let h = `<div class="kart-ic"><div class="serit"><span>PROJE GENELİ HESAPLAR</span>
             <span class="kaynak">${bolumler.length} bölüm · bütün asansörler için bir kez</span></div>
           <div class="uyari ${o.proje_geneli_uygun === false ? 'kirmizi' : 'mavi'}"
                style="margin:0 0 12px">Temel topraklama ve makine dairesi
             aydınlatması <b>binaya</b> aittir, asansöre değil: projedeki
             ${o.adet || 1} asansör için bir kez hesaplanır ve paftanın
             <b>en sonunda</b> bir kez basılır.</div>`;
  bolumler.forEach(b=>{ h += bolumCiz(b); });
  kutu.innerHTML = h + '</div>';
}

/*  PROJE sekmesinin sağ sütunu:  bütün asansörlerin durumu bir arada.
    Ayrıntı asansör sekmelerinde;  burada yalnız "hangisi kaldı" görünür. */
function mProjeOzetiCiz(c){
  const kutu = $('p_ozet'); if(!kutu) return;
  if(!c || !c.asansorler){ kutu.innerHTML = ''; return; }
  const liste = (c.ozet && c.ozet.asansorler) || [];
  let h = `<div class="kart-ic"><div class="serit"><span>PROJE ÖZETİ</span>
             <span class="kaynak">${liste.length} asansör</span></div>
           <div class="kaydir"><table class="veri">
             <tr><th>No</th><th>Asansör</th><th>N ( kW )</th><th>Sonuç</th></tr>`;
  liste.forEach(a=>{
    const sinif = a.aktif === false ? 'hata'
                : (a.tumu_uygun === true ? 'ok' : (a.tumu_uygun === false ? 'hata' : ''));
    const metin = a.aktif === false ? 'HESAP YAPILAMADI'
                : (a.genel_sonuc || (a.tumu_uygun ? 'UYGUNDUR.' : 'UYGUN DEĞİLDİR'));
    h += `<tr class="m-gidilir" onclick="mAsansorSec(${a.no - 1})"
              title="${kacis(a.tanim || '')} sekmesine git">
            <td class="etiket">${a.no}</td><td>${kacis(a.tanim || '')}</td>
            <td>${a.N_hesap == null ? '—' : tr(a.N_hesap)}</td>
            <td class="${sinif}">${metin}</td></tr>`;
  });
  kutu.innerHTML = h + '</table></div></div>';
}
