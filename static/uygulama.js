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
  //  ORTAK GİRDİ UYARISI.  Kullanıcı "elektrik hesabının kabin ölçüsünü
  //  nereye gireceğim" diye aramasın:  bu değerlerin mukavemet alanlarından
  //  geldiği açıkça yazılır.
  if((MUK.ortak_kopru||[]).length){
    h += `<div class="uyari mavi" style="margin:0 0 12px">
      <b>Ortak girdiler bir kez girilir.</b> Elektrik ve topraklama hesapları
      aşağıdaki değerleri mukavemet alanlarından alır — ikinci kez sorulmaz:
      <div class="satir2" style="margin-top:6px">`
      + MUK.ortak_kopru.map(k=>
          `${kacis(k.mukavemet)} <b>→</b> ${kacis(k.avan)}`).join(' &nbsp;·&nbsp; ')
      + '</div></div>';
  }
  for(const g of MUK.gruplar){
    h += `<div class="bolum-bas">${kacis(g.ad)}</div>`;
    let acik = [];
    for(const f of g.alanlar){
      if(f.tur === 'liste'){
        //  Durak yükseklikleri kendi düzenleyicisini ister
        if(acik.length){ h += mSatir(acik); acik = []; }
        h += mDurakKutusu(f);
        continue;
      }
      acik.push(mAlan(f));
      if(acik.length === 2){ h += mSatir(acik); acik = []; }
    }
    if(acik.length) h += mSatir(acik);
  }
  $('m_form').innerHTML = h;
  //  Varsayılan durak listesi
  const d = MUK.gruplar.flatMap(g=>g.alanlar).find(f=>f.tur==='liste');
  MUK_DURAK = (d && d.varsayilan ? d.varsayilan : [3000]).map(mSayi);
  mukavemetGeriYukle();
  mDurakCiz();
  hesapMukavemet();
}

/*  Form SONRADAN kurulduğu için açılıştaki uygula() bu alanları bulamaz;
    saklanan değerler burada, form ayağa kalktıktan sonra yerine oturur.
    Yoksa uygulama projesi her açılışta varsayılanlara dönüyordu. */
function mukavemetGeriYukle(){
  let o; try{ o = JSON.parse(localStorage.getItem(ANAHTAR)||'null'); }catch(e){ o = null; }
  if(!o) return;
  for(const gr of MUK.gruplar) for(const f of gr.alanlar){
    if(f.tur === 'liste') continue;
    const e = $(M_ID(f.anahtar));
    if(!e || o[e.id] === undefined) continue;
    if(e.type === 'checkbox') e.checked = !!o[e.id];
    else if(o[e.id] !== '') alanaYaz(e, o[e.id]);
  }
  if(Array.isArray(o.__muk_durak) && o.__muk_durak.length)
    MUK_DURAK = o.__muk_durak.slice(0, MUK.durak_azami).map(mSayi);
}

const mSatir = alanlar => `<div class="satir i${alanlar.length}">${alanlar.join('')}</div>`;

/*  UYGULAMA PROJESİNİN KAPAĞI AYRI BİR MMO KİTABINDADIR — elimizde yok.
    Bu yüzden avan kapağı buraya BASILMAZ;  sunucuya yalnız dosya adı ve
    belge özellikleri için gereken proje kimliği gönderilir. */
/*  Sabitler / Ofis Standardı sekmesindeki değerler.  Avan tarafında
    avanGirdi() aynı işi yapar;  uygulama projesinin elektrik ve topraklama
    hesapları da bunları kullanır. */
function ofisSabitleri(){
  const o = {};
  Object.keys((SEC && SEC.sabit_b) || {}).forEach(k=>{
    const x = v('sb_'+k); if(x!=='') o[k] = x; });
  Object.keys((SEC && SEC.ofis_varsayilan) || {}).forEach(k=>{
    const x = v('of_'+k); if(x!=='') o[k] = x; });
  return o;
}

function mukavemetKimlik(){
  const al = id => ($(id)?.value || '').trim();
  return {project_title: al('mk_proje_adi'), owner: al('mk_isveren'),
          sheet_no: al('mk_pafta_no')};
}

function mAlan(f){
  const et = kacis(f.etiket)
    + (f.birim && f.birim !== '—' ? ` <span class="ipucu">(${kacis(f.birim)})</span>` : '')
    + (f.hucre ? `<span class="ipucu" style="opacity:.55"> · ${kacis(f.hucre)}</span>` : '');
  if(f.tur === 'onay'){
    return `<div class="alan"><label class="kutu-satir">`
      + `<input type="checkbox" id="${M_ID(f.anahtar)}"${f.varsayilan?' checked':''}>`
      + `<span>${kacis(f.etiket)}</span></label></div>`;
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
function mukavemetGirdi(){
  const g = {};
  for(const gr of MUK.gruplar) for(const f of gr.alanlar){
    if(f.tur === 'liste'){ g[f.anahtar] = MUK_DURAK.slice(); continue; }
    const e = $(M_ID(f.anahtar));
    if(e) g[f.anahtar] = (e.type === 'checkbox') ? e.checked : e.value;
  }
  return g;
}

let mZaman = null;
function mukavemetPlanla(){
  yaz();                              // girdiler tarayıcıda saklansın
  clearTimeout(mZaman);
  mZaman = setTimeout(hesapMukavemet, 220);
}

async function hesapMukavemet(){
  if(!MUK) return;
  const sira = ++ISTEK.mukavemet;
  try{
    const r = await (await fetch('/api/uygulama', {method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({girdiler: mukavemetGirdi(),
                            sabitler: ofisSabitleri()})})).json();
    if(sira !== ISTEK.mukavemet) return;      // daha yeni istek var
    SON.m = r;
    cizMukavemet(r);
    const hatali = !r.aktif;
    sekmeRozeti('mukavemet', hatali, hatali ? 0 : (r.uyarilar||[]).length);
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
     + kutu('Sonuç', o.tumu_uygun?'UYGUN':'UYGUN DEĞİL', '', o.tumu_uygun?'ok':'hata')
     + '</div>';

  /* bölüm sonuçları — hangi bölüm takıldı, bir bakışta görünsün */
  h += `<div class="serit"><span>BÖLÜM SONUÇLARI</span>
        <span class="kaynak">${(r.bolumler||[]).length} hesap bölümü</span></div>
        <div class="kaydir"><table class="veri"><tr><th>Bölüm</th><th>Kaynak</th><th>Sonuç</th></tr>`;
  (r.bolumler||[]).forEach(b=>{
    const sn = b.sonuc || {};
    const sinif = sn.uygun === true ? 'ok' : (sn.uygun === false ? 'hata' : '');
    h += `<tr><td class="etiket">${kacis(b.baslik)}</td>
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
