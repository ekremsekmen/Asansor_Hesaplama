# ASANSÖR PROJE PROGRAMI

Asansör projelerinin hesaplarını yapan, sonuçları **XLSX**, **PDF** ve **CAD**
olarak veren yerel program.  Açılışta hangi projenin hazırlanacağı seçilir:

| Bölüm | Kapsam | Kaynak |
|---|---|---|
| **AVAN PROJE** | Trafik hesabı · avan hesapları · proje kapağı | MMO/697 (2. Baskı, Ocak 2020) · TS EN 81-20 · ISO 8100-32:2020 · IEEE Std 80 · IEC 60364-5-52 |
| **UYGULAMA PROJESİ** | Mukavemet ( 10 bölüm ) + kabin ve kuyu aydınlatması, kurulu güç, gerilim düşümü, makine dairesi aydınlatması, temel topraklama | TS EN 81-20 · TS EN 81-50 · TS 12385-5 · ISO 7465 · MMO 208/4 · MMO 208/7 · IEEE Std 80 · IEC 60364-5-52 |

**Mukavemet tarafı avandan ayrıdır** — tabloları ve kabulleri kendi kaynağından
gelir. Elektrik ve topraklama hesapları ise avan projesindekilerin **aynısıdır**;
kopyalanmadı, aynı motor çağrılıyor ( `engine/avan/hesap.py` ). Sekme şeridi moda göre
değişir, yalnız **Sabitler / Ofis Standardı** iki modda da durur — ofis standardı
ikisinde de aynıdır.

### Ortak girdiler bir kez girilir

Mukavemet ile elektrik hesapları aynı büyüklüklerin çoğunu paylaşır. Aynı değeri
iki kez sormak yalnız zahmet değil, **hata kaynağıdır**: biri düzeltilip öteki
unutulduğunda iki hesap sessizce ayrışır ve pafta kendi içinde çelişir. Bu yüzden
ortak girdiler **yalnız mukavemet alanlarında** durur ve elektrik tarafına
kendiliğinden köprülenir:

| Girilen ( mukavemet alanı ) | Elektrik hesabında |
|---|---|
| Beyan yükü | Q |
| Beyan hızı | V |
| Boş kabin ağırlığı | Gk |
| Kabin derinliği | a ( kabin boyu ) |
| Kabin genişliği | b |
| Kuyu boyu ( durak listesinden ) | Hk |
| Motor gücü | Nsç |
| Askı oranı | i |
| Kabin rayı profili | gr ( ray metre ağırlığı ) |

Bu liste ekranda formun başında da yazılıdır. **Yalnız elektrik hesabına ait**
olan girdiler ( kuyu genişliği, kablo kesit ve uzunlukları, temel ölçüleri,
makine dairesi ) ayrı bir grupta toplanmıştır.

**Avanın motor gücü ve kuvvet hesapları uygulama projesine alınmaz:** motor gücünü
mukavemet bölüm 1 zaten MMO 208/7 §2.4'e göre hesaplar, kuvvetleri de bölüm 7-9
verir. İkisini birden basmak paftada iki farklı motor gücü gösterirdi.

Hesap motorları, ofisin mevcut Excel dosyalarındaki **her formülün birebir
Python karşılığıdır** — değerler hücre hücre karşılaştırılarak doğrulanmıştır.

**Sürüm 3.0** — **uygulama projesi eklendi.**

Program artık iki proje türü hazırlıyor. Açılışta hangisi olduğu seçiliyor;
sekme şeridi, girdiler ve çıktılar ona göre değişiyor.

| | Ne geldi |
|---|---|
| **Mukavemet** | 10 bölüm: motor gücü · makine konstrüksiyonu · kabin alanı · askı halatları · regülatör halatı · tahrik yeteneği ( 4 yük durumu ) · kabin kılavuz rayları ( C.2.1 / C.2.2 / C.2.3 ) · karşı ağırlık rayları · kuyu tabanı yükleri · sığınma alanları |
| **Elektrik ve topraklama** | Kabin ve kuyu aydınlatması, kurulu güç cetveli, gerilim düşümü, makine dairesi aydınlatması, temel topraklama. **Avan motoru çağrılıyor** — kopyalanmadı |
| **Ortak girdi köprüsü** | Kabin ölçüleri, beyan yükü, hız, kuyu boyu, motor gücü, askı oranı, ray profili **bir kez** giriliyor; elektrik tarafına kendiliğinden geçiyor |
| **Çıktılar** | Uygulama projesi PDF ( bütün bölümler tek paftada ) · Excel ( kaynak çalışma kitabı ) · CAD · revizyon akışı |

**Kaynak Excel'de yedi hata bulundu ve TS EN 81-20 / TS EN 81-50'ye göre
düzeltildi** — dördü hesabı olduğundan **iyi** gösteriyordu. Ayrıntısı 6.
bölümdeki tabloda; hepsi kodda `EXCEL_FARKLARI` altında standart maddesiyle
kayıtlı ve her biri için "gerçekten uygulanıyor mu" testi var.

**Teslim edilen Excel de düzeltiliyor.** Program kitaptan ayrıldığı için, kitap
olduğu gibi verilseydi aynı projenin iki belgesi birbirini yalanlardı. Teslim
kopyasında ilgili **formüller** düzeltiliyor ( değerler değil ), kitap kendi
kendini hesaplamaya devam ediyor. Doğrulama paketi ikisinin **hücre hücre aynı**
olduğunu denetliyor. Şablon dosyasına dokunulmuyor.

**Kod avan ve uygulama diye ayrıldı** — hesap motorları ( `engine/avan` ·
`engine/uygulama` ), HTTP uçları ( `api/avan.py` · `api/uygulama.py` ) ve arayüz
betikleri ( `avan.js` · `uygulama.js` ) ayrı dosyalarda. Ortak olan yalnız
gerçekten ortak olanlar ( bkz. 9. bölüm ). Ayrıştırmadan önce ve sonra doğrulama
paketi **aynı sayıyı** verdi — o gün 24.592 kontrol, tek bir hesap sonucu
değişmedi. ( Paket sonradan büyüdü;  bugünkü sayı 6. bölümdedir. )

**Doğrulama paketi 7 testten 11'e çıktı.** Yenileri: mukavemet tabloları ·
mukavemet motoru · mukavemet ↔ Excel ( girdi uzayı taraması ) · uygulama
projesi ( ortak girdi köprüsü ).

---

**Sürüm 2.0** — **tekli / çoklu ayrımı kalktı.  Yöntemi artık veri belirliyor.**

Trafik sekmesinde iki ayrı gövde ( tek hesap · grup hesabı ) ve aralarında seçim
yapan bir düğme vardı. Kullanıcının, hangi MMO yönteminin uygulanacağına karar
vermesi gerekiyordu — oysa bu karar **girdiden çıkarılabilir**. Artık öyle:

| | Önce | Sonra |
|---|---|---|
| **Ekran** | İki gövde; "asansör adedi 1" tek hesabı, "2-4" grup hesabını açıyordu | **Tek gövde.** Adet seçicisi duruyor ama anlamı değişti: *"Kaç asansör tanımlıyorsunuz"* — yöntem değil, veri |
| **Yöntem** | Kullanıcı seçiyordu | **Program çıkarıyor:** asansörlerin hepsi aynı tipse MMO/697 s.11-12 yolu ( `PAFTA` ), farklı tip varsa grup formülü ( `PAFTA-COKLU` ) |
| **1 asansör tanımı** | "kaç gerekir" hesabı | **Aynı** — eski davranışın birebir kopyası ( 87 senaryonun 87'sinde özet **bit bit aynı** çıktı ) |
| **2-4 aynı tip** | Yalnız "grup yeterli mi" derdi | Grup denetlenir **ve gerekli adet ayrıca yazılır** — 3 koyduysan "gerekli 2" görürsün. Bu bilgi eskiden hiç verilmiyordu |
| **Görünürlük** | — | Sonucun başında: *"Asansörlerin hepsi aynı tip — MMO/697 s.11-12 yolu. Üretilecek pafta: **PAFTA**"* Hangi yolun ve hangi Excel sayfasının kullanıldığı sessiz kalmıyor |

**Neden güvenli:** iki yolun özdeş asansörlerde aynı sonucu verdiği ölçüldü —
`ΣRi = n·R` ve `1/TReş = Σ(1/TRi) = n/TR` → `TReş = TR/n`, **fark 0,00e+00**.
Yani seçim hesabın doğruluğunu değil, yalnız **belgenin biçimini** belirliyor:
PAFTA türetmeyi adım adım yazar, PAFTA-COKLU asansör bazında tablo verir.
Motorun iki yolu da, Excel'in iki pafta sayfası da yerinde duruyor.

**Yol boyunca düzelen iki şey:** Excel'den geri yükleme artık tek forma doğru
oturuyor ( TEK sayfasının bina alanları ortak alanlara, asansör alanları 1.
kolona ); ve adet 2 → 1 → 2 gidip gelirken gizlenen kolonun değeri **silinmiyor**
( 10 + 16 kişilik grup korunuyor ) — hesaba yalnız görünen kolonlar girer.

**Sürüm 1.9** — dış denetimden gelen **dört bulgu** ölçülerek doğrulandı ve giderildi.

| Bulgu | Ölçülen davranış | Ne yapıldı |
|---|---|---|
| **S2 ( makine besleme ) akım bakımından hiç denetlenmiyordu** | 37 kW motor + **S2 = 1,5 mm²** : motor akımı **62,5 A**, kablonun taşıma kapasitesi **17,5 A** — program yine **"uygundur"** diyordu. Gerilim düşümü yakalamıyor: kısa hatta ε2 = %0,31. Bu kontrol **ofis Excel'inde de yok**. | Motor akımı I2 ve kablo kapasitesi Iz2 hesaplanıyor; yetersizse **⚠ uyarı** çıkıyor. Paftadaki `I ≤ Iz` satırı **kolon hattına ( S1 ) ait ve öyle kalmalı** — o hat asansörün toplam kurulu gücünü taşır. Sonuç satırı değiştirilmedi ki **XLSX ile pafta ayrışmasın**. |
| **Motor sigortası her güçte "4 x 25"** | Şablonda `G102` hücresinde **sabit metin**. 37 kW motorda akım ≈ 62 A, 110 kW'ta ≈ 186 A — üçünde de "4 x 25" yazıyordu. | **Motor akımından seçiliyor**: `In = P2 / ( √3 · U · cosφ )`, sigorta = kalkış katsayısı × In üstündeki ilk standart kademe ( IEC 60269 gG ). Katsayı **Sabitler → ③** altında, varsayılan **1,25** — bu katsayı ofisin 11 kW örneğinde yine **"4 x 25"** verir. Değer hem paftaya hem **XLSX'e** yazılıyor; şablon hücresi metin olduğu için Excel'e formül eklenmedi. |
| **Ekran reddediyor, indirme üretiyor** | `1.200` gibi belirsiz yazım ekranda reddediliyordu ama **trafik-XLSX, avan-XLSX ve avan-PDF** aynı girdiyle dosya üretiyordu; sayı boşa çevrildiği için hücre **boş** kalıyor, eksik girdili pafta teslim edilebilir hâlde çıkıyordu. | Beş indirme ucunun **hepsi** artık ekranla aynı kapıdan geçiyor. |
| **Kabin kuyuya sığıyor mu diye bakılmıyordu** | Kuyu 1500 mm + kabin 2100 mm sessizce hesaplanıyordu. | `kabin genişliği ≥ kuyu genişliği` ise **⚠ uyarı**. Asgari boşluk **dayatılmıyor** — kapı tipine, ray ve karşı ağırlık konumuna göre değişir. |

**Sürüm 1.8** — **şerit boyu artık girdi değil, temel ölçülerinden türetiliyor.**

Ofiste temel topraklama hesabı için **yalnız uzunluk ve genişlik** giriliyor;
elektrik projesinin topraklama planına avan aşamasında bakılamıyor. Program
artık aynı şekilde çalışıyor.

| Konu | Ne değişti |
|---|---|
| **L — şerit boyu boş bırakılır** | Alan boş kalırsa band boyu temel ölçülerinden hesaplanır: band temelin çevresini **kapalı ring** olarak dolaşır, 20 m'yi aşan kenarlarda gözler **20 × 20 m**'yi geçmeyecek şekilde **enine bağ** atılır — <b>L = 2·( a + b ) + enine bağlar</b>. Kullanılan sayı ve açılımı alanın altında görünür ( ör. `ring 99,90 m + enine bağ 1 × 18,90 = 118,80 m` ). |
| **Girilen boy türetileni ezer** | Topraklama planı çizildiğinde plandaki gerçek boy yazılır; program o değeri kullanır. **Pafta değişmez** — boyun elle mi girildiği yoksa türetildiği mi teslim edilen hesaba yazılmaz, L her zaman sıradan bir girdi satırıdır. Kaynak bilgisi yalnız ekranda, alanın altında görünür. |
| **Karelaj gözü ofis sabiti oldu** | **Sabitler → ④ Temel Topraklama** grubuna `Karelaj gözü (m)` eklendi ( varsayılan **20** ). Ofis başka bir aralık kullanıyorsa bir kez değiştirilir. |
| **"Tahmin et" düğmesi kalktı** | Düğmeye basmayı unutma ihtimali ortadan kalktı; türetme kendiliğinden ve **motorun içinde** yapılıyor — arayüzde ikinci bir formül kopyası yok. |
| **XLSX yine kendi başına doğru** | Türetilen boy indirilen dosyanın **GİRİŞ!C13** hücresine yazılır; Excel'i tek başınıza açsanız da aynı Ry / Rç / Re çıkar. Şablonda değişiklik yok. |

Ofisin kendi paftasıyla ( 31,05 × 18,90 m · β = 150 Ω·m · L = 140 m · Is = 4 )
karşılaştırıldı: **Ry = 3,82 Ω · Rç = 25,00 Ω · Re = 3,310 Ω · Re max = 166,67 Ω**
— birebir aynı. Aynı temel için türetilen boy **118,80 m** ve Re **3,45 Ω**;
sınır 166,67 Ω olduğundan **sonucu değiştirmiyor** — boydaki tahmin payı bu
kontrolü etkilemeyecek kadar küçük kalıyor.

**Sürüm 1.7** — bu sürümde giderilen **geçersiz girdi** açıkları:

Dış bir denetimde, hesabın "normal" girdilerde Excel ile birebir tuttuğu ama
**geçersiz girdi yollarında** programın yanlışlıkla "uygun" sonucu verebildiği
altı nokta bulundu. Altısı da doğrulandı ve giderildi; her biri için pakete
kalıcı test eklendi.

| Bulgu | Ne oluyordu | Ne yapıldı |
|---|---|---|
| **Manuel ta / tk / tg / tp sıfır veya negatif girilebiliyordu** | Dördü de `0` iken 44 daireli örnekte program 2 yerine **1 asansör yeterli** dedi ( TR = 24,5 sn ). Hesabın içinde fiziksel olarak imkânsız **ts = −1,88 sn** oluşuyordu. | Süreler için fiziksel aralık denetimi ( ta/tk 0,1-30 sn · tg 0,1-60 sn · tp 0,1-20 sn ). Tek ve çoklu hesapta, çokluda ayrıca asansör bazında. |
| **Çoklu hesap bina girdilerini doğrulamıyordu** | `h = −3 m` ile hata vermeden **"Yükseltilmiş kriteri karşılanıyor"** çıkıyordu; bina/yapı yüksekliği boşken sessizce "Standart" sınıfına düşüyordu. Tek asansör hesabı aynı girdileri reddediyordu. | Bina girdileri denetimi **tek yapılıp iki yolda da** kullanılıyor: N, h, bina ve yapı yüksekliği. |
| **Belirsiz sayı yazımı** | Türkçede `1.200` = bin iki yüz, `1,200` = bir virgül iki. Program ikisini de **1,2** okuyordu: 1.200 daireli bir binada gerekli asansör adedi **41 yerine 2** çıkıyordu. | Bu yazım artık **reddediliyor** ve ne yazılması gerektiği söyleniyor. `0,075` gibi sıfırla başlayan ondalıklar etkilenmez — binlik ayracı sıfırdan sonra gelmez. |
| **Avanda elle girilen yük / ağırlık / verim sınırsızdı** | `Q elle = 0` ile motor gücü **0 kW**, otomatik motor **2,2 kW** ve sonuç "uygun" oluyordu. `Gk elle` negatif olabiliyor, `η = 10` girilince motor gereksiz küçülüyordu. | Q elle ve Gk elle 50-20.000 kg, η 0,05-1,00 aralığında olmalı; dışı hesabı durdurur. |
| **Tablo-11 dışı yükte boş kabin kütlesi sessizce sabitleniyordu** | `Q = 5.000 kg` için de `Gk = 1.900 kg` kullanılıyordu ( tablonun üst ucu ). Kuvvet hesapları olduğundan küçük çıkıyordu. | Tablo-11 kapsamı ( 450-2.500 kg ) dışında **`Gk elle` zorunlu**; verilmezse hesap durur ve sebebi yazılır. |
| **Denge faktörü q = 1 kabul ediliyordu** | `q = 1` iken N = (1−q)·… = **0 kW** çıkıyor, 2,2 kW motor "uygun" görünüyordu. | Sert sınır **0,20 - 0,80**; dışı reddedilip varsayılana dönülür ve **uyarı** çıkar. Uygulama bandı 0,40 - 0,55; dışı hesabı durdurmaz ama paftaya gerekçe yazılmasını ister. |

Ayrıca: aralık dışı bırakıldığı için **varsayılana dönülen her alan** ( gr, Fmk,
Fsh, S1, S2, L2, Nsç, L1, i, q ) artık **uyarı üretir** — kullanıcı bir sayı
yazıp programın başka bir sayı kullandığını fark etmeden kalamaz.

**Sürüm 1.6** — önceki sürümde eklenenler:

| Konu | Ne değişti |
|---|---|
| **C ) Ofis Varsayılanları** | Asansörden asansöre, projeden projeye **değişmeyen** 15 değer tek bir kartta toplandı ( Sabitler sekmesi ): U · κ · εmax · ray birim kütlesi · makine ve sehpa ağırlığı · kolon ve besleme kesiti · besleme uzunluğu · kablo tipi · L1 payı · toprak özgül direnci · çubuk adedi · kat yüksekliği · kapı tipi. **Bir kez ayarlanır**, her yeni asansör ve her yeni proje bunları kullanır. |
| **Asansör kartı sadeleşti** | Ray, makine, sehpa, kesitler, kablo ve L1 kartta doğrudan durmuyor; **"Ofis standardından farklı değerler"** katlanır bölümüne indi. Boş bırakıldıklarında ofis standardı kullanılır; yalnız o asansörde farklı bir değer gerekiyorsa doldurulur ve başlıkta **"n özel"** rozeti çıkar. Paftada değerin kaynağı ( GİRİŞ — asansör bazında / OFİS VARSAYILANI ) yazılır. |
| **U, κ, εmax avan panelinden kalktı** | Projeden projeye değişmedikleri için ofis varsayılanına taşındı. **β ve çubuk adedi** yerinde bırakıldı ( zemin ölçümü arsadan arsaya değişir ) ama artık boş bırakılabiliyor — yer tutucu ofis değerini gösteriyor. |
| **Nsç motor gücü otomatik** | Boş bırakılırsa hesaplanan güçten büyük **ilk standart anma gücü** seçilir ( IEC 60072 / TS EN 60034: 2,2 · 3 · 4 · 5,5 · 7,5 · 11 · 15 · 18,5 · 22 · 30 · 37 · 45 kW ). ⚠ Excel'inizdeki örnekte 16 kişilik asansör **N = 13,33 kW** hesaplanıyor ama **Nsç = 11 kW** yazılıydı — pafta "UYGUN DEĞİL" veriyordu. Program artık **15 kW** seçiyor. |
| **L1 kolon hattı uzunluğu** | Boş bırakılırsa **L1 = kuyu yüksekliği + ofis payı** ( varsayılan 3,5 m ). Plandan ölçülen değer farklıysa elle yazılır. |
| **Çubuk adedi uyuşmazlığı** | Program **0**, Excel'iniz **4** diyordu. Ofis varsayılanı **4** oldu. |
| **Q ve Gk artık girdi değil** | Kapasiteyi seçince anma yükü **Tablo-7**'den, boş kabin kütlesi de **Tablo-11**'den kendiliğinden geliyor ve kartta **gri, salt okunur** olarak görünüyor — sarı ( elle doldurulan ) alan değiller. Tablo dışı bir yük gerekirse **Q elle** / **Gk elle** katlanır bölümde duruyor; girildiğinde üstteki satır girilen değeri gösterir, yani hep hesapta kullanılan değer görünür. |
| **Sabitler hesap bazında gruplandı** | "B) Ofis Standardı" ve "C) Ofis Varsayılanları" **tek panelde** birleşti ve alanlar **hangi hesaba girdiklerine göre** ayrıldı: ① Motor gücü ve kuvvetler · ② Aydınlatma · ③ Kurulu güç ve gerilim düşümü · ④ Temel topraklama. Her grubun başlığında hangi hesap ve hangi kaynak olduğu yazılı. Bir sabit gruba yazılmayı unutulursa **DİĞER** başlığı altında görünür — sessizce kaybolmaz. |
| **Kat yüksekliği ve kapı tipi ait olduğu yere döndü** | v1.6'da ofis varsayılanı yapılmışlardı; **her projede değiştiği için** geri alındı. İkisi de yalnız **Trafik Hesabı** sekmesinde. Sabitler panelindeki "askı oranı buradan kaldırıldı" bilgi bandı da kalktı — bu bilgi artık kart başlığındaki ( ! ) balonunda. |
| **β ve çubuk adedi ofis standardına taşındı** | Avan panelindeki **β — toprak özgül direnci** ve **Is — çubuk topraklayıcı adedi** kaldırıldı; ④ Temel Topraklama grubundalar. Zemin etüdü varsa oradan değiştirilir ve değer o projenin dosyasıyla saklanır. **L — şerit boyu** avan panelinde kaldı ( v1.8'de temel ölçülerinden türetilir oldu ). |
| **İki farklı L ayrıştırıldı** | Topraklamadaki **L ( şerit boyu )** ile asansördeki **L1 ( kolon hattı )** karışıyordu. L'nin etiketine "topraklama" eklendi ve ( ! ) balonunda farkı yazıldı; balonda temel çevresi de karşılaştırma olarak veriliyor. **L1'in yer tutucusu artık hesaplanan sayıyı gösteriyor** — `42,00 ( Hk + 3,50 )` — kuyu yüksekliğini değiştirince o da değişiyor. |
| **Manuel k ve manuel V ana akıştan kalktı** | Çoklu asansör gövdesinde ortada duruyorlardı; artık katlanır **"Manuel değerler"** bölümünde. Elle bir değer girilirse başlıkta **"n elle"** rozeti çıkar — gizlenen bir ezme sessiz kalmaz. Tek asansör gövdesinde zaten "İleri seçenekler" altındaydılar, oraya da rozet eklendi. |
| **Çokluda manuel k sessizce yok sayılıyordu** | Tablo-9'da değeri olan bir bina tipinde çoklu hesap, girilen manuel k'yı **görmezden geliyor ve hiçbir şey söylemiyordu**. Artık tek asansör hesabındaki gibi açıkça reddediliyor. Kamu binası ve Tablo-9'da olmayan bina tipleri ( karma, poliklinik, katlı otopark ) için manuel k yine geçerli. |
| **Şablon denetimi** | Yanlış ya da eski bir Excel `templates/` klasörüne konursa program yine dosya üretiyordu — hesap doğru olduğu için ekranda belirti çıkmıyor, hata yalnız teslim edilen paftada görünüyordu. Artık üç katmanlı denetim var ( sayfalar · girdi hücreleri · şablonun içindeki tablo değerleri ) ve **denetimden geçmeyen şablonla XLSX ÜRETİLMEZ**. Sabitler sekmesinde **Şablon durumu** kartı, komut satırında `python3 araclar/sablon_denetle.py`. |
| **XLSX kendi başına doğru** | İndirilen dosyanın **GİRİŞ hücrelerine, motorun gerçekten kullandığı değer yazılır** — boş bırakılan ofis alanları, otomatik seçilen Nsç / L1 ve aralık dışı olduğu için reddedilenler dâhil. Excel'i tek başına açsanız da ekrandakiyle aynı sonucu verir. Şablonda hiçbir değişiklik yapılmadı. |

**Sürüm 1.5** — daha önce eklenenler:

| Konu | Ne değişti |
|---|---|
| **Asansör adedi tek yerde** | Avan sekmesindeki asansör adedi artık **trafik hesabından gelir** ve kendiliğinden eşitlenir — tek tek "kullan" kutusu işaretlemek yok. **1 asansör** seçiliyken trafik hesabının *bulduğu* adet ( "yetmiyor, 3 gerekir" derse avanda 3 kart açılır ), **2–4** seçiliyken grupta tanımlanan adet. Trafik adedinin **altına inilemez**: gruptaki her asansörün elektrik hesabı da yapılmalıdır. |
| **Trafik grubu dışı asansör** | Binada trafik hesabına girmeyen ayrı bir yük ya da sedye asansörü varsa avandaki adet **elle artırılır**. Fazlalar **trafik grubu dışı** diye etiketlenir: kurulu güce ve gerilim düşümüne girer, trafik kontrolüne girmez — pafta bunu **not** olarak yazar ( uyarı olarak değil ). |
| **Kapasite ve hız trafiği izler** | Avandaki kapasite ve hız, trafik hesabındaki değer **değiştiğinde kendiliğinden güncellenir** — düğmeye basmayı unutma diye bir şey kalmadı. Elle başka bir değer girerseniz o değer **korunur** ( trafik yeniden değişene kadar ) ve program farkı uyarı olarak yazar; **↧ Trafikten güncelle** istediğiniz an trafiğe döndürür. |
| **Askı oranı Sabitler'den kalktı** | "B) Ofis Standardı" panelinde hâlâ **i — Palanga ( askı ) katsayısı** duruyordu; oysa v1.4'te asansörün kendi girdisi olmuştu. Panelden kaldırıldı, yerine nereye taşındığını söyleyen bir not kondu. Excel'deki `SABİTLER!C22` yalnız boş bırakılan kolon için **yedek** olarak duruyor. |
| **Kabin hızında sessiz varsayım kalktı** | Avan hız listesi artık boş başlar; değer trafikten gelir ya da elle seçilir. Önceden hiç dokunulmayan alan sessizce **1,60 m/s** kabul ediliyordu. |
| **Grup tanımı korunuyor** | Adet 2 → 1 → 2 gidip gelindiğinde gruptaki farklı kapasiteler ( ör. 10 + 16 kişilik ) artık silinmiyor; yalnız 1. kolon tek hesaptaki tanımı alır. |

**Sürüm 1.4** — daha önce eklenenler:

| Konu | Ne değişti |
|---|---|
| **Tek trafik sekmesi** | "Trafik Hesabı" ve "Çoklu Asansör Trafik" birleşti. Üstteki **asansör adedi** seçicisinden 1–4 arası seçiyorsunuz: **1** → program tek asansörün yetip yetmediğini söyler ve **yetmiyorsa kaç adet gerektiğini hesaplar**; **2–4** → her asansör ayrı tanımlanır, grup kontrolü ( Reş ≥ B·k, TReş ≤ Izul ) yapılır. Adet değişince ortak bina girdileri korunur. Tek hesap "n adet gerekir" dediğinde tek tıkla o gruba geçilir. |
| **Makine tipi ve askı oranı** | Asansörün normal girdisi oldu. **Makine tipi** ( dişlisiz / dişli ) seçilince η, MMO/697 s.21 değeriyle ( 0,85 / 0,50 ) kendiliğinden dolar. **Askı oranı** ( 1:1 / 2:1 ) Sabitler'den kalktı; artık kapasite ve hız gibi asansöre ait. |
| **Toplam sistem verimi** | İmalatçı kataloğundan gelen ( dişli 1:1 ≈ 0,60 · dişlisiz 2:1 ≈ 0,82 gibi ) **toplam** verim değerleri kullanılabiliyor: asansörün altındaki kutu işaretlenince MMO/697 §2.4'teki palanga düşüşü ikinci kez uygulanmaz ve paftada hangi esasın kullanıldığı yazılır. |
| **Makine dairesi yok ( MRL )** | Ölçülere 0 yazmak yerine açık işaret kutusu. İşaretliyken ölçü alanları kapanır ve pafta "makine dairesiz sistem" der; işaretli değilken ölçü boşsa program uyarır. |

**Sürüm 1.3** — daha önce eklenenler:

| Konu | Ne değişti |
|---|---|
| **Bodrum durağı** | Ana giriş altındaki duraklar artık girilebiliyor. Tablo-2 asgari hızı `N + 1 + Nb` durak adedinden seçilir; H, S ve TR (MMO tanımı gereği) değişmez. Tek ve çoklu sayfada, çokluda asansör bazında. |
| **Kapı genişliği boşlukları** | 1000 ve 1200 mm (Tablo-4) ile 700 mm (Tablo-8) artık hesaplanıyor — komşu satırlardan enterpolasyon / dış değerleme, kaynağı paftada belirtiliyor. Listedeki yedi genişliğin tamamı çalışıyor. |
| **Askı ve denge asansör bazında** | Palanga katsayısı (i) ve denge faktörü (q) artık η gibi asansöre özel; dişlili + dişlisiz karışık projeler doğru hesaplanıyor. |
| **Çokluda imalatçı süreleri** | ta / tk / tg / tp asansör bazında elle girilebiliyor (tek sayfadaki imkânın karşılığı). |
| **Erişilebilirlik uyarısı** | 630 kg altı kabin ve 800 mm altı kapı TS EN 81-70 / TS 9111 ölçütüyle uyarılıyor; öneri sıralamasındaki kural da buna bağlandı. |
| **Kamu binası** | Hem %k hem hız varsayımı paftaya yazılıyor. |
| **15 kişi / 1125 kg** | Tablo-7'ye açık istisna olarak yazıldı, kaynağı paftada ayrı gösteriliyor. |
| **Trafik ↔ avan bağı** | Kapasite, hız ve kuyu yüksekliği trafik hesabıyla karşılaştırılıyor; tutarsızlık uyarı olarak çıkıyor. |
| **Arayüz** | Sekme başlığında uyarı sayısı rozeti; avan uyarıları artık ekranda da görünüyor (önceden yalnız PDF'te vardı). |
| **( ! ) açıklama simgeleri** | Yöntemi anlatan uzun metinler — Tablo kuralları, bodrumun H ve S'ye neden girmediği, ara değerlerin nasıl türetildiği — ekranda başlık ve alan adlarının yanındaki **( ! )** dairesine toplandı; üzerine gelince (dokunmatikte tıklayınca) açılıyor. **⚠ uyarılar buraya girmez**, karar gerektirdikleri için açıkta durur. Paftaya ve PDF'e bu metinler yine tam basılır. |
| **Excel biçimi** | Yeni ve güncellenen uzun açıklama notları Excel'de kırpılıyordu — satır kaydırma açıldı, satır yükseklikleri verildi; ÇOKLU sayfasındaki gizli yardımcı alan gizlendi. |
| **Pafta biçimi** | İki satıra düşen bölüm başlığı mavi bandın dışına taşıyordu; band artık başlıkla birlikte büyüyor. Uyarı kutusunda çift ⚠ görünmesi giderildi. |

---

## 1. Kurulum ve çalıştırma

### macOS
`baslat.command` dosyasına **çift tıklayın.**

İlk açılışta kendi kurulumunu yapar (yaklaşık 1 dakika, internet gerekir);
sonraki açılışlarda doğrudan başlar. Tarayıcı kendiliğinden açılır.

> macOS "geliştirici doğrulanamadı" uyarısı verirse: dosyaya **sağ tık → Aç**
> deyip bir kez onaylayın. Bundan sonra çift tıklama yeterlidir.

### Windows
`baslat.bat` dosyasına **çift tıklayın.** (Python kurulu değilse uyarır.)

### Kapatmak
Açılan siyah pencerede **Ctrl + C**, ya da pencereyi kapatın.

**Program tümüyle sizin bilgisayarınızda çalışır.** İlk kurulumdan sonra
internet gerekmez; hiçbir veri dışarı gitmez.

---

## 2. Program nasıl çalışır

| Sekme | Ne yapar | Excel karşılığı |
|---|---|---|
| **Proje Bilgileri** | Pafta antedi, proje kaydet/aç | — |
| **1 · Trafik Hesabı** | **Adet 1** — tek tip asansör: kaç adet, kaç kişilik, hangi hız | `HESAPLAMA` → `PAFTA` |
| **1 · Trafik Hesabı** | **Adet 2–4** — farklı kapasitede asansör grubunun kontrolü | `ÇOKLU ASANSÖR` → `PAFTA-COKLU` |
| **2 · Avan Hesapları** | 1–4 asansör: motor, kuvvetler, aydınlatma, kurulu güç, gerilim düşümü + makine dairesi + topraklama | `1–4 NOLU ASANSÖR`, `MK.DAİRESİ AYD.`, `TOPRAKLAMA`, `ÖZET` |
| **Sabitler / Ofis Standardı** | Palanga, denge faktörü, armatür, priz, cosφ… | `SABİTLER` B bölümü |
| **Tablolar** | Kullanılan tüm tablolar ve kaynakları | `TABLOLAR` |

**Uygulama projesi** modunda tek adım vardır:

| Sekme | Ne yapar | Excel karşılığı |
|---|---|---|
| **1 · Uygulama Hesapları** | 82 girdi → 14–18 hesap bölümü. **Mukavemet ( 1–10 ):** motor gücü · makine konstrüksiyonu · kabin alanı · askı halatları · regülatör halatı · tahrik yeteneği · kabin kılavuz rayları · karşı ağırlık rayları · kuyu tabanı yükleri · sığınma alanları. **Elektrik ( 11– ):** kabin ve kuyu aydınlatması · kurulu güç cetveli · gerilim düşümü ve kesit kontrolü · makine dairesi aydınlatması · temel topraklama | `MUKAVEMET_HESABI.xlsx` → `Veri Girişi`, `11-Muk. Hesapları`, `Askı Tipleri`  ·  `ASANSOR_AVAN_HESAPLARI.xlsx` → `1 NOLU ASANSÖR`, `MK.DAİRESİ AYD.`, `TOPRAKLAMA` |
| **Sabitler / Ofis Standardı** | Armatürler, priz, cosφ, U, κ, εmax, β, çubuk sayısı — elektrik ve topraklama hesapları buradan beslenir | `SABİTLER` B bölümü |

Sonuçlar **yazdıkça** hesaplanır; kaydet düğmesi yoktur.
**Sarı zeminli** alanlar sizin doldurduğunuz girdilerdir; boş bırakılan
opsiyonel alanlar tablo değerini kullanır.

### Tipik akış

1. **Proje Bilgileri** — proje adı, işveren, pafta no.
2. **1 · Trafik Hesabı** — üstteki **asansör adedi** seçicisiyle başlayın.
   **1** seçiliyken bina tipi, yükseklikler, kat sayısı, daire sayısı, kabin
   kapasitesi ve kapı bilgilerini girin; program kaç asansör gerektiğini bulur.
   *Otomatik öneri tablosu* hangi kabin–hız birleşiminin kaç asansör
   gerektirdiğini yan yana gösterir.
   → Farklı kapasitede bir grup kuracaksanız adedi **2–4** yapın; her asansör
   ayrı tanımlanır ve grup kontrolü yapılır.
3. **2 · Avan Hesapları** — asansör adedi, kapasite ve hız buraya
   **kendiliğinden** gelir ve trafikte bir şey değişirse **kendiliğinden
   güncellenir**. Kuyu/kabin ölçüleri, ağırlıklar ve kablo bilgilerini girin.
   Trafik hesabına girmeyen ayrı bir yük ya da sedye asansörü varsa adedi
   elle artırın.
4. **PDF indir** / **XLSX indir**.

### Uygulama projesi akışı

1. Açılış ekranından **UYGULAMA PROJESİ**'ni seçin.
2. **Proje kimliği** — proje adı, işveren, pafta no. ( Yalnız dosya adında ve
   belge özelliklerinde kullanılır; uygulama projesi kapağı MMO'nun **ayrı**
   kitabına aittir, avan kapağı buraya basılmaz. )
3. **Uygulama projesi girdileri** — on grup. İlk dokuzu mukavemet ( 71 alan ),
   sonuncusu yalnız elektrik hesaplarına ait olanlar ( kuyu genişliği, kablo
   kesit ve uzunlukları, temel ölçüleri, makine dairesi ). Mukavemet alanlarının
   etiketinin
   yanında kaynak Excel'deki **hücre adresi** yazılıdır ( `C59`, `E73`… ), kâğıttan
   giren için. Hücre adresi **olmayan** alanlar programın kendi eklediği
   girdilerdir ( paten balatası uzunluğu, *"ofis verimi toplam sistem
   verimidir"*, karşı ağırlıktaki güvenlik tertibatı, tertibatı devreye sokma
   kuvveti ); teslim edilen kitaba ayrı bir blokta yazılır ve oradan geri okunur.
   **Durak yükseklikleri** kendi düzenleyicisindedir ( ekle / sil, en çok 20 ).
   *Seyir mesafesi* ve *son kat yüksekliği* bu listeden **kendiliğinden** dolar —
   Excel'de ikisi de elle giriliyor ve sessizce çelişebiliyordu.
   **Kabin ağırlığı da beyan yükünü izler:** yükü değiştirdiğinizde ofis
   tablosundan dolar ( 1275 kg → 1100 kg ). Elle yazdığınız değer, beyan yükünü
   yeniden değiştirene kadar korunur — avan tarafındaki *trafik → kapasite*
   izlemesinin aynısıdır. Tablo **tahmindir**, standardın sayısı değildir;
   kesin tasarımda imalatçı verisiyle değiştirin ( bkz. §7 ).
   **Regülatörün "devreye sokma kuvveti"** imalatçının tip inceleme
   belgesinden gelir; girilmezse o madde denetlenemez ve bölüm
   *"HESAP EKSİK"* der — proje *uygundur* çıkmaz ( bkz. §7 ).
4. Sağ panelde bütün bölümler, hangisinin takıldığı, **kuyu tabanına gelen
   yükler** ( inşaat projesine bildirilecek FKR · FAR · Fkt · Fat ), asansörün
   kurulu gücü, gerilim düşümü ve topraklama direnci görünür.
5. **PDF** ( bütün hesaplar tek paftada ) / **Excel** ( uygulama projesinin
   kendi kitabı ) / **CAD** indirin.

> Topraklama hesabı için temel ölçüleri, gerilim düşümü için kolon hattı
> uzunluğu girilmelidir; boş bırakılırsa o bölümler paftaya girmez ve program
> bunu söyler. Makine dairesiz ( MRL ) sistemde kutuyu işaretli bırakın.

---

## 3. Çıktılar

### Program Excel'e bağımlı mı?

**Hesabın kendisi Excel'den tümüyle bağımsızdır.** MMO/697, TS EN 81-20,
ISO 8100-32 ve IEC tablolarının tamamı ile her formül `engine/` klasöründe
Python olarak yazılıdır. Bilgisayarda Excel kurulu olmasa bile program çalışır,
sonuçları ekranda gösterir ve **PDF paftasını üretir**.

Excel yalnız **tek bir yerde** devrededir: `templates/` klasöründeki üç dosya,
**XLSX çıktısının şablonudur.** Program o dosyayı açıp girdi hücrelerini
doldurur; sonuç değerlerini dosyanın kendi formülleri, siz Excel'de açtığınızda
hesaplar.

| | Şablon gerekir mi? | Excel kurulu olmalı mı? |
|---|---|---|
| Ekranda hesap | hayır | hayır |
| PDF çıktısı | hayır | hayır |
| XLSX çıktısı | **evet** — `templates/` içindeki üç dosya | hayır (üretmek için); açmak için Excel/LibreOffice/Numbers |

Bu bilinçli bir tercihtir: çıktının ofis paftasıyla **birebir** kalmasını
garanti eder ve Excel'inizde biçim değişikliği yaptığınızda program çıktısı da
kendiliğinden değişir. Şablon dosyaları silinirse program çökmez — XLSX
indirmede anlaşılır bir uyarı verir, hesap ve PDF çalışmaya devam eder.

### XLSX — şablon yöntemi
Program **sıfırdan tablo üretmez**. Ofisin kendi Excel dosyasını şablon olarak
açar, yalnız girdi hücrelerini doldurur ve kaydeder. Böylece:

- tüm sayfalar (`PAFTA`, `ÇOKLU ASANSÖR`, `1–4 NOLU ASANSÖR`, `ÖZET` …),
  formüller, işlem adımları ve sayfa biçimi **birebir korunur**;
- dosya Excel'de açıldığında **kendiliğinden yeniden hesaplanır**;
- ofis şablonu değişirse program çıktısı da kendiliğinden değişir —
  `templates/` klasöründeki dosyaları güncellemeniz yeterlidir.

**Her projenin kendi çalışma kitabı vardır ve karışmaz:**

| Proje | Çalışma kitabı |
|---|---|
| Avan | `ASANSOR_TRAFIK_HESABI_v2_1.xlsx` · `ASANSOR_AVAN_HESAPLARI.xlsx` |
| Uygulama | `MUKAVEMET_HESABI.xlsx` |

Uygulama projesinin elektrik ve topraklama hesapları avan **motorunu** kullanır
( kod kopyalanmadı ) ama avan **kitabını** çıktı olarak vermez — o kitap avan
projesine aittir. Uygulama tarafında bu hesaplar ekranda ve **PDF paftasında**
verilir.

**Mukavemet çıktısında yöntem biraz farklıdır:** program yeni bir kitap kurmaz,
**kaynak çalışma kitabının kendisini** teslim eder — girdiler "Veri Girişi"
sayfasına yazılır, **1115 formül yerinde kalır**, dosya açıldığında Excel kendi
hesabını yapar. Böylece projeci programın sonucunu kitabın kendi formülleriyle
karşılaştırabilir; iki doğruluk kaynağı yaratılmamış olur.

### PDF — baskıya hazır pafta
Sayfa düzeni Excel'deki işlem akışını izler: başlık → girdi satırları →
denklem → sayıların yerine konmuş hâli → sonuç → kontrol → notlar.
Antet, kaynak referansları, sayfa numarası ve imza kutusu içerir.

---

## 4. Revizyon — Excel'den proje aç

**Programın ürettiği XLSX, girdileri de taşır.** Aylar sonra projede bir şey
değiştiğinde (kat eklendi, kuyu genişledi, kapasite değişti) hiçbir şeyi baştan
girmezsiniz:

1. **Proje Bilgileri** sekmesindeki bırakma alanına, proje klasörünüzdeki
   Excel'i sürükleyin — trafik ve avan dosyalarını **birlikte** bırakabilirsiniz.
   Uygulama projesinde aynı işi mukavemet sayfasındaki **"Revizyon — Excel'den
   aç"** alanı yapar; oraya programın ürettiği mukavemet kitabını da,
   elinizdeki **özgün** kitabı da bırakabilirsiniz — girdiler ikisinde de aynı
   hücrelerdedir.
2. Bütün girdiler yerine oturur, hesaplar anında yeniden yapılır.
3. Değişen değeri düzeltin.
4. Güncel **PDF ve XLSX**'i yeniden indirin, paftaya koyun.

Yeni indirdiğiniz dosya da aynı şekilde yüklenebilir — revizyon zinciri kapalıdır.

> **Uygulama projesinin elektrik girdileri.** Kesitler, hat uzunlukları, temel
> ölçüleri, makine dairesi ve paten balatası uzunluğu kaynak kitapta
> **yoktur** — program bunları teslim kopyasında `Veri Girişi` sayfasının
> sonuna, *"PROGRAMIN EKLEDİĞİ GİRDİLER"* başlığı altına yazar ve oradan geri
> okur. **Elinizdeki özgün kitabı** yüklerseniz o satırlar bulunmadığı için bu
> alanlar varsayılana döner; program hangilerinin döndüğünü **tek tek sayarak
> söyler** — sessiz kalmaz.

**Neden Excel, PDF değil?** Girdiler Excel'de *görünür hücrelerde* durur:
gözle görürsünüz, gerekirse Excel'de elle düzeltirsiniz, program onu da okur.
PDF'e gömülü gizli veri ise AutoCAD'e yerleştirme, yeniden yazdırma ya da bir
PDF optimize edicisinden geçme sırasında sessizce silinebilir — ve siz bunu
ancak yükleme başarısız olduğunda fark edersiniz. Tek ve görünür bir geri
yükleme noktası olması, iki belirsiz noktadan iyidir.

> Proje antedi (proje adı, işveren, pafta no, mühendis) şablonda bir hücreye
> sahip olmadığı için dosyanın **özelliklerine** yazılır (Excel: Dosya → Bilgi →
> Özellikler). Ofis şablonunun düzenine dokunulmaz, bilgi yine de dosyayla taşınır.

---

## 5. Proje dosyası ve paketleme

### Proje dosyası — girdilerin geri dönüş noktası

**Projeyi kaydet** tüm girdileri tek dosyaya yazar. Ne PDF ne Excel ne CAD —
yalnız programın okuyup yazdığı veri. Aylar sonra revizyon gerektiğinde dosyayı
yükler, değişeni düzeltir, çıktıları yeniden alırsınız.

**İki ayrı uzantı**, çünkü avan ve uygulama ayrı projelerdir:

| Proje | Uzantı | Nerede |
|---|---|---|
| Avan | **`.avan`** | Proje Kapağı → Proje araçları |
| Uygulama | **`.uygulama`** | Uygulama Hesapları → Proje dosyası |

Dosya adı **proje adından** üretilir (`Jan Mühendislik.uygulama`). Her dosya
**yalnız kendi projesinin** alanlarını taşır; avan dosyasını uygulamaya
yüklemeye çalışırsanız program *"Bu dosya AVAN projesine ait"* deyip reddeder.

Dosyanın içinde ayrıca **`surum`** alanı vardır. Girdi sözleşmesi zamanla
değişir; sürüm yazılı olmasaydı eski bir dosyadaki eksik alan **sessizce**
varsayılana düşerdi. Yazılı olduğu için program kaç alanın döndüğünü sayıp
söyler. **Ofis sabitleri de dosyaya girer** — proje o günkü kabullerle
hesaplandı, üç yıl sonra açıldığında aynı sonucu vermelidir.

### Projeyi paketle — tek ZIP

**Projeyi paketle (ZIP)** düğmesi teslim edilecek her şeyi ve geri dönüş
noktasını **aynı arşive** koyar:

```
Jan Mühendislik - Uygulama Projesi.dxf     ← CAD çizimi ( + DWG üretilebildiyse )
pafta pdf/1 - Kapak.pdf
pafta pdf/2 - Uygulama Projesi.pdf
Jan Mühendislik - Uygulama Projesi.xlsx    ← çalışma kitabı
Jan Mühendislik.uygulama                   ← GERİ DÖNÜŞ NOKTASI
OKUBENI.txt
```

Çıktılar projeyi **anlatır**, proje dosyası onu **geri getirir**. İkisi ayrı
yerlerde durursa arşivden dönmek imkânsızlaşır — bu yüzden birlikte inerler.

### Kalıcılık

Girdiler tarayıcıda da kendiliğinden saklanır; programı kapatıp açtığınızda
kaldığınız yerden devam edersiniz. **Avan ve uygulama ayrı kovalarda durur**:
biri diğerini görmez, **"Tümünü temizle" yalnız içinde bulunduğunuz projeyi
siler**, ve aynı anda bir avan ile bir uygulama projesi tutabilirsiniz.

**Örnek proje yükle** düğmesi, Excel dosyalarınızdaki örnek değerleri yükler.

---

## 6. Hesabın doğruluğu

Program bir **doğrulama paketiyle** birlikte gelir ve son çalıştırmada
**23.711 kontrolün tamamı geçmiştir.**

| Test | Kapsam | Sonuç |
|---|---|---|
| **1 · Excel uyumu** | 120 senaryo × ~40 hücre | **5.604 / 5.604** |
| **2 · Kenar durumlar** | tablo sınırları, yuvarlama, ofis varsayılanları, motor kademesi, manuel k, **geçersiz girdi yolları**, **kolon hattı akımının ηm ile hesaplandığı**, **boş kabin kütlesi tablosu** | **790 / 790** |
| **3 · Girdi dayanıklılığı** | ~1.900 bozuk girdi birleşimi + tüm API uçları | **149 / 149** |
| **4 · Çıktı bütünlüğü** | XLSX ve PDF açılabilirliği, içerik, **şablon denetimi**, uygulama paftası, **teslim edilen kitabın paftayla birebir aynı olduğu** ve **CAD çizimini AutoCAD'in açtığı** ( şapka · `%%` · sınırlar · açılış görünümü ) | **438 / 438** |
| **5 · Arayüz** | tarayıcıda iki modun tüm sekmeleri, canlı hesap, indirme, **ayrı veri kovaları**, **proje dosyası**, revizyon, yerleşim taşması, **kabin ağırlığının beyan yükünü izlemesi** | **370 / 370** |
| **6 · Geri yükleme** | girdiler → XLSX → geri okuma → aynı girdiler ( avan + mukavemet ) | **4.537 / 4.537** |
| **7 · Altın çıktı** | 411 senaryonun tüm sonucu satır satır kilitli — refah kalkanı | **824 / 824** |
| **8 · Mukavemet tabloları** | 15 tablo + 71 girdi alanı, kaynak Excel'e karşı hücre hücre;  Nequiv(t) **Çizelge 2'den türetilir** ve varsayılan açılarda kitapla birebir tutar | **951 / 951** |
| **9 · Mukavemet motoru** | 100 sonuç hücresi + **yirmi iki sapmanın uygulandığının kanıtı** + **standardın metnine karşı bağımsız doğrulama** + **ikinci · üçüncü · dördüncü denetimin her bulgusu yeniden üretilerek** + girdi reddi | **470 / 470** |
| **10 · Mukavemet ↔ Excel** | **78 senaryo × 168 hücre** ( 52'si standart gereği sapan, ayrı denetlenen ) — girdi uzayının tamamı LibreOffice ile yeniden hesaplanır; standart gereği sapılan hücreler ayrı denetlenir; **düzeltilmiş ana kitap** da yeniden hesaplatılıp motorla karşılaştırılır | **9.354 / 9.354** |
| **11 · Uygulama projesi** | ortak girdi köprüsü, bölüm birleştirme, makine dairesi ve topraklama yolları, **kendi ofis standardı ve tabloları**, **birinci denetimde bulunan sekiz hatanın her biri**, **boş kabin kütlesinin iki projede aynı tablodan geldiği**, **uygulama paftasının CAD çıktısı** ( beşinci denetim ) | **224 / 224** |

### Test 1 neden güçlü bir kanıt?

Girdiler **ofisin kendi Excel şablonuna** yazılır, dosya **LibreOffice ile
açılıp yeniden hesaplattırılır** — yani sonucu Excel'in kendi formülleri üretir,
program değil — ve çıkan **her hücre** programın motoruyla karşılaştırılır.
Kapsam: 10 bina tipinin tamamı (küçük ve büyük nüfusla), 9 kabin kapasitesi,
10 kabin hızı, **yedi kapı genişliğinin tamamı × üç kapı tipi** (ara değerli
1000 / 1200 / 700 mm dâhil), N = 1…30 kat sınırları, **bodrum durakları
(0 – 10, Tablo-2 eşiğini aşan durumlar dâhil)**, Standart/Yükseltilmiş eşiği,
elle süre ve adet girişleri, 1–4 asansörlü gruplar, farklı duraklı asansörler,
**asansör bazında bodrum ve imalatçı süreleri**, **asansör bazında askı ve
denge faktörü (dişlili + dişlisiz karışık proje)**, makine daireli/MRL
sistemler ve topraklama varyasyonları.

### Bağımsız denetimde bulunan ve düzeltilen hatalar

Testlerin geçmesi hataları dışlamaz. Aşağıdakiler **testlerin yakalamadığı**,
ayrı denetimlerde bulunup yeniden üretilen hatalardır; her biri artık kendi
regresyon kontrolüyle korunuyor. Beş tur yapıldı: birincisi programın
**davranışını** ( girdi–çıktı, dosya akışı, uyarılar ), ikincisi doğrudan
**hesap motorlarını** standardın metnine karşı, üçüncüsü **sayısal fiziği**,
dördüncüsü **sınır durumlarını**, beşincisi de **teslim edilen çizimin
AutoCAD'de açıldığını** denetledi.

#### Birinci denetim — davranış ve dosya akışı

| Bulgu | Etkisi |
|---|---|
| **Negatif gerilme "uygun" sayılıyordu.** Yan yatak boyu mesnet payından küçükse `X ≤ 0` çıkıyor, σe = −5.350 N/mm² oluyor ve `σe ≤ σem` bunu sessizce geçiriyordu | fiziksel olmayan bir kaide **"UYGUNDUR"** raporlanabiliyordu — artık geometri baştan reddediliyor, ayrıca negatif gerilme hiçbir koşulda uygun sayılmıyor |
| **Genel sonuç engelleyici uyarıları saymıyordu.** 37 kW motora 1,5 mm² kablo ( 62,5 A / 17,5 A ) yalnız ⚠ uyarı üretiyor, bölüm ve proje "uygundur" diyordu | akım kontrolü artık **bölüm sonucuna** girer;  uyarılar **engelleyici / bilgilendirici** diye ayrıldı;  yapılamayan zorunlu hesap ( topraklama · makine dairesi ) projeyi uygun bırakmıyor |
| **Excel'den dönünce sonuç değişiyordu.** Ofis sabitleri dosyaya yazılmıyordu: σem = 100 ile "UYGUN DEĞİL" olan proje, aktarılıp geri okununca varsayılan 130'a dönüp "UYGUN" oluyordu | proje sabitleri artık dosyada saklanıp geri okunuyor — **aynı projenin sonucu dosyadan geçince değişmiyor** |
| **Reddedilen ofis sabiti Excel'e ham gidiyordu.** `cosφ = 2` motor tarafından reddedilip 0,9 kullanılırken dosyaya 2 yazılıyordu | ekran ve indirilen kitap **farklı hesap yapıyordu**;  artık motorun kullandığı değer yazılıyor |
| **Metin ofis alanı sayıya çevriliyordu.** Kablo tipine "NYY" yazınca `None`'a düşüp sessizce varsayılan kullanılıyordu | metin alanları korunuyor;  belirsiz sayı yazımı ( `1.200` ) artık **bildiriliyor** |
| **Fiziksel girdi doğrulaması eksikti.** 6,5 halat ile hesap yapılıp "UYGUN" veriliyor;  konsol aralığı 0 `TypeError`, regülatör açısı 360° `OverflowError` ile çöküyordu | adet alanları tam sayı, uzunluklar pozitif, açılar aralıkta olmalı — hepsi **alan adıyla** reddediliyor |
| **Proje kimliği geri gelmiyordu.** Dosya özelliklerinde yazılı olan proje adı · işveren · pafta no yükleme yanıtına alınmıyordu | önceki projenin kimliği ekranda kalıp sonraki çıktı yanlış adla iniyordu;  artık geri okunuyor ( programın kendi imzası **mühendis sanılmıyor** ) |
| **Motor akımı %18 düşüktü.** Şebekeden çekilen akım `P2/(√3·U·cosφ·ηm)`'dir;  program `ηm`'ye bölmüyordu | **kablo ve sigorta olduğundan küçük seçiliyordu.** Kitabın kendi elektrik sayfası ( `12-Elk.Hesapları!W35` ) 0,85 ile bölerek doğrusunu yapıyordu — kaynak **kendi içinde tutarsızdı**. `motor_elektrik_verimi` ofis sabiti eklendi;  **sigorta kademeleri değişti** ( 11 kW'ta 4 x 25 → 4 x 32 ) |
| **Excel'in elektrik sayfası girdilerden kopuktu.** `12-Elk.Hesapları` kendi sabitleriyle çalışıyordu:  L2 = 5 m · U = 400 V · S1 = 6 · S2 = 4 mm² · cosφ = 0,8 ve kablo kapasiteleri 43 / 34 A hücreye yazılı | teslim edilen kitap ekrandan **başka** hesap yapıyordu;  artık programın girdileri yazılıyor ve kapasiteler kesitten geliyor |

#### İkinci denetim — hesap motorunun standarda karşı denetimi

Birincisi programın **davranışını** ( girdi–çıktı, dosya akışı, uyarılar )
denetlemişti. İkincisi doğrudan **hesap motorlarını** TS EN 81-20 / 81-50'nin
metnine karşı okudu ve on bulgu çıkardı. Hepsi yeniden üretildi; her biri
artık kendi regresyon kontrolüyle korunuyor
( `testler/test_mukavemet.py` · `_denetim_bulgulari` ).

| Bulgu | Yön | Etkisi ve düzeltme |
|---|---|---|
| **`Sf ≥ Smin` yanlış bir geçme ölçütü olarak kullanılıyordu** ( böl. 4 ) | yanlış ret | EN 81-20 m.5.5.2.2 tek şey ister: *gerçekleşen* S, 12/16 ile EN 81-50 m.5.12'nin Sf'sinin **büyüğünden** az olmayacak. `Sf < 12` bir uygunsuzluk değil, "asgariyi Smin belirliyor" demektir. Kitabın koşulu standarda uyan tasarımları reddediyordu ( Sf = 7,89 · **S = 32,5** → "UYGUN DEĞİLDİR" ) ve verdiği öğüt sonuca ulaşmıyordu: halat çapını artırmak Dt/dh'yi düşürür, Sf'yi **büyütür**. Ölçüt kaldırıldı; satır artık hangi asgarinin belirleyici olduğunu yazar |
| **Sonuç başlığı `Dt/dh ≥ 30` diyor, kontrol 40 ile yapılıyordu** ( böl. 4 ) | paftada yanlış sınır | Kontrol doğruydu ( m.5.5.2.1 = 40 ), paftaya basılan sayı yanlıştı. Başlık artık kontrolün kullandığı eşiği ve `S ≥ max( Sf ; Smin )` ifadesini yazar |
| **ω tanım aralığı dışında program çöküyordu** ( böl. 7 ) | çökme | `λ = konsol arası / ix`;  ω tablosu yalnız 20 ≤ λ ≤ 250'de tanımlı. Bölüm 2 λ'yı kırpıp `None`'a karşı korunuyor, bölüm 7 ikisini de yapmıyordu — 50 × 50 × 5 rayda 3.900 mm konsol aralığı ( gerçekçi bir girdi ) ham `TypeError` veriyordu. Artık girdi doğrulaması **izin verilen en büyük aralığı söyleyerek** reddediyor;  doğrulama atlansa bile motor çökmüyor |
| **Halat kütlesinin taraf dağılımı kendi içinde çelişikti** ( böl. 6 ) | **emniyetsiz** | `MSR = ( 0,5·H ± y )·ns·gh` bağıntısının ± işareti dört yük durumunun **üçünde** ters yazılmıştı: kabin en alt duraktayken halat kütlesinin tamamı karşı ağırlık tarafına konuyordu. Kitabın bölüm 1 açıklaması bunun **tersini** söylüyordu. Yön emniyetsizdi — tahrik yeteneği olduğundan iyi çıkıyordu ( 20 duraklı örnekte yükleme oranı 1,23 yerine **1,79**, e^(f·α) = 1,71 sınırını **aşar** ) |
| **Kolon hattı akımı motorun elektrik verimini içermiyordu** ( avan böl. 6 ) | **emniyetsiz** | ηm düzeltmesi makine besleme hattı için yapılmış, **kolon hattı için yapılmamıştı**. `I ≤ Iz` kararı kolon hattına aittir ve o hatta Pşeb = Nsç/ηm akar. Kaynak kitap bunu zaten doğru yapıyor ( `12-Elk.Hesapları!AT7 = W36×1000` ). Kesit olduğundan küçük seçilebiliyordu: **22 kW + 6 mm² · 30 kW + 10 mm² · 55 kW + 25 mm²** birleşimleri "uygun"dan "uygun değil"e döndü. Aynı düzeltme **ε1 ve ε2**'ye de girer ( ε ∝ P ) ve avan çalışma kitabının şablonu da güncellendi ( `SABİTLER!C39 = ηm`;  `E102` ve `E126` ona böler ) — ekran ile indirilen dosya ayrışmasın diye |
| **Sarılma açısı α 180°'yi aşabiliyordu** ( böl. 6 ) | **emniyetsiz** | `Ra < 2·R1` girildiğinde pay negatife düşüyor ve α tek sarımlı kasnakta imkânsız bir değere çıkıyordu ( Ra = 100 mm → 187,65° ). e^(f·α) sınırı α ile büyür. Halat arası artık kasnak çapından küçük olamaz;  bölüm ayrıca `0° < α ≤ 180°` denetler |
| **Ofis sabiti γ / β bölüm 6'yı değiştiriyor, bölüm 4'ü değiştirmiyordu** | pafta ile hesap ayrışıyor | `Nequiv(t)` kanalın **adına** bağlı sabit bir tablodan okunuyordu; γ = 45° seçilse bile 12 kalıyor, pafta 38° yazmayı sürdürüyordu. Artık EN 81-50 **Çizelge 2**'den, ofis açılarından, doğrusal ara değerle hesaplanıyor. Pafta hesabın gerçekten kullandığı γ ve β'yı yazar |
| **Moment ve mil kuvveti askı oranına göre indirgenmiyordu** ( böl. 1 ) | paftada 2 katı değer | 2:1 palangada tahrik kasnağının gördüğü kuvvet `Gmax` değil `Gmax/i`'dir. Motor gücünü etkilemez ( N askı oranından bağımsızdır ve doğru kurulmuştur ), ama paftadan moment okuyup makine seçen bir okuyucuya **iki katı** bir sayı yazılıyordu |
| **Uygulama projesinde "toplam sistem verimi" kutusu yoktu** | verim cezası iki kez inebilir | Avan motorundaki kutunun karşılığı yoktu; imalatçının toplam verimini kullanmak isteyen mühendis ancak ofis sabitini değiştirebiliyordu ve o değişiklik **projedeki bütün asansörleri** etkiliyordu. Kutu eklendi |
| **Kabin alanına pervaz katkısı yarım alınıyordu** ( böl. 3 ) | **emniyetsiz** | EN 81-20 m.5.4.2.1.3: girinti ≤ 100 mm ise hariç, **> 100 mm ise tamamı** alana katılır. Kitap kapı genişliğinin yarısını alıyordu ( 900 mm kapı + 300 mm pervaz → 0,1350 m², tamı **0,2700 m²** ). Kullanılabilir alanı küçük göstermek Çizelge 6'nın izin verdiğinden büyük kabine izin verir |

**Kolon hattı düzeltmesinin ofise pratik sonucu.** `I` ve `ε` motorun payı
kadar ( 1 / ηm = **%17,6** ) yükseldi. Aydınlatma + priz yükü ≈ 1,24 kW olan
tipik bir tesiste kolon hattı kesiti şu güçlerde bir kademe büyür:

| Motor | Eski I | Yeni I | S1 |
|---|---|---|---|
| 22 kW | 39,2 A | **45,8 A** | 6 → **10 mm²** |
| 30 kW | 52,7 A | **61,7 A** | 10 → **16 mm²** |
| 55 kW | 94,9 A | **111,3 A** | 25 → **35 mm²** |
| 75 kW | 128,7 A | **151,0 A** | 50 → **70 mm²** |

**Motor sigortası değişmez** — o zaten motor akımından, ηm dahil
hesaplanıyordu. Değişen kolon hattının kendisidir. Eldeki paftalarda bu güç
sınıflarındaki **S1 kesitleri gözden geçirilmelidir.**

Denetimin *"teyide muhtaç"* listesindeki noktalar da standardın metnine karşı
okundu:

| Nokta | Sonuç |
|---|---|
| `Nequiv(t) = 12` ( V kanal, γ = 38° ) doğru mu | **Doğru.** EN 81-50 Çizelge 2: γ = 35 · 36 · 38 · 40 · 42 · 45 · 50° → 18,5 · 16 · **12** · 10 · 8 · 6,5 · 5. Çizelgenin tamamı programa girdi |
| Regülatör kuvvet ölçütü | **Bulgu doğruydu — ve bir katman daha derindi.** Standardın iki ayrı maddesi iki ayrı kuvvetten söz ediyor: m.5.6.2.2.1.1 d) regülatörün **ürettiği** kuvveti sınırlar ( *"produced **by the governor**"* ) — bu, kasnağın iki yanındaki gerginlik **farkıdır**: `Fçekme = F′reg − Freg`. Güvenlik tertibatı mekanizmasını çeken odur; halatın statik gergisi Freg zaten oradadır ve hiçbir şeyi çekmez. m.5.6.2.2.1.3 b) ise **halattaki** en büyük gerginliği ( `F′reg` ) emniyet katsayısına sokar ( *"produced **in the rope**"* ). Kitap ikisini de F′reg ile yapıyor, üstelik sınıra `2 × Freg` koyuyordu. Devreye sokma kuvveti **imalatçı verisidir**; girilmezse madde denetlenemez ve bölüm **"HESAP EKSİK"** der — proje *uygundur* çıkmaz |
| Karşı ağırlıkta güvenlik tertibatı modellenmiyor | **Bulgu doğruydu.** Bölüm 8 yalnız C.2.2'yi ( normal işletme, k3 = 1,2 ) kuruyordu. Tertibat varsa belirleyici durum **C.2.1**'dir ve orada k1 = 2 · 3 · 5 geçer. Karşı ağırlık güvenlik tertibatı girdi oldu; seçilirse C.2.1 de hesaplanır |
| Bölüm 7 C.2.2'de burkulma ω'sız | **Bulgu yersizdi — program doğru.** EN 81-50 Ek **C.2.2.2** `σv = ( Fv + k3·Maux ) / A` der; ω yalnız **C.2.1.2**'de geçer. İki durumun ayrıldığı artık ayrıca denetleniyor |
| `reg_surtunme` μ üst sınırsız | **Bulgu doğruydu.** m.5.6.2.2.1.3 b) hesaba katılacak değeri kendisi verir: **µmax = 0,2**. Üstü reddediliyor |
| `Nsç = 0` girilirse paftada iki motor gücü | **Yeniden üretilemedi.** Aralık dışı Nsç uyarı ile bildiriliyor, standart kademeden seçiliyor ve bölüm 1, kurulu güç cetveli ve ε2 **aynı** değeri kullanıyor. Yine de kalıcı bir kontrol eklendi |
| Ölü ve yanıltıcı kod | `KANAL_ISLEME` gerçekten yanlış adlandırılmıştı — içindeki sayılar μ değil **f**'dir ( 0,1 / sin 19° = 0,30716 ). Başlık düzeltildi ve tablonun **çivili** olduğu ( γ = 38° · β = 90° ) açıkça yazıldı; motor onu hiç kullanmaz, ekrandaki tablo da artık f'yi ofis açılarından üretir |
| `DURAK_AZAMI = 20` — trafik 30 katı destekliyor | Sınır kaynak kitabın **kendi düzeninden** gelir ( `Veri Girişi`!G12:G34 ). Kapsam farkı bilinçlidir ve arayüz bunu söyler; 20 duraktan fazlası uygulama projesinde hesaplanamaz |
| Sigorta ↔ kablo koordinasyonu | `I2 ≤ Iz2` kontrolü ( ve artık `I ≤ Iz` de doğru güçle ) çoğu durumu yakalıyor. IEC 60364-4-43'ün `In ≤ Iz` şartı ayrıca denetlenmiyor — **bilinen sınırdır**, bkz. §7 |

#### Üçüncü denetim — sayısal fizik kontrolleri

Kuvvet dengesi ve sınır kontrollerini sınayan hesaplarla üç sorun daha
bulundu. Olumlu kontrol olarak kuvvet iki katına çıkarılınca eğilme momenti
**2 kat**, açıklık iki katına çıkarılınca sehim **8 kat** çıkıyor — temel
bağıntılar tutarlı.

| Bulgu | Yön | Etkisi ve düzeltme |
|---|---|---|
| **Negatif sehim ve gerilme, sınırı aşsa da "uygun" sayılıyordu** ( böl. 7 ) | **emniyetsiz** | Kabin merkezi ray ekseninin öbür yanına düşünce ( `xc < 0` ) Fx negatife iner. `δ = −5,59 mm` iken sınır 5 mm olmasına rağmen `δ ≤ 5` **sessizce geçiyordu**. Aynı hata bir yerde daha vardı: `σm = σx + σy` işaretli toplanınca ters işaretli iki eğilme **birbirini götürüyor**, `σc = σv + σm` de küçülüyordu ( örnekte σm = −19,87 yerine **71,44 N/mm²** ). Fx ve moment işaretini korur — yön bilgisidir; **σ ve δ büyüklük olarak** yazılır ve karşılaştırılır |
| **Karşı ağırlık güvenlik tertibatının tepkisi kuyu tabanına aktarılmıyordu** ( böl. 9 ) | **emniyetsiz** | Kabin rayında bu kalem sayılıyor, karşı ağırlıkta sayılmıyordu: tertibat *"Kaymalı"* seçilse bile **FAR değişmiyordu** ( 1.015,50 N ). Eksik tepki `k1·gn·Mcwt/n = 2 × 9,81 × 1.100 / 2 = 10.791 N/ray`; taban **11.806,50 N/ray** görmeliydi. Bu sayı **inşaat projesine** bildirilir ve olduğundan düşük gidiyordu. Ray kütlesinin payı burada da bir kez sayılır ( `Fk − Mg·gn` ) |
| **Denge oranı değişince aynı projede iki farklı karşı ağırlık** | tutarsızlık | Kitabın `C80` formülü *"kabin ağırlığı + beyan yükü / 2"* diye çivili; bölüm 1 ise `Ga = P + q·Q` kuruyordu. `q = 0,60`'ta motor ve ağırlık tamponu **1.180 kg**, tahrik ve ağırlık rayı **1.100 kg** kullanıyordu. Kütle artık **tek yerden** türer ve bölüm 1 de onu okur; teslim edilen kitabın `C80` formülü de projenin q'suyla yazılır |

#### Dördüncü denetim — sınır durumları

Fiziksel olarak geçersiz girdilerin **güvenilir görünen sonuç üretmesi**. Bu
iki bulgu normal girdilerde hesabı etkilemez; kalkanların eksikliğidir.

| Bulgu | Etkisi ve düzeltme |
|---|---|
| **Sıfır ya da negatif sistem verimi kabul ediliyordu.** Verim ile palanga kaybı ayrı ayrı geçerli sayılıyor, **aralarındaki ilişki** denetlenmiyordu | η = 0,10 · Δη = 0,10 → η′ = 0 → **sıfıra bölme**. Δη = 0,20 → η′ = **−0,10** ve gereken güç **−44,26 kW**; `Nsç ≥ N` her motoru geçiriyor, temiz bir projede genel sonuç **"UYGUN"** çıkıyordu. Artık hesaptan önce `0 < η′ ≤ 1` denetleniyor ve hata **iki sabiti de adıyla** söylüyor. *( Avan motorunda bu kalkan zaten vardı — eksik olan uygulama tarafıydı. )* |
| **İmkânsız geometri negatif halat ağırlığı üretiyordu.** Kabin paten arası 30.000 mm verildiğinde halat boyu **−4,82 m**, ağırlığı **−5,13 kg** | Negatif ağırlık yükten **düşülüyor**: motor gücünü azaltıyor, halat güvenlik katsayısını **yükseltiyor** — imkânsız geometri hesabı *iyileştiriyordu*. Artık tampon/paten yığınının kuyuya sığması denetleniyor; hata toplama giren beş ölçüyü tek tek yazıyor |

Her ikisinde de **ikinci kalkan** var: girdi doğrulaması atlansa bile motor
çökmüyor, bölüm 1 *"HESAP YAPILAMADI"* diyor ve proje *uygundur* çıkmıyor.

#### Beşinci denetim — teslim edilen çizim AutoCAD'de açılmıyordu

Teslim edilmiş bir uygulama projesinin DXF'i **AutoCAD 2027 for Mac'te
açılmıyor**, program *"A software problem has caused application to close
unexpectedly"* verip kapanıyordu. Dosya bozuk değildi: yapısal denetimden
sıfır hatayla geçiyor, etiket akışı kusursuz, sınıflar ve karolar eksiksiz.

Sebep AutoCAD'in kendi başsız motoruyla ( `AcCoreConsole` ) yığın izi alınarak
bulundu — çökme yeniden çizim sırasında, bir yazının TrueType genişliği
ölçülürken:

```
regenall → fullregen → AcDbImpText::textDraw → TextEditor::get_extents
  → AcGiContextImp::getTrueTypeTextExtents → WhipImp::GetTextExtents
    → FontCacheHashImp::calTotalWidths → FontCacheOSX::getCharData   ← ÇÖKME
```

Suçlu, ikili aramayla 2 943 varlıktan tek bir yazıya, oradan **iki karaktere**
indirildi. Her adım gerçek AutoCAD çekirdeğinde ölçüldü.

| Bulgu | Etkisi ve düzeltme |
|---|---|
| **Şapka ( `^` ) AutoCAD'i çökertiyordu.** AutoCAD metinde `^` + karakteri **denetim karakteri** diye yorumlar ( `^8` → 0x18, `^(` → 0x08 ); yazı tipinde o kodun glifi yoktur ve macOS'ta arama çöker | En kısa çökerten parça **`^8`** ( `8` tek başına açılıyor ). İkinci suçlu `e^(f·α)`. Şapka paftada **üs işareti** olarak geçiyor — `10^[…]` · `(Dt/dh)^8,567` · `e^(f·α)` — yani kaçınılmaz. Çizimde artık **U+02C6** yazılır: görünüşü şapkanın aynısı, CP1252'de 0x88'de durduğu için her ANSI yazı tipinde var, hiçbir CAD onu denetim karakteri saymaz. `**` ve `%%94` de çökertmiyordu ama biri gösterimi bozar, öteki yalnız AutoCAD'in anladığı bir kaçıştır |
| **`$EXTMIN` / `$EXTMAX` atamaları dosyaya hiç geçmiyordu** | ezdxf bu başlıkları dosyayı **yazarken** model sekmesinin kendi değerlerinden yeniden üretir ( `Drawing.update_extents` ); başlığa yazmak boşunaydı. Şablondan gelen `1e+20 / -1e+20` ( *"hiç hesaplanmadı"* ) dosyaya olduğu gibi geçiyor, ZOOM EXTENTS'in dayanağı kalmıyordu. Değer artık sekmenin üstüne yazılıyor |
| **Kayıtlı görünüm orijinde duruyordu** | Şablonun `*Active` görünümü ( 0, 0 ), 1 000 birim yüksekliğinde; oysa ofisin pafta formatı **x ≈ −4 000**'de. Çökme olmasaydı bile çizim **bomboş ekranla** açılırdı. Görünüm artık çizimin üstüne oturtulur |

Şapka **yalnız uygulama paftasında** geçiyordu; avan paftalarını ölçen TEST 4
bu yüzden hatayı göremedi. Uygulama paftasının CAD çıktısı artık **TEST 11'de**
ayrıca ölçülüyor: hiçbir yazıda `^` ya da `%%` kalmadığı, üs işaretinin
paftada gerçekten geçtiği ( ölçüt boş kalmasın ), sınırların hesaplandığı ve
görünümün çizimin üstünde olduğu. Düzeltilmiş çizim, aynı kaynak paftalardan
yeniden üretilip **AutoCAD 2027'de açılarak** doğrulandı.

### Test yazılırken bulunan ve düzeltilen hatalar

| Bulgu | Etkisi |
|---|---|
| Python'un `round()` bankacı yuvarlaması yapıyor (865 → 860), Excel'in `ROUND`'u yarımı yukarı yuvarlıyor (865 → 870) | Tablo-11 boş kabin kütlesinde bazı ara yüklerde **10 kg sapma** |
| Çoklu asansör sonuç metni Excel'den bir boşluk farklıydı | paftada metin uyuşmazlığı |
| `1,234.56` gibi İngilizce ondalık yazımı `1,23456` olarak okunuyordu | **yanlış hesap** |
| `NaN`, `Infinity`, aşırı büyük sayı girilirse | **program çöküyordu** |
| Avan tarafında zorunlu bir alan boş bırakılırsa | **program çöküyordu** |
| Ofis standardına `0` yazılırsa (armatür ışık akısı, ray sayısı) | **sıfıra bölme hatası** |
| XLSX indirmesinde kullanılmayan hesap yolu şablonun örnek verisiyle geliyordu | projeyle **ilgisiz bir pafta** çıktı alınabiliyordu |
| Bozuk istek gövdesi API uçlarında | **HTTP 500** |
| Hesap tamamlanamadığında PDF üretimi | **çöküyordu** |
| Şablon dosyası eksikse XLSX indirmesi | sessizce **bozuk bir dosya** iniyordu |
| Test paketi geçici dosyaları proje klasörüne yazıyordu | silme izni kısıtlı makinede test takılıyordu |
| Excel'den geri yüklemede ondalıklı açılır liste değeri (hız 1,6 / kesit 1,5) eşleşmiyordu | kabin hızı **sessizce boş kalıyor**, avan paneli tamamen boşalıyordu |
| Dar ekranda 331 px yatay taşma | telefonda düzen bozuluyordu |
| Avan sekmesinin uyarıları yalnız PDF'e basılıyor, ekranda hiç görünmüyordu | eksik girdi / geçersiz ofis standardı uyarısı **fark edilmiyordu** |
| Trafikte kapasite veya hız değişince avan sekmesi sessizce eski değerde kalıyordu | revizyonda **tutarsız pafta** çıkabiliyordu |
| Açılır listede seçilebilen 1000 / 1200 / 700 mm kapı genişlikleri tabloda yoktu | seçilebilen bir değer **hesabı durduruyordu** |
| Palanga ve denge faktörü proje geneli sabitti | dişlili + dişlisiz karışık projede **yanlış motor gücü ve karşı ağırlık** |
| Bodrum durağı hiçbir yerde hesaba girmiyordu | Tablo-2 asgari hızı **düşük seçilebiliyordu** |
| Uygulama projesinin **12 girdisi** ( kesitler · hat uzunlukları · temel ölçüleri · makine dairesi · paten balatası ) Excel'e hiç yazılmıyordu | revizyonda **sessizce kayboluyor**, kesitler varsayılana dönüyordu — ekran *"41 girdi geri yüklendi"* deyip eksiği söylemiyordu |
| Aralık dışı Nsç / L1 motor tarafından reddedilip varsayılan kullanılırken, **XLSX'e reddedilen değer yazılıyordu** ( Nsç = 900 kW → ekran 7,5 kW, dosya 900 kW ) | indirilen kitap **paftadan farklı hesaplıyordu**;  yazıcı motorun kabul koşulunu kendi süzgeciyle ikinci kez uyguluyordu |

Bunların hepsi düzeltildi; her biri için pakete kalıcı bir test eklendi.

### Mukavemet kitabında bulunanlar ( uygulama projesi )

Motor yazılırken kaynak çalışma kitabında bir dizi sorun çıktı. **Uyulması
gereken standart TS EN 81-20 / TS EN 81-50'dir**; kitap yalnız bir başlangıç
noktasıdır. Aşağıdaki **yirmi iki** noktada kitap standarttan ( yalnız verim,
moment ve denge oranı maddelerinde ofisin kendi kabulünden ) sapıyor — program
standardı uyguluyor. Liste kodda tek yerde durur
( `engine/uygulama/mukavemet.py` · `EXCEL_FARKLARI` ) ve doğrulama testi oradan okur.

| # | Konu | Standart | Kitabın yaptığı | Programın yaptığı |
|---|---|---|---|---|
| ① | Tahrik kasnağı / halat oranı | **EN 81-20 m.5.5.2.1** — en az **40** | Başlığı "≥ 40" yazar, kontrolü **30** ile yapar | 40 uygulanır |
| ② | Karşı ağırlık rayı σ(My) | **EN 81-50 Ek C.2.1.1** — Fy → Mx → **Wx** | Wy'ye böler | Wx'e bölünür |
| ③ | Durum 2'de xQ | **EN 81-50 Ek C.2.1.1** | Sabit **0** yazar ( başlığı "xQ = xc" dese de ) | xQ = xc |
| ④ | Flanş eğilmesinde ℓ | **EN 81-50 m.5.10.5** — ℓ = paten balatası **uzunluğu** | Paydaya **1** yazar ( ℓ harfi 1 rakamı okunmuş ) | ℓ girdi; boşsa 2·b'den türetilir |
| ⑤ | ω burkulma katsayısı | **EN 81-50 m.5.10.3** — ω, λ **ve Rm**'e bağlıdır | Tek tablo kullanır; o tablo yalnız **Rm = 370** eğrisidir ve ray çeliğinden bağımsız uygulanır | Rm 370 ve 520 eğrileri, arada doğrusal ara değer |
| ⑥ | Acil frenlemede μ | **EN 81-50 m.5.11.2.3.2** — μ = 0,1/(1+v/10), v **halat** hızı | Bağıntıya **kabin** hızını koyar | v = kabin hızı × askı oranı |
| ⑦ | Nps · Npr | **EN 81-50 m.5.12.2** — tesisin askı düzenine bağlı | Hesap sayfasına **sabit** 1 ve 0 yazar | Girdi; palangalı sistemde uyarı verilir |
| ⑬ | **Kuyu tabanı yükünde ray ağırlığı** | **EN 81-20 m.5.2.1.8.4** — ray kütlesi ve güvenlik tertibatı tepkisi **ayrı kalemler** | `FKR = gn·Gr·LR + MY + Fk`;  `Fk` zaten `Mg·gn` içerir → ray ağırlığı **iki kez** | Ray kütlesi bir kez;  tepki `Fk − Mg·gn` |
| ⑫ | **Sürtünme çarpanı f** | **EN 81-50 m.5.11.2.3.1.1** ( yarım daire ) ve **m.5.11.2.3.1.2** ( V ) — **iki ayrı bağıntı** | Kanal şeklinden **bağımsız** olarak hep V kanal bağıntısı;  alt kesilmesi olmayan kanalda da β = 90° | Şekle göre doğru madde;  alt kesilme yoksa β = 0 |
| ⑪ | Acil frenleme yavaşlamasının **alt** sınırı | **EN 81-50 m.5.11.2.2.2** — *"in no case … less than 0,5 m/s²"* | Yalnız üst sınırı ( 1 gn ) denetler | 0,5 m/s² altı **reddedilir** |
| ⑩ | **Kabin alanı tablosu** | **EN 81-20 Çizelge 6** — 28 beyan yükü | 7'si tabloda ve açılır listede **yok** ( 100 · 1050 · **1250** · 1350 · 1425 · **1500** · 2500 kg );  320 kg için 0,97 m² | Tablo Çizelge 6'ya tamamlandı;  320 kg standardın ara değeriyle **0,953** |
| ⑨ | Motor verimi η | **Ofisin kendi tablosu** ( avan ): dişlisiz 0,85 · dişli 0,50 · palangalı sistemde −0,10 ( MMO/697 §2.4 ) | Makine tipinden **bağımsız** sabit 0,92; `B130`'daki makine tipini hiç okumaz | η makine tipinden gelir, palanga düşüşü uygulanır |
| ⑧ | İki sığınma açıklığı | **EN 81-20 m.5.2.5.7.3** ve **m.5.2.5.8.2 a) 2)** | Kabin üstü **1200 mm**, ray dibi **150 mm** — ikisi de standartta yok | Kabin üstü = sığınma hacminin yüksekliği ( **1000 mm** ), ray dibi = Şekil 7 ( **100 mm** ) |
| ⑭ | **Kabin önü girintisi** | **EN 81-20 m.5.4.2.1.3** — ≤ 100 mm hariç, **> 100 mm ise tamamı** | Kapı genişliğinin **yarısını** katar;  eşiği "≥ 100" tutar | Girintinin tamamı;  100 mm'nin kendisi hariç |
| ⑮ | **`Sf ≥ Smin` geçme ölçütü** | **EN 81-20 m.5.5.2.2** — ölçüt `S ≥ max( Sf ; Smin )` | Sf'yi Smin ile karşılaştırıp **UYGUN / UYGUN DEĞİL** yazar | Ölçüt kaldırıldı;  satır hangi asgarinin belirleyici olduğunu yazar |
| ⑯ | **Nequiv(t)** | **EN 81-50 m.5.12.2.2 Çizelge 2** — γ ve β'nın fonksiyonu | Kanalın **adına** bağlı sabit tablo;  ofis açısı değişse kımıldamaz | Çizelge 2'den, ofis açılarından, doğrusal ara değerle |
| ⑰ | **Halat kütlesinin taraf dağılımı** | **EN 81-50 m.5.11.2.2** — ± işareti kabinin konumundan | Dört yük durumunun **üçünde** ters;  kabin en altta iken halat karşı ağırlıkta | Kabin en altta → halat kabin tarafında ( en olumsuz durum ) |
| ⑱ | **Mil kuvveti ve moment** | Ofis kabulü ( MMO 208/7 - 2.4 ) | `Pm = F1 − Ga` · `M = Gmax·Dt/2` — askı oranı hiç girmez | 2:1'de kasnak tarafındaki büyüklükler **yarıya** iner |
| ⑳ | **Ray σ ve δ'sinin işareti** | **EN 81-50 Ek C.2.1** · **m.5.10.6** | σ ve δ'yı işaretli karşılaştırır;  σm = σx + σy'yi işaretli toplar | σ ve δ **büyüklüktür**;  en olumsuz lif iki eğilmeyi de toplayarak görür |
| ㉑ | **Karşı ağırlık tertibatının taban tepkisi** | **EN 81-20 m.5.2.1.8.4** — tepki ayrı kalem | Karşı ağırlıkta güvenlik tertibatı girdisi yok;  FAR tepkiyi hiç saymaz | Tertibat varsa `k1·gn·Mcwt/n` FAR'a girer |
| ㉒ | **Karşı ağırlık denge oranı q** | Ofis kabulü ( MMO 208/7 - 2.4 ) | `C80 = C75 + C59/2` **çivili** — ofis q'yu değiştirse bile 0,50 | Kütle tek yerden, projenin q'suyla türer |
| ⑲ | **Regülatör çekme kuvveti ve ikinci sınır** | **EN 81-20 m.5.6.2.2.1.1 d)** ve **m.5.6.2.2.1.3 b)** — biri regülatörün **ürettiği** kuvveti, öteki **halattaki** gerginliği sınırlar | İkisini de F′reg ile yapar;  sınıra da **2 × Freg** koyar | `Fçekme = F′reg − Freg` maddeye, `F′reg` emniyet katsayısına girer;  imalatçı kuvveti yoksa **HESAP EKSİK** |

**①'in pratik sonucu:** kitabın kendi örneğinde tahrik kasnağı 240 mm, halat
6,5 mm → oran **36,9**. Kitap 30 eşiğiyle "uygun" der; **standardın 40 eşiğine
göre uygun değildir** ve program bunu kırmızı gösterir. 40'ı sağlamak için
kasnak en az **260 mm** olmalıdır. 30 sayısı aynı standardın *dengeleme halatı
gergi kasnağı* ( m.5.5.6.2 ) ve *regülatör* ( m.5.6.2.2.1.3 ) eşiğidir — askı
halatının değil.

**③ ve ④'ün etkisi** ( kitabın örnek projesinde ):

| | Kitap | Program |
|---|---|---|
| Durum 2 σm | 40,3 N/mm² | **57,4** — Durum 2 belirleyici hâle gelir |
| Flanş σF ( Durum 1 ) | 19,8 N/mm² | **15,0** ( ℓ = 2·b = 34 mm ) |

**⑤'in etkisi.** Standart Rm = 370 ve 520 için iki ω eğrisi verir ve arada
doğrusal ara değer ister; kendi notu, işlenmiş raylarda 440 N/mm² yaygın
olduğu için bunun *"her zaman yapılması"* gerektiğini söyler. Kitabın tek
tablosu yalnız 370 eğrisidir ( 231 değerinin 231'i standardın 370 formülüyle
birebir çıkıyor ) ve ray çeliğinden bağımsız kullanılır:

| λ | Rm 370 | Rm 440 | Rm 520 |
|---|---|---|---|
| 100 | 1,898 | 2,194 **(+16 %)** | 2,533 **(+34 %)** |
| 155 | 4,057 | 5,004 **(+23 %)** | 6,086 **(+50 %)** |
| 250 | 10,554 | 13,017 **(+23 %)** | 15,831 **(+50 %)** |

Burkulma gerilmesi σk doğrudan ω ile çarpıldığı için, 440 ya da 520 çelik
seçildiğinde kitap σk'yı **%19-33 düşük** gösterir.

**⑥'nın etkisi.** EN 81-50'nin çözümlü örneği bunu kanıtlıyor: 1 m/s kabin
hızı ve 2:1 askı için standart μ = 0,083 verir — bu ancak v = 2 m/s ( halat
hızı ) ile çıkar. Kabin hızı kullanmak μ'yü, dolayısıyla e^(f·α) sınırını
büyütür ve tahrik yeteneğini olduğundan iyi gösterir.

**⑬'ün etkisi.** Örnek projede kitap 21.326 N der, doğrusu 18.096 N — ray
başına **3,23 kN ( %18 )**. Bu kalem **fazla hesaplanıyor**. Hatanın yönü
emniyetli olsa da, listede bulunması gereken başka yüklerin ( ör. klips itme
kuvveti Fp ) eksikliğini telafi etmez.

**⑫'nin etkisi.** Kanal şekli açılır listede **seçilebiliyor** ama `f`'yi hiç
değiştirmiyordu — beş şekil de aynı sürtünme çarpanını veriyordu. Standardın
yarım daire kanallar için ayrı bir maddesi vardır:

| Kanal | Doğrusu | Kitabın verdiği | |
|---|---|---|---|
| Altı kesik yarım daire ( β=90° · γ=25° ) | 0,1933 | 0,2053 | **+%6** |
| Düz yarım daire ( β=0 · γ=25° ) | 0,1248 | 0,2053 | **+%65** |
| V kanal | 0,2053 | 0,2053 | fark yok |

İkisi de **emniyetsiz** taraftaydı — tahrik yeteneğini olduğundan iyi
gösteriyordu. Kanal açıları ( V için γ ≥ 35° · yarım daire için γ ≥ 25° ·
β ≤ 105° ) proje bazında bilinemediği için **ofis standardına** konmuştur.

Ayrıca m.5.11.2.3.1.2, sertleştirilmemiş kanalda **alt kesilmenin gerekli**
olduğunu söyler; alt kesilmesiz + sertleştirilmemiş birleşimi seçilirse pafta
uyarı basar.

**⑪'in etkisi.** `a = 0,05 m/s²` girip tahrik hesabını "UYGUN" almak
mümkündü. Küçük bir yavaşlama atalet kuvvetini küçültür, T1/T2 oranını
iyileştirir — emniyetsiz taraf.

**⑩'un etkisi.** Liste **kapalıdır** — içinde olmayan bir yük seçilemez. Yani
1250 ve 1500 kg gibi yaygın asansörlerde program hiç hesap yapamıyordu;
yanlış cevap vermiyordu ama o projeyi çıkaramıyordunuz. Seçenekler artık
tablodan **türetilir** ( iki listenin bir daha ayrışmaması için ) ve teslim
edilen kitabın açılır listesi de genişletilir. 320 kg Çizelge 6'da yoktur;
standardın kendi dipnotu ara yükler için doğrusal ara değer ister ve
300/375 arası **0,953 m²** verir — kitabın 0,97'si **emniyetsiz** taraftaydı,
o yük için standardın izin verdiğinden büyük kabine izin veriyordu.

**⑭'ün etkisi.** 900 mm kapı + 300 mm pervazda kitap girintiye **0,1350 m²**
katıyor, standart ise **0,2700 m²**'nin tamamını ister. Kullanılabilir alanı
küçük göstermek **emniyetsiz** yöndür: Çizelge 6'nın izin verdiğinden büyük bir
kabine izin verilir. Standardın metni ikiye ayırır — girinti derinliği
≤ 100 mm ise **hariç**, > 100 mm ise *"the **total** available area shall be
included"*.

**⑮'in etkisi.** Kitabın koşulu standarda uyan tasarımları reddediyordu ve
**verdiği öğüt sonuca ulaşmıyordu**: `Sf` gereken güvenlik katsayısıdır ve
halat çapını artırmak `Dt/dh`'yi düşürerek onu **büyütür**. Örnek: Dt = 400 mm ·
dh = 8 mm · 8 halat · yarım daire kanal → `Sf = 7,89`, gerçekleşen `S = 32,54`
— hem 7,89'un hem 12'nin çok üstünde, ama pafta "UYGUN DEĞİLDİR" yazıyordu.
`Sf < 12` yaygındır:

| Kanal | Dt/dh = 40 | 50 | 60 |
|---|---|---|---|
| V Kanal | 20,55 | 14,64 | **11,59** |
| Altı Kesik V Kanal | 15,51 | **11,34** | **9,14** |
| Yarım Daire Kanal | **10,40** | **7,89** | **6,53** |

**⑯'nın etkisi.** Ofis sabiti γ = 45° yapıldığında `Nequiv(t)` 12'den **6,5**'e
iner ve gereken `Sf` düşer; kitapta hiçbir şey değişmiyordu. Ters yönde
β = 100° seçildiğinde 5 → **10** çıkar ve `Sf` **büyür**. Üstelik pafta γ = 38°
yazmayı sürdürüyordu — yani teslim edilen belge, hesabın gerçekten kullandığı
sayıyı göstermiyordu. Altı kesik kanallarda kitap bu sütuna γ değil **β**
yazıyor ( 90 ), pafta da onu "γ" diye basıyordu.

**⑰'nin etkisi.** Halat kütlesinin taraf dağılımı dört yük durumunun üçünde
tersti. 20 duraklı · 76 m seyirli · 8 × Ø13 halatlı 1:1 bir tesiste:

| | Kitap | Doğrusu |
|---|---|---|
| Yükleme T1/T2 | 1,23 | **1,79** |
| Sınır e^(f·α) | 1,71 | 1,71 |
| Sonuç | UYGUN | **UYGUN DEĞİL** |

Kısa kuyularda fark ihmal edilebilir; **yüksek binada belirleyici** olur.

**⑱'in etkisi.** 1275 kg · 1,0 m/s · **2:1** · Dt = 240 mm örneğinde kitap
`M = 85,74 kg·m` yazar, tahrik kasnağının gördüğü moment **42,87 kg·m**'dir.
Motor gücünü etkilemez — `N = Gmax·v/(η′·102)` askı oranından bağımsızdır ve
kitapta doğru kurulmuştur. Ama paftadan moment okuyup makine seçen bir okuyucu
iki katı bir sayı görüyordu.

**⑧'in etkisi.** Kitabın 150 mm'si, m.5.2.5.8.2 a) 1)'deki **yatay**
0,15 m sınırının düşey sınır sanılmasından geliyor görünüyor; standardın
Şekil 7'si raya yatay Xₕ ≤ 0,15 m uzaklıktaki karkas parçaları, paten ve
güvenlik tertibatı için **0,10 m** verir ( Xₕ = 0,30 m'de 0,30 m,
Xₕ ≥ 0,50 m'de 0,50 m ). Kabin üstündeki 1200 mm'nin ise standartta
karşılığı yok: m.5.2.5.7.3, ayakta durulabilen alanın üzerindeki serbest
yüksekliği **seçilen sığınma hacminin yüksekliğine** bağlar — çömelmiş
duruşta ( Çizelge 3 ) **1,00 m**. Program bu sınırı artık ayrı bir sabit
olarak değil, doğrudan sığınma hacminden okur.

Ayrıca kitap ölçüleri `>` ile karşılaştırıyordu; standart **"en az"** dediği
için sınıra **eşit** ölçü de uygundur — program `≥` kullanır.

**⑨'un etkisi.** Kitap η'yı makine tipinden bağımsız 0,92 alıyordu; ofisin
**kendi avan tablosu** ise dişlisiz için 0,85, dişli için 0,50 diyor. Aynı
asansör, aynı ofis, iki pafta:

| | mukavemet ( eski ) | avan | mukavemet ( şimdi ) |
|---|---|---|---|
| Dişlisiz 2:1 | 4,81 kW | 5,23 kW | **5,90 kW** |
| Dişli 2:1 | 4,81 kW | 9,80 kW | **11,07 kW** |

Dişli makinede kitap gerekli gücün **yarısından azını** söylüyordu — emniyetsiz.
Örnek projede seçilen motor 4,9 kW: kitap "uygun" diyordu, program artık
**UYGUN DEĞİL** diyor. Mukavemetin avandan bir tık yüksek çıkması normaldir:
mukavemet halat ağırlığını ( Gh ) da dengesiz yüke katar, avan katmaz.

Tablo artık **iki projede tek kaynaktan** okunur ( `engine/ortak/ofis.py` ) —
ayrışmanın sebebi iki yerde iki kopya olmasıydı.

② · ④ · ⑧'de kitap **emniyetli tarafta** ama yanlış — ⑧ standarda uygun bir
projeyi haksız yere reddeder, kuyu boyunu gereksiz büyütür. **③ · ⑤ · ⑥ · ⑦ ·
⑨'da emniyetsiz tarafta** — hesabı olduğundan iyi gösteriyor.

### Teslim edilen Excel de düzeltilir

Program kitaptan ayrıldığı için, kitap **olduğu gibi** teslim edilseydi aynı
projenin iki belgesi birbirini yalanlardı: pafta *"uygun değildir"* derken
Excel *"uygundur"* derdi. Bu yüzden **teslim edilen kopyada ilgili formüller
düzeltilir** — değerler değil, **formüller**; kitap kendi kendini hesaplamaya
devam eder ve Excel'de girdi değiştirildiğinde de doğru sonucu verir.

**Şablonun HESABINA dokunulmaz.** `templates/MUKAVEMET_HESABI.xlsx` içindeki
formüller, değerler ve tablolar özgün hâlinde kalır; doğrulama testleri
programı ona karşı denetlemeye devam eder. Doğrulama paketi hem şablonun
hesabının değişmediğini hem de teslim kopyasının paftayla **hücre hücre
birebir aynı** olduğunu denetler.

Şablonda hesap dışı **tek** düzeltme yapılmıştır: *Veri Girişi* `B131`
( **Ray Çeliği Rm** ) hücresinin 370 / 440 / 520 açılır listesi, Excel'in
**uzantı biçiminde** ( `x14:dataValidation` ) yazılmıştı. openpyxl bu biçimi
tanımıyor — okurken *"Data Validation extension is not supported and will be
removed"* diye uyarıyor, kaydederken de **atıyordu**:  teslim edilen kitapta o
tek açılır liste kayboluyor, kitabı elle açan biri Rm'ye listede olmayan bir
sayı yazabiliyordu. Doğrulama artık kitabın **kendi düzenine uygun** normal
biçimde duruyor ve sayfa-dışı listeyi `rayçeliğirm` adlandırılmış alanıyla
gösteriyor — kitap `firmalistesi`, `tamponmarka` gibi dört listeyi zaten böyle
kuruyor ve eski Excel sürümleri sayfa-dışı referansı ancak böyle kabul eder.
Teslim edilen kopyada doğrulama sayısı **32 → 33** çıktı, uyarı da sustu.

#### Ofisin ana kitabını düzeltmek

Teslim edilen dosya düzeltiliyor, ama **ofisin masasındaki ana kitap**
düzelmiyordu: onu açıp elle hesap yapan eski — bazıları emniyetsiz —
sonuçları alıyordu. Düzeltilmiş bir kopya üretmek için:

```bash
python3 araclar/kaynak_excel_duzelt.py
```

`MUKAVEMET_HESABI_DUZELTILMIS.xlsx` çıkar. Ofis bunu yeni ana dosya olarak
kullanabilir: içine **hiçbir projenin girdisi yazılmaz**, yalnız formüller
düzeltilir, kitap kendi kendini hesaplamaya devam eder. İçinde bir
**`DÜZELTMELER`** sayfası vardır — her sapmanın gerekçesi ve standart
maddesi, artı **düzenlenen 71 hücrenin** tek tek "kitapta ne yazıyordu /
şimdi ne yazıyor" dökümü. Dosya elden ele dolaşacağı için kayıt dosyanın
İÇİNDE durur.

Doğrulama paketi bu kitabı da denetler: LibreOffice ile yeniden hesaplatılır
ve **motorun ürettiği 168 değerin tamamıyla** karşılaştırılır ( TEST 10 ).

> **Şablon dosyasına dokunulmaz.** `templates/MUKAVEMET_HESABI.xlsx` özgün
> hâlinde kalır — doğrulama paketinin tamamı motoru **ona** karşı denetler ve
> sapmalarımızın gerekçesi kitabın o hücrelerde ne yaptığıdır. Düzeltilmiş
> kitap **ayrı** bir dosyadır.

Elle düzeltmek isterseniz hücreler şunlardır: `11!Q97` ( 30 → 40 ) ·
`11!AO312` ( 0 → `=AH293` ) · `11!AU575` ( sütun 7 → 6 ) · `11!AK190`
( `C61` → `C61*B100` ) · `11!AH105/AH106` ( sabit → girdi ) ·
`11!Q380·Q385·Q477·Q482·Q538·Q596` ( `1+2*` → `ℓ+2*` ) · `11!AD354` ve
`AB39` ( ω tablosu → EN 81-50 formülü ) · `11!AD636` ( 1200 → `=P639*1000` ) ·
`11!AD647` ( 150 → 100 ) · `11!AQ22` ( 0,92 → makine tipi ve askı oranına
bağlı formül ).

#### Kitapta ayrıca bulunanlar

| Bulgu | Ne yapıldı |
|---|---|
| Karşı ağırlık malzemesi açılır listesi **"Döküm"** yazıyor, arama tablosunun anahtarı **"Pik Döküm"** — Excel'de seçilirse **#YOK** | Tablo anahtarı esas alındı |
| NPU **240 · 280 · 300** satırlarında atalet yarıçapı boş — seçilirse **#SAYI/0!** | Program bu seçimi **açık mesajla reddediyor** |
| Seyir mesafesi ve son kat yüksekliği elle giriliyor, durak listesiyle **sessizce çelişebiliyor** | Programda listeden **türetiliyor** |
| `TABLOLAR!U63/U64` ve `X61:Z62` satırları hiçbir hesaba girmiyor | **Ölü artık** — tabloya alınmadı |
| *"Ana Giriş Üstü Durak"* ve *"Makine Tipi"* girdileri hiçbir hesaba girmiyor | Girdi sözleşmesine **alınmadı** |
| `AB38` hücresi "Imin — eylemsizlik momenti" der ama NPU tablosunun **atalet yarıçapı** sütununu okur | Matematiğe göre adlandırıldı — **EN 81-50 m.5.10.3** de λ = Lk/imin, imin = √(I/A) der |

#### Standarda karşı doğrulananlar

Motor yalnız kitaba değil, standardın kendisine karşı da denetlendi — bunların
hepsi **birebir tutuyor**:

- **σperm = Rm / St**, St = 2,25 normal · 1,8 güvenlik tertibatı ( EN 81-20
  Çizelge 15, A5 > %12 ) → 165/205 · 195/244 · 230/288
- **δperm** 5 mm ( güvenlik tertibatlı ray ) · 10 mm ( karşı ağırlık ) — m.5.7.4.6
- **k1** = 2 kaymalı · 3 makaralı ani · 5 ani ( Çizelge 14 ) · **k2** = 1,2
- **ω yöntemi** — EN 81-50 m.5.10.3'ün dört bantlı formülleri; Rm = 370 eğrisi
  kitabın tablosundaki **231 değerin 231'ini** birebir üretiyor ( bu, tablonun
  hangi eğri olduğunu kanıtlar )
- **Fv** = k1·gn·(P+Q)/n + Mg·gn + Fp — EN 81-20 m.5.7.2.3.5
- **σk** = ( Fv + k3·Maux )·ω / A — yardımcı donanım çarpanının **k3 = 1,2**
  olması standart gereğidir ( güvenlik tertibatı durumunda bile )
- **Fy** paydası h·n/2, **Fx** paydası h·n — EN 81-50 Ek C.2.1.1
- **Tahrik eşitsizlikleri** — EN 81-50 m.5.11.2: yükleme ve acil frenlemede
  T1/T2 ≤ e^(f·α), kabin/karşı ağırlık bloke olduğunda T1/T2 ≥ e^(f·α)
- **Sf formülü** — EN 81-50 m.5.12.3; standardın çözümlü örneğini
  ( Dt/dr = 40, Nequiv = 7 → Sf ≈ 16 ) üretiyor
- **Nequiv(p)** = ( Dt/Dp )⁴ · ( Nps + 4·Npr ) — EN 81-50 m.5.12.2
- Birleşik gerilmeler σm + (Fv+k3·Maux)/A ve σk + 0,9·σm
- **Halat emniyet katsayısı** 12 ( ≥ 3 halat ) / 16 ( 2 halat ) — m.5.5.2.2
- **Sehim** 0,7·F·L³/(48·E·I), Fy ↔ Ix eşleşmesi
- **Motor gücü** N = Gmax·v/(η′·102);  102 = 1000/gn ( kgf·m/s → kW ),
  Gmax = F1 − Ga cebirsel olarak **Q/2 + Gh** — güç askı oranından
  bağımsızdır, askı yalnız halat boyu ve verim üzerinden girer
- **Makine kaidesi** basit kiriş statiği:  FA = F1(L−X)/L · FB = F1·X/L ·
  Mmax = F1·X(L−X)/L — ΣF ve ΣM dengede;  σe = M/Wx;  burkulmada
  σb = FB·ω/A ( omega yöntemi ), λ = L1/imin yukarı yuvarlanır
- **Sığınma hacimleri** Çizelge 3 / Çizelge 4 tip 2 ( çömelmiş )
  0,50 × 0,70 × 1,00 m · **açıklıklar** m.5.2.5.7.2 ( 0,50 m ) ·
  m.5.2.5.8.2 ( 0,50 · 0,10 · 0,30 m ) · Şekil 7 ( Xₕ ≤ 0,15 m → 0,10 m )
- **0,035·v²** — TS EN 81-20'de açıklığın değil, kabinin **en üst konumunun**
  tanımındadır ( Çizelge 2 ). Program kuyu ölçülerini anma konumundan aldığı
  için terimi sınıra ekler; eşitsizlik cebirsel olarak aynıdır.

#### Standardın METNİNE karşı bağımsız doğrulama

Kaynak Excel'e karşı karşılaştırma *"kitapla aynı mıyız"* der. Ayrı bir soru
daha vardır: *"standartla aynı mıyız"*. Program bunu da her koşuda denetler —
aşağıdaki sayılar **BS EN 81-20:2014** ve **BS EN 81-50:2014**'ün kendi
metninden çıkarılmıştır ve motorun koduna bakılmadan yazılmıştır:

| Standart | Doğrulanan |
|---|---|
| EN 81-20 Çiz.6 · Çiz.8 · m.5.4.2.3.1 | 28 beyan yükünün azami alanı · kişi sayısı = Q/75 · asgari alan ( 20 kişi üstü +0,115 m² kuralı dâhil ) |
| EN 81-20 Çiz.14 | k1 = 2 · 3 · 5 · k2 = 1,2 |
| EN 81-20 Çiz.15 | σperm = Rm/2,25 ve Rm/1,8 |
| EN 81-20 m.5.5.2.1 · m.5.6.2.2.1 · m.5.7.4.6 | Dt/dh ≥ 40 · Dreg/dreg ≥ 30 · Sf ≥ 8 · 300 N · μmax = 0,2 · δperm 5/10 mm |
| EN 81-20 m.5.2.5.7 · m.5.2.5.8 | altı asgari açıklık · sığınma hacimleri |
| EN 81-50 m.5.10.2 · 5.10.3 · 5.10.4 · 5.10.6 | Mm = 3·Fh·l/16 · ω polinomlarının **katsayıları** · σ = σk + 0,9·σm · δ = 0,7·F·l³/(48·E·I) |
| EN 81-50 m.5.10.5 | σF = Fx·(h₁−b−f)·6 / [ c²·( ℓ + 2·(h₁−f) ) ] |
| EN 81-50 Ek C.2.1 | Fx = k1·gn·(Q·xQ+P·xP)/(n·h) → My → σy = My/Wy · Fv = k1·gn·(P+Q)/n + Mg·gn |
| EN 81-50 m.5.12.3 | Sf bağıntısı, standardın çözümlü örneğini üretiyor |

**Eksen adlandırması standardın kendisidir:** Fx → My → Wy ve Fy → Mx → Wx —
yani x yönündeki kuvvet rayı **y ekseni** etrafında eğer. Kaynak kitap bu
ikisini ters adlandırıyordu ( sayı doğru, ad yanlıştı ) ve kendi sehim
satırlarıyla çelişiyordu; paftayı Ek C ile karşılaştıran bir denetçi olmayan
bir hata görüyordu.

#### Hangi baskıya karşı doğrulandı

Hesaplar **EN 81-20:2020 / EN 81-50:2020**'ye uygundur. Doğrulama metin
olarak **2014** baskısından okundu; bu bir eksiklik değildir, çünkü 2020
baskısının **kendi Avrupa önsözü** şunu yazar:

> *"This document supersedes EN 81-20:2014. This document is a revision of
> EN 81-20:2014. Significant changes made are as follows: — All externally
> referenced standards have now been dated. — A new Annex ZA has been
> developed … **No technical changes have been made during this revision.**"*

Aynı cümle EN 81-50:2020'nin önsözünde de vardır. İki ayrı ulusal
uyarlamadan ( İrlanda **I.S. EN 81-20:2020** · Slovenya **SIST EN 81-50:2020**
ve **SIST EN 81-20:2020** ) birebir aynı metinle teyit edildi. Madde
numaraları da değişmemiştir — programın kullandıklarının hepsi iki baskıda
aynı yerdedir:

| Program | 2014 | 2020 |
|---|---|---|
| Kasnak / halat oranı | 5.5.2 | 5.5.2 ✔ |
| Emniyet gerilmeleri · darbe katsayıları | 5.7.2 · 5.7.4 | 5.7.2 · 5.7.4 ✔ |
| Ray hesabı · burkulma · flanş | 5.10 · 5.10.3 · 5.10.5 | aynı ✔ |
| Tahrik · Nequiv · Sf | 5.11.2 · 5.12.2 · 5.12.3 | aynı ✔ |
| Ray / tahrik / Nequiv örnekleri | Ek C · D · E | aynı ✔ |

**Geçerlilik takvimi:** EN 81-20/50:2020 Şubat 2020'de yayımlandı, Temmuz
2021'de AB Resmî Gazetesi'ne girdi; **2014 baskısı 27 Temmuz 2022'de** uygunluk
varsayımını yitirdi. Bugün geçerli olan 2020 baskısıdır — teknik içeriği 2014
ile aynı olduğu için programda değişiklik gerekmedi.

#### ISO 8100 ve 2026 revizyonu

Hesaplar **TS EN 81-20 / EN 81-50**'ye göre yapılır. Aynı kurallar
**ISO 8100-1 / ISO 8100-2:2019** olarak da yayımlanmıştır — bu iki parça
EN 81-20/50:2014'ün **birebir aynısıdır** ( "identical adoption" ), yani
oradan bakmak aynı sayıları verir. ISO 8100-**32** ise trafik planlamasıdır,
mukavemetle ilgisi yoktur.

**EN ISO 8100-1/-2:2026** yayımlandı; **36 aylık** geçiş süresi işliyor, yani
TS EN 81-20/50:2020 bugün hâlâ geçerli. Avrupa Asansör Birliği'nin ( ELA ) 144
sayfalık karşılaştırma belgesine göre programın yaptığı hesaplarda değişen:

| Konu | 2026 revizyonunda |
|---|---|
| **D/d ≥ 40** ( ① ) | **Değişmedi** — ISO 4344 halatlarında yorulma deneyi yapılmadan eski kural aynen geçerli |
| **Halat emniyet katsayısı** | ISO 4344 halatları için **"gereklilikler değişmedi"** ( m.4.5.2.2.2 ) |
| **Ray hesabı** ( Ek C → **Ek B** ) | Bazı burkulma bağıntılarına **ω eklendi**; birleşik gerilme hesabı tamamlandı; **k3·Maux yerine Faux** yazıldı |
| **Tahrik** | ISO 8100-2 m.4.11 + Çizelge 1'e taşındı; klasik çelik halatta *"küçük değişiklikler"* |
| **Sığınma hacimleri** | Çizelge 3'e **diz çökmüş** duruş eklendi; kuyu-eşik boşluğu 0,15 → **0,12 m** |
| **Makine dairesi çalışma yüksekliği** | 2,10 → **2,00 m** |

Yani ⑤ ( ω ) ve ⑧ ( ray hesabındaki k3 ) için yaptığımız düzeltmelerin yönü
2026 revizyonunda da doğrulanıyor; ① ve Sf ise hiç değişmiyor. Yeni sürüm
esas olarak **yeni askı türlerini** ( elastomer kaplı halat, karbon elyaf
kayış ) ve SIL devrelerini getiriyor — programın kapsamı dışında.

### Doğrulama paketi — kendiniz çalıştırabilirsiniz

Program bir **test paketiyle** birlikte gelir. Şablonu değiştirdiğinizde ya da
programa dokunulduğunda hesabın hâlâ Excel'le birebir olduğunu doğrulamak için:

```bash
python3 testler/calistir.py          # tümü
python3 testler/calistir.py hizli    # Excel taraması hariç (saniyeler)
```

macOS'ta programın kendi Python'unu kullanmak için `./.venv/bin/python3 testler/calistir.py`.

| Test | Ne yapar |
|---|---|
| **1 · Excel uyumu** | 118 senaryoyu şablona yazar, **LibreOffice ile yeniden hesaplatır**, çıkan her hücreyi programla karşılaştırır. Yani hesabı Excel'in kendi formülleri yapar — program değil. |
| **2 · Kenar durumlar** | Tablo sınırları, yuvarlama kuralları, kapsam dışı girdiler, hata mesajları. |
| **3 · Girdi dayanıklılığı** | Bozuk / boş / uç girdilerin binlerce birleşimi ve tüm API uçları — program çökmemeli. |
| **4 · Çıktı bütünlüğü** | Üretilen XLSX ve PDF'ler açılabiliyor mu, hata hücresi var mı, Türkçe karakterler yerinde mi, doğru sayfalar mı? |
| **5 · Arayüz** | Tarayıcıda tüm sekmeler, canlı hesap, aktarım, indirme düğmeleri, kalıcılık, dar ekran, Excel'den geri yükleme. |
| **6 · Geri yükleme** | Her senaryoyu XLSX'e yazıp geri okur; girdilerin birebir döndüğünü doğrular. Excel'de elle düzenlenmiş dosya ve bozuk dosya senaryoları dâhil. |
| **7 · Altın çıktı** | Önceki sürümün tüm çıktısı sıkıştırılmış olarak saklanır; her koşuda satır satır karşılaştırılır. Refactor sırasında **hiçbir sayı sessizce değişemez**. |
| **8 · Mukavemet tabloları** | `engine/uygulama/mukavemet_tablolari.py` içindeki her değeri kaynak Excel'e karşı doğrular. Tablolar makineyle aktarıldı; bir sütun kayması hiçbir hesap testinde görünmezdi — bu test **aktarmanın kendisini** denetler. |
| **9 · Mukavemet motoru** | Excel'in kendi örneğindeki 100 sonuç hücresi; ayrıca geçersiz girdi yolları ve profil / hız / kanal varyantları. |
| **10 · Mukavemet ↔ Excel** | **Girdi uzayını** tarar: 78 farklı girdi bileşimi kaynak kitaba yazılır, LibreOffice 1115 formülü yeniden hesaplar, motorun ürettiği 168 değer hücre hücre karşılaştırılır;  standart gereği sapılan 52 hücre ayrıca 'gerçekten ayrışıyor mu' diye denetlenir. |
| **11 · Uygulama projesi** | **Ortak girdi köprüsünü** denetler: her ortak alan tek tek oynatılır ve elektrik sonucunun gerçekten değiştiği doğrulanır. Köprü sessizce kopabilir ( bir alan adı değişir, biri `None` kalır ) ve hiçbir hesap testi bunu göremez — iki motor da kendi içinde tutarlı çalışmaya devam eder. Ayrıca mukavemet sonucunun birlikte koşarken **kirlenmediği** kanıtlanır. |

Test 1 ve 10 **LibreOffice**, Test 3 ve 5 **programın açık olmasını**, Test 5
ayrıca **Playwright**, Test 4 ise **pypdf** ister. Eksik olan test **atlanır** —
diğerleri yine çalışır, paket hata vermez. Bunlar programın çalışması için
gerekli değildir; `requirements.txt` içinde isteğe bağlı olarak listelenmiştir:

```
pip install playwright pypdf  &&  playwright install chromium
```

Atlanan bir test "geçti" sayılmaz; özet tablosunda **atlandı** olarak görünür.
Yani eksik bir bağımlılık, doğrulanmamış bir alanı doğrulanmış gibi göstermez.

Tablo-3 (H) ve Tablo-5 (S) için MMO/697'nin kapalı formülleri kullanılır:

```
H = N − Σ(i/N)^P        (i = 1…N−1)
S = N · ( 1 − ((N−1)/N)^P )
```

Bu formüllerin Excel'deki tablo değerleriyle farkı en fazla **5×10⁻¹⁴**'tür.
Kapsam tablo sınırlarıyla aynıdır: **P = 6…34 kişi, N = 1…30 kat.**

---

## 7. Hesabın sınırları — dikkat edilecekler

- **N > 30 kat**: MMO/697 Tablo-3/5 en fazla 30 katı kapsar. Program hesabı
  durdurur ve **bölgeli (zoned) trafik hesabı** gerektiğini bildirir.
- **Kapı genişliği**: listedeki yedi genişliğin (700 – 1300 mm) **tamamı
  hesaplanır**. MMO Tablo-4'te 1000 ve 1200 mm, ISO 8100-32 Tablo 6'da 700 mm
  basılı değildir; bu üç değer komşu tablo satırlarından **enterpolasyon /
  dış değerleme** ile türetilir ve paftada kaynağı *"ara değer"* olarak yazılır
  (Tablo-6'daki 1,75 ve 3,00 m/s ile aynı yöntem). Tek istisna: *"Kabin İçi Oto.
  Kat K.Ç."* kapı tipi 1200 ve 1300 mm'de tabloda hiç yoktur — bu ikisinde
  program imalatçı ta/tk değerinin elle girilmesini ister.
- **1,75 ve 3,00 m/s**: Tablo-6'da satır başlığı değildir; tg doğrusal
  enterpolasyonla bulunur ve paftada *"ara değer"* olarak yazılır.
- **15 kişi / 1125 kg**: Tablo-7'de yoktur; MMO/697 s.53-54 örneğinde geçtiği
  için *örnek istisnası* olarak desteklenir.
- **Kamu binaları**: Tablo-2'de hız, Tablo-9'da %k verilmemiştir. Program
  Büro/İş Merkezi değerlerini varsayar ve **her iki varsayımı da paftaya yazar**;
  %k elle değiştirilebilir.
- **Karma binalar, poliklinik, katlı otopark**: Tablo-2 ve/veya Tablo-9'da
  değer yoktur — hız ve/veya k **elle girilmelidir**, gerekçesi paftaya yazılır.
- **Topraklama**: TT sistem, UL = 50 V, IΔn = 300 mA kabulüyle hesaplanır.
  Şebeke TN sistemse bu kontrol ölçütü geçerli değildir. Hesaplanan değer
  **tahminîdir — tesis tamamlandıktan sonra ölçümle doğrulanmalıdır.**
- **L1 (kolon hattı uzunluğu)**: gerçek kablo güzergâhıdır — ana panodan asansör
  panosuna yatay + düşey toplam. **Kuyu yüksekliğine eşit kabul etmeyin,
  plandan ölçün.**
- **Kılavuz ray > 40 m**: halat / kompanzasyon kuvveti Fp uygulama projesinde
  ayrıca hesaplanır (MMO/697 s.20).
- **Bodrum durağı (⑪)**: ana giriş altında hizmet verilen durak adedidir.
  MMO/697 s.14 ve s.16, H (Tablo-3) ve S (Tablo-5) büyüklüklerini **ana giriş
  üstündeki** kat adedi N üzerinden tanımlar; yukarı yoğun trafikte tur ana
  giriş katından başlar. Bu yüzden bodrum durağı **H, S ve TR'yi değiştirmez**;
  yalnız (a) Tablo-2 asgari hız seçimindeki durak adedine (N + 1 + Nb) ve
  (b) toplam seyahat mesafesine ((N + Nb) · h) girer. Program bu notu paftaya
  basar. Hem tek hem çoklu sayfada, çokluda ayrıca asansör bazında girilir.
- **Erişilebilirlik**: 630 kg (8 kişi) altındaki kabin ve 800 mm altındaki net
  kapı, TS EN 81-70 / TS 9111 ölçütünü karşılamaz. Program bunu **uyarır** ve
  otomatik öneri sıralamasına almaz; hesabı durdurmaz — karar projecinindir.
- **Trafik ↔ avan tutarlılığı**: avan sekmesi, trafik hesabındaki kapasite,
  hız ve toplam seyahat mesafesiyle karşılaştırılır. Trafikte
  bir şey değişirse avan sekmesi sessizce eski değerde kalmaz — uyarı çıkar.
  Kuyu yüksekliği Hk ile seyahat mesafesi arasındaki pay (kuyu dibi + üst
  boşluk) da makul aralıkta mı diye kontrol edilir.

### Uygulama projesi — mukavemet

- **Kaynak kitaptan ayrılan yirmi iki nokta** 6. bölümdeki tabloda sayılıdır; her
  biri kodda `engine/uygulama/mukavemet.py` · `EXCEL_FARKLARI` içinde standart maddesiyle
  birlikte durur ve ekranda bölüm başlığının yanındaki **( ! )** simgesinden
  okunabilir.
- **Paten balatası uzunluğu ( ℓ )** flanş eğilmesine girer ( EN 81-50 m.5.10.5 ).
  Boş bırakılırsa ray tablosundaki balata yarı genişliğinden **2·b** olarak
  türetilir — kare balata kabulüdür, gerilmeyi emniyetli tarafta ( büyük )
  bırakır. **Kesin değer paten imalatçısından alınmalıdır.**
- **Sığınma alanı payları** ( kabin gövde yüksekliği 2400, kabin üstü kotu 2100,
  revizyon kutusu 500, etek 400 / 950, ray altı 270 mm ) kaynak kitabın **ofis
  kabulüdür — TS EN 81-20 sayısı değildir.** Farklı kabin imalatında
  `engine/uygulama/mukavemet.py` içindeki `SIGINMA` sözlüğünden güncellenmelidir.
  Buna karşılık aynı sözlükteki **asgari açıklıklar** ( 100 · 500 · 500 · 100 ·
  100 · 300 mm ve sığınma hacimleri ) doğrudan **TS EN 81-20 m.5.2.5.7 /
  m.5.2.5.8**'dendir — her satırın karşısında madde numarası yazılıdır ve
  ofis kabulü olarak değiştirilmemelidir. Ray dibi açıklığı, parçanın raya
  **yatay Xₕ ≤ 0,15 m** uzaklıkta olduğu kabulüyle Şekil 7'den 0,10 m alınır;
  daha uzaktaki parçalar için sınır 0,30 m ( Xₕ = 0,30 ) ve 0,50 m
  ( Xₕ ≥ 0,50 ) olur.
- **Sürtünme yükü Gs = 0**, **ST 37 emniyet gerilmesi σem = 130 N/mm²**,
  **yan yatak mesnet payı 335 mm** kitabın kabulleridir; hepsi `SABIT`
  sözlüğünde, yanlarında Excel hücre adresiyle durur. ( **Motor verimi η**
  artık sabit değildir — makine tipinden gelir, bkz. sapma ⑨. )
- **Motor gücü N kararlı rejim gücüdür.** Beyan hızındaki dengesiz yükü
  karşılar; **kalkış ( ivmelenme ) momenti** — kabin, karşı ağırlık, halat,
  kasnak ve rotor ataletleri — hesaba girmez. Motor seçiminde üretici kalkış
  verisi ayrıca kontrol edilmelidir.
- **Karşı ağırlık denge oranı q = 0,50 sabittir** ( Ga = P + Q/2 ). Kaynak
  kitabın tamamı bu kabul üzerine kuruludur — karşı ağırlık kütlesi tahrik,
  ray ve tampon hesaplarına da aynı yerden girer.
- **Makine kaidesinde ( bölüm 2 ) darbe katsayısı k1 ve σem ofis kabulüdür.**
  TS EN 81-20 makine kaidesi için yük modeli **vermez** — Çizelge 14
  ( k1·k2·k3 ) o standartta açıkça **kılavuz ray** hesabına aittir. Buradaki
  kullanım ödünçtür ve **emniyetli** taraftadır: k1 makinenin kendi ağırlığına
  da uygulanır ve σem = 130, aynı standardın ST 37 için verdiği
  Rm/1,8 = 205,6 N/mm²'nin yaklaşık yarısıdır. Güvenlik tertibatı tipi bu
  bölümü doğrudan büyütür ( k1 = 2 · 3 · 5 → kaide yükü 2,5 kata kadar ).
- **Ray tablosunda bir tutarsızlık işaretlidir.** Atalet yarıçapı tanım
  gereği i = √(I/A)'dır ( kaynak kitabın kendi 60. satırı da bunu formülle
  hesaplar ). `125 x 82 x 16` profilinde `iy = 25,20` yazılı, ama aynı
  satırdaki I ve A `26,15` veriyor — %3,6. O satırda A, Ix ve ix birbiriyle
  tutarlıdır; tutmayan tek sayı `iy`'dir. **Değer değiştirilmedi**: küçük iy
  narinliği büyük gösterir, yani burkulma emniyetli tarafta hesaplanır.
  Doğrusu **ISO 7465'ten ya da ray imalatçısının veri sayfasından** teyit
  edilmelidir; o profil seçilince pafta uyarı basar.
- **Burkulma boyu Lk = L1 alınır** ( β = 1,0 — iki ucu mafsallı ). Kolon tek
  ucundan ankastre, öbür ucu serbestse bu kabul narinliği **olduğundan küçük**
  gösterir; öyle bir konstrüksiyonda λ elle iki katına çıkarılmalıdır.
- **Acil frenleme yavaşlaması a**, TS EN 81-20 gereği **en çok 1 gn**'dir; program
  bunu denetler. Tam **a = 1 gn** sınırında kabin tarafındaki halat kuvveti
  sıfırlanır — program tahrik yeteneğini *UYGUN DEĞİL* sayar ( kaynak Excel bu
  noktada **#SAYI/0!** verir ).
- **Kabin alanı tablosu** mukavemet kitabının kendi tablosudur ve avandakinden
  **bilerek ayrıdır** — 320 kg satırı burada vardır, avanın Tablo-11'inde yoktur.
- **Boş kabin ağırlığı ( P ) bir TAHMİNDİR — standardın sayısı değildir.**
  TS EN 81-20 ve TS EN 81-50 P'yi geçtiği dokuz yerin hiçbirinde tablolamaz;
  hep *"the mass of the empty car and components supported by the car"* diye
  **girdi** olarak tanımlar. ISO 4190-1 aynı yük serisi için kabin
  **ölçülerini** verir, kütle vermez. Program boş bırakılan alanı ofisin
  kendi tablosundan doldurur ( `engine/ortak/ofis.py` ) ve paftaya kaynağını
  *"OFİS TABLOSU"* diye basar. **Uygulama projesinde imalatçı verisiyle
  değiştirilmelidir**:  P hatası iki yönde birden emniyetsizdir — 100 kg fark
  ray kuvvetini, kuyu tabanı yükünü ve tampon kuvvetini %5–7 **artırır**
  ( yani küçük almak emniyetsiz ), buna karşılık tahrik oranı T1/T2'yi %3
  **düşürür** ( yani büyük almak tahriki olduğundan iyi gösterir ). Motor
  gücü etkilenmez:  P, Gmax = F1 + Gs − Ga bağıntısında sadeleşir.
- Uygulama projesi **tek asansör** içindir. Grup projesinde her asansör için
  ayrı koşturulup ayrı pafta alınır.
- **Elektrik hesapları avan motorunun aynısıdır** ( `engine/avan/hesap.py` ) — avan
  projesindeki bütün sınırlar burada da geçerlidir: topraklama TT sistem,
  UL = 50 V, IΔn = 300 mA kabulüyle hesaplanır ve **tesis tamamlandıktan sonra
  ölçümle doğrulanmalıdır**; L1 gerçek kablo güzergâhıdır, kuyu yüksekliğine
  eşit kabul edilmemelidir.
- **Motor gücü:** uygulama projesinde paftaya mukavemetin **MMO 208/7** hesabı
  basılır. Avan projesindeki MMO/697 hesabı farklı bir formüldür ( halat
  ağırlığını almaz, palanga verim düşüşü uygular ) ve küçük bir fark verir —
  aynı asansörün iki projesinde iki değer görülmesi normaldir. Kurulu güç
  cetveli her iki tarafta da **seçilen** motor gücünü ( Nsç ) kullanır — ama
  cetvele yazılan sayı **şebekeden çekilen** güçtür ( Pşeb = Nsç / ηm );
  hatta akan odur ve kesitler ondan seçilir.
- **Çift sarımda sarılma açısı α tek sarım bağıntısıyla hesaplanır**
  ( α = 180° − arctan(A/B), yani **α ≤ 180°** ). Gerçekte halat kasnağı iki kez
  dolanır ve α bunun yaklaşık iki katıdır. Hesap bu yüzden tahrik yeteneğini
  **olduğundan kötü** gösterir — emniyetli taraftadır, ama "Yarım Daire Kanal
  ( Çift Sarım )" seçildiğinde bölüm bunu not olarak yazar ve gerçek α saptırma
  düzenine göre ayrıca belirlenmelidir. `Nequiv(t)` ise çift geçişle doğru
  hesaplanır.
- **Tahrik yeteneğinde dört yük durumu hesaplanır**: yükleme, en altta ve en
  üstte acil frenleme, karşı ağırlığın asılı kalması. TS EN 81-50 m.5.11.2.2.3
  bloke durumunu *"empty car at the **highest and lowest** position"* der;
  program üsttekini kurar. **Kabinin tampona oturduğu** karşı durum ( kaynak
  kitabın da hesaplamadığı ) modellenmez — kuyu dibine girilebiliyorsa bu
  durum ayrıca değerlendirilmelidir.
- **Konsol itme kuvveti Fp modellenmez.** TS EN 81-50 Ek C.1.3 `Fp`'yi
  *"push through forces of all brackets at one guide rail ( due to normal
  settling of the building or shrinkage of concrete )"* diye tanımlar ve
  C.2.1.2 / C.2.2.2'de Fv'ye ekler. Betonarme kuyuda oturma / rötre bekleniyorsa
  bu kalem ayrıca hesaplanmalıdır.
- **Ray narinliği λ = konsol arası / ix, 250'yi aşamaz.** ω tablosu
  ( m.5.10.3 ) o aralıkta tanımlıdır; program aşan girdiyi **izin verilen en
  büyük konsol aralığını söyleyerek** reddeder. `λ < 20` burkulmanın belirleyici
  olmadığı bölgedir, tablonun ilk satırı kullanılır.
- **Sigorta ↔ kablo koordinasyonu ayrıca denetlenmez.** `sigorta_sec` yalnız
  `1,25 × In`'e bakar; IEC 60364-4-43'ün `In ≤ Iz` şartı doğrudan kontrol
  edilmez. `I ≤ Iz` ve `I2 ≤ Iz2` kontrolleri çoğu durumu dolaylı yakalar,
  ama seçilen kademe kablo kapasitesiyle ayrıca karşılaştırılmalıdır.
- **Regülatörün ikinci kuvvet sınırı imalatçı verisi ister.** TS EN 81-20
  m.5.6.2.2.1.1 d) *"güvenlik tertibatını devreye sokmak için gerekenin iki
  katı"* der; bu kuvvet tertibatın **tip inceleme belgesinden** gelir.
  Girilmezse madde **denetlenemez**: bölüm *"HESAP EKSİK"* der ve proje
  **uygundur çıkmaz**. Sınır, regülatörün ÜRETTİĞİ kuvvete uygulanır
  ( `Fçekme = F′reg − Freg` ) — halattaki toplam gerginliğe değil; halatın
  emniyet katsayısı ( ≥ 8 ) ise `F′reg`'e karşı hesaplanır ( m.5.6.2.2.1.3 b ).

---

## 8. Ofis standardını değiştirmek

> **İKİ PROJENİN OFİS STANDARDI AYRIDIR.** Sabitler sekmesi her iki projede de
> vardır ama **içerikleri farklıdır** — avan yaparken uygulamanın kabullerini,
> uygulama yaparken avanınkini görmezsiniz.
>
> Avan **ön tasarımdır**: genel, emniyetli kabullerle çalışır. Uygulama **kesin
> tasarımdır**: elinizde imalatçı verisi vardır. Dişlisiz makine için avanda
> 0,85 kabulü yeterliyken uygulamada makinenin kataloğundaki değer kullanılabilir.
> **İkisinin aynı sayıyı tutma zorunluluğu yoktur.**
>
> Fabrika ayarı ortaktır (`engine/ortak/ofis.py`): ikisi de oradan başlar,
> sonrası her projenin kendi kararıdır. Her değer paftaya **kaynağıyla**
> basıldığı için ayrışırlarsa bilerek ayrışırlar.

### Uygulama projesinin ofis standardı

**45 alan, 6 grup** — `engine/uygulama/sabitler.py`:

| Grup | İçindekiler |
|---|---|
| ① Makine ve motor | dişlisiz / dişli verimi, palanga düşüşü, Gs, q, halat payı, **kanal açıları γ ve β** |
| — | Boş kabin kütlesi tablosu **ekrandan değiştirilmez** ( `engine/ortak/ofis.py` · `GK_TABLOSU` ) — iki proje de aynı tablodan okur |
| ② **Mukavemet kabulleri** | **σem**, **k1** (kaymalı · makaralı · ani), yan yatak mesnet payı |
| ③ Sığınma payları | kabin gövde yüksekliği, kabin üstü kotu, tavan / etek / ray altı payları |
| ④ Aydınlatma | kabin · kuyu armatürleri, azami aralık, tablo sütunu |
| ⑤ Kurulu güç ve gerilim düşümü | U · κ · εmax · cosφ · priz · kablo tipi · sigorta katsayısı |
| ⑥ Temel topraklama | β · çubuk adedi · karelaj gözü · çubuk boyu · UL · IΔn |

**② özellikle gözden geçirilmelidir.** σem = 130 ve k1 = 2/3/5 bugüne kadar
**kodda gömülüydü**, artık ekranda. TS EN 81-20 makine kaidesi için yük modeli
**vermez** ve Çizelge 14 (k1) o standartta açıkça **kılavuz ray** hesabına
aittir — buradaki kullanım ödünçtür ve emniyetli taraftadır (σem = 130,
standardın ST 37 için verdiği Rm/1,8 = 205,6 N/mm²'nin yaklaşık yarısı).
Kiriş gereğinden kalın çıkıyorsa bakılacak yer burasıdır.

Buradan değiştirdiğinizde **ekrandaki hesap, PDF paftası ve indirilen Excel
birlikte** değişir — teslim edilen kitaptaki formüller de bu değerleri kullanır.

**Tablolar sekmesi de ayrıdır.** Uygulamanın 14 tablosu (ray profilleri, NPU
kesitleri, halat ağırlıkları, ω burkulma, kabin alanları, kanal katsayıları …)
bugüne kadar **yalnız motorun içindeydi** — hesaba giriyorlardı ama ekranda
görünmüyorlardı. Tablolar kopyalanmaz; motorun kendi sözlüklerinden okunur, o
yüzden ekrandaki tablo ile hesaba giren tablo ayrışamaz.

### Avan projesinin ofis standardı

**Sabitler / Ofis Standardı** sekmesindeki değerler proje geneli için ortaktır
(palanga, denge faktörü, ray sayısı, flexbil, montör, armatürler, priz, cosφ,
UL, IΔn, çubuk boyu, aydınlatma verimi sütunu). Buradan değiştirdiğinizde hem
ekrandaki hesap hem XLSX çıktısı birlikte değişir.

**Askı oranı (i) artık burada değil, asansörün kendi girdisidir** — avan
sekmesinde makine tipiyle yan yana durur (Excel'de GİRİŞ 53. satır). Bir projede
dişlili ve dişlisiz makine ya da 1:1 ve 2:1 askı birlikte kullanılabildiği için
bu değer, makine verimi η gibi, asansöre özeldir.

**Denge faktörü (q)** ofis standardında kalır (uygulamada hep 0,50); gerekirse
asansör bazında **"Denge faktörü"** bölümünden ezilebilir (GİRİŞ 54. satır).

### Verim (η) nasıl kullanılıyor?

| Makine tipi | Askı | η (MMO/697 s.21) | η′ (hesapta kullanılan) |
|---|---|---|---|
| Dişli | 1:1 | 0,50 | **0,50** |
| Dişli | 2:1 | 0,50 | **0,40** |
| Dişlisiz | 1:1 | 0,85 | **0,85** |
| Dişlisiz | 2:1 | 0,85 | **0,75** |

Askı oranı motor gücüne **yalnız verim üzerinden** girer: N = (1−q)·Q·V / (102·η′)
bir *güç* bağıntısıdır ve güç askı oranından bağımsızdır — 2:1 askıda halat hızı
yarıya iner, kuvvet iki katına çıkar, çarpımları değişmez. Askı oranının etkisi
MMO/697 §2.4'teki **Δη = 0,10** verim düşüşüdür.

Yukarıdaki değerler **makine** verimidir ve emniyetli taraftadır. İmalatçı
katalogları genellikle **toplam sistem verimi** verir (makine × dişli × askı ×
motor) — uygulamada dişli sistemlerde ≈ 0,52 – 0,78, dişlisizlerde daha üstü.
Öyle bir değer kullanacaksanız asansörün altındaki **"Girilen η toplam sistem
verimidir"** kutusunu işaretleyin: palanga düşüşü ikinci kez uygulanmaz ve
paftaya hangi esasın kullanıldığı yazılır. İşaretlemezseniz askı kaybı **iki kez**
düşülür ve motor gereğinden büyük çıkar.

Yönetmelik / standart sabitleri (A bölümü) programda **kilitlidir** ve
değiştirilemez.

---

## 9. Klasör yapısı

**Avan projesi ile uygulama projesi her katmanda ayrıdır** — hesap motoru, API
uçları ve arayüz betikleri ayrı dosyalarda. Ortak olan yalnız gerçekten ortak
olan şeyler: adım yapısı, sayı biçimi, çizim yardımcıları ve indirme.

```
AVAN HESAPLAMA PROGRAMI/
├── baslat.command          ← macOS: çift tıklayın
├── baslat.bat              ← Windows: çift tıklayın
├── main.py                 ← sunucu kabuğu:  uygulamayı kurar, uç paketlerini
│                              bağlar, ana sayfa · Excel yükleme · sağlık
├── requirements.txt
├── OKUBENI.md              ← bu dosya
│
├── engine/                 ← HESAP MOTORLARI  ( arayüzden ve sunucudan bağımsız )
│   ├── ortak/
│   │   ├── steps.py        ← işlem adımı yapısı, Türkçe sayı biçimi
│   │   └── ofis.py         ← FABRİKA AYARI:  iki projenin ofis standardı da
│   │                          buradan başlar ( makine verimleri, palanga düşüşü )
│   ├── avan/               ─────────────────────────────── AVAN PROJESİ
│   │   ├── tablolar.py     ← MMO/697 + ISO + IEC tabloları
│   │   ├── trafik.py       ← trafik hesabı ( tek + çoklu )
│   │   └── hesap.py        ← avan hesapları
│   └── uygulama/           ─────────────────────────── UYGULAMA PROJESİ
│       ├── mukavemet_tablolari.py ← ISO 7465 · TS 12385-5 · EN 81-50
│       ├── mukavemet_girdi.py     ← 71 girdinin sözleşmesi ( TEK KAYNAK )
│       ├── mukavemet.py           ← 10 bölümlük mukavemet hesabı
│       ├── sabitler.py            ← UYGULAMANIN KENDİ OFİS STANDARDI
│       │                             ( 45 alan · avanınkinden ayrı )
│       ├── tablolar_gorunum.py    ← 14 tablonun EKRAN GÖRÜNÜMÜ
│       │                             ( kopya değil — motorun sözlüğünden okur )
│       ├── girdi.py               ← ek girdiler + ORTAK GİRDİ KÖPRÜSÜ
│       └── hesap.py               ← mukavemet + elektrik orkestratörü
│
├── api/                    ← HTTP UÇLARI
│   ├── ortak.py            ← sayı çevirme · belirsiz yazım denetimi ·
│   │                          proje kimliği · dosya adı · indirme yanıtı
│   ├── avan.py             ← trafik · avan · kapak ve çıktıları  ( 10 uç )
│   └── uygulama.py         ← mukavemet + elektrik ve çıktıları  (  5 uç )
│
├── exports/                ← BELGE ÜRETİMİ
│   ├── hucre_haritasi.py   ← girdi alanı ↔ Excel hücresi eşlemesi (TEK KAYNAK)
│   ├── xlsx_export.py      ← avan şablonunu dolduran XLSX çıktısı
│   ├── xlsx_import.py      ← avan Excel'inden geri yükleme ( revizyon )
│   ├── mukavemet_xlsx.py   ← mukavemet kitabını doldurur, STANDARDA UYDURUR
│   │                          ve geri okur
│   ├── pdf_export.py       ← baskıya hazır PDF  ( trafik · avan · uygulama )
│   ├── dxf_export.py       ← CAD çıktısı  ( ortak )
│   └── kapak_export.py     ← avan proje kapağı
│
├── static/                 ← ARAYÜZ.  Yükleme sırası önemli:
│   ├── index.html
│   ├── style.css
│   ├── ortak.js            ← biçimleme · sekme şeridi ve MOD anahtarı ·
│   │                          çizim yardımcıları · indirme · kalıcılık ·
│   │                          Excel'den proje açma · açılış ekranı
│   ├── avan.js             ← trafik · avan · ofis standardı · tablolar
│   └── uygulama.js         ← mukavemet + elektrik  ·  en sonda kur() çağrısı
│
├── testler/                ← doğrulama paketi
│   ├── calistir.py         ← hepsini çalıştırır
│   ├── test_excel_uyumu.py · test_kenar_durum.py · test_dayaniklilik.py
│   ├── test_ciktilar.py · test_arayuz.py · test_geri_yukleme.py
│   ├── test_altin.py       ← altın çıktı kalkanı
│   ├── altin_uret.py       ← altın çıktıyı yeniden üretir
│   ├── test_mukavemet_tablolari.py · test_mukavemet.py
│   ├── test_mukavemet_excel.py
│   └── test_uygulama.py    ← ortak girdi köprüsü
│
├── templates/              ← OFİSİN KENDİ EXCEL ŞABLONLARI
│   ├── ASANSOR_TRAFIK_HESABI_v2_1.xlsx  ┐ avan
│   ├── ASANSOR_AVAN_HESAPLARI.xlsx      ┘
│   └── MUKAVEMET_HESABI.xlsx            ← uygulama projesi
└── fonts/                  ← PDF için Türkçe karakter destekli yazı tipi
```

### İki proje neyi paylaşır, neyi paylaşmaz

| Paylaşılan | Niçin |
|---|---|
| `engine/ortak/steps.py` | Hesap adımlarının yapısı ve sayı biçimi — iki pafta da aynı dilde konuşsun |
| `pdf_export.py` çizim yardımcıları | İki paftanın aynı programdan çıktığı belli olsun |
| `api/ortak.py` | Sayı okuma ve belirsiz yazım denetimi tek yerde kalsın |
| `dxf_export.py` | CAD yerleşimi hesaptan bağımsız |
| **Avanın elektrik motoru** | Uygulama projesindeki aydınlatma · kurulu güç · gerilim düşümü · topraklama, avanın `engine/avan/hesap.py`'sini **çağırır**. Kopyalanmaz — iki kopya zamanla ayrışır |

| `engine/ortak/ofis.py` | **Fabrika ayarı** — iki projenin ofis standardı da buradan başlar. Ayrı ayrı değiştirilebilirler, ama sıfır noktaları ortaktır |
| **Boş kabin kütlesi tablosu** ( `ofis.py` · `GK_TABLOSU` ) | Aynı asansör iki projede aynı kabin kütlesiyle hesaplansın. İki kopya tutulsaydı biri güncellenir, öteki unutulurdu |

| Paylaşılmayan | Niçin |
|---|---|
| **Ofis standardı** | Avan ön tasarım, uygulama kesin tasarım — kabulleri aynı olmak zorunda değil. Her projenin kendi Sabitler ekranı var |
| **Tablolar** | Mukavemet kendi kaynağından gelir; kabin alanı tablosu bile bilerek ayrıdır. Her projenin kendi Tablolar sekmesi var |
| **Veri kovası** | `avan_program_v1` · `uygulama_program_v1` — biri diğerini görmez, "Tümünü temizle" yalnız kendi projesini siler |
| **Proje dosyası** | `.avan` · `.uygulama` — her biri yalnız kendi alanlarını taşır, yanlış moda yüklenmez |
| Çalışma kitapları | Her proje kendi Excel'iyle teslim edilir |
| Sekme şeridi ve girdi formları | Moda göre ayrılır. Sabitler ve Tablolar sekmeleri ikisinde de vardır ama **içerikleri ayrıdır** |

### Şablonu güncellemek
Excel dosyalarınızda **biçim, açıklama veya sayfa düzeni** değişirse
`templates/` içindeki dosyaların üzerine yazmanız yeterlidir — XLSX çıktısı
kendiliğinden yeni şablonu kullanır.

**Formül veya tablo değeri** değişirse `engine/avan/tablolar.py` (tablo değerleri)
ya da `engine/avan/trafik.py` / `engine/avan/hesap.py` (formüller) de
güncellenmelidir; aksi
hâlde ekrandaki sonuç ile XLSX çıktısı ayrışır.

**Mukavemet kitabı** ( `MUKAVEMET_HESABI.xlsx` ) hem şablon hem de doğrulama
kaynağıdır. Üzerine yeni bir sürüm yazarsanız `python3 testler/calistir.py 8 9 10 11`
komutu, tablo ve formüllerin hâlâ tutup tutmadığını **tek seferde** söyler:
tablolar aktarımıyla, motor da 78 senaryoda kitabın kendi hesabıyla
karşılaştırılır. Tutmuyorsa ne değiştiğini hücre adresiyle bildirir.

---

## 10. Ekibe dağıtım

Klasörün tamamını kopyalayın (ağ sürücüsü, USB veya paylaşılan klasör).
Her bilgisayarda ilk çalıştırmada kendi kurulumunu yapar.

Tek dosyalık `.app` / `.exe` isterseniz PyInstaller ile paketlenebilir:

```bash
./.venv/bin/pip install pyinstaller
./.venv/bin/pyinstaller --onefile --add-data "static:static" \
    --add-data "templates:templates" --add-data "fonts:fonts" \
    --name "Asansor Avan" main.py
```

---

## 11. Sorun giderme

| Belirti | Çözüm |
|---|---|
| Tarayıcı açılmıyor | Adres çubuğuna `http://127.0.0.1:8760` yazın |
| "Port kullanımda" | Program kendiliğinden boş bir porta geçer; adresi açılan pencerede yazar |
| Program iki kez açıldı | İkinci kopya yeni pencere açmaz, var olan sekmeyi öne getirir |
| PDF'de Türkçe karakter bozuk | `fonts/` klasöründeki iki `.ttf` dosyasının yerinde olduğundan emin olun |
| XLSX'te değerler boş görünüyor | Excel/LibreOffice'te bir kez **F9** (yeniden hesapla) |
| Sonuç "HESAP HATASI" diyor | Kırmızı kutudaki mesaj hangi girdinin eksik/kapsam dışı olduğunu söyler |
| Hesabın doğruluğundan kuşkulandınız | `python3 testler/calistir.py` — Excel'e karşı 3.600+ kontrol koşar |

---

*MMO/697, 2. Baskı, Ocak 2020 · TS EN 81-20 · ISO 8100-32:2020 ·
IEEE Std 80 · IEC 60364-5-52 · BYKHY md.4*
