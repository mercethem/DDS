#!/bin/bash

# Get script directory and navigate to project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/../.."

# Verify and display the new working directory (Project Root)
echo "Proje Koku olarak ayarlandi: $(pwd)"
echo

echo "Calistiriliyor: json_patcher.py..."

# Run the Python script with relative path from project root
python3 scripts/py/json_patcher.py

echo
echo "Islem tamamlandi. Kapatmak icin bir tusa basin..."
read -p "Press Enter to continue..."

exit 0