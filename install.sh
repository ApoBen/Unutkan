#!/usr/bin/env bash

# Unutkan - Linux Kurulum Betiği
# Bu betik uygulamayı yerel sisteme (~/.local/bin) kurar ve masaüstü kısayolu oluşturur.

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
echo -e "${BLUE}=== Unutkan - Güvenli Metadata Temizleyici Kurulumu ===${NC}\n"

# Hedef dizinler
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"

# Dizinlerin varlığını kontrol et, yoksa oluştur
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"

# Geliştirme/Yerel test kontrolü
# Eğer derlenmiş binary dist klasöründe varsa yerel kopyalama yap, yoksa indir.
LOCAL_BINARY=""
LOCAL_TUI_BINARY=""

for path in "$(dirname "$0")/dist/unutkan" "./dist/unutkan" "$HOME/Masaüstü/unutkan/dist/unutkan" "$HOME/Desktop/unutkan/dist/unutkan" "$HOME/unutkan/dist/unutkan"; do
    if [ -f "$path" ]; then
        LOCAL_BINARY="$path"
        break
    fi
done

for path in "$(dirname "$0")/dist/unutkantui" "./dist/unutkantui" "$HOME/Masaüstü/unutkan/dist/unutkantui" "$HOME/Desktop/unutkan/dist/unutkantui" "$HOME/unutkan/dist/unutkantui"; do
    if [ -f "$path" ]; then
        LOCAL_TUI_BINARY="$path"
        break
    fi
done

# GUI Kurulumu
if [ -n "$LOCAL_BINARY" ]; then
    echo -e "${GREEN}[*] Yerel olarak derlenmiş GUI binary bulundu, kopyalanıyor...${NC}"
    cp "$LOCAL_BINARY" "$BIN_DIR/unutkan"
else
    echo -e "${GREEN}[*] GUI binary dosyası GitHub Releases üzerinden indiriliyor...${NC}"
    if curl -f -sSL -o "$BIN_DIR/unutkan" "https://github.com/ApoBen/Unutkan/releases/latest/download/unutkan"; then
        echo -e "${GREEN}[✓] GUI indirme tamamlandı.${NC}"
    else
        if [ -f "dist/unutkan" ]; then
            cp "dist/unutkan" "$BIN_DIR/unutkan"
        else
            echo -e "${RED}[Hata] GUI dosyası indirilemedi ve yerel 'dist/unutkan' bulunamadı.${NC}"
            exit 1
        fi
    fi
fi

# TUI Kurulumu
if [ -n "$LOCAL_TUI_BINARY" ]; then
    echo -e "${GREEN}[*] Yerel olarak derlenmiş TUI binary bulundu, kopyalanıyor...${NC}"
    cp "$LOCAL_TUI_BINARY" "$BIN_DIR/unutkantui"
else
    echo -e "${GREEN}[*] TUI binary dosyası GitHub Releases üzerinden indiriliyor...${NC}"
    if curl -f -sSL -o "$BIN_DIR/unutkantui" "https://github.com/ApoBen/Unutkan/releases/latest/download/unutkantui"; then
        echo -e "${GREEN}[✓] TUI indirme tamamlandı.${NC}"
    else
        if [ -f "dist/unutkantui" ]; then
            cp "dist/unutkantui" "$BIN_DIR/unutkantui"
        else
            # Try running with python interpreter directly if binary is missing as fallback
            if [ -f "tui.py" ]; then
                echo -e "${GREEN}[*] Python TUI kaynak kodu yerel olarak kopyalanıyor...${NC}"
                cp "tui.py" "$BIN_DIR/unutkantui"
            else
                echo -e "${RED}[Hata] TUI dosyası indirilemedi ve yerel kaynaklar bulunamadı.${NC}"
                exit 1
            fi
        fi
    fi
fi

# Uninstall Betiği Kurulumu
if [ -f "$(dirname "$0")/uninstall.sh" ]; then
    echo -e "${GREEN}[*] Yerel uninstall betiği kopyalanıyor...${NC}"
    cp "$(dirname "$0")/uninstall.sh" "$BIN_DIR/unutkan-uninstall"
elif [ -f "uninstall.sh" ]; then
    echo -e "${GREEN}[*] Yerel uninstall betiği kopyalanıyor...${NC}"
    cp "uninstall.sh" "$BIN_DIR/unutkan-uninstall"
else
    echo -e "${GREEN}[*] Uninstall betiği GitHub üzerinden indiriliyor...${NC}"
    if curl -f -sSL -o "$BIN_DIR/unutkan-uninstall" "https://raw.githubusercontent.com/ApoBen/Unutkan/main/uninstall.sh"; then
        echo -e "${GREEN}[✓] Uninstall betiği indirme tamamlandı.${NC}"
    else
        echo -e "${RED}[Hata] Uninstall betiği indirilemedi.${NC}"
    fi
fi

# Çalıştırılabilirlik izinleri ver
chmod +x "$BIN_DIR/unutkan"
chmod +x "$BIN_DIR/unutkantui"
chmod +x "$BIN_DIR/unutkan-uninstall"
echo -e "${GREEN}[✓] Çalıştırılabilir dosyalar başarıyla yerleştirildi:${NC}"
echo -e "    - GUI: $BIN_DIR/unutkan"
echo -e "    - TUI: $BIN_DIR/unutkantui"
echo -e "    - Uninstall: $BIN_DIR/unutkan-uninstall"

# Masaüstü Kısayolu (.desktop) Oluştur (Sadece GUI için)
DESKTOP_FILE="$DESKTOP_DIR/unutkan.desktop"
echo -e "${GREEN}[*] Masaüstü kısayolu oluşturuluyor...${NC}"

cat <<EOF > "$DESKTOP_FILE"
[Desktop Entry]
Type=Application
Name=Unutkan
Comment=Güvenli Metadata Temizleyici
Exec=$BIN_DIR/unutkan
Icon=security-high
Terminal=false
Categories=Utility;Security;
Keywords=privacy;metadata;cleaner;exif;forget;
EOF

chmod +x "$DESKTOP_FILE"
echo -e "${GREEN}[✓] Masaüstü kısayolu başarıyla oluşturuldu: $DESKTOP_FILE${NC}"

# PATH Kontrolü
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo -e "${BLUE}[Bilgi] $BIN_DIR dizini sistem PATH değişkeninizde bulunmuyor.${NC}"
    echo -e "${BLUE}[Bilgi] Bu dizini .bashrc veya .zshrc dosyanıza eklemeniz önerilir:${NC}"
    echo -e "        export PATH=\"\$HOME/.local/bin:\$PATH\""
fi

echo -e "\n${GREEN}=== Kurulum Başarıyla Tamamlandı! ===${NC}"
echo -e "GUI arayüzü için: ${PURPLE}unutkan${NC}"
echo -e "TUI (Terminal) arayüzü için: ${PURPLE}unutkantui${NC}"
echo -e "Uygulamayı kaldırmak için: ${PURPLE}unutkan-uninstall${NC} yazabilirsiniz.\n"
