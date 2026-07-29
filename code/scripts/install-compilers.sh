#!/usr/bin/env bash
# Install programming toolchains for Lipi OS Compiler Hub.
# Usage:
#   sudo ./code/scripts/install-compilers.sh           # full set
#   sudo ./code/scripts/install-compilers.sh --minimal # smaller set (server)
#   sudo ./code/scripts/install-compilers.sh --list    # show packages only
set -euo pipefail

PROFILE="full"
LIST_ONLY=0
for arg in "$@"; do
  case "$arg" in
    --minimal|-m|server) PROFILE="minimal" ;;
    --full|-f|desktop) PROFILE="full" ;;
    --list) LIST_ONLY=1 ;;
    -h|--help)
      echo "Usage: sudo $0 [--full|--minimal] [--list]"
      exit 0
      ;;
  esac
done

export DEBIAN_FRONTEND=noninteractive
export NEEDRESTART_MODE="${NEEDRESTART_MODE:-a}"

log() { printf '==> %s\n' "$*"; }

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo $0 $*"
  exit 1
fi

MINIMAL_PKGS=(
  build-essential
  binutils
  nasm
  make
  pkg-config
  openjdk-17-jdk-headless
  golang-go
  nodejs
  npm
  python3
)

FULL_PKGS=(
  "${MINIMAL_PKGS[@]}"
  gdb
  clang
  rustc
  cargo
  lua5.4
  ruby
  php-cli
  perl
  gfortran
  openjdk-17-jdk
)

if [[ "${PROFILE}" == "full" ]]; then
  PKGS=("${FULL_PKGS[@]}")
else
  PKGS=("${MINIMAL_PKGS[@]}")
fi

OPTIONAL_PKGS=(
  kotlin
  zig
  typescript
  deno
)

log "Profile: ${PROFILE}"
log "Packages: ${PKGS[*]}"

if [[ "${LIST_ONLY}" -eq 1 ]]; then
  printf '%s\n' "${PKGS[@]}"
  exit 0
fi

log "apt-get update…"
apt-get update -qq

log "Installing compilers…"
apt-get install -y -qq "${PKGS[@]}" || {
  log "Batch install had issues — retrying packages individually"
  for p in "${PKGS[@]}"; do
    apt-get install -y -qq "$p" || log "skip/fail: $p"
  done
}

for p in "${OPTIONAL_PKGS[@]}"; do
  if apt-cache show "$p" >/dev/null 2>&1; then
    apt-get install -y -qq "$p" && log "optional ok: $p" || true
  fi
done

if command -v npm >/dev/null 2>&1; then
  log "Installing typescript + ts-node via npm (global)…"
  npm install -g typescript ts-node >/dev/null 2>&1 || log "npm global install skipped/failed"
fi

if command -v lua5.4 >/dev/null 2>&1 && ! command -v lua >/dev/null 2>&1; then
  ln -sf "$(command -v lua5.4)" /usr/local/bin/lua || true
fi

log "Done. Toolchain check:"
for t in gcc g++ clang nasm javac java rustc cargo go node npm tsc ts-node lua ruby php perl python3 gfortran; do
  if command -v "$t" >/dev/null 2>&1; then
    printf '  [OK] %s -> %s\n' "$t" "$(command -v "$t")"
  else
    printf '  [..] %s\n' "$t"
  fi
done

log "In Lipi shell run:  langs"
