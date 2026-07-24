# -*- coding: utf-8 -*-
"""
Unutkan Core Module
Çevrimdışı Veri Mahremiyeti ve Dijital Hijyen Çekirdek Mantığı
"""

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

# Optional non-GUI dependencies
try:
    from PIL import Image, ExifTags
except ImportError:
    Image = None
    ExifTags = None

try:
    from pypdf import PdfReader, PdfWriter
except ImportError:
    PdfReader, PdfWriter = None, None

try:
    import mutagen
except ImportError:
    mutagen = None


def validate_file_path(path):
    """
    Validate that a path is a regular file, not a symlink, device, or directory.
    Returns (is_valid: bool, real_path: str, error_message: str)
    """
    if not path or not isinstance(path, str):
        return False, "", "Geçersiz dosya yolu."
    
    real_path = os.path.realpath(path)
    if os.path.islink(path):
        return False, real_path, "Sembolik linkler güvenlik nedeniyle kabul edilmiyor."
    if not os.path.isfile(real_path):
        return False, real_path, "Yol bir dosyaya işaret etmiyor (dizin, cihaz veya pipe olabilir)."
    return True, real_path, ""


def extract_file_metadata(file_path):
    """
    Extract metadata key-value dictionary from image, PDF, Office, ODF, and audio files.
    """
    valid, real_path, err = validate_file_path(file_path)
    if not valid:
        return {"Hata": err}

    ext = os.path.splitext(real_path)[1].lower()
    metadata = {}

    try:
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            if Image is None:
                return {"Hata": "Pillow kütüphanesi yüklü değil."}
            with Image.open(real_path) as img:
                exif = img.getexif()
                if exif:
                    for tag_id in exif:
                        tag = ExifTags.TAGS.get(tag_id, tag_id) if ExifTags else tag_id
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
            reader = PdfReader(real_path)
            meta = reader.metadata
            if meta:
                for k, v in meta.items():
                    key = k[1:] if k.startswith('/') else k
                    metadata[f"PDF: {key}"] = str(v)

        elif ext in ['.docx', '.xlsx', '.pptx']:
            with zipfile.ZipFile(real_path, 'r') as z:
                if 'docProps/core.xml' in z.namelist():
                    xml_content = z.read('docProps/core.xml').decode('utf-8', errors='replace')
                    tags = ['title', 'creator', 'lastModifiedBy', 'revision', 'created', 'modified']
                    for tag in tags:
                        pattern = re.compile(
                            r'<dcterms:{0}[^>]*>(.*?)</dcterms:{0}>|<cp:{0}[^>]*>(.*?)</cp:{0}>|<dc:{0}[^>]*>(.*?)</dc:{0}>'.format(tag)
                        )
                        match = pattern.search(xml_content)
                        if match:
                            val = next(group for group in match.groups() if group is not None)
                            metadata[f"Office: {tag}"] = val

        elif ext in ['.odt', '.ods', '.odp']:
            with zipfile.ZipFile(real_path, 'r') as z:
                if 'meta.xml' in z.namelist():
                    xml_content = z.read('meta.xml').decode('utf-8', errors='replace')
                    tags = ['title', 'creator', 'creation-date', 'date', 'generator', 'editing-duration']
                    for tag in tags:
                        pattern = re.compile(
                            r'<dc:{0}[^>]*>(.*?)</dc:{0}>|<meta:{0}[^>]*>(.*?)</meta:{0}>'.format(tag)
                        )
                        match = pattern.search(xml_content)
                        if match:
                            val = next(group for group in match.groups() if group is not None)
                            metadata[f"ODF: {tag}"] = val

        elif ext in ['.mp3', '.flac', '.ogg', '.m4a']:
            if mutagen is None:
                return {"Hata": "mutagen kütüphanesi yüklü değil."}
            audio = mutagen.File(real_path)
            if audio:
                for k, v in audio.items():
                    metadata[f"Ses: {k}"] = str(v)

    except Exception as e:
        metadata["Hata"] = f"Metadata okunamadı: {str(e)}"

    return metadata


def _clean_image_metadata(input_path, output_path, ext_lower):
    if Image is None:
        raise RuntimeError("Pillow kütüphanesi yüklü değil.")
    with Image.open(input_path) as img:
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            clean_img = img.copy()
        else:
            clean_img = Image.new(img.mode, img.size)
            clean_img.putdata(img.getdata())

        clean_img.info = {}

        if ext_lower in ['.jpg', '.jpeg']:
            clean_img.save(output_path, format='JPEG', exif=b"", quality=95)
        elif ext_lower == '.png':
            clean_img.save(output_path, format='PNG', pnginfo=None)
        elif ext_lower == '.webp':
            clean_img.save(output_path, format='WEBP', exif=b"", quality=90)
        else:
            clean_img.save(output_path)


def _clean_pdf_metadata(input_path, output_path):
    if PdfReader is None or PdfWriter is None:
        raise RuntimeError("pypdf kütüphanesi yüklü değil.")
    reader = PdfReader(input_path)
    writer = PdfWriter()

    for page in reader.pages:
        writer.add_page(page)

    writer.add_metadata({
        "/Producer": "",
        "/Creator": "",
        "/Author": "",
        "/Title": "",
        "/Subject": "",
        "/Keywords": "",
        "/CreationDate": "",
        "/ModDate": ""
    })

    # Clear XMP metadata object if present
    if "/Metadata" in writer._root_object:
        del writer._root_object["/Metadata"]

    with open(output_path, 'wb') as f:
        writer.write(f)


def _clean_office_metadata(input_path, output_path):
    blank_core = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
        'xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\n'
        '</cp:coreProperties>'
    )
    blank_app = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
        '<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">\n'
        '</Properties>'
    )

    with zipfile.ZipFile(input_path, 'r') as yin:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as yout:
            for item in yin.infolist():
                if item.filename == 'docProps/core.xml':
                    yout.writestr(item.filename, blank_core)
                elif item.filename == 'docProps/app.xml':
                    yout.writestr(item.filename, blank_app)
                elif item.filename == 'docProps/custom.xml':
                    continue
                else:
                    yout.writestr(item, yin.read(item.filename))


def _clean_opendocument_metadata(input_path, output_path):
    blank_meta = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<office:document-meta xmlns:office="urn:oasis:names:tc:opendocument:xmlns:office:1.0" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:dc="http://purl.org/dc/elements/1.1/" '
        'xmlns:meta="urn:oasis:names:tc:opendocument:xmlns:meta:1.0" office:version="1.3">\n'
        '  <office:meta>\n'
        '  </office:meta>\n'
        '</office:document-meta>'
    )

    with zipfile.ZipFile(input_path, 'r') as yin:
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as yout:
            for item in yin.infolist():
                if item.filename == 'Thumbnails/thumbnail.png':
                    continue
                if item.filename == 'meta.xml':
                    yout.writestr(item.filename, blank_meta)
                else:
                    yout.writestr(item, yin.read(item.filename))


def _clean_audio_metadata(input_path, output_path):
    if mutagen is None:
        raise RuntimeError("mutagen kütüphanesi yüklü değil.")
    shutil.copyfile(input_path, output_path)
    audio = mutagen.File(output_path)
    if audio is not None:
        audio.delete()
        audio.save()


def clean_file(file_path, overwrite=True, randomize=False):
    """
    Clean metadata from supported file formats.
    Returns (success: bool, output_path: str, error_message: str)
    """
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

        if ext_lower in ['.jpg', '.jpeg', '.webp', '.png']:
            _clean_image_metadata(file_path, temp_path, ext_lower)
        elif ext_lower == '.pdf':
            _clean_pdf_metadata(file_path, temp_path)
        elif ext_lower in ['.docx', '.xlsx', '.pptx']:
            _clean_office_metadata(file_path, temp_path)
        elif ext_lower in ['.odt', '.ods', '.odp']:
            _clean_opendocument_metadata(file_path, temp_path)
        elif ext_lower in ['.mp3', '.flac', '.ogg', '.m4a']:
            _clean_audio_metadata(file_path, temp_path)
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


def shred_file(file_path, method_index=1, progress_callback=None):
    """
    Securely overwrite and shred a file from disk.
    method_index: 0 (1-pass zeros), 1 (3-pass random+zero), 2 (7-pass multi-pattern)
    Returns (success: bool, error_message: str)
    """
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

        # Open with O_NOFOLLOW to mitigate symlink race conditions
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


def _clean_url(url_str):
    try:
        trail = ""
        while url_str and url_str[-1] in ['.', ',', ';', '?', '!', ':', ')', '}', ']']:
            trail = url_str[-1] + trail
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
    result = text
    google_key_pattern = re.compile(r'AIzaSy[0-9A-Za-z-_]{30,40}')
    result = google_key_pattern.sub("[GOOGLE_API_KEY_SECRET]", result)

    aws_key_pattern = re.compile(r'AKIA[0-9A-Z]{16}')
    result = aws_key_pattern.sub("[AWS_API_KEY_SECRET]", result)

    generic_secret_pattern = re.compile(r'(?i)(bearer\s+|token\s*[:=]\s*|key\s*[:=]\s*)[a-zA-Z0-9_\-\.]{12,}')
    result = generic_secret_pattern.sub(lambda m: f"{m.group(1)}[SECRET_TOKEN]", result)

    return result


def sanitize_text(text, settings=None):
    """
    Sanitize input text according to settings dict:
    - 'urls': bool (default True)
    - 'emails': bool (default True)
    - 'phones': bool (default True)
    - 'secrets': bool (default True)
    """
    if not text:
        return ""

    if settings is None:
        settings = {'urls': True, 'emails': True, 'phones': True, 'secrets': True}

    result = text

    if settings.get('secrets', True):
        result = _mask_secrets(result)

    if settings.get('urls', True):
        url_pattern = re.compile(r'https?://[^\s\)\}\]\"\'>]+')
        result = url_pattern.sub(lambda m: _clean_url(m.group(0)), result)

    if settings.get('emails', True):
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b')
        result = email_pattern.sub(lambda m: _mask_email(m.group(0)), result)

    if settings.get('phones', True):
        phone_pattern = re.compile(
            r'\b(?:\+?90[-.\s]?)?0?[5-9]\d{2}[-.\s]?\d{3}[-.\s]?\d{2}[-.\s]?\d{2}\b|\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
        )
        result = phone_pattern.sub(lambda m: _mask_phone(m.group(0)), result)

    return result


class RamVault:
    """
    RAM Vault manager for holding sensitive text & files in-memory only.
    Uses memoryview zero-overwriting for secure wiping.
    """
    def __init__(self):
        self.mem_text = None
        self.mem_files = {}
        self.time_left = 0
        self.total_time = 120
        self.max_file_size_mb = 100
        self.timer_thread = None
        self.lock = threading.Lock()
        self.active = False

    def start_timer(self, duration_sec, log_callback=None):
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
                    if log_callback:
                        log_callback("[!] ZAMAN AŞIMI: Bellek kilitlendi ve veriler kazındı.")
                    break

    def wipe(self, log_callback=None):
        with self.lock:
            self.active = False
            self._wipe_internal(log_callback)

    def _wipe_internal(self, log_callback=None):
        if self.mem_text:
            try:
                mv = memoryview(self.mem_text)
                block_size = 1024 * 1024
                zero_block = b'\x00' * block_size
                length = len(self.mem_text)
                for offset in range(0, length, block_size):
                    chunk = min(block_size, length - offset)
                    mv[offset:offset+chunk] = zero_block[:chunk]
                if log_callback:
                    log_callback("[Güvenli] Metin bellek bölgesi güvenli şekilde kazındı.")
            except Exception as e:
                if log_callback:
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
                    if log_callback:
                        log_callback(f"[Güvenli] '{filename}' dosya tamponu güvenli şekilde kazındı.")
                except Exception as e:
                    if log_callback:
                        log_callback(f"[UYARI] '{filename}' bellek kazıma başarısız: {e}")
            self.mem_files.clear()

        gc.collect()
