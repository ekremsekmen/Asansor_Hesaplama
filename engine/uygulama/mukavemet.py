# -*- coding: utf-8 -*-
"""
MUKAVEMET HESAP MOTORU              ( UYGULAMA PROJESİ  —  avandan ayrıdır )

Kaynak Excel:  templates/MUKAVEMET_HESABI.xlsx
               "11-Muk. Hesapları" + "Askı Tipleri" sayfaları

Standartlar:  TS EN 81-20 · TS EN 81-50 · TS 12385-5 · ISO 7465
              MMO 208/7 m.2.4  ( motor gücü )
              MMO 208/4 m.3.4.6 ( makine konstrüksiyonu )

Bölümler
  1  Asansör motor gücü                       MMO 208/7 - 2.4
  2  Makine konstrüksiyonu                    MMO 208/4 - m.3.4.6
  3  Kullanılabilir kabin alanı               EN 81-20 m.5.4.2
  4  Askı halatları                           EN 81-50 m.5.12
  5  Hız regülatörü halatı                    EN 81-20 m.5.6.2.2.1
  6  Tahrik yeteneği                          EN 81-50 m.5.11.2 / m.5.11.3
  7  Kabin kılavuz rayları                    EN 81-50 m.C.2.1 / C.2.2 / C.2.3
  8  Karşı ağırlık kılavuz rayları            EN 81-50 m.5.10
  9  Kuyu tabanına gelen yükler               EN 81-20 m.5.2.1.8
 10  Sığınma alanları ve açıklıklar           EN 81-20 m.5.2.5.7 / 5.2.5.8

Çıktı biçimi avan motoruyla aynıdır ( engine.steps.Bolum / veri / hesap /
kontrol ), böylece ekran, PDF ve XLSX katmanları ortak kalır.
"""
import math

from engine.uygulama import mukavemet_girdi as MG
from engine.uygulama import sabitler as US
from engine.uygulama import mukavemet_tablolari as MT
from engine.ortak.steps import Bolum, hesap, kontrol, numarala, veri
from engine.ortak.steps import metin, tr, trn

# =====================================================================
#  KAYNAK EXCEL'DEN BİLEREK AYRILAN NOKTALAR
# =====================================================================
#  Uyulması gereken standart TS EN 81-20 / TS EN 81-50'dir;  kaynak Excel
#  yalnız bir başlangıç noktasıdır.  Aşağıdaki noktalarda Excel standarttan
#  ayrılıyor — motor STANDARDI uygular, Excel'i değil.
#
#  Her satır:  ( kısa ad , standart maddesi , Excel'in yaptığı , motorun yaptığı ,
#                etkilenen "11-Muk. Hesapları" hücreleri )
#  Doğrulama testleri bu listeyi okur;  bir sapma sessizce kapanır ya da
#  yenisi eklenirse test bunu söyler.
EXCEL_FARKLARI = (
    ("Kasnak atalet terimi hiç hesaba girmiyordu",
     "TS EN 81-50 m.5.11.2.2 a)  ·  Ek D",
     "T1 ve T2'de kasnak ataletinden gelen terimler yapıda vardır ama "
     "hiçbir girdiden beslenmez, hep sıfırdır;  Σ( mPcar·iPcar·a )/r terimi "
     "ise hiç yoktur.",
     "Madde  mPcar = J·( v_kasnak/v )²/R²  der:  kasnağın ATALET MOMENTİ.  "
     "J bir bileşen özelliğidir ve standart onu imalatçıdan bekler — ama "
     "sahada kimse kasnağın atalet momentini veri sayfasından okuyup "
     "girmez.  Bu yüzden kasnak, ÇAPI VE HALAT DÜZENİ ZATEN BİLİNEN bir "
     "döküm disk olarak modellenir;  kullanıcıdan yeni bir girdi "
     "İSTENMEZ:\n"
     "            J  = ½·π·ρ·A·( R⁴ − R₁⁴ ) + ½·π·ρ·A₁·R₁⁴\n"
     "            R  = Dp/2   ·   R₁ = ( Dp − göbek payı )/2\n"
     "            A  = ( ns−1 )·1,6·dr + kanal payı   ·   A₁ = A × oran\n"
     "        Dp, ns ve dr formda ZATEN vardır;  ρ, göbek payı, kanal payı "
     "ve göbek oranı ofis kabulüdür ve Sabitler sekmesinde durur.\n"
     "        KASNAK SAYILARI EK D'DEDİR:  2:1 çözümlü örneği katsayıları "
     "açık yazar — kabin tarafı  mPcar·2·a/2 , ağırlık tarafı  mPcwt·1·a/2 . "
     "Yani 2 ve 1;  tahmin değil, standardın kendi örneği.\n"
     "        J MODELİ DOĞRULANDI:  ELEport'un yayımlanmış paftasında "
     "Dp = 294 mm ve 7 × 6,5 mm halat için J = 0,29 kg·m² yazılıdır;  bu "
     "bağıntı 0,2920 verir  ( %0,7 ).\n"
     "        BÜYÜKLÜĞÜ:  varsayılan projede terim T1/T2 oranını %0,17 "
     "büyütür ( 1,6285 → 1,6313 ).  Küçüktür ama YÖNÜ emniyetsizdir "
     "( atlamak kontrolü kolaylaştırır ) ve askı oranı ile kasnak ataleti "
     "büyüdükçe payı artar.  Koşul III gereği yalnız askı oranı > 1 iken "
     "hesaba girer;  1:1'de kasnak yoktur, terim sıfırdır.",
     ("AF250", "AJ255", "K257", "AH264", "AF269", "K271")),
    ("Askı noktası ( S ) sabit sıfır alınıyordu",
     "TS EN 81-50 Ek C.1.2 / C.2.2.1 / C.2.3.1",
     "Kabin merkezinin kaçıklığını sorar ama halatların NEREDEN asıldığını "
     "sormaz;  xs ve ys yoktur.",
     "Ek C.1.2 ray eksenini orijin alıp BEŞ nokta tanımlar:  kabin merkezi "
     "( C ), boş kabin kütlesi ( P ), beyan yükü ( Q ), ASKI ( S ) ve kapı.  "
     "Kaçıklık ağırlığın nerede DURDUĞU, askı ise nereden ASILDIĞIDIR;  ray "
     "kuvveti ikisinin arasındaki moment kolundan doğar — C.2.2.1 ve C.2.3.1 "
     "bu yüzden ( xQ − xs ) ve ( yp − ys ) yazar.  İkisi bağımsızdır:\n"
     "            kabin ortada · askı 200 kaçık  →  kaçıklık 0 iken kuvvet VAR\n"
     "            kabin 200 kaçık · kendi üstünden asılı  →  boş kabin momenti SIFIR\n"
     "        C.2.1'DE ( güvenlik tertibatı ) askı geçmez:  tertibat RAYI "
     "kavradığı için tepki ray ekseninden ölçülür.  Bölümün hükmünü genelde "
     "o durum verdiğinden ( k1 = 2 ) varsayılan xs = ys = 0 çoğu projede "
     "sonucu değiştirmez;  eksantrik askılı yerleşimde C.2.2 kuvvetleri "
     "%100'ü aşan oranda sapıyordu.\n"
     "        YÜK YÖNÜ AYRI SEÇİLİR:  en olumsuz yük konumu ( m.5.7.2.3.4 ) "
     "C.2.1 ile C.2.2'de farklı çıkabilir, çünkü birinin momenti askıyı "
     "taşımaz.  Tek bir yön seçip ikisine birden vermek yanlıştı.\n"
     "        VARSAYILAN 0'DIR — mevcut projelerin tek sayısı değişmez.",
     ()),
    ("Tamponlar hiç denetlenmiyordu",
     "TS EN 81-20 m.5.8.1 / m.5.8.2 / m.5.2.1.8.5",
     "Tamponu yalnız YERLEŞİM ölçüsü olarak tanır:  baba yüksekliği, ezilme "
     "miktarı ve uzunluk sığınma açıklıklarına ve halat boyuna girer.  "
     "Tampon TİPİ hiç sorulmaz, strok yeterliliği hiç denetlenmez, kuyu "
     "tabanı kuvveti tampon adedine bölünmez.",
     "m.5.8.1 tamponları üçe ayırır ve her birine BAŞKA kural bağlar;  "
     "hangisinin geçerli olduğunu tip belirler:\n"
     "            m.5.8.1.5    enerji biriktirmeli  →  v ≤ 1 m/s\n"
     "            m.5.8.2.1.1  lineer               →  strok ≥ 0,135·v² , ≥ 65 mm\n"
     "            m.5.8.2.2.1  enerji yutmalı       →  strok ≥ 0,0674·v²\n"
     "            m.5.8.2.1.2  lineer olmayan       →  bağıntı yok, TİP DENEYİ\n"
     "        Tip sorulmadığı için bunların hiçbiri denetlenemiyordu:  2,5 m/s "
     "beyan hızında 90 mm'lik bir tampon sessizce geçiyordu, lineer tamponda "
     "gereken 844 mm'dir.  Poliüretan tampon 1,6 m/s'de hiç kullanılamaz "
     "( m.5.8.1.5 ) — bu da görülmüyordu.  EMNİYETSİZ taraf.\n"
     "        m.5.2.1.8.5 kuyu tabanı kuvvetini \"evenly distributed between "
     "the total number of car buffers\" der;  döşemenin yerel olarak "
     "taşıyacağı sayı tampon BAŞINA düşendir.  Toplam kuvvet duruyor, yanına "
     "Fkt1 = Fkt / ncar eklendi ( ELEport da böyle yazar ).\n"
     "        m.5.8.2.1.2.2 \"tam ezilmiş\" durumu kurulu yüksekliğin %90'ı "
     "diye tanımlar;  girilen ezilme bundan küçükse kuyu dibi açıklığı "
     "olduğundan büyük çıkar — uyarı verilir ( bkz. MG.uyarilar ).\n"
     "        YENİ BÖLÜM:  \"TAMPONLARIN KONTROLÜ\".  Kaynak kitapta karşılığı "
     "olmadığı için ayrışan hücre yoktur;  bölüm tamamen eklemedir.",
     ()),
    ("Acil frenlemede ivme işaretleri ters",
     "TS EN 81-50 m.5.11.2.2  ·  Ek D",
     "T1 ve T2'yi 11!D235…AF283 satırlarındaki beş elemanlı işaret "
     "demetleriyle kurar;  yüklü kabin en alt durakta frenlerken KABİN "
     "tarafına ( gn − a ), KARŞI AĞIRLIK tarafına ( gn + a ) verir.  Boş "
     "kabin en üstte durumunda da aynı şekilde terstir.",
     "Maddenin kuralı açıktır:  \"the upper operation is applicable in case "
     "the car with its rated load is retarding in the DOWN direction and "
     "the lower operation in case the empty car is retarding in the UP "
     "direction\".  Yüklü kabin aşağı inerken fren tutunca kabin YUKARI "
     "yönde yavaşlar;  halat kabini tutmak için daha ÇOK gerilir "
     "( gn + a ), karşı ağırlık tarafı ise daha AZ ( gn − a ).\n"
     "        Ek D'nin çözümlü örneği ( 2:1, dengeleme yok ) bunu açıkça "
     "yazar:\n"
     "            T1 = (P+Q)/2·( gn + a ) + MSRcar·( gn + 2a ) − FRcar/2\n"
     "            T2 = Mcwt/2·( gn − a )                       + FRcwt/2\n"
     "        Ters işaret T1'i küçültüp T2'yi büyüttüğü için T1/T2 oranı "
     "%36 KÜÇÜK çıkıyordu:  varsayılan projede 1,199 yerine 1,628.  "
     "Tahrik yeteneği kontrolü ( T1/T2 ≤ e^(f·α) ) böylece olduğundan "
     "kolay geçiliyordu — EMNİYETSİZ taraf.  Örneklenen 16 asansörün "
     "12'sinde hüküm UYGUN'dan UYGUN DEĞİL'e döner.\n"
     "        ELEport'un paftası da Ek D ile aynı işaretleri yazar "
     "( \"stops with emergency brake while descending\" başlığı altında "
     "T1 = (Q+P)·(gn+a)/r … − FRcar/r ).\n"
     "        Ayrıca mDP terimi 2'ye bölünüyordu;  standart r'ye böler "
     "( 2:1 askıda aynı, 1:1'de yanlış ).  Sürtünme kuvvetleri de artık "
     "kendi tarafının sürtünmesiz kuvvetinden türetilir;  eskiden ayrı ve "
     "farklı yönlü bir işaret tablosu vardı.",
     ("AF250", "AJ255", "K257", "AH264", "AF269", "K271")),
    ("Burkulma narinliği büyük atalet yarıçapından ölçülüyordu",
     "TS EN 81-50 m.5.10.3",
     "λ = konsol arası / ix.  Ray tablosundan ix SÜTUNUNU okur "
     "( VLOOKUP 'Veri Girişi'!E73 ; TABLOLAR!I60:S65 ; 8 ; 0 ) — 8. sütun "
     "ix'tir, iy 9. sütundadır ve hiç okunmaz.",
     "Maddenin kendi sembol listesi  \"i is the MINIMUM radius of "
     "gyration\"  der:  kolon hangi eksende zayıfsa orada burkulur.  Ray "
     "konsolları iki yönde de aynı aralıkta bağladığı için seçici olan "
     "kesitin kendisidir ve ISO 7465 T raylarının çoğunda iy < ix'tir — "
     "kataloğun altı profilinden beşinde.  Büyük yarıçapla bölmek λ'yı, "
     "dolayısıyla ω'yı ve burkulma gerilmesini KÜÇÜK gösterir:\n"
     "            70 x 65 x 9   ω 3,50 yerine 7,81   ( %123 eksik )\n"
     "            90 x 75 x 16  ω 2,60 yerine 5,00   ( % 92 eksik )\n"
     "        50 x 50 x 5 rayında 2 m konsolda σk 96,8 yerine 205,7 N/mm² "
     "çıkar ve σperm = 205'i AŞAR — hüküm UYGUN'dan UYGUN DEĞİL'e döner.  "
     "EMNİYETSİZ taraf.\n"
     "        İki bağımsız kaynak da aynı yerdedir:  Nick Mellor'un EN "
     "81-50 incelemesi  \"the lesser of the two radii of gyration\"  der;  "
     "ELEport'un paftası ray verisinde yalnız iy'yi listeler ve "
     "λ = l / iy yazar.\n"
     "        YAN ETKİ:  kitabın kendi varsayılanı ( 50 x 50 x 5 ağırlık "
     "rayı + 3.000 mm konsol ) doğru yarıçapla λ = 285 verir, yani ω "
     "tablosunun dışına düşer.  Formun varsayılan konsol aralığı bu yüzden "
     "2.500 mm'ye çekilmiştir ( bkz. mukavemet_girdi.ALAN ).",
     ("AV354", "AV355", "AD354", "AL354", "AE365", "AE374")),
    ("Kabinin y kaçıklığı Fy'ye girmiyordu",
     "TS EN 81-50 Ek C.1.2 / C.2.1.1 b) / C.2.2.1 b) / C.2.3.1 b)",
     "Fy'nin payındaki yc ve yp'yi SABİT SIFIR alır:  'Veri Girişi'!C76'ya "
     "girilen kabin kaçıklığı yalnız kapı eşiğinin konumuna ( yi ) gider, "
     "kabinin kendi ağırlık merkezine gitmez.",
     "Ek C.1.2 ikisini de tanımlar:  yc 'kabin merkezinin ray "
     "koordinatlarına göre konumu', yp 'boş kabin kütlesinin (P) konumu'.  "
     "Ek C.2.1.1 b) Fy = k1·gn·( Q·yQ + P·yp ) / ( (n/2)·h ) der ve "
     "yQ = yc ( Durum 1 ) ya da yc + Dy/8 ( Durum 2 ) alınır — üçü de "
     "kaçıklıktan beslenir.  Sıfır alınınca kabin ne kadar kaçık olursa "
     "olsun Fy değişmiyordu:  200 mm kaçıklıkta 836,7 N, doğrusu "
     "2.567,9 N — üç katı, EMNİYETSİZ taraf.\n"
     "        ELEport'un paftası da Yp'yi gerçek bir girdi olarak taşır "
     "( örnek projesinde Yp = −15,0 cm ) ve  Fy = k2·gn·( Q·(yQ−Ys) + "
     "P·(Yp−Ys) ) / ((n/2)·h)  yazar.\n"
     "        KAÇIKLIK SIFIRKEN HİÇBİR HÜCRE DEĞİŞMEZ;  aşağıdaki adresler "
     "yalnız gerçek bir kaçıklık girildiğinde ayrışır.",
     ("AY327", "AU330", "Z360", "AJ362", "AE365", "AH396",
      "K344", "AU347", "Z369", "AJ371", "AE374", "AH404", "Z312",
      "L424", "AU427", "Z461", "AC463", "AH490",
      "L444", "AU447", "Z468", "AH470", "AH498",
      "L516", "AU519", "Z530", "AF532", "AH545")),
    ("Karşı ağırlığın ölçüleri tablodan türetiliyordu",
     "TS EN 81-50 Ek C.2.2",
     "Karşı ağırlığın iki ölçüsünü de tablodan bulur:  derinliği "
     "MALZEMEDEN ( VLOOKUP B118 → 150 / 100 mm ), genişliği RAY ARASINDAN "
     "( HLOOKUP B119 ; X59:Z60 ; 2 ; 0 — TAM EŞLEŞME, yalnız 700 · 1050 · "
     "1400 ).  Genişlik girdisi bu yüzden üç değere kilitliydi;  1200 mm "
     "ray arası olan bir kuyuda mühendis 1050 seçmek zorunda kalıyor ve "
     "genişlik 154 mm yanlış çıkıyordu — hata eksantriklik Dya üzerinden "
     "ray gerilmesine ve sehimine geçiyordu.",
     "İKİSİ DE GİRDİDİR ( Gx · Gy ).  Ek C.2.2 karşı ağırlığın KENDİ "
     "ölçülerini veri olarak ister;  standardı izleyen ray hesabı kılavuzu "
     "da öyle yapar ( 'Gx = 130 mm, Gy = 960 mm Counterweight dimensions', "
     "XG = %10 × Gx, YG = %5 × Gy ) ve referans uygulama projesi de ikisini "
     "doğrudan sorar.  Ölçü ne ray arasının ne malzemenin özelliğidir — "
     "imal edilen çerçevenin özelliğidir.  Program kabin tarafında zaten "
     "böyle yapıyordu.  Ray arası pafta bilgisi olarak sorulmaya devam "
     "eder, hesaba girmez.",
     #  HÜCRE LİSTESİ BOŞ.  Bu bir formül sapması değil, GİRDİ SÖZLEŞMESİ
     #  değişikliğidir:  özgün kitapta bu iki girdinin hücresi hiç yoktur,
     #  ölçüleri kendi tablolarından türetir.  Aynı girdilerle iki tarafı
     #  karşılaştırıp "şu hücrede ayrışıyoruz" demek mümkün değil;  ayrışma
     #  ancak kitabın göremediği bir ölçü girildiğinde doğar ve bütün karşı
     #  ağırlık rayı bölümüne yayılır.  Serbest ölçülerin doğruluğu TESLİM
     #  EDİLEN kitapta denetlenir ( bkz. test_mukavemet_excel — "serbest
     #  ölçü" bloğu ).
     ()),
    ("Tahrik kasnağı / halat oranı",
     "TS EN 81-20 m.5.5.2.1",
     "Başlık '≥ 40' yazar ama kontrolü 30 ile yapar. 30, aynı standardın "
     "m.5.5.6.2 c) dengeleme gergi kasnağı ve m.5.6.2.2.1.3 regülatör eşiğidir.",
     "Standardın istediği 40 uygulanır.",
     ()),
    ("Kapı konumu xi ham mesafe olarak yazılıyordu",
     "TS EN 81-50 Ek C.1.2 / C.2.3.1",
     "xi'ye ray–kapı arasını HAM MESAFE olarak yazar ( hep artı ).  Oysa aynı "
     "toplamdaki xp ray ekseninden ölçülen İŞARETLİ bir konumdur.",
     "Ek C.1.2 xi'yi 'the position of the car door' diye, xC · xp · xQ · xS "
     "ile AYNI Kartezyen sistemde tanımlar.  Kapı düzlemi ray ekseninin "
     "kabin merkezine göre TERS tarafındadır:  kabin merkezi +xc'de ise kapı "
     "−RK'dedir.  Ray ekseni kabin merkezini geçtiğinde ( xc < 0 ) eşik "
     "kuvveti Fs ile boş kabinin momenti yanlış yönde toplanıyor ve "
     "birbirini DENGELİYORDU.\n"
     "        1400 mm derinlikte ray–kapı arası 1.200 mm iken yükleme "
     "durumunun Fx'i 8,2 N çıkıyor, doğrusu 864,4 N — 105 kat, EMNİYETSİZ "
     "taraf.  Ray ekseni kabin merkezinin kapı tarafındayken ( xc > 0 ) "
     "kitabın değeri fazla emniyetliydi.",
     ("AH299", "L508", "AU511", "L516", "AU519", "Z530", "AF532", "Z537",
      "AH542", "AH545")),
    ("Yük yalnız + yönde kaydırılıyordu",
     "TS EN 81-20 m.5.7.2.3.4",
     "xQ'yu her zaman xc + Dx/8 alır.  Ek C'nin Şekil C.2'si kaymayı tek "
     "yönde gösterir ama Ek C BİLGİLENDİRİCİDİR ve bir örnektir.",
     "Madde NORMATİFTİR ve şöyle der:  beyan yükü, kabin alanının en "
     "OLUMSUZ konumdaki dörtte üçüne eşit dağıtılır.  Dx/8 zaten bunun "
     "geometrik sonucudur ( 3/4 alan yüklenince merkez Dx/2 − 3·Dx/8 = Dx/8 "
     "kayar );  yön ise SEÇİLMELİDİR.\n"
     "        Ek C.2.1.1'in payı  Q·xQ + P·xp  bir moment toplamıdır.  Kabin "
     "merkezi ray ekseninin öbür yanındaysa ( xc < 0 ) boş kabinin momenti "
     "negatiftir ve yükü + yönde kaydırmak onu DENGELER:  toplam moment "
     "küçülür, ray gerilmesi ve sehimi olduğundan küçük çıkar, bölüm "
     "'UYGUNDUR' der.  Yolcular öbür yana yığıldığında ray hesaplanandan "
     "büyük yük görür — EMNİYETSİZ taraf.\n"
     "        Artık ± iki konum da denenip momenti büyüten seçilir.  1400 mm "
     "derinlikte ray–kapı arası 1.200 mm iken Fx 192 N yerine 2.114 N "
     "çıkıyor ( 11 kat ) ve sehim 5 mm sınırını aşıyor.  Simetrik yerleşimde "
     "( xc = 0 ) iki yön aynı sonucu verir.",
     ("Z309",)),
    ("Altı kesik V kanalda Nequiv(t) yanlış satırdan okunuyordu",
     "TS EN 81-50 m.5.12.2.2 Çizelge 2",
     "Altı kesik V kanalı Çizelge 2'nin ALT KESME ( β ) satırından okur:  "
     "β = 90° için 5,0.  Oysa aynı kanalın V açısı γ = 38°'dir ve V satırı "
     "12 verir.  Nequiv küçük çıkınca gereken güvenlik katsayısı da küçülür.",
     "Çizelge 2'nin iki satırı 'V-grooves' ( γ ) ve 'U-Undercut grooves' "
     "( β )'dir;  altı kesik V için ayrı bir satır YOKTUR.  Standardın kendi "
     "sınıflandırması nettir:  m.5.11.2.3.1.1 yarım daire ve altı kesik yarım "
     "daire kanalları, m.5.11.2.3.1.2 ise V kanalları ele alır — ve altı "
     "kesik V açıkça İKİNCİSİNİN içindedir ( 'sertleştirilmemişse alt kesme "
     "gereklidir' ).  m.5.12.2'nin girişi de kanalları 'U- ya da V-' diye "
     "ikiye ayırır.\n"
     "        Örnek projede gereken Sf 15,51 yerine 20,55 çıkar ( %32,5 ) — "
     "yani hata EMNİYETSİZ yöndeydi.",
     ("AH104", "V116", "T125")),
    ("Normal işletme ve yüklemede Fy'nin paydası",
     "TS EN 81-50 Ek C.2.2.1 b) / C.2.3.1 b)",
     "Fy'yi ( n × h )'ye böler.  Oysa standart üç yük durumunda da "
     "( n / 2 ) × h yazar;  kitap yalnız güvenlik tertibatı durumunda "
     "( C.2.1.1 b) ) doğru paydayı kullanıyordu.",
     "Fy = k2·gn·[ Q·(yQ−yS) + P·(yp−yS) ] / ( (n/2)·h ).  Payda yarıya "
     "inince Fy İKİ KAT büyür;  kitabın değeri gerçeğin YARISIYDI ve hata "
     "EMNİYETSİZ yöndeydi.  Aynı düzeltme karşı ağırlık rayına da uygulanır.",
     ("L444", "AU447", "AH498", "L516", "AU519", "AH545", "AP572", "AH603")),
    ("Normal işletme katsayısı k2 yerine k3 deniyordu",
     "TS EN 81-20 Çizelge 14  /  TS EN 81-50 Ek C.2.2.1",
     "Normal işletme eğilme gerilmesinde katsayıya 'k3' der.  Çizelge 14'te "
     "k2 ( Running ) = 1,2 iken k3 yardımcı donanım katsayısıdır ve çizelge "
     "ona SAYI VERMEZ:  'the value has to be determined by the manufacturer "
     "due to the actual installation'.",
     "Katsayı k2 olarak adlandırılır ( değeri 1,2, çizelgeden ).  k3 ise "
     "ofis sabiti oldu ( sabitler.k3_yardimci, varsayılan 1,2 ):  standardın "
     "vermediği bir sayıyı motorda çivilemek yanlıştır.  Sayısal sonuç "
     "varsayılanda değişmez, ad ve kaynak düzelir.",
     ()),
    ("Konsol klipslerinin itme kuvveti Fp hiç yoktu",
     "TS EN 81-50 Ek C.2.1.2 / C.2.2.2 / C.2.3.2",
     "Fv'yi 'k1·gn·(P+Q)/n + Mg·gn' ( ya da 'Mg·gn' ) diye kurar;  "
     "standardın üç bağıntısında da bulunan + Fp terimi yoktur.",
     "Fp, bir raydaki bütün konsol klipslerinin itme kuvvetidir ( binanın "
     "oturması, betonun büzülmesi ).  Girdi olarak eklendi;  varsayılanı 0 "
     "olduğu için normal hesap değişmez, ama tesis bir değer veriyorsa artık "
     "hesaba girer.",
     ()),
    ("Bina yapısının sehimi δstr hiç yoktu",
     "TS EN 81-50 Ek C.2.1.5 / C.2.2.5 / C.2.3.5",
     "Sehim ölçütünü 'δ = 0,7·F·l³/(48·E·I) ≤ δperm' diye kurar;  standardın "
     "üç bağıntısında da bulunan + δstr terimi yoktur.",
     "δstr binanın kendi sehimidir ve rayın sehimine EKLENİR.  δstr-x ve "
     "δstr-y girdi oldu;  varsayılanları 0.",
     ()),
    ("Makaralı paten flanş formülü hiç yoktu",
     "TS EN 81-50 m.5.10.5 / Ek C.2.1.4",
     "Yalnız kaymalı paten formülünü tanır;  paten tipi sorulmaz.",
     "Madde İKİ formül verir ve hangisinin geçerli olduğunu paten tipi "
     "söyler:  makaralı patende σF = 1,85·Fx/c².  Paten tipi girdi oldu "
     "( varsayılan Kaymalı — kitabın kabulü ).  Örnek projede makaralı "
     "seçilirse σF 13,40 yerine 16,55 N/mm² çıkıyor:  %24 daha büyük, yani "
     "eksikliği EMNİYETSİZ yöndeydi.",
     ()),
    ("Boş kabinin ağırlık merkezi kabin merkezinden ölçülüyordu",
     "TS EN 81-50 Ek C.2.1.1",
     "xp'yi yalnız kapı + mekanizma kütlesinin KABİN MERKEZİNE göre "
     "kaçıklığından kurar:  xp = mkapı·( D/2 + pay ) / P.  Oysa aynı "
     "toplamdaki xQ ray ekseninden ölçülür ( xQ = xc + D/8 ) ve xc, "
     "ray–kapı arası değiştikçe kayar.  xp ise HİÇ KIMILDAMAZ:  kabin "
     "gövdesinin ray eksenine göre kaçıklığı sayılmıyordu.",
     "Fx = k1·gn·( Q·xQ + P·xp ) / ( n·h ) bağıntısının payı, sistemin RAY "
     "EKSENİNE göre devirici momentidir;  iki moment kolu da aynı orijinden "
     "ölçülmek zorundadır.  Boş kabin, gövde ( P − mkapı ) xc'de ve kapı "
     "( mkapı ) xc − ( D/2 + pay )'da olacak şekilde toplanır:\n"
     "            xp = xc − mkapı·( D/2 + pay ) / P\n"
     "        Ray ekseni kabin merkezinden geçtiğinde ( xc = 0 ) iki okuma "
     "aynı büyüklüğü verir — kitabın örneği oradadır — ama ray kaydıkça "
     "ayrışır ve EMNİYETSİZ tarafa da düşer:  1400 mm derinlikte ray–kapı "
     "arası 500 mm iken moment toplamı gerçeğin %79'u, 1000 mm iken %36'sı "
     "çıkıyordu.",
     ("AH295", "AY321", "AU324", "Z360", "AJ362", "AH393",
      "L415", "AU418", "Z461", "AC463", "AH487", "L508", "AU511",
      "Z530", "AF532", "AH542")),
    ("Saptırma kasnağı / halat oranı denetlenmiyordu",
     "TS EN 81-20 m.5.5.2.1",
     "Yalnız TAHRİK kasnağını sınar.  Saptırma kasnağının çapı ( D2 ) hesaba "
     "sadece Kp = (Dt/Dp)⁴ olarak girer;  kendi oranına hiç bakılmaz.  "
     "Dt/dh = 400/8 = 50 ama Dp/dh = 240/8 = 30 olan bir tesiste halat "
     "bölümü de genel sonuç da UYGUN çıkıyordu.",
     "m.5.5.2.1 oranı 'kasnak, makara ve tamburlar' için ister — tahrik "
     "kasnağına özel değildir.  Saptırma kasnağı bulunan projelerde "
     "Dp / dh ≥ 40 da denetlenir;  kasnak yoksa ( Nps = Npr = 0 ) denetlenecek "
     "bir kasnak da yoktur.\n"
     "        Dp girdisi kasnakların ORTALAMA çapıdır, denetim de ortalamaya "
     "uygulanır:  çapları birbirinden farklı bir düzende en küçük kasnak "
     "ayrıca gözden geçirilmelidir.",
     ()),
    ("Karşı ağırlık rayında Fy'nin mukavemet momenti",
     "TS EN 81-50 Ek C.2.2.1",
     "Fy'den gelen gerilme için Wy'ye böler.",
     "Ek C.2.1.1 / C.2.2.1 açıkça şöyle yazar:\n"
     "            Fx → My = 3·Fx·l/16 → σy = My/Wy\n"
     "            Fy → Mx = 3·Fy·l/16 → σx = Mx/Wx\n"
     "        Yani y yönündeki kuvvet rayı X EKSENİ etrafında eğer ve Wx'e "
     "bölünür.  Excel'in kabin raylarında ve bütün sehim satırlarında doğrusu "
     "zaten yapılmıştır;  yalnız karşı ağırlık rayında Wy kalmış.",
     ("AU575", "Z588", "AF590")),
    ("Moment ve gerilmelerin eksen adları",
     "TS EN 81-50 Ek C.2.1.1",
     "Fx'ten gelen momente 'Mx', Fy'den gelene 'My' der ( doğru mukavemet "
     "momentine bölse de ).",
     "Standart bunun TERSİNİ yazar:  Fx → My, Fy → Mx.  Sayılar değişmez, "
     "ama paftayı Ek C ile karşılaştıran bir denetçi olmayan bir hata "
     "görüyordu — üstelik pafta kendi içinde de çelişiyordu:  sehim "
     "satırları ( δx ↔ Fx ↔ Iy ) standardın adlandırmasını kullanıyordu.",
     ()),
    ("Durum 2'de xQ",
     "TS EN 81-50 Ek C.2.1.1",
     "Sabit 0 yazar ( satır başlığı 'xQ = xc' dese de ).",
     "xQ = xc.  Durum 2'de yük yalnız y'de kaydırılır;  x'teki moment kolu "
     "kabin merkezidir.  Ek C'nin örneğinde kabin merkezi ray ekseniyle "
     "çakışık olduğu için ( xc = 0 ) iki okuma orada ayrışmaz.",
     ("AY335", "AU338", "Z369", "AJ371", "AE374", "Z384", "AH401",
      "L435", "AU438", "Z468", "AH470", "AH495")),
    ("ω burkulma katsayısı ray çeliğine bağlı",
     "TS EN 81-50 m.5.10.3",
     "Tek bir ω tablosu kullanır;  o tablo yalnız Rm = 370 eğrisidir "
     "( 231/231 değeri standardın 370 formülleriyle birebir çıkar ) ve "
     "ray çeliğinden bağımsız uygulanır.",
     "ω, λ ve Rm'in ikisine birden bağlıdır.  Standart Rm = 370 ve 520 için "
     "iki eğri verir, aradaki dayanımlar için doğrusal ara değer ister — "
     "standardın kendi notu, işlenmiş raylarda 440 yaygın olduğu için bunun "
     "'her zaman yapılması' gerektiğini söyler.  Excel'in yaklaşımı Rm = 440 "
     "ve 520'de ω'yı %23 ve %50 DÜŞÜK verir, yani burkulma gerilmesini "
     "olduğundan küçük gösterir — emniyetsiz taraf.\n"
     "        Ayrıca Excel'in tablosu 2 haneye yuvarlıdır;  motor standardın "
     "formülünü doğrudan kullanır.  Makine kaidesi ST 37 olduğu için orada "
     "( 11!AB39 · K73 ) yalnız bu yuvarlama farkı kalır — %0,2.",
     #  ω'ya bağlı olan her şey:  ω'nın kendisi, burkulma gerilmesi σk ve
     #  σk'yı içeren birleşik gerilmeler.
     ("AD354", "AL354", "AE365", "AE374", "AB39", "K73")),
    ("Acil frenlemede μ  —  halat hızı",
     "TS EN 81-50 m.5.11.2.3.2",
     "μ = 0,1 / ( 1 + v/10 ) bağıntısına KABİN hızını koyar "
     "( 'Veri Girişi'!C61 ).",
     "Bağıntıdaki v HALAT hızıdır:  v_halat = kabin hızı × askı oranı.  "
     "EN 81-50'nin çözümlü örneğinde 1 m/s kabin hızı ve 2:1 askı için "
     "μ = 0,083 çıkar — bu ancak v = 2 m/s ile mümkündür.  Kabin hızı "
     "kullanmak μ'yü, dolayısıyla e^(f·α) sınırını BÜYÜK gösterir:  "
     "tahrik yeteneğini olduğundan iyi çıkarır — emniyetsiz taraf.",
     ("AS190", "AL202", "AV211", "O257", "O271")),
    ("Flanş eğilmesinde ℓ",
     "TS EN 81-50 m.5.10.5",
     "Paydadaki ℓ yerine 1 yazar — ℓ harfi 1 rakamı okunmuş görünüyor.",
     "ℓ = paten balatasının uzunluğu ( girdi ).  Boş bırakılırsa ray "
     "tablosundaki balata yarı genişliğinden ( 2·b ) türetilir.",
     ("Z379", "Z384", "Z476", "Z481", "Z537", "Z595")),
    ("Motor veriminin makine tipine bağlanması",
     "MMO 208/7 - 2.4  ( ofis standardı )",
     "η'yı makine tipinden BAĞIMSIZ sabit 0,92 alır;  makine tipini "
     "( 'Veri Girişi'!B130, açılır listesi bile var ) hiçbir hesaba sokmaz "
     "ve palangalı sistemdeki verim düşüşünü uygulamaz.",
     "η makine tipine bağlıdır — ofisin KENDİ avan tablosu dişlisiz için "
     "0,85, dişli için 0,50 der;  palangalı sistemde ( i > 1 ) MMO/697 "
     "§2.4 gereği η − 0,10 uygulanır.  0,92 dişli makinede gerekli gücü "
     "YARIYA yakın gösteriyordu — emniyetsiz taraf.\n"
     "        Aynı asansör için avan paftası ile uygulama paftası farklı "
     "motor gücü veriyordu;  tablo artık iki projede TEK kaynaktan okunur "
     "( engine/ortak/ofis.py ).",
     #  Q25 kitapta "=AQ23" aynasıdır ve motorda karşılığı yoktur;  listeye
     #  alınırsa "hiçbir senaryoda ayrışmadı" der.  AQ23 zaten denetleniyor.
     ("AQ22", "AQ23", "X25")),
    ("Kabin alanı tablosu eksik",
     "TS EN 81-20 Çizelge 6  /  Çizelge 8",
     "Çizelge 6'nın 28 beyan yükünden 7'si tabloda ve açılır listede yoktu "
     "( 100 · 1050 · 1250 · 1350 · 1425 · 1500 · 2500 kg );  liste kapalı "
     "olduğu için o yüklerde HİÇ hesap yapılamıyordu.  Ayrıca 320 kg için "
     "0,97 m² yazar.",
     "Tablo Çizelge 6'ya tamamlandı;  asgari alanlar Çizelge 8'den, kişi "
     "sayısı m.5.4.2.3.1 a)'dan ( Q/75 ) türetildi.  1250 ve 1500 kg yaygın "
     "asansörlerdir.\n"
     "        320 kg Çizelge 6'da YOKTUR;  standardın kendi notu ara yükler "
     "için doğrusal ara değer ister ve 300/375 arası 0,953 m² verir.  0,97 "
     "EMNİYETSİZ taraftadır — o yük için standardın izin verdiğinden büyük "
     "kabine izin verir.\n"
     "        Teslim edilen kitabın açılır listesi de genişletilir ( 'Veri "
     "Girişi'!S sütunu ), yoksa kitap yeni yükleri reddederdi.",
     #  AC82:  azami kabin alanı.  320 kg'da kitap 0,97 der, standardın ara
     #  değeri 0,953'tür — yalnız bu yükte ayrışır.
     ("AC82",)),
    ("Sürtünme çarpanı f kanal şeklinden bağımsız",
     "TS EN 81-50 m.5.11.2.3.1.1  /  m.5.11.2.3.1.2",
     "Kanal şeklinden BAĞIMSIZ olarak hep V kanal bağıntısını kullanır;  "
     "yarım daire kanal seçilebildiği hâlde onun maddesi hiç uygulanmaz.  "
     "Alt kesilmesi olmayan kanallarda da β = 90° alır.",
     "Standart iki ayrı madde verir:\n"
     "            YARIM DAİRE  ( m.5.11.2.3.1.1 )\n"
     "                f = μ·4( cos(γ/2) − sin(β/2) ) / "
     "( π − β − γ − sin β + sin γ )\n"
     "            V KANAL  ( m.5.11.2.3.1.2 )\n"
     "                sertleştirilmemiş:  f = μ·4( 1 − sin(β/2) ) / "
     "( π − β − sin β )\n"
     "                sertleştirilmiş ve ağırlık bloke:  f = μ / sin(γ/2)\n"
     "        Alt kesilmesi olmayan kanalda β = 0'dır.  Kitabın yaklaşımı "
     "yarım daire kanalda f'yi %6 ( altı kesik ) ila %65 ( düz ) BÜYÜK "
     "gösteriyordu — tahrik yeteneğini olduğundan iyi çıkarır, emniyetsiz "
     "taraf.  V kanalda bir fark yoktur.",
     #  f ve ona bağlı e^(f·α) sınırları
     ("AU206", "AV211", "AE216", "O242", "O285")),
    ("Kuyu tabanı yükünde ray ağırlığı iki kez",
     "TS EN 81-20 m.5.2.1.8.4",
     "FKR = gn·Gr·LR + MY + Fk yazar.  Fk ( bölüm 7'nin Fv'si ) ZATEN Mg·gn "
     "içerir;  ray hattının ağırlığı aynı toplamda iki kez sayılır.",
     "Standart kalemleri tek tek sayar:  'the force due to the MASS OF THE "
     "GUIDE RAILS plus any load due to components fixed or linked to the "
     "guide(s) … plus the REACTION at the moment of operation of the safety "
     "gear'.  Ray kütlesi ayrı bir kalem, güvenlik tertibatı tepkisi ayrı bir "
     "kalemdir;  tepki k1·gn·(P+Q)/n'dir ve Mg·gn ona dahil değildir.\n"
     "        Örnek projede kitap 21.326 N der, doğrusu 18.096 N — ray başına "
     "3,23 kN ( %18 ) FAZLA.  Bu kalem fazla hesaplanıyor;  hatanın yönü "
     "emniyetli olsa da, listede bulunması gereken başka yüklerin ( ör. klips "
     "itme kuvveti Fp ) eksikliğini telafi etmez.",
     ("AX611",)),
    ("Acil frenleme yavaşlamasının alt sınırı",
     "TS EN 81-50 m.5.11.2.2.2",
     "Yalnız üst sınırı ( 1 gn ) denetler;  a = 0,05 m/s² gibi bir değer "
     "sorunsuz kabul edilirdi.",
     "Standart 'In no case shall the rate of retardation to consider be less "
     "than … 0,5 m/s²' der.  Küçük bir a atalet kuvvetini küçültür, T1/T2 "
     "oranını iyileştirir ve tahrik yeteneğini olduğundan İYİ gösterir — "
     "emniyetsiz taraf.  Alt sınır artık reddediliyor.",
     ()),
    ("Kabin önü girintisinin alana katkısı",
     "TS EN 81-20 m.5.4.2.1.3",
     "Kapı kasası dikmeleri arasındaki girintiye kapı genişliğinin YARISINI "
     "katar ( 11!X84 ) ve eşiği '≥ 100 mm' tutar.",
     "Standardın son fıkrası iki kural verir:  a) derinlik ≤ 100 mm ise alana "
     "HİÇ katılmaz;  b) > 100 mm ise 'the TOTAL available area shall be "
     "included in the floor area' — girintinin TAMAMI katılır.\n"
     "        900 mm kapı + 300 mm pervazda kitap 0,1350 m² ekler, tamı "
     "0,2700 m²'dir.  Kullanılabilir alanı küçük göstermek EMNİYETSİZ "
     "yöndür:  Çizelge 6'nın izin verdiğinden büyük bir kabine izin verilir. "
     "Eşik de düzeltildi — 100 mm'nin kendisi hariçtir.",
     ("X84",)),
    ("'Sf ≥ Smin' geçme ölçütü sayılıyor",
     "TS EN 81-20 m.5.5.2.2",
     "Sf'nin kendisini Smin ile karşılaştırıp UYGUN / UYGUN DEĞİL yazar "
     "( 11!AH125 ) ve bölüm sonucuna sokar.",
     "Standart tek bir şey ister:  'The safety factor … shall not be less "
     "than 12 ( iki halatta 16 ) … IN ADDITION the safety factor of "
     "suspension ropes shall not be less than that calculated according to "
     "EN 81-50:2014, 5.12.'  Yani GERÇEKLEŞEN S, ikisinin BÜYÜĞÜNDEN küçük "
     "olmayacak.  Sf < 12 bir uygunsuzluk değildir, yalnız 'asgariyi Smin "
     "belirliyor' demektir.\n"
     "        Kitabın koşulu standarda uyan tasarımları reddediyordu:  "
     "Sf = 7,89 · S = 32,54 olan bir askı 'UYGUN DEĞİLDİR' alıyordu.  "
     "Verilen öğüt de sonuca ulaşmıyordu — halat çapını artırmak Dt/dh'yi "
     "düşürür ve Sf'yi BÜYÜTÜR;  koşul hiçbir zaman sağlanamazdı.  Teslim "
     "edilen kitapta bu hücre artık hangi asgarinin belirleyici olduğunu "
     "yazar, karar vermez.",
     ()),
    ("Nequiv(t) kanalın adına bağlı",
     "TS EN 81-50 m.5.12.2.2  ( Çizelge 2 )",
     "Nequiv(t)'yi kanal şeklinin ADINDAN sabit bir tabloyla okur "
     "( TABLOLAR!D47:G52 ) ve 'açı' sütununda V kanalda γ'yı, altı kesik "
     "kanalda β'yı aynı yere yazar.  Ofis sabiti γ = 45° yapılsa bile tablo "
     "38 yazmayı, Nequiv(t) 12 kalmayı sürdürür.",
     "Çizelge 2 Nequiv(t)'yi doğrudan bu açıların fonksiyonu verir:\n"
     "            V kanal      γ  35 · 36 · 38 · 40 · 42 · 45 · 50°\n"
     "                  Nequiv(t) 18,5 · 16 · 12 · 10 · 8 · 6,5 · 5\n"
     "            Altı kesik   β  75 · 80 · 85 · 90 · 95 · 100 · 105°\n"
     "                  Nequiv(t)  2,5 · 3,0 · 3,8 · 5,0 · 6,7 · 10,0 · 15,2\n"
     "            Alt kesilmesiz yarım daire:  Nequiv(t) = 1\n"
     "        Çizelgede olmayan açılar için doğrusal ara değer alınır "
     "( çizelgenin kendi notu ).  Ofis açılarının varsayılanında "
     "( γ = 38° · β = 90° ) sayılar kitapla birebir aynıdır;  ayrışma ancak "
     "ofis sabiti değiştiğinde başlar — ve o zaman pafta hesabın gerçekten "
     "kullandığı sayıyı yazar.  Teslim edilen kitabın tablosu da projenin "
     "açılarıyla yeniden yazılır.",
     ()),
    ("Halat kütlesinin taraf dağılımı",
     "TS EN 81-50 m.5.11.2.2",
     "MSR = ( 0,5·H ± y )·ns·gh bağıntısının ± işaretini dört yük durumunun "
     "ÜÇÜNDE ters yazar:  kabin en alt duraktayken halat kütlesinin tamamını "
     "KARŞI AĞIRLIK tarafına koyar ( Askı Tipleri!M119/M120 · P119/P120 · "
     "Q119/Q120 ).",
     "İşaret kabinin kuyudaki KONUMUNDAN çıkar.  Üstte makineli bir tesiste "
     "kabin en alttayken kabin tarafındaki halat uzundur ( 0,5·H + y = H ), "
     "karşı ağırlık üsttedir ve o taraf kısadır.  Standart T1/T2'yi 'for the "
     "worst case depending on the position of the car in the well' "
     "değerlendirmeyi ister;  '%125 yüklü kabin en alt durakta' durumu zaten "
     "halat kütlesi kabin tarafında olduğu için en olumsuzdur.\n"
     "        Kitap kendi içinde de çelişiyordu:  bölüm 1'in açıklaması "
     "'kabin en altta iken halat ağırlığının TAMAMI kabin tarafındadır' der, "
     "bölüm 6 ise tersini yapardı.  Dört durumdan yalnız 'karşı ağırlığın "
     "asılı kalması' doğruydu.\n"
     "        Yön EMNİYETSİZDİ:  T1 küçük çıkıyor, tahrik yeteneği "
     "olduğundan iyi görünüyordu.  Kısa kuyularda fark ihmal edilebilir; "
     "20 duraklı bir tesiste yükleme oranı 1,23 yerine 1,79 çıkar ve "
     "e^(f·α) = 1,71 sınırını AŞAR.",
     ("AF235", "AJ240", "K242", "AF250", "AJ255", "K257",
      "AH264", "AF269", "K271")),
    ("Mil kuvveti ve moment askı oranından bağımsız",
     "MMO 208/7 - 2.4  ( ofis standardı )",
     "Pm = F1 − Ga ve M = Gmax × Dt/2 yazar;  askı oranı hiç girmez "
     "( 11!AQ7 · AQ21 ).",
     "2:1 palangalı bir sistemde tahrik kasnağının gördüğü kuvvet Gmax "
     "değil Gmax/i'dir — kasnak tarafındaki büyüklükler yarıya iner, halat "
     "hızı iki katına çıkar.  1275 kg · 2:1 · Dt = 240 mm örneğinde kitap "
     "85,74 kg·m yazar, doğrusu 42,87 kg·m'dir.\n"
     "        MOTOR GÜCÜNÜ ETKİLEMEZ:  N = Gmax·v/(η·102) askı oranından "
     "bağımsızdır ve kitapta doğru kurulmuştur.  Pm ile M hiçbir hesaba "
     "girmez, yalnız paftaya basılır — ama paftadan moment okuyup makine "
     "seçen bir okuyucuya iki katı bir sayı yazılıyordu.",
     ("AQ7", "AQ21")),
    ("Regülatör çekme kuvveti ve ikinci alt sınırı",
     "TS EN 81-20 m.5.6.2.2.1.1 d)  /  m.5.6.2.2.1.3 b)",
     "Sınırı  max( 300 N ; 2 × Freg )  alır ( 11!AA156 ) ve bu sınırı "
     "halattaki TOPLAM gerginlikle ( F'reg, 11!U156 = J156 ) karşılaştırır.  "
     "Freg halatın kendi statik gergisidir.",
     "Standardın İKİ AYRI maddesi iki AYRI kuvvetten söz eder:\n"
     "            m.5.6.2.2.1.1 d)  'the tensile force … produced BY THE "
     "GOVERNOR … at least the greater of twice that necessary to ENGAGE THE "
     "SAFETY GEAR, or 300 N'\n"
     "            m.5.6.2.2.1.3 b)  'the minimum breaking load … related by a "
     "safety factor of at least 8 to the tensile force produced IN THE ROPE'\n"
     "        Birincisi regülatörün ÜRETTİĞİ çekme kuvvetidir — kasnağın iki "
     "yanındaki gerginlik FARKI:  Fçekme = F'reg − Freg.  Güvenlik tertibatı "
     "mekanizmasını çeken odur;  halatın statik gergisi Freg zaten oradadır ve "
     "hiçbir şeyi çekmez.  İkincisi halattaki EN BÜYÜK gerginliktir ( F'reg ) "
     "ve emniyet katsayısı ona karşı hesaplanır.\n"
     "        Kitap ikisini de F'reg ile yapıyor, üstelik sınıra 2·Freg "
     "koyuyordu — yani ölçüt e^(f·α') ≥ 2 demeye geliyor ve standardın "
     "istemediği bir koşulla tasarımları reddedebiliyordu.\n"
     "        Devreye sokma kuvveti İMALATÇI VERİSİDİR ( tip inceleme "
     "belgesi ).  Girilmezse bu madde DENETLENEMEZ:  bölüm 'HESAP EKSİK' der "
     "ve proje 'uygundur' çıkmaz — teslim edilen kitap da aynısını yazar.",
     ("AA156", "U156")),
    ("Ray gerilmesi ve sehimi işaretli karşılaştırılıyor",
     "TS EN 81-50 Ek C.2.1  /  m.5.10.6",
     "σ ve δ'yı İŞARETLİ karşılaştırır:  'δ ≤ δperm' ve 'σ ≤ σperm'.  "
     "Ayrıca σm = σx + σy'yi işaretli toplar.",
     "Fx / Fy işaretlidir ve işaret YÖNÜ gösterir — kabin merkezi ray "
     "ekseninin öbür yanındaysa ( xc < 0 ) kuvvet de moment de negatife "
     "düşer.  Rayın gördüğü gerilme ile yaptığı sehim ise yönden bağımsız "
     "BÜYÜKLÜKLERDİR.\n"
     "        İşaretli karşılaştırma iki ayrı yerde emniyetsizdi:\n"
     "            · δ = −5,59 mm, sınır 5 mm iken SESSİZCE geçiyordu "
     "( −5,59 ≤ 5 doğrudur );\n"
     "            · σm = σx + σy toplamında ters işaretli iki eğilme "
     "birbirini GÖTÜRÜYOR, σm olduğundan küçük çıkıyor ve σc = σv + σm "
     "ile birleşik gerilme de küçülüyordu.\n"
     "        Kuvvet ve moment satırları işaretini korur;  σ ve δ büyüklük "
     "olarak yazılır ve karşılaştırılır.  En olumsuz lif iki eğilmeyi de "
     "toplayarak görür.",
     ()),
    ("Karşı ağırlık güvenlik tertibatının taban tepkisi",
     "TS EN 81-20 m.5.2.1.8.4",
     "Karşı ağırlıkta güvenlik tertibatı diye bir girdisi yoktur;  kuyu "
     "tabanına bildirilen FAR yalnız ray kütlesi ile yardımcı donanımı "
     "sayar ( 11!AN616 ).",
     "Standart kalemleri tek tek sayar ve 'the REACTION at the moment of "
     "operation of the safety gear' ayrı bir kalemdir — kabin rayında "
     "sayılıyor, karşı ağırlıkta sayılmıyordu.  Tertibat 'Kaymalı' "
     "seçilse bile FAR değişmiyordu.\n"
     "        Örnek projede eksik tepki  k1·gn·Mcwt/n = 2 × 9,81 × 1.100 / 2 "
     "= 10.791 N/ray;  taban 1.015,50 yerine 11.806,50 N/ray görmeliydi.  "
     "Kuyu tabanı yükü İNŞAAT PROJESİNE bildirilen sayıdır ve OLDUĞUNDAN "
     "DÜŞÜK bildiriliyordu.  Ray kütlesinin payı burada da bir kez sayılır "
     "( Fk − Mg·gn ).",
     ()),
    ("Karşı ağırlık denge oranı q",
     "MMO 208/7 - 2.4  ( ofis standardı )",
     "C80 formülü  'kabin ağırlığı + beyan yükü / 2'  diye ÇİVİLİDİR;  "
     "ofis q'yu değiştirse bile 0,50 kalır.",
     "Ofisin denge oranı q bir sabittir ve bölüm 1 Ga'yı  P + q·Q  ile "
     "kurar.  Karşı ağırlık kütlesi ise C80'den geliyordu:  q = 0,60'ta "
     "AYNI PROJEDE İKİ FARKLI karşı ağırlık oluşuyordu — motor ve ağırlık "
     "tamponu 1.180 kg, tahrik ve ağırlık rayı 1.100 kg.  Aynı fiziksel "
     "parçanın kütlesi her hesapta aynı olmalıdır.\n"
     "        Kütle artık tek yerden türer ( mukavemet_girdi.tamamla ) ve "
     "bölüm 1 de onu okur;  teslim edilen kitabın C80 formülü de projenin "
     "q'suyla yazılır.",
     ()),
    ("Sığınma açıklıklarının iki alt sınırı",
     "TS EN 81-20 m.5.2.5.7.3  /  m.5.2.5.8.2 a) 2)",
     "Kabin üstü serbest yüksekliğini 1200 mm, ray dibi açıklığını 150 mm "
     "ister.  Standartta bu iki sayı yoktur;  150 mm, m.5.2.5.8.2 a) 1)'deki "
     "YATAY 0,15 m'nin düşey sınır sanılmasından gelmiş görünüyor.",
     "Kabin üstü:  m.5.2.5.7.3 ayakta durulabilen alanın üzerindeki serbest "
     "yüksekliği seçilen sığınma hacminin yüksekliğine bağlar — çömelmiş "
     "duruşta ( Çizelge 3 ) 1,00 m.  Ray dibi:  m.5.2.5.8.2 a) 2) ve Şekil 7, "
     "raya yatay XH ≤ 0,15 m uzaklıktaki karkas / paten / güvenlik tertibatı "
     "için 0,10 m verir.\n"
     "        Excel'in iki sayısı da standarttan KATI taraftadır;  yani "
     "emniyetsiz bir tasarımı geçirmez, ama standarda uygun bir projeyi "
     "haksız yere reddeder ( kuyu boyunu gereksiz büyütür ).\n"
     "        Ayrıca karşılaştırma '>' idi;  standart 'en az' dediği için "
     "sınıra eşit ölçü de uygundur — '≥' yapıldı.",
     ()),
    ("Dengesiz yük Gmax halatın TAMAMINI sayıyordu",
     "MMO 208/7 - 2.4  ( fiziksel dengesizlik )",
     "Gmax = F1 + Gs − Ga yazar, yani ( 1−q )·Q + Gh.  Buradaki Gh kabin "
     "tarafındaki TOPLAM halat kütlesidir ( kuyu boyu + 5 m pay ) ve "
     "dengesizlik DEĞİLDİR:  kabin en alttayken karşı ağırlık tarafında da "
     "halat vardır.  Denge zinciri ve gezici kablo hiç girmez.",
     "Motoru zorlayan, iki taraf arasındaki FARKTIR:\n"
     "        Gmax = ( Q + P − Ga ) + Gs + i·H·gh·ns·( 1 − λ ) + 0,5·H·mt\n"
     "        MSR = i·H·gh·ns  —  seyahat mesafesi üzerinden;  askı oranı "
     "çarpandır çünkü 2:1'de kabin 1 m indiğinde kabin tarafındaki halat "
     "2 m uzar.  λ denge zincirinin karşıladığı oran, MTrav gezici kablonun "
     "yarısıdır.\n"
     "        Kuyu boyu yerine seyahat mesafesi kullanmak kısa kuyuda gücü "
     "küçültür;  denge zinciri olmayan UZUN kuyuda ise eski hesap — hafif "
     "tablo halatıyla birleşince — gücü OLDUĞUNDAN KÜÇÜK gösteriyordu.  "
     "Zincirli tesiste eski hesap motoru iki katına kadar büyütüyordu "
     "( 120 m seyirde 20,7 kW yerine 39,3 kW ).\n"
     "        Gh ve F1 DEĞİŞMEDİ:  onlar kabin tarafındaki gerçek yüktür ve "
     "kaide, halat güvenlik katsayısı, tahrik ve Tst onlara dayanır.",
     ("AQ9",)),
)

#  Testlerin okuduğu düz küme
FARKLI_HUCRELER = tuple(sorted({h for *_x, hucreler in EXCEL_FARKLARI
                                for h in hucreler}))


# =====================================================================
#  SABİTLER
# =====================================================================
#  Bu değerler Excel'de doğrudan hücreye yazılıdır ( girdi değildir ).
#  Kaynakları yanlarında; değiştirmek gerekirse tek yer burasıdır.
SABIT = {
    "gn":              9.81,      # yerçekimi ivmesi              [m/s²]
    "motor_sabiti":    102,       # kW ↔ kg·m/s dönüşümü                 (11!AQ23)
    "hp_carpani":      1.34,      # kW → HP                              (11!X25)
    "Dt_dh_asgari":    40,        # tahrik kasnağı / halat oranı   EN 81-20 m.5.5.2.1
    "Dreg_dreg_asgari": 30,       # regülatör kasnağı / halat oranı      (11!N142)
    "reg_kat_asgari":  8,         # regülatör halatı emniyet katsayısı   (11!K161)
    "reg_kuvvet_asgari": 300,     # F'reg alt sınırı              [N]    (11!AA156)
    #  TS EN 81-20 m.5.6.2.2.1.1 a) — devreye girme hızı penceresi
    "reg_hiz_alt_carpan": 1.15,   # "at least 115 % of the rated speed"
    "reg_hiz_ust_ani":    0.80,   # ani frenlemeli ( makaralı hariç )
    "reg_hiz_ust_makara": 1.00,   # ani frenlemeli makaralı
    "reg_hiz_ust_kaymali": 1.50,  # kaymalı, v ≤ 1,0 m/s
    #  m.5.6.2.1.2.1 b) — ani frenlemeli kabin tertibatı üst hız sınırı
    "ani_tertibat_azami_v": 0.63,
    #  m.5.6.2.1.2.3 — karşı ağırlık tertibatı bu hızın üstünde KAYMALI olmalı
    "agirlik_kaymali_esigi": 1.0,
    "reg_sarilma_aci": 180,       # α'  regülatör kasnağı sarılma [°]    (11!AI133)
    "Nps":             1,         # tek yönde bükülmeli kasnak sayısı    (11!AH105)
    "Npr":             0,         # ters yönde bükülmeli kasnak sayısı   (11!AH106)
    "mu_yukleme":      0.1,       # μ  yükleme                           (11!V188)
    "mu_bloke":        0.2,       # μ  kabin bloke                       (11!V192)
    "kanal_acisi":     38,        # γ  sertleştirilmiş kanal      [°]    (11!AH102)
    "alt_kesilme":     90,        # β  alt kesilme açısı          [°]    (11!AH103)
    "E":               206010,    # elastisite modülü           [N/mm²]  (11!AH302)
    #  TS EN 81-20 Çizelge 14.  k2 ÇİZELGEDE YAZILIDIR ( Running = 1,2 );
    #  k3 için çizelge sayı vermez — "imalatçı tarafından, gerçek tesise göre
    #  belirlenir" — o yüzden k3 OFİS SABİTİDİR ( sabitler.k3_yardimci ).
    #  Kitap ikisini tek bir 1,2 ile karıştırıyordu.
    "k2":              1.2,       # normal kullanma darbe katsayısı  ( Çiz.14 )
    "MY_kabin":        150,       # kabin rayına bağlı donanım    [N]    (11!AH292)
    "MY_agirlik":      50,        # ağırlık rayına bağlı donanım  [N]    (11!AH555)
    "dperm_kabin":     5,         # kabin rayı azami sehim        [mm]   (11!AH306)
    "dperm_agirlik":   10,        # ağırlık rayı azami sehim      [mm]   (11!AL600)
    "sehim_katsayi":   0.7,       # sehim formülü katsayısı              (11!R393)
    "sehim_bolen":     48,        # 48·E·I                               (11!U394)
    "moment_pay":      3,         # M = 3·F·l/16                         (11!M324)
    "moment_bolen":    16,
    "birlesik_katsayi": 0.9,      # σk + 0,9·σm                          (11!X365)
    "kabin_merkez_payi": 130,     # xc = ( derinlik/2 + 130 ) − RK  [mm] (11!AH293)
    "Dx_bolen":        8,         # Dx = derinlik / 8                    (11!S310)
    "Dy_bolen":        8,         # Dy = genişlik  / 8                   (11!S313)
    "Dxa_katsayi":     0.1,       # Dxa = 0,1 × ağırlık derinliği        (11!N562)
    "Dya_katsayi":     0.05,      # Dya = 0,05 × ağırlık genişliği       (11!AL562)
    "Fs_alt":          0.4,       # eşik kuvveti  Q < 2500 kg            (11!AH303)
    "Fs_ust":          0.6,       # eşik kuvveti  Q ≥ 2500 kg
    "Fs_sinir":        2500,      # [kg]
    "tampon_katsayi":  4,         # F = 4·gn·(P+Q)                       (11!R621)
    "FRcar_katsayi":   0.02,      # kabin sürtünme direnci        (Askı Tipleri!P128)
    "FRcwt_katsayi":   0.015,     # ağırlık sürtünme direnci      (Askı Tipleri!P129)
    "ray_kaide_payi":  200,       # ray boyu:  kaide yüksekliği − 200 mm (11!AH291)
    "ray_kuyu_payi":   300,       # ray boyu:  kuyu dibi − 300 mm
}

#  Sığınma alanı hesaplarındaki kabin/kuyu geometrisi payları.  Excel'de
#  doğrudan formüle gömülüdür ( 11!AI635…AI648 ); ofis kabulüdür, MMO ya da
#  EN 81-20 sayısı DEĞİLDİR.
#  Kabin / kuyu geometrisi payları OFİS STANDARDINDADIR ( ekrandan
#  değiştirilir );  aşağıdaki değerler yalnız motor tek başına çağrıldığında
#  geçerli olan fabrika ayarıdır.
SIGINMA_PAYLARI = ("kabin_yuksekligi", "kabin_ust_donanim", "paten_payi",
                   "tavan_payi", "revizyon_payi", "etek_payi", "etek_kotu",
                   "ray_alt_payi", "regulator_payi")
SIGINMA = {
    "kabin_yuksekligi":     2400,   # üst paten - ray üst ucu payı      [mm]
    "kabin_ust_donanim":    2100,   # kabin üstü kotu                   [mm]
    "paten_payi":            300,
    "tavan_payi":            150,
    "revizyon_payi":         500,
    "etek_payi":             400,
    "etek_kotu":             950,
    "ray_alt_payi":          270,
    "regulator_payi":        300,
    #  SIĞINMA HACİMLERİ ARTIK BURADA DEĞİL.  Duruş tipi ( dik / çömelme /
    #  yatarak ) tesise özel bir BEYANDIR, ofis sabiti değil:  girdiden gelir
    #  ve ölçüler mukavemet_tablolari.SIGINMA_HACMI tablosundan okunur.
    #  Eskiden çömelme tipi buraya çivilenmişti ve yatarak tipiyle uygun olan
    #  kuyu diplerine "UYGUN DEĞİL" deniyordu ( bkz. MT.SIGINMA_HACMI notu ).
    #  ---------------------------------------------------------------
    #  TS EN 81-20 asgari açıklıklar  [mm].  Her satırın karşısındaki
    #  madde numarası standardın kendi metnindendir.
    #  ---------------------------------------------------------------
    "min_ust_paten":         100,   # m.5.2.5.6.2  ilave kılavuzlu yol   0,10 m
    #  m.5.2.5.7.3:  kabin üstünde ayakta durulabilen her alanın üzerindeki
    #  serbest yükseklik, seçilen sığınma hacminin yüksekliği kadardır —
    #  çömelmiş duruşta ( Çizelge 3, tip 2 ) 1,00 m.  Ayrı bir sabit
    #  tutulmaz;  doğrudan  ust_hacim[2]  okunur.
    "min_revizyon":          500,   # m.5.2.5.7.2 a) kabin üstü donanım  0,50 m
    "min_kuyu_tabani":       500,   # m.5.2.5.8.2 a) kuyu dibi - kabin   0,50 m
    "min_etek":              100,   # m.5.2.5.8.2 a) 1) etek            0,10 m
    #  m.5.2.5.8.2 a) 2) + Şekil 7:  raya yatay XH ≤ 0,15 m uzaklıktaki
    #  karkas parçaları, paten ve güvenlik tertibatı için asgari düşey
    #  açıklık 0,10 m'dir.  ( Şekil 7 eğrisi:  0,15 m → 0,10 m ·
    #  0,30 m → 0,30 m ·  0,50 m ve ötesi → 0,50 m. )
    "min_ray_alt":           100,
    "min_regulator":         300,   # m.5.2.5.8.2 b) kuyuya sabit parça  0,30 m
}


def _pozitif(x):
    """Pozitif bir sayı mı  ( bool tuzağı dâhil )."""
    return isinstance(x, (int, float)) and not isinstance(x, bool) and x > 0


def _halat_verisi(g):
    """Askı halatı birim kütlesi ve kopma yükü  —  KATALOG GİRDİSİ TABLOYU EZER.

    Döner:  ( gh kg/m , Tmin N , gh_kaynak , Tmin_kaynak )

    TS 12385-5 tablosu yalnız 6x19 / 8x19 LİF ÖZLÜ halatları kapsar;  küçük
    kasnaklı dişlisiz makinelerin çelik özlü / özel halatları orada yoktur.
    Elle girilen değer tabloyu ezer ve paftaya kaynağı 'imalatçı kataloğu'
    olarak yazılır — hangi verinin kullanıldığı GÖRÜNÜR olmalıdır.
    """
    dh = g.get("halat_capi")
    gh_t, Tmin_t = MT.halat_agirlik(dh), MT.halat_kopma(dh)
    gh_e, Tmin_e = g.get("halat_birim_kutle"), g.get("halat_kopma_kN")
    tablo = f"TS 12385-5  ·  {MT.halat_tipi(dh)}"
    if _pozitif(gh_e):
        gh, gh_k = float(gh_e), "GİRİŞ — imalatçı kataloğu"
    else:
        gh, gh_k = gh_t, tablo
    if _pozitif(Tmin_e):
        Tmin, Tmin_k = float(Tmin_e) * 1000.0, "GİRİŞ — imalatçı kataloğu"
    else:
        Tmin, Tmin_k = Tmin_t, tablo
    return gh, Tmin, gh_k, Tmin_k


def _bosluk(v):
    """0,10 m ilave kılavuzlu yol + 0,035·v² sıçrama payı  →  mm.

    TS EN 81-20'de 0,035·v² açıklığın değil, kabinin en üst konumunun
    tanımındadır ( Çizelge 2 );  0,10 m ise m.5.2.5.6.2'nin ilave kılavuzlu
    yoludur.  Kuyu ölçüleri anma konumundan alındığı için ikisi burada
    tek sınırda toplanır — eşitsizlik cebirsel olarak aynıdır.
    """
    return (0.1 + 0.035 * v * v) * 1000


def _oran(a, b):
    return max(a / b, b / a) if (a and b) else None


def _kay(o, **hucreler):
    """Hesaplanan değeri kaynak Excel'deki hücre adresine bağlar.

    Motoru Excel'e karşı hücre hücre doğrulayabilmek için tek yol budur;
    doğrulama testi bu haritayı okur, hesabı tekrar etmez.
    Anahtarlar "11-Muk. Hesapları" sayfasının adresleridir.
    """
    o.setdefault("_h", {}).update(hucreler)


# =====================================================================
#  1 -  ASANSÖR MOTOR GÜCÜ                        ( MMO 208/7 - 2.4 )
# =====================================================================
def _motor(g, o):
    S, O = SABIT, o["ofis"]
    Q, P, v = g["beyan_yuku"], g["kabin_agirligi"], g["beyan_hizi"]
    Dt, dh, nh, r = (g["tahrik_kasnak_capi"], g["halat_capi"],
                     g["halat_adedi"], g["aski_orani"])
    gh, _Tmin_h, gh_kaynak, _Tmin_kaynak = _halat_verisi(g)

    #  Halat boyu:  kuyu boyundan tampon/paten yığını düşülür, 5 m pay eklenir;
    #  2:1 askıda halat iki kat gider.
    yigin = (g["agirlik_tampon_baba"] + g["agirlik_carpma_arasi"]
             - g["agirlik_tampon_ezilme"] + g["agirlik_paten_arasi"]
             + g["kabin_paten_arasi"])
    lh = (g["kuyu_boyu"] - yigin) / 1000.0 + O["halat_pay_m"]
    if r != 1:
        lh *= 2
    Gh = gh * lh * nh
    F1 = Q + P + Gh                       # kabin ve aksesuarlarının yükü
    #  KARŞI AĞIRLIK TEK YERDEN GELİR  ( MG.tamamla → 'karsi_agirlik' ).
    #  Burada ikinci kez  P + q·Q  hesaplansaydı, q değiştiğinde bu bölüm ile
    #  tahrik / ray / tampon bölümleri ayrışırdı — nitekim ayrışıyordu.
    Ga = g["karsi_agirlik"]               # karşı ağırlık yükü

    #  ------------------------------------------------------------------
    #  DENGESİZ ( ARTAN ) YÜK  Gmax  —  motor gücünü belirleyen büyüklük
    #  ------------------------------------------------------------------
    #  ESKİDEN:  Gmax = F1 + Gs − Ga,  yani ( 1−q )·Q + Gh.  Buradaki Gh
    #  KABİN TARAFINDAKİ TOPLAM halat kütlesidir ve dengesizlik DEĞİLDİR:
    #  kabin en alttayken karşı ağırlık tarafında da halat vardır, motoru
    #  zorlayan iki tarafın FARKIDIR.  Üç eksik vardı:
    #
    #    1) Halat dengesizliği kuyu boyu + 5 m payla hesaplanıyordu;  doğrusu
    #       SEYAHAT MESAFESİDİR ( MSR = i·H·gh·ns ).  Kısa kuyuda fazla, uzun
    #       kuyuda — hafif tablo halatıyla birleşince — EKSİK çıkıyordu.
    #    2) DENGE ZİNCİRİ hiç yoktu.  Zincir halat dengesizliğini karşılar;
    #       zincirli bir tesiste program motoru gereğinden büyük seçiyordu.
    #    3) GEZİCİ KABLO ( flexbil ) hiç girmiyordu.  Küçük ama her zaman
    #       eksi yönde:  kablo kuyu ortasından asılıdır, kabin en alttayken
    #       yarısı kabin tarafındadır.
    #
    #  Gh ve F1 OLDUĞU GİBİ KALIR:  onlar kabin tarafındaki GERÇEK yüktür ve
    #  kaide ( bölüm 2 ), halat güvenlik katsayısı ( bölüm 4 ), tahrik
    #  ( bölüm 6 ) ve Tst bunlara dayanır — dengesizlikle karıştırılmamalıdır.
    H = g["seyir_mesafesi"]                          # seyahat mesafesi, m
    MSR = r * H * gh * nh                            # dengesiz halat kütlesi
    #  DENGE ZİNCİRİ VAR / YOK.  Zincir halatı dengelemek için takılır ve
    #  halat ağırlığına göre seçilir;  bu yüzden "var" TAM DENGELEME kabulüdür
    #  ( λ = 1 ).  Zincirin metre ağırlığı sahada ölçülemediği için ofis
    #  kabulü olarak alınır — bilerek hafif seçilmiş bir zincir gerçek güç
    #  ihtiyacını bu hesabın üstüne çıkarır.  Kabul, paftada λ satırında
    #  görünür.
    lam = ((O["denge_zinciri_orani"] or 0) / 100.0
           if str(g.get("denge_zinciri") or "").strip() == "Var" else 0.0)
    MCR = lam * MSR                                  # zincirin dengelediği
    mt = sum(MT.kablo_agirligi(g.get(k)) or 0.0
             for k in ("kablo_tipi_1", "kablo_tipi_2"))
    MTrav = 0.5 * H * mt                             # gezici kablo dengesizliği
    Gden = (Q + P) - Ga                              # dengelenmeyen beyan yükü
    Gmax = Gden + O["Gs"] + MSR - MCR + MTrav
    #  MİL KUVVETİ VE MOMENT ASKI ORANINA GÖRE İNDİRGENİR.
    #  Kitap bu iki satırı kabin tarafındaki yükle yazıyordu.  2:1 palangalı
    #  bir sistemde tahrik kasnağının gördüğü kuvvet Gmax değil Gmax/i'dir —
    #  kasnak tarafındaki büyüklükler yarıya iner, halat hızı iki katına
    #  çıkar.  ( Gücü etkilemez:  N = Gmax·v / (η·102) askı oranından
    #  bağımsızdır ve doğrudur.  Ama paftadan MOMENT okuyup makine seçen bir
    #  okuyucuya iki katı bir sayı yazılıyordu. )
    Pm = (F1 - Ga) / r                    # tahrik kasnağına gelen döndürme kuvveti
    M = (Gmax / r) * (Dt / 2000.0)        # tahrik kasnağı momenti
    #  TAHRİK KASNAĞINA GELEN STATİK YÜK.  Kasnak iki halat kolunu birden
    #  taşır;  Pm bunların FARKI ( döndüren kuvvet ), Tst ise TOPLAMIDIR.
    #  Palangalı sistemde her kol yükün yarısını çeker, bu yüzden askı
    #  oranına bölünür:  1:1'de F1 + Ga,  2:1'de ( F1 + Ga ) / 2.
    #  İmalatçının kasnak için verdiği azami statik yük aşılmamalıdır;
    #  program bunu HİÇ denetlemiyordu — motor gücü "UYGUN" çıkan bir seçim
    #  kasnak yükünü aşmış olabilirdi.
    #
    #  DENGE ZİNCİRİ DE KASNAĞA BİNER.  Zincir kabin ile karşı ağırlık
    #  arasında asılıdır;  ağırlığı ikisine paylaşılır ve halatlar üzerinden
    #  kasnağa ulaşır.  Gmax'ta zincir dengesizliği AZALTIR ( eksi işaretli ),
    #  statik yükte ise ARTIRIR — ikisi ayrı büyüklüktür.  Zincir hesaba
    #  girmezse Tst olduğundan küçük çıkar ve kasnak yükü aşılmış bir makine
    #  "UYGUN" görünebilir;  bu EMNİYETSİZ taraftır.  Karşı ağırlık koluna
    #  eklenir ( EN 81-20/50 şablonlarının T2 = gn·( Mcwt + MCR )/r bağıntısı
    #  ile aynı kabul ).
    Tst_h = (F1 + Ga + MCR) / r
    Tst = g.get("makine_tst")
    Tst_verildi = isinstance(Tst, (int, float)) and not isinstance(Tst, bool) and Tst > 0
    tst_uygun = (Tst >= Tst_h) if Tst_verildi else None
    #  VERİM — makine tipine bağlı TOPLAM SİSTEM VERİMİ  ( ofis standardı ).
    #  Kaynak kitap burada makine tipinden bağımsız sabit 0,92 kullanıyordu;
    #  ofisin kendi avan tablosu ise dişli makinede 0,50 der.  Dişli makinede
    #  0,92 gerekli gücü YARIYA yakın gösteriyordu — emniyetsiz taraf.
    #  ASKI ORANINA BAĞLI Δη = 0,10 DÜŞÜŞÜ KALDIRILDI ( bkz. ortak/ofis.py ):
    #  askı ( palanga ) kaybı artık η'nın İÇİNDEDİR, ikinci kez inmez.  Bu
    #  yüzden "Ofis verimi η toplam sistem verimidir" anahtarı da kalktı —
    #  η her zaman toplam sistem verimidir.
    eta = US.verim(O, g.get("makine_tipi"))
    #  İKİNCİ KALKAN.  Girdi doğrulaması η ≤ 0'ı ve negatif halat boyunu
    #  zaten reddediyor;  motor doğrudan çağrılırsa ( testler ) sıfıra
    #  bölünmesin ve fiziksel olmayan bir güç "uygun" sayılmasın.
    hesaplanabilir = eta > 0 and lh > 0
    N = (Gmax * v / (eta * S["motor_sabiti"])) if hesaplanabilir else None
    HP = N * S["hp_carpani"] if N is not None else None
    uygun = bool(N is not None and N > 0 and g["motor_gucu"] >= N
                 and tst_uygun is not False)

    #  λ ve zincir kütlesi TEK YERDE hesaplanır ( burada ) ve tahrik bölümü
    #  buradan okur — iki yerde ayrı türetilirse ayrışırlar.
    o.update(lam=lam, MCR=MCR, MSR_dengesiz=MSR)
    o.update(Q=Q, P=P, v=v, gh=gh, lh=lh, Gh=Gh, F1=F1, Ga=Ga, Gmax=Gmax,
             N_hesap=N, motor_uygun=uygun, r=r, nh=nh, dh=dh, Dt=Dt,
             Tst_hesap=Tst_h, Tst=Tst if Tst_verildi else None,
             tst_uygun=tst_uygun)
    o.update(eta=eta)
    _kay(o, AQ18=gh, AQ19=lh, AQ16=Gh, AQ11=F1, AQ13=Ga, AQ9=Gmax, AQ7=Pm,
         AQ21=M, AQ22=eta, AQ23=N, X25=HP)

    b = Bolum("ASANSÖR MOTOR GÜCÜNÜN HESAPLANMASI", kimlik="motor_gucu", kaynak="MMO 208/7 - 2.4")
    b["adimlar"] = [
        veri("v", "Kabin hızı", v, "m/s", "GİRİŞ"),
        veri("Q", "Beyan yükü", Q, "kg", "GİRİŞ"),
        veri("P", "Boş kabin ağırlığı", P, "kg",
             g.get("kabin_agirligi_kaynak") or "GİRİŞ"),
        veri("dh", "Halat çapı", dh, "mm", "GİRİŞ"),
        veri("nh", "Halat sayısı", nh, "adet", "GİRİŞ"),
        veri("gh", "Halatın 1 m'deki ağırlığı", gh, "kg/m", gh_kaynak, 4),
        hesap("lh = ( Kuyu boyu − tampon/paten yığını ) / 1000 + 5"
              + ("  ( × 2 :  2:1 askı )" if r != 1 else ""),
              f"( {trn(g['kuyu_boyu'], 0)} − {trn(yigin, 0)} ) / 1000 + "
              f"{O['halat_pay_m']}" + ("  × 2" if r != 1 else ""),
              lh, "m", "11!AQ19"),
        hesap("Gh = gh × lh × nh", f"{tr(gh)} × {tr(lh)} × {trn(nh, 0)}",
              Gh, "kg"),
        hesap("F1 = P + Q + Gh", f"{trn(P, 0)} + {trn(Q, 0)} + {tr(Gh)}", F1, "kg"),
        hesap(f"Ga = P + {tr(O['q_denge'])} × Q",
              f"{trn(P, 0)} + {tr(O['q_denge'])} × {trn(Q, 0)}", Ga, "kg"),
        veri("Gs", "Sürtünme yükü", O["Gs"], "kg", "OFİS STANDARDI"),
        metin("Dengesiz  ( artan )  yükün bileşenleri :"),
        hesap("Gden = ( Q + P ) − Ga        ( dengelenmeyen beyan yükü )",
              f"( {trn(Q, 0)} + {trn(P, 0)} ) − {tr(Ga)}", Gden, "kg"),
        veri("H", "Seyir mesafesi", H, "m", "GİRİŞ"),
        hesap("MSR = i × H × gh × ns" if r != 1 else "MSR = H × gh × ns",
              (f"{trn(r, 0)} × {tr(H)} × {tr(gh)} × {trn(nh, 0)}" if r != 1
               else f"{tr(H)} × {tr(gh)} × {trn(nh, 0)}"), MSR, "kg",
              "dengesiz halat kütlesi  ( kabin en altta )"),
        veri("", "Denge ( kompanzasyon ) zinciri",
             "Var" if lam else "Yok", "", "GİRİŞ"),
        veri("λ", "Dengeleme oranı", lam, "—",
             f"OFİS STANDARDI  ·  %{trn(O['denge_zinciri_orani'], 0)}"
             if lam else "zincir yok", 2),
        hesap("MCR = λ × MSR", f"{tr(lam)} × {tr(MSR)}", MCR, "kg",
              "zincirin dengelediği kütle"),
        hesap("MTrav = 0,5 × H × mt",
              f"0,5 × {tr(H)} × {tr(mt)}", MTrav, "kg",
              "gezici kablo dengesizliği"),
        hesap("Gmax = Gden + Gs + MSR − MCR + MTrav",
              f"{tr(Gden)} + {tr(O['Gs'])} + {tr(MSR)} − {tr(MCR)} + {tr(MTrav)}",
              Gmax, "kg"),
        hesap("Pm = ( F1 − Ga ) / i" if r != 1 else "Pm = F1 − Ga",
              (f"( {tr(F1)} − {tr(Ga)} ) / {trn(r, 0)}" if r != 1
               else f"{tr(F1)} − {tr(Ga)}"), Pm, "kg",
              "tahrik kasnağına gelen döndürme kuvveti"),
        veri("Dt", "Tahrik kasnağı çapı", Dt, "mm", "GİRİŞ"),
        hesap("M = ( Gmax / i ) × ( Dt / 2 )" if r != 1 else "M = Gmax × ( Dt / 2 )",
              (f"( {tr(Gmax)} / {trn(r, 0)} ) × {tr(Dt / 2000.0)}" if r != 1
               else f"{tr(Gmax)} × {tr(Dt / 2000.0)}"), M, "kg·m",
              "tahrik kasnağı momenti"),
        veri("", "Makine tipi", g.get("makine_tipi") or "—", "", "GİRİŞ"),
        veri("η", "Toplam sistem verimi  ( askı / palanga kaybı DÂHİL )", eta, "",
             f"OFİS STANDARDI  ·  {g.get('makine_tipi') or 'tanınmayan tip'}"),
        hesap("N = Gmax × v / ( η × 102 )",
              f"{tr(Gmax)} × {tr(v)} / ( {tr(eta)} × 102 )",
              N, "kW", "MMO 208/7 - 2.4"),
        hesap("HP = N × 1,34", f"{tr(N)} × 1,34", HP, "HP"),
        veri("Nsç", "Kullanılan motor gücü", g["motor_gucu"], "kW", "GİRİŞ"),
        metin("Tahrik kasnağına gelen statik yük :"),
        hesap("Tst-h = ( F1 + Ga + MCR ) / i" if r != 1
              else "Tst-h = F1 + Ga + MCR",
              (f"( {tr(F1)} + {tr(Ga)} + {tr(MCR)} ) / {trn(r, 0)}" if r != 1
               else f"{tr(F1)} + {tr(Ga)} + {tr(MCR)}"), Tst_h, "kg",
              "kasnağın taşıdığı toplam yük  ( halatlar + denge zinciri )"),
    ] + ([
        veri("Tst", "Makinenin azami kasnak statik yükü", Tst, "kg",
             "GİRİŞ — imalatçı kataloğu", 0),
        kontrol(f"Tst-h = {trn(Tst_h, 0)} kg  ≤  Tst = {trn(Tst, 0)} kg", bool(tst_uygun)),
    ] if Tst_verildi else [
        metin("Tst girilmediği için kasnak statik yükü DENETLENMEDİ — "
              "imalatçı kataloğundaki sınırla karşılaştırın."),
    ])
    b["aciklamalar"] = [
        "N bir GÜÇ bağıntısıdır ve güç askı oranından bağımsızdır — 2:1'de "
        "kuvvet yarıya iner, halat hızı iki katına çıkar. Askı oranı buraya "
        "yalnız TEK yoldan girer:  halat boyu ( dolayısıyla Gh ) iki katına "
        "çıkar. Verime AYRICA girmez — askı ( palanga ) kaybı η'nın "
        "içindedir ve eski Δη = 0,10 düşüşü kaldırılmıştır.",
        "Gmax, kabin EN ALTTA ve TAM YÜKLÜ iken yukarı çıkarken motorun "
        "yenmesi gereken dengesiz kütledir. Ga = P + q·Q kabulüyle "
        "dengelenmeyen beyan yükü Gden = ( 1 − q )·Q'dur;  üstüne halatın iki "
        "taraf arasındaki FARKI ( MSR ) ve gezici kablonun yarısı eklenir, "
        "denge zincirinin karşıladığı kısım ( MCR ) düşülür.",
        "MSR = i·H·gh·ns:  askı oranı çarpan olarak girer çünkü 2:1'de kabin "
        "1 m indiğinde kabin tarafındaki halat 2 m uzar. Denge zinciri 1:1 "
        "asıldığı için tam dengeleme ( λ = %100 ) tam bu kütleyi ister."]
    #  PAFTAYA GİDEN TEK NOT:  ne alınacağı.  Ötekiler YÖNTEM ANLATIMIDIR ve
    #  aciklamalar'a taşındı — Bolum'ün kendi tanımı böyle ayırıyor ve ekranda
    #  ⓘ altında zaten görünüyorlar.  Dördü birden basılınca tek bir bölüm
    #  paftada yarım sayfa yöntem metni ediyordu.
    b["notlar"] = [f"Binada en az {tr(N)} kW ( {tr(HP)} HP ) gücünde makine "
                   "motor kullanılacaktır."]
    b["aciklamalar"] += [
        "Tst, kasnağın taşıdığı TOPLAM yüktür ( iki halat kolu "
        "artı denge zinciri ) ve makinenin katalog sınırıyla "
        "karşılaştırılır. Denge zinciri Gmax'ta dengesizliği "
        "AZALTIR ama statik yükte ARTIRIR — iki ayrı büyüklüktür. "
        "Makinenin kendi ağırlığı buna girmez — o, kaide "
        "hesabındadır ( bölüm 2 ).",
        "Bu güç KARARLI REJİM gücüdür:  beyan hızındaki dengesiz "
        "yükü karşılar. Kalkış ( ivmelenme ) momenti — kabin, karşı "
        "ağırlık, halat, kasnak ve rotor ataletleri — hesaba "
        "girmez; motor seçiminde üretici kalkış verisi ayrıca "
        "kontrol edilmelidir.",
        "Karşı ağırlık denge oranı q = 0,50 olarak sabittir ( "
        "Ga = P + Q/2 ). Kaynak çalışma kitabının tamamı bu kabul "
        "üzerine kuruludur — karşı ağırlık kütlesi tahrik, ray ve "
        "tampon hesaplarına da aynı yerden girer."]
    _ne = []
    if hesaplanabilir and not (N is not None and N > 0 and g["motor_gucu"] >= N):
        _ne.append("motoru büyütün")
    if tst_uygun is False:
        _ne.append("kasnak statik yükü aşıldı — makineyi büyütün")
    b["sonuc"] = {"baslik": "KONTROL      Nsç ≥ N"
                            + ("   ·   Tst-h ≤ Tst" if Tst_verildi else ""),
                  "metin": "UYGUNDUR." if uygun else
                           ("HESAP YAPILAMADI — sistem verimi ya da halat boyu "
                            "fiziksel değil" if not hesaplanabilir
                            else "UYGUN DEĞİLDİR — " + " ve ".join(_ne)),
                  "uygun": bool(uygun)}
    if not hesaplanabilir:
        b["eksik_hesap"] = b["sonuc"]["metin"]
    return b


# =====================================================================
#  2 -  MAKİNE KONSTRÜKSİYONU                   ( MMO 208/4 - m.3.4.6 )
# =====================================================================
def _makine(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    k1 = US.darbe_k1(O, g["guvenlik_tertibati"])
    Gm, L, L1 = g["makine_agirligi"], g["yan_yatak_boyu"], g["sase_yuksekligi"]
    A = MT.npu(g["dikine_kiris"], "A") * 100            # cm² → mm²
    #  NPU tablosunun 14. sütunu:  atalet YARIÇAPI ix ( cm ).  Excel bu satırı
    #  "Imin — eylemsizlik momenti" diye adlandırır ama λ = L1 / imin
    #  bağıntısında yarıçap kullanılır; adlandırma matematiğe göre yapıldı.
    imin = MT.npu(g["dikine_kiris"], "ix") * 10         # cm → mm
    Wx = MT.npu(g["yan_yatak"], "Wx") * 1000            # cm³ → mm³

    F = k1 * gn * (o["Q"] + o["P"] + o["Gh"] + o["Ga"] + Gm)
    F1 = F / 2.0                                        # yan yatak putreli
    X = L - O["yan_yatak_L_X"]
    FB = F1 * X / L
    FA = F1 - FB
    Mmax = FA * X
    sigma_e = Mmax / Wx
    lam_ham = L1 / imin
    lam = max(20, math.ceil(lam_ham - 1e-9))
    #  Kaide kirişi ST 37'dir ( σem = 130 ) — ω'nın Rm = 370 eğrisi geçerli.
    omega = MT.omega_en8150(lam, MT.OMEGA_RM_ALT)
    sigma_b = FB * omega / A if omega else None
    #  σem "en çok" değeridir:  sınıra eşit gerilme de uygundur.
    #  NEGATİF GERİLME "UYGUN" SAYILMAZ:  gerilme büyüklüktür, işareti
    #  geometrinin ters dönmesinden gelir ( X < 0 ).  Yalnız "≤ σem" bakmak,
    #  −5.350 N/mm² gibi anlamsız bir değeri sessizce geçirirdi.  Girdi
    #  doğrulaması bu geometriyi zaten reddediyor;  bu ikinci kalkandır.
    egilme_uygun = 0 <= sigma_e <= O["sigma_em"]
    burkulma_uygun = (sigma_b is not None and 0 <= sigma_b <= O["sigma_em"])

    o.update(k1=k1, F_kaide=F, FA=FA, FB=FB)
    _kay(o, AB31=k1, AB37=A, AB38=imin, AB41=Wx, AB39=omega, C47=F, I51=F1,
         K58=X, O53=FB, AK53=FA, M63=Mmax, J65=sigma_e, O71=lam_ham, Z71=lam,
         K73=sigma_b)

    b = Bolum("MAKİNE KONSTRÜKSİYONUNUN HESAPLANMASI", kimlik="makine_konstruksiyonu", kaynak="MMO 208/4 - m.3.4.6")
    b["adimlar"] = [
        veri("k1", "Darbe katsayısı", k1, "",
             f"OFİS STANDARDI  ·  {g['guvenlik_tertibati']}"),
        veri("Gm", "Makine motor ağırlığı", Gm, "kg", "GİRİŞ ( üretici kataloğu )"),
        veri("L", "Yan yatak boyu", L, "mm", "GİRİŞ"),
        veri("L1", "Dikine kirişin boyu", L1, "mm", "GİRİŞ"),
        veri("A", "Dikine kirişin kesit alanı", A, "mm²",
             f"NPU {g['dikine_kiris']}", 0),
        veri("imin", "Dikine kirişin atalet yarıçapı", imin, "mm",
             f"NPU {g['dikine_kiris']}"),
        veri("Wx", "Yan yatağın mukavemet momenti", Wx, "mm³",
             f"NPU {g['yan_yatak']}", 0),
        veri("σem", "Emniyet gerilmesi ( ST 37 )", O["sigma_em"], "N/mm²", "OFİS STANDARDI"),
        metin("Kaide üzerindeki en büyük kuvvet :"),
        hesap("F = k1 × gn × ( Q + P + Gh + Ga + Gm )",
              f"{tr(k1)} × {tr(gn)} × ( {trn(o['Q'], 0)} + {trn(o['P'], 0)} + "
              f"{tr(o['Gh'])} + {tr(o['Ga'])} + {trn(Gm, 0)} )", F, "N"),
        metin("Yan yatak putreline gelen kuvvet :"),
        hesap("F1 = F / 2", f"{tr(F)} / 2", F1, "N"),
        hesap("X = L − 335", f"{trn(L, 0)} − {O['yan_yatak_L_X']}", X, "mm"),
        hesap("FB = F1 × X / L", f"{tr(F1)} × {trn(X, 0)} / {trn(L, 0)}", FB, "N"),
        hesap("FA = F1 − FB", f"{tr(F1)} − {tr(FB)}", FA, "N"),
        metin("Kaide yatay kirişlerinde eğilme momenti ve gerilmesi :"),
        hesap("Mmax = FA × X", f"{tr(FA)} × {trn(X, 0)}", Mmax, "N·mm", ondalik=0),
        hesap("σe = Mmax / Wx", f"{trn(Mmax, 0)} / {trn(Wx, 0)}", sigma_e, "N/mm²"),
        kontrol(f"σe = {tr(sigma_e)}  ≤  σem = {tr(O['sigma_em'])} N/mm²  →  "
                f"NPU {g['yan_yatak']}", egilme_uygun),
        metin("Dikine kirişlerin bükülme kontrolü :"),
        hesap("λ = L1 / imin", f"{trn(L1, 0)} / {tr(imin)}", lam_ham, ""),
        veri("λ", "Yuvarlanmış burkulma narinliği ( en az 20 )", lam, "", "11!Z71", 0),
        veri("ω", "Omega değeri", omega, "", f"Burkulma tablosu  λ = {lam}", 4),
        hesap("σb = FB × ω / A",
              f"{tr(FB)} × {tr(omega)} / {trn(A, 0)}", sigma_b, "N/mm²"),
        kontrol(f"σb = {tr(sigma_b)}  ≤  σem = {tr(O['sigma_em'])} N/mm²  →  "
                f"NPU {g['dikine_kiris']}", burkulma_uygun),
    ]
    b["sonuc"] = {"baslik": "KONTROL      σe ≤ σem   ve   σb ≤ σem",
                  "metin": "UYGUNDUR." if (egilme_uygun and burkulma_uygun)
                           else "UYGUN DEĞİLDİR — kiriş kesitini büyütün",
                  "uygun": bool(egilme_uygun and burkulma_uygun)}
    b["aciklamalar"] = [
        "Kiriş statiği:  açıklığı L olan basit kirişte, A mesnedinden X "
        "uzaktaki tekil yük için  FA = F1·(L−X)/L,  FB = F1·X/L,  "
        "Mmax = FA·X.  Burkulmada σb = FB·ω/A ( omega yöntemi ) ve "
        "λ = L1/imin — yani burkulma boyu Lk = L1 alınır, iki ucu mafsallı "
        "kabulüdür ( β = 1,0 ).  Kolon tek ucundan ankastre, öbür ucu "
        "serbestse bu kabul narinliği OLDUĞUNDAN KÜÇÜK gösterir."]
    #  İKİSİ DE YÖNTEM ANLATIMI — paftaya değil, ekrandaki ⓘ'ye.
    b["aciklamalar"] += [
        "Darbe katsayısı k1 ve emniyet gerilmesi σem OFİS KABULLERİDİR "
        "( Sabitler sekmesinden değiştirilir ). TS EN 81-20 makine kaidesi için yük "
        "modeli vermez — Çizelge 14 (k1·k2·k3) o standartta açıkça KILAVUZ "
        "RAY hesabına aittir. Buradaki kullanım ödünçtür ve emniyetli "
        "taraftadır:  k1 makinenin kendi ağırlığına da uygulanır ve σem, "
        "aynı standardın ST 37 için verdiği Rm/1,8 = 205,6 N/mm²'nin "
        "yaklaşık yarısıdır. Sonuç, kirişin gereğinden kalın çıkmasıdır.",
        "Güvenlik tertibatı tipi bu bölümü doğrudan büyütür ( k1 = 2 · 3 · 5 ): "
        "ani frenlemeli tertibatta kaide yükü kaymalıya göre 2,5 kat çıkar. "
        "Kesit bu yüzden UYGUN DEĞİL çıkıyorsa, ofis kabulü gözden "
        "geçirilmeli — standart bu katsayıyı burada zorunlu kılmaz."]
    return b


# =====================================================================
#  3 -  KULLANILABİLİR KABİN ALANI              ( TS EN 81-20 m.5.4.2 )
# =====================================================================
def _kabin_alani(g, o):
    Q = g["beyan_yuku"]
    W, D = g["kabin_genisligi"], g["kabin_derinligi"]
    azami = MT.kabin_azami_alan(Q)
    asgari = MT.kabin_asgari_alan(Q)
    kisi = MT.kabin_kisi(Q)
    alan = (W * D) / 1e6
    pervaz = g["uzun_pervaz"]
    #  TS EN 81-20 m.5.4.2.1.3'ün son fıkrası, kapı kasası dikmeleri arasındaki
    #  girinti için İKİ KURAL verir:
    #      a)  derinlik ≤ 100 mm  →  alana HİÇ katılmaz;
    #      b)  derinlik > 100 mm  →  "the TOTAL available area shall be
    #          included in the floor area" — girintinin TAMAMI katılır.
    #  Kitap ( 11!X84 ) tamamı yerine kapı genişliğinin YARISINI alıyordu:
    #  900 mm kapı + 300 mm pervazda 0,1350 m² yazıyor, tamı 0,2700 m².
    #  Kullanılabilir alanı küçük göstermek EMNİYETSİZ yöndür — Çizelge 6'nın
    #  izin verdiğinden büyük bir kabine izin verilir.
    #  Eşik de düzeltildi:  standart "≤ 100 mm hariç" der, kitap 100 mm'yi
    #  dahil ediyordu.
    girinti_var = pervaz > 100
    if girinti_var:
        alan += (g["kapi_genisligi"] * pervaz) / 1e6
    ust_uygun = azami is not None and azami >= alan
    alt_uygun = asgari is not None and alan >= asgari
    o.update(kabin_alani=alan, kabin_kisi=kisi)
    _kay(o, X84=alan, AC82=azami, L86=kisi, AK88=asgari)

    b = Bolum("KULLANILABİLİR KABİN ALANI", kimlik="kabin_alani", kaynak="TS EN 81-20 m.5.4.2")
    b["adimlar"] = [
        veri("Q", "Beyan yükü", Q, "kg", "GİRİŞ"),
        veri("", "Kabin genişliği × derinliği", f"{trn(W, 0)} × {trn(D, 0)} mm"),
        hesap("Kabin alanı = ( genişlik × derinlik ) / 10⁶"
              + ("  +  ( kapı genişliği × uzun pervaz ) / 10⁶"
                 if girinti_var else ""),
              f"( {trn(W, 0)} × {trn(D, 0)} ) / 10⁶"
              + (f" + ( {trn(g['kapi_genisligi'], 0)} × {trn(pervaz, 0)} ) / 10⁶"
                 if girinti_var else
                 f"   ( pervaz {trn(pervaz, 0)} mm ≤ 100 mm — girinti alana katılmaz )"),
              alan, "m²", "TS EN 81-20 m.5.4.2.1.3", 4),
        veri("", f"{trn(Q, 0)} kg için kullanılabilir EN BÜYÜK kabin alanı",
             azami, "m²", "EN 81-20 Çizelge 6"),
        kontrol(f"Kabin alanı {tr(alan)} m²  ≤  {tr(azami)} m²", ust_uygun),
        veri("", "Kabindeki insan sayısı", kisi, "kişi", "EN 81-20 Çizelge 6", 0),
        veri("", f"{trn(kisi, 0)} kişi için kullanılabilir EN KÜÇÜK kabin alanı",
             asgari, "m²", "EN 81-20 Çizelge 8"),
        kontrol(f"Kabin alanı {tr(alan)} m²  ≥  {tr(asgari)} m²", alt_uygun),
    ]
    b["sonuc"] = {"baslik": "KONTROL      Amin  ≤  Akabin  ≤  Amax",
                  "metin": "UYGUNDUR." if (ust_uygun and alt_uygun)
                           else "UYGUN DEĞİLDİR — kabin ölçülerini düzeltin",
                  "uygun": bool(ust_uygun and alt_uygun)}
    return b


# =====================================================================
#  4 -  ASKI HALATLARI                           ( TS EN 81-50 m.5.12 )
# =====================================================================
def _aski_halatlari(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    Dt, dh, nh, r = o["Dt"], o["dh"], o["nh"], o["r"]
    Dp = g["saptirma_kasnak_capi"]                       # ORTALAMA — Kp için
    #  Ds — EN KÜÇÜK kasnak çapı.  m.5.5.2.1'in D/dr ≥ 40 sınırı HER kasnak
    #  için geçerlidir;  Kp = (Dt/Dp)⁴ ise ortalama bükülme şiddetidir.
    #  Girilmezse ortalamaya düşülür — eski davranış, sonuç değişmez.
    Ds = g.get("saptirma_kasnak_min_capi")
    Ds_verildi = _pozitif(Ds)
    Ds = float(Ds) if Ds_verildi else Dp
    oran = Dt / dh
    oran_uygun = oran >= S["Dt_dh_asgari"]

    Nps, Npr = g["kasnak_tek_yon"], g["kasnak_ters_yon"]
    #  SAPTIRMA KASNAĞI DA m.5.5.2.1 KAPSAMINDADIR.
    #  Madde oranı "kasnak, makara ve tamburlar" için ister;  tahrik kasnağına
    #  özel değildir.  Kitap yalnız Dt'yi sınıyordu:  Dp hesaba SADECE
    #  Kp = (Dt/Dp)⁴ olarak giriyor, kendi oranı hiç bakılmıyordu — Dt/dh = 50
    #  ama Dp/dh = 30 olan bir tesis "UYGUN" çıkıyordu.
    #  Kasnak yoksa ( Nps = Npr = 0 ) ortada denetlenecek kasnak da yoktur.
    kasnak_var = (Nps or 0) + (Npr or 0) > 0
    oran_p = Ds / dh
    oran_p_uygun = (not kasnak_var) or oran_p >= S["Dt_dh_asgari"]
    #  Nequiv(t) OFİS AÇILARINDAN HESAPLANIR  ( EN 81-50 Çizelge 2 ).
    #  Kitap bunu kanalın ADINA bağlı sabit bir tablodan okuyordu:  ofis
    #  sabiti γ = 45° yapılsa bile Nequiv(t) 12 kalıyor, pafta γ = 38° yazmayı
    #  sürdürüyordu — hesabın bölüm 6'da kullandığı sayı ile paftaya basılan
    #  sayı ayrışıyordu.
    sekil = g["kanal_sekli"]
    gama = MT.kanal_acisi(sekil, O["kanal_gama_v"], O["kanal_gama_yd"])
    beta = MT.kanal_beta(sekil, O["kanal_beta"])
    Nequiv_t = MT.kanal_nequiv_t(sekil, O["kanal_gama_v"], O["kanal_beta"])
    _gh4, Tmin, _gh4_kaynak, Tmin_kaynak = _halat_verisi(g)
    nh_uygun = nh >= 2 and float(nh).is_integer()
    Smin = 16 if nh == 2 else 12
    Kp = (Dt / Dp) ** 4
    Nequiv_p = Kp * (Nps + 4 * Npr)
    Nequiv = Nequiv_t + Nequiv_p
    #  EN 81-50 m.5.12 halat güvenlik katsayısı
    Sf = 10 ** (2.6834 - (math.log10(695.85e6 * Nequiv / oran ** 8.567)
                          / math.log10(77.09 * oran ** -2.894)))
    Fmax = gn * o["F1"] / r
    Sger = nh * Tmin / Fmax
    sinir = max(Sf, Smin)
    #  "Sf ≥ Smin" BİR GEÇME ÖLÇÜTÜ DEĞİLDİR  ( bkz. EXCEL_FARKLARI ).
    #  Belirleyici olanın hangisi olduğunu söyler, o kadar.
    belirleyici = "Sf  ( EN 81-50 m.5.12 )" if Sf >= Smin else \
                  f"Smin = {trn(Smin, 0)}  ( EN 81-20 m.5.5.2.2 )"
    s_uygun = Sger >= sinir
    o.update(Sf=Sf, S_gercek=Sger)
    _kay(o, N97=oran, AH104=Nequiv_t, AH109=Tmin, AH110=Smin, T112=Kp,
         P114=Nequiv_p, V116=Nequiv, T125=Sf, T126=Sger)

    b = Bolum("ASKI HALATLARININ HESAPLANMASI", kimlik="aski_halatlari", kaynak="TS EN 81-50 m.5.12")
    b["adimlar"] = [
        #  PAFTADA KONTROL SATIRI YALNIZ KARARINI BASAR ( "UYGUN" ).  Neyin
        #  kontrolü olduğunu ÖNÜNDEKİ değer satırı söyler;  o olmadan pafta
        #  bölümün başında bağlamsız bir "UYGUN" gösteriyordu.
        metin("Askı halatı sayısı  ( TS EN 81-20 m.5.5.1.3 ) :"),
        veri("nh", "Askı halatı adedi", nh, "adet", "GİRİŞ", 0),
        kontrol(f"Askı halatı adedi nh = {tr(nh)} ≥ 2  ( TS EN 81-20 m.5.5.1.3 )", nh_uygun),
        metin("Tahrik kasnağı & askı halatı oranı  ( TS EN 81-20 m.5.5.2.1 ) :"),
        hesap("Dt / dh", f"{trn(Dt, 0)} / {tr(dh)}", oran, ""),
        kontrol(f"Dt / dh = {tr(oran)}  ≥  {S['Dt_dh_asgari']}", oran_uygun),
    ] + ([
        veri("Ds", "Kasnakların EN KÜÇÜK çapı", Ds, "mm",
             "GİRİŞ" if Ds_verildi else "girilmedi — ortalama çap kullanıldı", 0),
        hesap("Ds / dh", f"{trn(Ds, 0)} / {tr(dh)}", oran_p, ""),
        kontrol(f"Ds / dh = {tr(oran_p)}  ≥  {S['Dt_dh_asgari']}", oran_p_uygun),
    ] if kasnak_var else [
        metin("Tahrik kasnağı dışında kasnak yok  ( Nps = Npr = 0 ) — "
              "saptırma kasnağı oranı denetlenmedi."),
    ]) + [
        metin("Halat güvenlik katsayısının hesaplanması :"),
        veri("", "Kanal tipi", sekil),
        veri("γ", "Kanal açısı  ( hesapta kullanılan )", gama, "°",
             "OFİS STANDARDI  ·  " + ("yarım daire" if MT.kanal_yarim_daire_mi(sekil)
                                      else "V kanal"), 0),
        veri("β", "Alt kesilme açısı", beta, "°",
             "OFİS STANDARDI" if MT.kanal_alti_kesik_mi(sekil)
             else "alt kesilme yok", 0),
        veri("Nequiv(t)", "Kasnakların eşdeğer sayısı", Nequiv_t, "",
             "EN 81-50 Çizelge 2  ·  "
             + (f"β = {trn(beta, 0)}°" if MT.kanal_alti_kesik_mi(sekil)
                else (f"γ = {trn(gama, 0)}°" if not MT.kanal_yarim_daire_mi(sekil)
                      else "alt kesilmesiz yarım daire"))
             + (f"  ×  {trn(MT.kanal_gecis_sayisi(sekil), 0)} geçiş"
                if (MT.kanal_gecis_sayisi(sekil) or 1) > 1 else ""), 2),
        veri("Nps", "Tek yönde bükülmeli kasnak sayısı", Nps, "adet", "GİRİŞ", 0),
        veri("Npr", "Ters yönde bükülmeli kasnak sayısı", Npr, "adet", "GİRİŞ", 0),
        veri("Dp", "Tahrik kasnağı hariç kasnakların ortalama çapı", Dp, "mm", "GİRİŞ"),
        veri("r", "Halat askı oranı", r, "", "GİRİŞ", 0),
        veri("Tmin", "Halatın en küçük kopma değeri", Tmin, "N", Tmin_kaynak, 0),
        veri("Smin", "Asgari halat güvenlik katsayısı", Smin, "",
             "EN 81-20 m.5.5.2.2  ( nh = 2 ise 16 )", 0),
        hesap("Kp = ( Dt / Dp )⁴", f"( {trn(Dt, 0)} / {trn(Dp, 0)} )⁴", Kp, "", ondalik=4),
        hesap("Nequiv(p) = Kp × ( Nps + 4 × Npr )",
              f"{tr(Kp)} × ( {trn(Nps, 0)} + 4 × {trn(Npr, 0)} )", Nequiv_p, "",
              "EN 81-50 m.5.12.2"),
        hesap("Nequiv = Nequiv(t) + Nequiv(p)",
              f"{tr(Nequiv_t)} + {tr(Nequiv_p)}", Nequiv, ""),
        hesap("Sf = 10^[ 2,6834 − log( 695,85·10⁶ · Nequiv / (Dt/dh)^8,567 ) "
              "/ log( 77,09 · (Dt/dh)^−2,894 ) ]",
              f"Nequiv = {tr(Nequiv)} ,  Dt/dh = {tr(oran)}", Sf, "",
              "EN 81-50 m.5.12"),
        veri("", "Belirleyici asgari güvenlik katsayısı", belirleyici, "",
             f"max( Sf = {tr(Sf)} ; Smin = {trn(Smin, 0)} ) = {tr(sinir)}"),
        hesap("S = nh × Tmin / Fmax        ( Fmax = gn × F1 / r )",
              f"{trn(nh, 0)} × {trn(Tmin, 0)} / ( {tr(gn)} × {tr(o['F1'])} / {trn(r, 0)} )",
              Sger, ""),
        kontrol(f"S = {tr(Sger)}  ≥  max( Sf ; Smin ) = {tr(sinir)}", s_uygun),
    ]
    _esik = trn(S["Dt_dh_asgari"], 0)
    b["sonuc"] = {"baslik": (f"KONTROL      Dt/dh ≥ {_esik}"
                             + (f"   ·   Ds/dh ≥ {_esik}" if kasnak_var else "")
                             + "   ·   S ≥ max( Sf ; Smin )"),
                  "metin": "UYGUNDUR." if (nh_uygun and oran_uygun and oran_p_uygun and s_uygun)
                           else ("UYGUN DEĞİLDİR — "
                                 + " ve ".join(
                                     ([f"tahrik kasnağı çapını büyütün ya da halat çapını "
                                       f"küçültün ( Dt/dh = {tr(oran)} )"]
                                      if not oran_uygun else [])
                                     + ([f"saptırma kasnağı çapını büyütün ya da halat "
                                         f"çapını küçültün ( Ds/dh = {tr(oran_p)} )"]
                                        if not oran_p_uygun else [])
                                     + (["en az iki bağımsız askı halatı kullanın"] if not nh_uygun else [])
                                     + (["halat çapını / adedini artırın"]
                                        if not s_uygun else []))),
                  "uygun": bool(nh_uygun and oran_uygun and oran_p_uygun and s_uygun)}
    b["notlar"] = []
    _iki_cap = []
    if kasnak_var:
        #  YÖNTEM ANLATIMI — paftaya değil ekrandaki ⓘ'ye.  Uygulanabilir
        #  öğüdü ( "Ds'yi girin" ) zaten Ds satırının kaynak kolonunda yazılı.
        _iki_cap.append(
            "İKİ AYRI ÇAP KULLANILIR:  Kp = (Dt/Dp)⁴ ORTALAMA çapı ister "
            "( ortalama bükülme şiddeti ), m.5.5.2.1'in D/dr ≥ "
            f"{trn(S['Dt_dh_asgari'], 0)} sınırı ise HER kasnak için geçerli "
            "olduğundan EN KÜÇÜK çapa ( Ds ) uygulanır. Ds girilmezse "
            "ortalamaya düşülür;  çapları farklı bir askı düzeninde Ds'yi "
            "mutlaka girin — ortalama sınırı geçse de tek bir küçük kasnak "
            "geçemiyor olabilir.")
    if r > 1 and Nps < 2:
        b["notlar"] += [
            "⚠ Palangalı ( 1:" + trn(r, 0) + " ) sistemde halatın en olumsuz "
            "kesiti genelde tahrik kasnağı + EN AZ İKİ kabin kasnağı üzerinden "
            "geçer ( EN 81-50 Ek E ). Tek yönde bükülmeli kasnak sayısı "
            f"{trn(Nps, 0)} girilmiş; tesisin gerçek askı düzenine göre "
            "denetleyin — düşük girilirse Nequiv, dolayısıyla gereken "
            "asgari güvenlik katsayısı olduğundan küçük çıkar."]
    b["aciklamalar"] = _iki_cap + [
        "TS EN 81-20 m.5.5.2.2:  'Askı elemanlarının güvenlik katsayısı … 12'den "
        "( iki halatta 16'dan ) az olamaz.  BUNA EK OLARAK askı halatlarının "
        "güvenlik katsayısı EN 81-50 m.5.12'ye göre hesaplanandan az olamaz.'  "
        "Yani ölçüt tektir:  GERÇEKLEŞEN S, ikisinin BÜYÜĞÜNDEN küçük olmayacak. "
        "Sf'nin kendisinin 12'yi geçmesi ŞART DEĞİLDİR — Sf < 12 yalnız "
        "'asgariyi Smin belirliyor' demektir. Kitap buna ayrıca 'Sf ≥ Smin' "
        "diye bir geçme koşulu koyuyordu ( 11!AH125 ) ve standarda uyan "
        "tasarımları reddediyordu:  Sf = 7,89 · S = 32,54 olan bir askı — hem "
        "7,89'un hem 12'nin çok üstünde — 'UYGUN DEĞİLDİR' alıyordu.  Verilen "
        "öğüt de sonuca ulaşmıyordu:  halat çapını artırmak Dt/dh'yi düşürür ve "
        "Sf'yi BÜYÜTÜR, koşul hiçbir zaman sağlanamazdı.",
        "TS EN 81-20 m.5.5.2.1: tahrik kasnağı / saptırma kasnağı bölüm dairesi "
        "çapının askı halatı anma çapına oranı, halatın kol sayısından bağımsız "
        "olarak EN AZ 40 olmalıdır. Kaynak Excel bu kontrolü 30 ile yapar; 30 "
        "aynı standardın dengeleme halatı gergi kasnağı ( m.5.5.6.2 ) ve "
        "regülatör ( m.5.6.2.2.1.3 ) eşiğidir, askı halatının değil."]
    return b


# =====================================================================
#  5 -  HIZ REGÜLATÖRÜ HALATI               ( TS EN 81-20 m.5.6.2.2.1 )
# =====================================================================
def _regulator(g, o):
    S, gn = SABIT, SABIT["gn"]
    Dreg, dreg = g["reg_kasnak_capi"], g["reg_halat_capi"]
    mu, gama = g["reg_surtunme"], g["reg_kanal_acisi"]
    alfa = S["reg_sarilma_aci"]
    #  Regülatör halatı kuyu boyunca iki kat gider  ( 11!AI134 )
    boy = ((sum(g["durak_yukseklikleri"]) + g["kaide_yuksekligi"]
            - S["ray_kaide_payi"]) * 2) / 1000.0
    gh = MT.halat_agirlik(dreg) * boy
    Gra = g["reg_gergi_agirligi"]
    Tmin = MT.halat_kopma(dreg)

    oran = Dreg / dreg
    oran_uygun = oran >= S["Dreg_dreg_asgari"]
    f = mu / math.sin(math.radians(gama) / 2.0)
    efa = math.exp(f * math.radians(alfa))
    Freg = gn * (gh + Gra) / 2.0
    Freg2 = Freg * efa
    #  TS EN 81-20 m.5.6.2.2.1.1 d):  regülatörün ürettiği çekme kuvveti,
    #  şu İKİ değerin BÜYÜĞÜNDEN az olamaz —
    #      · güvenlik tertibatını devreye sokmak için GEREKENİN İKİ KATI,
    #      · 300 N.
    #  Kitap ikinci sınıra "2 × Freg" koyuyordu;  Freg halatın kendi statik
    #  gergisidir, güvenlik tertibatını devreye sokan kuvvet DEĞİLDİR.  O
    #  kuvvet imalatçıdan / tip inceleme belgesinden gelir.  Kitabın ölçütü
    #  e^(f·α') ≥ 2 demeye geliyordu ve standardın istemediği bir koşulla
    #  tasarımları reddedebiliyordu.
    F_devreye = g.get("guvenlik_devreye_kuvvet")
    devreye_var = isinstance(F_devreye, (int, float)) and not isinstance(
        F_devreye, bool) and F_devreye > 0
    sinir = max(S["reg_kuvvet_asgari"], 2 * F_devreye) if devreye_var \
        else S["reg_kuvvet_asgari"]
    sinir_metni = (f"max( {trn(S['reg_kuvvet_asgari'], 0)} N ; 2 × "
                   f"{tr(F_devreye)} N )" if devreye_var
                   else f"{trn(S['reg_kuvvet_asgari'], 0)} N")
    Fcekme = Freg2 - Freg
    kuvvet_uygun = devreye_var and Fcekme >= sinir

    #  ── TS EN 81-20 m.5.6.2.1.2.1 b)  ve  m.5.6.2.2.1.1 a) ────────────
    #  Kitap ikisini de hiç denetlemiyordu:  2,5 m/s'lik bir asansöre ani
    #  frenlemeli tertibat konsa da, regülatör hangi hızda devreye girerse
    #  girsin bölüm "UYGUNDUR" diyordu.
    v = g["beyan_hizi"]
    tertibat = g["guvenlik_tertibati"]
    ani = tertibat.startswith("Ani Frenlemeli")
    makarali = tertibat == "Ani Frenlemeli Makaralı"
    #  m.5.6.2.1.2.1 b):  ani frenlemeli KABİN tertibatı yalnız v ≤ 0,63 m/s
    tip_uygun = (not ani) or v <= S["ani_tertibat_azami_v"]
    #  m.5.6.2.2.1.1 a):  alt sınır 1,15·v ;  üst sınır tertibat tipine bağlı
    v_alt = S["reg_hiz_alt_carpan"] * v
    if ani:
        v_ust = S["reg_hiz_ust_makara"] if makarali else S["reg_hiz_ust_ani"]
        ust_dayanak = ("m.5.6.2.2.1.1 a) 2)  ani frenlemeli makaralı" if makarali
                       else "m.5.6.2.2.1.1 a) 1)  ani frenlemeli")
    elif v <= 1.0:
        v_ust = S["reg_hiz_ust_kaymali"]
        ust_dayanak = "m.5.6.2.2.1.1 a) 3)  kaymalı, v ≤ 1,0 m/s"
    else:
        v_ust = 1.25 * v + 0.25 / v
        ust_dayanak = "m.5.6.2.2.1.1 a) 4)  1,25·v + 0,25/v"
    v_dev = g.get("reg_devreye_hizi")
    hiz_var = isinstance(v_dev, (int, float)) and not isinstance(v_dev, bool) \
        and v_dev > 0
    hiz_uygun = (v_alt <= v_dev < v_ust) if hiz_var else True
    kat = Tmin / Freg2
    kat_uygun = kat >= S["reg_kat_asgari"]

    _kay(o, AI134=gh, AI136=Tmin, J142=oran, W146=f, AF146=efa, W151=Freg,
         J156=Freg2, U156=Fcekme, AA156=sinir, G161=kat)

    b = Bolum("HIZ REGÜLATÖRÜ HALATININ HESAPLANMASI", kimlik="regulator_halati",
              kaynak="TS EN 81-20 m.5.6.2.2.1  /  TS EN 81-50 m.5.11.2.3")
    b["adimlar"] = [
        veri("Dreg", "Regülatör kasnak çapı", Dreg, "mm", "GİRİŞ"),
        veri("dreg", "Regülatör halat çapı", dreg, "mm", "GİRİŞ"),
        veri("μ", "Sürtünme faktörü", mu, "", "GİRİŞ"),
        veri("γ", "Kanal açısı", gama, "°", "GİRİŞ", 0),
        veri("α'", "Regülatör kasnağı sarılma açısı", alfa, "°", "Ofis kabulü", 0),
        hesap("gh = ( 1 m ağırlık ) × ( Σ durak + kaide − 200 ) × 2 / 1000",
              f"{tr(MT.halat_agirlik(dreg))} × {tr(boy)}", gh, "kg"),
        veri("Gra", "Regülatör alt ağırlığı ve kasnak kütlesi", Gra, "kg", "GİRİŞ"),
        veri("Fgt", "Güvenlik tertibatını devreye sokma kuvveti",
             F_devreye if devreye_var else "girilmedi", "N" if devreye_var else "",
             "GİRİŞ  ( imalatçı / tip inceleme belgesi )" if devreye_var
             else "İMALATÇI VERİSİ — girilmediği için 2·Fgt sınırı denetlenemedi"),
        veri("T'min", "Halatın en küçük kopma yükü", Tmin, "N", "TS 12385-5", 0),
        metin("Güvenlik tertibatı tipi & beyan hızı  ( m.5.6.2.1.2.1 ) :"),
        veri("", "Kabin güvenlik tertibatı tipi", tertibat, "", "GİRİŞ"),
        kontrol(f"{tertibat} tertibat, v = {tr(v)} m/s"
                + (f"  ≤  {tr(S['ani_tertibat_azami_v'])} m/s"
                   if ani else "  ( kaymalı — hız sınırı yok )"), tip_uygun),
        metin("Regülatör devreye girme hızı  ( m.5.6.2.2.1.1 a) ) :"),
        hesap("v_alt = 1,15 × v", f"1,15 × {tr(v)}", v_alt, "m/s",
              "en az beyan hızının %115'i", 3),
        hesap("v_üst", ust_dayanak, v_ust, "m/s", "tertibat tipine bağlı", 3),
        veri("v_dev", "Regülatör devreye girme hızı",
             v_dev if hiz_var else "seçilecek", "m/s" if hiz_var else "",
             "GİRİŞ  ( imalatçı / tip inceleme belgesi )" if hiz_var
             else f"İMALATÇI ŞARTI — [{tr(v_alt)}, {tr(v_ust)}) m/s aralığında olmalıdır", 3 if hiz_var else None),
        kontrol(f"{tr(v_alt)} ≤ v_dev = {tr(v_dev)} < {tr(v_ust)} m/s", hiz_uygun)
        if hiz_var else
        kontrol(f"Şart:  {tr(v_alt)} m/s  ≤  v_dev  <  {tr(v_ust)} m/s", True,
                "Regülatör bu aralıkta seçilmelidir"),
        metin("Regülatör kasnağı & halat oranı :"),
        hesap("Dreg / dreg", f"{trn(Dreg, 0)} / {tr(dreg)}", oran, ""),
        kontrol(f"Dreg / dreg = {tr(oran)}  ≥  {S['Dreg_dreg_asgari']}", oran_uygun),
        metin("Regülatör halatında oluşan gergi kuvveti :"),
        hesap("f = μ / sin( γ / 2 )",
              f"{tr(mu)} / sin( {trn(gama, 0)}° / 2 )", f, "", ondalik=4),
        hesap("e^(f·α')", f"exp( {tr(f)} × {trn(alfa, 0)}° )", efa, "", ondalik=4),
        hesap("Freg = gn × ( gh + Gra ) / 2",
              f"{tr(gn)} × ( {tr(gh)} + {trn(Gra, 0)} ) / 2", Freg, "N"),
        hesap("F'reg = Freg × e^(f·α')", f"{tr(Freg)} × {tr(efa)}", Freg2, "N"),
        hesap("Fçekme = F'reg − Freg",
              f"{tr(Freg2)} − {tr(Freg)}", Fcekme, "N",
              "regülatörün ÜRETTİĞİ çekme kuvveti  —  m.5.6.2.2.1.1 d)"),
        #  İMALATÇI KUVVETİ YOKSA BU SATIR "UYGUN DEĞİL" DEMEZ.
        #  Sınırın kendisi bilinmiyor;  sağlanmış bir eşitsizliğin yanına
        #  "UYGUN DEĞİL" yazmak paftada çelişki gibi okunurdu
        #  ( Fçekme = 1.981 N ≥ 300 N doğrudur ).  Doğrusu:  DENETLENEMEDİ.
        kontrol(f"Fçekme = {tr(Fcekme)} N  ≥  {sinir_metni} = {tr(sinir)} N",
                kuvvet_uygun) if devreye_var else
        kontrol(f"Fçekme = {tr(Fcekme)} N  ≥  max( "
                f"{trn(S['reg_kuvvet_asgari'], 0)} N ; 2 × devreye sokma "
                "kuvveti )", False,
                "DENETLENEMEDİ — imalatçı kuvveti girilmedi"),
        metin("Regülatör halatı emniyet katsayısı :"),
        hesap("T'min / F'reg", f"{trn(Tmin, 0)} / {tr(Freg2)}", kat, ""),
        kontrol(f"T'min / F'reg = {tr(kat)}  ≥  {S['reg_kat_asgari']}", kat_uygun),
    ]
    #  Başlık, imalatçı kuvveti yokken SAYI yazmaz:  sınır bilinmiyor.
    _baslik_sinir = sinir_metni if devreye_var else (
        f"max( {trn(S['reg_kuvvet_asgari'], 0)} N ; 2 × devreye sokma kuvveti )")
    b["sonuc"] = {"baslik": (f"KONTROL      Dreg/dreg ≥ {trn(S['Dreg_dreg_asgari'], 0)}"
                             f"   ·   Fçekme ≥ {_baslik_sinir}"
                             f"   ·   T'min/F'reg ≥ {trn(S['reg_kat_asgari'], 0)}"),
                  "metin": "UYGUNDUR." if (tip_uygun and hiz_uygun and oran_uygun
                                            and kuvvet_uygun and kat_uygun)
                           else ("UYGUN DEĞİLDİR"
                                 + (f" — {tertibat} tertibat en çok "
                                    f"{tr(S['ani_tertibat_azami_v'])} m/s'de kullanılır "
                                    f"( m.5.6.2.1.2.1 b) )" if not tip_uygun
                                    else (" — regülatör devreye girme hızı izin verilen sınırların dışındadır"
                                          if not hiz_uygun else ""))),
                  "uygun": bool(tip_uygun and hiz_uygun and oran_uygun
                                and kuvvet_uygun and kat_uygun)}
    b["aciklamalar"] = [
        "TS EN 81-20 m.5.6.2.2.1.1 d):  'the tensile force in the overspeed "
        "governor rope produced by the governor, when tripped, shall be at "
        "least the greater of … twice that necessary to engage the safety "
        "gear, or 300 N.'  İkinci sınırdaki kuvvet GÜVENLİK TERTİBATINI "
        "DEVREYE SOKAN kuvvettir ve imalatçıdan gelir — halatın statik "
        "gergisi Freg değildir.",
        "μ, TS EN 81-20 m.5.6.2.2.1.3 b)'nin verdiği µmax = 0,2 ile "
        "sınırlıdır:  emniyet katsayısı hesabında bundan büyük bir sürtünme "
        "varsayılamaz."]
    if not devreye_var:
        b["sonuc"]["metin"] = "HESAP EKSİK — güvenlik tertibatını devreye sokma kuvveti girilmedi"
        b["eksik_hesap"] = b["sonuc"]["metin"]
        b["notlar"] = [
            "⚠ 'Güvenlik tertibatını devreye sokma kuvveti' GİRİLMEDİ.  "
            "TS EN 81-20 m.5.6.2.2.1.1 d) sınırı  max( 300 N ; 2 × o kuvvet )  "
            "olarak verir;  ikinci terim bilinmediği için sınırın kendisi "
            "bilinmiyor ve madde DENETLENEMİYOR.  Bu yüzden bölüm 'uygun "
            "değil' değil, HESAP EKSİK sayılır ve proje 'uygundur' çıkmaz.  "
            "Kuvvet, güvenlik tertibatı ile regülatörün TİP İNCELEME "
            "BELGELERİNDEN okunup buraya girilmelidir."]
    return b


# =====================================================================
#  6 -  TAHRİK YETENEĞİ                  ( TS EN 81-50 m.5.11.2 / 5.11.3 )
# =====================================================================
#  Yük durumları  —  Excel'in "Askı Tipleri" sayfası ( L…Q sütunları ).
#  Her durum, EN 81-50 m.5.11.2 terimlerini kendi işaretleriyle üretir.
YUK_DURUMLARI = (
    ("yukleme", "Kabinin yüklenmesi  ( %125 yüklü kabin en alt durakta dururken )"),
    ("fren_alt", "Acil frenleme  ( %100 yüklü kabin en alt durakta )"),
    ("fren_ust", "Acil frenleme  ( boş kabin en üst durakta )"),
    ("bloke", "Karşı ağırlığın asılı kalması  ( boş kabin en üstte )"),
)


def _terimler(g, o, durum):
    """Bir yük durumunun EN 81-50 m.5.11.2 terimleri  ( Askı Tipleri sayfası )."""
    S = SABIT
    Q, P, r = o["Q"], o["P"], o["r"]
    nh, gh, H = o["nh"], o["gh"], g["seyir_mesafesi"]
    Mcwt = g["karsi_agirlik"]
    a_in = g["acil_frenleme_a"]
    w_kablo = ((MT.kablo_agirligi(g["kablo_tipi_1"]) or 0)
               + (MT.kablo_agirligi(g["kablo_tipi_2"]) or 0))
    ycar = ycwt = H / 2.0        # Askı Tipleri!*131 · *132

    #  ASKI KASNAKLARININ ATALETİ  —  yalnız askı oranı > 1 iken  ( koşul III )
    mP, _J, _A = _kasnak_atalet(g, o["ofis"])
    _cok = r > 1
    t = {"P": P, "Q": 0.0, "Mcwt": Mcwt, "MCRcar": 0.0, "MCRcwt": 0.0,
         "MComp": 0.0, "MTrav": 0.0, "mPTD": 0.0, "mDP": 0.0, "iPDT": 0.0,
         "mPcar": mP if _cok else 0.0, "mPcwt": mP if _cok else 0.0,
         "iPcar": o["ofis"]["kasnak_adet_kabin"] if _cok else 0,
         "iPcwt": o["ofis"]["kasnak_adet_agirlik"] if _cok else 0,
         "r": r, "gn": S["gn"], "a": 0.0,
         "MSRcar": 0.0, "MSRcwt": 0.0, "FRcar": 0.0, "FRcwt": 0.0}
    #  MSR:  askı halatlarının kabin / karşı ağırlık tarafındaki indirgenmiş
    #  kütlesi.  Kabin ve karşı ağırlık tarafı Excel'de AYRI satırlardan
    #  ( ycar · ycwt ) okunur;  ikisi sayısal olarak eşit olsa da ayrım korunur.
    #  ------------------------------------------------------------------
    #  HALAT KÜTLESİNİN TARAF DAĞILIMI      EN 81-50 m.5.11.2.2
    #  ------------------------------------------------------------------
    #  MSR = ( 0,5·H ± y ) · ns · ( halatın 1 m kütlesi ).  ± işareti kabinin
    #  KUYUDAKİ KONUMUNDAN çıkar.  Üstte makineli bir tesiste halat, tahrik
    #  kasnağından kabine ve karşı ağırlığa iner:
    #      kabin EN ALTTA  →  kabin tarafındaki halat UZUN   ( 0,5·H + y = H )
    #                          ağırlık üsttedir, o taraf KISA ( 0,5·H − y = 0 )
    #      kabin EN ÜSTTE  →  tam tersi.
    #
    #  Kitap bunu dört yük durumunun ÜÇÜNDE ters yazıyordu:  kabin en altta
    #  iken halat kütlesinin tamamını KARŞI AĞIRLIK tarafına koyuyordu.  Oysa
    #  "kabin en alt durakta" durumu tam da halat kütlesi kabin tarafında
    #  olduğu için EN OLUMSUZ durumdur — standart T1/T2'yi "for the worst case
    #  depending on the position of the car in the well" değerlendirmeyi ister
    #  ve kitabın kendi bölüm 1 açıklaması da bunu söylüyordu.
    #  Yön EMNİYETSİZDİ:  T1 küçük çıkıyor, tahrik yeteneği olduğundan iyi
    #  görünüyordu ( 20 duraklı bir tesiste 1,23 yerine 1,79 ).
    uzun_car = (0.5 * H + ycar) * nh * gh     # kabin EN ALTTA  →  halat kabinde
    kisa_car = (0.5 * H - ycar) * nh * gh     # kabin EN ÜSTTE  ( ycar = H/2 → 0 )
    uzun_cwt = (0.5 * H + ycwt) * nh * gh     # ağırlık EN ALTTA ( kabin üstte )
    kisa_cwt = (0.5 * H - ycwt) * nh * gh
    #  ------------------------------------------------------------------
    #  DENGE ZİNCİRİ  MCRcar / MCRcwt        EN 81-50 m.5.11.2
    #  ------------------------------------------------------------------
    #  Terimler _T1 / _T2'de ZATEN vardı ama hiçbir yerde atanmıyordu:  tahrik
    #  hesabı zincirden habersizdi.  Zincir kabin altından kuyu dibine sarkıp
    #  karşı ağırlığa çıkar;  dağılımı HALATIN TAM TERSİDİR:
    #      kabin EN ALTTA  →  zincir kabin tarafında KISA ( kabin kuyu dibinde ),
    #                          karşı ağırlık tarafında UZUN
    #      kabin EN ÜSTTE  →  tam tersi
    #  Toplamı her konumda sabittir ve motor bölümündeki MCR'ye eşittir.
    #  ( λ ve MCR bölüm 1'den okunur — tek kaynak.  Bölüm 1 her zaman önce
    #    çalışır;  motor tek başına çağrılırsa zincirsiz duruma düşülür. )
    mu_zincir = (o.get("lam") or 0.0) * r * gh * nh    # zincirin metre kütlesi
    zincir_uzun = (0.5 * H + ycar) * mu_zincir         # = H · mu  = MCR
    zincir_kisa = (0.5 * H - ycar) * mu_zincir         # = 0
    #  MTrav:  gezici kablonun indirgenmiş kütlesi
    trav = (0.25 * H + 0.5 * ycar) * w_kablo

    if durum == "yukleme":                    # sütun M — %125 yüklü kabin EN ALTTA
        t["Q"] = 1.25 * Q
        t["MSRcar"], t["MSRcwt"] = uzun_car, kisa_cwt
        t["MCRcar"], t["MCRcwt"] = zincir_kisa, zincir_uzun
    elif durum == "fren_alt":                 # sütun P — %100 yüklü kabin EN ALTTA
        t["Q"] = Q
        t["a"] = a_in
        t["MSRcar"], t["MSRcwt"] = uzun_car, kisa_cwt
        t["MCRcar"], t["MCRcwt"] = zincir_kisa, zincir_uzun
    elif durum == "fren_ust":                 # sütun Q — boş kabin EN ÜSTTE
        t["a"] = a_in
        t["MSRcar"], t["MSRcwt"] = kisa_car, uzun_cwt
        t["MCRcar"], t["MCRcwt"] = zincir_uzun, zincir_kisa
        t["MTrav"] = trav
    elif durum == "bloke":                    # sütun O — boş kabin EN ÜSTTE
        t["Mcwt"] = 0.0
        #  Kitabın DOĞRU yazdığı tek durum budur ( Askı Tipleri!O119 / O120 ):
        #  kabin üstte, halat kütlesi karşı ağırlık tarafında.  O120 bunu
        #  "ns × H × gh" diye yazar;  ( 0,5·H + H/2 )·ns·gh ile birebir aynıdır.
        t["MSRcar"], t["MSRcwt"] = kisa_car, uzun_cwt
        t["MCRcar"], t["MCRcwt"] = zincir_uzun, zincir_kisa
        t["MTrav"] = trav
    return t


def _kasnak_atalet(g, O):
    """Saptırma kasnaklarının indirgenmiş kütlesi  mP = J / R²   [ kg ].

    TS EN 81-50 m.5.11.2.2 a) tahrik kuvvetlerine kasnak ataletini de katar:

        Σ( mPcar · iPcar · a ) / r          mPcar = J · ( v_kasnak / v )² / R²

    J bir BİLEŞEN ÖZELLİĞİDİR ve standart onu imalatçıdan bekler.  Sahada
    kimse kasnağın atalet momentini veri sayfasından okuyup girmez;  bu
    yüzden kasnak, ÇAPI VE HALAT DÜZENİ BİLİNEN bir döküm disk olarak
    modellenir  ( dört sayı da ofis kabulüdür, bkz. sabitler.py ):

        J  = ½·π·ρ·A·( R⁴ − R₁⁴ )  +  ½·π·ρ·A₁·R₁⁴
        R  = Dp / 2                          Dp : ortalama saptırma çapı
        R₁ = ( Dp − göbek payı ) / 2
        A  = ( ns − 1 )·1,6·dr + kanal payı  ns · dr : halat sayısı ve çapı
        A₁ = A × göbek oranı

    2:1 askıda kasnağın çevresel hızı kabin hızına eşittir, yani
    ( v_kasnak / v ) = 1 ve mP = J / R² olur.

    DOĞRULAMA:  ELEport'un yayımlanmış örnek paftasında Dp = 294 mm ve
    7 × 6,5 mm halat için J = 0,29 kg·m² yazar;  bu bağıntı 0,2920 verir.
    """
    Dp = g.get("saptirma_kasnak_capi")
    ns, dr = g.get("halat_adedi"), g.get("halat_capi")
    if not (Dp and ns and dr) or Dp <= O["kasnak_gobek_pay"]:
        return 0.0, 0.0, 0.0
    R = (Dp / 2.0) / 1000.0
    R1 = ((Dp - O["kasnak_gobek_pay"]) / 2.0) / 1000.0
    A = ((ns - 1) * 1.6 * dr + O["kasnak_kanal_payi"]) / 1000.0
    A1 = A * O["kasnak_gobek_orani"]
    rho = O["kasnak_yogunluk"]
    J = (0.5 * math.pi * rho * A * (R ** 4 - R1 ** 4)
         + 0.5 * math.pi * rho * A1 * R1 ** 4)
    return (J / (R ** 2)) if R else 0.0, J, A


def _T1(t, FRcar, s):
    """Kabin tarafındaki halat kuvveti  T1  ( EN 81-50 m.5.11.2.2 a ).

        T1 = ( P + Q + MCRcar + MTrav ) / r · ( gn ± a )
             + MComp / ( 2·r ) · gn
             + MSRcar · ( gn ± a · ( r² + 2 ) / 3 )
             ± ( iPTD · mPTD / ( 2·r ) ) · a
             ± ( mDP · a ) / r
             ∓ FRcar / r

    ``s`` İŞLEMİ seçer:  +1 ÜST işlem  ( beyan yüklü kabin AŞAĞI yönde
    yavaşlıyor ), −1 ALT işlem  ( boş kabin YUKARI yönde yavaşlıyor ).
    Yükleme ve bloke durumlarında a = 0'dır, işlem fark etmez.
    """
    r, gn, a = t["r"], t["gn"], t["a"]
    return ((t["P"] + t["Q"] + t["MCRcar"] + t["MTrav"]) * (gn + s * a) / r
            + t["MComp"] / (2.0 * r) * gn
            + t["MSRcar"] * (gn + s * a * (r * r + 2) / 3.0)
            + s * (t["iPDT"] * t["mPTD"] * a) / (2.0 * r)
            + s * t["mDP"] * a / r
            #  Σ( mPcar · iPcar · a ) / r   —  askı kasnaklarının ataleti
            #  ( m.5.11.2.2, koşul III:  yalnız askı oranı > 1 iken )
            + s * (t["mPcar"] * t["iPcar"] * a) / r
            - s * FRcar / r)


def _T2(t, FRcwt, s):
    """Karşı ağırlık tarafındaki halat kuvveti  T2  —  işaretler T1'in TERSİ.

        T2 = ( Mcwt + MCRcwt ) / r · ( gn ∓ a )  +  MComp / ( 2·r ) · gn
             + MSRcwt · ( gn ∓ a · ( r² + 2 ) / 3 )
             ∓ ( iPTD · mPTD / ( 2·r ) ) · a  ∓ ( mDP · a ) / r  ± FRcwt / r
    """
    r, gn, a = t["r"], t["gn"], t["a"]
    return ((t["Mcwt"] + t["MCRcwt"]) * (gn - s * a) / r
            + t["MComp"] * gn / (2.0 * r)
            + t["MSRcwt"] * (gn - s * a * (r * r + 2) / 3.0)
            - s * (t["iPDT"] * t["mPTD"] * a) / (2.0 * r)
            - s * t["mDP"] * a / r
            - s * (t["mPcwt"] * t["iPcwt"] * a) / r
            + s * FRcwt / r)


#  YÜK DURUMU  →  m.5.11.2.2'nin HANGİ İŞLEMİ
#
#  Maddenin kendi cümlesi:  "the upper operation is applicable in case the
#  car with its rated load is retarding in the DOWN direction and the lower
#  operation in case the empty car is retarding in the UP direction.  For
#  the cases car loading and stalled condition a = 0."
#
#  Ek D'nin çözümlü örneği ( 2:1, dengeleme yok ) bunu sayıya döker:
#      a) yüklü kabin en alt durakta :  T1 = (P+Q)/2·( gn + a ) …  − FRcar/2
#                                       T2 = Mcwt/2·( gn − a ) …  + FRcwt/2
#      b) boş kabin  en üst durakta  :  işaretlerin tamamı ters.
#
#  ESKİDEN İŞARETLER TERSTİ.  Excel'in 11!D235…AF283 satırlarından birebir
#  alınmış beş elemanlı işaret demetleri vardı ve yüklü kabin aşağı
#  yavaşlarken kabin tarafına ( gn − a ), ağırlık tarafına ( gn + a )
#  veriyordu — tam tersi.  T1/T2 oranı %36 KÜÇÜK çıkıyor, yani tahrik
#  yeteneği kontrolü olduğundan kolay geçiliyordu.  EMNİYETSİZ taraf.
#  ( ELEport'un paftası da Ek D ile aynı işaretleri yazar. )
ISLEM = {"yukleme": +1, "fren_alt": +1, "fren_ust": -1, "bloke": +1}


def _tahrik(g, o):
    S, O = SABIT, o["ofis"]
    Ra = g["halat_arasi"]
    C, D = g["sap_kasnak_yuk"], g["makine_yatak_yuk"]
    R1 = g["tahrik_kasnak_capi"] / 2.0
    H = g["sase_yuksekligi"]
    v = o["v"]

    #  ------------------------------------------------------------------
    #  SARILMA AÇISI  α          TEK SARIMLI TAHRİK KASNAĞI MODELİ
    #  ------------------------------------------------------------------
    #  α = 180° − arctan( ( Ra − 2·R1 ) / B ).  Halat kasnağın iki yanından
    #  teğet iner;  iki iniş kolu birbirinden uzaklaştıkça ( Ra büyüdükçe )
    #  α küçülür ve EN ÇOK 180° olur.  Ra < 2·R1 girildiğinde pay negatife
    #  düşüyor ve α 180°'yi aşıyordu ( Ra = 100 mm → 187,65° ) — fiziksel
    #  olarak imkânsız bir geometri sessizce hesaplanıyordu.  Yön
    #  EMNİYETSİZDİR:  e^(f·α) sınırı α ile büyür, tahrik yeteneği olduğundan
    #  iyi çıkar.  Girdi doğrulaması bu geometriyi zaten reddediyor;  aşağısı
    #  ikinci kalkandır ( bkz. bölüm 2'deki negatif gerilme kalkanı ).
    A_yatay = Ra - 2 * R1
    B_dusey = H - C + D
    theta = math.atan2(A_yatay, B_dusey)
    alfa_derece = 180 - math.degrees(theta)
    alfa = math.radians(alfa_derece)
    alfa_uygun = 0 < alfa_derece <= 180

    #  Sürtünme katsayısı kabulleri  ( EN 81-50 m.5.11.2.3.2 )
    #  Acil frenlemedeki μ HALAT hızına bağlıdır;  palangalı sistemde halat
    #  kabinden askı oranı katı hızlı gider.  ( Kaynak Excel kabin hızını
    #  koyar — bkz. EXCEL_FARKLARI. )
    v_halat = v * o["r"]
    mu_yuk = S["mu_yukleme"]
    mu_fren = S["mu_yukleme"] / (1 + v_halat / 10.0)
    mu_bloke = S["mu_bloke"]
    #  SÜRTÜNME ÇARPANI f  —  KANAL ŞEKLİNE GÖRE AYRI MADDE.
    #  Kaynak kitap şekilden bağımsız olarak hep V kanal bağıntısını
    #  kullanıyordu;  yarım daire kanal seçilebildiği hâlde onun maddesi
    #  ( m.5.11.2.3.1.1 ) hiç uygulanmıyordu — f olduğundan BÜYÜK, yani
    #  tahrik yeteneği olduğundan iyi çıkıyordu.  ( bkz. EXCEL_FARKLARI )
    sekil = g["kanal_sekli"]
    yarim_daire = MT.kanal_yarim_daire_mi(sekil)
    #  Alt kesilme yoksa β = 0;  düz yarım daire kanalın alt kesilmesi yoktur.
    #  Açılar bölüm 4 ile AYNI kaynaktan okunur ( MT.kanal_acisi / kanal_beta ) —
    #  pafta ile hesap ayrışmasın diye.
    beta_derece = MT.kanal_beta(sekil, O["kanal_beta"])
    gama_derece = MT.kanal_acisi(sekil, O["kanal_gama_v"], O["kanal_gama_yd"])
    beta = math.radians(beta_derece)
    gama = math.radians(gama_derece)
    sert = g["kanal_isleme"] == "Sertleştirilmiş"

    def _f(mu):
        """TS EN 81-50 m.5.11.2.3.1.1 ( yarım daire ) / m.5.11.2.3.1.2 ( V )."""
        if yarim_daire:
            pay = 4 * (math.cos(gama / 2.0) - math.sin(beta / 2.0))
            payda = (math.pi - beta - gama - math.sin(beta) + math.sin(gama))
            return mu * pay / payda
        if sert:
            return mu / math.sin(gama / 2.0)
        return mu * 4 * (1 - math.sin(beta / 2.0)) / (math.pi - beta - math.sin(beta))

    f_yuk, f_fren = _f(mu_yuk), _f(mu_fren)
    #  Ağırlık bloke durumu:  V kanalda m.5.11.2.3.1.2 sertleştirilmiş olsun
    #  olmasın μ/sin(γ/2) der;  yarım dairede ayrı bir kural yoktur, aynı
    #  bağıntı μ = 0,2 ile kullanılır.
    f_bloke = (_f(mu_bloke) if yarim_daire else mu_bloke / math.sin(gama / 2.0))

    _kay(o, U174=A_yatay, Z178=B_dusey, C184=math.degrees(theta),
         S184=alfa_derece, AA184=alfa, AS190=mu_fren, AE216=f_bloke)
    #  Excel her iki kanal işlemesinin f değerini de ayrı satırda tutar
    _kay(o, **{("AJ198" if sert else "AU206"): f_yuk,
               ("AL202" if sert else "AV211"): f_fren})

    b = Bolum("TAHRİK YETENEĞİNİN HESAPLANMASI", kimlik="tahrik_yetenegi",
              kaynak="TS EN 81-50 m.5.11.2  /  m.5.11.3")
    #  m.5.11.2.3.1.2:  "Where the groove has not been submitted to an
    #  additional hardening process, in order to limit the deterioration of
    #  traction due to wear, an undercut is necessary."  Yani sertleştirilmemiş
    #  V kanalın ALT KESİLMESİ OLMALIDIR;  bu birleşim standardın dışındadır.
    if (not yarim_daire) and (not sert) and not MT.kanal_alti_kesik_mi(sekil):
        b["notlar"] = [
            "STANDART DIŞI BİRLEŞİM:  TS EN 81-50 m.5.11.2.3.1.2, "
            "sertleştirilmemiş kanalda aşınmadan doğan tahrik kaybını "
            "sınırlamak için ALT KESİLMENİN GEREKLİ olduğunu söyler.  "
            f"Seçilen '{sekil}' + '{g['kanal_isleme']}' birleşiminde alt "
            "kesilme yoktur;  hesap β = 0 ile ( emniyetli tarafta ) "
            "yapılmıştır ama kanal ya sertleştirilmeli ya da altı kesik "
            "seçilmelidir."]
    b["adimlar"] = [
        veri("Ra", "Halat arası ( ray merkezleri arası mesafe )", Ra, "mm",
             "GİRİŞ  ( " + g["agirlik_yeri"] + " ağırlık )"),
        veri("C", "Saptırma kasnağı milinin yerden yüksekliği", C, "mm", "GİRİŞ"),
        veri("D", "Tahrik kasnağı mili yatak yüksekliği", D, "mm", "GİRİŞ"),
        veri("R1", "Tahrik kasnağı yarıçapı", R1, "mm"),
        veri("H", "Makine şasesi yüksekliği", H, "mm", "GİRİŞ"),
        hesap("A = Ra − 2 × R1", f"{trn(Ra, 0)} − 2 × {trn(R1, 0)}", A_yatay, "mm"),
        hesap("B = H − C + D",
              f"{trn(H, 0)} − {trn(C, 0)} + {trn(D, 0)}", B_dusey, "mm"),
        hesap("θ = arctan( A / B )",
              f"arctan( {trn(A_yatay, 0)} / {trn(B_dusey, 0)} )",
              math.degrees(theta), "°"),
        hesap("α = 180° − θ", f"180 − {tr(math.degrees(theta))}", alfa_derece, "°"),
        kontrol(f"α = {tr(alfa_derece)}°  —  tek sarımlı kasnakta 0° < α ≤ 180°",
                alfa_uygun),
        metin("Sürtünme katsayısı μ kabulleri  ( TS EN 81-50 Şekil 8 ) :"),
        veri("μ", "Yükleme için", mu_yuk, "", "EN 81-50 Şekil 8"),
        veri("v halat", "Halat hızı  ( kabin hızı × askı oranı )", v_halat, "m/s"),
        hesap("μ = 0,1 / ( 1 + v_halat / 10 )",
              f"0,1 / ( 1 + {tr(v_halat)} / 10 )", mu_fren, "",
              "EN 81-50 m.5.11.2.3.2"),
        veri("μ", "Kabinin bloke edildiği durumlar için", mu_bloke, "",
             "EN 81-50 Şekil 8"),
        metin(f"Sürtünme faktörü f  —  kanal işleme : {g['kanal_isleme']} :"),
        veri("γ", "Kanal açısı", gama_derece, "°", "OFİS STANDARDI", 0),
        veri("β", "Alt kesilme açısı", beta_derece, "°",
             "OFİS STANDARDI" if MT.kanal_alti_kesik_mi(sekil)
             else "alt kesilme yok", 0),
        veri("f", "Kabinin yüklenmesi", f_yuk, "", "EN 81-50 m.5.11.2.3", 4),
        veri("f", "Durdurma tertibatının çalışması", f_fren, "",
             "EN 81-50 m.5.11.2.3", 4),
        veri("f", "Kabinin bloke edilmesi", f_bloke, "", "EN 81-50 m.5.11.2.3", 4),
    ]

    #  ── ASKI KASNAKLARININ ATALETİ  ( m.5.11.2.2, koşul III ) ────────
    #  Paftada GÖRÜNÜR:  terim ofis kabulleriyle modellenen bir kasnaktan
    #  çıkıyor, okuyan mühendis nereden geldiğini görebilmeli.
    _mP, _J, _A = _kasnak_atalet(g, O)
    if o["r"] > 1 and _mP:
        b["adimlar"] += [
            metin("Askı kasnaklarının ataleti  ( m.5.11.2.2 · koşul III ) :",
                  vurgu=True),
            veri("Dp", "Saptırma kasnaklarının ortalama çapı",
                 g["saptirma_kasnak_capi"], "mm", "GİRİŞ", 0),
            hesap("A = ( ns − 1 ) × 1,6 × dr + pay",
                  f"( {trn(g['halat_adedi'], 0)} − 1 ) × 1,6 × {tr(g['halat_capi'])}"
                  f" + {trn(O['kasnak_kanal_payi'], 0)}", _A * 1000, "mm",
                  "OFİS KABULÜ  ·  kasnak genişliği", 0),
            hesap("J = ½·π·ρ·A·( R⁴ − R₁⁴ ) + ½·π·ρ·A₁·R₁⁴",
                  f"ρ = {trn(O['kasnak_yogunluk'], 0)} kg/m³  ·  "
                  f"göbek payı {trn(O['kasnak_gobek_pay'], 0)} mm",
                  _J, "kg·m²", "OFİS KABULÜ  ·  döküm disk modeli", 4),
            hesap("mP = J / R²", f"{tr(_J)} / ( {tr(g['saptirma_kasnak_capi'] / 2000)} )²",
                  _mP, "kg"),
            veri("iPcar", "Kabin tarafındaki kasnak sayısı",
                 O["kasnak_adet_kabin"], "adet", "OFİS KABULÜ", 0),
            veri("iPcwt", "Ağırlık tarafındaki kasnak sayısı",
                 O["kasnak_adet_agirlik"], "adet", "OFİS KABULÜ", 0),
        ]

    #  Her yük durumunun Excel'deki T1 · T2 · oran · sınır hücreleri
    DURUM_HUCRE = {
        "yukleme":  ("AF235", "AJ240", "K242", "O242"),
        "fren_alt": ("AF250", "AJ255", "K257", "O257"),
        "fren_ust": ("AH264", "AF269", "K271", "O271"),
        "bloke":    ("AH278", "AF283", "K285", "O285"),
    }
    tumu_uygun = alfa_uygun
    for durum, baslik in YUK_DURUMLARI:
        t = _terimler(g, o, durum)
        isl = ISLEM[durum]
        #  SÜRTÜNME DİRENCİ, KENDİ TARAFININ KUVVETİNDEN TÜREMELİDİR.
        #  FRcar kabin tarafındaki, FRcwt ağırlık tarafındaki dirençtir;
        #  ikisi de o taraftaki sürtünmesiz halat kuvvetinin bir yüzdesidir
        #  ( ELEport da öyle yazar:  FRcar = (Q+P)·(gn+a)·%2 ).  Eskiden bunun
        #  için AYRI bir işaret tablosu vardı ( FR_ISARET ) ve T1/T2'nin
        #  kendi işaretlerinden farklı yönde kuvvet üretiyordu;  artık aynı
        #  işlemle, yalnız sürtünmesiz hâlden ( FR = 0 ) türetilir.
        #  a = 0 olan durumlarda ( yükleme · bloke ) sürtünme hesaba
        #  katılmaz:  m.5.11.2.2 sürtünmeyi yalnız frenlemede tanımlar ve
        #  "en az bir sürtünme kuvveti garanti edilemiyorsa silinmelidir"
        #  der — statik durumlarda garanti edilemez.
        if durum in ("fren_alt", "fren_ust"):
            FRcar = S["FRcar_katsayi"] * _T1(t, 0.0, isl)
            FRcwt = S["FRcwt_katsayi"] * _T2(t, 0.0, isl)
        else:
            FRcar = FRcwt = 0.0
        T1 = _T1(t, FRcar, isl)
        T2 = _T2(t, FRcwt, isl)
        #  HALAT KUVVETİ SIFIRIN ALTINA İNEMEZ.  T ≤ 0, halatın gevşemesi
        #  demektir;  o noktada tahrik modeli ( T1/T2 ≤ e^(f·α) ) geçersizdir,
        #  çünkü sürtünme bağıntısı GERGİN halat varsayar.
        #  Oran max(a/b, b/a) olduğu için negatif bir kuvvet oranı da NEGATİF
        #  yapıyor ve "oran ≤ sınır" karşılaştırması sessizce GEÇİYORDU:
        #  a = 1 gn'de T2 = −48,8 N çıkıp bölüm "UYGUNDUR" diyordu.
        #  Eskiden T tam sıfıra denk geldiği için _oran None döner ve durum
        #  tesadüfen yakalanırdı;  kasnak atalet terimi eklenince sıfırı
        #  geçip negatife düştü ve tesadüf bozuldu.
        gergin = T1 > 0 and T2 > 0
        if durum == "bloke":
            oran = T1 / T2 if T2 else None
            f_kul = f_bloke
            sinir = math.exp(f_kul * alfa)
            uygun = gergin and oran is not None and sinir <= oran
            metni = (f"e^(f·α) = {tr(sinir)}  ≤  T1/T2 = {tr(oran)}" if gergin
                     else "HALAT GEVŞİYOR — T1 ya da T2 sıfırın altına iniyor, "
                          "tahrik bağıntısı bu noktada geçerli değildir")
        else:
            oran = _oran(T1, T2)
            f_kul = f_yuk if durum == "yukleme" else f_fren
            sinir = math.exp(f_kul * alfa)
            uygun = gergin and oran is not None and sinir >= oran
            metni = (f"T1/T2 = {tr(oran)}  ≤  e^(f·α) = {tr(sinir)}" if gergin
                     else "HALAT GEVŞİYOR — T1 ya da T2 sıfırın altına iniyor, "
                          "tahrik bağıntısı bu noktada geçerli değildir")
        tumu_uygun = tumu_uygun and uygun
        h1, h2, h3, h4 = DURUM_HUCRE[durum]
        _kay(o, **{h1: T1, h2: T2, h3: oran, h4: sinir})
        b["adimlar"] += [
            metin(baslik + " :", vurgu=True),
            hesap("T1  ( kabin tarafı )", "EN 81-50 m.5.11.2", T1, "N"),
            hesap("T2  ( karşı ağırlık tarafı )", "EN 81-50 m.5.11.2", T2, "N"),
            hesap("T1 / T2", f"{tr(T1)} / {tr(T2)}"
                  if durum == "bloke" else "büyük / küçük", oran, "", ondalik=4),
            hesap("e^(f·α)", f"exp( {tr(f_kul)} × {tr(alfa_derece)}° )", sinir,
                  "", "EN 81-50 m.5.11.3", 4),
            kontrol(metni, uygun),
        ]

    b["sonuc"] = {"baslik": "KONTROL      dört yük durumunda tahrik yeteneği",
                  "metin": "UYGUNDUR." if tumu_uygun else
                           ("UYGUN DEĞİLDİR — sarılma açısı α tek sarımlı kasnakta "
                            "imkânsız ( halat arası ile kasnak çapını denetleyin )"
                            if not alfa_uygun else "UYGUN DEĞİLDİR"),
                  "uygun": bool(tumu_uygun)}
    if (MT.kanal_gecis_sayisi(sekil) or 1) > 1:
        b["notlar"] = (b.get("notlar") or []) + [
            "ÇİFT SARIM SEÇİLDİ.  Sarılma açısı yukarıdaki bağıntıyla TEK "
            "SARIM için hesaplanır ( α ≤ 180° );  çift sarımda halat kasnağı "
            "iki kez dolanır ve gerçek α bunun yaklaşık iki katıdır.  Hesap bu "
            "yüzden tahrik yeteneğini OLDUĞUNDAN KÖTÜ gösterir — emniyetli "
            "taraftadır, ama gerçek α saptırma düzenine göre ayrıca "
            "belirlenmelidir.  ( Nequiv(t) çift sarımda iki geçişle hesaba "
            "girer;  bkz. bölüm 4. )"]
    return b


# =====================================================================
#  RAY HESABI ORTAK YARDIMCILARI
# =====================================================================
def _ray_tutarsizlik_notu(profil):
    """Seçilen ray profilinin tablo değerleri kendi içinde tutarlı mı.

    i = √(I/A) tanım gereğidir;  kaynak kitabın kendi 60. satırı da bunu
    formülle hesaplar.  Tutmayan bir satır seçildiğinde projeci bunu
    BİLMELİDİR — sayı emniyetli tarafta olsa bile.
    """
    if profil not in MT.RAY_TUTARSIZ:
        return None
    for ad, eksen, tablo, hesap in MT.ray_tutarsizliklari():
        if ad == profil:
            return (f"RAY TABLOSU TUTARSIZ:  {profil} profilinde {eksen} = "
                    f"{tr(tablo)} yazılı, ama aynı satırdaki I ve A "
                    f"{eksen} = {tr(hesap)} veriyor ( √(I/A) ).  Tablodaki "
                    "küçük değer narinliği büyük gösterir, yani burkulma "
                    "EMNİYETLİ tarafta hesaplanır;  yine de doğrusu ISO 7465 "
                    "ya da ray imalatçısının veri sayfasından teyit "
                    "edilmelidir.")
    return None


def _ray_ozellik(profil):
    """Bir ray profilinin hesaba giren bütün kesit değerleri."""
    d = {k: MT.ray(profil, k)
         for k in ("A", "Ix", "Iy", "Wx", "Wy", "ix", "iy", "c")}
    #  BURKULMA NARİNLİĞİ EN KÜÇÜK ATALET YARIÇAPINDAN ÇIKAR.
    #  m.5.10.3 sembol listesi:  "i is the MINIMUM radius of gyration".
    #  Kolon hangi eksende zayıfsa orada burkulur;  ray konsolları iki yönde
    #  de aynı aralıkta bağladığı için seçici olan kesitin kendisidir.
    d["imin"] = min(d["ix"], d["iy"])
    d["h1_b_f"] = MT.ray_geo(profil, "h1_b_f")
    d["h1_f"] = MT.ray_geo(profil, "h1_f")
    d["b"] = MT.ray_geo(profil, "b")        # paten balatası yarı genişliği
    return d


def _moment(F, l):
    """Eğilme momenti  M = 3 · F · l / 16   ( iki açıklıklı sürekli kiriş )."""
    return SABIT["moment_pay"] * F * l / SABIT["moment_bolen"]


def _flans(F, p, balata, makarali=False):
    """Flanş eğilme gerilmesi  —  TS EN 81-50 m.5.10.5 / Ek C.2.1.4.

    Madde İKİ formül verir ve hangisinin geçerli olduğunu PATEN TİPİ söyler:

        makaralı paten :  σF = 1,85 · Fx / c²
        kaymalı  paten :  σF = 6 · Fx · ( h1 − b − f ) / ( c² · ( ℓ + 2·( h1 − f ) ) )

    ℓ, maddenin kendi sembol listesinde "the length of the guide shoe
    lining" — paten balatasının UZUNLUĞUDUR.  Kaynak Excel oraya 1 yazar
    ( ℓ harfi 1 rakamı okunmuş görünüyor ) ve yalnız kaymalı formülü tanır.
    """
    if makarali:
        return 1.85 * F / p["c"] ** 2
    return F * (p["h1_b_f"] * 6) / (p["c"] ** 2 * (balata + 2 * p["h1_f"]))


def _balata_boyu(g, p):
    """Paten balata uzunluğu ℓ  ( mm ).

    Girilmemişse ray tablosundaki balata YARI genişliğinden türetilir:
    ℓ = 2·b, yani kare balata kabulü.  Balatalar genelde genişliğinden
    uzundur;  kare kabulü ℓ'yi küçük tutar ve σF'yi EMNİYETLİ tarafta
    ( büyük ) bırakır.  Kesin değer paten imalatçısından alınmalıdır.
    """
    d = g.get("paten_balata_boyu")
    if isinstance(d, (int, float)) and not isinstance(d, bool) and d > 0:
        return d, "GİRİŞ"
    return 2 * p["b"], "türetilen  ( 2 × balata yarı genişliği )"


def _sehim(F, l, I):
    """Sehim  δ = 0,7 · l³ · F / ( 48 · E · I )."""
    S = SABIT
    return S["sehim_katsayi"] * l ** 3 * F / (S["sehim_bolen"] * S["E"] * I)


def _burkulma_omega(l, imin, rm):
    """Narinlik ve ω  —  TS EN 81-50 m.5.10.3.

    ``imin`` EN KÜÇÜK atalet yarıçapıdır.  Madde sembol listesinde
    "i is the MINIMUM radius of gyration" der;  kaynak Excel oraya ix
    sütununu okuyordu ( VLOOKUP … TABLOLAR!I60:S65 ; 8 ; 0 ).  Kataloğun
    altı profilinden beşinde iy < ix olduğu için bu λ'yı KÜÇÜK, ω'yı da
    küçük gösteriyordu — burkulma gerilmesi olduğundan düşük çıkıyordu
    ( 70 x 65 x 9'da ω %123 eksik ).  Bkz. EXCEL_FARKLARI.

    ω RAY ÇELİĞİNİN çekme dayanımına da bağlıdır;  kaynak Excel'in tek
    tablosu yalnız Rm = 370 eğrisidir ( bkz. EXCEL_FARKLARI ).

    λ ALT SINIRDA KIRPILIR.  ω tablosu 20 ≤ λ ≤ 250 arasında tanımlıdır;
    λ < 20 burkulmanın belirleyici olmadığı bölgedir ve tablonun ilk satırı
    kullanılır ( makine kaidesi hesabı da öyle yapar ).  ÜST sınırın
    dışında ω yoktur:  bu durumda None döner ve bölüm "burkulma hesabı
    yapılamadı" der — girdi doğrulaması bu geometriyi zaten reddeder,
    burası ikinci kalkandır.  Eskiden None doğrudan çarpıma giriyor ve
    motor ham bir TypeError ile çöküyordu.
    """
    lam = max(MT.OMEGA_LAMBDA_MIN, math.ceil(l / imin - 1e-9))
    return lam, MT.omega_en8150(lam, rm)


def _yuk_merkezi(merkez, sapma, Q, P, p_kolu, askı=0.0):
    """Yükün EN OLUMSUZ konumu  —  TS EN 81-20 m.5.7.2.3.4.

    Madde normatiftir:  "the rated load Q of the car shall be evenly
    distributed over those three quarters of the car area being in the MOST
    UNFAVOURABLE POSITION".  Kabin alanının 3/4'ü yüklenince yükün ağırlık
    merkezi kabin merkezinden  Dx/2 − 3·Dx/8 = Dx/8  kadar kayar;  Ek C'nin
    "xQ = xC + Dx/8" satırı bunun bir ÖRNEĞİDİR ( Ek C bilgilendiricidir ) ve
    kaymayı tek yönde gösterir.

    Yön SEÇİLMELİDİR.  Ek C.2.1.1'in payı  Q·xQ + P·xp  bir moment
    toplamıdır;  kabin merkezi ray ekseninin öbür yanındaysa ( xc < 0 ) boş
    kabinin momenti negatiftir ve yükü inatla + yönde kaydırmak onu
    DENGELER:  toplam moment küçülür, ray gerilmesi olduğundan küçük çıkar,
    program "UYGUNDUR" der.  Oysa yolcular öbür yana yığılırsa ray
    hesaplanandan büyük yük görür — emniyetsiz taraf.

    Bu yüzden ± iki konum da denenir ve momentin BÜYÜKLÜĞÜNÜ büyüteni
    seçilir.  Simetrik yerleşimde ( xc = 0 ) iki yön aynı sonucu verir.
    """
    sabit = P * (p_kolu - askı)
    arti, eksi = merkez + sapma, merkez - sapma
    return (arti if abs(Q * (arti - askı) + sabit) >= abs(Q * (eksi - askı) + sabit)
            else eksi)


def _ray_satirlari(eksen, kuvvet, F, l, W, I, adimlar, dstr=0.0):
    """Bir kuvvet için moment · gerilme satırlarını yazar, ( σ , δ ) döndürür.

    ADLANDIRMA TS EN 81-50 Ek C.2.1.1'İN KENDİSİDİR:

        Fx  →  My = 3·Fx·l/16  →  σy = My/Wy
        Fy  →  Mx = 3·Fy·l/16  →  σx = Mx/Wx

    Yani x yönündeki kuvvet rayı Y EKSENİ etrafında eğer.  Kaynak kitap bu
    ikisini ters adlandırıyordu ( Fx'ten gelen momente "Mx" diyordu ) — sayı
    doğruydu, ad yanlıştı.  Paftayı standartla karşılaştıran bir denetçi için
    bu, olmayan bir hata gibi görünüyordu.
    """
    M = _moment(F, l)
    #  GERİLME VE SEHİM BİRER BÜYÜKLÜKTÜR.
    #  Fx / Fy işaretlidir ve işaret YÖNÜ gösterir:  kabin merkezi ray
    #  ekseninin öbür yanındaysa ( xc < 0 ) kuvvet de moment de negatife
    #  düşer.  Ama rayın gördüğü gerilme ile yaptığı sehim, yönden bağımsız
    #  büyüklüklerdir;  "δ ≤ 5 mm" karşılaştırması işaretli yapılırsa
    #  −5,59 mm SESSİZCE geçer ( sınır 5 mm olmasına rağmen ).
    #  Kuvvet ve moment satırları işaretini korur — yön bilgisi paftada
    #  kalsın diye;  σ ve δ büyüklük olarak yazılır ve karşılaştırılır.
    sigma = abs(M) / W
    #  Ek C.2.1.5 / C.2.2.5 / C.2.3.5:  δ = 0,7·F·l³/(48·E·I) + δstr.
    #  δstr BİNANIN kendi sehimidir ve rayın sehimine EKLENİR;  kaynak
    #  kitapta hiç yoktu.  Varsayılan 0 — değeri yapı hesabından gelir.
    d = abs(_sehim(F, l, I)) + (dstr or 0.0)
    adimlar.extend([
        hesap(f"M{eksen} = 3 × F{kuvvet} × l / 16",
              f"3 × {tr(F)} × {trn(l, 0)} / 16", M, "N·mm", ondalik=0),
        hesap(f"σ{eksen} = | M{eksen} | / W{eksen}",
              f"| {trn(M, 0)} | / {trn(W, 0)}", sigma, "N/mm²"),
    ])
    return sigma, d


# =====================================================================
#  7 -  KABİN KILAVUZ RAYLARI     ( TS EN 81-50 m.C.2.1 / C.2.2 / C.2.3 )
# =====================================================================
def _kabin_raylari(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    Q, P = o["Q"], o["P"]
    k1, k2, k3 = o["k1"], S["k2"], O["k3_yardimci"]
    Fp = g["klips_itme_kuvveti"] or 0.0
    dstr_x, dstr_y = g["yapi_sehim_x"] or 0.0, g["yapi_sehim_y"] or 0.0
    makarali = g["paten_tipi"] == "Makaralı"
    prof = g["kabin_ray_profili"]
    p = _ray_ozellik(prof)
    n, h, l = g["kabin_ray_sayisi"], g["kabin_paten_arasi"], g["kabin_konsol_arasi"]
    W, D = g["kabin_genisligi"], g["kabin_derinligi"]

    ray_boyu = MG.toplam_ray_boyu(g)
    Mg = ray_boyu * MT.ray(prof, "Gr")
    MY = S["MY_kabin"]
    sperm_g = MT.sigma_perm_guvenlik(g["ray_celigi_rm"])
    sperm_n = MT.sigma_perm_normal(g["ray_celigi_rm"])
    dperm = S["dperm_kabin"]

    xc = (D / 2.0 + S["kabin_merkez_payi"]) - g["ray_kapi_arasi"]
    #  KABİN MERKEZİNİN y KAÇIKLIĞI HESABA GİRER.
    #  Ek C.1.2 yc'yi "kabin merkezinin ray koordinatlarına göre konumu",
    #  yp'yi "boş kabin kütlesinin (P) konumu" diye tanımlar;  ikisi de
    #  C.2.1.1 b), C.2.2.1 b) ve C.2.3.1 b)'de Fy'nin payına girer.
    #  Burada ikisi de SABİT SIFIR yazılıydı:  girdi listesinde "Kabin
    #  merkezinin y ekseninde kaçıklığı" diye bir kutu vardı, kullanıcı
    #  değer giriyordu ve Fy hiç değişmiyordu — kutu yalnız kapı eşiğinin
    #  konumunu ( yi, m.C.2.3 ) besliyordu.  200 mm kaçıklıkta Fy 836,7 N
    #  kalıyordu, doğrusu 2.567,9 N — EMNİYETSİZ taraf.
    #  ( ELEport'un paftası da Yp'yi gerçek bir girdi olarak taşır:
    #    "Fy = k2·gn·( Q·(yQ−Ys) + P·(Yp−Ys) ) / ((n/2)·h)" )
    yc = g["kabin_kaciklik"]
    #  BOŞ KABİNİN AĞIRLIK MERKEZİ DE RAY EKSENİNDEN ÖLÇÜLÜR.
    #  Ek C.2.1.1'in  Fx = k1·gn·( Q·xQ + P·xp ) / ( n·h )  bağıntısındaki pay,
    #  sistemin RAY EKSENİNE göre devirici momentidir;  xQ ile xp aynı toplama
    #  giriyorsa ikisinin de orijini ray merkez çizgisi olmak ZORUNDADIR.
    #  Kitap xp'yi kabin merkezinden ölçüyordu:  yalnız kapı + mekanizma
    #  kütlesinin kaçıklığını sayıyor, kabin gövdesinin ray eksenine göre
    #  kaçıklığını ( xc ) hiç saymıyordu.  Ray ekseni kabin merkezinden
    #  geçtiğinde ( xc = 0 ) iki okuma çakışır — kitabın örneği oradadır — ama
    #  ray kaydıkça ayrışır ve EMNİYETSİZ tarafa da düşer:  ray–kapı arası
    #  500 mm'de moment toplamı gerçeğin %79'u, 1000 mm'de %36'sı çıkıyordu.
    #      gövde  ( P − mkapı )  →  xc
    #      kapı   ( mkapı )      →  xc − ( D/2 + mekanizma payı )
    #      xp = [ (P−mkapı)·xc + mkapı·( xc − (D/2+pay) ) ] / P = xc − xp_kapı
    xp_kapi = (g["kapi_agirligi"] * (D / 2.0 + g["kapi_mekanizma_payi"])) / P
    xp = xc - xp_kapi
    #  yp = yc:  kapı x yüzündedir, kabinin y merkezini kaydırmaz — bu yüzden
    #  x'teki gibi ayrı bir kapı düzeltmesi yoktur.
    yp = yc
    #  ASKI NOKTASI ( S ) GİRDİDİR.  Ek C.1.2'nin tanımı:  "xs, ys is the
    #  position of the suspension (S) in relation to the guide rail cross
    #  coordinates".  C.2.1.1'de geçmez ( güvenlik tertibatı rayı kavrar,
    #  tepki ray ekseninden ölçülür );  C.2.2.1 ve C.2.3.1 taşır.
    #  Eskiden sabit sıfırdı:  askısı eksantrik bir kabinde normal çalışma
    #  kuvvetleri yanlış çıkıyordu ( ±%100'ü aşan sapmalar ).
    xs, ys = g["aski_kaciklik_x"], g["aski_kaciklik_y"]
    #  KAPI KONUMU DA RAY EKSENİNDEN ÖLÇÜLÜR  ( Ek C.1.2 ).
    #  C.2.3'ün payı  gn·P·(xp − xs) + Fs·(xi − xs)  bir moment toplamıdır;
    #  xp ray ekseninden ölçülen İŞARETLİ bir konumdur, xi de öyle olmalıdır.
    #  Kitap oraya ray–kapı arasını HAM MESAFE olarak yazıyordu ( hep artı ).
    #  Kapı, ray ekseninin kabin merkezinin TERS tarafındadır:  kabin merkezi
    #  +xc'de ise kapı düzlemi −RK'dedir.  Ray ekseni kabin merkezini geçince
    #  ( xc < 0 ) iki terim yanlış yönde toplanıyor ve eşik kuvveti boş
    #  kabinin momentini DENGELİYORDU:  1400 mm derinlikte RK = 1.200 mm iken
    #  Fx 8,2 N çıkıyor, doğrusu 864,4 N — 105 kat, EMNİYETSİZ taraf.
    xi, yi = -g["ray_kapi_arasi"], g["kabin_kaciklik"]
    balata, balata_kaynak = _balata_boyu(g, p)
    Fs = ((S["Fs_alt"] if Q < S["Fs_sinir"] else S["Fs_ust"]) * gn * Q)

    #  Durum 1  ( x ekseni ) ve Durum 2  ( y ekseni ) yük merkezleri.
    #  TS EN 81-50 Ek C.2.1.1:  yük yalnız ilgili eksende Dx/8 ya da Dy/8
    #  kadar kaydırılır;  ÖTEKİ eksendeki moment kolu kabin merkezidir.
    #  ( Kaynak Excel Durum 2'de xQ'yu sabit 0 yazar — bkz. EXCEL_FARKLARI. )
    #  Yük ± kaydırılır, momenti büyüten yön seçilir  ( m.5.7.2.3.4 ).
    #
    #  YÖN HER YÜK DURUMU İÇİN AYRI SEÇİLİR.  C.2.1'in momenti
    #  ( Q·yQ + P·yp ) askı noktasını TAŞIMAZ;  C.2.2 ve C.2.3'ünki
    #  ( Q·(yQ−ys) + P·(yp−ys) ) taşır.  Askı ray ekseninde değilken en
    #  olumsuz yön ikisinde FARKLI olabilir — tek bir yön seçip ikisine
    #  birden vermek, güvenlik tertibatı durumunda yanlış yönü seçtiriyordu.
    #  ( xs = ys = 0 iken iki seçim çakışır;  eski davranış aynen korunur. )
    xQ1_g = _yuk_merkezi(xc, D / S["Dx_bolen"], Q, P, xp)          # C.2.1
    yQ2_g = _yuk_merkezi(yc, W / S["Dy_bolen"], Q, P, yp)
    xQ1_n = _yuk_merkezi(xc, D / S["Dx_bolen"], Q, P, xp, xs)      # C.2.2 · C.2.3
    yQ2_n = _yuk_merkezi(yc, W / S["Dy_bolen"], Q, P, yp, ys)
    #  Paftada gösterilen "Durum 1 / Durum 2" satırları güvenlik tertibatı
    #  durumunundur — bölümün hükmünü genelde o verir.
    xQ1, yQ1, xQ2, yQ2 = xQ1_g, yc, xc, yQ2_g

    b = Bolum("KABİN KILAVUZ RAYLARININ HESAPLANMASI", kimlik="kabin_raylari",
              kaynak="TS EN 81-50 m.C.2.1 / C.2.2 / C.2.3")
    ad = [
        veri("h", "Patenler arası düşey mesafe", h, "mm", "GİRİŞ"),
        veri("l", "Ray konsolları arasındaki en uzun mesafe", l, "mm", "GİRİŞ"),
        veri("n", "Ray sayısı", n, "adet", "GİRİŞ", 0),
        veri("", "Ray profili", prof, "", "ISO 7465"),
        hesap("Mg = ray boyu × Gr", f"{tr(ray_boyu)} m × {tr(MT.ray(prof, 'Gr'))} kg/m",
              Mg, "kg"),
        veri("MY", "Raylara bağlı yardımcı donanım kütlesi", MY, "N", "Ofis kabulü", 0),
        #  DARBE KATSAYILARI PAFTADA GÖRÜNSÜN.  k1 ve k2'nin değeri EN 81-20
        #  Çizelge 14'te YAZILIDIR;  k3 için çizelge sayı vermez ( "imalatçı
        #  tarafından, gerçek tesise göre belirlenir" ) — hangi sayının
        #  kullanıldığı denetçiye görünmelidir.
        veri("k1", "Güvenlik tertibatı darbe katsayısı", k1, "",
             f"EN 81-20 Çizelge 14  ·  {g['guvenlik_tertibati']}", 0),
        veri("k2", "Normal işletme darbe katsayısı", k2, "",
             "EN 81-20 Çizelge 14  ·  Running", 1),
        veri("k3", "Yardımcı donanım darbe katsayısı", k3, "",
             "OFİS STANDARDI  —  Çizelge 14 sayı vermez, imalatçı belirler", 1),
        veri("xc", "Kabin merkezinin x mesafesi", xc, "mm"),
        veri("yc", "Kabin merkezinin y mesafesi", yc, "mm"),
        veri("xp", "Boş kabin ağırlık merkezinin x mesafesi", xp, "mm",
             f"xc − kapı katkısı  ( {trn(g['kapi_agirligi'], 0)} kg × "
             f"{trn(D / 2 + g['kapi_mekanizma_payi'], 0)} mm / {trn(P, 0)} kg )  ·  "
             "gövde kabin merkezinde kabul edilir"),
        veri("yp", "Boş kabin ağırlık merkezinin y mesafesi", yp, "mm"),
        veri("xs", "Askı noktasının x mesafesi", xs, "mm"),
        veri("ys", "Askı noktasının y mesafesi", ys, "mm"),
        veri("xi", "Kabin kapısının x mesafesi", xi, "mm"),
        veri("yi", "Kabin kapısının y mesafesi", yi, "mm"),
        veri("E", "Elastisite modülü", S["E"], "N/mm²", "Ofis kabulü", 0),
        hesap("Fs = 0,4 × gn × Q      ( Q < 2500 kg )" if Q < S["Fs_sinir"]
              else "Fs = 0,6 × gn × Q      ( Q ≥ 2500 kg )",
              f"{tr(S['Fs_alt'] if Q < S['Fs_sinir'] else S['Fs_ust'])} × "
              f"{tr(gn)} × {trn(Q, 0)}", Fs, "N", "EN 81-20 Çizelge 13"),
        veri("σperm", "Güv. tertibatı çalışmasında izin verilen gerilme", sperm_g,
             "N/mm²", f"EN 81-20 m.5.7.3.1  ·  Rm = {trn(g['ray_celigi_rm'], 0)}", 0),
        veri("σperm", "Normal kullanmada izin verilen gerilme", sperm_n, "N/mm²",
             "EN 81-20 m.5.7.3.1", 0),
        veri("δperm", "İzin verilen en büyük eğilme miktarı", dperm, "mm",
             "EN 81-20 m.5.7.4.6", 0),
        veri("ℓ", "Paten balatasının uzunluğu",
             "—" if makarali else balata,
             "" if makarali else "mm",
             "Makaralı paten  ( EN 81-50 m.5.10.5 makara formülü geçerlidir )"
             if makarali else balata_kaynak, 0),
        hesap(f"Durum 1 :  xQ = xc {'+' if xQ1 >= xc else '−'} D / 8",
              f"{tr(xc)} {'+' if xQ1 >= xc else '−'} {trn(D, 0)} / 8", xQ1, "mm",
              "EN 81-20 m.5.7.2.3.4  ·  yük en olumsuz konumda"),
        hesap(f"Durum 2 :  yQ = yc {'+' if yQ2 >= yc else '−'} W / 8",
              f"{tr(yc)} {'+' if yQ2 >= yc else '−'} {trn(W, 0)} / 8", yQ2, "mm",
              "EN 81-20 m.5.7.2.3.4  ·  yük en olumsuz konumda"),
    ]

    uygunlar = []

    def _kesim(baslik, kaynak, Fx1, Fy1, Fx2, Fy2, kk, sperm, omega=None,
               hucre=()):
        """Bir yükleme durumu için gerilme · burkulma · flanş · sehim satırları.

        hucre  her durum için  ( Fx, σy, Fy, σx, σm, σc, σ, σF, δx, δy )
               Excel adresleri;  boş dize atlanır.

        SIRA DİKKAT:  Excel'in hücreleri "Fx'ten gelen gerilme" ve "Fy'den
        gelen gerilme" diye dizilidir.  TS EN 81-50'de Fx'ten gelen gerilme
        σy'dir ( Fx → My → Wy ), Fy'den gelen ise σx.  Bu yüzden demet
        σy · σx sırasındadır — Excel adresleri değişmez, yalnız adlar
        standardın adlandırmasına oturmuştur.
        """
        ad.append(metin(baslik, vurgu=True))
        sonuc = []
        for sira, (etiket, Fx, Fy) in enumerate(
                (("Durum 1  x-ekseni", Fx1, Fy1), ("Durum 2  y-ekseni", Fx2, Fy2))):
            h = hucre[sira] if sira < len(hucre) else ()
            ad.append(metin(etiket + " :"))
            ad.append(hesap("Fx", kaynak, Fx, "N"))
            ad.append(hesap("Fy", kaynak, Fy, "N"))
            #  m.C.2.1.1:  Fx → My → Wy   ·   Fy → Mx → Wx
            sy, dx = _ray_satirlari("y", "x", Fx, l, p["Wy"], p["Iy"], ad, dstr_x)
            sx, dy = _ray_satirlari("x", "y", Fy, l, p["Wx"], p["Ix"], ad, dstr_y)
            sm = sx + sy
            sc = (kk["Fv"] + kk["k"] * MY) / p["A"] + sm
            ad.append(hesap("σm = σx + σy", f"{tr(sx)} + {tr(sy)}", sm, "N/mm²"))
            ad.append(kontrol(f"σm = {tr(sm)}  ≤  σperm = {trn(sperm, 0)} N/mm²",
                              sm <= sperm))
            ad.append(hesap("σc = ( Fv + k × MY ) / A + σm",
                            f"( {tr(kk['Fv'])} + {tr(kk['k'])} × {trn(MY, 0)} ) / "
                            f"{trn(p['A'], 0)} + {tr(sm)}", sc, "N/mm²"))
            ad.append(kontrol(f"σc = {tr(sc)}  ≤  σperm = {trn(sperm, 0)} N/mm²",
                              sc <= sperm))
            sonuc += [sm <= sperm, sc <= sperm]
            if omega is not None:
                st = kk["sigma_k"] + S["birlesik_katsayi"] * sm
                ad.append(hesap("σ = σk + 0,9 × σm",
                                f"{tr(kk['sigma_k'])} + 0,9 × {tr(sm)}", st, "N/mm²"))
                ad.append(kontrol(f"σ = {tr(st)}  ≤  σperm = {trn(sperm, 0)} N/mm²",
                                  st <= sperm))
                sonuc.append(st <= sperm)
            sf = abs(_flans(Fx, p, balata, makarali))
            ad.append(hesap(
                "σF = 1,85 × | Fx | / c²" if makarali else
                "σF = | Fx | × ( h1−b−f ) × 6 / ( c² × ( ℓ + 2 × ( h1−f ) ) )",
                (f"1,85 × {tr(Fx)} / {tr(p['c'] ** 2)}" if makarali else
                 f"{tr(Fx)} × {tr(p['h1_b_f'] * 6)} / "
                 f"{tr(p['c'] ** 2 * (balata + 2 * p['h1_f']))}"),
                sf, "N/mm²", f"EN 81-50 m.5.10.5  ·  {g['paten_tipi'].lower()} paten"))
            ad.append(kontrol(f"σF = {tr(sf)}  ≤  σperm = {trn(sperm, 0)} N/mm²",
                              sf <= sperm))
            ad.append(hesap("δx = | 0,7 × l³ × Fx / ( 48 × E × Iy ) | + δstr-x",
                            f"l = {trn(l, 0)} mm ,  Iy = {trn(p['Iy'], 0)} mm⁴"
                            + (f" ,  δstr-x = {tr(dstr_x)} mm" if dstr_x else ""),
                            dx, "mm"))
            ad.append(kontrol(f"δx = {tr(dx)}  ≤  δperm = {trn(dperm, 0)} mm",
                              dx <= dperm))
            ad.append(hesap("δy = | 0,7 × l³ × Fy / ( 48 × E × Ix ) | + δstr-y",
                            f"l = {trn(l, 0)} mm ,  Ix = {trn(p['Ix'], 0)} mm⁴"
                            + (f" ,  δstr-y = {tr(dstr_y)} mm" if dstr_y else ""),
                            dy, "mm"))
            ad.append(kontrol(f"δy = {tr(dy)}  ≤  δperm = {trn(dperm, 0)} mm",
                              dy <= dperm))
            sonuc += [sf <= sperm, dx <= dperm, dy <= dperm]
            if h:
                st_v = kk["sigma_k"] + S["birlesik_katsayi"] * sm if omega else None
                for adres, deger in zip(h, (Fx, sy, Fy, sx, sm, sc, st_v,
                                            sf, dx, dy)):
                    if adres:
                        _kay(o, **{adres: deger})
        uygunlar.extend(sonuc)

    # ── C.2.1  Güvenlik tertibatının çalışması ────────────────────────
    #  Ek C.2.1.2:  Fv = k1·gn·(P+Q)/n + Mg·gn + Fp.  Fp bir raydaki bütün
    #  konsol klipslerinin itme kuvvetidir;  kaynak kitapta hiç yoktu.
    Fk = k1 * gn * (P + Q) / n + Mg * gn + Fp
    lam, omega = _burkulma_omega(l, p["imin"], g["ray_celigi_rm"])
    #  MY çarpanı burada da k3'tür ( 11!W354 = 1,2 ) — güvenlik tertibatı
    #  durumunda bile yardımcı donanım normal kullanma katsayısıyla alınır.
    sigma_k = ((Fk + k3 * MY) * omega / p["A"]) if omega else None
    burkulma_uygun = sigma_k is not None and 0 <= sigma_k <= sperm_g
    ad += [
        metin("Güvenlik Tertibatının Çalışması  ( TS EN 81-50 m.C.2.1 ) :", vurgu=True),
        hesap("Fk = k1 × gn × ( P + Q ) / n + Mg × gn + Fp",
              f"{tr(k1)} × {tr(gn)} × ( {trn(P, 0)} + {trn(Q, 0)} ) / {trn(n, 0)} "
              f"+ {tr(Mg)} × {tr(gn)}" + (f" + {tr(Fp)}" if Fp else ""), Fk, "N"),
        hesap("λ = l / imin", f"{trn(l, 0)} / {tr(p['imin'])}"
              f"   ( ix = {tr(p['ix'])} · iy = {tr(p['iy'])} )",
              l / p["imin"], ""),
        veri("λ", "Yuvarlanmış burkulma narinliği  ( en az 20 )", lam, "",
             "11!AV355", 0),
        veri("ω", "Omega değeri", omega, "",
             (f"EN 81-50 m.5.10.3  ·  λ = {lam}  ·  Rm = {trn(g['ray_celigi_rm'], 0)}"
              if omega else
              f"TABLO DIŞI — λ = {lam} > {MT.OMEGA_LAMBDA_MAX};  konsol aralığını "
              "küçültün ya da daha büyük kesitli ray seçin"), 6),
        hesap("σk = ( Fk + k3 × MY ) × ω / A",
              f"( {tr(Fk)} + {tr(k3)} × {trn(MY, 0)} ) × {tr(omega)} / {trn(p['A'], 0)}",
              sigma_k, "N/mm²"),
        kontrol(f"σk = {tr(sigma_k)}  ≤  σperm = {trn(sperm_g, 0)} N/mm²",
                burkulma_uygun),
    ]
    uygunlar.append(burkulma_uygun)
    _kesim("Eğilme gerilmesi  ( C.2.1 ) :", "k1 × gn × ( Q·xQ + P·xp ) / ( n × h )",
           k1 * gn * (Q * xQ1_g + P * xp) / (n * h),
           k1 * gn * (Q * yc + P * yp) / ((n / 2.0) * h),
           k1 * gn * (Q * xc + P * xp) / (n * h),
           k1 * gn * (Q * yQ2_g + P * yp) / ((n / 2.0) * h),
           {"Fv": Fk, "k": k3, "sigma_k": sigma_k}, sperm_g, omega,
           (("AY321", "AU324", "AY327", "AU330", "Z360", "AJ362", "AE365",
             "Z379", "AH393", "AH396"),
            ("AY335", "AU338", "K344", "AU347", "Z369", "AJ371", "AE374",
             "Z384", "AH401", "AH404")))

    # ── C.2.2  Normal çalışma, işletme ────────────────────────────────
    #  Ek C.2.2.2 / C.2.3.2:  Fv = Mg·gn + Fp   ( burada ω yoktur )
    Fv = Mg * gn + Fp
    sigma_v = (Fv + k3 * MY) / p["A"]
    ad += [
        metin("Normal Çalışma, İşletme  ( TS EN 81-50 m.C.2.2 ) :", vurgu=True),
        hesap("Fv = Mg × gn + Fp", f"{tr(Mg)} × {tr(gn)}"
              + (f" + {tr(Fp)}" if Fp else ""), Fv, "N"),
        hesap("σv = ( Fv + k3 × MY ) / A",
              f"( {tr(Fv)} + {tr(k3)} × {trn(MY, 0)} ) / {trn(p['A'], 0)}",
              sigma_v, "N/mm²"),
        kontrol(f"σv = {tr(sigma_v)}  ≤  σperm = {trn(sperm_n, 0)} N/mm²",
                sigma_v <= sperm_n),
    ]
    uygunlar.append(sigma_v <= sperm_n)
    #  Ek C.2.2.1 katsayıyı k2 der ( EN 81-20 Çizelge 14:  Running = 1,2 );
    #  kitap burada "k3" yazıyordu — sayı aynı, AD yanlıştı.
    #  Fy'nin paydası da C.2.1.1 b) ile aynıdır:  ( n / 2 ) · h.  Kitap
    #  n·h yazıyordu, yani Fy'yi YARISI kadar gösteriyordu — emniyetsiz.
    _kesim("Eğilme gerilmesi  ( C.2.2 ) :",
           "k2 × gn × ( Q·(xQ−xs) + P·(xp−xs) ) / ( n × h )",
           k2 * gn * (Q * (xQ1_n - xs) + P * (xp - xs)) / (n * h),
           k2 * gn * (Q * (yc - ys) + P * (yp - ys)) / ((n / 2.0) * h),
           k2 * gn * (Q * (xc - xs) + P * (xp - xs)) / (n * h),
           k2 * gn * (Q * (yQ2_n - ys) + P * (yp - ys)) / ((n / 2.0) * h),
           {"Fv": Fv, "k": k3}, sperm_n, None,
           (("L415", "AU418", "L424", "AU427", "Z461", "AC463", "",
             "Z476", "AH487", "AH490"),
            ("L435", "AU438", "L444", "AU447", "Z468", "AH470", "",
             "Z481", "AH495", "AH498")))

    # ── C.2.3  Normal çalışma, yükleme ────────────────────────────────
    Fx3 = (gn * P * (xp - xs) + Fs * (xi - xs)) / (n * h)
    #  Ek C.2.3.1 b) paydası da ( n / 2 ) · h'dir.
    Fy3 = (gn * P * (yp - ys) + Fs * (yi - ys)) / ((n / 2.0) * h)
    ad.append(metin("Normal Çalışma, Yükleme  ( TS EN 81-50 m.C.2.3 ) :", vurgu=True))
    ad.append(hesap("Fx = ( gn × P × (xp−xs) + Fs × (xi−xs) ) / ( n × h )",
                    f"( {tr(gn)} × {trn(P, 0)} × {tr(xp - xs)} + {tr(Fs)} × "
                    f"{tr(xi - xs)} ) / ( {trn(n, 0)} × {trn(h, 0)} )", Fx3, "N"))
    ad.append(hesap("Fy = ( gn × P × (yp−ys) + Fs × (yi−ys) ) / ( n × h )",
                    f"( {tr(gn)} × {trn(P, 0)} × {tr(yp - ys)} + {tr(Fs)} × "
                    f"{tr(yi - ys)} ) / ( {trn(n, 0)} × {trn(h, 0)} )", Fy3, "N"))
    #  m.C.2.3:  Fx → My → Wy   ·   Fy → Mx → Wx
    sy3, dx3 = _ray_satirlari("y", "x", Fx3, l, p["Wy"], p["Iy"], ad, dstr_x)
    sx3, dy3 = _ray_satirlari("x", "y", Fy3, l, p["Wx"], p["Ix"], ad, dstr_y)
    sm3 = sx3 + sy3
    sc3 = (Fv + k3 * MY) / p["A"] + sm3
    sf3 = abs(_flans(Fx3, p, balata, makarali))
    ad += [
        hesap("σm = σx + σy", f"{tr(sx3)} + {tr(sy3)}", sm3, "N/mm²"),
        kontrol(f"σm = {tr(sm3)}  ≤  σperm = {trn(sperm_n, 0)} N/mm²", sm3 <= sperm_n),
        hesap("σc = ( Fv + k3 × MY ) / A + σm", f"σv + σm", sc3, "N/mm²"),
        kontrol(f"σc = {tr(sc3)}  ≤  σperm = {trn(sperm_n, 0)} N/mm²", sc3 <= sperm_n),
        hesap("σF  ( flanş eğilmesi )", f"Fx = {tr(Fx3)} N", sf3, "N/mm²"),
        kontrol(f"σF = {tr(sf3)}  ≤  σperm = {trn(sperm_n, 0)} N/mm²", sf3 <= sperm_n),
        hesap("δx", f"Iy = {trn(p['Iy'], 0)} mm⁴", dx3, "mm"),
        kontrol(f"δx = {tr(dx3)}  ≤  δperm = {trn(dperm, 0)} mm", dx3 <= dperm),
        hesap("δy", f"Ix = {trn(p['Ix'], 0)} mm⁴", dy3, "mm"),
        kontrol(f"δy = {tr(dy3)}  ≤  δperm = {trn(dperm, 0)} mm", dy3 <= dperm),
    ]
    uygunlar += [sm3 <= sperm_n, sc3 <= sperm_n, sf3 <= sperm_n,
                 dx3 <= dperm, dy3 <= dperm]

    _kay(o, AH291=Mg, AH293=xc, AH295=xp, AH299=xi, AH300=yi, AH303=Fs,
         AH304=sperm_g, AH305=sperm_n, Z309=xQ1, Z312=yQ2,
         AU351=Fk, AV354=l / p["imin"], AV355=lam, AD354=omega, AL354=sigma_k,
         AE452=Fv, AL455=sigma_v,
         #  AU511 Fx3'ten, AU519 Fy3'ten gelen gerilmedir;  standardın
         #  adlandırmasında bunlar sırasıyla σy ve σx'tir.
         L508=Fx3, AU511=sy3, L516=Fy3, AU519=sx3, Z530=sm3, AF532=sc3,
         Z537=sf3, AH542=dx3, AH545=dy3)
    o.update(Fk_kabin=Fk, Mg_kabin=Mg, ray_boyu=ray_boyu)
    b["adimlar"] = ad
    hepsi = all(uygunlar)
    b["sonuc"] = {"baslik": "KONTROL      σm · σc · σF ≤ σperm   ve   δ ≤ δperm",
                  "metin": "UYGUNDUR." if hepsi
                           else "UYGUN DEĞİLDİR — ray profilini büyütün ya da "
                                "konsol aralığını küçültün",
                  "uygun": bool(hepsi)}
    _not = _ray_tutarsizlik_notu(prof)
    if _not:
        b["notlar"] = [_not]
    b["aciklamalar"] = [
        "Adlandırma TS EN 81-50 Ek C.2.1.1'in kendisidir:  Fx → My → Wy ve "
        "Fy → Mx → Wx.  Yani x yönündeki kuvvet rayı Y ekseni etrafında eğer. "
        "Kaynak kitap bu ikisini ters adlandırıyordu ( sayı doğru, ad "
        "yanlıştı ) ve kendi sehim satırlarıyla çelişiyordu.",
        "Durum 1 yükü x ekseninde Dx/8, Durum 2 y ekseninde Dy/8 kadar "
        "kaydırır ( TS EN 81-50 Ek C.2.1.1 ); öteki eksendeki moment kolu her "
        "iki durumda da kabin merkezidir. Kaynak Excel Durum 2'de xQ'yu sabit "
        "0 yazar — standart uygulanmıştır.",
        "Flanş eğilmesinde ℓ paten balatasının uzunluğudur ( EN 81-50 "
        "m.5.10.5 ). Girilmezse ray tablosundaki balata yarı genişliğinden "
        "2·b olarak türetilir; kesin değer paten imalatçısından alınmalıdır."]
    return b


# =====================================================================
#  8 -  KARŞI AĞIRLIK KILAVUZ RAYLARI              ( TS EN 81-50 m.5.10 )
# =====================================================================
def _agirlik_raylari(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    #  k2  normal işletme darbe katsayısı  ( EN 81-20 Çizelge 14 = 1,2 ),
    #  k3  yardımcı donanım katsayısı  —  çizelge ona sayı vermez, ofis verir.
    k2, k3 = S["k2"], O["k3_yardimci"]
    Fp = g["klips_itme_kuvveti"] or 0.0
    dstr_x, dstr_y = g["yapi_sehim_x"] or 0.0, g["yapi_sehim_y"] or 0.0
    #  YAN AĞIRLIKTA BİNA SEHİM EKSENLERİ RAYA GÖRE DÖNER.
    #  Kabin rayları kuyu yan duvarındadır ( ray x'i genişlik, y'si derinlik ).
    #  Karşı ağırlık yanda ( Sağ / Sol ) olduğunda raylar 90° dönük monte edilir:
    #  binanın X sehimi ağırlık rayının Y eksenine ( sırtına ), Y sehimi ise
    #  rayın X eksenine ( flanşına ) etki eder.  Arka ağırlıkta eksenler paraleldir.
    if g.get("agirlik_yeri") in ("Sağ", "Sol"):
        dstr_ray_x, dstr_ray_y = dstr_y, dstr_x
    else:
        dstr_ray_x, dstr_ray_y = dstr_x, dstr_y
    makarali = g["paten_tipi"] == "Makaralı"
    prof = g["agirlik_ray_profili"]
    p = _ray_ozellik(prof)
    n = g["agirlik_ray_sayisi"]
    h, l = g["agirlik_paten_arasi"], g["agirlik_konsol_arasi"]
    Mcwt = g["karsi_agirlik"]
    MY = S["MY_agirlik"]
    sperm = MT.sigma_perm_normal(g["ray_celigi_rm"])

    gt = g.get("agirlik_guvenlik_tertibati") or "Yok"
    gt_var = gt != "Yok"
    #  TS EN 81-20 m.5.6.2.1.2.3:  karşı ağırlık ( ya da dengeleme ağırlığı )
    #  güvenlik tertibatı, BEYAN HIZI 1 m/s'yi AŞIYORSA kaymalı olmak
    #  zorundadır;  altında ani frenlemeli de olabilir.  Kitap tertibat tipini
    #  hiç sınamıyordu — 2,5 m/s'lik bir asansöre ani frenlemeli tertibat
    #  konsa da bölüm "UYGUNDUR" diyordu.
    gt_tip_uygun = (not gt_var or not gt.startswith("Ani Frenlemeli")
                    or g["beyan_hizi"] <= S["agirlik_kaymali_esigi"])
    #  TS EN 81-20 m.5.7.4.6:  İzin verilen azami sehim ( δperm )
    #  a) Güv. tertibatlı kabin ve GÜV. TERTİBATLI KARŞI AĞIRLIK raylarında: 5 mm
    #  b) Güv. tertibatsız karşı ağırlık raylarında: 10 mm
    dperm = S["dperm_kabin"] if gt_var else S["dperm_agirlik"]

    #  KARŞI AĞIRLIĞIN KENDİ ÖLÇÜLERİ  —  Ek C.2.2'nin Gx ( derinlik ) ve
    #  Gy ( genişlik )'si.  İKİSİ DE GİRDİDİR;  eskiden derinlik malzemeden,
    #  genişlik ray arasından türetiliyordu ve ikisi de yanlıştı — ölçü imal
    #  edilen çerçevenin özelliğidir ( bkz. mukavemet_tablolari'ndeki
    #  "AĞIRLIK RAY ARASI → GENİŞLİK TABLOSU · KALDIRILDI" notu ).
    derinlik = g["agirlik_derinligi"]
    genislik = g["agirlik_genisligi"]
    Dxa = S["Dxa_katsayi"] * derinlik
    Dya = S["Dya_katsayi"] * genislik
    xsa = ysa = 0.0

    Mg = o["ray_boyu"] * MT.ray(prof, "Gr")
    #  Ek C.2.2.1:  katsayı k2'dir ve Fy'nin paydası ( n / 2 ) · h'dir.
    Fx = (k2 * gn * Mcwt * (Dxa - xsa)) / (n * h)
    Fy = (k2 * gn * Mcwt * (Dya - ysa)) / ((n / 2.0) * h)
    Mx, My = _moment(Fx, l), _moment(Fy, l)
    #  σ ve δ BÜYÜKLÜKTÜR  ( bkz. _ray_satirlari ).  Karşı ağırlıkta Dxa/Dya
    #  ve Mcwt pozitif olduğu için bugün işaret dönmüyor;  kural yine de
    #  kabin rayıyla AYNI tutulur — geometri kabulü değişirse iki bölüm
    #  sessizce ayrışmasın.
    sx, sy = abs(Mx) / p["Wy"], abs(My) / p["Wx"]
    sm = sx + sy
    Fv = Mg * gn + Fp
    sv = (Fv + k3 * MY) / p["A"]
    sc = sv + sm
    balata, balata_kaynak = _balata_boyu(g, p)
    sf = abs(_flans(Fx, p, balata, makarali))
    dx = abs(_sehim(Fx, l, p["Iy"])) + dstr_ray_x
    dy = abs(_sehim(Fy, l, p["Ix"])) + dstr_ray_y
    kontroller = [sm <= sperm, sc <= sperm, sf <= sperm, dx <= dperm, dy <= dperm,
                  gt_tip_uygun]

    #  ------------------------------------------------------------------
    #  KARŞI AĞIRLIKTA GÜVENLİK TERTİBATI      TS EN 81-50 Ek C.2.1
    #  ------------------------------------------------------------------
    #  TS EN 81-20 m.5.6.1:  kuyunun altındaki hacme girilebiliyorsa karşı
    #  ağırlıkta güvenlik tertibatı ZORUNLUDUR.  Kitap ağırlık rayını yalnız
    #  C.2.2'ye ( normal işletme, k3 ) göre kuruyordu;  k1 hiç girmiyordu.
    #  Tertibat varsa rayın asıl belirleyici yük durumu odur:  k1 = 2 … 5,
    #  yani ray kuvvetleri iki ila dört kat büyür.
    kg = None
    if gt_var:
        k1a = US.darbe_k1(o["ofis"], gt)
        sperm_g = MT.sigma_perm_guvenlik(g["ray_celigi_rm"])
        lam_a, omega_a = _burkulma_omega(l, p["imin"], g["ray_celigi_rm"])
        Fxg = (k1a * gn * Mcwt * (Dxa - xsa)) / (n * h)
        Fyg = (k1a * gn * Mcwt * (Dya - ysa)) / ((n / 2.0) * h)
        sxg = abs(_moment(Fxg, l)) / p["Wy"]
        syg = abs(_moment(Fyg, l)) / p["Wx"]
        smg = sxg + syg
        Fkg = (k1a * gn * Mcwt) / n + Mg * gn + Fp
        skg = ((Fkg + k3 * MY) * omega_a / p["A"]) if omega_a else None
        scg = (skg + S["birlesik_katsayi"] * smg) if skg is not None else None
        sfg = abs(_flans(Fxg, p, balata, makarali))
        dxg = abs(_sehim(Fxg, l, p["Iy"])) + dstr_ray_x
        dyg = abs(_sehim(Fyg, l, p["Ix"])) + dstr_ray_y
        #  Bölüm 9 bunu okur:  kuyu tabanına bildirilen yükte güvenlik
        #  tertibatı tepkisi AYRI bir kalemdir ( EN 81-20 m.5.2.1.8.4 ).
        o["Fk_agirlik"] = Fkg
        kg = {"k1": k1a, "sperm": sperm_g, "lam": lam_a, "omega": omega_a,
              "Fx": Fxg, "Fy": Fyg, "sx": sxg, "sy": syg, "sm": smg,
              "Fk": Fkg, "sk": skg, "sc": scg, "sF": sfg, "dx": dxg, "dy": dyg}
        kontroller += [
            smg <= sperm_g,
            skg is not None and 0 <= skg <= sperm_g,
            scg is not None and scg <= sperm_g,
            sfg <= sperm_g, dxg <= dperm, dyg <= dperm]

    b = Bolum("KARŞI AĞIRLIK KILAVUZ RAYLARININ HESAPLANMASI", kimlik="agirlik_raylari",
              kaynak="TS EN 81-50 m.5.10  /  m.C.2.2" + ("  /  m.C.2.1" if gt_var else ""))
    b["adimlar"] = [
        veri("", "Ray profili", prof, "", "ISO 7465"),
        veri("n", "Ağırlık rayı sayısı", n, "adet", "GİRİŞ", 0),
        veri("h", "Ağırlık paten arası", h, "mm", "GİRİŞ"),
        veri("l", "Ağırlık rayı konsollar arası en uzun mesafe", l, "mm", "GİRİŞ"),
        veri("Mcwt", "Karşı ağırlık kütlesi", Mcwt, "kg"),
        veri("", "Karşı ağırlıkta güvenlik tertibatı", gt, "", "GİRİŞ"),
        kontrol(f"{gt} tertibat, beyan hızı {tr(g['beyan_hizi'])} m/s"
                + ("  ( m.5.6.2.1.2.3:  v > 1 m/s ise KAYMALI olmalı )"
                   if gt_var else "  ( tertibat yok )"), gt_tip_uygun),
        veri("", "Karşı ağırlık malzemesi", g["agirlik_malzemesi"]),
        veri("Gx", "Karşı ağırlık derinliği", derinlik, "mm", "GİRİŞ", 0),
        veri("Gy", "Karşı ağırlık genişliği", genislik, "mm", "GİRİŞ", 0),
        veri("", "Ağırlık ray arası  ( hesaba girmez )",
             g["agirlik_ray_arasi"], "mm", "GİRİŞ", 0),
        hesap("Dxa = 0,1 × ağırlık derinliği",
              f"0,1 × {trn(derinlik, 0)}", Dxa, "mm"),
        hesap("Dya = 0,05 × ağırlık genişliği",
              f"0,05 × {trn(genislik, 0)}", Dya, "mm"),
        veri("xsa", "Askı noktasının x mesafesi", xsa, "mm"),
        veri("ysa", "Askı noktasının y mesafesi", ysa, "mm"),
        veri("MY", "Raylara bağlı yardımcı donanım", MY, "N", "Ofis kabulü", 0),
        veri("ℓ", "Paten balatasının uzunluğu",
             "—" if makarali else balata,
             "" if makarali else "mm",
             "Makaralı paten  ( EN 81-50 m.5.10.5 makara formülü geçerlidir )"
             if makarali else balata_kaynak, 0),
        hesap("Mg = ray boyu × Gr",
              f"{tr(o['ray_boyu'])} m × {tr(MT.ray(prof, 'Gr'))} kg/m", Mg, "kg"),
        metin("Eğilme gerilmesi  ( TS EN 81-50 m.C.2.2 ) :", vurgu=True),
        hesap("Fx = k2 × gn × Mcwt × ( Dxa − xsa ) / ( n × h )",
              f"{tr(k2)} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dxa)} / "
              f"( {trn(n, 0)} × {trn(h, 0)} )", Fx, "N"),
        hesap("Fy = k2 × gn × Mcwt × ( Dya − ysa ) / ( ( n / 2 ) × h )",
              f"{tr(k2)} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dya)} / "
              f"( {tr(n / 2.0)} × {trn(h, 0)} )", Fy, "N"),
        #  m.C.2.2.1:  Fx → My → Wy   ·   Fy → Mx → Wx
        hesap("My = 3 × Fx × l / 16", f"3 × {tr(Fx)} × {trn(l, 0)} / 16", Mx,
              "N·mm", ondalik=0),
        hesap("σy = My / Wy", f"{trn(Mx, 0)} / {trn(p['Wy'], 0)}", sx, "N/mm²"),
        hesap("Mx = 3 × Fy × l / 16", f"3 × {tr(Fy)} × {trn(l, 0)} / 16", My,
              "N·mm", ondalik=0),
        hesap("σx = Mx / Wx", f"{trn(My, 0)} / {trn(p['Wx'], 0)}", sy, "N/mm²"),
        metin("Burkulma :"),
        hesap("Fv = Mg × gn + Fp" if Fp else "Fv = Mg × gn",
              f"{tr(Mg)} × {tr(gn)}" + (f" + {tr(Fp)}" if Fp else ""), Fv, "N"),
        hesap("σv = ( Fv + k3 × MY ) / A",
              f"( {tr(Fv)} + {tr(k3)} × {trn(MY, 0)} ) / {trn(p['A'], 0)}", sv, "N/mm²"),
        metin("Birleşik gerilme :"),
        hesap("σm = σx + σy", f"{tr(sy)} + {tr(sx)}", sm, "N/mm²"),
        kontrol(f"σm = {tr(sm)}  ≤  σperm = {trn(sperm, 0)} N/mm²", sm <= sperm),
        hesap("σc = σv + σm", f"{tr(sv)} + {tr(sm)}", sc, "N/mm²"),
        kontrol(f"σc = {tr(sc)}  ≤  σperm = {trn(sperm, 0)} N/mm²", sc <= sperm),
        metin("Flanş eğilmesi :"),
        hesap("σF = 1,85 × | Fx | / c²" if makarali else
              "σF = Fx × ( h1−b−f ) × 6 / ( c² × ( ℓ + 2 × ( h1−f ) ) )",
              (f"1,85 × {tr(Fx)} / {tr(p['c'] ** 2)}" if makarali else
               f"{tr(Fx)} × {tr(p['h1_b_f'] * 6)} / "
               f"{tr(p['c'] ** 2 * (balata + 2 * p['h1_f']))}"),
              sf, "N/mm²",
              f"EN 81-50 m.5.10.5  ·  {g['paten_tipi'].lower()} paten"),
        kontrol(f"σF = {tr(sf)}  ≤  σperm = {trn(sperm, 0)} N/mm²", sf <= sperm),
        metin("Sehim miktarları :"),
        hesap("δx = | 0,7 × l³ × Fx / ( 48 × E × Iy ) |" + (" + δstr-x" if dstr_ray_x else ""),
              f"l = {trn(l, 0)} mm ,  Iy = {trn(p['Iy'], 0)} mm⁴"
              + (f" ,  δstr = {tr(dstr_ray_x)} mm" if dstr_ray_x else ""), dx, "mm"),
        kontrol(f"δx = {tr(dx)}  ≤  δperm = {trn(dperm, 0)} mm", dx <= dperm),
        hesap("δy = | 0,7 × l³ × Fy / ( 48 × E × Ix ) |" + (" + δstr-y" if dstr_ray_y else ""),
              f"l = {trn(l, 0)} mm ,  Ix = {trn(p['Ix'], 0)} mm⁴"
              + (f" ,  δstr = {tr(dstr_ray_y)} mm" if dstr_ray_y else ""), dy, "mm"),
        kontrol(f"δy = {tr(dy)}  ≤  δperm = {trn(dperm, 0)} mm", dy <= dperm),
    ]
    if kg:
        sg = kg["sperm"]
        b["adimlar"] += [
            metin("Güvenlik Tertibatının Çalışması  ( TS EN 81-50 m.C.2.1 ) :",
                  vurgu=True),
            veri("k1", "Darbe katsayısı", kg["k1"], "",
                 f"OFİS STANDARDI  ·  {gt}"),
            veri("σperm", "Güvenlik tertibatı durumunda izin verilen gerilme",
                 sg, "N/mm²", f"Rm = {trn(g['ray_celigi_rm'], 0)}  ·  Rm / 1,8", 0),
            hesap("Fx = k1 × gn × Mcwt × ( Dxa − xsa ) / ( n × h )",
                  f"{tr(kg['k1'])} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dxa)} / "
                  f"( {trn(n, 0)} × {trn(h, 0)} )", kg["Fx"], "N"),
            hesap("σy = My / Wy        ( My = 3 × Fx × l / 16 )",
                  f"Wy = {trn(p['Wy'], 0)} mm³", kg["sx"], "N/mm²"),
            hesap("Fy = k1 × gn × Mcwt × ( Dya − ysa ) / ( ( n / 2 ) × h )",
                  f"{tr(kg['k1'])} × {tr(gn)} × {trn(Mcwt, 0)} × {tr(Dya)} / "
                  f"( {tr(n / 2.0)} × {trn(h, 0)} )", kg["Fy"], "N"),
            hesap("σx = Mx / Wx        ( Mx = 3 × Fy × l / 16 )",
                  f"Wx = {trn(p['Wx'], 0)} mm³", kg["sy"], "N/mm²"),
            hesap("σm = σx + σy", f"{tr(kg['sy'])} + {tr(kg['sx'])}",
                  kg["sm"], "N/mm²"),
            kontrol(f"σm = {tr(kg['sm'])}  ≤  σperm = {trn(sg, 0)} N/mm²",
                    kg["sm"] <= sg),
            hesap("Fk = k1 × gn × Mcwt / n + Mg × gn + Fp" if Fp else
                  "Fk = k1 × gn × Mcwt / n + Mg × gn",
                  f"{tr(kg['k1'])} × {tr(gn)} × {trn(Mcwt, 0)} / {trn(n, 0)} "
                  f"+ {tr(Mg)} × {tr(gn)}" + (f" + {tr(Fp)}" if Fp else ""), kg["Fk"], "N"),
            veri("λ", "Yuvarlanmış burkulma narinliği  ( en az 20 )",
                 kg["lam"], "", "", 0),
            veri("ω", "Omega değeri", kg["omega"], "",
                 (f"EN 81-50 m.5.10.3  ·  λ = {kg['lam']}"
                  if kg["omega"] else "TABLO DIŞI — konsol aralığını küçültün"), 6),
            hesap("σk = ( Fk + k3 × MY ) × ω / A",
                  f"( {tr(kg['Fk'])} + {tr(k3)} × {trn(MY, 0)} ) × "
                  f"{tr(kg['omega'])} / {trn(p['A'], 0)}", kg["sk"], "N/mm²"),
            kontrol(f"σk = {tr(kg['sk'])}  ≤  σperm = {trn(sg, 0)} N/mm²",
                    kg["sk"] is not None and 0 <= kg["sk"] <= sg),
            hesap("σ = σk + 0,9 × σm",
                  f"{tr(kg['sk'])} + 0,9 × {tr(kg['sm'])}", kg["sc"], "N/mm²",
                  "EN 81-50 m.5.10.4"),
            kontrol(f"σ = {tr(kg['sc'])}  ≤  σperm = {trn(sg, 0)} N/mm²",
                    kg["sc"] is not None and kg["sc"] <= sg),
            hesap("σF = 1,85 × | Fx | / c²" if makarali else
                  "σF = Fx × ( h1−b−f ) × 6 / ( c² × ( ℓ + 2 × ( h1−f ) ) )",
                  (f"1,85 × {tr(kg['Fx'])} / {tr(p['c'] ** 2)}" if makarali else
                   f"{tr(kg['Fx'])} × {tr(p['h1_b_f'] * 6)} / "
                   f"{tr(p['c'] ** 2 * (balata + 2 * p['h1_f']))}"),
                  kg["sF"], "N/mm²",
                  f"EN 81-50 m.5.10.5  ·  {g['paten_tipi'].lower()} paten"),
            kontrol(f"σF = {tr(kg['sF'])}  ≤  σperm = {trn(sg, 0)} N/mm²",
                    kg["sF"] <= sg),
            hesap("δx = | 0,7 × l³ × Fx / ( 48 × E × Iy ) |" + (" + δstr-x" if dstr_ray_x else ""),
                  f"l = {trn(l, 0)} mm ,  Iy = {trn(p['Iy'], 0)} mm⁴"
                  + (f" ,  δstr = {tr(dstr_ray_x)} mm" if dstr_ray_x else ""), kg["dx"], "mm"),
            kontrol(f"δx = {tr(kg['dx'])}  ≤  δperm = {trn(dperm, 0)} mm",
                    kg["dx"] <= dperm),
            hesap("δy = | 0,7 × l³ × Fy / ( 48 × E × Ix ) |" + (" + δstr-y" if dstr_ray_y else ""),
                  f"l = {trn(l, 0)} mm ,  Ix = {trn(p['Ix'], 0)} mm⁴"
                  + (f" ,  δstr = {tr(dstr_ray_y)} mm" if dstr_ray_y else ""), kg["dy"], "mm"),
            kontrol(f"δy = {tr(kg['dy'])}  ≤  δperm = {trn(dperm, 0)} mm",
                    kg["dy"] <= dperm),
        ]
    b["sonuc"] = {"baslik": ("KONTROL      σm · σc · σF ≤ σperm   ve   δ ≤ δperm"
                             + ("   ( C.2.2 ve C.2.1 )" if gt_var else "")),
                  "metin": "UYGUNDUR." if all(kontroller)
                           else ("UYGUN DEĞİLDİR — karşı ağırlık güvenlik tertibatı v > 1,0 m/s "
                                 "için kaymalı tip olmalıdır ( TS EN 81-20 m.5.6.2.1.2.3 )"
                                 if not gt_tip_uygun else
                                 "UYGUN DEĞİLDİR — ağırlık rayı profilini büyütün"),
                  "uygun": bool(all(kontroller))}
    _not8 = _ray_tutarsizlik_notu(prof)
    if _not8:
        b["notlar"] = [_not8]
    b["aciklamalar"] = [
        "KAYNAK EXCEL'DEN AYRILAN NOKTA:  Excel, Fy'den gelen gerilme için de "
        "Wy'yi kullanır ( 11!AU575 ).  TS EN 81-50 Ek C.2.2.1 açıkça "
        "Fy → Mx → Wx der;  y yönündeki kuvvet rayı X ekseni etrafında eğer. "
        "Excel'in sehim satırı da zaten Ix kullanır — yani kitap kendi içinde "
        "de çelişiyordu.  Burada Wx alındı;  Excel'in değeri daha büyük "
        "( emniyetli ama yanlış ) çıkar.",
        "TS EN 81-20 m.5.6.1:  karşı ağırlıkta güvenlik tertibatı, kuyunun "
        "altındaki hacme girilebiliyorsa ZORUNLUDUR.  Kitap ağırlık rayını "
        "yalnız normal işletmeye ( m.C.2.2, k3 = 1,2 ) göre kuruyordu;  "
        "tertibat varsa belirleyici yük durumu m.C.2.1'dir ve orada k1 "
        "( 2 · 3 · 5 ) geçer. "
        + ("Bu projede tertibat '" + gt + "' seçilmiştir ve m.C.2.1 de "
           "hesaplanmıştır." if gt_var else
           "Bu projede 'Yok' seçilmiştir;  kuyu dibindeki hacme "
           "girilebiliyorsa seçim gözden geçirilmelidir.")]
    _kay(o, AH550=derinlik, AH551=genislik, N562=Dxa, AL562=Dya, AH554=Mg,
         AP566=Fx, AU569=sx, AP572=Fy, AU575=sy, AE580=Fv, AL583=sv,
         Z588=sm, AF590=sc, Z595=sf, AH600=dx, AH603=dy)
    o.update(Mg_agirlik=Mg)
    return b


# =====================================================================
#  9 -  KUYU TABANINA GELEN YÜKLER            ( TS EN 81-20 m.5.2.1.8 )
# =====================================================================
def _kuyu_tabani(g, o):
    S, gn, O = SABIT, SABIT["gn"], o["ofis"]
    Q, P = o["Q"], o["P"]
    LR = o["ray_boyu"] * 1000.0                      # mm
    Gr_k = MT.ray(g["kabin_ray_profili"], "Gr")
    Gr_a = MT.ray(g["agirlik_ray_profili"], "Gr")
    #  RAY AĞIRLIĞI BİR KEZ SAYILIR.  TS EN 81-20 m.5.2.1.8.4 kalemleri tek
    #  tek sayar:  "the force due to the MASS OF THE GUIDE RAILS plus any load
    #  due to components fixed or linked to the guide(s) … plus the REACTION
    #  at the moment of operation of the safety gear".  Yani ray kütlesi ayrı
    #  bir kalem, güvenlik tertibatı tepkisi ayrı bir kalemdir.
    #
    #  Kaynak kitap ikisini üst üste ekliyordu:  Fk ( bölüm 7'nin Fv'si,
    #  EN 81-50 Ek C.2.1.2 ) zaten Mg·gn içerir, üstüne bir de gn·Gr·LR
    #  ekleniyordu.  Aynı sayı iki kez sayılıyordu.
    ray_agirlik = gn * Gr_k * LR / 1000.0
    #  Fk'den ray kütlesinin payı düşülür;  geriye güvenlik tertibatı
    #  tepkisi ( k1·gn·(P+Q)/n ) ve varsa klips itme kuvveti kalır.
    guvenlik_tepkisi = o["Fk_kabin"] - o["Mg_kabin"] * gn
    FKR = ray_agirlik + S["MY_kabin"] + guvenlik_tepkisi
    #  KARŞI AĞIRLIKTA GÜVENLİK TERTİBATI VARSA TEPKİSİ DE TABANA GELİR.
    #  Kabin tarafında bu kalem sayılıyordu, karşı ağırlıkta sayılmıyordu:
    #  tertibat "Kaymalı" seçilse bile FAR değişmiyordu.  Kuyu tabanı yükü
    #  OLDUĞUNDAN DÜŞÜK bildiriliyordu — inşaat projesine giden sayı budur.
    #  Ray kütlesinin payı burada da bir kez sayılır ( Fk − Mg·gn ).
    agirlik_tepkisi = (o["Fk_agirlik"] - o["Mg_agirlik"] * gn
                       if o.get("Fk_agirlik") is not None else 0.0)
    FAR = (gn * Gr_a * LR / 1000.0) + S["MY_agirlik"] + agirlik_tepkisi
    Fkt = S["tampon_katsayi"] * gn * (P + Q)
    Fat = S["tampon_katsayi"] * gn * (P + o["ofis"]["q_denge"] * Q)
    #  ADET SIFIR YA DA BOŞ GİRİLİRSE 1 SAYILIR:  bölme çökmesin ve
    #  "tek tampon" en olumsuz ( en büyük ) tekil kuvveti versin.
    n_kt = max(1, int(g["kabin_tampon_adedi"] or 1))
    n_at = max(1, int(g["agirlik_tampon_adedi"] or 1))
    Fkt1, Fat1 = Fkt / n_kt, Fat / n_at

    b = Bolum("KUYU TABANINA GELEN YÜKLERİN HESAPLANMASI", kimlik="kuyu_tabani",
              kaynak="TS EN 81-20 m.5.2.1.8")
    b["adimlar"] = [
        veri("LR", "Kılavuz ray boyu", LR, "mm", "Σ durak + kaide − 200 + kuyu dibi − 300", 0),
        metin("Kabin raylarına gelen kuvvetler :"),
        hesap("FKR = gn × Gr × LR / 1000 + MY + Fgt",
              f"{tr(gn)} × {tr(Gr_k)} × {trn(LR, 0)} / 1000 + "
              f"{trn(S['MY_kabin'], 0)} + {tr(guvenlik_tepkisi)}", FKR, "N",
              "EN 81-20 m.5.2.1.8.4"),
        veri("Fgt", "Güvenlik tertibatı çalışma tepkisi  ( Fk − Mg·gn )",
             guvenlik_tepkisi, "N",
             "ray kütlesi ayrı kalemdir, iki kez sayılmaz"),
        metin("Ağırlık raylarına gelen kuvvetler :"),
        hesap("FAR = gn × Gar × Lar / 1000 + Ma"
              + ("  +  Fgt" if agirlik_tepkisi else ""),
              f"{tr(gn)} × {tr(Gr_a)} × {trn(LR, 0)} / 1000 + "
              f"{trn(S['MY_agirlik'], 0)}"
              + (f" + {tr(agirlik_tepkisi)}" if agirlik_tepkisi else ""),
              FAR, "N", "EN 81-20 m.5.2.1.8.4"),
        veri("Fgt", "Karşı ağırlık güvenlik tertibatı çalışma tepkisi",
             agirlik_tepkisi if agirlik_tepkisi else "tertibat yok",
             "N" if agirlik_tepkisi else "",
             (f"{g['agirlik_guvenlik_tertibati']}  ·  Fk − Mg·gn"
              if agirlik_tepkisi else "karşı ağırlıkta güvenlik tertibatı seçilmedi")),
        metin("Kabin tamponlarına gelen kuvvetler :"),
        hesap("Fkt = 4 × gn × ( P + Q )",
              f"4 × {tr(gn)} × ( {trn(P, 0)} + {trn(Q, 0)} )", Fkt, "N"),
        veri("ncar", "Kabin tamponu adedi", n_kt, "adet", "GİRİŞ", 0),
        #  m.5.2.1.8.5:  kuvvet "evenly distributed between the total number
        #  of car buffers".  Döşemenin YEREL olarak taşıyacağı sayı budur;
        #  toplam kuvvet bütün tamponlara dağılır.
        hesap("Fkt1 = Fkt / ncar", f"{trn(Fkt, 0)} / {trn(n_kt, 0)}",
              Fkt1, "N", "m.5.2.1.8.5  ·  bir tampon altına"),
        metin("Ağırlık tamponlarına gelen kuvvetler :"),
        hesap("Fat = 4 × gn × ( P + q × Q )",
              f"4 × {tr(gn)} × ( {trn(P, 0)} + {tr(O['q_denge'])} × {trn(Q, 0)} )",
              Fat, "N"),
        veri("ncwt", "Ağırlık tamponu adedi", n_at, "adet", "GİRİŞ", 0),
        hesap("Fat1 = Fat / ncwt", f"{trn(Fat, 0)} / {trn(n_at, 0)}",
              Fat1, "N", "m.5.2.1.8.6  ·  bir tampon altına"),
    ]
    b["notlar"] = [
        "Bu kuvvetler kuyu alt boşluğu tabanının ( temel / döşeme ) statik "
        "hesabına girer; inşaat projesine bildirilmelidir."]
    b["sonuc"] = {"baslik": "KUYU TABANI YÜKLERİ",
                  "metin": f"FKR = {tr(FKR)} N  ·  FAR = {tr(FAR)} N  ·  "
                           f"Fkt = {tr(Fkt)} N  ·  Fat = {tr(Fat)} N",
                  "uygun": None}
    _kay(o, AH611=LR, AX611=FKR, AN616=FAR, AF621=Fkt, AI627=Fat)
    o.update(FKR=FKR, FAR=FAR, Fkt=Fkt, Fat=Fat)
    return b


# =====================================================================
# 10 -  SIĞINMA ALANLARI VE AÇIKLIKLAR  ( EN 81-20 m.5.2.5.7 / 5.2.5.8 )
# =====================================================================
def _siginma(g, o):
    #  Paylar OFİS STANDARDINDAN, asgari açıklıklar SIGINMA'dan:  birincisi
    #  kabin imalatına bağlı bir kabuldür ve ekrandan değiştirilir, ikincisi
    #  TS EN 81-20'nin sayısıdır ve değiştirilemez.
    K, v = dict(SIGINMA, **{k: o["ofis"][k] for k in SIGINMA_PAYLARI}), o["v"]
    #  Beyan edilen sığınma duruşları.  Tanınmayan bir değer gelirse ( eski
    #  proje dosyası, elle düzenlenmiş Excel ) çömelmeye dönülür — eski
    #  davranış budur ve emniyetli taraftır.
    tip_ust = g.get("siginma_tipi_ust") or "Çömelme"
    tip_dip = g.get("siginma_tipi_dip") or "Çömelme"
    ust_hacim = MT.siginma_hacmi(tip_ust, "ust") or MT.siginma_hacmi("Çömelme", "ust")
    dip_hacim = MT.siginma_hacmi(tip_dip, "dip") or MT.siginma_hacmi("Çömelme", "dip")
    K["ust_hacim"], K["dip_hacim"] = ust_hacim, dip_hacim
    SK = g["son_kat_yuksekligi"]
    W, D = g["kabin_genisligi"], g["kabin_derinligi"]
    bosluk = _bosluk(v)

    #  Kabin tam kapanmış tampon üzerinde otururken kabinin altındaki yığın
    yigin = (g["kabin_paten_arasi"] + g["kabin_carpma_arasi"]
             + g["kabin_tampon_boyu"] - g["kabin_tampon_ezilme"]
             + g["kabin_tampon_baba"])
    #  Ç.2  —  cebirsel olarak  ( son kat yüksekliği − ağırlık paten arası )
    c2_agirlik = (g["kuyu_boyu"] - yigin
                  - (g["agirlik_paten_arasi"]
                     + (g["kuyu_boyu"] - SK - yigin)))
    #  Kuyu tabanı ile kabinin en alt kısmı arası
    a_dip = g["kabin_tampon_baba"] + (g["kabin_tampon_boyu"] - g["kabin_tampon_ezilme"])

    #  Excel'deki "HESAPLANAN" sütunu  ( 11!AI635 … AI648 )
    HUCRE = ("AI635", "AI636", "AI637", "AI638", "AI640",
             "AI645", "AI646", "AI647", "AI648")
    satir = [
        ("b - Üst paten / rayın üst ucu arası",
         K["min_ust_paten"], SK - K["kabin_yuksekligi"] - K["paten_payi"] - K["tavan_payi"]),
        #  m.5.2.5.7.3 — sınır, seçilen sığınma hacminin yüksekliğidir;
        #  ikisi ayrışmasın diye tek yerden okunur.
        ("c.2 - Kabin üstü / kuyu tavanının en alt kısmı arası",
         K["ust_hacim"][2] * 1000, SK - K["kabin_ust_donanim"] - K["tavan_payi"]),
        ("a - Revizyon kutusu / kuyu tavanının en alt kısmı arası",
         K["min_revizyon"],
         SK - K["kabin_ust_donanim"] - K["revizyon_payi"] - K["tavan_payi"]),
        ("b - Paten / halat bağlantısı - kuyu tavanı arası",
         bosluk, SK - K["kabin_ust_donanim"] - K["revizyon_payi"]
         - K["paten_payi"] - K["tavan_payi"]),
        ("Ç.2 - Karşı ağırlık üst pateni / rayın üst ucu arası",
         bosluk, c2_agirlik),
        ("a - Kuyu tabanı / kabinin en alt kısımları arası",
         K["min_kuyu_tabani"], a_dip),
        ("a.1 - Kuyu tabanı / kabin eteği arası",
         K["min_etek"], a_dip + K["etek_payi"] - K["etek_kotu"]),
        ("a.2 - Kılavuz raylar / kabinin en alt kısmı arası",
         K["min_ray_alt"], a_dip - g["kabin_tampon_baba"] + K["ray_alt_payi"]),
        ("b - Regülatör alt makarası / kabin en alt kısmı arası",
         K["min_regulator"], a_dip - K["regulator_payi"]),
    ]
    ad = [veri("", "En üst durak ( son kat ) yüksekliği", SK, "mm", "GİRİŞ", 0),
          hesap("Serbest boşluk = ( 0,1 + 0,035 × v² ) × 1000",
                f"( 0,1 + 0,035 × {tr(v)}² ) × 1000", bosluk, "mm",
                "TS EN 81-20 Çiz.2 + m.5.2.5.6.2"),
          metin("Kabin tavanı üzerindeki sığınma alanları  ( m.5.2.5.7 ) :",
                vurgu=True)]
    _kay(o, AD638=bosluk)
    uygunlar = []
    for i, (etiket, asgari, hesaplanan) in enumerate(satir):
        _kay(o, **{HUCRE[i]: hesaplanan})
        if i == 5:
            ad.append(metin("Kuyu boşluğundaki sığınma alanları  ( m.5.2.5.8 ) :",
                            vurgu=True))
        #  Standart "en az" der:  sınıra eşit ölçü de uygundur.
        uygun = hesaplanan >= asgari
        uygunlar.append(uygun)
        ad.append(veri("", etiket + "  ( en az " + trn(asgari, 0) + " mm )",
                       hesaplanan, "mm", "", 0))
        ad.append(kontrol(f"{trn(hesaplanan, 0)} mm  ≥  {trn(asgari, 0)} mm", uygun))

    #  Sığınma hacimleri  ( EN 81-20 Çizelge 3 — çömelmiş duruş )
    ust_h = (SK - K["kabin_ust_donanim"] - K["tavan_payi"]) / 1000.0
    for etiket, tip, (a, bb, c), olcu in (
            ("Ç.3 - Kabin üstünde sığınma hacmi", tip_ust,
             K["ust_hacim"], ((W + 40) / 1000.0, (D + 20) / 1000.0, ust_h)),
            ("Ç.4 - Kuyu dibinde sığınma hacmi", tip_dip,
             K["dip_hacim"], (W / 1000.0, D / 1000.0, a_dip / 1000.0))):
        uygun = a <= olcu[0] and bb <= olcu[1] and c <= olcu[2]
        uygunlar.append(uygun)
        ad.append(veri("", f"{etiket}   —   beyan edilen duruş :  {tip}"
                           f"  ( en az {tr(a)} × {tr(bb)} × {tr(c)} m )",
                       f"{tr(olcu[0])} × {tr(olcu[1])} × {tr(olcu[2])} m"))
        ad.append(kontrol(f"{etiket}  ( {tip} )", uygun))

    b = Bolum("SIĞINMA ALANLARI VE AÇIKLIKLARIN UYGUNLUĞU", kimlik="siginma_alanlari",
              kaynak="TS EN 81-20 m.5.2.5.7  /  m.5.2.5.8")
    b["adimlar"] = ad
    b["sonuc"] = {"baslik": "KONTROL      bütün sığınma ölçüleri",
                  "metin": "UYGUNDUR." if all(uygunlar)
                           else "UYGUN DEĞİLDİR — kuyu üst/alt boşluğunu artırın",
                  "uygun": bool(all(uygunlar))}
    b["aciklamalar"] = [
        "Kabin gövde yükseklikleri, etek ve revizyon kutusu payları ( 2400 · "
        "2100 · 500 · 400 · 950 · 270 · 150 mm ) kaynak Excel'in kabulleridir; "
        "TS EN 81-20 sayısı değildir. Farklı kabin imalatında SIGINMA "
        "sözlüğünden güncellenmelidir.",
        "Buna karşılık asgari açıklıklar ( 100 · 1000 · 500 · 500 · 100 · "
        "100 · 300 mm ) doğrudan TS EN 81-20 m.5.2.5.7 ve m.5.2.5.8'dendir. "
        "Ray dibi açıklığı, parça raya yatay XH ≤ 0,15 m uzaklıkta olduğu "
        "kabulüyle Şekil 7'den 0,10 m alınır; daha uzaktaki parçalar için "
        "sınır 0,30 m ( XH = 0,30 ) ve 0,50 m ( XH ≥ 0,50 ) olur.",
        "Serbest boşluğa eklenen 0,035 × v² terimi TS EN 81-20'de açıklığın "
        "değil, kabinin EN ÜST KONUMUNUN tanımındadır ( Çizelge 2 ). Burada "
        "kuyu ölçüleri anma konumundan alındığı için aynı eşitsizlik, terim "
        "sınıra eklenerek yazılmıştır — cebirsel olarak birebir aynıdır.",
        "SIĞINMA HACMİ TİPİ BİR BEYANDIR. TS EN 81-20 m.5.2.5.7.1 ve "
        "m.5.2.5.8.1 üç duruştan BİRİNİ ister: dik ( 0,40 × 0,50 × 2,00 m ), "
        "çömelme ( 0,50 × 0,70 × 1,00 m ) ve — yalnız kuyu dibinde — yatarak "
        "( 0,70 × 1,00 × 0,50 m ). Kontrol, GİRİŞ'te beyan edilen duruşa göre "
        "yapılır; seçilen duruş kuyu dibinde işaretlenmeli ve projede "
        "belgelenmelidir."]
    b["notlar"] = [
        f"Beyan edilen sığınma duruşu — kabin üstü : {tip_ust}   ·   "
        f"kuyu dibi : {tip_dip}."]
    return b


# =====================================================================
#  GİRİŞ NOKTASI
# =====================================================================
# =====================================================================
#  TAMPONLARIN KONTROLÜ            ( TS EN 81-20 m.5.8.1 / m.5.8.2 )
# =====================================================================
def _tamponlar(g, o):
    """Tampon tipinin hıza ve strokun beyan hızına uygunluğu.

    BU BÖLÜM ÖNCEDEN HİÇ YOKTU.  Program tampon geometrisini yalnız
    YERLEŞİM için okuyordu:  ezilme miktarı sığınma açıklıklarına ve halat
    boyuna giriyordu, ama tamponun o hız için YETERLİ olup olmadığı hiç
    sorulmuyordu.  2,5 m/s beyan hızında 90 mm'lik bir tampon sessizce
    "uygun" geçiyordu — lineer tamponda gereken strok 844 mm'dir.

    Standart üç ayrı kural koyar ve hangisinin geçerli olduğunu TAMPON TİPİ
    belirler ( bkz. mukavemet_tablolari.TAMPON_TIPLERI ):

        m.5.8.1.5    enerji biriktirmeli tampon  →  v ≤ 1 m/s
        m.5.8.2.1.1  lineer                      →  strok ≥ 0,135·v² , ≥ 65 mm
        m.5.8.2.2.1  enerji yutmalı              →  strok ≥ 0,0674·v²
        m.5.8.2.1.2  lineer olmayan              →  formül yok, TİP DENEYİ

    Lineer olmayan ( poliüretan ) tamponda strok bir bağıntıdan çıkmaz;
    m.5.8.2.1.2.1 yavaşlama ölçütlerini tip deneyine bırakır.  Orada
    denetlenebilen tek sayısal kural hız sınırıdır — bölüm bunu söyler ve
    strok için tip inceleme belgesine yollar.
    """
    v = g["beyan_hizi"]
    ad_t, biriktirmeli, katsayi = MT.tampon(g["tampon_tipi"])
    e_kabin = g["kabin_tampon_ezilme"]
    e_agirlik = g["agirlik_tampon_ezilme"]

    b = Bolum("TAMPONLARIN KONTROLÜ", kimlik="tamponlar",
              kaynak="TS EN 81-20 m.5.8.1 / m.5.8.2")
    ad = [
        veri("", "Tampon tipi", ad_t, "", "GİRİŞ"),
        veri("v", "Beyan hızı", v, "m/s", "GİRİŞ"),
        veri("", "Kabin tamponu strok ( ezilme ) miktarı", e_kabin, "mm", "GİRİŞ", 0),
        veri("", "Ağırlık tamponu strok ( ezilme ) miktarı", e_agirlik, "mm", "GİRİŞ", 0),
    ]
    uygunlar = []

    #  ── m.5.8.1.5  TİP / HIZ UYUMU ────────────────────────────────────
    hiz_uygun = (not biriktirmeli) or v <= MT.TAMPON_BIRIKTIRMELI_AZAMI_HIZ
    ad += [
        metin("Tampon tipinin beyan hızına uygunluğu  ( m.5.8.1.5 / m.5.8.1.6 ) :",
              vurgu=True),
        kontrol(
            (f"Enerji biriktirmeli tampon:  v = {tr(v)} m/s  ≤  "
             f"{tr(MT.TAMPON_BIRIKTIRMELI_AZAMI_HIZ)} m/s" if biriktirmeli else
             f"Enerji yutmalı tamponda hız sınırı yoktur  ( v = {tr(v)} m/s )"),
            hiz_uygun),
    ]
    uygunlar.append(hiz_uygun)

    #  ── STROK ────────────────────────────────────────────────────────
    if katsayi is None:
        #  Lineer olmayan:  strok bağıntısı yok, tip deneyi belirler.
        ad += [
            metin("Strok  ( m.5.8.2.1.2 ) :", vurgu=True),
            metin("Lineer olmayan tamponda strok bir bağıntıdan çıkmaz;  "
                  "m.5.8.2.1.2.1 ortalama yavaşlamanın 1 gn'yi, 2,5 gn üstü "
                  "sürenin 0,04 s'yi, tepe yavaşlamanın 6 gn'yi aşmamasını "
                  "ister ve bunları TİP DENEYİNE bırakır.  Tamponun beyan "
                  "yükü ( P + Q ) ve çarpma hızı için belgeli olduğu "
                  "AT tip inceleme belgesinden doğrulanmalıdır."),
        ]
        gereken = None
    else:
        gereken = katsayi * v * v * 1000.0            # m  →  mm
        alt = MT.TAMPON_ASGARI_STROK if biriktirmeli else 0.0
        gereken = max(gereken, alt)
        madde = "m.5.8.2.1.1.1" if biriktirmeli else "m.5.8.2.2.1"
        ad.append(metin(f"Gereken strok  ( {madde} ) :", vurgu=True))
        ad.append(hesap(
            f"s = {tr(katsayi)} × v² × 1000",
            f"{tr(katsayi)} × {tr(v)}² × 1000", katsayi * v * v * 1000.0, "mm",
            madde, 0))
        if biriktirmeli:
            ad.append(veri("", "En küçük strok  ( madde alt sınırı )",
                           MT.TAMPON_ASGARI_STROK, "mm", madde, 0))
            ad.append(hesap("s = max( hesap ; alt sınır )",
                            f"max( {trn(katsayi * v * v * 1000.0, 0)} ; "
                            f"{trn(MT.TAMPON_ASGARI_STROK, 0)} )",
                            gereken, "mm", ondalik=0))
        for etiket, e in (("Kabin", e_kabin), ("Ağırlık", e_agirlik)):
            iyi = isinstance(e, (int, float)) and e >= gereken - 1e-9
            ad.append(kontrol(
                f"{etiket} tamponu:  strok = {trn(e, 0)} mm  ≥  "
                f"{trn(gereken, 0)} mm", iyi))
            uygunlar.append(iyi)

    b["adimlar"] = ad
    b["aciklamalar"] = [
        "Tampon strokları YERLEŞİME de girer:  aynı sayı sığınma "
        "açıklıklarında ( m.5.2.5.7 / m.5.2.5.8 ) ve halat boyunda "
        "kullanılır — bkz. bölüm 'SIĞINMA ALANLARI'.",
        "TS EN 81-20 m.5.8.1.7:  lineer olmayan ve enerji yutmalı tamponlar "
        "GÜVENLİK BİLEŞENİDİR;  TS EN 81-50 m.5.5'e göre doğrulanır ve "
        "üzerinde tip inceleme belge numarası bulunur ( m.5.8.1.8 ).",
    ]
    tumu = all(uygunlar)
    if gereken is None:
        metni = ("Tip uygun — strok tip inceleme belgesinden doğrulanır."
                 if tumu else "UYGUN DEĞİLDİR — tampon tipi bu hıza uygun değil.")
    else:
        metni = ("UYGUNDUR." if tumu else
                 f"UYGUN DEĞİLDİR — en az {trn(gereken, 0)} mm strok gerekir.")
    b["sonuc"] = {"baslik": "KONTROL TİP · HIZ · STROK", "metin": metni,
                  "uygun": tumu}
    o.update(tampon_gereken_strok=gereken, tampon_biriktirmeli=biriktirmeli)
    return b


BOLUM_URETICILERI = (_motor, _makine, _kabin_alani, _aski_halatlari, _regulator,
                     _tahrik, _kabin_raylari, _agirlik_raylari, _kuyu_tabani,
                     _tamponlar, _siginma)


def hesapla(veriler=None):
    """Mukavemet hesabının tamamı.

    veriler   girdi sözlüğü ( engine.mukavemet_girdi.ALANLAR anahtarları ).
              Eksik alanlar Excel örneğinin varsayılanlarıyla tamamlanır.
    """
    g = MG.varsayilanlar()
    g.update(veriler or {})
    g = MG.tamamla(g)
    hata = MG.dogrula(g)
    if hata:
        return {"aktif": False, "hata": hata, "girdi": g}

    #  OFİS STANDARDI — uygulama projesinin KENDİ sabitleri ( avandan ayrı,
    #  bkz. engine/uygulama/sabitler.py ).  Bölümler bunu o["ofis"]'ten okur;
    #  ekrandaki Sabitler sekmesinde değiştirilen her değer buradan geçer.
    o = {"ofis": US.sabitler(g.get("_ofis"))}
    #  NUMARA BURADA VERİLİR, BÖLÜMÜN İÇİNDE DEĞİL.  Bölüm kendi adını ve
    #  değişmez kimliğini taşır;  kaçıncı sırada basılacağı onu kullanan
    #  projeye aittir — uygulama projesi bu on bölümün arkasına elektrik ve
    #  topraklama hesaplarını ekleyip hepsini yeniden numaralar.
    bolumler = [numarala(uret(g, o), i)
                for i, uret in enumerate(BOLUM_URETICILERI, 1)]
    uygunlar = [b["sonuc"]["uygun"] for b in bolumler
                if b.get("sonuc") and b["sonuc"].get("uygun") is not None]
    return {
        "aktif": True,
        "baslik": "ASANSÖR MUKAVEMET HESAPLARI",
        "girdi": g,
        "bolumler": bolumler,
        "sabitler": dict(SABIT),
        "ozet": {
            "N_hesap": o.get("N_hesap"), "motor_uygun": o.get("motor_uygun"),
            "Tst_hesap": o.get("Tst_hesap"), "Tst": o.get("Tst"),
            "tst_uygun": o.get("tst_uygun"),
            "kabin_alani": o.get("kabin_alani"), "kabin_kisi": o.get("kabin_kisi"),
            "Sf": o.get("Sf"), "S_gercek": o.get("S_gercek"),
            "ray_boyu": o.get("ray_boyu"), "Mg_kabin": o.get("Mg_kabin"),
            "Mg_agirlik": o.get("Mg_agirlik"), "Fk_kabin": o.get("Fk_kabin"),
            "FKR": o.get("FKR"), "FAR": o.get("FAR"),
            "Fkt": o.get("Fkt"), "Fat": o.get("Fat"),
            "tumu_uygun": all(uygunlar),
            "eksik_hesap": [b["eksik_hesap"] for b in bolumler if b.get("eksik_hesap")],
        },
        #  HESABI DURDURMAYAN UYARILAR  ( bkz. MG.uyarilar ).  λ > 250 gibi
        #  durumlar hesabı imkânsız kılmaz, yalnız bir kontrolü düşürür;
        #  sebebi paftada ve ekranda görünsün diye buradan taşınır.
        "uyarilar": MG.uyarilar(g),
        #  Kaynak Excel doğrulaması için  { hücre adresi : hesaplanan değer }
        "_h": o.get("_h", {}),
    }
