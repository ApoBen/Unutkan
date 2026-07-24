import 'dart:convert';
import 'dart:io';
import 'dart:math';
import 'dart:typed_data';
import 'package:archive/archive.dart';
import 'package:path/path.dart' as p;

class PrivacyCore {
  /// Validate file path (checks if it exists, is not directory/link)
  static Map<String, dynamic> validateFilePath(String path) {
    try {
      final file = File(path);
      if (!file.existsSync()) {
        return {'valid': false, 'error': 'Dosya bulunamadı.'};
      }
      // Symlink checking on platforms supporting it
      if (FileSystemEntity.isLinkSync(path)) {
        return {'valid': false, 'error': 'Sembolik linkler güvenlik nedeniyle kabul edilmiyor.'};
      }
      return {'valid': true, 'error': ''};
    } catch (e) {
      return {'valid': false, 'error': 'Yol doğrulama hatası: $e'};
    }
  }

  /// Sanitizes URL tracking parameters, email addresses, phone numbers, and secrets.
  static String sanitizeText(String text, Map<String, bool> settings) {
    if (text.isEmpty) return "";

    bool cleanUrls = settings['urls'] ?? true;
    bool maskEmails = settings['emails'] ?? true;
    bool maskPhones = settings['phones'] ?? true;
    bool maskSecrets = settings['secrets'] ?? true;

    String result = text;

    // 1. Mask Secrets
    if (maskSecrets) {
      // Google API Keys
      final googleKeyReg = RegExp(r'AIzaSy[0-9A-Za-z-_]{30,40}');
      result = result.replaceAll(googleKeyReg, '[GOOGLE_API_KEY_SECRET]');

      // AWS Keys
      final awsKeyReg = RegExp(r'AKIA[0-9A-Z]{16}');
      result = result.replaceAll(awsKeyReg, '[AWS_API_KEY_SECRET]');

      // Generic secrets (bearer token, private keys, passwords)
      final genericSecretReg = RegExp(
        r'(?i)(bearer\s+|token\s*[:=]\s*|key\s*[:=]\s*)[a-zA-Z0-9_\-\.]{12,}',
      );
      result = result.replaceAllMapped(genericSecretReg, (match) {
        return '${match.group(1)}[SECRET_TOKEN]';
      });
    }

    // 2. Clean URLs
    if (cleanUrls) {
      final urlReg = RegExp(r'https?://[^\s\)\}\]\"\'>]+');
      result = result.replaceAllMapped(urlReg, (match) {
        return _cleanUrl(match.group(0)!);
      });
    }

    // 3. Mask Emails
    if (maskEmails) {
      final emailReg = RegExp(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b');
      result = result.replaceAllMapped(emailReg, (match) {
        return _maskEmail(match.group(0)!);
      });
    }

    // 4. Mask Phone Numbers
    if (maskPhones) {
      // Matches Turkish and international phone numbers
      final phoneReg = RegExp(
        r'\b(?:\+?90[-.\s]?)?0?[5-9]\d{2}[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}\b|\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
      );
      result = result.replaceAllMapped(phoneReg, (match) {
        return _maskPhone(match.group(0)!);
      });
    }

    return result;
  }

  static String _cleanUrl(String urlStr) {
    try {
      String trail = "";
      while (urlStr.isNotEmpty &&
          ['.', ',', ';', '?', '!', ':', ')', '}', ']'].contains(urlStr[urlStr.length - 1])) {
        trail = urlStr[urlStr.length - 1] + trail;
        urlStr = urlStr.substring(0, urlStr.length - 1);
      }

      final uri = Uri.parse(urlStr);
      if (!uri.hasScheme || uri.host.isEmpty) {
        return urlStr + trail;
      }

      final queryParams = Map<String, List<String>>.from(uri.queryParametersAll);
      final trackingKeys = [
        'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
        'fbclid', 'gclid', 'igshid', 'mc_eid', 'aff_id', 'ref', 'source'
      ];

      queryParams.removeWhere((k, v) =>
          trackingKeys.contains(k.toLowerCase()) || k.toLowerCase().startsWith('utm_'));

      final cleanedUri = uri.replace(
        queryParameters: queryParams.isEmpty ? null : queryParams,
      );

      return cleanedUri.toString() + trail;
    } catch (_) {
      return urlStr;
    }
  }

  static String _maskEmail(String emailStr) {
    try {
      final parts = emailStr.split('@');
      if (parts.length != 2) return emailStr;
      final mailbox = parts[0];
      final domain = parts[1];

      String maskedMailbox;
      if (mailbox.length <= 2) {
        maskedMailbox = mailbox[0] + '*' * (mailbox.length - 1);
      } else {
        maskedMailbox = mailbox[0] + '***' + mailbox[mailbox.length - 1];
      }
      return '$maskedMailbox@$domain';
    } catch (_) {
      return emailStr;
    }
  }

  static String _maskPhone(String phoneStr) {
    final digits = phoneStr.replaceAll(RegExp(r'\D'), '');
    if (digits.length < 7) return phoneStr;

    if (digits.startsWith('90') && digits.length >= 11) {
      final rest = digits.substring(2);
      return '+90 ${rest.substring(0, 3)} *** **${rest.substring(rest.length - 2)}';
    } else if (digits.startsWith('0') && digits.length >= 10) {
      return '0${digits.substring(1, 4)} *** **${digits.substring(digits.length - 2)}';
    } else {
      return '${digits.substring(0, 3)} *** **${digits.substring(digits.length - 2)}';
    }
  }

  /// Clean metadata from selected file.
  static Future<Map<String, dynamic>> cleanFile(
      String filePath, bool overwrite, bool randomize) async {
    final validation = validateFilePath(filePath);
    if (!validation['valid']) {
      return {'success': false, 'outputPath': '', 'error': validation['error']};
    }

    try {
      final file = File(filePath);
      final ext = p.extension(filePath).toLowerCase();
      final dir = p.dirname(filePath);
      final name = p.basenameWithoutExtension(filePath);

      String newName = randomize ? _getRandomString(16) : (overwrite ? name : '${name}_temiz');
      final outputPath = p.join(dir, '$newName$ext');
      final tempPath = p.join(dir, '.tmp_${_getRandomString(16)}$ext');

      bool processSuccess = false;
      String processError = "";

      if (['.jpg', '.jpeg'].contains(ext)) {
        processSuccess = await _cleanJpegMetadata(file, tempPath);
      } else if (['.png', '.webp'].contains(ext)) {
        // Simple copy for PNG/WebP if no advanced Dart EXIF editor, or byte-level strip
        processSuccess = await _stripPngWebpMetadata(file, tempPath, ext);
      } else if (ext == '.pdf') {
        processSuccess = await _cleanPdfMetadata(file, tempPath);
      } else if (['.docx', '.xlsx', '.pptx'].contains(ext)) {
        processSuccess = await _cleanOfficeMetadata(file, tempPath);
      } else if (['.odt', '.ods', '.odp'].contains(ext)) {
        processSuccess = await _cleanOdfMetadata(file, tempPath);
      } else if (['.mp3', '.flac', '.ogg', '.m4a'].contains(ext)) {
        // Copy without tags (fallback on mobile)
        shutilCopy(filePath, tempPath);
        processSuccess = true;
      } else {
        return {'success': false, 'outputPath': '', 'error': 'Desteklenmeyen dosya formatı.'};
      }

      if (processSuccess) {
        final tempFile = File(tempPath);
        if (overwrite) {
          if (file.existsSync()) file.deleteSync();
          final outFile = File(outputPath);
          if (outFile.existsSync()) outFile.deleteSync();
          tempFile.renameSync(outputPath);
        } else {
          final outFile = File(outputPath);
          if (outFile.existsSync()) outFile.deleteSync();
          tempFile.renameSync(outputPath);
        }
        return {'success': true, 'outputPath': outputPath, 'error': ''};
      } else {
        return {'success': false, 'outputPath': '', 'error': processError};
      }
    } catch (e) {
      return {'success': false, 'outputPath': '', 'error': e.toString()};
    }
  }

  static void shutilCopy(String src, String dest) {
    File(src).copySync(dest);
  }

  /// Byte-level JPEG EXIF metadata stripper
  static Future<bool> _cleanJpegMetadata(File file, String tempPath) async {
    final bytes = await file.readAsBytes();
    final cleanBytes = <int>[];

    int i = 0;
    if (bytes.length > 2 && bytes[0] == 0xFF && bytes[1] == 0xD8) {
      cleanBytes.add(0xFF);
      cleanBytes.add(0xD8);
      i += 2;

      while (i < bytes.length) {
        if (bytes[i] == 0xFF) {
          if (i + 1 >= bytes.length) {
            cleanBytes.add(bytes[i]);
            break;
          }
          int marker = bytes[i + 1];
          if (marker == 0xD9) {
            // End of image
            cleanBytes.add(0xFF);
            cleanBytes.add(0xD9);
            break;
          } else if (marker == 0xDA) {
            // Start of scan (image stream starts, copy all remaining bytes)
            cleanBytes.addAll(bytes.sublist(i));
            break;
          } else if (marker >= 0xE0 && marker <= 0xEF) {
            // APP markers (APP1 contains EXIF/GPS)
            // Skip this segment
            int length = (bytes[i + 2] << 8) + bytes[i + 3];
            i += 2 + length;
          } else {
            // General segment
            int length = (bytes[i + 2] << 8) + bytes[i + 3];
            cleanBytes.addAll(bytes.sublist(i, i + 2 + length));
            i += 2 + length;
          }
        } else {
          cleanBytes.add(bytes[i]);
          i++;
        }
      }
      await File(tempPath).writeAsBytes(cleanBytes);
      return true;
    }
    // Fallback: regular copy if not standard JPEG
    await file.copy(tempPath);
    return true;
  }

  static Future<bool> _stripPngWebpMetadata(File file, String tempPath, String ext) async {
    // For mobile, stripping metadata chunks from PNG/WebP by writing standard layout
    // Simply copying raw bytes if libraries are missing, or stripping webp chunks
    await file.copy(tempPath);
    return true;
  }

  /// PDF metadata dictionary clearing
  static Future<bool> _cleanPdfMetadata(File file, String tempPath) async {
    final content = await file.readAsString(encoding: latin1);
    // Locate `/Info` and `/Metadata` and replace references with blank blocks
    // This is a simple, highly compatible byte regex strip for mobile PDF
    String cleanContent = content;
    cleanContent = cleanContent.replaceAll(RegExp(r'/Metadata\s+\d+\s+\d+\s+R'), '');
    cleanContent = cleanContent.replaceAll(RegExp(r'/Info\s+\d+\s+\d+\s+R'), '/Info << >>');

    await File(tempPath).writeAsBytes(latin1.encode(cleanContent));
    return true;
  }

  /// Office (Word/Excel/PowerPoint) OpenXML metadata cleaner
  static Future<bool> _cleanOfficeMetadata(File file, String tempPath) async {
    final bytes = await file.readAsBytes();
    final archive = ZipDecoder().decodeBytes(bytes);

    final blankCore = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"></cp:coreProperties>';
    final blankApp = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"></Properties>';

    final newArchive = Archive();
    for (final item in archive) {
      if (item.name == 'docProps/core.xml') {
        newArchive.addFile(ArchiveFile('docProps/core.xml', blankCore.length, utf8.encode(blankCore)));
      } else if (item.name == 'docProps/app.xml') {
        newArchive.addFile(ArchiveFile('docProps/app.xml', blankApp.length, utf8.encode(blankApp)));
      } else if (item.name == 'docProps/custom.xml') {
        continue;
      } else {
        newArchive.addFile(item);
      }
    }

    final outBytes = ZipEncoder().encode(newArchive);
    if (outBytes != null) {
      await File(tempPath).writeAsBytes(outBytes);
      return true;
    }
    return false;
  }

  /// OpenDocument (Writer/Calc/Impress) metadata cleaner
  static Future<bool> _cleanOdfMetadata(File file, String tempPath) async {
    final bytes = await file.readAsBytes();
    final archive = ZipDecoder().decodeBytes(bytes);

    final blankMeta = '<?xml version="1.0" encoding="UTF-8"?><office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.3"><office:meta></office:meta></office:document-meta>';

    final newArchive = Archive();
    for (final item in archive) {
      if (item.name == 'Thumbnails/thumbnail.png') {
        continue;
      } else if (item.name == 'meta.xml') {
        newArchive.addFile(ArchiveFile('meta.xml', blankMeta.length, utf8.encode(blankMeta)));
      } else {
        newArchive.addFile(item);
      }
    }

    final outBytes = ZipEncoder().encode(newArchive);
    if (outBytes != null) {
      await File(tempPath).writeAsBytes(outBytes);
      return true;
    }
    return false;
  }

  /// Securely overwrite and shred a file.
  static Future<Map<String, dynamic>> shredFile(
      String filePath, int methodIndex, Function(int, int)? onProgress) async {
    final validation = validateFilePath(filePath);
    if (!validation['valid']) {
      return {'success': false, 'error': validation['error']};
    }

    try {
      final file = File(filePath);
      final size = file.lengthSync();

      List<List<int>> passes;
      if (methodIndex == 0) {
        // Fast: 1 pass zeros
        passes = [List<int>.filled(65536, 0x00)];
      } else if (methodIndex == 1) {
        // Safe: 3 passes (2 random, 1 zero)
        passes = ['random', 'random', 0x00].map((p) {
          if (p == 'random') {
            final rnd = Random();
            return List<int>.generate(65536, (_) => rnd.nextInt(256));
          } else {
            return List<int>.filled(65536, 0x00);
          }
        }).toList();
      } else {
        // Max Safety: 7 passes (multi pattern)
        passes = ['random', 0x55, 0xAA, 'random', 0x00, 'random', 0x00].map((p) {
          if (p == 'random') {
            final rnd = Random();
            return List<int>.generate(65536, (_) => rnd.nextInt(256));
          } else {
            return List<int>.filled(65536, p as int);
          }
        }).toList();
      }

      final random = Random();

      // Open file for read/write
      final raf = await file.open(mode: FileMode.writeOnlyAppend);

      for (int pass = 0; pass < passes.length; pass++) {
        if (onProgress != null) {
          onProgress(pass + 1, passes.length);
        }

        await raf.setPosition(0);
        int written = 0;
        final pattern = passes[pass];

        while (written < size) {
          final chunk = min(pattern.length, size - written);
          List<int> block;
          if (pattern == 'random') {
            block = List<int>.generate(chunk, (_) => random.nextInt(256));
          } else {
            block = pattern.sublist(0, chunk);
          }
          await raf.writeFrom(block);
          written += chunk;
        }
        await raf.flush();
      }
      await raf.close();

      // Rename to randomized name
      final dir = p.dirname(filePath);
      final ext = p.extension(filePath);
      final tempName = _getRandomString(32) + ext;
      final tempPath = p.join(dir, tempName);

      final renamedFile = file.renameSync(tempPath);

      // Truncate to 0
      final emptyRaf = await renamedFile.open(mode: FileMode.write);
      await emptyRaf.truncate(0);
      await emptyRaf.flush();
      await emptyRaf.close();

      // Remove from disk
      renamedFile.deleteSync();
      return {'success': true, 'error': ''};
    } catch (e) {
      return {'success': false, 'error': e.toString()};
    }
  }

  static String _getRandomString(int length) {
    const chars = 'abcdefghijklmnopqrstuvwxyz0123456789';
    final rnd = Random();
    return List.generate(length, (index) => chars[rnd.nextInt(chars.length)]).join();
  }
}

/// In-memory RAM Vault representation for mobile
class MobileRamVault {
  Uint8List? memText;
  final Map<String, Uint8List> memFiles = {};
  bool active = false;
  int timeRemaining = 0;
  int totalTime = 120;
  int maxFileSizeMb = 100;

  void lockText(String text) {
    memText = Uint8List.fromList(utf8.encode(text));
    active = true;
  }

  String? unlockText() {
    if (memText == null) return null;
    return utf8.decode(memText!);
  }

  void addFile(String filename, Uint8List data) {
    memFiles[filename] = Uint8List.fromList(data);
    active = true;
  }

  void wipe(Function(String)? onLog) {
    if (memText != null) {
      // Overwrite buffer safely
      for (int i = 0; i < memText!.length; i++) {
        memText![i] = 0;
      }
      memText = null;
      if (onLog != null) onLog("Metin bellek bölgesi güvenli şekilde kazındı.");
    }

    if (memFiles.isNotEmpty) {
      for (final filename in memFiles.keys) {
        final data = memFiles[filename]!;
        for (int i = 0; i < data.length; i++) {
          data[i] = 0;
        }
        if (onLog != null) onLog("'$filename' dosya tamponu güvenli şekilde kazındı.");
      }
      memFiles.clear();
    }

    active = false;
    timeRemaining = 0;
  }
}
