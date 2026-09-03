/* ═══════════════════════════════════════════════════════════════════
   ASANSÖR AVAN HESAPLAMA PROGRAMI  —  arayüz
   ═══════════════════════════════════════════════════════════════════ */
let SEC = {};                 // sunucudan gelen seçenekler / tablolar
let SON = {t:null, c:null, a:null};
let TRAFIK_ADET = 1;          // 1 → tek hesap (adet hesaplanır) · 2-4 → grup kontrolü
let AVAN_EK = 0;              // avanda TRAFİK GRUBUNA girmeyen asansör adedi (yük/sedye)
let AVAN_OTO = {};            // kapasite/hızı trafikten OTOMATİK gelen asansörler
let AVAN_TRF = {};            // her asansöre en son YANSITILAN trafik değeri
const $  = id => document.getElementById(id);
const el = (t,s,h)=>{const e=document.createElement(t); if(s)e.className=s; if(h!=null)e.innerHTML=h; return e;};

/* ---------------------------------------------------------- biçimleme */
function tr(x, d=2){
  if(x===null||x===undefined||x==='') return '—';
  if(typeof x==='string') return x;
  if(!isFinite(x)) return '—';
  return Number(x).toLocaleString('tr-TR',{minimumFractionDigits:d, maximumFractionDigits:d});
}
function trn(x, d=2){
  if(x===null||x===undefined||x==='') return '—';
  if(typeof x==='string') return x;
  if(!isFinite(x)) return '—';
  return Math.abs(x-Math.round(x))<1e-9 ? tr(Math.round(x),0) : tr(x,d);
}
const kacis = s => String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');

function durum(msg, hata){
  const d=$('durum'); d.textContent=msg; d.className='durum gorunur'+(hata?' hata':'');
  clearTimeout(d._t); d._t=setTimeout(()=>d.className='durum',2600);
}

/* ---------------------------------------------------------- sekmeler */
/* Trafik hesabı TEK sekmedir; asansör adedine göre iki gövdeden biri
   gösterilir:  1 asansör → #s-trafik (adet hesaplanır),
                2-4       → #s-coklu  (grup kontrolü).
   İkisi de "trafik" sekmesine aittir. */
function sekmeGoster(ad){
  document.querySelectorAll('.sekme').forEach(x=>
    x.classList.toggle('etkin', x.dataset.sekme===ad));
  document.querySelectorAll('.sayfa').forEach(s=>s.hidden=true);
  //  Trafik ARTIK TEK GÖVDEDİR ( #s-coklu ) — 1..4 asansör aynı formda
  //  tanımlanır, yöntemi program veriden çıkarır.
  $('s-' + (ad==='trafik' ? 'coklu' : ad)).hidden=false;
  window.scrollTo({top:0,behavior:'instant'});
}
document.querySelectorAll('.sekme').forEach(b=>b.onclick=()=>sekmeGoster(b.dataset.sekme));
function katla(bas, hedef){
  bas.classList.toggle('kapali');
  $(hedef).style.display = bas.classList.contains('kapali') ? 'none' : '';
}

/* ------------------------------------------------- trafik: asansör adedi */
/*  Tek ve çoklu hesap AYNI SORUYU sormaz:
      1 asansör  →  "yeter mi, yetmiyorsa kaç adet gerekir?"  (HESAPLAMA → PAFTA)
      2-4        →  "bu grup yeterli mi?"                     (ÇOKLU → PAFTA-COKLU)
    Bu yüzden iki motor yolu da korunur; kullanıcı yalnız adedi seçer.
    Ortak bina girdileri iki gövde arasında aynalanır, hiçbir şey kaybolmaz. */
const TRAFIK_ORTAK = ['bina_tipi','bina_yuksekligi','yapi_yuksekligi','N','h','bodrum',
                      'hizli1','hizli2','manuel_k','manuel_V'];

function adetDugmeleriKur(){
  const kt=$('adet_dugmeler_c');
  if(kt) kt.innerHTML=[1,2,3,4].map(n=>
      `<button type="button" class="adet-dg${n===TRAFIK_ADET?' secili':''}"
        onclick="trafikAdedi(${n})">${n}</button>`).join('');

  /* Avan sekmesindeki adet seçici — trafik adedinin ALTINA inemez, çünkü
     trafik grubundaki her asansörün elektrik hesabı da yapılmalıdır. */
  const ka=$('adet_dugmeler_a');
  if(ka){
    const taban=avanTaban(), n=avanAdedi();
    ka.innerHTML=[1,2,3,4].map(x=>
      `<button type="button" class="adet-dg${x===n?' secili':''}${x<taban?' kilitli':''}"
        ${x<taban?`title="Trafik hesabı ${taban} asansör veriyor"`:''}
        onclick="avanAdediSec(${x})">${x}</button>`).join('');
    const aa=$('a_adet_aciklama');
    if(aa) aa.textContent = n>taban
      ? `${taban} asansör trafik grubundan  ·  ${n-taban} adet trafik grubu dışı ( yük / sedye )`
      : `Trafik hesabıyla eşitlendi — ${n} asansör`;
  }
}

/*  Adet artık YÖNTEM değil, VERİ:  kaç asansör tanımlandığını söyler.
    Kapanan kolonun DEĞERİ SİLİNMEZ, yalnız gizlenir — 2 → 1 → 2 gidip
    gelindiğinde grupta tanımlı farklı kapasiteler ( ör. 10 + 16 kişilik )
    kaybolmasın.  Hesaba yalnız GÖRÜNEN kolonlar gönderilir ( trafikGirdi ).
    Yeni açılan boş kolon 1. asansörden doldurulur. */
function trafikAdedi(n){
  n=Math.max(1,Math.min(4,parseInt(n,10)||1));
  if(n===TRAFIK_ADET){ return; }
  TRAFIK_ADET=n;
  for(let i=2;i<=n;i++){
    if($('c_P'+i) && !$('c_P'+i).value){
      alanaYaz($('c_P'+i),  v('c_P1'));
      alanaYaz($('c_kg'+i), v('c_kg1'));
      alanaYaz($('c_kt'+i), v('c_kt1'));
    }
  }
  cokluKolonlariGoster();
  avanSenkron();                 // avan adedi trafik adedini takip eder
  sekmeGoster('trafik');
  yaz(); planla();
  durum(n>1 ? `${n} asansör tanımlandı — grup denetlenecek`
            : 'Tek asansör tanımlandı — gerekli adet hesaplanacak');
}

function cokluKolonlariGoster(){
  for(let i=1;i<=4;i++){
    const k=$('c_kutu'+i);
    if(k) k.hidden = (i>TRAFIK_ADET);
  }
}

/* ------------------------------------------- avan: asansör adedi
   ADET TEK YERDE BELİRLENİR.  Avandaki asansör adedi, trafik hesabının
   verdiği asansör adedini kendiliğinden takip eder:

     · 1 asansör seçiliyken   →  trafik hesabının BULDUĞU adet
       ( "1 asansör yetmiyor, 3 gerekir" derse avanda 3 kart açılır )
     · 2 - 4 asansör seçiliyken →  grupta tanımlanan adet

   Binada trafik grubuna girmeyen bir asansör varsa ( ör. ayrı bir yük ya da
   sedye asansörü ) avan adedi ELLE artırılır; fazlalar "trafik grubu dışı"
   diye işaretlenir — kurulu güce girer, trafik kontrolüne girmez.  Bu fark
   ( AVAN_EK ) kalıcıdır, trafik adedi değişince korunur.

   DOLDURULMUŞ bir kart kendiliğinden KAPANMAZ: trafik grubu küçülürse o
   asansör trafik dışına alınır, sessizce hesap dışı kalmaz.  Kapatmak
   kullanıcının açık kararıdır. */
function trafikGrupAdedi(){
  const k = trafikKoprusu();
  const n = k && Array.isArray(k.asansorler) ? k.asansorler.length : 0;
  return n > 0 ? n : TRAFIK_ADET;          // ham değer — 4'ten büyük olabilir
}
function avanTaban(){ return Math.max(1, Math.min(4, trafikGrupAdedi())); }

/* Kullanıcının ELLE doldurduğu en yüksek asansör numarası.
   Trafikten otomatik gelen değerler sayılmaz — yoksa trafik grubu küçüldüğünde
   kendi doldurduğumuz kart "kullanıcı verisi" sanılıp sonsuza dek açık kalırdı. */
function avanDoluUst(){
  let u = 0;
  for(let i=1;i<=4;i++){
    if(AVAN_OTO[i]) continue;
    if(v('a_kapasite'+i)!=='' || v('a_Q_elle'+i)!=='') u = i;
  }
  return u;
}

function avanAdedi(){
  const taban = avanTaban();
  AVAN_EK = Math.max(0, Math.min(4 - taban, AVAN_EK));
  let n = Math.min(4, taban + AVAN_EK);
  const dolu = Math.min(4, avanDoluUst());
  if(dolu > n){ AVAN_EK = dolu - taban; n = dolu; }   // dolu kart kapanmaz
  return Math.max(1, n);
}

function avanAdediSec(n){
  const taban = avanTaban();
  n = Math.max(1, Math.min(4, parseInt(n,10)||1));
  if(n < taban){
    durum(`Trafik hesabı ${taban} asansör veriyor — avan adedi bunun altına inemez`, true);
    return;
  }
  const dolu = avanDoluUst();
  if(n < dolu){
    durum(`${dolu} nolu asansörün girdileri dolu — kapatmak için önce kapasitesini boşaltın`, true);
    return;
  }
  AVAN_EK = n - taban;
  avanSenkron();
  yaz(); planla();
  const ek = n - taban;
  durum(ek > 0 ? `${n} asansör  —  ${ek} adedi trafik grubu dışı ( yük / sedye )`
               : `${n} asansör  —  tamamı trafik grubundan`);
}

/* Kart aç / kapa + "trafik grubundan / dışı" etiketi.
   a_aktif kutuları artık ADETTEN türetilir; kullanıcı tek tek işaretlemez. */
function avanKartlariGoster(){
  const n = avanAdedi(), taban = avanTaban();
  for(let i=n+1;i<=4;i++){          // kapanan OTOMATİK kartın izi kalmasın
    if(!AVAN_OTO[i]) continue;
    const sp=$('a_kapasite'+i), sv=$('a_V'+i);
    if(sp) sp.value=''; if(sv) sv.value='';
    delete AVAN_OTO[i]; delete AVAN_TRF[i];
  }
  for(let i=1;i<=4;i++){
    const c=$('a_aktif'+i), k=$('a_kutu'+i), e=$('a_etiket'+i);
    if(c) c.checked = (i<=n);
    if(k) k.classList.toggle('pasif', i>n);
    if(e){
      e.textContent = i>n ? '' : (i<=taban ? 'trafik grubundan' : 'trafik grubu dışı');
      e.className = 'as-etiket' + (i>taban && i<=n ? ' dis' : '');
    }
  }
}

/* Kapasite ve hızı trafikten doldurur — YALNIZ BOŞ alanları.
   Elle girilmiş bir değerin üzerine hiçbir zaman yazılmaz; uyuşmazlık
   varsa motor uyarı üretir, kullanıcı "Trafikten güncelle" ile eşitler. */
function avanDoldur(){
  const k = trafikKoprusu();
  if(!k || !Array.isArray(k.asansorler)) return false;
  const taban = avanTaban();
  let degisti = false, yansiyan = 0;

  /*  Bir alan iki durumda trafikten yazılır:
        1) alan BOŞSA                                     → ilk doldurma
        2) TRAFİKTEKİ DEĞER DEĞİŞTİYSE                    → avan onu izler
      Trafik değişmediği sürece alana dokunulmaz; kullanıcının elle girdiği
      değer orada durur.  ( Her hesapta körü körüne yazılsaydı elle
      düzeltmek imkânsız olurdu: yazdığınız değer 0,2 sn sonra geri
      dönerdi. )  AVAN_TRF, her asansöre EN SON YANSITILAN trafik değerini
      tutar; karşılaştırma buna göre yapılır. */
  const yaz1 = (alan, yeni, i) => {
    if(!alan || yeni==null || yeni==='') return false;
    alanaYaz(alan, yeni);
    if(alan.value===''){ return false; }
    degisti = true; AVAN_OTO[i] = true;
    return true;
  };

  for(let i=1;i<=Math.min(taban, k.asansorler.length, 4);i++){
    const t = k.asansorler[i-1] || {};
    const onceki = AVAN_TRF[i] || {};
    const sp = $('a_kapasite'+i), sv = $('a_V'+i);

    //  Kapasite —  'Q elle' doluysa dokunulmaz ( kullanıcı Tablo-7 dışına çıkmış )
    if(sp && t.P!=null && t.P!==''){
      const bos = (sp.value==='' && v('a_Q_elle'+i)==='');
      const trafikDegisti = ('P' in onceki) && String(onceki.P)!==String(t.P);
      const ilkKez = !('P' in onceki);
      if(bos || trafikDegisti || (ilkKez && v('a_Q_elle'+i)==='')){
        const eskiDeger = sp.value;
        if(yaz1(sp, t.P, i) && eskiDeger!=='' && eskiDeger!==sp.value) yansiyan++;
      }
      AVAN_TRF[i] = Object.assign({}, AVAN_TRF[i], {P: t.P});
    }

    //  Kabin hızı
    if(sv && t.V!=null && t.V!==''){
      const trafikDegisti = ('V' in onceki) && String(onceki.V)!==String(t.V);
      const ilkKez = !('V' in onceki);
      if(sv.value==='' || trafikDegisti || ilkKez){
        const eskiDeger = sv.value;
        if(yaz1(sv, t.V, i) && eskiDeger!=='' && eskiDeger!==sv.value) yansiyan++;
      }
      AVAN_TRF[i] = Object.assign({}, AVAN_TRF[i], {V: t.V});
    }
  }
  if(yansiyan) durum('Trafik hesabı değişti — avandaki kapasite / hız güncellendi');
  return degisti;
}

function avanSenkron(){
  const degisti = avanDoldur();          // önce doldur — adet dolu karta bakar
  avanKartlariGoster();
  adetDugmeleriKur();
  return degisti;
}

/* ---------------------------------------------------------- kurulum */
async function kur(){
  SEC = await (await fetch('/api/secenekler')).json();
  const opts=(a,f)=>a.map(v=>`<option value="${f?f(v):v}">${f?f(v):v}</option>`).join('');
  $('c_bina_tipi').innerHTML = opts(SEC.bina_tipleri);
  $('c_manuel_V').innerHTML = '<option value="">Tablo-2 minimumu</option>' +
      SEC.hizlar.map(v=>`<option value="${v}">${tr(v)} m/s</option>`).join('');

  cokluAsansorleriKur();
  avanAsansorleriKur();
  sabitFormuKur();
  sabitATablosu();
  tablolariKur();

  document.body.addEventListener('input', e=>{
    if(e.target.closest('#s-proje')){ yaz(); return; }
    planla(e.target);
  });
  document.body.addEventListener('change', e=>{
    if(e.target.closest('#s-proje')){ yaz(); return; }
    planla(e.target);
  });

  birakAlaniniKur();
  oku();
  cokluKolonlariGoster();
  avanKartlariGoster();
  adetDugmeleriKur();
  mkYokUygula();
  ofisTazele();
  etiketleriGuncelle();
  sablonDurumu();
  hesaplaHepsi();
}

let zaman=null;
function planla(hedef){
  if(hedef && hedef.closest('#s-proje')){ yaz(); return; }
  /*  Kullanıcı kapasite / hız alanına dokunduysa o asansör artık "otomatik"
      değildir: değeri korunur ve kartı kendiliğinden kapanmaz. */
  if(hedef && hedef.id){
    const m = /^a_(kapasite|Q_elle|V)([1-4])$/.exec(hedef.id);
    if(m) delete AVAN_OTO[m[2]];
  }
  etiketleriGuncelle();
  clearTimeout(zaman);
  zaman=setTimeout(()=>{ yaz(); hesaplaHepsi(); }, 220);
}

function etiketleriGuncelle(){
  ofisTazele();
  temelCevresi();
  [['c','c_bina_tipi']].forEach(([p,id])=>{
    const bt=$(id).value||'';
    let l1='⑤ —', l2='⑥ (bu bina tipinde gerekmiyor — boş bırakın)';
    if(bt==='Konut'){ l1='⑤ Daire sayısı (bağımsız bölüm adedi)';
      l2='⑥ Daire başına DİĞER oda sayısı (ilk yatak odası hariç)'; }
    else if(bt.startsWith('İş Merkezi')||bt.startsWith('Kamu')){ l1='⑤ Toplam çalışma alanı (m²)  →  12 m² = 1 kişi'; }
    else if(bt.startsWith('Otel')||bt==='Hastane'){ l1='⑤ Toplam yatak sayısı'; }
    else if(bt==='Katlı Otopark'){ l1='⑤ Özel amaçlı araç adedi'; l2='⑥ Ticari amaçlı araç adedi'; }
    else { l1='⑤ Bu bina tipinde hızlı giriş yok — ek nüfus kalemlerini kullanın'; }
    $(p+'_l_hizli1').innerHTML=l1; $(p+'_l_hizli2').innerHTML=l2;
  });
}

/* ---------------------------------------------------------- girdi topla */
const v = id => { const e=$(id); return e ? e.value.trim() : ''; };

/*  TEK GİRDİ BİÇİMİ:  bina alanları + asansör listesi.
    Yöntemi ( PAFTA / PAFTA-COKLU ) sunucu, asansörlerin aynı tip olup
    olmamasına bakarak seçer — kullanıcı seçmez. */
function trafikGirdi(){
  return {
    bina_tipi:v('c_bina_tipi'), bina_yuksekligi:v('c_bina_yuksekligi'),
    yapi_yuksekligi:v('c_yapi_yuksekligi'), N:v('c_N'), h:v('c_h'),
    bodrum:v('c_bodrum'),
    hizli1:v('c_hizli1'), hizli2:v('c_hizli2'),
    manuel_k:v('c_manuel_k'), manuel_V:v('c_manuel_V'),
    ek_nufus:ekNufusTopla('c'),
    //  YALNIZ GÖRÜNEN kolonlar hesaba girer; gizli kolonlar değerlerini
    //  korur ama tanımlanmamış sayılır.
    asansorler:[1,2,3,4].filter(i=>i<=TRAFIK_ADET).map(i=>({
      P:v('c_P'+i), kapi_genisligi:v('c_kg'+i), kapi_tipi:v('c_kt'+i),
      V:v('c_V'+i), durak:v('c_durak'+i), h:v('c_h'+i), bodrum:v('c_bodrum'+i),
      manuel_ta:v('c_mta'+i), manuel_tk:v('c_mtk'+i),
      manuel_tg:v('c_mtg'+i), manuel_tp:v('c_mtp'+i)
    })).filter(a=>a.P!=='')
  };
}
function avanGirdi(){
  /*  U · κ · εmax · β · Is alanları avan panelinden kaldırıldı ( ofis
      standardında ).  v() olmayan alan için '' döndürür, motor da boş
      değeri ofis varsayılanına çevirir — liste yine de tam bırakıldı ki
      Excel'den geri yüklenen eski projelerdeki değerler taşınabilsin. */
  const ortak={}; ['U','kappa','eps_max','temel_a','temel_b','beta','serit_L','cubuk_sayisi',
    'mk_uzunluk','mk_genislik'].forEach(k=>ortak[k]=v('a_'+k));
  ortak.mk_yok = !!($('a_mk_yok') && $('a_mk_yok').checked);
  const asansorler=[1,2,3,4].map(i=>{
    const o={aktif:$('a_aktif'+i).checked};
    ['tanim','kapasite','Q_elle','V','eta','Hk','kuyu_genisligi','kabin_boyu','kabin_genisligi',
     'Gk_elle','gr','Fmk','Fsh','Nsc','S1','L1','S2','L2','kablo_tipi',
     'i_palanga','q_denge','makine_tipi']
      .forEach(k=>o[k]=v('a_'+k+i));
    o.toplam_verim = !!($('a_toplam_verim'+i) && $('a_toplam_verim'+i).checked);
    return o;
  });
  const sabitler={}; Object.keys(SEC.sabit_b).forEach(k=>{const x=v('sb_'+k); if(x!=='')sabitler[k]=x;});
  Object.keys(SEC.ofis_varsayilan||{}).forEach(k=>{const x=v('of_'+k); if(x!=='')sabitler[k]=x;});
  return {ortak, asansorler, sabitler, trafik:trafikKoprusu()};
}
/* Sekme başlığındaki uyarı rozeti — sağ paneldeki uyarılar sekme kapalıyken
   gözden kaçmasın diye sekmenin üstünde sayı olarak da görünür. */
function sekmeRozeti(sekme, hata, sayi){
  const b=document.querySelector('.sekme[data-sekme="'+sekme+'"]');
  if(!b) return;
  let r=b.querySelector('.sekme-rozet');
  if(!hata && !sayi){ if(r) r.remove(); return; }
  if(!r){ r=document.createElement('span'); b.appendChild(r); }
  r.className='sekme-rozet '+(hata?'kirmizi':'sari');
  r.textContent = hata ? '!' : String(sayi);
  r.title = hata ? 'Hesap hatası var' : sayi+' uyarı';
}

/* ---------------------------------------------------------- hesap */
/* Önce trafik hesaplanır — avan adedi ve kapasite/hız oradan gelir; avan
   ondan SONRA hesaplanır ki ilk çizimde eksik asansör görünmesin. */
async function hesaplaHepsi(){
  await hesapTrafik();
  avanSenkron();
  await hesapAvan();
}

/*  TEK HESAP YOLU.  Kullanıcı yöntem seçmez; sunucu, tanımlanan asansörler
    aynı tipte mi diye bakıp PAFTA ya da PAFTA-COKLU yolunu kendisi seçer
    ( engine.traffic.hesapla ).  Dönen sonuçta `yol` ve `pafta` alanları var. */
async function hesapTrafik(){
  try{
    const r = await (await fetch('/api/trafik',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({girdiler:trafikGirdi()})})).json();
    SON.c=r; SON.t=r; ciz('c_sonuc', r, r.yol||'tek');
    sekmeRozeti('trafik', !!r.hata, (r.uyarilar||[]).length);
    const rz=$('c_std_rozet');
    if(rz) rz.innerHTML = r.ozet && r.ozet.standart
      ? `<span class="rozet ${r.ozet.standart==='Yükseltilmiş'?'sari':'ok'}">Hesap standardı: ${r.ozet.standart}</span>` : '';
  }catch(e){ $('c_sonuc').innerHTML=`<div class="kart-ic"><div class="uyari kirmizi">Bağlantı hatası: ${kacis(e)}</div></div>`; }
}
async function hesapAvan(){
  try{
    const r = await (await fetch('/api/avan',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({girdiler:avanGirdi()})})).json();
    SON.a=r; cizAvan(r); turetilenGoster(r); seritGoster(r);
    sekmeRozeti('avan', !!r.hata, (r.uyarilar||[]).length);
  }catch(e){ $('a_sonuc').innerHTML=`<div class="kart-ic"><div class="uyari kirmizi">Bağlantı hatası: ${kacis(e)}</div></div>`; }
}

/* "ℹ" ile başlayan iletiler UYARI değil NOT'tur — mavi kutuda gösterilir. */
function uyariSinifi(u){ return String(u||'').trim().startsWith('ℹ') ? 'mavi' : 'sari'; }

/* ---------------------------------------------------------- çizim: ortak */
function adimTablosu(adimlar){
  let h='<div class="kaydir"><table class="hesap">';
  for(const a of adimlar){
    if(a.tip==='metin'){ h+=`<tr class="baslik-satir"><td colspan="6">${kacis(a.deger)}</td></tr>`; continue; }
    if(a.tip==='hesap'){
      h+=`<tr class="formul"><td colspan="6">${kacis(a.formul)}</td></tr>`
       + `<tr class="islem"><td></td><td class="islem" colspan="2">${kacis(a.islem)}</td>`
       + `<td class="deger">${kacis(a.metin)}</td><td class="birim">${kacis(a.birim)}</td>`
       + `<td class="kaynak">${kacis(a.kaynak)}</td></tr>`;
      continue;
    }
    h+=`<tr><td class="sembol">${kacis(a.sembol)}</td><td class="aciklama">${kacis(a.aciklama)}</td>`
     + `<td class="esit">=</td><td class="deger">${kacis(a.metin)}</td>`
     + `<td class="birim">${kacis(a.birim)}</td><td class="kaynak">${kacis(a.kaynak)}</td></tr>`;
  }
  return h+'</table></div>';
}
function cetvelTablosu(c){
  let t=0, h='<div class="kaydir"><table class="veri"><tr><th>Lin</th><th>Sorti</th><th style="text-align:right">Gücü</th><th>Birim</th><th>Sigorta A</th></tr>';
  c.forEach(x=>{t+=x.guc; h+=`<tr><td>${x.lin}</td><td>${kacis(x.sorti)}</td><td class="sag">${trn(x.guc,0)}</td><td>${x.birim}</td><td>${x.sigorta}</td></tr>`;});
  return h+`<tr class="toplam"><td></td><td>ASANSÖRÜN KURULU GÜCÜ</td><td class="sag">${trn(t,0)}</td><td>W</td><td></td></tr></table></div>`;
}
/* Yöntem açıklamalarını başlığın yanındaki ( ! ) dairesine toplar; üzerine
   gelince açılır, dokunmatik ekranda tıklayınca kalır.  Uyarılar buraya
   girmez — onlar açıkta durur.  Paftada bu metinler yine tam basılır. */
function bilgiSimgesi(metinler, sinif){
  const liste=(Array.isArray(metinler)?metinler:[metinler])
    .filter(x=>x!==null&&x!==undefined&&String(x).trim()!=='');
  if(!liste.length) return '';
  return `<span class="bilgi${sinif?' '+sinif:''}" tabindex="0" role="button"`
    + ` aria-label="Açıklamayı göster" onclick="bilgiAc(this,event)">`
    + `<span class="bilgi-im">!</span><span class="bilgi-balon">`
    + liste.map(x=>`<p>${kacis(String(x))}</p>`).join('')
    + `</span></span>`;
}
/* Balon fixed konumlandırılır; yoksa kartların overflow'u kırpıyor.
   Ekranın sağına / altına taşacaksa kendini içeri alır. */
function bilgiKonumla(e){
  const balon=e.querySelector('.bilgi-balon'); if(!balon) return;
  balon.style.maxWidth=Math.min(430,window.innerWidth-24)+'px';
  balon.style.left='0px'; balon.style.top='0px';
  const r=e.getBoundingClientRect(), b=balon.getBoundingClientRect();
  let x=r.left-8, y=r.bottom+8;
  if(x+b.width > window.innerWidth-12) x=window.innerWidth-12-b.width;
  if(x<12) x=12;
  if(y+b.height > window.innerHeight-12) y=Math.max(12, r.top-8-b.height);
  balon.style.left=Math.round(x)+'px'; balon.style.top=Math.round(y)+'px';
}
function bilgiAc(e, olay){
  if(olay) olay.stopPropagation();
  const acik=e.classList.contains('acik');
  document.querySelectorAll('.bilgi.acik').forEach(x=>x.classList.remove('acik'));
  if(!acik){ e.classList.add('acik'); bilgiKonumla(e); }
}
function _bilgiHedef(ev){
  const t=ev.target;
  return (t && t.closest) ? t.closest('.bilgi') : null;
}
document.addEventListener('mouseover',ev=>{const e=_bilgiHedef(ev); if(e) bilgiKonumla(e);}, true);
document.addEventListener('focusin',ev=>{const e=_bilgiHedef(ev); if(e) bilgiKonumla(e);});
document.addEventListener('click',()=>document.querySelectorAll('.bilgi.acik')
  .forEach(x=>x.classList.remove('acik')));
document.addEventListener('keydown',ev=>{
  if(ev.key!=='Escape') return;
  document.querySelectorAll('.bilgi.acik').forEach(x=>x.classList.remove('acik'));
  /* Esc'ten sonra tarayıcı odağı :focus-visible'a yükseltiyor ve balon açık
     kalıyordu; kapatırken odağı da bırakıyoruz. */
  const o=document.activeElement;
  if(o && o.classList && o.classList.contains('bilgi')) o.blur();
});
addEventListener('scroll',()=>{const a=document.querySelector('.bilgi.acik');
  if(a) bilgiKonumla(a);}, true);
addEventListener('resize',()=>document.querySelectorAll('.bilgi.acik')
  .forEach(x=>x.classList.remove('acik')));

function bolumCiz(b){
  //  "ekran_notlari":  paftaya basılmayan ama ekranda kalması gereken
  //  açıklamalar ( bkz. engine/avan.py — topraklama kontrolü ).
  const bilgi = [...(b.aciklamalar||[]), ...(b.ekran_notlari||[])];
  let h=`<div class="serit"><span>${kacis(b.baslik)}${bilgiSimgesi(bilgi)}</span>`
      + `<span class="kaynak">${kacis(b.kaynak||'')}</span></div>`;
  if(b.adimlar&&b.adimlar.length) h+=adimTablosu(b.adimlar);
  if(b.cetvel&&b.cetvel.length) h+=cetvelTablosu(b.cetvel);
  if(b.sonuc) h+=`<div class="sonuc-kutu ${b.sonuc.uygun?'ok':'hata'}"><span class="et">${kacis(b.sonuc.baslik)}</span><span>${kacis(b.sonuc.metin)}</span></div>`
    + (b.sonuc.alt||[]).map(x=>`<div class="notlar"><div>${kacis(x)}</div></div>`).join('');
  if(b.notlar&&b.notlar.length) h+='<div class="notlar">'+b.notlar.map(n=>`<div>${kacis(n)}</div>`).join('')+'</div>';
  return h;
}
const kutu = (et,dg,bi,sinif='') => `<div class="k ${sinif}"><div class="et">${et}</div><div class="dg2">${dg}</div><div class="bi">${bi||''}</div></div>`;

/* ---------------------------------------------------------- çizim: trafik */
function ciz(hedef, r, mod){
  const o=r.ozet||{};
  let h=`<div class="pafta-bas"><h2>ASANSÖR TRAFİK HESABI${mod==='coklu'?'  —  ÇOKLU ASANSÖR':''}</h2>
         <div class="alt">MMO/697, 2. Baskı, Ocak 2020, s.11-17</div></div><div class="kart-ic">`;
  /*  Hangi yolun ve hangi Excel pafta sayfasının kullanıldığı SESSİZ kalmasın:
      kullanıcı yöntemi seçmiyor, o hâlde ne seçildiğini görmeli. */
  if(!r.hata && r.pafta){
    const ayni = r.yol!=='coklu';
    h += `<div class="uyari mavi" style="margin:0 0 10px">
      ${ayni ? 'Asansörlerin hepsi <b>aynı tip</b> — MMO/697 s.11-12 yolu.'
             : 'Asansörler <b>farklı tipte</b> — grup formülü ( MMO/697 s.12 ).'}
      Üretilecek pafta: <b>${kacis(r.pafta)}</b></div>`;
  }
  if(r.hata) h+=`<div class="uyari kirmizi">${kacis(r.hata)}</div>`;
  (r.uyarilar||[]).forEach(u=>h+=`<div class="uyari ${uyariSinifi(u)}">${kacis(u)}</div>`);

  if(!r.hata){
    h+='<div class="olcut">';
    if(mod==='coklu'){
      const okR = o.Res>=o.gereken, okT = o.TRes<=o.Izul;
      h+=kutu('Asansör adedi', o.adet, 'adet')
       + kutu('Reş / B·k', tr(o.Res,1)+' / '+tr(o.gereken,1), 'kişi / 5 dk', okR?'ok':'hata')
       + kutu('Bekleme TReş', tr(o.TRes,1), 'sn  ·  sınır '+trn(o.Izul,0)+' sn', okT?'ok':'hata')
       + kutu('Tasarım nüfusu B', trn(o.B,0), 'kişi')
       + kutu('Taşınacak yüzde k', '%'+tr((o.k||0)*100,1), 'Tablo-9');
    }else{
      const ok = o.Ieer<=o.Izul;
      /*  Tanımlanan adet ile GEREKLİ adet ayrı gösterilir: kullanıcı
          fazla ya da eksik koyduğunu görsün.  Eşitse tek satır yeter. */
      const gerekli = o.adet_hesap;
      h+=kutu('Asansör adedi', o.adet, (gerekli!=null && gerekli!==o.adet)
               ? `adet  ·  gerekli ${trn(gerekli,0)}` : 'adet  ·  '+trn(o.P,0)+' kişilik',
               (gerekli!=null && o.adet<gerekli) ? 'hata' : '')
       + kutu('Bekleme Ieer', tr(o.Ieer,1), 'sn  ·  sınır '+trn(o.Izul,0)+' sn', ok?'ok':'hata')
       + kutu('Kabin hızı V', tr(o.V), 'm/s')
       + kutu('Tur süresi TR', tr(o.TR,1), 'sn')
       + kutu('5 dk taşıma R', tr(o.R,1), 'kişi')
       + kutu('Tasarım nüfusu B', trn(o.B,0), 'kişi');
    }
    h+='</div>';
  }
  (r.bolumler||[]).forEach(b=>h+=bolumCiz(b));

  if(mod==='coklu' && r.asansorler && r.asansorler.length) h+=cokluTablo(r.asansorler);
  if(r.nufus && r.nufus.length) h+=nufusTablo(r.nufus, o.b);

  if(o.sonuc){
    const kotu = /^(Kabul|YETERSİZ|HESAP)/.test(o.sonuc);
    h+=`<div class="sonuc-kutu ${kotu?'hata':'ok'}"><span class="et">SONUÇ</span><span>${kacis(o.sonuc)}</span></div>`;
    /*  NİHAİ CEVAP ve DAYANAĞI  —  paftadaki karar kutusunun ekran karşılığı.
        Hangi ölçütün hangi sayıyla sağlandığı sonucun yanında durur; bölüm
        dip notu olarak ayrı yerde aranmaz. */
    const c = o.sonuc_cumlesi||o.pafta_satiri;
    const olc = o.karar_olcutleri||[];
    if((c && c!==o.sonuc) || olc.length){
      h+=`<div class="karar-kutu ${kotu?'hata':'ok'}">`;
      if(c && c!==o.sonuc) h+=`<div class="karar-metin">${kacis(c)}</div>`;
      if(olc.length) h+=`<div class="karar-olcut">` + olc.map(x=>
        `<div><span class="im ${x.uygun?'ok':'hata'}">${x.uygun?'✔':'✘'}</span>
         <b>${kacis(x.ad)}</b><span>${kacis(x.metin)}</span></div>`).join('') + `</div>`;
      h+=`</div>`;
    }
    /* Tek asansör hesabı "n adet gerekir" diyorsa, o n asansörü tek tıkla
       tanımlamaya geçiş — kullanıcı adedi elle değiştirmek zorunda kalmasın. */
    if(mod!=='coklu' && o.adet>1 && o.adet<=4 && !r.hata){
      h+=`<div class="dugmeler" style="margin-top:10px">
        <button class="dg ana" onclick="trafikAdedi(${o.adet})">
          → ${o.adet} asansör olarak tanımla ve grubu kontrol et</button></div>
        <div class="notlar" style="margin-top:6px"><div>Aynı tipte ${o.adet} asansör
        kolonlara kopyalanır; farklı kapasitede olacaksa kolonları düzeltebilirsiniz.</div></div>`;
    } else if(mod!=='coklu' && o.adet>4 && !r.hata){
      h+=`<div class="uyari sari" style="margin-top:10px">Hesap ${trn(o.adet,0)} adet asansör
        gerektiriyor; program en çok 4 asansörlü grubu kontrol eder. Daha büyük gruplarda
        bölgeli (zoned) trafik hesabı yapılmalıdır.</div>`;
    }
  }
  if(r.oneriler && r.oneriler.length) h+=oneriTablo(r.oneriler);
  $(hedef).innerHTML = h+'</div>';
}

function cokluTablo(as){
  const S=[['P — Kabin kapasitesi (kişi)',a=>trn(a.P,0)],['Beyan yükü (kg)',a=>trn(a.yuk_kg,0)],
    ['Kapı genişliği (mm) / tipi',a=>trn(a.kapi_genisligi,0)+' / '+(a.kapi_tipi||'')],
    ['Durak adedi (ana giriş dâhil)',a=>trn(a.durak,0)],['V — Kabin hızı (m/s)',a=>tr(a.V)],
    ['h — Katlar arası mesafe (m)',a=>tr(a.h)],['p = 0,8·P',a=>tr(a.p,1)],
    ['H — Ort. en yüksek dönüş katı',a=>tr(a.H,4)],['S — Ortalama durak adedi',a=>tr(a.S,4)],
    ['ta / tk  (s)',a=>tr(a.ta,1)+' / '+tr(a.tk,1)],['tg / tp  (s)',a=>tr(a.tg,1)+' / '+tr(a.tp,1)],
    ['tv = h / V  (s)',a=>tr(a.tv,3)],['ts = ta+tk+tg−tv  (s)',a=>tr(a.ts,3)],
    ['TR = 2·H·tv+(S+1)·ts+2·p·tp  (s)',a=>tr(a.TR,2)],['R = 5·60·p / TR  (kişi/5dk)',a=>tr(a.R,2)]];
  let h=`<div class="serit"><span>ASANSÖR BAZINDA HESAP</span><span class="kaynak">MMO/697 s.11-12</span></div>
         <div class="kaydir"><table class="veri"><tr><th>Büyüklük</th>`+
         as.map(a=>`<th style="text-align:right">${kacis(a.ad)}</th>`).join('')+'</tr>';
  S.forEach(([et,fn])=>{ h+=`<tr><td class="etiket">${kacis(et)}</td>`+
    as.map(a=>`<td class="sag">${kacis(fn(a))}</td>`).join('')+'</tr>'; });
  return h+'</table></div>';
}
function nufusTablo(n,b){
  let h=`<div class="serit"><span>NÜFUSUN AYRINTISI  ( b = Σc )</span><span class="kaynak">MMO/697 Tablo-1</span></div>
    <div class="kaydir"><table class="veri"><tr><th>Grup / açıklama</th><th style="text-align:right">Miktar</th>
    <th>Tablo-1 kalemi</th><th>Birim</th><th style="text-align:right">Katsayı</th><th style="text-align:right">c (kişi)</th></tr>`;
  n.forEach(s=>h+=`<tr><td>${kacis(s.aciklama)}</td><td class="sag">${trn(s.miktar,2)}</td>
    <td>${kacis(s.kalem)}</td><td>${kacis(s.birim)}</td><td class="sag">${trn(s.katsayi,4)}</td>
    <td class="sag">${trn(s.c,2)}</td></tr>`);
  return h+`<tr class="toplam"><td colspan="5">TOPLAM  b = Σc</td><td class="sag">${trn(b,2)}</td></tr></table></div>`;
}
function oneriTablo(o){
  let h=`<div class="serit"><span>OTOMATİK ÖNERİ — hangi kabin ve hız kaç asansör gerektirir?`
    + bilgiSimgesi([`TS EN 81-70 / TS 9111 erişilebilirlik ölçütünü karşılamayan seçenekler ( 630 kg altı kabin ya da 800 mm altı net kapı ) satırda işaretlenir ve öneri sıralamasına alınmaz; hesaptan çıkarılmaz.`,`Her satırda kapasiteye uygun kapı genişliği varsayılır — ISO 8100-32:2020 Ek C, Tablo 8.`,`Bu blok bilgi amaçlıdır; kesin hesap sizin ⑧ / ⑨ / ⑩ girdilerinizle yapılır.`]) + `</span>
    <span class="kaynak">bilgi amaçlıdır</span></div><div class="kaydir"><table class="veri">
    <tr><th>Seçenek (kabin — hız)</th><th style="text-align:right">Adet</th><th style="text-align:right">Bekleme (sn)</th>
    <th>Sınıf</th><th style="text-align:right">TR (sn)</th><th style="text-align:right">R</th></tr>`;
  o.forEach(s=>h+=`<tr class="${s.onerilen?'onerilen':''}"><td>${kacis(s.secenek)}${s.onerilen?' &nbsp;<span class="rozet ok">ÖNERİLEN</span>':''}</td>
    <td class="sag">${s.adet}</td><td class="sag">${tr(s.Ieer,1)}</td><td>${kacis(s.sinif)}</td>
    <td class="sag">${tr(s.TR,1)}</td><td class="sag">${tr(s.R,1)}</td></tr>`);
  return h+`</table></div>`;
}

/* ---------------------------------------------------------- çizim: avan */
function cizAvan(r){
  let h=`<div class="pafta-bas"><h2>ASANSÖR AVAN PROJE HESAPLARI</h2>
    <div class="alt">MMO/697, 2. Baskı, Ocak 2020, s.18-21  ·  TS EN 81-20</div></div><div class="kart-ic">`;
  /* Uyarılar PDF'te basılıyordu ama ekranda görünmüyordu; trafik ↔ avan
     tutarsızlığı da buradan bildirilir. */
  (r.uyarilar||[]).forEach(u=>h+=`<div class="uyari ${uyariSinifi(u)}">${kacis(u)}</div>`);
  if(r.hata){ $('a_sonuc').innerHTML=h+`<div class="uyari kirmizi">${kacis(r.hata)}</div></div>`; return; }
  const aktif=(r.asansorler||[]).filter(a=>a.aktif);
  if(!aktif.length){
    $('a_sonuc').innerHTML = h+`<div class="bos">Henüz asansör tanımlanmadı.<br>
      Trafik hesabını yapın — asansör adedi, kapasite ve hız buraya kendiliğinden gelir.</div></div>`;
    (r.asansorler||[]).forEach(a=>{}); return;
  }
  const oz=r.ozet||{};
  h+='<div class="olcut">'
    + kutu('Tanımlı asansör', aktif.length, 'adet')
    + kutu('Tesisin kurulu gücü', trn(oz.tesis_kurulu_guc,0), 'W')
    + (oz.Re!=null ? kutu('Re — Topraklama', tr(oz.Re,3), 'Ω', oz.topraklama_uygun?'ok':'hata') : '')
    + '</div>';

  /* özet tablo */
  const S=[['Asansör tanımı',o=>o.tanim||'—'],['P — Kabin kapasitesi (kişi)',o=>trn(o.kapasite,0)],
    ['Q — Anma yükü (kg)',o=>trn(o.Q,0)],['V — Kabin hızı (m/s)',o=>tr(o.V)],
    ['N — Hesaplanan motor gücü (kW)',o=>tr(o.N_hes)],['Nsç — Seçilen motor gücü (kW)',o=>tr(o.Nsc)],
    ['Kontrol  ( Nsç ≥ N )',o=>o.motor_uygun?'UYGUN':'UYGUN DEĞİL'],
    ['P1 — Kuyu alt boşluğu tabanına (N)',o=>trn(o.P1,0)],
    ['P2 — Karşı ağırlık tamponu altına (N)',o=>trn(o.P2,0)],
    ['PR — Bir kabin kılavuz rayına (N)',o=>trn(o.PR,0)],
    ['PK — Bir karşı ağırlık rayına (N)',o=>trn(o.PK,0)],
    ['Fs — Kuyu üstü betonuna (N)',o=>trn(o.Fs,0)],
    ['Kabin armatür sayısı (adet)',o=>trn(o.n_kabin,0)],['Kuyu armatür sayısı (adet)',o=>trn(o.n_kuyu,0)],
    ['P — Asansörün kurulu gücü (W)',o=>trn(o.P_kurulu,0)],
    ['ε — Toplam gerilim düşümü (%)',o=>tr(o.eps,3)],
    ['Kontrol  ( ε ≤ εmax )',o=>o.eps_uygun?'UYGUN':'UYGUN DEĞİL'],
    ['I — Hat akımı / Iz (A)',o=>tr(o.I,1)+' / '+trn(o.Iz,1)]];
  h+=`<div class="serit"><span>SONUÇ ÖZETİ</span><span class="kaynak">tüm asansörler</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Büyüklük</th>`+
      aktif.map(a=>`<th style="text-align:right">${a.no} NOLU</th>`).join('')+'</tr>';
  S.forEach(([et,fn])=>{h+=`<tr><td class="etiket">${kacis(et)}</td>`+
    aktif.map(a=>`<td class="sag">${kacis(fn(a.ozet))}</td>`).join('')+'</tr>';});
  h+=`<tr class="toplam"><td>Tesisin toplam kurulu gücü (W)</td>
      <td class="sag" colspan="${aktif.length}">${trn(oz.tesis_kurulu_guc,0)}</td></tr>`;
  if(oz.Re!=null) h+=`<tr class="toplam"><td>Re — Temel topraklama direnci (Ω)</td>
      <td class="sag" colspan="${aktif.length}">${tr(oz.Re,3)}  —  ${oz.topraklama_uygun?'UYGUN':'UYGUN DEĞİL'}</td></tr>`;
  h+='</table></div>';

  /* uyarılar */
  (r.asansorler||[]).forEach(a=>{ if(!a.aktif && a.uyari && a.uyari.includes('TABLO-7'))
    h+=`<div class="uyari sari" style="margin-top:10px">${kacis(a.uyari)}</div>`; });

  /* her asansör */
  aktif.forEach(a=>{
    h+=`<div class="serit" style="margin-top:22px;background:#0E3357"><span>${kacis(a.baslik)}${a.tanim?'  —  '+kacis(a.tanim):''}</span>
        <span class="kaynak">AVAN PROJE HESAPLARI</span></div>`;
    a.bolumler.forEach(b=>h+=bolumCiz(b));
  });

  /* makine dairesi
     MRL ( makine dairesiz ) sistemde bu bölüm HİÇ GÖSTERİLMEZ — makine dairesi
     yoksa aydınlatma hesabının konusu da yoktur.  Ekran ile pafta aynı kuralı
     uygular ( bkz. pdf_export.avan_pdf ).
     Tek istisna EKSİK GİRDİ:  MRL kutusu işaretli değil ama A × B ölçüsü de
     girilmemişse bu bir tercih değil unutulmuş bir girdidir — kırmızı uyarı
     basılır, yoksa eksik hesap sessizce gizlenmiş olurdu. */
  const mk=r.makine_dairesi||{};
  if(mk.aktif || mk.mk_yok === false){
    h+=`<div class="serit" style="margin-top:22px;background:#0E3357"><span>MAKİNE DAİRESİ AYDINLATMASI</span>
        <span class="kaynak">TS EN 81-20</span></div>`;
    h += mk.aktif ? bolumCiz(mk.bolum)
       : `<div class="uyari kirmizi" style="margin-top:8px">${kacis(mk.uyari||'')}</div>`;
  }

  /* topraklama */
  const tp=r.topraklama||{};
  h+=`<div class="serit" style="margin-top:22px;background:#0E3357"><span>TEMEL TOPRAKLAMA HESABI</span>
      <span class="kaynak">Temel ( ızgara ) + paralel çubuk</span></div>`;
  if(tp.aktif) tp.bolumler.forEach(b=>h+=bolumCiz(b));
  else h+=`<div class="uyari kirmizi" style="margin-top:8px">${kacis(tp.uyari||'')}</div>`;

  $('a_sonuc').innerHTML = h+'</div>';
}

/* ---------------------------------------------------------- dinamik formlar */
function cokluAsansorleriKur(){
  let h='';
  for(let i=1;i<=4;i++){
    h+=`<div class="as-kutu" id="c_kutu${i}">
      <div class="as-bas">ASANSÖR-${i}</div>
      <div class="as-ic">
        <div class="satir i2">
          <div class="alan"><label>⑧ Kapasite P (kişi)</label><select id="c_P${i}" class="girdi">
            <option value="">— seçilmedi —</option>
            ${SEC.kapasiteler.map(p=>`<option value="${p}">${p} kişi — ${SEC.tablo_7[p]||p*75} kg</option>`).join('')}</select></div>
          <div class="alan"><label>⑨ Kapı genişliği (mm)</label><select id="c_kg${i}" class="girdi">
            ${SEC.kapi_genislikleri.map(k=>`<option value="${k}"${k===900?' selected':''}>${k}</option>`).join('')}</select></div>
        </div>
        <div class="alan"><label>⑩ Kapı tipi</label><select id="c_kt${i}" class="girdi">
          ${SEC.kapi_tipleri.map(k=>`<option value="${k}">${k}</option>`).join('')}</select></div>
        <div class="satir i3">
          <div class="alan"><label>V (m/s) <span class="ipucu">boş = Tablo-2</span></label><select id="c_V${i}" class="girdi">
            <option value="">Tablo-2 min</option>${SEC.hizlar.map(x=>`<option value="${x}">${tr(x)}</option>`).join('')}</select></div>
          <div class="alan"><label>Durak <span class="ipucu">boş = N+1</span></label><input id="c_durak${i}" class="girdi"></div>
          <div class="alan"><label>h (m) <span class="ipucu">boş = ortak</span></label><input id="c_h${i}" class="girdi"></div>
        </div>
        <div class="bolum-bas katla kapali" onclick="katla(this,'c_ileri${i}')">İleri seçenekler
          <span class="ipucu">— bodrum ve imalatçı süreleri</span></div>
        <div id="c_ileri${i}" style="display:none">
          <div class="alan"><label>Bodrum durağı <span class="ipucu">(ana giriş altı) boş = ortak</span>
            ${bilgiSimgesi(['Bu asansörün ana giriş altında hizmet verdiği durak adedi. Boş bırakırsanız ortak değer (⑪) kullanılır.','Bodrum durağı H (Tablo-3) ve S (Tablo-5) değerlerini değiştirmez; yalnız bu asansörün Tablo-2 asgari hızındaki durak adedine ve seyahat mesafesine girer.'])}</label>
            <input id="c_bodrum${i}" class="girdi"></div>
          <div class="satir i4">
            <div class="alan"><label>ta (s) ${bilgiSimgesi(['İmalatçı katalog değeri girilirse MMO Tablo-4 / Tablo-6 / ISO Tablo 6 değerinin yerine bu kullanılır.','Manuel süre girildiğinde paftada marka-model ve teknik föy referansı belirtilmelidir — program bunu uyarı olarak hatırlatır.'])}</label><input id="c_mta${i}" class="girdi" placeholder="T-4"></div>
            <div class="alan"><label>tk (s)</label><input id="c_mtk${i}" class="girdi" placeholder="T-4"></div>
            <div class="alan"><label>tg (s)</label><input id="c_mtg${i}" class="girdi" placeholder="T-6"></div>
            <div class="alan"><label>tp (s)</label><input id="c_mtp${i}" class="girdi" placeholder="T-8"></div>
          </div>
        </div>
      </div></div>`;
  }
  $('c_asansorler').innerHTML=h;
}

function avanAsansorleriKur(){
  let h='';
  const kesitOpt = () => SEC.kesitler.map(x=>`<option value="${x}">${tr(x,1)} mm²</option>`).join('');
  for(let i=1;i<=4;i++){
    /*  "kullan" kutusu artık ADETTEN türetilir — kullanıcı tek tek işaretlemez.
        Kutu gizli olarak durur; avanGirdi() ve geri yükleme onu kullanır. */
    h+=`<div class="as-kutu ${i>2?'pasif':''}" id="a_kutu${i}">
      <div class="as-bas">
        <span>${i} NOLU ASANSÖR</span>
        <span class="as-etiket" id="a_etiket${i}"></span>
        <input type="checkbox" id="a_aktif${i}" ${i<=2?'checked':''} hidden></div>
      <div class="as-ic">
        <div class="alan"><label>Asansör tanımı</label><input id="a_tanim${i}" class="girdi" placeholder="İnsan / Sedye + Yük"></div>
        <div class="satir i2">
          <div class="alan"><label>P — Kapasite (kişi) <span class="ipucu">trafikten</span></label>
            <select id="a_kapasite${i}" class="girdi"><option value="">—</option>
            ${SEC.kapasiteler.map(p=>`<option value="${p}">${p} kişi — ${SEC.tablo_7[p]||p*75} kg</option>`).join('')}</select></div>
          <div class="alan"><label>Q — Anma yükü (kg) <span class="ipucu">kapasiteden</span>
            ${bilgiSimgesi(['Soldaki kapasiteyi seçince MMO/697 Tablo-7\'deki anma yükü kendiliğinden gelir — burası girdi değildir, elle doldurulmaz.','Tablo-7 dışında bir anma yükü gerekiyorsa ( ör. özel bir yük asansörü ) "Ofis standardından farklı değerler" bölümündeki Q elle alanına yazın; o zaman bu satır girilen değeri gösterir.'])}</label>
            <input id="a_Q_goster${i}" class="girdi salt" readonly tabindex="-1" aria-readonly="true"></div>
        </div>
        <div class="satir i2">
          <div class="alan"><label>V — Kabin hızı (m/s) <span class="ipucu">trafikten</span></label>
            <select id="a_V${i}" class="girdi"><option value="">—</option>
            ${SEC.hizlar.map(x=>`<option value="${x}">${tr(x)}</option>`).join('')}</select></div>
          <div class="alan"><label>Makine tipi</label>
            <select id="a_makine_tipi${i}" class="girdi" onchange="verimTazele(${i});planla()">
              ${Object.keys(SEC.makine_tipleri||{}).map(k=>`<option value="${k}">${k}</option>`).join('')}
            </select></div>
        </div>
        <div class="satir i2">
          <div class="alan"><label>i — Askı ( palanga ) oranı
            ${bilgiSimgesi(['Doğrudan askı 1:1 / palangalı 2:1. Asansörün kendi özelliğidir — kapasite ve hız gibi burada girilir.','Motor GÜCÜ askı oranından bağımsızdır: 2:1 askıda halat hızı yarıya iner, kuvvet iki katına çıkar, çarpımları değişmez. Askı oranı hesaba yalnız VERİM üzerinden girer (MMO/697 §2.4: palangalı sistemde η − 0,10).'])}</label>
            <select id="a_i_palanga${i}" class="girdi" onchange="verimTazele(${i});planla()">
              ${Object.keys(SEC.aski_oranlari||{}).map(k=>
                `<option value="${SEC.aski_oranlari[k]}"${SEC.aski_oranlari[k]===2?' selected':''}>${k}</option>`).join('')}
            </select></div>
          <div class="alan"><label>η — Makine verimi
            ${bilgiSimgesi(['MMO/697 s.21: dişlisiz 0,85 · dişli 0,50. Makine tipini seçince kendiliğinden dolar, üzerine yazabilirsiniz.','İmalatçı katalogları genellikle TOPLAM SİSTEM verimi verir (makine × dişli × askı × motor) ve bu değerler daha yüksektir. Öyle bir değer giriyorsanız alttaki kutuyu işaretleyin — yoksa palanga kaybı ikinci kez düşülür.'])}</label>
            <input id="a_eta${i}" class="girdi" value="0,85"></div>
        </div>
        <label class="kutu-satir"><input type="checkbox" id="a_toplam_verim${i}" onchange="planla()">
          <span>Girilen η <b>toplam sistem verimidir</b> ( askı kaybı dâhil )</span>
          ${bilgiSimgesi(['İşaretliyken MMO/697 §2.4 uyarınca uygulanan palanga verim düşüşü (Δη = 0,10) AYRICA uygulanmaz — askı kaybı zaten girilen değerin içindedir.','Uygulamada toplam sistem verimi dişli sistemlerde ≈ 0,52 – 0,78, dişlisizlerde daha üsttedir. MMO değerleri (dişli 1:1 = 0,50 · dişlisiz 2:1 = 0,75) daha muhafazakârdır ve motoru büyütür.','İşaretlerseniz paftada imalatçı / marka-model referansı belirtilmelidir — program bunu not olarak yazar.'])}</label>
        <div class="bolum-bas">Boyutlar</div>
        <div class="satir i2">
          <div class="alan"><label>Hk — Kuyu yüksekliği (m)</label><input id="a_Hk${i}" class="girdi"></div>
          <div class="alan"><label>Kuyu genişliği (mm)</label><input id="a_kuyu_genisligi${i}" class="girdi"></div>
        </div>
        <div class="satir i2">
          <div class="alan"><label>Kabin boyu a (mm)</label><input id="a_kabin_boyu${i}" class="girdi"></div>
          <div class="alan"><label>Kabin genişliği b (mm)</label><input id="a_kabin_genisligi${i}" class="girdi"></div>
        </div>
        <div class="bolum-bas">Ağırlık ve motor</div>
        <div class="satir i2">
          <div class="alan"><label>Gk — Boş kabin kütlesi (kg) <span class="ipucu">Tablo-11'den</span>
            ${bilgiSimgesi(['Anma yüküne göre MMO/697 Tablo-11\'den gelir; ara yükler doğrusal enterpolasyonla bulunur.','İmalatçı verisi varsa "Ofis standardından farklı değerler" bölümündeki Gk elle alanına yazın.'])}</label>
            <input id="a_Gk_goster${i}" class="girdi salt" readonly tabindex="-1" aria-readonly="true"></div>
          <div class="alan"><label>Nsç — Motor gücü (kW) <span class="ipucu">boş = otomatik</span>
            ${bilgiSimgesi(['Boş bırakılırsa hesaplanan motor gücünden büyük ilk STANDART anma gücü seçilir ( IEC 60072 / TS EN 60034 kademeleri: 2,2 · 3 · 4 · 5,5 · 7,5 · 11 · 15 · 18,5 · 22 · 30 · 37 · 45 kW ).','İmalatçının kademesi farklıysa buraya elle yazın; program yine Nsç ≥ N kontrolünü yapar ve uymuyorsa uyarır.'])}</label>
            <input id="a_Nsc${i}" class="girdi" placeholder="otomatik"></div>
        </div>
        <div class="bolum-bas katla kapali" onclick="katla(this,'a_ozel${i}')">Ofis standardından farklı değerler
          <span class="ipucu">— boş = ofis standardı</span><span class="ozel-rozet" id="a_ozel_rozet${i}"></span></div>
        <div id="a_ozel${i}" style="display:none">
          <div class="uyari mavi" style="margin:0 0 10px">Bu alanlar <b>boş bırakıldığında</b>
            Sabitler sekmesindeki <b>ofis standardı</b> kullanılır. Yalnız bu asansörde
            farklı bir değer gerekiyorsa doldurun.</div>
          <div class="satir i2">
            <div class="alan"><label>Q elle (kg) <span class="ipucu">yalnız Tablo-7 dışı</span>
              ${bilgiSimgesi(['Normalde BOŞ kalır: anma yükü kapasiteden ( Tablo-7 ) gelir.','Yalnız tabloda karşılığı olmayan bir yük gerekiyorsa doldurun. MMO/697 Tablo-11 kapsamı 450 - 2.500 kg\'dır; bunun dışında bir yük girerseniz boş kabin kütlesini de ( Gk elle ) vermeniz gerekir, program bunu uyarır.'])}</label>
              <input id="a_Q_elle${i}" class="girdi"></div>
            <div class="alan"><label>Gk elle (kg) <span class="ipucu">boş = Tablo-11</span></label><input id="a_Gk_elle${i}" class="girdi"></div>
          </div>
          <div class="satir i2">
            <div class="alan"><label>gr — Ray birim kütlesi (kg/m)</label><input id="a_gr${i}" class="girdi ofis-alan" data-ofis="gr"></div>
            <div class="alan"><label>Fmk — Makine ağırlığı (kg)</label><input id="a_Fmk${i}" class="girdi ofis-alan" data-ofis="Fmk"></div>
          </div>
          <div class="satir i2">
            <div class="alan"><label>Fsh — Sehpa ağırlığı (kg)</label><input id="a_Fsh${i}" class="girdi ofis-alan" data-ofis="Fsh"></div>
            <div class="alan"><label>q — Denge faktörü <span class="ipucu">0 – 1</span>
              ${bilgiSimgesi(['Karşı ağırlığın dengelediği anma yükü oranı; uygulamada 0,50 alınır.','Motor gücü N = (1−q)·Q·V / (102·η′) ve karşı ağırlık Ga = P + q·Q bağıntılarına girer.','Boş bırakırsanız Sabitler / Ofis Standardı sekmesindeki değer kullanılır.'])}</label>
              <input id="a_q_denge${i}" class="girdi" placeholder="Sabitler B"></div>
          </div>
          <div class="satir i2">
            <div class="alan"><label>S1 — Kolon hattı kesiti</label>
              <select id="a_S1${i}" class="girdi ofis-alan" data-ofis="S1"><option value="">ofis standardı</option>${kesitOpt()}</select></div>
            <div class="alan"><label>L1 — Kolon hattı uzunluğu (m) <span class="ipucu">elektrik</span>
              ${bilgiSimgesi(['Boş bırakılırsa L1 = kuyu yüksekliği ( Hk ) + Sabitler sekmesindeki ofis payı kullanılır — pano ile kuyu arasındaki mesafe.','Plandan ölçtüğünüz değer farklıysa buraya yazın.'])}</label>
              <input id="a_L1${i}" class="girdi" placeholder="Hk + pay"></div>
          </div>
          <div class="satir i2">
            <div class="alan"><label>S2 — Makine besleme kesiti</label>
              <select id="a_S2${i}" class="girdi ofis-alan" data-ofis="S2"><option value="">ofis standardı</option>${kesitOpt()}</select></div>
            <div class="alan"><label>L2 — Makine besleme uzunluğu (m)</label><input id="a_L2${i}" class="girdi ofis-alan" data-ofis="L2"></div>
          </div>
          <div class="alan"><label>Kablo tipi <span class="ipucu">metne yazılır</span></label><input id="a_kablo_tipi${i}" class="girdi ofis-alan" data-ofis="kablo_tipi"></div>
        </div>
      </div></div>`;
  }
  $('a_asansorler').innerHTML=h;
}

/* Makine tipi seçilince η'yı MMO/697 s.21 değeriyle doldurur.
   Kullanıcı elle bir değer yazdıysa ona dokunmaz — yalnız hâlâ bir MMO
   değeri duruyorsa günceller, böylece "dişli seçtim ama 0,85 kaldı" olmaz. */
function verimTazele(i){
  const tip=$('a_makine_tipi'+i), alan=$('a_eta'+i);
  if(!tip||!alan) return;
  const tablo=SEC.makine_tipleri||{};
  const yeni=tablo[tip.value];
  if(yeni===undefined) return;
  const simdiki=parseFloat(String(alan.value).replace(',','.'));
  const mmoDegerleri=Object.values(tablo);
  const dokunulmamis = !isFinite(simdiki)
    || mmoDegerleri.some(x=>Math.abs(x-simdiki)<1e-9);
  if(dokunulmamis) alan.value=tr(yeni);
}

/* MRL işaretliyken makine dairesi ölçüleri kapanır — 0 yazma alışkanlığı
   yerine açık bir tercih. */
function mkYokUygula(){
  const k=$('a_mk_yok'), kutu=$('a_mk_olculer');
  if(!k||!kutu) return;
  const yok=k.checked;
  kutu.classList.toggle('sonuk', yok);
  ['a_mk_uzunluk','a_mk_genislik'].forEach(id=>{
    const e=$(id); if(!e) return;
    e.disabled=yok;
    if(yok) e.value='0';
  });
}

/* ═══════════════ OFİS STANDARDI  —  HESAP BAZINDA GRUPLU ═══════════════
   Sabitler iki ayrı yerde tutulur ve öyle kalmalıdır:

     sb_*  →  Excel'in SABİTLER sayfasındaki B bölümüne yazılır
     of_*  →  Excel'de SABİTLER'de karşılığı YOKTUR; GİRİŞ sayfasının kendi
              girdi hücrelerine yazılır  ( bkz. engine/avan.py OFIS_VARSAYILAN )

   Ama KULLANICI için bu ayrımın hiçbir anlamı yok; onun sorusu "bu sabit
   hangi hesaba giriyor".  Bu yüzden ekranda tek panel var ve alanlar
   HESABA göre gruplanıyor.  Kimlik ön ekleri ( sb_ / of_ ) değişmediği için
   dışa aktarma ve geri yükleme tarafı bundan etkilenmez. */
const SABIT_ETIKET = {
  //  sb_*  ( Excel: SABİTLER sayfası )
  i_palanga:['i — Palanga ( askı ) katsayısı','Doğrudan askı 1 / Palangalı 2'],
  q_denge:['q — Denge faktörü','karşı ağırlığın dengelediği yük oranı'],
  n_ray:['n — Kabin kılavuz ray sayısı','kabin daima iki raya oturur'],
  gf:['gf — Gezici kablo ( flexbil ) birim kütlesi (kg/m)',''],
  Fmt:['Fmt — Montör ağırlığı (kg)','kuyu üstü yükünde'],
  kabin_armatur_W:['Kabin armatürü gücü (W)','LED spot'],
  kabin_armatur_lm:['Kabin armatürü ışık akısı (lm)','5 W LED ≈ 300 lm'],
  kabin_ustu_armatur:['Kabin üstü armatür adedi','kurulu güce eklenir'],
  kuyu_armatur_W:['Kuyu armatürü gücü (W)','flüoresan'],
  kuyu_armatur_lm:['Kuyu armatürü ışık akısı (lm)','ofis teamülü 2600 lm'],
  kuyu_Dmax:['Kuyu armatürü azami aralığı (m)','0 = kontrol kapalı'],
  priz_adedi:['Priz adedi',''], priz_gucu:['Priz başına güç (W)',''],
  cosfi:['cosφ — Güç katsayısı','hat akımı hesabında'],
  UL:['UL — İzin verilen temas gerilimi (V)','TT sistem'],
  IDn:['IΔn — Kaçak akım rölesi (A)','300 mA = 0,30 A'],
  lc:['lç — Çubuk topraklayıcı boyu (m)',''],
  ayd_sutun:['Aydınlatma verimi sütunu (1-10)','Tablo-2 yansıma çifti'],
  //  of_*  ( Excel: GİRİŞ sayfasının girdi hücreleri )
  U:['U — Şebeke gerilimi (V)','fazlar arası'],
  kappa:['κ — İletken iletkenliği','bakır 56 m/Ω·mm²'],
  eps_max:['εmax — İzin verilen gerilim düşümü (%)','yönetmelik sınırı'],
  gr:['gr — Kılavuz ray birim kütlesi (kg/m)','ofis ray profili'],
  Fmk:['Fmk — Makine ağırlığı (kg)',''],
  Fsh:['Fsh — Makine sehpası ağırlığı (kg)',''],
  S1:['S1 — Kolon hattı kesiti (mm²)',''],
  S2:['S2 — Makine besleme kesiti (mm²)',''],
  L2:['L2 — Makine besleme uzunluğu (m)','pano – makine arası'],
  kablo_tipi:['Kablo tipi','paftaya metin olarak yazılır'],
  L1_pay:['L1 payı (m)','L1 = kuyu yüksekliği Hk + bu pay'],
  beta:['β — Toprak özgül direnci (Ω·m)','zemin etüdü varsa o değeri yazın'],
  cubuk_sayisi:['Is — Çubuk topraklayıcı adedi','paralel bağlı çubuk sayısı'],
  goz_araligi:['Karelaj gözü (m)','şerit boyu temel ölçülerinden türetilirken kullanılır'],
  sigorta_katsayisi:['Motor sigortası kalkış katsayısı','sigorta = bu katsayı × motor akımı, standart kademeye yuvarlanır'],
};

/*  Her sabitin HANGİ HESABA girdiği.  [ başlık, açıklama, alanlar ]
    alan = "sb:anahtar" ya da "of:anahtar" */
const SABIT_GRUP = [
  //  Kat yüksekliği ve kapı tipi burada DEĞİL — her projede değişirler,
  //  trafik hesabı sekmesinde girilirler.
  ['① MOTOR GÜCÜ VE KUVVETLER', 'MMO/697 s.18-21 — motor gücü, karşı ağırlık, ray ve kuyu dibi kuvvetleri',
   ['sb:q_denge', 'of:gr', 'sb:n_ray', 'sb:gf', 'of:Fmk', 'of:Fsh', 'sb:Fmt']],
  ['② AYDINLATMA', 'kabin · kuyu · makine dairesi aydınlatma hesapları',
   ['sb:kabin_armatur_W', 'sb:kabin_armatur_lm', 'sb:kabin_ustu_armatur',
    'sb:kuyu_armatur_W', 'sb:kuyu_armatur_lm', 'sb:kuyu_Dmax', 'sb:ayd_sutun']],
  ['③ KURULU GÜÇ VE GERİLİM DÜŞÜMÜ', 'IEC 60364-5-52 — kurulu güç, hat akımı, kablo ve gerilim düşümü',
   ['of:U', 'of:kappa', 'of:eps_max', 'sb:cosfi', 'sb:priz_adedi', 'sb:priz_gucu',
    'of:S1', 'of:S2', 'of:L2', 'of:L1_pay', 'of:kablo_tipi', 'of:sigorta_katsayisi']],
  ['④ TEMEL TOPRAKLAMA', 'IEEE Std 80 · BYKHY — temel ve çubuk topraklayıcı',
   ['of:beta', 'of:cubuk_sayisi', 'of:goz_araligi', 'sb:lc', 'sb:UL', 'sb:IDn']],
];

function sabitFormuKur(){
  const yedek = new Set(SEC.sabit_b_yedek || []);
  const B = SEC.sabit_b || {}, C = SEC.ofis_varsayilan || {};
  const deger = (kaynak, k) => (kaynak === 'sb' ? B[k] : C[k]);
  let h = '', basilan = new Set();

  SABIT_GRUP.forEach(([baslik, aciklama, alanlar]) => {
    const gecerli = alanlar.filter(x => {
      const [kaynak, k] = x.split(':');
      return !yedek.has(k) && deger(kaynak, k) !== undefined;
    });
    if(!gecerli.length) return;
    h += `<div class="bolum-bas">${baslik}${aciklama ? ` <span class="ipucu">— ${aciklama}</span>` : ''}</div>`;
    gecerli.forEach(x => {
      const [kaynak, k] = x.split(':');
      basilan.add(k);
      const [et, ip] = SABIT_ETIKET[k] || [k, ''];
      const d = String(deger(kaynak, k)).replace('.', ',');
      const girdi = (k === 'kapi_tipi')
        ? `<select id="of_${k}" class="girdi">${(SEC.kapi_tipleri||[])
             .map(v=>`<option value="${v}"${v===C[k]?' selected':''}>${v}</option>`).join('')}</select>`
        : `<input id="${kaynak}_${k}" class="girdi" value="${d}">`;
      h += `<div class="alan"><label>${et} ${ip?`<span class="ipucu">— ${ip}</span>`:''}</label>${girdi}</div>`;
    });
  });

  /*  Gruplara yazılmamış bir sabit kalırsa SESSİZCE kaybolmasın — yeni bir
      sabit eklenip SABIT_GRUP güncellenmezse burada görünür. */
  const artan = [];
  Object.keys(B).forEach(k=>{ if(!yedek.has(k) && !basilan.has(k)) artan.push(['sb',k]); });
  Object.keys(C).forEach(k=>{ if(!yedek.has(k) && !basilan.has(k)) artan.push(['of',k]); });
  if(artan.length){
    h += `<div class="bolum-bas">DİĞER <span class="ipucu">— henüz bir hesap grubuna yazılmadı</span></div>`;
    artan.forEach(([kaynak,k])=>{
      const [et,ip] = SABIT_ETIKET[k] || [k,''];
      const d = String(deger(kaynak,k)).replace('.',',');
      h += `<div class="alan"><label>${et} ${ip?`<span class="ipucu">— ${ip}</span>`:''}</label>
            <input id="${kaynak}_${k}" class="girdi" value="${d}"></div>`;
    });
  }

  //  Panelde görünmeyen alanlar ( SABIT_B_YEDEK — askı oranı ) kart
  //  başlığındaki ( ! ) balonunda anlatılır; ekranı kalabalıklaştıran
  //  bilgi bandına gerek yok.
  $('sabit_b_form').innerHTML = h;
}

function ofisSifirla(){ sabitleriSifirla(); }

/* Şablon durumu — yanlış / eski Excel konmuşsa kullanıcı XLSX indirmeyi
   denemeden önce görsün.  Hesap ve PDF bundan etkilenmez. */
async function sablonDurumu(){
  const k=$('sablon_durumu'); if(!k) return;
  let d;
  try{ d = await (await fetch('/api/sablon')).json(); }
  catch(e){ k.innerHTML=`<div class="uyari sari">Şablon durumu okunamadı: ${kacis(e.message)}</div>`; return; }
  let h='';
  if(d.uygun){
    h+=`<div class="uyari yesil"><b>Her iki şablon da doğrulandı.</b>
        XLSX çıktısı ofisin kendi paftasını üretecek.</div>`;
  }else{
    h+=`<div class="uyari kirmizi"><b>ŞABLON UYUŞMUYOR.</b> Bu dosyalarla
        <b>XLSX üretilmez</b> — sessizce yanlış pafta vermektense hiç vermemek doğrudur.
        Doğru şablonu <code>templates/</code> klasörüne koyun.
        <b>Hesap ve PDF çıktısı etkilenmez</b>, motor Excel'den bağımsızdır.</div>`;
  }
  (d.sablonlar||[]).forEach(s=>{
    h+=`<div class="serit"><span>${kacis(s.baslik)}</span>
        <span class="kaynak">${s.uygun?'doğrulandı':'uyuşmuyor'}</span></div>
        <div class="notlar" style="margin:8px 0 12px">
          <div><b>Dosya:</b> ${kacis(s.dosya)} &nbsp;·&nbsp; ${s.sayfa_sayisi} sayfa</div>
          <div><b>Parmak izi ( md5 ):</b> <code>${kacis(s.md5||'—')}</code></div>`;
    if(!s.uygun){
      h+=`<div class="uyari kirmizi" style="margin-top:8px"><b>${s.hatalar.length} sorun:</b><ul style="margin:6px 0 0 18px">`
        + s.hatalar.slice(0,12).map(x=>`<li>${kacis(x)}</li>`).join('')
        + (s.hatalar.length>12?`<li>… ve ${s.hatalar.length-12} sorun daha</li>`:'')
        + `</ul></div>`;
    }
    h+='</div>';
  });
  h+=`<div class="yardim" style="margin-top:4px">Komut satırından da bakabilirsiniz:
      <code>python3 araclar/sablon_denetle.py</code> — saniyeler sürer.
      Tam doğrulama ( LibreOffice ile yeniden hesaplatma ) için
      <code>python3 testler/calistir.py</code>.</div>`;
  k.innerHTML=h;
}

/*  ŞERİT BOYU  —  artık GİRDİ değil, TÜRETİLEN değerdir.
    Avan aşamasında elektrik projesinin topraklama planı çizilmemiş olur;
    ofiste de temel için yalnız UZUNLUK ve GENİŞLİK giriliyor.  Uygulamadaki
    kural: band temelin çevresini KAPALI RİNG olarak dolaşır, gözler
    20 × 20 m'yi geçmeyecek şekilde enine bağ atılır.  Buradan:

        L  =  2·( a + b )  +  enine bağlar

    Hesabı MOTOR yapar ( engine/avan.py · serit_boyu_tahmin ); burada yalnız
    sonucu yer tutucuda gösteririz — iki yerde iki ayrı formül bulunmasın.
    Alan boş bırakılırsa türetilen değer kullanılır; topraklama planı
    çizildiğinde plandaki gerçek boy yazılır ve o değer türetileni ezer. */

/* Temel çevresi — L ( şerit boyu ) için KARŞILAŞTIRMA bilgisi.
   Kural değildir: şeridin temelde nasıl dolaştığı projeye göre değişir,
   bazen çevreden kısa ( yalnız bir bölüm ), bazen enine bağlarla uzun olur.
   Yalnız "yazdığım sayı mantıklı mı" diye bakabilmek için gösterilir. */
function temelCevresi(){
  const e=$('a_temel_cevre'); if(!e) return;
  const a=sayiOku(v('a_temel_a')), b=sayiOku(v('a_temel_b'));
  e.textContent = (a>0 && b>0)
    ? `Karşılaştırma için: bu temelin çevresi 2·( ${tr(a)} + ${tr(b)} ) = ${tr(2*(a+b))} m.`
    : '';
}

/* Şerit boyu yer tutucusu — motorun türettiği değeri ve açılımını gösterir.
   Böylece "boş bıraktım, ne kullanıldı" sorusu ekrandan cevaplanır. */
function seritGoster(r){
  const e = $('a_serit_L'); if(!e) return;
  const oz = (r && r.ozet) || {};
  const L = oz.serit_L, ring = oz.serit_L_ring, na = oz.serit_L_na, nb = oz.serit_L_nb;
  const not = $('a_serit_tahmin');
  if(!(typeof L === 'number' && isFinite(L)) || oz.serit_L_kaynak !== 'türetilen'){
    e.placeholder = 'temel ölçülerinden türetilir';
    if(not) not.textContent = '';
    return;
  }
  e.placeholder = `${tr(L)}   ( temel ölçülerinden )`;
  if(not){
    const a = sayiOku(v('a_temel_a')), b = sayiOku(v('a_temel_b'));
    const bag = [];
    if(na) bag.push(`${na} × ${tr(b)}`);
    if(nb) bag.push(`${nb} × ${tr(a)}`);
    not.textContent = `Kullanılan: ring ${tr(ring)} m`
      + (bag.length ? `  +  enine bağ ${bag.join(' + ')}` : '  ·  enine bağ gerekmiyor')
      + `  =  ${tr(L)} m`;
  }
}

/* Türkçe / İngilizce ondalık ayracını kabul eden basit okuyucu ( yalnız
   ekranda gösterim için; hesabın kendisi sunucuda ayrıştırılır ). */
function sayiOku(x){
  const s=String(x||'').trim().replace(/\s/g,'');
  if(!s) return NaN;
  const sv=s.lastIndexOf(','), sn=s.lastIndexOf('.');
  let t=s;
  if(sv>=0 && sn>=0) t = sv>sn ? s.replace(/\./g,'').replace(',','.') : s.replace(/,/g,'');
  else if(sv>=0) t = s.replace(',','.');
  const f=parseFloat(t);
  return isFinite(f) ? f : NaN;
}

/* Q ve Gk artık GİRDİ değil, TÜRETİLEN değerdir:
     Q  = kapasiteden ( Tablo-7 ),  Gk = anma yükünden ( Tablo-11 ).
   Ana kartta salt okunur gösterilir; tablo dışına çıkmak gerekirse
   katlanır bölümdeki "Q elle" / "Gk elle" alanları kullanılır ve bu
   satırlar o zaman GİRİLEN değeri gösterir — yani her zaman hesapta
   kullanılan değer görünür. */
function turetilenGoster(r){
  const liste = (r && r.asansorler) || [];
  for(let i=1;i<=4;i++){
    const oz = (liste[i-1] || {}).ozet || null;
    const q = $('a_Q_goster'+i), g = $('a_Gk_goster'+i);
    if(q){
      q.value = (oz && oz.Q!=null) ? trn(oz.Q,0)
              : (v('a_Q_elle'+i) || (SEC.tablo_7||{})[v('a_kapasite'+i)] || '');
    }
    if(g){
      g.value = (oz && oz.Gk!=null) ? trn(oz.Gk,0) : (v('a_Gk_elle'+i) || '');
    }
    //  L1 yer tutucusu HESAPLANAN değeri gösterir: "42,00  ( Hk + 3,50 )".
    //  Böylece "kuyu yüksekliğinden mi geliyor" sorusu ekrandan cevaplanır.
    const l1 = $('a_L1'+i);
    if(l1){
      const pay = sayiOku((($('of_L1_pay')||{}).value) || (SEC.ofis_varsayilan||{}).L1_pay);
      const hk  = sayiOku(v('a_Hk'+i));
      const hes = (oz && oz.L1!=null) ? oz.L1 : ((hk>0 && pay>=0) ? hk+pay : NaN);
      l1.placeholder = isFinite(hes)
        ? `${tr(hes)}   ( Hk + ${tr(pay)} )` : 'Hk + ofis payı';
    }
  }
}

/* Katlanır "manuel değerler" bölümü kapalıyken de elle girilmiş bir değer
   olduğu görünsün — gizlenen bir ezme sessiz kalmamalı. */
function manuelRozet(){
  [['c_manuel_rozet', ['c_manuel_V','c_manuel_k']]].forEach(([rozet, alanlar])=>{
    const r=$(rozet); if(!r) return;
    const n = alanlar.filter(id=>v(id)!=='').length;
    r.textContent = n ? `${n} elle` : '';
    r.className = 'ozel-rozet' + (n ? ' dolu' : '');
  });
}

/* Asansör kartında ofis standardından SAPAN alan sayısı — katlanır bölüm
   kapalıyken de görünsün diye başlıkta rozet olarak yazılır. */
function ozelRozet(i){
  const r = $('a_ozel_rozet'+i); if(!r) return;
  const alanlar = ['Q_elle','Gk_elle','gr','Fmk','Fsh','S1','S2','L2',
                   'kablo_tipi','L1','q_denge'];
  const n = alanlar.filter(k=>v('a_'+k+i)!=='').length;
  r.textContent = n ? `${n} özel` : '';
  r.className = 'ozel-rozet' + (n ? ' dolu' : '');
}

/* Ofis varsayılanı olan alanların YER TUTUCUSU her zaman güncel değeri
   gösterir: kullanıcı panelde ray kütlesini değiştirdiğinde asansör
   kartındaki boş alan da yeni değeri "hayalet" olarak gösterir. */
function ofisTazele(){
  document.querySelectorAll('.ofis-alan').forEach(e=>{
    const k = e.dataset.ofis; if(!k) return;
    const kaynak = $('of_'+k);
    const deger = kaynak ? kaynak.value.trim() : '';
    if(e.tagName==='SELECT'){
      const ilk = e.options[0];
      if(ilk && ilk.value==='') ilk.textContent = deger ? `ofis standardı ( ${deger} )` : 'ofis standardı';
    }else{
      e.placeholder = deger || 'ofis standardı';
    }
  });
  for(let i=1;i<=4;i++) ozelRozet(i);
  manuelRozet();
}

function sabitleriSifirla(){
  //  İki kaynak da sıfırlanır: sb_* ( SABİTLER sayfası ) + of_* ( GİRİŞ hücreleri )
  Object.entries(SEC.sabit_b||{}).forEach(([k,val])=>{
    const e=$('sb_'+k); if(e) alanaYaz(e, String(val).replace('.',','));
  });
  Object.entries(SEC.ofis_varsayilan||{}).forEach(([k,val])=>{
    const e=$('of_'+k); if(e) alanaYaz(e, String(val).replace('.',','));
  });
  ofisTazele(); planla(); durum('Ofis standardının tamamı varsayılana döndürüldü');
}
function sabitATablosu(){
  const ET={gn:['gn','Yerçekimi ivmesi','m/s²','MMO/697 s.18 — TS EN 81-20'],
    tampon_katsayi:['—','Tampon altı zemin kuvvet katsayısı','—','MMO/697 §2.3.3.1-2  F = 4·gn·(P+Q)'],
    k1_hizli:['k1','Darbe faktörü — V > 1,00 m/s','—','MMO/697 Çizelge-1'],
    k1_orta:['k1','Darbe faktörü — 0,63 < V ≤ 1,00 m/s','—','MMO/697 Çizelge-1'],
    k1_yavas:['k1','Darbe faktörü — 0,15 < V ≤ 0,63 m/s','—','MMO/697 Çizelge-1'],
    motor_sabiti:['—','Motor gücü denklem sabiti','kg·m/s','MMO/697 §2.4'],
    palanga_verim_dususu:['Δη','Palangalı sistemde verim düşüşü','—','MMO/697 §2.4'],
    kirlenme_faktoru:['d','Aydınlatmada kirlenme (bakım) faktörü','—','Aydınlatma tekniği teamülü'],
    E_makine_dairesi:['E','Aydınlatma şiddeti — makine dairesi','lüx','TS EN 81-20'],
    E_kabin:['E','Aydınlatma şiddeti — kabin','lüx','TS EN 81-20'],
    E_kuyu:['E','Aydınlatma şiddeti — kuyu','lüx','TS EN 81-20'],
    kuyu_ek_armatur:['—','Kuyu aydınlatmasına eklenen armatür','adet','Kuyu dibi + kuyu üstü'],
    h_armatur:['h','Armatür ile çalışma düzlemi arası yükseklik','m','Bölge indeksi k hesabında'],
    ray_dusumu:['—','Ray uzunluğu düşümü','m','I = Hk − 0,20'],
    flexbil_sabiti:['—','Flexbil uzunluğu sabiti','m','Flexbil boyu = Hk / 2 + 3']};
  let h='<tr><th>Sembol</th><th>Büyüklük</th><th style="text-align:right">Değer</th><th>Birim</th><th>Kaynak</th></tr>';
  Object.entries(SEC.sabit_a).forEach(([k,val])=>{
    const [s,b,bi,kay]=ET[k]||[k,k,'',''];
    h+=`<tr><td><b>${s}</b></td><td>${b}</td><td class="sag">${trn(val,3)}</td><td>${bi}</td><td style="font-size:11px;color:#98A2AE">${kay}</td></tr>`;
  });
  $('sabit_a_tablo').innerHTML=h;
}

/* ek nüfus satırları */
function ekNufusEkle(p, veri){
  const liste=$(p+'_eknufus_liste');
  const d=el('div','satir i3'); d.style.marginBottom='8px';
  d.innerHTML=`<div class="alan" style="margin:0"><input class="girdi en-ac" placeholder="Açıklama" value="${kacis(veri?.aciklama||'')}"></div>
    <div class="alan" style="margin:0"><input class="girdi en-mi" placeholder="Miktar" value="${kacis(veri?.miktar??'')}"></div>
    <div class="alan" style="margin:0;display:flex;gap:6px"><select class="girdi en-ka" style="flex:1">
      ${SEC.nufus_kalemleri.map(k=>`<option value="${k}"${veri?.kalem===k?' selected':''}>${k}</option>`).join('')}</select>
      <button class="dg kucuk" onclick="this.closest('.satir').remove();planla()">×</button></div>`;
  liste.appendChild(d);
  if(!veri) planla();
}
function ekNufusTopla(p){
  const kok = $(p+'_eknufus_liste');
  if(!kok) return [];                      //  tek gövde kalktı: 't' listesi yok
  return [...kok.querySelectorAll('.satir')].map(r=>({
    aciklama:r.querySelector('.en-ac').value, miktar:r.querySelector('.en-mi').value,
    kalem:r.querySelector('.en-ka').value })).filter(x=>x.miktar!=='');
}
/* Adet değişince ek nüfus kalemleri de taşınır — karma yapıda bunlar
   nüfusun tamamını belirlediği için kaybolmaları hesabı bozardı. */

/* Avan sekmesi trafik sonucuyla karşılaştırılır: kapasite / hız / kuyu
   yüksekliği tutarsızlığı uyarı olarak görünür.  Çoklu hesap varsa o,
   yoksa tek hesap esas alınır — aktarım düğmesiyle aynı öncelik. */
function trafikKoprusu(){
  const al = x => (x && !x.hata && x.avan_koprusu
                   && (x.avan_koprusu.asansorler||[]).length) ? x.avan_koprusu : null;
  /*  Tek hesap yolu kaldı — hangi yöntemin kullanıldığı sonucun içindedir. */
  return al(SON.c);
}

/* ---------------------------------------------------------- aktarım
   Adet ve BOŞ alanlar kendiliğinden gelir ( avanSenkron ).  Bu düğme, elle
   girilmiş kapasite / hız değerlerini trafik hesabındakiyle ZORLA eşitler —
   yani "trafikte 10 kişi, avanda 13 kişi" uyarısının tek tıklık karşılığıdır.
   Trafik grubu DIŞINDAKİ asansörlere ( yük / sedye ) dokunmaz. */
function trafiktenAktar(){
  const k = trafikKoprusu();
  const liste = (k && Array.isArray(k.asansorler)) ? k.asansorler : [];
  if(!liste.length){ durum('Aktarılacak geçerli trafik hesabı yok', true); return; }
  const kaynak = k.tip==='coklu' ? 'asansör grubu trafik hesabı' : 'tek asansör trafik hesabı';
  const n = Math.min(avanTaban(), liste.length, 4);
  for(let i=1;i<=n;i++){
    const t=liste[i-1]||{};
    if(t.P!=null && t.P!=='') alanaYaz($('a_kapasite'+i), t.P);
    if(t.V!=null && t.V!=='') alanaYaz($('a_V'+i), t.V);
    delete AVAN_OTO[i];
  }
  avanSenkron();
  yaz(); planla();
  durum(`${n} asansörün kapasite ve hızı güncellendi — ${kaynak}`);
}

/* ---------------------------------------------------------- indir */
async function indir(uc){
  durum('Dosya hazırlanıyor…');
  //  KAPAK HER İSTEKTE GİDER:  sunucu proje adını yalnız dosyanın ADI ve
  //  ( XLSX'te ) dosya özellikleri için kullanır — paftanın içeriği değişmez.
  const govde = uc==='kapak-pdf'
    ? {kapak:kapakGirdi()}
    : uc.startsWith('trafik')
    ? {kapak:kapakGirdi(), girdiler:trafikGirdi()}
    : {kapak:kapakGirdi(), girdiler:avanGirdi()};
  try{
    const r = await fetch('/api/indir/'+uc, {method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(govde)});
    // Sunucu dosya yerine JSON döndürdüyse bu bir hata iletisidir — bozuk dosya indirme
    const tur = r.headers.get('Content-Type')||'';
    if(tur.includes('application/json')){
      const h = await r.json();
      durum(h.hata || 'Dosya üretilemedi', true);
      alert(h.hata || 'Dosya üretilemedi');
      return;
    }
    if(!r.ok) throw new Error('sunucu hatası '+r.status);
    const cd = r.headers.get('Content-Disposition')||'';
    let ad = 'cikti'; const m = cd.match(/filename\*=UTF-8''(.+)$/);
    if(m) ad = decodeURIComponent(m[1]);
    const b = await r.blob(), u = URL.createObjectURL(b);
    const a = document.createElement('a'); a.href=u; a.download=ad; document.body.appendChild(a); a.click();
    a.remove(); setTimeout(()=>URL.revokeObjectURL(u),3000);
    durum('İndirildi: '+ad);
  }catch(e){ durum('İndirme başarısız: '+e.message, true); }
}

/* ---------------------------------------------------------- BÜTÜN PROJE — CAD
   Kapak, trafik ve avan girdilerinin ÜÇÜ BİRDEN gönderilir; sunucu her biri
   için paftayı üretip tek bir çizim dosyasına dizer.  Hesap burada YAPILMAZ —
   ekranda ne görünüyorsa CAD çıktısı da odur ( tek kaynak motordur ). */
async function indirProjeDwg(){
  const dg = $('dg_proje_dwg');
  const eskiYazi = dg ? dg.textContent : '';
  if(dg){ dg.disabled = true; dg.textContent = 'Çizim hazırlanıyor…'; }
  durum('Proje çizimi hazırlanıyor — bütün paftalar CAD varlığına çevriliyor…');
  try{
    const govde = {kapak: kapakGirdi(),
                   girdiler: {trafik: trafikGirdi(), avan: avanGirdi()}};
    const r = await fetch('/api/indir/proje-dwg', {method:'POST',
      headers:{'Content-Type':'application/json'}, body:JSON.stringify(govde)});
    const tur = r.headers.get('Content-Type')||'';
    if(tur.includes('application/json')){
      const h = await r.json();
      durum(h.hata || 'Çizim üretilemedi', true); alert(h.hata || 'Çizim üretilemedi'); return;
    }
    if(!r.ok) throw new Error('sunucu hatası '+r.status);
    const cd = r.headers.get('Content-Disposition')||'';
    let ad = 'Avan Projesi.zip'; const m = cd.match(/filename\*=UTF-8''(.+)$/);
    if(m) ad = decodeURIComponent(m[1]);
    const notlar = (r.headers.get('X-Avan-Not')||'').split(',');
    const sadeceDxf = notlar.includes('DXF'), tasti = notlar.includes('TASMA');
    const b = await r.blob(), u = URL.createObjectURL(b);
    const a = document.createElement('a'); a.href=u; a.download=ad;
    document.body.appendChild(a); a.click(); a.remove();
    setTimeout(()=>URL.revokeObjectURL(u),3000);
    /*  DXF BİR EKSİKLİK DEĞİLDİR.  Çizim yalnız LINE + TEXT içerir; DWG'nin
        taşıyıp DXF'in taşıyamayacağı hiçbir şey yok ve AutoCAD DXF'i doğrudan
        açar.  Eski metin "bulunamadı" diye başlayıp kullanıcıya bir şey
        kaçırdığını düşündürüyordu. */
    const bicim = sadeceDxf
      ? '  —  ZIP içinde DXF var; AutoCAD birebir açar (DWG isterseniz açıp Farklı Kaydet demeniz yeterli).'
      : '  —  ZIP içinde hem DWG hem DXF var.';
    if(tasti){
      const u = 'DİKKAT: pafta sayısı proje formatının çerçevesine sığmadı, '
              + 'alta taşan sayfalar var. Çizimi baskıya göndermeden kontrol edin.';
      durum('İndirildi: '+ad+bicim+'  '+u, true); alert(u);
    }else{
      durum('İndirildi: '+ad+bicim);
    }
  }catch(e){ durum('İndirme başarısız: '+e.message, true); }
  finally{ if(dg){ dg.disabled = false; dg.textContent = eskiYazi; } }
}

function kapakGirdi(){
  const al = id => ($(id)?.value || '').trim();
  return {
    project_title:al('k_project_title'), owner:al('k_owner'), usage:al('k_usage'),
    contractor:al('k_contractor'), contractor_tax:al('k_contractor_tax'),
    city:al('k_city'), district:al('k_district'), neighborhood:al('k_neighborhood'),
    area:al('k_area'), sheet_no:al('k_sheet_no'), island_no:al('k_island_no'), parcel_no:al('k_parcel_no'),
    block:al('k_block'), capacity:al('k_capacity'), speed:al('k_speed'), stops:al('k_stops'),
    travel:al('k_travel'), cabin_width:al('k_cabin_width'), cabin_depth:al('k_cabin_depth'),
    standard:al('k_standard'), elevator_class:al('k_elevator_class'), suspension:al('k_suspension'),
    elevator_count:al('k_elevator_count'), drive_type:al('k_drive_type'), rail_size:al('k_rail_size'),
    motor_power:al('k_motor_power'), scale:al('k_scale'),
    mech_tax:al('k_mech_tax'), mech_registry:al('k_mech_registry'), mech_surname:al('k_mech_surname'),
    mech_name:al('k_mech_name'), mech_chamber:al('k_mech_chamber'),
    elec_tax:al('k_elec_tax'), elec_registry:al('k_elec_registry'), elec_surname:al('k_elec_surname'),
    elec_name:al('k_elec_name'), elec_chamber:al('k_elec_chamber'),
    company_name:al('k_company_name'), company_tax:al('k_company_tax'),
    company_tax_office:al('k_company_tax_office'), company_address:al('k_company_address')
  };
}

/* ---------------------------------------------------------- kalıcılık */
const ANAHTAR='avan_program_v1';
function tumGirdiler(){
  const o={};
  document.querySelectorAll('input,select').forEach(e=>{
    //  "_goster" alanları TÜRETİLMİŞTİR ( Q, Gk ) — girdi değildir, kaydedilmez;
    //  her hesapta yeniden doldurulurlar.
    if(!e.id || e.id.indexOf('_goster') >= 0) return;
    o[e.id] = e.type==='checkbox' ? e.checked : e.value;
  });
  o.__eknufus_c = ekNufusTopla('c');
  o.__trafik_adet = TRAFIK_ADET;
  o.__avan_ek = AVAN_EK;
  o.__avan_oto = AVAN_OTO;
  o.__avan_trf = AVAN_TRF;
  return o;
}
function yaz(){ try{ localStorage.setItem(ANAHTAR, JSON.stringify(tumGirdiler())); }catch(e){} }
function oku(){
  let o; try{ o=JSON.parse(localStorage.getItem(ANAHTAR)||'null'); }catch(e){ o=null; }
  if(o) uygula(o);
}
/* Bir alana değer yazar.
   Açılır listelerde ondalık ayracı farkı olabilir: Excel'den "1,6" gelir ama
   seçeneğin değeri "1.6"dır.  Bu durumda sayısal karşılaştırma ile eşleştirilir;
   aksi hâlde seçim boş kalır ve hesap sessizce yapılamaz. */
function alanaYaz(e, val){
  if(e.type==='checkbox'){ e.checked = !!val; return; }
  const s = (val===null||val===undefined) ? '' : String(val);
  if(e.tagName!=='SELECT'){ e.value = s; return; }
  const secenekler = [...e.options].map(o=>o.value);
  if(secenekler.includes(s)){ e.value = s; return; }
  const sayi = parseFloat(s.replace(',','.'));
  if(isFinite(sayi)){
    const esles = secenekler.find(o=>{
      const x = parseFloat(o); return isFinite(x) && Math.abs(x-sayi) < 1e-9; });
    if(esles !== undefined){ e.value = esles; return; }
  }
  e.value = secenekler.includes('') ? '' : s;
}

function uygula(o){
  Object.entries(o).forEach(([k,val])=>{
    if(k.startsWith('__')) return;
    const e=$(k); if(!e) return;
    alanaYaz(e, val);
  });
  // Ek nüfus listeleri yalnız o bölüm gerçekten verilmişse yeniden kurulur;
  // böylece kısmi yükleme (yalnız trafik ya da yalnız avan) diğerini bozmaz.
  //  Eski projelerde ek nüfus 't' ( tek gövde ) altında saklanmış olabilir;
  //  tek gövde kalktığı için 'c' boşsa oradan taşınır.
  ['c','t'].forEach(p=>{
    if(!(('__eknufus_'+p) in o)) return;
    const liste = o['__eknufus_'+p] || [];
    if(p==='t' && (o.__eknufus_c || []).length) return;
    $('c_eknufus_liste').innerHTML='';
    liste.forEach(s=>ekNufusEkle('c', s));
  });
  /* Asansör adedi: kaydedilmişse ondan, yoksa dolu çoklu kolon sayısından
     türetilir — Excel'den geri yüklemede doğru gövde açılsın. */
  let adet = parseInt(o.__trafik_adet, 10);
  if(!(adet>=1 && adet<=4)){
    const dolu=[1,2,3,4].filter(i=>$('c_P'+i) && $('c_P'+i).value!=='').length;
    adet = dolu>1 ? dolu : TRAFIK_ADET;
  }
  TRAFIK_ADET = Math.max(1, Math.min(4, adet));
  /* Trafik grubu dışı asansör adedi: kaydedilmişse ondan, yoksa Excel'den
     gelen "kullan" kutularından türetilir ( eski dosyalar için ). */
  let ek = parseInt(o.__avan_ek, 10);
  if(!(ek>=0 && ek<=3)){
    const etkin=[1,2,3,4].filter(i=>$('a_aktif'+i) && $('a_aktif'+i).checked).length;
    ek = Math.max(0, etkin - TRAFIK_ADET);
  }
  AVAN_EK = Math.max(0, Math.min(3, ek));
  AVAN_OTO = (o.__avan_oto && typeof o.__avan_oto==='object') ? {...o.__avan_oto} : {};
  AVAN_TRF = (o.__avan_trf && typeof o.__avan_trf==='object') ? {...o.__avan_trf} : {};
  cokluKolonlariGoster();
  avanKartlariGoster();
  adetDugmeleriKur();
  mkYokUygula();
  ofisTazele();
  etiketleriGuncelle();
}

/* ------------------------------------------------ Excel'den proje aç
   Programın ürettiği XLSX girdileri de taşır.  Revizyonda proje
   klasöründeki Excel'i yükleyip yalnız değişen değeri düzeltmek yeter. */
const TUR_ADI = {tek:'1 · Trafik Hesabı  ( tek asansör )',
                 coklu:'1 · Trafik Hesabı  ( asansör grubu )',
                 avan:'2 · Avan Hesapları'};

async function xlsxYukle(dosyalar){
  const liste=[...(dosyalar||[])].filter(f=>/\.xlsx$/i.test(f.name));
  if(!liste.length){ durum('Yalnız .xlsx dosyası yüklenebilir', true); return; }
  const ozet=$('yukleme_ozeti'); ozet.innerHTML='';
  const basarili=[];
  for(const f of liste){
    durum('Yükleniyor: '+f.name);
    try{
      const b64 = await new Promise((coz,red)=>{
        const fr=new FileReader();
        fr.onload=()=>coz(String(fr.result).split(',')[1]);
        fr.onerror=()=>red(new Error('dosya okunamadı'));
        fr.readAsDataURL(f);
      });
      const r = await fetch('/api/xlsx-yukle',{method:'POST',
        headers:{'Content-Type':'application/json'}, body:JSON.stringify({icerik:b64})});
      const veri = await r.json();
      if(!r.ok || veri.hata){ throw new Error(veri.hata||('sunucu hatası '+r.status)); }

      const uygulanacak = {...veri.alanlar};
      if(veri.ek_nufus_hedef) uygulanacak['__eknufus_'+veri.ek_nufus_hedef] = veri.ek_nufus||[];
      uygula(uygulanacak);
      basarili.push({ad:f.name, tur:veri.tur, ozet:veri.ozet});
    }catch(e){
      ozet.innerHTML += `<div class="uyari kirmizi" style="margin-top:10px">
        <b>${kacis(f.name)}</b><br>${kacis(e.message)}</div>`;
    }
  }
  if(basarili.length){
    yaz(); await hesaplaHepsi();
    ozet.innerHTML = `<div class="yuklendi">
      <b>${basarili.length} dosya yüklendi</b>
      ${basarili.map(b=>`<div class="satir2">▪ ${kacis(b.ad)} → <b>${TUR_ADI[b.tur]||b.tur}</b> &nbsp;(${kacis(b.ozet)})</div>`).join('')}
      <div class="satir2" style="margin-top:6px">Değişen girdiyi ilgili sekmede düzeltip
      güncel PDF / XLSX'i yeniden indirebilirsiniz.</div></div>` + ozet.innerHTML;
    durum(basarili.length+' dosya yüklendi');
  }
}

function birakAlaniniKur(){
  const a=$('birak_alani'); if(!a) return;
  a.onclick=()=>$('xlsx_ac').click();
  ['dragenter','dragover'].forEach(o=>a.addEventListener(o,e=>{
    e.preventDefault(); e.stopPropagation(); a.classList.add('uzerinde'); }));
  ['dragleave','drop'].forEach(o=>a.addEventListener(o,e=>{
    e.preventDefault(); e.stopPropagation(); a.classList.remove('uzerinde'); }));
  a.addEventListener('drop',e=>xlsxYukle(e.dataTransfer.files));
  // Sayfanın herhangi bir yerine bırakılan dosya tarayıcıda açılmasın
  ['dragover','drop'].forEach(o=>window.addEventListener(o,e=>{
    if(!a.contains(e.target)) e.preventDefault(); }));
}
function projeKaydet(){
  const ad='Asansor - avan projesi.avan';
  const b=new Blob([JSON.stringify(tumGirdiler(),null,1)],{type:'application/json'});
  const u=URL.createObjectURL(b), a=document.createElement('a');
  a.href=u; a.download=ad; a.click(); setTimeout(()=>URL.revokeObjectURL(u),3000);
  durum('Proje kaydedildi: '+ad);
}
function projeAc(ev){
  const f=ev.target.files[0]; if(!f) return;
  const fr=new FileReader();
  fr.onload=()=>{ try{ uygula(JSON.parse(fr.result)); yaz(); hesaplaHepsi(); durum('Proje açıldı: '+f.name); }
    catch(e){ durum('Dosya okunamadı', true); } };
  fr.readAsText(f); ev.target.value='';
}
function hepsiniTemizle(){
  if(!confirm('Tüm girdiler silinecek. Emin misiniz?')) return;
  localStorage.removeItem(ANAHTAR); location.reload();
}
function ornekYukle(){
  const O={c_bina_tipi:'Konut', c_bina_yuksekligi:'39,98', c_yapi_yuksekligi:'43', c_N:'11', c_h:'3',
    c_hizli1:'44', c_hizli2:'3',
    c_P1:'10', c_kg1:'900', c_kt1:'Teleskopik Otomatik',
    c_P2:'16', c_kg2:'1100', c_kt2:'Teleskopik Otomatik', c_P3:'', c_P4:'',
    /*  Ofis varsayılanı olan alanlar ( U, κ, εmax, β, çubuk adedi, ray, makine,
        sehpa, kesitler, kablo, L1, Nsç ) BİLEREK boş bırakıldı — örnek proje
        de gerçek kullanımdaki gibi bunları ofis standardından alır.
        Şerit boyu da boş: ofiste yalnız temel uzunluğu ve genişliği girilir,
        band boyu bunlardan türetilir. */
    a_temel_a:'26,55', a_temel_b:'16,4', a_serit_L:'',
    a_mk_yok:true, a_mk_uzunluk:'0', a_mk_genislik:'0',
    a_aktif1:true, a_tanim1:'İnsan', a_kapasite1:'10', a_V1:'1.6', a_eta1:'0,85', a_Hk1:'38,50',
    a_makine_tipi1:'Dişlisiz', a_i_palanga1:'2', a_toplam_verim1:false,
    a_kuyu_genisligi1:'1800', a_kabin_boyu1:'1450', a_kabin_genisligi1:'1300',
    a_aktif2:true, a_tanim2:'Sedye + Yük', a_kapasite2:'16', a_V2:'1.6', a_eta2:'0,85', a_Hk2:'38,50',
    a_makine_tipi2:'Dişlisiz', a_i_palanga2:'2', a_toplam_verim2:false,
    a_kuyu_genisligi2:'2650', a_kabin_boyu2:'1350', a_kabin_genisligi2:'2100',
    a_aktif3:false, a_aktif4:false, __eknufus_c:[],
    /* Ofisin Excel örneği 10 + 16 kişilik İKİ asansörlük bir gruptur —
       trafik adedi 2, avanda trafik dışı asansör yok. */
    __trafik_adet:2, __avan_ek:0};
  uygula(O); yaz(); hesaplaHepsi();
  durum('Örnek proje yüklendi — Excel dosyanızdaki değerler');
}

/* ---------------------------------------------------------- tablolar sekmesi */
function tablolariKur(){
  const T=SEC;
  let h='';
  h+=`<div class="serit" style="margin-top:0"><span>TABLO-1 — Binada sürekli bulunan insan sayısı</span>
      <span class="kaynak">MMO/697 s.13</span></div><div class="kaydir"><table class="veri">
      <tr><th>Kalem</th><th>Birim</th><th style="text-align:right">Kişi katsayısı</th></tr>`;
  Object.entries(T.tablo_1).forEach(([k,x])=>{
    h+=`<tr><td class="etiket">${k}</td><td>${x.birim}</td><td class="sag">${trn(x.katsayi,4)}</td></tr>`; });
  h+='</table></div>';

  h+=`<div class="serit"><span>TABLO-2 — Kabin hızları (durak adedine göre asgari)</span><span class="kaynak">MMO/697 s.13</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Bina tipi</th><th>Durak adedi</th><th>Hız (m/s)</th></tr>
      <tr><td rowspan="4" class="etiket">Konut</td><td>2 – 9</td><td>1,00</td></tr>
      <tr><td>10 – 14</td><td>1,60</td></tr><tr><td>15 – 19</td><td>2,00</td></tr><tr><td>20 ve üzeri</td><td>≥ 2,50</td></tr>
      <tr><td rowspan="5" class="etiket">Büro ve İş Merkezi</td><td>2 – 5</td><td>1,00</td></tr>
      <tr><td>6 – 10</td><td>1,60</td></tr><tr><td>11 – 15</td><td>2,00</td></tr><tr><td>16 – 19</td><td>2,50</td></tr><tr><td>20 ve üzeri</td><td>&gt; 2,50</td></tr>
      <tr><td rowspan="5" class="etiket">Otel</td><td>2 – 6</td><td>1,00</td></tr>
      <tr><td>7 – 10</td><td>1,60</td></tr><tr><td>11 – 15</td><td>2,00</td></tr><tr><td>16 – 19</td><td>2,50</td></tr><tr><td>20 ve üzeri</td><td>&gt; 2,50</td></tr>
      </table></div>`;

  h+=`<div class="serit"><span>TABLO-3 / TABLO-5 — H ve S</span><span class="kaynak">MMO/697 s.14 ve s.16</span></div>
      <div class="notlar" style="margin-top:8px">
      <div><b>H = N − Σ(i/N)^P</b> &nbsp;(i = 1…N−1) &nbsp;—&nbsp; Ortalama en yüksek dönüş katı</div>
      <div><b>S = N · ( 1 − ((N−1)/N)^P )</b> &nbsp;—&nbsp; Ortalama durak adedi</div>
      <div>Kapsam: P = 6…34 kişi, N = 1…30 kat. Program bu kapalı formülleri kullanır; değerler
        MMO/697 tablolarıyla 10⁻¹³ mertebesinde örtüşür.</div></div>`;

  h+=`<div class="serit"><span>TABLO-4 — Kapı açılma (ta) ve kapanma (tk) zamanları</span><span class="kaynak">MMO/697 s.15</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Kapı genişliği (mm)</th>`+
      T.kapi_tipleri.map(k=>`<th colspan="2" style="text-align:center">${k}</th>`).join('')+'</tr><tr><th></th>'+
      T.kapi_tipleri.map(()=>'<th style="text-align:right">ta (s)</th><th style="text-align:right">tk (s)</th>').join('')+'</tr>';
  Object.keys(T.tablo_4).sort((a,b)=>a-b).forEach(g=>{
    h+=`<tr><td class="etiket">${g}</td>`+T.kapi_tipleri.map(k=>{
      const p=T.tablo_4[g][k]||[null,null];
      return `<td class="sag">${p[0]==null?'—':tr(p[0],1)}</td><td class="sag">${p[1]==null?'—':tr(p[1],1)}</td>`;}).join('')+'</tr>';
  });
  h+='</table></div>'+
      `<div class="notlar"><div>1000 ve 1200 mm satırları MMO/697 Tablo-4'te <b>basılı değildir</b>;
      komşu satırlar arasında doğrusal enterpolasyonla türetilmiştir
      ( 1000 = (900+1100)/2 ,  1200 = (1100+1300)/2 ) ve paftada "ara değer" olarak yazılır.</div>
      <div>"Kabin İçi Oto. Kat K.Ç." sütunu 1300 mm'de tabloda yoktur; 1200 mm için de bu yüzden
      üretilememiştir — bu iki durumda imalatçı ta/tk değeri elle girilmelidir.</div></div>`;

  h+=`<div class="serit"><span>TABLO-6 — Tek katı geçme zamanı tg</span><span class="kaynak">MMO/697 s.17</span></div>
      <div class="kaydir"><table class="veri"><tr><th>V (m/s)</th><th>&lt; 1</th><th>1,00</th><th>1,60</th>
      <th>1,75*</th><th>2,00</th><th>2,50</th><th>3,00*</th><th>3,50</th><th>5,00</th><th>&gt; 5,00</th></tr>
      <tr><td class="etiket">tg (s)</td><td>10</td><td>7</td><td>6</td><td>5,8875</td><td>5,7</td><td>5,5</td>
      <td>5,25</td><td>5</td><td>4,5</td><td>4,3</td></tr></table></div>
      <div class="notlar"><div>* 1,75 ve 3,00 m/s MMO/697 Tablo-6 satır başlıklarında yoktur; komşu noktalar
      arasında doğrusal enterpolasyonla türetilmiştir ve paftada "ara değer" olarak yazılır.</div></div>`;

  h+=`<div class="serit"><span>TABLO-7 — Kabin kapasitesi / anma yükü</span><span class="kaynak">MMO/697 s.17</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Kapasite (kişi)</th>`+
      Object.keys(T.tablo_7).map(p=>`<th style="text-align:right">${p}</th>`).join('')+'</tr>'+
      '<tr><td class="etiket">Anma yükü (kg)</td>'+Object.values(T.tablo_7).map(q=>`<td class="sag">${q}</td>`).join('')+'</tr></table></div>'+
      `<div class="notlar"><div>15 kişi / 1125 kg Tablo-7'de yer almaz; MMO/697'nin s.53-54 örnek projesinde
      kullanıldığı için program tarafından "örnek istisnası" olarak desteklenir.</div></div>`;

  h+=`<div class="serit"><span>TABLO-8 — Kişi transfer zamanı tp</span><span class="kaynak">ISO 8100-32:2020, Tablo 6</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Kapı genişliği (mm)</th>`+
      Object.keys(T.tablo_8).map(g=>`<th style="text-align:right">${g}</th>`).join('')+'</tr>'+
      '<tr><td class="etiket">tp (s)</td>'+Object.values(T.tablo_8).map(x=>`<td class="sag">${tr(x,1)}</td>`).join('')+'</tr></table></div>'+
      `<div class="notlar"><div>tp, tek yolcunun kabine giriş <b>veya</b> çıkış süresidir; TR denkleminde
      <b>2·p·tp</b> olarak kullanılır.</div>
      <div>700 mm ISO 8100-32 tablosunda yoktur (tablo 800 mm'de başlar); 800→900 mm eğiminden
      dış değerleme ile <b>1,3 s</b> alınır — büyük tp, TR'yi büyüttüğü için emniyetli taraftır.
      İmalatçı verisi varsa manuel tp girin.</div></div>`;

  h+=`<div class="serit"><span>TABLO-9 — Taşınacak insan yüzdesi %k</span><span class="kaynak">MMO/697 s.17</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Bina tipi</th><th style="text-align:right">Standart</th>
      <th style="text-align:right">Yükseltilmiş</th></tr>`;
  Object.entries(T.tablo_9).forEach(([k,x])=>h+=`<tr><td class="etiket">${k}</td>
    <td class="sag">% ${tr(x['Standart']*100,1)}</td><td class="sag">% ${tr(x['Yükseltilmiş']*100,1)}</td></tr>`);
  h+=`</table></div><div class="notlar"><div>Yüksek yapı ölçütü: bina yüksekliği &gt; 21,50 m <b>veya</b>
      yapı yüksekliği &gt; 30,50 m ise Yükseltilmiş seçilir (BYKHY md.4). Program bunu kendiliğinden yapar.</div></div>`;

  h+=`<div class="serit"><span>TABLO-10 — İzin verilen en fazla bekleme zamanı Izul</span><span class="kaynak">MMO/697 s.17</span></div>
      <div class="kaydir"><table class="veri"><tr><th>Sınıf</th><th style="text-align:right">Şartlı Kabul</th>
      <th style="text-align:right">Standart</th><th style="text-align:right">Yükseltilmiş</th>
      <th>Tablo-2 hız grubu</th><th>Tablo-9 %k tipi</th></tr>`;
  Object.entries(T.tablo_10).forEach(([k,x])=>h+=`<tr><td class="etiket">${k}</td>
    <td class="sag">${x.sartli??'—'}</td><td class="sag">${x.standart??'—'}</td><td class="sag">${x.yukseltilmis??'—'}</td>
    <td>${x.hiz_grubu||'<i>manuel gerekli</i>'}</td><td>${x.k_tipi||'<i>manuel gerekli</i>'}</td></tr>`);
  h+='</table></div>';

  h+=`<div class="serit"><span>TABLO-11 — Anma yüküne göre ortalama boş kabin kütlesi</span><span class="kaynak">avan hesapları</span></div>
      <div class="kaydir"><table class="veri"><tr><th style="text-align:right">Q (kg)</th>`+
      T.tablo_11.map(x=>`<th style="text-align:right">${x[0]}</th>`).join('')+'</tr>'+
      '<tr><td class="etiket">Gk (kg)</td>'+T.tablo_11.map(x=>`<td class="sag">${x[1]}</td>`).join('')+'</tr></table></div>'+
      `<div class="notlar"><div>Standart yolcu asansörü kabini için <b>ortalama</b> değerlerdir (kabin iskeleti,
      panel, tavan, zemin, kapı, süspansiyon ve paraşüt dâhil; mermer/granit kaplama ve özel dekor hariç).
      Ara yükler doğrusal enterpolasyonla bulunur. İmalatçı verisi varsa "Gk elle" alanına yazın.</div></div>`;

  h+=`<div class="serit"><span>KABLO AKIM TAŞIMA KAPASİTESİ</span>
      <span class="kaynak">IEC 60364-5-52 Tablo B.52.4 — bakır, PVC, 3 yüklü iletken, Yöntem C</span></div>
      <div class="kaydir"><table class="veri"><tr><th style="text-align:right">Kesit (mm²)</th>`+
      Object.keys(T.kablo_iz).map(k=>`<th style="text-align:right">${tr(Number(k),1)}</th>`).join('')+'</tr>'+
      '<tr><td class="etiket">Iz (A)</td>'+Object.values(T.kablo_iz).map(x=>`<td class="sag">${tr(x,1)}</td>`).join('')+'</tr></table></div>';

  $('tablolar_ic').innerHTML=h;
}

/* ═══════════════════════════════════════════════════════════════════════
   AÇILIŞ EKRANI
   Program açıldığında hangi projenin hazırlanacağı seçilir.  Şimdilik
   yalnız "Avan Proje" hazır;  uygulama projesi bölümü sonra eklenecek.
   ═══════════════════════════════════════════════════════════════════════ */
function uygulamaAc(hangi){
  if(hangi !== 'avan'){
    //  Hazır olmayan bölüm sessizce yutulmaz — kullanıcı neden açılmadığını bilsin.
    durum('Uygulama projesi bölümü henüz hazır değil — şimdilik Avan Proje ile devam edin.', true);
    alert('UYGULAMA PROJESİ\n\nBu bölüm henüz hazır değil, daha sonra eklenecek.\n'
        + 'Şimdilik "AVAN PROJE" ile devam edebilirsiniz.');
    return;
  }
  document.body.classList.remove('giriste');
  window.scrollTo(0, 0);
  durum('Avan proje — 1 · Trafik Hesabı ile başlayabilirsiniz.');
}

function anaEkran(){
  document.body.classList.add('giriste');
  window.scrollTo(0, 0);
}

kur();
