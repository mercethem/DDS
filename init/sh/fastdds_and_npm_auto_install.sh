#!/bin/bash
set -e

# İndirme URL'si
URL="https://www.eprosima.com/component/ars/item/eProsima_Fast-DDS-v3.2.2-Linux.tgz?format=tgz&category_id=7&release_id=188&Itemid=0"

DOWNLOAD_DIR="$HOME/Downloads"
FILE_NAME="Fast-DDS-v3.2.2-Linux.tgz"

echo ">>> Dosya indiriliyor..."
wget -O "$DOWNLOAD_DIR/$FILE_NAME" "$URL"
echo ">>> İndirme tamamlandı."

cd "$DOWNLOAD_DIR"

# Arşiv adından klasör adı oluştur
BASE_NAME=$(basename "$FILE_NAME" .tgz)

echo ">>> Arşiv şu klasöre açılıyor: $BASE_NAME"
mkdir -p "$BASE_NAME"

# Arşivi çıkar
tar -xvf "$FILE_NAME" -C "$BASE_NAME" --strip-components=1
echo ">>> Arşiv çıkarıldı: $BASE_NAME"

# HOME içine taşı
echo ">>> Klasör HOME dizinine taşınıyor..."
mv "$BASE_NAME" "$HOME/"

TARGET_DIR="$HOME/$BASE_NAME"
echo ">>> Hedef klasör: $TARGET_DIR"

# install.sh dosyasını bul
INSTALL_SCRIPT=$(find "$TARGET_DIR" -maxdepth 2 -name "install.sh" | head -n 1)

if [ -z "$INSTALL_SCRIPT" ]; then
    echo "!!! install.sh bulunamadı!"
    exit 1
fi

echo ">>> install.sh bulundu: $INSTALL_SCRIPT"

# install.sh çalıştırılabilir yap
chmod +x "$INSTALL_SCRIPT"

echo ">>> install.sh sudo ile çalıştırılıyor..."
cd "$(dirname "$INSTALL_SCRIPT")"

sudo ./install.sh

echo ">>> Kurulum başarıyla tamamlandı!"
echo ">>> Kurulum dizini: $TARGET_DIR"

