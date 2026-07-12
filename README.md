# Unutkan

Kişisel veri güvenliğinizi ve gizliliğinizi korumak için tasarlanmış, tamamen çevrimdışı (offline) çalışan bir Linux masaüstü dijital hijyen uygulamasıdır.

---

## Özellikler

### 1. Metadata Temizleyici
Dosyaların (resim, ses, belge, PDF, ODF) içine gömülü olan konum (GPS), kamera/cihaz bilgileri, yazar adı gibi gizli metadataları temizler.
* **Desteklenen Formatlar:** PNG, JPG, JPEG, WEBP, PDF, DOCX, XLSX, PPTX, ODT, ODS, ODP, MP3, FLAC, OGG, M4A.
* **Detay İnceleme:** Temizleme öncesi dosyadaki metadataları listeler.

### 2. Güvenli Silici
Dosyaları diske rastgele veriler yazarak geri döndürülemeyecek şekilde kalıcı olarak imha eder.
* **Yöntemler:** Hızlı Sıfırlama (1 Geçiş), Güvenli (3 Geçiş - DoD 5220.22-M), Maksimum Güvenlik (7 Geçiş - Gutmann).
* **Güvenli Dizin Temizliği:** Dosyayı silmeden önce adını rastgele karakterlerle değiştirerek disk izlerini tamamen yok eder.

### 3. Metin Arındırıcı
Paylaşacağınız metinlerdeki hassas verileri filtreler.
* **Takip Kodları:** Bağlantılardaki (URL) `utm_*`, `fbclid`, `ref` gibi takip parametrelerini kaldırır.
* **Maskeleme:** E-posta adreslerini, telefon numaralarını ve API anahtarlarını maskeleyerek gizler.

### 4. Geçici Bellek Kasası
Şifre, not veya hassas dosyaları diskte iz bırakmadan sadece RAM bellek üzerinde geçici olarak tutar.
* **RAM Güvenliği:** Veriler fiziksel bellek dökümü (memory dump) saldırılarına karşı değiştirilebilir tamponlarda tutulur.
* **İmha Zamanlayıcısı:** Belirlenen süre sonunda veya manuel olarak "Belleği Şimdi Kazı" butonuna basıldığında tüm veriler bellekten sıfır yazılarak fiziksel olarak ezilir ve yok edilir.

---

## Kurulum

### Tek Komutla Hızlı Kurulum

Terminalden aşağıdaki komutu çalıştırarak en güncel sürümü doğrudan kurabilirsiniz:

```bash
curl -sSL https://raw.githubusercontent.com/ApoBen/Unutkan/main/install.sh | bash
```

Bu komut uygulamayı yerel dizininize (`~/.local/bin/unutkan`) kuracak ve masaüstünüzde bir kısayol oluşturacaktır.

### Manuel Kurulum

1. Depoyu klonlayın:
```bash
git clone https://github.com/ApoBen/Unutkan.git
cd Unutkan
```

2. Bağımlılıkları yükleyin:
```bash
pip install PySide6 pypdf pillow mutagen pyinstaller
```

3. Kurulum betiğini çalıştırın:
```bash
chmod +x install.sh
./install.sh
```

---

## Derleme

Uygulamayı kaynak kodundan yeniden derlemek için:

```bash
pyinstaller --onefile --noconsole --name unutkan app.py
```
Derlenen dosya `dist/unutkan` dizininde oluşturulacaktır.
