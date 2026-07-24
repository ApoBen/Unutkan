import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../core/privacy_core.dart';

class SanitizerScreen extends StatefulWidget {
  const SanitizerScreen({super.key});

  @override
  State<SanitizerScreen> createState() => _SanitizerScreenState();
}

class _SanitizerScreenState extends State<SanitizerScreen> {
  final TextEditingController _inputController = TextEditingController();
  final TextEditingController _outputController = TextEditingController();

  bool _cleanUrls = true;
  bool _maskEmails = true;
  bool _maskPhones = true;
  bool _maskSecrets = true;
  String _copyButtonText = 'Panoya Kopyala';

  void _clearText() {
    setState(() {
      _inputController.clear();
      _outputController.clear();
    });
  }

  void _copyToClipboard() {
    final text = _outputController.text;
    if (text.isNotEmpty) {
      Clipboard.setData(ClipboardData(text: text));
      setState(() {
        _copyButtonText = '✓ Kopyalandı!';
      });
      Future.delayed(const Duration(seconds: 2), () {
        if (mounted) {
          setState(() {
            _copyButtonText = 'Panoya Kopyala';
          });
        }
      });
    }
  }

  void _sanitize() {
    final text = _inputController.text;
    if (text.isEmpty) return;

    final settings = {
      'urls': _cleanUrls,
      'emails': _maskEmails,
      'phones': _maskPhones,
      'secrets': _maskSecrets,
    };

    final sanitized = PrivacyCore.sanitizeText(text, settings);
    setState(() {
      _outputController.text = sanitized;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1E1E1E),
      appBar: AppBar(
        title: const Text('Metin Arındırıcı', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF242424),
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text(
                'Arındırılacak Ham Metin:',
                style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _inputController,
                maxLines: 5,
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: InputDecoration(
                  hintText: 'Arındırılacak metni, linkleri veya log kayıtlarını buraya yapıştırın...',
                  hintStyle: const TextStyle(color: Colors.grey, fontSize: 12),
                  fillColor: const Color(0xFF303030),
                  filled: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                ),
              ),
              const SizedBox(height: 12),
              // Options card grid
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: const Color(0xFF303030),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  children: [
                    CheckboxListTile(
                      title: const Text('Bağlantı Takip Parametrelerini Temizle', style: TextStyle(color: Colors.white, fontSize: 11)),
                      subtitle: const Text('utm_*, fbclid vb.', style: TextStyle(color: Colors.grey, fontSize: 9)),
                      value: _cleanUrls,
                      activeColor: const Color(0xFF1CA8A3),
                      onChanged: (val) => setState(() => _cleanUrls = val ?? true),
                      controlAffinity: ListTileControlAffinity.leading,
                    ),
                    CheckboxListTile(
                      title: const Text('E-posta Adreslerini Maskele', style: TextStyle(color: Colors.white, fontSize: 11)),
                      value: _maskEmails,
                      activeColor: const Color(0xFF1CA8A3),
                      onChanged: (val) => setState(() => _maskEmails = val ?? true),
                      controlAffinity: ListTileControlAffinity.leading,
                    ),
                    CheckboxListTile(
                      title: const Text('Telefon Numaralarını Maskele', style: TextStyle(color: Colors.white, fontSize: 11)),
                      value: _maskPhones,
                      activeColor: const Color(0xFF1CA8A3),
                      onChanged: (val) => setState(() => _maskPhones = val ?? true),
                      controlAffinity: ListTileControlAffinity.leading,
                    ),
                    CheckboxListTile(
                      title: const Text('API Anahtarları ve Parolaları Maskele', style: TextStyle(color: Colors.white, fontSize: 11)),
                      value: _maskSecrets,
                      activeColor: const Color(0xFF1CA8A3),
                      onChanged: (val) => setState(() => _maskSecrets = val ?? true),
                      controlAffinity: ListTileControlAffinity.leading,
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 12),
              const Text(
                'Arındırılmış Sonuç:',
                style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _outputController,
                readOnly: true,
                maxLines: 5,
                style: const TextStyle(color: Colors.white, fontSize: 13),
                decoration: InputDecoration(
                  hintText: 'Arındırılan metin burada görüntülenecektir...',
                  hintStyle: const TextStyle(color: Colors.grey, fontSize: 12),
                  fillColor: const Color(0xFF303030),
                  filled: true,
                  border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                ),
              ),
              const SizedBox(height: 16),
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _clearText,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: Colors.white24),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: const Text('Temizle'),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _copyToClipboard,
                      style: OutlinedButton.styleFrom(
                        foregroundColor: Colors.white,
                        side: const BorderSide(color: Colors.white24),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: Text(_copyButtonText),
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: ElevatedButton(
                      onPressed: _sanitize,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFF1CA8A3),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                      child: const Text('Metni Arındır'),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
