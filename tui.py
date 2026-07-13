#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import uuid
import zipfile
import shutil
import re
import gc
import time
import threading
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# Try importing external non-GUI dependencies
try:
    from PIL import Image
except ImportError:
    Image = None

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader, PdfWriter = None, None

try:
    import mutagen
except ImportError:
    mutagen = None

# ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_BLUE = "\033[44m"

# Security Helper
def validate_file_path(path):
    """Validate that a path is a regular file, not a symlink, device, or directory."""
    real_path = os.path.realpath(path)
    if os.path.islink(path):
        return False, real_path, "Sembolik linkler güvenlik nedeniyle kabul edilmiyor."
    if not os.path.isfile(real_path):
        return False, real_path, "Yol bir dosyaya işaret etmiyor (dizin, cihaz veya pipe olabilir)."
    return True, real_path, ""

# Core Cleaner Logic
def extract_file_metadata(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    metadata = {}
    try:
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            if Image is None:
                return {"Hata": "Pillow kütüphanesi yüklü değil."}
            with Image.open(file_path) as img:
                exif = img.getexif()
                if exif:
                    for tag_id in exif:
                        tag = Image.ExifTags.TAGS.get(tag_id, tag_id)
                        data = exif.get(tag_id)
                        if isinstance(data, bytes):
                            try:
                                data = data.decode(errors='replace')
                            except Exception:
                                pass
                        metadata[f"EXIF: {tag}"] = str(data)
                
                for k, v in img.info.items():
                    if k not in ['exif', 'icc_profile']:
                        metadata[f"Görüntü: {k}"] = str(v)
                        
        elif ext == '.pdf':
            if PdfReader is None:
                return {"Hata": "pypdf kütüphanesi yüklü değil."}
            reader = PdfReader(file_path)
            meta = reader.metadata
            if meta:
                for k, v in meta.items():
                    key = k[1:] if k.startswith('/') else k
                    metadata[f"PDF: {key}"] = str(v)
                    
        elif ext in ['.docx', '.xlsx', '.pptx']:
            with zipfile.ZipFile(file_path, 'r') as z:
                if 'docProps/core.xml' in z.namelist():
                    xml_content = z.read('docProps/core.xml').decode('utf-8', errors='replace')
                    tags = ['title', 'creator', 'lastModifiedBy', 'revision', 'created', 'modified']
                    for tag in tags:
                        pattern = re.compile(r'<dcterms:{0}[^>]*>(.*?)</dcterms:{0}>|<cp:{0}[^>]*>(.*?)</cp:{0}>|<dc:{0}[^>]*>(.*?)</dc:{0}>'.format(tag))
                        match = pattern.search(xml_content)
                        if match:
                            val = next(group for group in match.groups() if group is not None)
                            metadata[f"Office: {tag}"] = val
                            
        elif ext in ['.odt', '.ods', '.odp']:
            with zipfile.ZipFile(file_path, 'r') as z:
                if 'meta.xml' in z.namelist():
                    xml_content = z.read('meta.xml').decode('utf-8', errors='replace')
                    tags = ['title', 'creator', 'creation-date', 'date', 'generator', 'editing-duration']
                    for tag in tags:
                        pattern = re.compile(r'<dc:{0}[^>]*>(.*?)</dc:{0}>|<meta:{0}[^>]*>(.*?)</meta:{0}>'.format(tag))
                        match = pattern.search(xml_content)
                        if match:
                            val = next(group for group in match.groups() if group is not None)
                            metadata[f"ODF: {tag}"] = val
                            
        elif ext in ['.mp3', '.flac', '.ogg', '.m4a']:
            if mutagen is None:
                return {"Hata": "mutagen kütüphanesi yüklü değil."}
            audio = mutagen.File(file_path)
            if audio:
                for k, v in audio.items():
                    metadata[f"Ses: {k}"] = str(v)
    except Exception as e:
        metadata["Hata"] = f"Metadata okunamadı: {str(e)}"
        
    return metadata

def clean_file(file_path, overwrite, randomize):
    temp_path = ""
    try:
        valid, real_path, err = validate_file_path(file_path)
        if not valid:
            return False, "", err
        file_path = real_path

        directory = os.path.dirname(file_path)
        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)
        ext_lower = ext.lower()

        if randomize:
            new_name = uuid.uuid4().hex
        else:
            new_name = name if overwrite else f"{name}_temiz"
        
        output_filename = f"{new_name}{ext_lower}"
        output_path = os.path.join(directory, output_filename)
        temp_path = os.path.join(directory, f".tmp_{uuid.uuid4().hex}{ext_lower}")

        # Check file libraries
        if ext_lower in ['.jpg', '.jpeg', '.webp', '.png']:
            if Image is None:
                return False, "", "Pillow kütüphanesi yüklü değil."
            with Image.open(file_path) as img:
                if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
                    clean_img = img.copy()
                else:
                    clean_img = Image.new(img.mode, img.size)
                    clean_img.putdata(img.getdata())
                clean_img.info = {}
                if ext_lower in ['.jpg', '.jpeg']:
                    clean_img.save(temp_path, format='JPEG', exif=b"", quality=95)
                elif ext_lower == '.png':
                    clean_img.save(temp_path, format='PNG', pnginfo=None)
                elif ext_lower == '.webp':
                    clean_img.save(temp_path, format='WEBP')

        elif ext_lower == '.pdf':
            if PdfReader is None:
                return False, "", "pypdf kütüphanesi yüklü değil."
            reader = PdfReader(file_path)
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            # Safe empty metadata
            writer.add_metadata({})
            with open(temp_path, 'wb') as f:
                writer.write(f)

        elif ext_lower in ['.docx', '.xlsx', '.pptx', '.odt', '.ods', '.odp']:
            shutil.copyfile(file_path, temp_path)
            # Remove metadata components from zip structure
            try:
                temp_zip_path = temp_path + ".zip"
                os.rename(temp_path, temp_zip_path)
                
                with zipfile.ZipFile(temp_zip_path, 'r') as zin:
                    with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                        for item in zin.infolist():
                            if ext_lower in ['.docx', '.xlsx', '.pptx']:
                                if item.filename in ['docProps/core.xml', 'docProps/app.xml']:
                                    # Write blank minimal core props
                                    blank_core = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"></cp:coreProperties>'
                                    zout.writestr(item, blank_core)
                                    continue
                            elif ext_lower in ['.odt', '.ods', '.odp']:
                                if item.filename == 'meta.xml':
                                    blank_meta = '<?xml version="1.0" encoding="UTF-8"?><office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.2"></office:document-meta>'
                                    zout.writestr(item, blank_meta)
                                    continue
                                if item.filename == 'Thumbnails/thumbnail.png':
                                    continue
                            
                            zout.writestr(item, zin.read(item.filename))
                os.remove(temp_zip_path)
            except Exception as e:
                if os.path.exists(temp_zip_path):
                    os.remove(temp_zip_path)
                raise e

        elif ext_lower in ['.mp3', '.flac', '.ogg', '.m4a']:
            if mutagen is None:
                return False, "", "mutagen kütüphanesi yüklü değil."
            shutil.copyfile(file_path, temp_path)
            audio = mutagen.File(temp_path)
            if audio is not None:
                audio.delete()
                audio.save()
        else:
            return False, "", f"Desteklenmeyen dosya formatı: {ext_lower}"

        if overwrite:
            if os.path.exists(file_path):
                os.remove(file_path)
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_path, output_path)
        else:
            if os.path.exists(output_path):
                os.remove(output_path)
            os.rename(temp_path, output_path)

        return True, output_path, ""

    except Exception as e:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        return False, "", str(e)

# Core Shredder Logic
def shred_file(file_path, method_index, progress_callback=None):
    try:
        valid, real_path, err = validate_file_path(file_path)
        if not valid:
            return False, err
        file_path = real_path
            
        file_size = os.path.getsize(file_path)
        
        if method_index == 0:
            passes = [b'\x00']
        elif method_index == 1:
            passes = ['random', 'random', b'\x00']
        else:
            passes = ['random', b'\x55', b'\xAA', 'random', b'\x00', 'random', b'\x00']

        # Open with O_NOFOLLOW to prevent symlink race conditions
        fd = os.open(file_path, os.O_RDWR | os.O_NOFOLLOW)
        with os.fdopen(fd, "r+b") as f:
            for p_num, pattern in enumerate(passes):
                if progress_callback:
                    progress_callback(p_num + 1, len(passes))
                f.seek(0)
                block_size = 64 * 1024
                bytes_written = 0
                
                while bytes_written < file_size:
                    left = file_size - bytes_written
                    current_block = min(block_size, left)
                    
                    if pattern == 'random':
                        data = os.urandom(current_block)
                    else:
                        data = pattern * current_block
                        
                    f.write(data)
                    bytes_written += current_block
                
                f.flush()
                os.fsync(f.fileno())

        directory = os.path.dirname(file_path)
        ext = os.path.splitext(file_path)[1]
        temp_name = uuid.uuid4().hex + ext
        temp_path = os.path.join(directory, temp_name)
        
        os.rename(file_path, temp_path)
        
        with open(temp_path, "w") as f:
            f.truncate(0)
            f.flush()
            os.fsync(f.fileno())
            
        os.remove(temp_path)
        return True, ""
        
    except Exception as e:
        return False, str(e)

# Core Sanitizer Logic
def _clean_url(url_str):
    try:
        trail = ""
        if url_str.endswith('/') and len(url_str) > 1:
            trail = "/"
            url_str = url_str[:-1]

        parsed = urlparse(url_str)
        if not parsed.scheme or not parsed.netloc:
            return url_str + trail
        
        query = parse_qs(parsed.query)
        tracking_keys = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content', 
            'fbclid', 'gclid', 'igshid', 'mc_eid', 'aff_id', 'ref', 'source'
        ]
        for k in list(query.keys()):
            if k.lower() in tracking_keys or k.lower().startswith('utm_'):
                query.pop(k, None)
                
        new_query = urlencode(query, doseq=True)
        new_parts = list(parsed)
        new_parts[4] = new_query
        return urlunparse(new_parts) + trail
    except (ValueError, KeyError):
        return url_str

def _mask_email(email_str):
    try:
        mailbox, domain = email_str.split('@', 1)
        if len(mailbox) <= 2:
            masked = mailbox[0] + '*' * (len(mailbox) - 1)
        else:
            masked = mailbox[0] + '***' + mailbox[-1]
        return f"{masked}@{domain}"
    except (ValueError, IndexError):
        return email_str

def _mask_phone(phone_str):
    digits = [c for c in phone_str if c.isdigit()]
    if len(digits) < 7:
        return phone_str
        
    clean_digits = "".join(digits)
    if clean_digits.startswith("90") and len(clean_digits) >= 11:
        rest = clean_digits[2:]
        return f"+90 {rest[:3]} *** **{rest[-2:]}"
    elif clean_digits.startswith("0") and len(clean_digits) >= 10:
        return f"0{clean_digits[1:4]} *** **{clean_digits[-2:]}"
    else:
        return f"{clean_digits[:3]} *** **{clean_digits[-2:]}"

def _mask_secrets(text):
    # Regex to detect secrets
    patterns = {
        'API Key / Token': r'(?i)(?:api_key|apikey|secret|token|password|passwd|private_key|passwd|access_token|auth_token)\s*[:=]\s*["\']([a-zA-Z0-9_\-\.\=\+]{8,})["\']',
        'Generic Key': r'(?i)\b(?:key|secret|token)[-_\w]{0,10}["\']?\s*[:=]\s*["\']?([a-zA-Z0-9_\-\.\=\+]{16,})["\']?\b'
    }
    cleaned = text
    for desc, pat in patterns.items():
        matches = re.finditer(pat, cleaned)
        for m in matches:
            if len(m.groups()) > 0:
                raw_secret = m.group(1)
                masked_secret = raw_secret[:3] + "..." + raw_secret[-3:]
                cleaned = cleaned.replace(raw_secret, masked_secret)
    return cleaned

def sanitize_text(text, settings):
    # Settings is a dict with boolean values
    result = text
    if settings.get('urls', True):
        # Find and sanitize URLs
        url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
        urls = url_pattern.findall(result)
        for url in urls:
            result = result.replace(url, _clean_url(url))

    if settings.get('emails', True):
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
        emails = email_pattern.findall(result)
        for email in emails:
            result = result.replace(email, _mask_email(email))

    if settings.get('phones', True):
        phone_pattern = re.compile(r'\b(?:\+?90[- ]?)?0?[5-9]\d{2}[- ]?\d{3}[- ]?\d{2}[- ]?\d{2}\b')
        phones = phone_pattern.findall(result)
        for phone in phones:
            result = result.replace(phone, _mask_phone(phone))

    if settings.get('secrets', True):
        result = _mask_secrets(result)

    return result

# RAM Vault State
class TuiVault:
    def __init__(self):
        self.mem_text = None
        self.mem_files = {}
        self.time_left = 0
        self.total_time = 120
        self.max_file_size_mb = 100
        self.timer_thread = None
        self.lock = threading.Lock()
        self.active = False

    def start_timer(self, duration_sec, log_callback):
        with self.lock:
            self.total_time = duration_sec
            self.time_left = duration_sec
            self.active = True
            
        if self.timer_thread is None or not self.timer_thread.is_alive():
            self.timer_thread = threading.Thread(target=self._run_timer, args=(log_callback,), daemon=True)
            self.timer_thread.start()

    def _run_timer(self, log_callback):
        while True:
            time.sleep(1)
            with self.lock:
                if not self.active:
                    break
                if self.time_left > 0:
                    self.time_left -= 1
                else:
                    self.active = False
                    self._wipe_internal(log_callback)
                    log_callback("[!] ZAMAN AŞIMI: Bellek kilitlendi ve veriler kazındı.")
                    break

    def wipe(self, log_callback):
        with self.lock:
            self.active = False
            self._wipe_internal(log_callback)

    def _wipe_internal(self, log_callback):
        wipe_errors = []
        if self.mem_text:
            try:
                mv = memoryview(self.mem_text)
                block_size = 1024 * 1024
                zero_block = b'\x00' * block_size
                length = len(self.mem_text)
                for offset in range(0, length, block_size):
                    chunk = min(block_size, length - offset)
                    mv[offset:offset+chunk] = zero_block[:chunk]
                log_callback("[Güvenli] Metin bellek bölgesi güvenli şekilde kazındı.")
            except Exception as e:
                wipe_errors.append(str(e))
                log_callback(f"[UYARI] Metin bellek kazıma başarısız: {e}")
            self.mem_text = None

        if self.mem_files:
            for filename, data in list(self.mem_files.items()):
                try:
                    mv = memoryview(data)
                    block_size = 1024 * 1024
                    zero_block = b'\x00' * block_size
                    length = len(data)
                    for offset in range(0, length, block_size):
                        chunk = min(block_size, length - offset)
                        mv[offset:offset+chunk] = zero_block[:chunk]
                    log_callback(f"[Güvenli] '{filename}' dosya tamponu güvenli şekilde kazındı.")
                except Exception as e:
                    wipe_errors.append(str(e))
                    log_callback(f"[UYARI] '{filename}' bellek kazıma başarısız: {e}")
            self.mem_files.clear()
            
        gc.collect()

# Main Interactive Loop
vault = TuiVault()

def clear_screen():
    os.system('clear' if os.name == 'posix' else 'cls')

def header(subtitle=""):
    clear_screen()
    print(BOLD + BLUE + "==================================================" + RESET)
    print(BOLD + CYAN + "  _   _ _   _ _   _ _____ _  __     _     _   _ " + RESET)
    print(BOLD + CYAN + " | | | | \\ | | | | |_   _| |/ /    / \\   | \\ | |" + RESET)
    print(BOLD + CYAN + " | | | |  \\| | | |   | | | ' /    / _ \\  |  \\| |" + RESET)
    print(BOLD + CYAN + " | |_| | |\\  | |_|   | | | . \\   / ___ \\ | |\\  |" + RESET)
    print(BOLD + CYAN + "  \\___/|_| \\_|\\___/  |_| |_|\\_\\ /_/   \\_\\|_| \\_|" + RESET)
    print(BOLD + BLUE + "==================================================" + RESET)
    print(BOLD + WHITE + "       Güvenli Metadata Temizleyici & Hijyen TUI  " + RESET)
    print(BOLD + BLUE + "==================================================" + RESET)
    if subtitle:
        print(BOLD + MAGENTA + f" >>> {subtitle} <<<" + RESET)
        print(BOLD + BLUE + "--------------------------------------------------" + RESET)

def main_menu():
    while True:
        header("ANA MENÜ")
        if vault.active:
            print(BOLD + YELLOW + f" [Kasa Durumu: AÇIK - Kalan Süre: {vault.time_left} sn]" + RESET)
        else:
            print(BOLD + GREEN + " [Kasa Durumu: KİLİTLİ / BOŞ]" + RESET)
        print()
        print(" 1. Metadata Temizleyici (Resim, PDF, Office, Ses)")
        print(" 2. Güvenli Dosya Silici (Geri Döndürülemez Silme)")
        print(" 3. Metin Arındırıcı (Takip Linki, Email, Telefon Maskeleme)")
        print(" 4. Geçici Bellek Kasası (Güvenli RAM Deposu)")
        print(" 5. Çıkış")
        print()
        
        choice = input(BOLD + WHITE + "Seçiminiz [1-5]: " + RESET).strip()
        if choice == "1":
            cleaner_menu()
        elif choice == "2":
            shredder_menu()
        elif choice == "3":
            sanitizer_menu()
        elif choice == "4":
            vault_menu()
        elif choice == "5":
            if vault.active:
                print(YELLOW + "Kasa temizleniyor..." + RESET)
                vault.wipe(print)
            print(GREEN + "Unutkan'ı kullandığınız için teşekkürler. Güvende kalın!" + RESET)
            break

def cleaner_menu():
    while True:
        header("METADATA TEMİZLEYİCİ")
        print(" 1. Dosya Metadatalarını İncele (Önizleme)")
        print(" 2. Dosya Temizle (Orijinal Üzerine Yaz)")
        print(" 3. Dosya Temizle (Yeni Dosya Olarak Kaydet)")
        print(" 4. Ana Menüye Dön")
        print()
        
        choice = input(BOLD + WHITE + "Seçiminiz [1-4]: " + RESET).strip()
        if choice == "4":
            break
            
        if choice in ["1", "2", "3"]:
            file_path = input("İşlem yapılacak dosyanın tam yolu: ").strip().strip('"\'')
            if not os.path.exists(file_path):
                print(RED + "[Hata] Belirtilen dosya bulunamadı." + RESET)
                input("\nDevam etmek için Enter'a basın...")
                continue
                
            valid, real_path, err = validate_file_path(file_path)
            if not valid:
                print(RED + f"[Hata] {err}" + RESET)
                input("\nDevam etmek için Enter'a basın...")
                continue

            if choice == "1":
                header("METADATA İNCELEME")
                print(BOLD + f"Dosya: {os.path.basename(real_path)}" + RESET)
                print(BLUE + "Okunan Metadatalar:" + RESET)
                print("--------------------------------------------------")
                meta = extract_file_metadata(real_path)
                if not meta:
                    print(YELLOW + "Herhangi bir metadata bulunamadı." + RESET)
                else:
                    for k, v in meta.items():
                        print(f"  {BOLD}{k}{RESET}: {v}")
                print("--------------------------------------------------")
                input("\nGeri dönmek için Enter'a basın...")
            else:
                overwrite = (choice == "2")
                randomize = False
                if not overwrite:
                    ans = input("Temizlenmiş dosya adı rastgele (UUID) mi olsun? [e/H]: ").strip().lower()
                    randomize = (ans == 'e')
                
                print(BLUE + "\nDosya temizleniyor..." + RESET)
                success, out_path, err = clean_file(real_path, overwrite, randomize)
                if success:
                    print(GREEN + f"[Başarılı] Dosya başarıyla temizlendi." + RESET)
                    print(f"Çıktı Yolu: {BOLD}{out_path}{RESET}")
                else:
                    print(RED + f"[Başarısız] Hata: {err}" + RESET)
                input("\nDevam etmek için Enter'a basın...")

def shredder_menu():
    while True:
        header("GÜVENLİ DOSYA SİLİCİ")
        print(RED + "⚠️ UYARI: Bu işlem dosyaları fiziksel olarak diskte ezerek yok eder. KURTARILAMAZ!" + RESET)
        print()
        file_path = input("İmha edilecek dosya yolu (Boş bırakarak menüye dönebilirsiniz): ").strip().strip('"\'')
        if not file_path:
            break
            
        if not os.path.exists(file_path):
            print(RED + "[Hata] Belirtilen dosya bulunamadı." + RESET)
            input("\nDevam etmek için Enter'a basın...")
            continue
            
        valid, real_path, err = validate_file_path(file_path)
        if not valid:
            print(RED + f"[Hata] {err}" + RESET)
            input("\nDevam etmek için Enter'a basın...")
            continue

        print("\nSilme Yöntemleri:")
        print(" 1. Hızlı Sıfırla (1 Geçiş - Sıfır Yazma)")
        print(" 2. Güvenli (3 Geçiş - Rastgele + Sıfır)")
        print(" 3. Maksimum Güvenlik (7 Geçiş - Çoklu Desen)")
        method_choice = input("Yöntem seçiniz [1-3]: ").strip()
        
        method_idx = 1
        if method_choice == "1":
            method_idx = 0
        elif method_choice == "3":
            method_idx = 2

        confirm = input(RED + BOLD + f"\n'{os.path.basename(real_path)}' dosyasını KALICI olarak imha etmek istediğinize emin misiniz? [evet/Hayırlı]: " + RESET).strip().lower()
        if confirm == "evet":
            print(BLUE + "\nİmha işlemi başlatıldı..." + RESET)
            def progress(p, total):
                print(YELLOW + f"  Geçiş {p}/{total} yazılıyor..." + RESET)
            
            success, err = shred_file(real_path, method_idx, progress)
            if success:
                print(GREEN + BOLD + "[Başarılı] Dosya geri döndürülemeyecek şekilde tamamen imha edildi!" + RESET)
            else:
                print(RED + f"[Hata] İmha edilemedi: {err}" + RESET)
        else:
            print(YELLOW + "İşlem iptal edildi." + RESET)
            
        input("\nDevam etmek için Enter'a basın...")

def sanitizer_menu():
    header("METİN ARINDIRICI")
    print("Maskelenecek metni girin (Girişi bitirmek için son satırda Ctrl+D yapın veya boş bırakıp enter yapın):")
    print("--------------------------------------------------")
    
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
        
    text = "\n".join(lines)
    if not text.strip():
        return
        
    settings = {
        'urls': True,
        'emails': True,
        'phones': True,
        'secrets': True
    }
    
    sanitized = sanitize_text(text, settings)
    
    header("ARINDIRILMIŞ METİN")
    print(GREEN + "Filtrelenmiş Sonuç:" + RESET)
    print("--------------------------------------------------")
    print(BOLD + sanitized + RESET)
    print("--------------------------------------------------")
    input("\nGeri dönmek için Enter'a basın...")

def vault_menu():
    while True:
        header("GEÇİCİ BELLEK KASASI (RAM VAULT)")
        if vault.active:
            print(BOLD + GREEN + f" STATUS: KASA AÇIK (Kalan Süre: {vault.time_left} sn)" + RESET)
            print(f" Yüklü Metin: {BOLD}{'Var (Gizli)' if vault.mem_text else 'Yok'}{RESET}")
            print(f" Yüklü Dosyalar: {BOLD}{len(vault.mem_files)} adet{RESET}")
        else:
            print(BOLD + RED + " STATUS: KİLİTLİ / BOŞ" + RESET)
            
        print()
        print(" 1. Metni RAM Belleğe Kilitle")
        print(" 2. Metni RAM Bellekten Oku ve Ekrana Getir")
        print(" 3. Dosyayı RAM Belleğe Yükle")
        print(" 4. RAM Bellekteki Dosyaları Listele")
        print(" 5. Kasayı Şimdi Kazı (Manuel Wipe)")
        print(" 6. Kasa Süresini Ayarla (Varsayılan 2 dk)")
        print(" 7. Maksimum Dosya Boyutunu Ayarla (Varsayılan 100 MB)")
        print(" 8. Ana Menüye Dön")
        print()
        
        choice = input(BOLD + WHITE + "Seçiminiz [1-8]: " + RESET).strip()
        if choice == "8":
            break
            
        if choice == "1":
            text = input("RAM'e kilitlenecek hassas metni girin: ").strip()
            if text:
                vault.mem_text = bytearray(text, 'utf-8')
                del text
                gc.collect()
                print(GREEN + "Metin başarıyla RAM'e kilitlendi." + RESET)
                vault.start_timer(vault.total_time, lambda msg: None)
            input("\nDevam etmek için Enter'a basın...")
            
        elif choice == "2":
            if vault.mem_text:
                try:
                    decoded = vault.mem_text.decode('utf-8')
                    print("\n" + BOLD + CYAN + "--- RAM Bellekteki Gizli Metin ---" + RESET)
                    print(decoded)
                    print(BOLD + CYAN + "---------------------------------" + RESET)
                    del decoded
                except Exception as e:
                    print(RED + f"Çözümleme hatası: {e}" + RESET)
            else:
                print(YELLOW + "Bellekte kayıtlı metin bulunamadı." + RESET)
            input("\nDevam etmek için Enter'a basın...")
            
        elif choice == "3":
            file_path = input("RAM'e yüklenecek dosya yolu: ").strip().strip('"\'')
            if not os.path.exists(file_path):
                print(RED + "[Hata] Dosya bulunamadı." + RESET)
                input("\nDevam etmek için Enter'a basın...")
                continue
                
            valid, real_path, err = validate_file_path(file_path)
            if not valid:
                print(RED + f"[Hata] {err}" + RESET)
                input("\nDevam etmek için Enter'a basın...")
                continue
                
            file_size = os.path.getsize(real_path)
            max_bytes = vault.max_file_size_mb * 1024 * 1024
            if file_size > max_bytes:
                print(RED + f"[Hata] Dosya boyutu belirlenen limiti ({vault.max_file_size_mb} MB) aşıyor." + RESET)
                input("\nDevam etmek için Enter'a basın...")
                continue
                
            filename = os.path.basename(real_path)
            try:
                with open(real_path, 'rb') as f:
                    data = f.read()
                vault.mem_files[filename] = bytearray(data)
                del data
                gc.collect()
                print(GREEN + f"'{filename}' başarıyla RAM belleğe yüklendi." + RESET)
                vault.start_timer(vault.total_time, lambda msg: None)
            except Exception as e:
                print(RED + f"Yükleme hatası: {e}" + RESET)
            input("\nDevam etmek için Enter'a basın...")
            
        elif choice == "4":
            print("\n" + BOLD + "RAM'deki Dosyalar:" + RESET)
            if not vault.mem_files:
                print("  (Kasa Boş)")
            else:
                for fname, data in vault.mem_files.items():
                    print(f"  - {fname} ({len(data)} bayt)")
            input("\nDevam etmek için Enter'a basın...")
            
        elif choice == "5":
            print(YELLOW + "Kasa kazınıyor..." + RESET)
            vault.wipe(print)
            print(GREEN + "Geçici bellek sıfırlandı." + RESET)
            input("\nDevam etmek için Enter'a basın...")
            
        elif choice == "6":
            print("\nKasa Süreleri:")
            print(" 1. 30 Saniye")
            print(" 2. 2 Dakika (Varsayılan)")
            print(" 3. 5 Dakika")
            print(" 4. 10 Dakika")
            dur_choice = input("Seçiminiz [1-4]: ").strip()
            sec = 120
            if dur_choice == "1":
                sec = 30
            elif dur_choice == "3":
                sec = 300
            elif dur_choice == "4":
                sec = 600
            vault.total_time = sec
            print(GREEN + f"Kapanma süresi {sec} saniye olarak ayarlandı." + RESET)
            input("\nDevam etmek için Enter'a basın...")
            
        elif choice == "7":
            print("\nMaksimum Dosya Boyutları:")
            print(" 1. 50 MB")
            print(" 2. 100 MB (Varsayılan)")
            print(" 3. 250 MB")
            print(" 4. 500 MB")
            print(" 5. Limitsiz")
            lim_choice = input("Seçiminiz [1-5]: ").strip()
            mb = 100
            if lim_choice == "1":
                mb = 50
            elif lim_choice == "3":
                mb = 250
            elif lim_choice == "4":
                mb = 500
            elif lim_choice == "5":
                mb = 999999
            vault.max_file_size_mb = mb
            print(GREEN + f"Maksimum dosya limiti {mb if mb != 999999 else 'Limitsiz'} olarak ayarlandı." + RESET)
            input("\nDevam etmek için Enter'a basın...")

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        if vault.active:
            vault.wipe(lambda msg: None)
        print("\n" + YELLOW + "Kasa temizlendi ve çıkış yapıldı." + RESET)
        sys.exit(0)
