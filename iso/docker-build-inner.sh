#!/usr/bin/env bash
# Inner Docker build: sync Windows mount -> /var/tmp, build, copy ISO to /lipi-out (Windows dist).
# Args: $1=TARGET
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE="${NEEDRESTART_MODE:-a}"

TARGET="${1:?TARGET required}"
SRC=/lipi-src
DST=/var/tmp/lipi-os-build
OUT=/lipi-out

echo "==> Sync $SRC -> $DST (Linux FS inside container)"
rm -rf "$DST"
mkdir -p "$DST" "$OUT"

if ! command -v rsync >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq rsync
fi

rsync -a --delete \
  --exclude '.git/' \
  --exclude 'iso/.work/' \
  --exclude 'dist/*.iso' \
  --exclude 'dist/*.iso.sha256' \
  "$SRC"/ "$DST"/

cd "$DST"
chmod +x iso/auto-build.sh iso/build.sh iso/*.sh 2>/dev/null || true
find iso -type f -name '*.sh' -print0 | xargs -0 -r sed -i 's/\r$//' || true

echo "==> Building ($TARGET)"
./iso/auto-build.sh "$TARGET"

echo "==> Copy ISO to Windows project mount $OUT"
shopt -s nullglob
ISOS=("$DST"/dist/*.iso)
if ((${#ISOS[@]} == 0)); then
  echo "[X] No ISO produced"
  ls -la "$DST/dist" || true
  exit 1
fi
cp -f "$DST"/dist/*.iso "$OUT"/
cp -f "$DST"/dist/*.iso.sha256 "$OUT"/ 2>/dev/null || true
ls -lh "$OUT"
echo "==> Done"
