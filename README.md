# 🔒 Unutkan - Güvenli Dijital Hijyen & Metadata Temizleyici

**Unutkan**, kişisel veri güvenliğinizi ve gizliliğinizi korumak için tasarlanmış, **%100 çevrimdışı (offline) ve yerel (native) çalışan** bir Linux masaüstü dijital hijyen uygulamasıdır. 

Uygulama, dosyalarınızın veya paylaştığınız metinlerin içinde farkında olmadan dışarıya sızan konum (GPS), cihaz bilgileri, kişisel veri (PII) ve takip kodlarını tamamen yerel olarak temizler. Hiçbir veriyi diske kaydetmeden veya internete göndermeden RAM üzerinde işleyebilir.

---

## 🚀 Tek Komutla Kurulum

Terminalden aşağıdaki komutu çalıştırarak en güncel kararlı sürümü otomatik olarak sisteminize kurabilirsiniz:

```bash
curl -sSL https://raw.githubusercontent.com/ApoBen/Unutkan/main/install.sh | bash
```

*Bu komut uygulamayı yerel dizininize (`~/.local/bin/unutkan` ve `~/.local/bin/unutkantui`) kuracak ve masaüstünüzde (`~/.local/share/applications`) bir kısayol oluşturacaktır.*

### ❌ Uygulamayı Kaldırma (Uninstall)

Uygulamayı sisteminizden tamamen temizlemek için şu komutu çalıştırabilirsiniz:

```bash
unutkan-uninstall
```

Veya depodan doğrudan tek komutla kaldırmak için:

```bash
curl -sSL https://raw.githubusercontent.com/ApoBen/Unutkan/main/uninstall.sh | bash
```

---

## 🛠️ Temel Özellikler & Güvenlik Mimarisi

### 1. Metadata Temizleyici (Metadata Cleaner)
Paylaştığınız dosyaların içine gömülü olan konum (GPS), kamera/cihaz bilgileri, yazar adı gibi gizli metadataları temizler.
* **Desteklenen Formatlar:** PNG, JPG, JPEG, WEBP, PDF, DOCX, XLSX, PPTX, ODT, ODS, ODP, MP3, FLAC, OGG, M4A.
* **Detay İnceleme:** Temizleme işlemi öncesinde dosyadaki mevcut metadataları listeleyip önizleme yapmanızı sağlar.
* **Güvenlik Güçlendirmesi:** Dosya okuma ve yazma işlemlerinde sembolik link (symlink) saldırılarına karşı tam koruma içerir.

### 2. Güvenli Silici (Secure Shredder)
Dosyaları diske rastgele veriler yazarak geri döndürülemeyecek şekilde kalıcı olarak imha eder.
* **Seçilebilir Yöntemler:** 
  * Hızlı Sıfırlama (1 Geçiş - Sıfır Yazma)
  * Güvenli (3 Geçiş - Rastgele + Sıfır)
  * Maksimum Güvenlik (7 Geçiş - Çoklu Desen)
* **İz Obfuskasyonu:** Dosya silinmeden önce dosya adı UUID formatında rastgele karakterlerle değiştirilir, böylece dosya sistemi günlüklerinde (journaling filesystem) orijinal dosya adı gizlenmiş olur.
* **Dosya Sistemi Entegrasyonu:** Her geçişten sonra ve truncate işleminde `fsync` çağrılarak verilerin fiziksel olarak diske yazılması garanti edilir.

### 3. Metin Arındırıcı (Text Sanitizer)
Paylaşacağınız metinlerde veya bağlantılarda bulunan hassas verileri filtreler.
* **Takip Kodları:** Bağlantılardaki (URL) `utm_source`, `fbclid`, `gclid`, `ref`, `source` gibi tüm reklam ve analiz takip parametrelerini kaldırır.
* **PII Maskeleme:** E-posta adreslerini, telefon numaralarını ve API anahtarlarını maskeleyerek gizler.

### 4. Geçici Bellek Kasası (RAM Vault)
Şifre, not veya hassas dosyaları disk üzerinde hiçbir iz bırakmadan, sadece RAM üzerinde şifrelenmiş geçici bellek tamponlarında tutar.
* **Zaman Ayarlı İmha:** Belirlenen süre sonunda veya manuel olarak "Belleği Şimdi Kazı" butonuna basıldığında veriler bellekten tamamen sıfırlanarak kazınır.
* **Hafıza Güvenliği:** Python'daki değişmez (immutable) veri yapılarının RAM'de kalmasını önlemek için veriler mutable `bytearray` olarak tutulur, işlem bittiğinde `del` ve `gc.collect()` ile temizlenir.
* **Wipe (Kazıma) Kontrolü:** Kazıma işlemlerinde oluşabilecek hatalar sessizce geçilmez, kullanıcıya anında rapor edilir.
* **Boyut Sınırlandırması:** Kullanıcı tarafından yapılandırılabilir dosya boyutu limiti (50MB, 100MB, 250MB, 500MB, 1GB veya Limitsiz) ile bellek aşımı (OOM) saldırılarına karşı koruma sağlar.

---

## 📦 Manuel Kurulum & Geliştirme

1. **Depoyu klonlayın:**
   ```bash
   git clone https://github.com/ApoBen/Unutkan.git
   cd Unutkan
   ```

2. **Bağımlılıkları yükleyin:**
   ```bash
   pip install PySide6 pypdf pillow mutagen pyinstaller
   ```

3. **Derleme (PyInstaller):**
   Uygulamayı kaynak kodundan tek bir binary dosyasına derlemek için:
   ```bash
   pyinstaller --onefile --noconsole --name unutkan app.py
   ```

4. **Yerel Kurulum:**
   ```bash
   chmod +x install.sh
   ./install.sh
   ```

---

## 🔒 Güvenlik Notu

Unutkan, tamamen **çevrimdışı** çalışmak üzere tasarlanmıştır. Uygulama kaynak kodunda hiçbir ağ kütüphanesi kullanılmamıştır ve dış dünya ile hiçbir şekilde veri alışverişi yapmaz. Güvenle kullanabilirsiniz.
