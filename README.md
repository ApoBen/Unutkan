# Unutkan - Güvenli Dijital Hijyen Araç Kutusu

**Unutkan**, kişisel veri güvenliğinizi ve gizliliğinizi en üst düzeyde korumak için geliştirilmiş, **%100 yerel (native) ve tamamen çevrimdışı (offline)** çalışan bir Linux masaüstü uygulamasıdır. 

Uygulama, sisteminizde hiçbir iz (dosya, internet geçmişi veya log) bırakmadan dijital temizlik yapmanızı sağlayan 4 temel güvenlik aracı barındırır.

---

## 🛠️ Ana Özellikler ve Araçlar

### 1. Metadata Temizleyici (Metadata Cleaner)
Paylaşacağınız dosyaların içinde gizlenen ve kimliğinizi ele verebilecek hassas verileri temizler.
* **Görüntüler (JPG, JPEG, PNG, WEBP):** Kamera modeli, çekim konumu (GPS), EXIF etiketleri ve yazılım bilgilerini yok eder.
* **PDF Belgeleri:** Yazar, oluşturucu araç, başlık, oluşturulma ve son değiştirilme tarihlerini temizler.
* **Office Belgeleri (DOCX, XLSX, PPTX) & OpenDocument (ODT, ODS, ODP):** Belge yazarı, revizyon numarası, düzenleme süresi gibi gizli xml özniteliklerini sıfırlar.
* **Ses Dosyaları (MP3, FLAC, OGG, M4A):** Şarkı/sanatçı etiketlerini (ID3) temizler.
* **Detay Analizi:** Temizleme işlemi öncesinde **"Detay"** butonuna basarak dosya içindeki tüm metadataları kırmızı liste halinde inceleyebilirsiniz.

### 2. Güvenli Silici (Secure Shredder)
Dosyalarınızı diskten geri döndürülemeyecek şekilde kalıcı olarak imha eder.
* **Üzerine Yazma Standartları:** Hızlı (1 Geçiş - Zero-fill), Güvenli (3 Geçiş - DoD 5220.22-M) ve Maksimum Güvenlik (7 Geçiş - Gutmann) algoritmalarını destekler.
* **Dosya Sistemi Temizliği:** Disk önbelleklerini bypass etmek için `os.fsync()` çağırır. Dosya içeriğini sıfırlayıp dizin kayıtlarından silmeden önce dosya adını rastgele UUID'ler ile değiştirerek sistem izlerini tamamen yok eder.

### 3. Metin Arındırıcı (Text Sanitizer)
Paylaşacağınız metin veya log kayıtlarındaki hassas bilgileri filtreler.
* **Takip Kodlarını Temizleme:** Bağlantılardaki (URL) `utm_*`, `fbclid`, `gclid`, `ref` gibi takip parametrelerini temizler.
* **Hassas Veri Maskeleme:** E-postaları (`a***b@domain.com`), telefon numaralarını (`0532 *** **12`) ve API anahtarlarını (AWS, Google, Bearer Tokens) otomatik tespit edip maskeler.

### 4. Geçici Bellek Kasası (RAM-Based Temporary Vault)
Şifre, not veya hassas dosyalarınızı **asla diske yazmadan** sadece RAM üzerinde geçici olarak tutar.
* **RAM Tabanlı Saklama:** Veriler RAM'de değiştirilebilir `bytearray` hücrelerinde tutulur.
* **Sayaç ve Wipe Koruması:** Belirlediğiniz süre (30sn, 2dk, 5dk, 10dk) dolduğunda veya "Belleği Şimdi Kazı" butonuna bastığınızda, RAM hücrelerindeki tüm veriler C seviyesinde sıfırlarla (`\x00`) doldurularak fiziksel olarak ezilir ve bellek dökümü (memory dump) saldırılarına karşı korunur.

---

## 🔒 Güvenlik & Mimari Yaklaşım

* **%100 Çevrimdışı (Offline):** Uygulama içinde hiçbir internet/ağ kütüphanesi kullanılmamıştır. Dış dünyaya tamamen kapalıdır.
* **Web Sarmalayıcısı Değildir:** Electron veya WebView kullanılmamıştır. Tamamen yerel (native) PySide6 (Qt6) kütüphaneleriyle çizilir ve düşük RAM tüketimiyle çok hızlı çalışır.
* **Evrensel Uyumluluk:** Emojilerin kare/bozuk göründüğü sistemler için emoji fontu bağımlılığı kaldırılmış, yerine harf tabanlı şık rozetler ve ASCII simgeler kullanılmıştır.

---

## 🚀 Tek Komutla Kurulum (Linux)

Terminalinizi açıp aşağıdaki komutu çalıştırmanız yeterlidir:

```bash
curl -sSL https://raw.githubusercontent.com/ApoBen/Unutkan/main/install.sh | bash
```

Bu komut; en güncel derlenmiş binary dosyasını GitHub üzerinden indirecek, yerel kullanıcı dizininize (`~/.local/bin/unutkan`) kuracak ve masaüstü menünüzde **Unutkan** kısayolunu oluşturacaktır.

---

## 🛠️ Manuel Kurulum ve Derleme

Uygulamayı kaynağından derlemek veya manuel kurmak isterseniz:

### 1. Depoyu Klonlayın:
```bash
git clone https://github.com/ApoBen/Unutkan.git
cd Unutkan
```

### 2. Gerekli Python Kütüphanelerini Yükleyin:
```bash
pip install PySide6 pypdf pillow mutagen pyinstaller
```

### 3. Çalıştırın veya Derleyin:
* **Çalıştırmak için:**
  ```bash
  python3 app.py
  ```
* **Derlemek için (Tek Binary):**
  ```bash
  pyinstaller --onefile --noconsole --name unutkan app.py
  ```

### 4. Kurulum Scriptini Çalıştırın:
Derleme işleminden sonra uygulamayı sisteme entegre etmek için:
```bash
chmod +x install.sh
./install.sh
```

---

## 📝 Lisans
Bu proje açık kaynaklı olup, kişisel gizliliği koruma amacıyla özgürce kullanılabilir ve dağıtılabilir.
