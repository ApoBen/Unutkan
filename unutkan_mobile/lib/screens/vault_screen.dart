import 'dart:async';
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:file_picker/file_picker.dart';
import 'package:share_plus/share_plus.dart';
import '../core/privacy_core.dart';

class VaultScreen extends StatefulWidget {
  const VaultScreen({super.key});

  @override
  State<VaultScreen> createState() => _VaultScreenState();
}

class _VaultScreenState extends State<VaultScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final MobileRamVault _vault = MobileRamVault();
  final List<String> _logs = [];

  final TextEditingController _vaultTextController = TextEditingController();
  Timer? _countdownTimer;

  int _selectedDurationIndex = 1; // Default 2 minutes
  int _selectedMaxFileIndex = 1; // Default 100 MB

  final List<int> _durations = [30, 120, 300, 600];
  final List<String> _durationLabels = ['30 Saniye', '2 Dakika', '5 Dakika', '10 Dakika'];

  final List<int> _maxFileSizes = [50, 100, 250, 500, 1000, 999999];
  final List<String> _maxFileLabels = ['50 MB', '100 MB', '250 MB', '500 MB', '1 GB', 'Limitsiz'];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _countdownTimer?.cancel();
    _tabController.dispose();
    _vaultTextController.dispose();
    super.dispose();
  }

  void _log(String message, {bool isError = false}) {
    setState(() {
      _logs.add(message);
    });
  }

  void _startTimer() {
    _countdownTimer?.cancel();
    final duration = _durations[_selectedDurationIndex];
    setState(() {
      _vault.timeRemaining = duration;
      _vault.totalTime = duration;
      _vault.active = true;
    });

    _log('Zamanlayıcı başlatıldı: $duration saniye.');

    _countdownTimer = Timer.periodic(const Duration(seconds: 1), (timer) {
      if (_vault.timeRemaining > 0) {
        setState(() {
          _vault.timeRemaining--;
        });
      } else {
        timer.cancel();
        _wipeVault();
        _log('[!] ZAMAN AŞIMI: Bellek kilitlendi ve veriler kazındı.');
      }
    });
  }

  void _wipeVault() {
    _countdownTimer?.cancel();
    setState(() {
      _vault.wipe((msg) => _log(msg));
      _vaultTextController.clear();
    });
    _log('Geçici bellek tamamen kazındı, kasa kilitlendi.');
  }

  void _lockText() {
    final text = _vaultTextController.text;
    if (text.isEmpty) {
      _log('Belleğe yüklenecek metin girilmedi.', isError: true);
      return;
    }

    setState(() {
      _vault.lockText(text);
      _vaultTextController.clear();
    });
    _log('Metin verisi RAM belleğe yüklendi ve ekran temizlendi.');
    _startTimer();
  }

  void _unlockText() {
    final decoded = _vault.unlockText();
    if (decoded != null) {
      setState(() {
        _vaultTextController.text = decoded;
      });
      _log('Metin verisi bellekten okunarak ekrana getirildi.');
    } else {
      _log('Bellekte çözülecek veri bulunamadı (Kilitli veya Boş).', isError: true);
    }
  }

  Future<void> _pickVaultFiles() async {
    try {
      final maxBytes = _maxFileSizes[_selectedMaxFileIndex] * 1024 * 1024;
      final result = await FilePicker.platform.pickFiles(
        allowMultiple: true,
        type: FileType.any,
      );

      if (result != null && result.files.isNotEmpty) {
        int added = 0;
        for (final file in result.files) {
          if (file.path != null) {
            final path = file.path!;
            final size = file.size;
            final name = file.name;

            if (size > maxBytes) {
              _log('Reddedildi ($name): Boyut limiti aşıldı.', isError: true);
              continue;
            }

            final data = await File(path).readAsBytes();
            setState(() {
              _vault.addFile(name, data);
            });
            _log('Dosya RAM belleğe yüklendi: $name ($size bayt)');
            added++;
          }
        }
        if (added > 0) {
          _startTimer();
        }
      }
    } catch (e) {
      _log('Dosya yükleme hatası: $e', isError: true);
    }
  }

  Future<void> _exportFile(String filename) async {
    if (_vault.memFiles.containsKey(filename)) {
      final data = _vault.memFiles[filename]!;
      // Write temporarily to share it safely
      final tempDir = Directory.systemTemp;
      final tempFile = File('${tempDir.path}/$filename');
      await tempFile.writeAsBytes(data);

      await Share.shareXFiles([XFile(tempFile.path)], text: 'Dışarı Aktarılan Dosya');
      _log("Dosya dışarı aktarıldı: $filename");
    }
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _vault.active ? const Color(0xFF2EC27E) : const Color(0xFFF66151);

    return Scaffold(
      backgroundColor: const Color(0xFF1E1E1E),
      appBar: AppBar(
        title: const Text('Geçici Bellek Kasası', style: TextStyle(color: Colors.white, fontSize: 18, fontWeight: FontWeight.bold)),
        backgroundColor: const Color(0xFF242424),
        iconTheme: const IconThemeData(color: Colors.white),
        elevation: 0,
      ),
      body: Padding(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          children: [
            // Left/Top Status Area
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: const Color(0xFF303030),
                borderRadius: BorderRadius.circular(12),
              ),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text('KASA DURUMU:', style: TextStyle(color: Colors.grey, fontSize: 11, fontWeight: FontWeight.bold)),
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: statusColor.withOpacity(0.1),
                          border: Border.all(color: statusColor.withOpacity(0.3)),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Text(
                          _vault.active ? 'BELLEK AKTİF' : 'KİLİTLİ / BOŞ',
                          style: TextStyle(color: statusColor, fontSize: 11, fontWeight: FontWeight.bold),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        _vault.active ? 'Kalan Süre: ${_vault.timeRemaining} sn' : 'Zamanlayıcı Pasif',
                        style: const TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                      ),
                      if (_vault.active)
                        SizedBox(
                          width: 100,
                          child: LinearProgressIndicator(
                            value: _vault.timeRemaining / _vault.totalTime,
                            backgroundColor: Colors.grey.withOpacity(0.2),
                            valueColor: const AlwaysStoppedAnimation<Color>(Color(0xFF2EC27E)),
                          ),
                        ),
                    ],
                  ),
                  const Divider(color: Colors.white12, height: 24),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Süre:', style: TextStyle(color: Colors.grey, fontSize: 10)),
                            DropdownButton<int>(
                              value: _selectedDurationIndex,
                              dropdownColor: const Color(0xFF303030),
                              style: const TextStyle(color: Colors.white, fontSize: 11),
                              underline: const SizedBox(),
                              isExpanded: true,
                              onChanged: (val) {
                                if (val != null) {
                                  setState(() {
                                    _selectedDurationIndex = val;
                                  });
                                }
                              },
                              items: List.generate(_durations.length, (index) {
                                return DropdownMenuItem(
                                  value: index,
                                  child: Text(_durationLabels[index]),
                                );
                              }),
                            ),
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('Limit:', style: TextStyle(color: Colors.grey, fontSize: 10)),
                            DropdownButton<int>(
                              value: _selectedMaxFileIndex,
                              dropdownColor: const Color(0xFF303030),
                              style: const TextStyle(color: Colors.white, fontSize: 11),
                              underline: const SizedBox(),
                              isExpanded: true,
                              onChanged: (val) {
                                if (val != null) {
                                  setState(() {
                                    _selectedMaxFileIndex = val;
                                    _vault.maxFileSizeMb = _maxFileSizes[val];
                                  });
                                }
                              },
                              items: List.generate(_maxFileSizes.length, (index) {
                                return DropdownMenuItem(
                                  value: index,
                                  child: Text(_maxFileLabels[index]),
                                );
                              }),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  SizedBox(
                    width: double.infinity,
                    child: ElevatedButton(
                      onPressed: _wipeVault,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: const Color(0xFFF66151),
                        foregroundColor: Colors.white,
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      ),
                      child: const Text('Belleği Şimdi Kazı (Wipe)', style: TextStyle(fontSize: 12)),
                    ),
                  )
                ],
              ),
            ),
            const SizedBox(height: 12),
            // Tabs panel
            TabBar(
              controller: _tabController,
              labelColor: Colors.white,
              unselectedLabelColor: Colors.grey,
              indicatorColor: const Color(0xFF2EC27E),
              tabs: const [
                Tab(text: 'Metin Kasası'),
                Tab(text: 'Dosya Kasası'),
              ],
            ),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  // Tab 1: Text Vault
                  Padding(
                    padding: const EdgeInsets.only(top: 8.0),
                    child: Column(
                      children: [
                        Expanded(
                          child: TextField(
                            controller: _vaultTextController,
                            maxLines: null,
                            expands: true,
                            style: const TextStyle(color: Colors.white, fontSize: 12),
                            decoration: InputDecoration(
                              hintText: 'Bellekte geçici olarak tutulacak şifre veya notları girin...',
                              hintStyle: const TextStyle(color: Colors.grey, fontSize: 11),
                              fillColor: const Color(0xFF303030),
                              filled: true,
                              border: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide.none),
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Row(
                          children: [
                            Expanded(
                              child: ElevatedButton(
                                onPressed: _lockText,
                                style: ElevatedButton.styleFrom(
                                  backgroundColor: const Color(0xFF3584E4),
                                  foregroundColor: Colors.white,
                                ),
                                child: const Text('Kilitle & Gizle'),
                              ),
                            ),
                            const SizedBox(width: 8),
                            Expanded(
                              child: OutlinedButton(
                                onPressed: _unlockText,
                                style: OutlinedButton.styleFrom(
                                  foregroundColor: Colors.white,
                                  side: const BorderSide(color: Colors.white24),
                                ),
                                child: const Text('Belleği Göster'),
                              ),
                            ),
                          ],
                        )
                      ],
                    ),
                  ),
                  // Tab 2: File Vault
                  Padding(
                    padding: const EdgeInsets.only(top: 8.0),
                    child: Column(
                      children: [
                        GestureDetector(
                          onTap: _pickVaultFiles,
                          child: Container(
                            height: 60,
                            width: double.infinity,
                            decoration: BoxDecoration(
                              color: const Color(0xFF303030),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(
                                color: const Color(0xFF2EC27E),
                              ),
                            ),
                            child: const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                Icon(Icons.file_upload, color: Color(0xFF2EC27E), size: 20),
                                SizedBox(width: 8),
                                Text(
                                  'Dosyaları RAM\'e Yükle',
                                  style: TextStyle(color: Colors.white, fontSize: 12, fontWeight: FontWeight.bold),
                                )
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(height: 8),
                        Expanded(
                          child: Container(
                            decoration: BoxDecoration(
                              color: const Color(0xFF303030),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: _vault.memFiles.isEmpty
                                ? const Center(child: Text('Kasa Boş', style: TextStyle(color: Colors.grey)))
                                : ListView.builder(
                                    itemCount: _vault.memFiles.length,
                                    itemBuilder: (context, index) {
                                      final filename = _vault.memFiles.keys.elementAt(index);
                                      final size = _vault.memFiles[filename]!.length;
                                      return Card(
                                        color: const Color(0xFF242424),
                                        child: ListTile(
                                          title: Text(filename, style: const TextStyle(color: Colors.white, fontSize: 11)),
                                          subtitle: Text('$size bayt (RAM Bellekte)', style: const TextStyle(color: Colors.grey, fontSize: 9)),
                                          trailing: IconButton(
                                            icon: const Icon(Icons.share, color: Color(0xFF2EC27E), size: 18),
                                            onPressed: () => _exportFile(filename),
                                          ),
                                        ),
                                      );
                                    },
                                  ),
                          ),
                        )
                      ],
                    ),
                  )
                ],
              ),
            ),
            const SizedBox(height: 8),
            // Logs Console
            Container(
              height: 70,
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
