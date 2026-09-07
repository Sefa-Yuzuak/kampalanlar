# -*- coding: utf-8 -*-
"""kampalanlar.com — rehber ve düz sayfa içeriklerini üretir.

Her rehberin ayrışma noktası yaygın bir yanlışı düzeltmek. Sayısal her iddia
resmî kaynaktan doğrulanmıştır; kaynak numaraları `kaynaklar` dizisinin sırasına bağlıdır.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

KOK = Path(__file__).resolve().parent.parent
G = "2026-09-07"

REHBERLER = [
{
 "slug": "ormanda-kamp-yasak-mi",
 "baslik": "Ormanda kamp yasak mı? 2026 cezası ve yasal durum",
 "ozet": "Türkiye'de ormanda çadır kurmak yasal mı, ceza ne kadar, nerede kamp yapılabilir. "
         "6831 sayılı Orman Kanunu ve OGM'nin 2026 ceza cetvelinden.",
 "cevap": "Devlet ormanlarında, Orman İdaresince belirlenen konak yerleri dışında gecelemek "
          "6831 sayılı Orman Kanunu'nun 76/a maddesiyle yasaklanmıştır. Yani \"vahşi kamp\" "
          "hukuken serbest değildir. OGM'nin 2026 yılı ceza cetveline göre bu ihlalin idari "
          "para cezası 4.293 TL'dir. Kamp yapılabilecek yerler; DKMP'nin ücret tarifesi "
          "kapsamındaki korunan alan kamp alanları ile OGM'nin tescilli mesire yerleridir.",
 "guncelleme": G,
 "bolumler": [
  {"tur": "uyari", "metin": "İnternette yaygın olarak dolaşan \"izinsiz çadır cezası 58.945 TL\" "
   "bilgisi, OGM'nin 2026 yılı resmî ceza cetveliyle uyuşmuyor. Cetvelin 16. sayfasında "
   "76/1-a maddesi karşısındaki tutar 4.293 TL olarak yazılıdır (1). Bu sayfadaki rakam "
   "doğrudan o cetvelden alınmıştır."},

  {"tur": "baslik", "metin": "Kanun ne diyor?"},
  {"tur": "metin", "metin": "6831 sayılı Orman Kanunu'nun 76. maddesi, devlet ormanlarında "
   "yapılması yasak olan fiilleri sayıyor (2). Kampçıyı doğrudan ilgilendiren iki bent var:"},
  {"tur": "madde", "maddeler": [
    "76/a — Orman İdaresince belirlenen konak yerlerinden başka yerlerde gecelemek.",
    "76/b — Orman İdaresince belirlenen ocak yerleri dışında ateş yakmak."]},
  {"tur": "metin", "metin": "Buradaki ölçüt \"ormanın içinde olmak\" değil, \"idarece belirlenmiş "
   "bir yerde olmak\". Tescilli bir mesire yerinde ya da kamp alanında geceliyorsanız yasal, "
   "kendi seçtiğiniz bir orman parçasında geceliyorsanız değil."},

  {"tur": "baslik", "metin": "2026 cezaları"},
  {"tur": "tablo",
   "basliklar": ["İhlal", "Dayanak", "2026 idari para cezası"],
   "satirlar": [
    ["Belirlenen konak yeri dışında gecelemek", "6831 s.K. m.76/1-a", "4.293 TL"],
    ["Belirlenen ocak yeri dışında ateş yakmak", "6831 s.K. m.76/1-b", "Cetveldeki ilgili satıra bakınız"]],
   "not": "Tutar, OGM'nin \"2026 Yılında Uygulanacak İdari Para Cezaları\" cetvelinden alınmıştır (1). "
          "Cezayı veren merci İşletme Şefliği, itiraz mercii Sulh Ceza Hâkimliğidir."},
  {"tur": "uyari", "metin": "İdari para cezası işin hafif tarafı. Ormanda izinsiz ateş yakmak ya da "
   "sönmemiş sigara atmak 6831 sayılı Kanun'un 110. maddesi kapsamında ADLİ suçtur ve hapis "
   "cezası öngörür. Taksirle orman yangınına sebep olmanın cezası daha da ağırdır. Kamp ateşi "
   "kurmadan önce bulunduğunuz yerin ocak yeri olarak belirlenip belirlenmediğini teyit edin."},

  {"tur": "baslik", "metin": "Milli parkta ceza bir kat artıyor"},
  {"tur": "metin", "metin": "2873 sayılı Milli Parklar Kanunu'nun 20. maddesi, Orman Kanunu'nda "
   "yasaklanan fiiller milli park sınırları içinde işlenirse cezanın artırılarak uygulanmasını "
   "öngörüyor (3). Milli parkta kamp yalnızca DKMP'nin ücret tarifesi kapsamındaki çadır ve "
   "karavan alanlarında yapılabilir."},

  {"tur": "baslik", "metin": "Peki nerede kamp yapılabilir?"},
  {"tur": "adim", "adimlar": [
    {"baslik": "DKMP korunan alan kamp alanları.", "metin": "Milli park, tabiat parkı ve benzeri "
     "korunan alanlarda idarece belirlenmiş çadır ve karavan alanları. Ücret tarifesi resmîdir; "
     "2026 tarifesini ayrı sayfada topladık."},
    {"baslik": "OGM tescilli mesire yerleri.", "metin": "Mesire Yerleri Yönetmeliği A, B, C ve D "
     "tipi mesire yerlerini tanımlıyor (4). Gecelemeye açık olanlar idarece belirlenir."},
    {"baslik": "Turizm belgeli kamping tesisleri.", "metin": "Kültür ve Turizm Bakanlığı'ndan "
     "belgeli özel kamping işletmeleri."},
    {"baslik": "Özel kamp alanları.", "metin": "Belediye ya da özel işletmelerin ruhsatlı alanları."}]},

  {"tur": "baslik", "metin": "Deniz kıyısında çadır kurmak"},
  {"tur": "metin", "metin": "3621 sayılı Kıyı Kanunu, kıyıyı devletin hüküm ve tasarrufu altında "
   "sayıyor ve herkesin eşit ve serbest yararlanmasına açık tutuyor; ancak çadır kurmaya ya da "
   "gecelemeye dair açık bir hüküm içermiyor (5). Uygulamada kıyıda kamp yasakları belediye "
   "kararlarıyla ve Kabahatler Kanunu üzerinden yürüyor; yani il ve ilçeye göre değişiyor."},
  {"tur": "uyari", "metin": "Kıyıda kamp kuracaksanız, o ilçenin belediye kararlarını ve varsa "
   "valilik yasaklarını önceden kontrol edin. \"Kanunda yasak yazmıyor\" demek, o sahilde "
   "yasak olmadığı anlamına gelmiyor."},

  {"tur": "baslik", "metin": "Valilik yasakları"},
  {"tur": "metin", "metin": "6831 sayılı Kanun'un 74. maddesi, yangın tehlikesi ve kuraklık "
   "gerekçesiyle ormana girişin valiliklerce yasaklanmasına imkân tanıyor (2). Yaz aylarında "
   "çok sayıda ilde bu yasaklar ilan ediliyor ve tescilli mesire yerleri genellikle yasağın "
   "dışında tutuluyor. Yola çıkmadan önce gideceğiniz ilin valilik duyurularına bakın."},

  {"tur": "baslik", "metin": "Özet"},
  {"tur": "madde", "maddeler": [
    "Vahşi kamp yasal değil; ölçüt \"idarece belirlenmiş yer\".",
    "2026'da konak yeri dışında gecelemenin idari para cezası 4.293 TL.",
    "İzinsiz ateş ayrı ve çok daha ağır bir suç; adli yaptırımı var.",
    "Milli parkta ceza artırılarak uygulanıyor.",
    "Kıyıda durum il ve ilçeye göre değişiyor; belediye kararına bakın.",
    "Yaz aylarında valilik giriş yasaklarını kontrol edin."]},
 ],
 "sss": [
  {"s": "Ormanda çadır kurmanın cezası 2026'da ne kadar?",
   "c": "OGM'nin 2026 yılı idari para cezaları cetveline göre, belirlenen konak yerleri dışında "
        "gecelemenin (6831 s.K. m.76/1-a) cezası 4.293 TL'dir. İnternette dolaşan 58.945 TL "
        "rakamı bu resmî cetvelle uyuşmuyor."},
  {"s": "Vahşi kamp Türkiye'de yasal mı?",
   "c": "Hayır. 6831 sayılı Orman Kanunu m.76/a, devlet ormanlarında idarece belirlenen konak "
        "yerleri dışında gecelemeyi yasaklıyor."},
  {"s": "Milli parkta kamp yapabilir miyim?",
   "c": "Yalnızca idarece belirlenmiş çadır ve karavan alanlarında ve resmî ücret tarifesine göre. "
        "Milli park sınırında işlenen ihlallerde ceza artırılarak uygulanıyor."},
  {"s": "Sahilde çadır kurmak yasak mı?",
   "c": "Kıyı Kanunu'nda çadıra dair açık bir hüküm yok. Yasaklar belediye kararlarıyla "
        "uygulandığı için il ve ilçeye göre değişiyor; gitmeden önce yerel duyurulara bakın."},
  {"s": "Kamp ateşi yakabilir miyim?",
   "c": "Yalnızca idarece belirlenen ocak yerlerinde. Bunun dışında ateş yakmak yasak ve "
        "orman yangınına yol açması hâlinde adli yaptırımı var."},
 ],
 "kaynaklar": [
  {"ad": "Orman Genel Müdürlüğü, 2026 Yılında Uygulanacak İdari Para Cezaları",
   "url": "https://www.ogm.gov.tr/tr/e-kutuphane-sitesi/mevzuat-sitesi/Talimatlar/2026_Yilinda_Uygulanacak_Idari_Para_Cezalari.pdf"},
  {"ad": "6831 sayılı Orman Kanunu, güncel metin",
   "url": "https://www.mevzuat.gov.tr/mevzuatmetin/1.3.6831.pdf"},
  {"ad": "2873 sayılı Milli Parklar Kanunu",
   "url": "https://www.mevzuat.gov.tr/mevzuatmetin/1.5.2873.pdf"},
  {"ad": "Orman Genel Müdürlüğü, Mesire Yerleri Yönetmeliği",
   "url": "https://www.ogm.gov.tr/tr/e-kutuphane-sitesi/mevzuat-sitesi/Yonetmelikler/Mesire%20Yerleri%20Y%C3%B6netmeli%C4%9Fi.pdf"},
  {"ad": "3621 sayılı Kıyı Kanunu",
   "url": "https://www.mevzuat.gov.tr/mevzuatmetin/1.3.3621.pdf"},
  {"ad": "Tarım ve Orman Bakanlığı DKMP, Korunan Alanlar Ücret Tarifesi",
   "url": "https://www.tarimorman.gov.tr/DKMP/Menu/39/Korunan-Alanlar-Ucret-Tarifesi"},
 ],
},

{
 "slug": "milli-park-tabiat-parki-farki",
 "baslik": "Milli park, tabiat parkı, koruma alanı: farkı ne, hangisinde kamp var?",
 "ozet": "Korunan alan türleri arasındaki hukuki fark, hangisinin kampa açık olduğu ve "
         "Türkiye'de her türden kaç tane bulunduğu.",
 "cevap": "Türkiye'de DKMP kayıtlarına göre 50 milli park, 276 tabiat parkı ve 32 tabiatı koruma "
          "alanı var. Milli parklar ulusal ölçekte değer taşıyan büyük alanlar; tabiat parkları "
          "dinlenme ve eğlenmeye uygun, halkın kullanımına daha açık alanlar; tabiatı koruma "
          "alanları ise bilim ve eğitim amaçlı, en sıkı korunan ve genellikle kampa kapalı alanlar.",
 "guncelleme": G,
 "bolumler": [
  {"tur": "metin", "metin": "\"Korunan alan\" tek bir şey değil. Hangi statüde olduğunuz, orada "
   "ne yapabileceğinizi doğrudan belirliyor. Aşağıdaki sayılar DKMP'nin 2025 korunan alan "
   "istatistiklerinden alınmıştır (1)."},
  {"tur": "tablo",
   "basliklar": ["Tür", "Sayı", "Amaç", "Kampa bakış"],
   "satirlar": [
    ["Milli Park", "50", "Ulusal/uluslararası ölçekte değer", "Yalnızca belirlenmiş kamp alanlarında"],
    ["Tabiat Parkı", "276", "Dinlenme ve eğlenme", "Kampa en açık tür"],
    ["Tabiatı Koruma Alanı", "32", "Bilim ve eğitim", "Genellikle kapalı"]],
   "not": "Sayılar DKMP 2025 istatistiklerinden; sitedeki alan sayfaları da aynı kaynaktan üretilmiştir."},

  {"tur": "baslik", "metin": "Milli park"},
  {"tur": "metin", "metin": "2873 sayılı Milli Parklar Kanunu'na dayanır (2). Bilimsel ve estetik "
   "bakımdan ulusal ve uluslararası ender bulunan doğa ve kültür kaynaklarını barındıran, koruma, "
   "dinlenme ve turizm alanlarına sahip büyük alanlardır. Uzun devreli gelişme planıyla yönetilir; "
   "kamp yalnızca planda belirlenmiş alanlarda mümkündür."},

  {"tur": "baslik", "metin": "Tabiat parkı"},
  {"tur": "metin", "metin": "Bitki örtüsü ve yaban hayatı özelliğine sahip, manzara bütünlüğü "
   "içinde halkın dinlenme ve eğlenmesine uygun tabiat parçalarıdır. Türkiye'de en kalabalık "
   "korunan alan türü ve kampa en açık olanı. Sitemizdeki resmî kamp izinli alanların büyük "
   "çoğunluğu tabiat parkıdır."},

  {"tur": "baslik", "metin": "Tabiatı koruma alanı"},
  {"tur": "metin", "metin": "Bilim ve eğitim bakımından önem taşıyan, ender ekosistemleri ve "
   "nesli tehlikedeki türleri barındıran alanlardır. Koruma önceliği en yüksek olan türdür; "
   "ziyaret ve kullanım en sıkı sınırlandırılan gruptur."},

  {"tur": "baslik", "metin": "Nasıl anlarım, o alanda kamp var mı?"},
  {"tur": "metin", "metin": "DKMP'nin istatistik tablolarında her alan için bir \"rekreasyon "
   "değeri\" sütunu bulunuyor ve burada o alanda hangi faaliyetlerin öngörüldüğü yazıyor. "
   "Bu sütunda çadırlı kamp, kamp ya da karavan geçen alanları ayrı bir listede topladık."},
  {"tur": "uyari", "metin": "Rekreasyon değerinde kamp geçmesi, o alanın her noktasında çadır "
   "kurabileceğiniz anlamına gelmez. Kamp yalnızca idarece belirlenmiş kamp alanlarında ve "
   "ücret tarifesine göre yapılır. Gitmeden önce alan müdürlüğünü arayın."},
 ],
 "sss": [
  {"s": "Türkiye'de kaç milli park var?",
   "c": "DKMP'nin 2025 korunan alan istatistiklerine göre 50 milli park bulunuyor."},
  {"s": "En çok hangi korunan alan türünde kamp yapılabiliyor?",
   "c": "Tabiat parklarında. Bu tür zaten dinlenme ve eğlenme amacıyla tanımlanmış durumda ve "
        "resmî kayıtta kamp geçen alanların çoğunluğunu oluşturuyor."},
  {"s": "Tabiatı koruma alanında kamp yapılabilir mi?",
   "c": "Genellikle hayır. Bu alanlar bilim ve eğitim amaçlı, en sıkı korunan gruptur."},
 ],
 "kaynaklar": [
  {"ad": "Tarım ve Orman Bakanlığı DKMP, Korunan Alan İstatistikleri",
   "url": "https://www.tarimorman.gov.tr/DKMP/Menu/18/Korunan-Alan-Istatistikleri"},
  {"ad": "2873 sayılı Milli Parklar Kanunu",
   "url": "https://www.mevzuat.gov.tr/mevzuatmetin/1.5.2873.pdf"},
  {"ad": "6831 sayılı Orman Kanunu",
   "url": "https://www.mevzuat.gov.tr/mevzuatmetin/1.3.6831.pdf"},
 ],
},
]

SAYFALAR = [
{
 "url": "/hakkinda/",
 "baslik": "Hakkında",
 "meta": "kampalanlar.com nedir, verisi nereden gelir, nasıl doğrulanır.",
 "html": """
<p><strong>kampalanlar.com</strong>, Türkiye'deki korunan alanların ve kamp yapılabilecek
yerlerin resmî kaynaklardan derlenmiş bağımsız bir dizinidir.</p>

<h2>Neden kurduk?</h2>
<p>Bu alandaki dizinlerin çoğu ham koordinat vermiyor, ücret bilgisini ya hiç yazmıyor ya da
kullanıcı yorumlarından alıyor, ve verinin ne zaman doğrulandığını göstermiyor. Bazı popüler
haritalar yıllar önce kurulmuş ve o günden beri güncellenmemiş durumda. Biz bunun tersini
yapıyoruz.</p>

<h2>İlkelerimiz</h2>
<ul>
<li><strong>Resmî kaynak:</strong> Alan adı, türü, büyüklüğü, ilan tarihi, rakımı ve rekreasyon
değeri Tarım ve Orman Bakanlığı DKMP'nin yayımladığı istatistiklerden alınır.</li>
<li><strong>Ham koordinat:</strong> Her alanın enlem-boylamı sayfada yazılıdır ve kopyalanabilir.</li>
<li><strong>Uydurma yok:</strong> Kaynakta olmayan bilgi boş bırakılır. Ücret, izin ya da olanak
bilgisini tahminle doldurmuyoruz.</li>
<li><strong>Hata varsa söyleriz:</strong> Resmî veride tespit ettiğimiz tutarsızlıkları gizlemiyoruz;
koordinatı şüpheli bulunan kayıtlar sayfasında açıkça belirtiliyor.</li>
<li><strong>Görünür tarih:</strong> Her sayfada verinin doğrulandığı tarih yazar.</li>
</ul>

<h2>Ne değiliz?</h2>
<p>Rezervasyon almıyoruz, hiçbir tesisi ödeme karşılığı listelemiyor ve sıralamada öne
çıkarmıyoruz. Site giderleri sayfalardaki reklamlarla karşılanıyor; ayrıntısı
<a href="/gizlilik/">gizlilik politikasında</a>.</p>

<h2>Düzeltme bildirin</h2>
<p>Kapanmış bir alan, değişmiş bir ücret ya da yanlış bir koordinat gördüyseniz kaynağıyla
birlikte bildirin; kontrol edip düzeltiriz.</p>
""",
},
{
 "url": "/kaynaklar/",
 "baslik": "Veri kaynakları",
 "meta": "Sitedeki verilerin hangi resmî yayınlardan alındığı ve kaynakta tespit edilen hatalar.",
 "html": """
<p>Bu sitedeki bilgilerin tamamı aşağıdaki resmî yayınlardan derlenmiştir. Hiçbir alan
tahminle doldurulmamıştır.</p>

<h2>Birincil kaynaklar</h2>
<ul>
<li><a href="https://www.tarimorman.gov.tr/DKMP/Menu/18/Korunan-Alan-Istatistikleri" rel="noopener" target="_blank">DKMP
Korunan Alan İstatistikleri</a> — alan adı, tür, il, büyüklük, ilan tarihi, koordinat, rakım,
kaynak ve rekreasyon değeri.</li>
<li><a href="https://www.tarimorman.gov.tr/DKMP/Menu/39/Korunan-Alanlar-Ucret-Tarifesi" rel="noopener" target="_blank">DKMP
Korunan Alanlar Ücret Tarifesi</a> — çadır, karavan ve giriş ücretleri.</li>
<li><a href="https://www.ogm.gov.tr/tr/e-kutuphane-sitesi/mevzuat-sitesi/Talimatlar/2026_Yilinda_Uygulanacak_Idari_Para_Cezalari.pdf" rel="noopener" target="_blank">OGM
2026 Yılında Uygulanacak İdari Para Cezaları</a> — orman suçlarının idari para cezaları.</li>
<li><a href="https://www.mevzuat.gov.tr/mevzuatmetin/1.3.6831.pdf" rel="noopener" target="_blank">6831
sayılı Orman Kanunu</a> ve <a href="https://www.mevzuat.gov.tr/mevzuatmetin/1.5.2873.pdf" rel="noopener" target="_blank">2873
sayılı Milli Parklar Kanunu</a>.</li>
</ul>

<h2>Kaynak veride tespit ettiğimiz hatalar</h2>
<p>Resmî dosyaları işlerken tespit ettiğimiz ve düzelttiğimiz sorunları saklamıyoruz:</p>
<ul>
<li><strong>Ters koordinat sütunları.</strong> Milli park listesinde enlem ve boylam sütunları
yer değiştirmiş durumdaydı. Düzeltilmeseydi 50 milli parkın tamamı haritada yanlış konumda
görünecekti. Her kayıt Türkiye sınırlarına karşı denetlenerek düzeltildi.</li>
<li><strong>Ondalık ayracı eksik koordinatlar.</strong> On iki kayıtta koordinat
<code>41126699</code> gibi tam sayı olarak girilmişti; <code>41.126699</code> olarak onarıldı.</li>
<li><strong>Satır kayması.</strong> Milli park listesinde bir alanın adı bir satır aşağı kaymış
ve sonraki il başlığıyla çakışmıştı; onarılmasaydı kayıt kaybolacaktı.</li>
<li><strong>Tek tek ters girilmiş kayıtlar.</strong> Aynı ildeki diğer alanların ortancasından
çok uzağa düşen noktalar denetlenir; yer değiştirme sonucu ilin içine düşüyorsa düzeltilir,
düşmüyorsa "koordinat doğrulanamadı" olarak işaretlenir ve haritada gösterilmez.</li>
</ul>

<h2>Açık veri</h2>
<p>Derlenmiş verinin tamamını <a href="/veri/korunan-alanlar.json">JSON olarak</a>
indirebilirsiniz. Kullanırken kaynak olarak bu sayfaya bağlantı vermenizi rica ederiz.</p>
""",
},
{
 "url": "/gizlilik/",
 "baslik": "Gizlilik ve çerez politikası",
 "meta": "Hangi verileri işliyoruz, hangi çerezleri kullanıyoruz ve reklamlar nasıl çalışıyor.",
 "html": """
<p>Bu site statik bir dizindir; üyelik almaz, form doldurtmaz ve rezervasyon yapmaz.</p>

<h2>Bizim topladığımız veri</h2>
<p>Sunucumuzda kişisel veri saklanmaz. Haritadaki "bana yakın" özelliği konumunuzu yalnızca
tarayıcınızda kullanır; konum bilginiz bize gönderilmez.</p>

<h2>Ölçümleme</h2>
<p>Ziyaretçi sayısını anonim ölçmek için istatistik araçları kullanılabilir. Bu veriler kişiyi
tanımlamaz; işleme 6698 sayılı KVKK'ya uygun yürütülür.</p>

<h2>Reklamlar (Google AdSense)</h2>
<p>Site giderlerini karşılamak için sayfalarda <strong>Google AdSense</strong> reklamları
gösterilir. Bu kapsamda:</p>
<ul>
<li>Google, üçüncü taraf sağlayıcı olarak çerezleri kullanarak bu sitede ve internetteki diğer
sitelerde yaptığınız ziyaretlere dayalı reklam gösterebilir.</li>
<li>Google'ın <strong>reklam çerezi</strong> kullanımı, kullanıcılara bu siteye ve diğer sitelere
yaptıkları ziyaretlere göre reklam sunulmasına olanak tanır.</li>
<li>Kişiselleştirilmiş reklamları
<a href="https://www.google.com/settings/ads" rel="noopener nofollow" target="_blank">Google Reklam
Ayarları</a>'ndan kapatabilirsiniz.</li>
<li>Üçüncü taraf satıcı çerezlerini
<a href="https://www.aboutads.info/choices/" rel="noopener nofollow" target="_blank">aboutads.info</a>
üzerinden yönetebilirsiniz.</li>
<li>Avrupa Ekonomik Alanı ve Birleşik Krallık ziyaretçilerine Google'ın kendi onay mesajı gösterilir.</li>
<li><strong>Hiçbir alan ödeme karşılığı listelenmez ya da sıralamada öne çıkarılmaz;</strong>
reklamlar içerikten bağımsızdır.</li>
</ul>

<h2>Üçüncü taraf içerikler</h2>
<ul>
<li>Harita karoları <a href="https://www.openstreetmap.org/copyright" rel="noopener nofollow" target="_blank">OpenStreetMap</a>'ten
yüklenir; karo sunucusu IP adresinizi görebilir.</li>
<li>"Google Haritalar'da aç" bağlantıları Google'a gider.</li>
</ul>

<h2>Çerezleri reddetme</h2>
<p>Tarayıcı ayarlarınızdan çerezleri her zaman silebilir veya engelleyebilirsiniz; sitenin
dizin işlevi bundan etkilenmez.</p>

<h2>İletişim</h2>
<p>Gizlilikle ilgili sorularınız için <a href="/hakkinda/">hakkında</a> sayfasındaki
yönergeyi kullanabilirsiniz.</p>
""",
},
]


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    (KOK / "data" / "rehberler.json").write_text(
        json.dumps(REHBERLER, ensure_ascii=False, indent=1), encoding="utf-8")
    (KOK / "data" / "sayfalar.json").write_text(
        json.dumps(SAYFALAR, ensure_ascii=False, indent=1), encoding="utf-8")
    kelime = sum(len(b.get("metin", "").split()) for r in REHBERLER for b in r["bolumler"])
    print(f"{len(REHBERLER)} rehber (~{kelime} kelime), {len(SAYFALAR)} düz sayfa yazıldı")


if __name__ == "__main__":
    main()
