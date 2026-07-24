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

import core

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

# Wrapper functions for core logic
def validate_file_path(path):
    return core.validate_file_path(path)

def extract_file_metadata(file_path):
    return core.extract_file_metadata(file_path)

def clean_file(file_path, overwrite, randomize):
    return core.clean_file(file_path, overwrite, randomize)

def shred_file(file_path, method_index, progress_callback=None):
    return core.shred_file(file_path, method_index, progress_callback)

def sanitize_text(text, settings):
    return core.sanitize_text(text, settings)

# Main RAM Vault instance
vault = core.RamVault()

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
