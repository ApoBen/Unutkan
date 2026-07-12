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
for path in "$(dirname "$0")/dist/unutkan" "./dist/unutkan" "$HOME/Masaüstü/unutkan/dist/unutkan" "$HOME/Desktop/unutkan/dist/unutkan" "$HOME/unutkan/dist/unutkan"; do
    if [ -f "$path" ]; then
        LOCAL_BINARY="$path"
        break
    fi
done

if [ -n "$LOCAL_BINARY" ]; then
    echo -e "${GREEN}[*] Yerel olarak derlenmiş binary bulundu, kopyalanıyor...${NC}"
    cp "$LOCAL_BINARY" "$BIN_DIR/unutkan"
else
    echo -e "${GREEN}[*] Binary dosyası GitHub Releases üzerinden indiriliyor...${NC}"
    if curl -f -sSL -o "$BIN_DIR/unutkan" "https://github.com/ApoBen/Unutkan/releases/latest/download/unutkan"; then
        echo -e "${GREEN}[✓] İndirme tamamlandı.${NC}"
    else
        if [ -f "dist/unutkan" ]; then
            cp "dist/unutkan" "$BIN_DIR/unutkan"
        else
            echo -e "${RED}[Hata] Binary dosyası indirilemedi ve yerel 'dist/unutkan' dosyası bulunamadı.${NC}"
            exit 1
        fi
    fi
fi

# Çalıştırılabilirlik izni ver
chmod +x "$BIN_DIR/unutkan"
echo -e "${GREEN}[✓] Binary başarıyla yerleştirildi: $BIN_DIR/unutkan${NC}"

# Masaüstü Kısayolu (.desktop) Oluştur
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
echo -e "Uygulamayı çalıştırmak için terminale ${PURPLE}unutkan${NC} yazabilir veya uygulama menüsünden aratabilirsiniz.\n"
