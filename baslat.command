#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  ASANSÖR AVAN HESAPLAMA PROGRAMI  —  macOS başlatıcı
#  Çift tıklayarak çalıştırın.
# ═══════════════════════════════════════════════════════════════
cd "$(dirname "$0")" || exit 1

echo ""
echo "══════════════════════════════════════════════════════════════"
echo "   ASANSÖR AVAN HESAPLAMA PROGRAMI"
echo "══════════════════════════════════════════════════════════════"
echo ""

PY=""
for c in python3 python3.12 python3.11 python3.10 /usr/bin/python3; do
  if command -v "$c" >/dev/null 2>&1; then PY="$c"; break; fi
done
if [ -z "$PY" ]; then
  echo "  Python bulunamadı."
  echo "  https://www.python.org/downloads/ adresinden Python 3 kurup"
  echo "  bu dosyayı yeniden çift tıklayın."
  echo ""; read -r -p "  Kapatmak için Enter..."; exit 1
fi

if [ ! -d ".venv" ]; then
  echo "  İlk kurulum yapılıyor (yalnız bir kez, ~1 dakika)…"
  "$PY" -m venv .venv || { echo "  Sanal ortam oluşturulamadı."; read -r -p "  Enter..."; exit 1; }
  ./.venv/bin/python -m pip install --upgrade pip -q
  ./.venv/bin/python -m pip install -r requirements.txt -q || {
    echo "  Kurulum başarısız — internet bağlantınızı kontrol edin."
    read -r -p "  Enter..."; exit 1; }
  echo "  Kurulum tamamlandı."
  echo ""
fi

./.venv/bin/python main.py
echo ""
read -r -p "  Program kapandı. Pencereyi kapatmak için Enter..."
