# Unutkan Uygulaması - Gelecekte Eklenecek Özellikler ve Notlar

Bu belgede, veri mahremiyetini artırmak amacıyla geliştirilen "unutkan" uygulaması için planlanan özellikler yer almaktadır.

## Planlanan Özellikler

### 1. Kapsamlı Metadata Temizleyici (Metadata Stripper)
* **Görsel Temizliği:** JPEG, PNG, WebP ve diğer formatlardaki resimlerin EXIF (GPS, Kamera, Tarih) verilerini silme.
* **Belge Temizliği:** PDF, DOCX, XLSX, PPTX dosyalarından yazar, düzenleme geçmişi ve şirket bilgisi gibi meta verileri arındırma.
* **Medya Temizliği:** MP3, MP4, WAV gibi ses ve video dosyalarından etiketleri ve kişisel bilgileri kaldırma.

### 2. Güvenli Dosya Silme (Secure Shredder)
* Dosyaları diskten silerken kurtarılmasını engellemek amacıyla üzerine rastgele veri yazarak (DoD 5220.22-M veya Gutmann standartları) imha etme.

### 3. Otomatik Pano (Clipboard) Temizleyici
* Kopyalanan hassas verilerin (şifreler, kimlik numaraları, cüzdan adresleri) 30 veya 60 saniye sonra panodan otomatik olarak silinmesi.

### 4. Metin Maskeleyici ve Takip Kodu Temizleyici (Text Sanitizer)
* Paylaşılan linklerdeki takip parametrelerini (örn: `utm_*`, `fbclid`) kaldırma.
* Metin içerisindeki e-posta, telefon numarası ve API anahtarı gibi hassas verileri otomatik maskeleme.

### 5. RAM Tabanlı Geçici Kasa (Ephemeral Vault)
* RAM üzerinde sanal bir disk alanı (tmpfs) oluşturarak dosyaları burada geçici olarak tutma. Bilgisayar kapandığında veya uygulama sonlandığında bu veriler tamamen yok olur.

## Kurulum ve Dağıtım Hedefi
* Uygulamanın tek bir terminal komutuyla (`curl -sSL ... | bash`) kurulabilen, Linux ekosistemine uygun bir araç olması planlanmaktadır.
