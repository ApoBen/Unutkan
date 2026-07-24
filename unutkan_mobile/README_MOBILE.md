# 📱 Unutkan Mobile — Flutter/Android Kurulum Kılavuzu

Bu dizin, **Unutkan** uygulamasının Android platformunda çalışabilmesi için sıfırdan yazılmış olan **Flutter (Dart)** kod tabanını içerir.

---

## 🛠️ Derleme ve Çalıştırma Adımları

Uygulamayı kendi bilgisayarınızda derlemek veya test etmek için aşağıdaki adımları sırasıyla uygulayabilirsiniz:

### 1. Ön Gereksinimler
- Bilgisayarınızda **Flutter SDK** (v3.0.0+) kurulu olmalıdır.
  - *Kurulu değilse [flutter.dev](https://docs.flutter.dev/get-started/install) üzerinden indirebilirsiniz.*
- Android derlemesi yapabilmek için **Android Studio** ve **Java Development Kit (JDK)** kurulu olmalıdır.

### 2. Proje Dizinine Geçiş
Terminalden bu klasöre geçin:
```bash
cd unutkan_mobile
```

### 3. Bağımlılıkların Yüklenmesi
Gerekli kütüphaneleri (`archive`, `file_picker`, `permission_handler` vb.) indirmek için şu komutu çalıştırın:
```bash
flutter pub get
```

### 4. Uygulamayı Cihazda/Simülatörde Çalıştırma
Android telefonunuzu USB hata ayıklama (USB Debugging) açık şekilde bilgisayara bağlayın veya bir Android Emülatörü açın, ardından çalıştırın:
```bash
flutter run
```

### 5. APK Derleme (Build APK)
Uygulamanın yüklenebilir kararlı sürüm APK dosyasını üretmek için şu komutu çalıştırın:
```bash
flutter build apk --release
```
*Derleme bittiğinde APK dosyanız `build/app/outputs/flutter-apk/app-release.apk` dizininde oluşturulacaktır. Bu dosyayı telefonunuza gönderip kurabilirsiniz.*

---

## 📂 Kod Yapısı Detayları

- **`lib/main.dart`:** Uygulama başlangıcı ve premium koyu tema yapılandırması.
- **`lib/core/privacy_core.dart`:** Python `core.py` çekirdeğinin Dart diline uyarlanmış versiyonu.
  - Metin maskeleme, byte düzeyinde JPEG EXIF silme, ZIP tabanlı Microsoft Office ve ODF metadatalarını temizleme, dosya ezerek güvenli silme (shredder) algoritmalarını barındırır.
- **`lib/screens/`:** Uygulama arayüzleri.
  - `dashboard_screen.dart` (Ana Sayfa)
  - `cleaner_screen.dart` (Metadata Temizleyici)
  - `shredder_screen.dart` (Güvenli Silici)
  - `sanitizer_screen.dart` (Metin Arındırıcı)
  - `vault_screen.dart` (RAM Bellek Kasası)
