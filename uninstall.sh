#!/usr/bin/env bash

# Unutkan - Linux Kaldırma Betiği
# Bu betik uygulamayı yerel sistemden (~/.local/bin ve masaüstü kısayolu) temizler.

set -e

# Renk tanımlamaları
RED='\033[0;31m'
GREEN='\033[0;32m'
PURPLE='\033[0;35m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${PURPLE}"
echo "  _   _ _   _ _   _ _____ _  __     _     _   _ "
echo " | | | | \ | | | | |_   _| |/ /    / \   | \ | |"
echo " | | | |  \| | | |   | | | ' /    / _ \  |  \| |"
echo " | |_| | |\  | |_|   | | | . \   / ___ \ | |\  |"
echo "  \___/|_| \_|\___/  |_| |_|\_\ /_/   \_\|_| \_|"
echo -e "${NC}"
echo -e "${RED}=== Unutkan - Kaldırma İşlemi Başlatıldı ===${NC}\n"

# Hedef dizinler
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

# GUI Binary dosyasını sil
if [ -f "$BIN_DIR/unutkan" ]; then
    echo -e "${GREEN}[*] GUI binary dosyası kaldırılıyor: $BIN_DIR/unutkan${NC}"
    rm "$BIN_DIR/unutkan"
else
    echo -e "${BLUE}[Bilgi] GUI binary dosyası bulunamadı.${NC}"
fi

# TUI Binary dosyasını sil
if [ -f "$BIN_DIR/unutkantui" ]; then
    echo -e "${GREEN}[*] TUI binary dosyası kaldırılıyor: $BIN_DIR/unutkantui${NC}"
    rm "$BIN_DIR/unutkantui"
    if [ -f "$BIN_DIR/core.py" ]; then
        rm "$BIN_DIR/core.py"
    fi
else
    echo -e "${BLUE}[Bilgi] TUI binary dosyası bulunamadı.${NC}"
fi

# Masaüstü kısayolunu sil
if [ -f "$DESKTOP_DIR/unutkan.desktop" ]; then
    echo -e "${GREEN}[*] Masaüstü kısayolu kaldırılıyor: $DESKTOP_DIR/unutkan.desktop${NC}"
    rm "$DESKTOP_DIR/unutkan.desktop"
else
    echo -e "${BLUE}[Bilgi] Masaüstü kısayolu bulunamadı.${NC}"
fi

echo -e "\n${GREEN}=== Kaldırma İşlemi Başarıyla Tamamlandı! ===${NC}"
echo -e "Unutkan uygulaması sisteminizden temizlendi.\n"
