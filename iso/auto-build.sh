#!/usr/bin/env bash
# Auto-prepare host deps and build Lipi OS ISO(s).
# Intended for Windows (WSL root / Docker) one-click builds.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

TARGET="${1:-all}"
export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE="${NEEDRESTART_MODE:-a}"

log() { printf '\n==> %s\n' "$*"; }

if [[ "${EUID}" -ne 0 ]]; then
  if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
    exec sudo -E "$0" "$@"
  fi
  echo "Need root. On WSL use: wsl -u root ..."
  echo "Or: sudo $0 $*"
  exit 1
fi

log "Lipi OS auto-build — target=${TARGET}"
log "Repo: ${ROOT_DIR}"

# Avoid interactive apt/dpkg prompts
mkdir -p /etc/needrestart/conf.d 2>/dev/null || true
echo "\$nrconf{restart} = 'a';" >/etc/needrestart/conf.d/99lipi.conf 2>/dev/null || true

log "Updating package indexes…"
apt-get update -qq

PKGS=(
  debootstrap
  squashfs-tools
  xorriso
  grub-pc-bin
  grub-efi-amd64-bin
  mtools
  dosfstools
  rsync
  ca-certificates
  wget
  curl
)

log "Installing build dependencies (auto)…"
apt-get install -y -qq "${PKGS[@]}"

chmod +x "${ROOT_DIR}/iso/build.sh"
log "Starting iso/build.sh ${TARGET}"
exec "${ROOT_DIR}/iso/build.sh" "${TARGET}"
