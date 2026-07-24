import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:path/path.dart' as p;
import '../core/privacy_core.dart';

class CleanerScreen extends StatefulWidget {
  const CleanerScreen({super.key});

  @override
  State<CleanerScreen> createState() => _CleanerScreenState();
}

class _CleanerScreenState extends State<CleanerScreen> {
  final List<Map<String, dynamic>> _selectedFiles = [];
  final List<String> _logs = [];
  bool _overwrite = true;
  bool _randomize = false;
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
        type: FileType.custom,
        allowedExtensions: [
          'png', 'jpg', 'jpeg', 'webp',
          'pdf',
          'docx', 'xlsx', 'pptx',
          'odt', 'ods', 'odp',
          'mp3', 'flac', 'ogg', 'm4a'
        ],
      );

      if (result != null && result.files.isNotEmpty) {
        int added = 0;
        for (final file in result.files) {
          if (file.path != null) {
            final path = file.path!;
            final name = file.name;

            // Avoid duplicates
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
          _log('$added adet yeni dosya listeye eklendi.');
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
    _log('Dosya listesi temizlendi.');
  }

  Future<void> _processFiles() async {
    if (_selectedFiles.isEmpty) {
      _log('Listede temizlenecek dosya yok.', isError: true);
      return;
    }

    setState(() {
      _isProcessing = true;
    });

    _log('Temizleme işlemi başlatılıyor...');

    for (int i = 0; i < _selectedFiles.length; i++) {
      final fileInfo = _selectedFiles[i];
      if (fileInfo['status'] == 'Başarılı') continue;

      setState(() {
        fileInfo['status'] = 'Temizleniyor...';
      });

      _log('İşleniyor: ${fileInfo['name']}');

      final result = await PrivacyCore.cleanFile(
        fileInfo['path'],
        _overwrite,
        _randomize,
      );

      setState(() {
        if (result['success']) {
          fileInfo['status'] = 'Başarılı';
          fileInfo['path'] = result['outputPath'];
          fileInfo['name'] = p.basename(result['outputPath']);
          _log('Başarılı: ${fileInfo['name']}');
        } else {
          fileInfo['status'] = 'Hata';
          fileInfo['error'] = result['error'];
          _log('Hata: ${fileInfo['name']} (${result['error']})', isError: true);
        }
      });
    }

    _log('İşlem tamamlandı.');
    setState(() {
      _isProcessing = false;
    });
  }

  void _inspectMetadata(String filePath, String filename) {
    _log('Metadata inceleniyor: $filename');
    final meta = PrivacyCore.extract_file_metadata(filePath);

    showDialog(
      context: context,
      builder: (context) {
        return AlertDialog(
          backgroundColor: const Color(0xFF303030),
          title: Text(
            'Metadata Analizi - $filename',
            style: const TextStyle(color: Colors.white, fontSize: 16, fontWeight: FontWeight.bold),
          ),
          content: SizedBox(
            width: double.maxFinite,
            height: 300,
            child: meta.isEmpty
                ? const Center(
                    child: Text(
                      'Temizlenecek herhangi bir hassas metadata bulunamadı.',
                      style: TextStyle(color: Colors.green),
                    ),
                  )
                : ListView.builder(
                    itemCount: meta.length,
                    itemBuilder: (context, index) {
                      final key = meta.keys.elementAt(index);
                      final val = meta[key];
                      return Container(
                        margin: const EdgeInsets.only(bottom: 6),
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: const Color(0xFF242424),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          '$key: $val',
                          style: const TextStyle(color: Colors.redAccent, fontSize: 11, fontFamily: 'monospace'),
                        ),
                      );
                    },
                  ),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Kapat', style: TextStyle(color: Color(0xFF3584E4))),
            )
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF1E1E1E),
      appBar: AppBar(
        title: const Text('Metadata Temizleyici', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
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
                    color: _isProcessing ? Colors.white.withOpacity(0.05) : const Color(0xFF3584E4),
                    style: BorderStyle.dashed,
                    width: 2,
                  ),
                ),
                child: const Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.add_circle_outline, size: 36, color: Color(0xFF3584E4)),
                    SizedBox(height: 8),
                    Text(
                      'Dosyaları Seçmek İçin Dokunun',
                      style: TextStyle(color: Colors.white, fontSize: 13, fontWeight: FontWeight.bold),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Resim, PDF, Office, ODF ve Ses Dosyaları',
                      style: TextStyle(color: Color(0xFFB3B3B3), fontSize: 10),
                    )
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            // Options panel
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFF303030),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  CheckboxListTile(
                    title: const Text('Orijinal Dosyanın Üzerine Yaz', style: TextStyle(color: Colors.white, fontSize: 12)),
                    value: _overwrite,
                    activeColor: const Color(0xFF3584E4),
                    onChanged: _isProcessing ? null : (val) => setState(() => _overwrite = val ?? true),
                    controlAffinity: ListTileControlAffinity.leading,
                  ),
                  CheckboxListTile(
                    title: const Text('Dosya Adını Rastgeleleştir (UUID)', style: TextStyle(color: Colors.white, fontSize: 12)),
                    value: _randomize,
                    activeColor: const Color(0xFF3584E4),
                    onChanged: _isProcessing ? null : (val) => setState(() => _randomize = val ?? false),
                    controlAffinity: ListTileControlAffinity.leading,
                  ),
                ],
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
                    ? const Center(child: Text('Liste Boş', style: TextStyle(color: Color(0xFFB3B3B3))))
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
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  if (f['status'] == 'Hazır')
                                    ElevatedButton(
                                      onPressed: () => _inspectMetadata(f['path'], f['name']),
                                      style: ElevatedButton.styleFrom(
                                        backgroundColor: Colors.transparent,
                                        side: BorderSide(color: Colors.white.withOpacity(0.2)),
                                        padding: const EdgeInsets.symmetric(horizontal: 12),
                                      ),
                                      child: const Text('Detay', style: TextStyle(color: Colors.white, fontSize: 10)),
                                    ),
                                  const SizedBox(width: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                                    decoration: BoxDecoration(
                                      color: f['status'] == 'Başarılı'
                                          ? Colors.green.withOpacity(0.2)
                                          : f['status'] == 'Hata'
                                              ? Colors.red.withOpacity(0.2)
                                              : Colors.blue.withOpacity(0.2),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      f['status'],
                                      style: TextStyle(
                                        color: f['status'] == 'Başarılı'
                                            ? Colors.green
                                            : f['status'] == 'Hata'
                                                ? Colors.red
                                                : Colors.blue,
                                        fontSize: 10,
                                        fontWeight: FontWeight.bold,
                                      ),
                                    ),
                                  ),
                                ],
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
                    onPressed: _isProcessing ? null : _processFiles,
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFF3584E4),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                    child: Text(_isProcessing ? 'Temizleniyor...' : 'Temizliği Başlat'),
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
                    style: const TextStyle(color: Colors.greenAccent, fontSize: 11, fontFamily: 'monospace'),
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
