import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import '../core/privacy_core.dart';

class ShredderScreen extends StatefulWidget {
  const ShredderScreen({super.key});

  @override
  State<ShredderScreen> createState() => _ShredderScreenState();
}

class _ShredderScreenState extends State<ShredderScreen> {
  final List<Map<String, dynamic>> _selectedFiles = [];
  final List<String> _logs = [];
  int _methodIndex = 1; // Default 3-pass safe
  bool _isProcessing = false;

  void _log(String message, {bool isError = false}) {
    setState(() {
      _logs.add(message);
    });
  }

  Future<void> _pickFiles() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        allowMultiple: true,
        type: FileType.any,
      );

      if (result != null && result.files.isNotEmpty) {
        int added = 0;
        for (final file in result.files) {
          if (file.path != null) {
            final path = file.path!;
            final name = file.name;

            if (_selectedFiles.any((f) => f['path'] == path)) continue;

            final validation = PrivacyCore.validateFilePath(path);
            if (!validation['valid']) {
              _log('Reddedildi ($name): ${validation['error']}', isError: true);
              continue;
            }

            setState(() {
              _selectedFiles.add({
                'path': path,
                'name': name,
                'status': 'Hazır',
                'error': '',
              });
            });
            added++;
          }
        }
        if (added > 0) {
          _log('$added adet dosya imha sırasına eklendi.');
        }
      }
    } catch (e) {
      _log('Dosya seçme hatası: $e', isError: true);
    }
  }

  void _clearList() {
    setState(() {
      _selectedFiles.clear();
      _logs.clear();
    });
    _log('Silme sırası temizlendi.');
  }

  Future<void> _shredFiles() async {
    if (_selectedFiles.isEmpty) {
      _log('Silinecek dosya seçilmedi.', isError: true);
      return;
    }

    // Double confirmation
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF303030),
          title: const Text('⚠️ Kalıcı İmha Onayı', style: TextStyle(color: Colors.red, fontWeight: FontWeight.bold)),
          content: const Text(
            'Seçilen tüm dosyalar diski kaplayan blokların üzerine tekrar tekrar rastgele veriler yazılarak kurtarılamayacak şekilde silinecektir. Emin misiniz?',
            style: TextStyle(color: Colors.white, fontSize: 13),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context, false),
              child: const Text('İptal', style: TextStyle(color: Colors.grey)),
            ),
            TextButton(
              onPressed: () => Navigator.pop(context, true),
              child: const Text('Evet, İmha Et', style: TextStyle(color: Colors.red)),
            ),
          ],
        );
      },
    );

    if (confirm != true) return;

    setState(() {
      _isProcessing = true;
    });

    _log('Güvenli imha işlemi başlatılıyor...');

    for (int i = 0; i < _selectedFiles.length; i++) {
      final fileInfo = _selectedFiles[i];
      if (fileInfo['status'] == 'Silindi') continue;

      setState(() {
        fileInfo['status'] = 'Siliniyor...';
      });

      _log('İmha ediliyor: ${fileInfo['name']}');

      final result = await PrivacyCore.shredFile(
        fileInfo['path'],
        _methodIndex,
        (pass, total) {
          _log('  [${fileInfo['name']}] Geçiş $pass/$total yazılıyor...');
        },
      );

      setState(() {
        if (result['success']) {
          fileInfo['status'] = 'Silindi';
          _log('İmha Edildi (Geri döndürülemez): ${fileInfo['name']}');
        } else {
          fileInfo['status'] = 'Hata';
          fileInfo['error'] = result['error'];
          _log('Hata: ${fileInfo['name']} (${result['error']})', isError: true);
        }
      });
    }

    _log('Tüm imha işlemleri tamamlandı.');
    setState(() {
      _isProcessing = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1E1E1E),
      appBar: AppBar(
        title: const Text('Güvenli Silici', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF242424),
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Drop zone area
            GestureDetector(
              onTap: _isProcessing ? null : _pickFiles,
              child: Container(
                height: 120,
                width: double.infinity,
                decoration: BoxDecoration(
                  color: const Color(0xFF303030),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: _isProcessing ? Colors.white.withOpacity(0.05) : const Color(0xFFF66151),
                    width: 2,
                  ),
                ),
                child: const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.delete_forever, size: 36, color: Color(0xFFF66151)),
                    SizedBox(height: 8),
                    Text(
                      'İmha Edilecek Dosyaları Seçin',
                      style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Her türlü dosya formatı kabul edilir',
                      style: TextStyle(color: Color(0xFFB3B3B3), fontSize: 10),
                    )
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            // Method Dropdown Panel
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: const Color(0xFF303030),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Row(
                children: [
                  const Text(
                    'Silme Yöntemi:',
                    style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(width: 16),
                  Expanded(
                    child: DropdownButton<int>(
                      value: _methodIndex,
                      dropdownColor: const Color(0xFF303030),
                      style: const TextStyle(color: Colors.white, fontSize: 12),
                      underline: const SizedBox(),
                      isExpanded: true,
                      onChanged: _isProcessing
                          ? null
                          : (val) {
                              if (val != null) {
                                setState(() {
                                  _methodIndex = val;
                                });
                              }
                            },
                      items: const [
                        DropdownMenuItem(
                          value: 0,
                          child: Text('Hızlı Sıfırla (1 Geçiş)'),
                        ),
                        DropdownMenuItem(
                          value: 1,
                          child: Text('Güvenli (3 Geçiş)'),
                        ),
                        DropdownMenuItem(
                          value: 2,
                          child: Text('Maksimum Güvenlik (7 Geçiş)'),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),
            // Red Warning Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: const Color(0xFFF66151).withOpacity(0.08),
                border: Border.all(color: const Color(0xFFF66151).withOpacity(0.15)),
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Text(
                'UYARI: Güvenli silinen dosyalar kurtarılamaz ve diskten kalıcı olarak imha edilir.',
                style: TextStyle(color: Color(0xFFF66151), fontSize: 10.5, fontWeight: FontWeight.bold),
              ),
            ),
            const SizedBox(height: 12),
            // Files List
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: const Color(0xFF303030),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: _selectedFiles.isEmpty
                    ? const Center(child: Text('İmha Listesi Boş', style: TextStyle(color: Color(0xFFB3B3B3))))
                    : ListView.builder(
                        padding: const EdgeInsets.all(8),
                        itemCount: _selectedFiles.length,
                        itemBuilder: (context, index) {
                          final f = _selectedFiles[index];
                          return Card(
                            color: const Color(0xFF242424),
                            margin: const EdgeInsets.only(bottom: 8),
                            child: ListTile(
                              title: Text(f['name'], style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold)),
                              subtitle: Text(f['path'], style: const TextStyle(color: Colors.grey, fontSize: 10)),
                              trailing: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                decoration: BoxDecoration(
                                  color: f['status'] == 'Silindi'
                                      ? Colors.green.withOpacity(0.2)
                                      : f['status'] == 'Hata'
                                          ? Colors.red.withOpacity(0.2)
                                          : Colors.blue.withOpacity(0.2),
                                  borderRadius: BorderRadius.circular(8),
                                ),
                                child: Text(
                                  f['status'],
                                  style: TextStyle(
                                    color: f['status'] == 'Silindi'
                                        ? Colors.green
                                        : f['status'] == 'Hata'
                                            ? Colors.red
                                            : Colors.blue,
                                    fontSize: 10,
                                    fontWeight: FontWeight.bold,
                                  ),
                                ),
                              ),
                            ),
                          );
                        },
                      ),
              ),
            ),
            const SizedBox(height: 12),
            // Actions
            Row(
              children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: _isProcessing ? null : _clearList,
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white,
                      side: const BorderSide(color: Colors.white24),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: const Text('Listeyi Temizle'),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: _isProcessing ? null : _shredFiles,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFF66151),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: Text(_isProcessing ? 'Siliniyor...' : 'Güvenli Sil'),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            // Logs Console
            Container(
              height: 100,
              width: double.infinity,
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(8),
              ),
              child: ListView.builder(
                itemCount: _logs.length,
                itemBuilder: (context, index) {
                  return Text(
                    '> ${_logs[index]}',
                    style: const TextStyle(color: Colors.orangeAccent, fontSize: 11, fontFamily: 'monospace'),
                  );
                },
              ),
            )
          ],
        ),
      ),
    );
  }
}
