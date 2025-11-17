#!/bin/bash
# Fast DDS Project - Basitleştirilmiş Build Script

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
IDL_DIR="$PROJECT_ROOT/IDL"

printf "${BLUE}DDS Basit Build - Sadece mevcut _idl_generated dizinlerinde derliyor${NC}\n"

mapfile -t GEN_DIRS < <(find "$IDL_DIR" -maxdepth 1 -type d -name "*_idl_generated" | sort)
if [[ ${#GEN_DIRS[@]} -eq 0 ]]; then
    printf "${RED}Hiçbir _idl_generated dizini bulunamadı!${NC}\n"
    exit 1
fi

for d in "${GEN_DIRS[@]}"; do
    mod=$(basename "$d" | sed 's/_idl_generated$//')
    echo "[INFO] Derleniyor: $mod ($d)"
    cd "$d"
    if [[ -f "CMakeLists.txt" ]]; then
        if [[ ! -d build ]]; then mkdir build; fi
        cd build
        # CMake cache'ini temizle (taşınabilirlik için - eski PC path'leri cache'de kalabilir)
        if [[ -f CMakeCache.txt ]]; then
            echo "[INFO] CMake cache temizleniyor (taşınabilirlik için)..."
            rm -f CMakeCache.txt
            rm -rf CMakeFiles/
        fi
        cmake ..
        if command -v ninja >/dev/null 2>&1 && [[ -f ../build.ninja ]]; then
            ninja
        else
            make
        fi
        echo -e "${GREEN}[OK] Build tamam: $d/build${NC}"
        echo -e "${YELLOW}Bulunan çalıştırılabilirler:${NC}"
        for exe in *; do
            if [[ -x "$exe" && -f "$exe" && ! -d "$exe" ]]; then
                echo "  - $d/build/$exe"
            fi
        done
        cd ..
    else
        echo -e "${YELLOW}CMakeLists.txt yok, atlanıyor: $d${NC}"
        continue
    fi
    cd "$PROJECT_ROOT"
done

echo -e "\n${GREEN}Tüm build işlemleri tamamlandı. Çıktılar ilgili _idl_generated/build dizinlerinde.${NC}\n"