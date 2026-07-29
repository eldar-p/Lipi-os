#!/usr/bin/env bash
# Inner WSL build: sync Windows repo -> Linux /var/tmp, build, copy ISO back to Windows dist\.
# Args: $1=SRC (wsl path to Windows repo)  $2=DST (/var/tmp/...)  $3=TARGET  $4=WINLOG (optional)
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE="${NEEDRESTART_MODE:-a}"

SRC="${1:?SRC path required}"
DST="${2:?DST path required}"
TARGET="${3:?TARGET required}"
WINLOG="${4:-}"

mkdir -p "${SRC}/dist" || true

log() {
  # Always print; also append to Windows log when possible
  echo "$1"
  if [[ -n "${WINLOG}" ]]; then
    mkdir -p "$(dirname "${WINLOG}")" 2>/dev/null || true
    echo "$1" >>"${WINLOG}" 2>/dev/null || true
  fi
}

log "==> Lipi WSL inner build start"
log "    SRC=$SRC"
log "    DST=$DST"
log "    TARGET=$TARGET"

if [[ ! -d "$SRC" ]]; then
  log "[X] SRC does not exist: $SRC"
  exit 1
fi
if [[ ! -f "$SRC/iso/build.sh" ]]; then
  log "[X] Missing $SRC/iso/build.sh — wrong SRC path?"
  exit 1
fi

log "==> Sync $SRC -> $DST"
rm -rf "$DST"
mkdir -p "$DST"

if ! command -v rsync >/dev/null 2>&1; then
  log "==> Installing rsync"
  apt-get update -qq
  apt-get install -y -qq rsync
fi

rsync -a --delete \
  --exclude '.git/' \
  --exclude 'iso/.work/' \
  --exclude 'dist/*.iso' \
  --exclude 'dist/*.iso.sha256' \
  --exclude 'dist/build-windows.log' \
  "$SRC"/ "$DST"/

cd "$DST"
chmod +x iso/auto-build.sh iso/build.sh iso/*.sh 2>/dev/null || true
# Strip CRLF from scripts (Windows zip checkouts)
find iso -type f \( -name '*.sh' -o -name '*.cfg' \) -print0 2>/dev/null \
  | xargs -0 -r sed -i 's/\r$//' || true

log "==> Building ($TARGET) inside Linux FS — then copy ISO to Windows dist\\"
set -o pipefail
if [[ -n "${WINLOG}" ]]; then
  ./iso/auto-build.sh "$TARGET" 2>&1 | tee -a "${WINLOG}"
else
  ./iso/auto-build.sh "$TARGET"
fi

log "==> Copying ISO artifacts to Windows project: $SRC/dist"
mkdir -p "$SRC/dist"
shopt -s nullglob
ISOS=("$DST"/dist/*.iso)
if ((${#ISOS[@]} == 0)); then
  log "[X] No ISO produced under $DST/dist"
  ls -la "$DST/dist" 2>&1 | while read -r line; do log "$line"; done || true
  exit 1
fi

cp -f "$DST"/dist/*.iso "$SRC/dist/"
cp -f "$DST"/dist/*.iso.sha256 "$SRC/dist/" 2>/dev/null || true
sync || true

log "==> Files now in Windows dist:"
ls -lh "$SRC/dist" | while read -r line; do log "$line"; done

# Verify at least one iso is readable from SRC (DrvFs)
ok=0
for f in "$SRC"/dist/*.iso; do
  [[ -f "$f" ]] || continue
  sz=$(stat -c%s "$f" 2>/dev/null || echo 0)
  log "    verified: $f ($sz bytes)"
  ok=1
done
if [[ "$ok" -ne 1 ]]; then
  log "[X] Copy to Windows dist appeared to fail"
  exit 1
fi

log "==> Done. ISO is in the project dist\\ folder on Windows."
exit 0
