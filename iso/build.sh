#!/usr/bin/env bash
# Build Lipi OS Live ISOs: desktop (full) and/or server (minimal).
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_DIR="${ROOT_DIR}/iso"
DIST_DIR="${ROOT_DIR}/dist"
OVERLAY_DIR="${ISO_DIR}/overlay"
OVERLAY_SERVER_DIR="${ISO_DIR}/overlay-server"

CODENAME="${CODENAME:-noble}"
ARCH="${ARCH:-amd64}"
MIRROR="${MIRROR:-http://archive.ubuntu.com/ubuntu}"

VARIANT="${VARIANT:-desktop}"
WORK_DIR="${ISO_DIR}/.work/${VARIANT}"
CHROOT_DIR="${WORK_DIR}/chroot"
IMAGE_DIR="${WORK_DIR}/image"
CACHE_DIR="${ISO_DIR}/.work/cache"

need_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Run as root: sudo ./iso/build.sh [desktop|server|all|clean]"
    exit 1
  fi
}

log() {
  printf '\n==> [%s] %s\n' "${VARIANT}" "$*"
}

cleanup_mounts_at() {
  local root="${1:-}"
  [[ -n "${root}" && -d "${root}" ]] || return 0
  umount -lf "${root}/dev/pts" 2>/dev/null || true
  umount -lf "${root}/dev" 2>/dev/null || true
  umount -lf "${root}/proc" 2>/dev/null || true
  umount -lf "${root}/sys" 2>/dev/null || true
  umount -lf "${root}/run" 2>/dev/null || true
}

cleanup_mounts() {
  cleanup_mounts_at "${CHROOT_DIR}"
}

cleanup_all_work_mounts() {
  local d
  for d in "${ISO_DIR}/.work/desktop/chroot" "${ISO_DIR}/.work/server/chroot"; do
    cleanup_mounts_at "${d}"
  done
}

trap cleanup_mounts EXIT

set_variant() {
  VARIANT="$1"
  WORK_DIR="${ISO_DIR}/.work/${VARIANT}"
  CHROOT_DIR="${WORK_DIR}/chroot"
  IMAGE_DIR="${WORK_DIR}/image"
  case "${VARIANT}" in
    desktop)
      ISO_NAME="${ISO_NAME_DESKTOP:-lipi-os-live.iso}"
      ISO_LABEL="${ISO_LABEL_DESKTOP:-LIPIOS}"
      ;;
    server)
      ISO_NAME="${ISO_NAME_SERVER:-lipi-os-server.iso}"
      ISO_LABEL="${ISO_LABEL_SERVER:-LIPISRV}"
      ;;
    *)
      echo "Unknown variant: ${VARIANT}"
      exit 1
      ;;
  esac
}

install_host_deps() {
  log "Checking host packages"
  local pkgs=(debootstrap squashfs-tools xorriso grub-pc-bin grub-efi-amd64-bin mtools dosfstools rsync ca-certificates)
  local missing=()
  for p in "${pkgs[@]}"; do
    if ! dpkg -s "$p" >/dev/null 2>&1; then
      missing+=("$p")
    fi
  done
  if ((${#missing[@]})); then
    apt-get update -qq
    DEBIAN_FRONTEND=noninteractive apt-get install -y -qq "${missing[@]}"
  fi
}

bootstrap_rootfs() {
  log "Bootstrapping base (${CODENAME}/${ARCH})"
  mkdir -p "${CACHE_DIR}" "${CHROOT_DIR}"
  if [[ ! -d "${CHROOT_DIR}/bin" ]]; then
    debootstrap --arch="${ARCH}" --variant=minbase \
      --cache-dir="${CACHE_DIR}" \
      "${CODENAME}" "${CHROOT_DIR}" "${MIRROR}"
  else
    log "Reusing existing chroot at ${CHROOT_DIR}"
  fi
}

configure_rootfs_desktop() {
  log "Installing desktop packages (full)"
  chroot "${CHROOT_DIR}" /bin/bash -euo pipefail <<'CHROOT'
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq \
  linux-image-generic \
  live-boot \
  live-boot-initramfs-tools \
  systemd-sysv \
  initramfs-tools \
  busybox-static \
  sudo \
  locales \
  ca-certificates \
  python3 \
  python3-tk \
  python3-pip \
  python3-psutil \
  python3-requests \
  nano \
  less \
  pciutils \
  usbutils \
  iproute2 \
  iputils-ping \
  net-tools \
  isc-dhcp-client \
  systemd-resolved \
  kmod

sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen || true
sed -i 's/^# *ru_RU.UTF-8/ru_RU.UTF-8/' /etc/locale.gen || true
locale-gen
update-locale LANG=en_US.UTF-8
# Live console: empty root password (local TTY only). Prefer setting a password after boot.
passwd -d root
systemctl enable systemd-networkd.service || true
systemctl enable systemd-resolved.service || true
ln -sfn /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf 2>/dev/null || true
update-initramfs -u
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
CHROOT
}

configure_rootfs_server() {
  log "Installing server packages (minimal, no GUI)"
  chroot "${CHROOT_DIR}" /bin/bash -euo pipefail <<'CHROOT'
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq

# Prefer smaller virtual kernel; fall back to generic if missing
if apt-cache show linux-image-virtual >/dev/null 2>&1; then
  KERNEL_PKG=linux-image-virtual
else
  KERNEL_PKG=linux-image-generic
fi

apt-get install -y -qq \
  "$KERNEL_PKG" \
  live-boot \
  live-boot-initramfs-tools \
  systemd-sysv \
  initramfs-tools \
  busybox-static \
  sudo \
  locales \
  ca-certificates \
  python3 \
  python3-psutil \
  python3-requests \
  nano \
  iproute2 \
  iputils-ping \
  isc-dhcp-client \
  systemd-resolved \
  openssh-server \
  kmod

# Drop GUI / heavy leftovers if somehow present
apt-get purge -y -qq python3-tk python3-pip x11-common 2>/dev/null || true
apt-get autoremove -y -qq 2>/dev/null || true

sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen || true
sed -i 's/^# *ru_RU.UTF-8/ru_RU.UTF-8/' /etc/locale.gen || true
locale-gen
update-locale LANG=C.UTF-8
# Live password (lab): root / lipi — change after first boot
echo 'root:lipi' | chpasswd
passwd -u root 2>/dev/null || true

systemctl enable ssh.service || systemctl enable sshd.service || true
systemctl enable systemd-networkd.service || true
systemctl enable systemd-resolved.service || true
ln -sfn /run/systemd/resolve/stub-resolv.conf /etc/resolv.conf 2>/dev/null || true

# SSH: password login allowed, but NOT empty passwords
if [[ -f /etc/ssh/sshd_config ]]; then
  sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin yes/' /etc/ssh/sshd_config
  sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
  sed -i 's/^#\?PermitEmptyPasswords.*/PermitEmptyPasswords no/' /etc/ssh/sshd_config
fi

# Do not ship host private keys in the ISO — regenerated on first boot
rm -f /etc/ssh/ssh_host_* 2>/dev/null || true

update-initramfs -u
apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* \
  /usr/share/doc/* /usr/share/man/* /usr/share/info/* \
  /usr/share/locale/*/LC_MESSAGES/*.mo 2>/dev/null || true
# Keep en_US / C locales usable
find /usr/share/locale -mindepth 1 -maxdepth 1 ! -name 'en*' ! -name 'ru*' ! -name 'locale.alias' -exec rm -rf {} + 2>/dev/null || true
CHROOT
}

prepare_apt() {
  mkdir -p "${CHROOT_DIR}/etc/apt/apt.conf.d"
  cat >"${CHROOT_DIR}/etc/apt/apt.conf.d/99norecommends" <<'EOF'
APT::Install-Recommends "false";
APT::Install-Suggests "false";
EOF
  cat >"${CHROOT_DIR}/etc/apt/sources.list" <<EOF
deb ${MIRROR} ${CODENAME} main universe
deb ${MIRROR} ${CODENAME}-updates main universe
deb ${MIRROR} ${CODENAME}-security main universe
EOF

  mount --bind /dev "${CHROOT_DIR}/dev"
  mount --bind /dev/pts "${CHROOT_DIR}/dev/pts"
  mount -t proc proc "${CHROOT_DIR}/proc"
  mount -t sysfs sysfs "${CHROOT_DIR}/sys"
  mount -t tmpfs tmpfs "${CHROOT_DIR}/run"
  # Host resolv only for apt inside chroot; replaced before squashfs.
  if [[ -f /etc/resolv.conf ]]; then
    cp /etc/resolv.conf "${CHROOT_DIR}/etc/resolv.conf"
  else
    printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' >"${CHROOT_DIR}/etc/resolv.conf"
  fi
}

finalize_live_rootfs() {
  log "Finalizing Live rootfs (DNS, machine-id, network)"
  # Public DNS fallback for first boot (resolved may rewrite later)
  printf 'nameserver 1.1.1.1\nnameserver 8.8.8.8\n' >"${CHROOT_DIR}/etc/resolv.conf"
  # Unique machine-id per boot (empty → systemd generates)
  : >"${CHROOT_DIR}/etc/machine-id"
  rm -f "${CHROOT_DIR}/var/lib/dbus/machine-id" 2>/dev/null || true
  # Drop static /dev nodes left from bootstrap; live uses devtmpfs
  find "${CHROOT_DIR}/dev" -mindepth 1 -maxdepth 1 ! -name 'pts' ! -name 'shm' \
    -exec rm -rf {} + 2>/dev/null || true
}

configure_rootfs() {
  log "Configuring ${VARIANT} rootfs"
  prepare_apt
  if [[ "${VARIANT}" == "server" ]]; then
    configure_rootfs_server
  else
    configure_rootfs_desktop
  fi
  cleanup_mounts
}

apply_lipi_identity() {
  log "Applying Lipi OS identity (${VARIANT})"

  local os_release lsb lipi_release motd_header
  if [[ "${VARIANT}" == "server" ]]; then
    os_release="${OVERLAY_SERVER_DIR}/etc/os-release"
    lsb="${OVERLAY_SERVER_DIR}/etc/lsb-release"
    lipi_release="${OVERLAY_SERVER_DIR}/etc/lipi-release"
    motd_header="${OVERLAY_SERVER_DIR}/etc/update-motd.d/00-lipi-header"
  else
    os_release="${OVERLAY_DIR}/etc/os-release"
    lsb="${OVERLAY_DIR}/etc/lsb-release"
    lipi_release="${OVERLAY_DIR}/etc/lipi-release"
    motd_header="${OVERLAY_DIR}/etc/update-motd.d/00-lipi-header"
  fi

  rm -f "${CHROOT_DIR}/etc/os-release" "${CHROOT_DIR}/usr/lib/os-release" \
    "${CHROOT_DIR}/etc/lsb-release"
  cp -f "${os_release}" "${CHROOT_DIR}/usr/lib/os-release"
  cp -f "${os_release}" "${CHROOT_DIR}/etc/os-release"
  cp -f "${lsb}" "${CHROOT_DIR}/etc/lsb-release"
  cp -f "${lipi_release}" "${CHROOT_DIR}/etc/lipi-release"

  mkdir -p "${CHROOT_DIR}/etc/update-motd.d"
  if compgen -G "${CHROOT_DIR}/etc/update-motd.d/*" >/dev/null; then
    chmod a-x "${CHROOT_DIR}/etc/update-motd.d/"* 2>/dev/null || true
  fi
  cp -f "${motd_header}" "${CHROOT_DIR}/etc/update-motd.d/00-lipi-header"
  chmod 755 "${CHROOT_DIR}/etc/update-motd.d/00-lipi-header"
  rm -f "${CHROOT_DIR}/etc/legal"
  : >"${CHROOT_DIR}/etc/motd.dynamic" 2>/dev/null || true

  local host="lipi-os"
  [[ "${VARIANT}" == "server" ]] && host="lipi-server"
  printf '%s\n' "${host}" >"${CHROOT_DIR}/etc/hostname"
  cat >"${CHROOT_DIR}/etc/hosts" <<EOF
127.0.0.1	localhost
127.0.1.1	${host}
::1		localhost ip6-localhost ip6-loopback
ff02::1		ip6-allnodes
ff02::2		ip6-allrouters
EOF
}

install_lipi() {
  log "Installing Lipi OS into /opt/lipi-os"
  rm -rf "${CHROOT_DIR}/opt/lipi-os"
  mkdir -p "${CHROOT_DIR}/opt/lipi-os"

  local excludes=(
    --exclude '__pycache__/'
    --exclude '*.pyc'
    --exclude '.venv/'
    --exclude 'venv/'
  )

  if [[ "${VARIANT}" == "server" ]]; then
    # Keep CLI-useful apps only; drop GUI-oriented ones
    excludes+=(
      --exclude 'apps/browser/'
      --exclude 'apps/ide/'
      --exclude 'apps/file_manager/'
      --exclude 'apps/calculator/'
    )
  fi

  rsync -a --delete "${excludes[@]}" \
    "${ROOT_DIR}/code/" "${CHROOT_DIR}/opt/lipi-os/"

  # Shared overlay
  rsync -a "${OVERLAY_DIR}/" "${CHROOT_DIR}/"
  # Server overrides
  if [[ "${VARIANT}" == "server" ]]; then
    rsync -a "${OVERLAY_SERVER_DIR}/" "${CHROOT_DIR}/"
  fi

  chmod 755 "${CHROOT_DIR}/usr/local/bin/lipi-os"
  chmod 755 "${CHROOT_DIR}/etc/update-motd.d/00-lipi-header" 2>/dev/null || true

  apply_lipi_identity

  # Force CLI launcher defaults for server
  if [[ "${VARIANT}" == "server" ]]; then
    cat >"${CHROOT_DIR}/usr/local/bin/lipi-os" <<'EOF'
#!/bin/sh
set -e
export LIPI_HOME="${LIPI_HOME:-/opt/lipi-os}"
export LIPI_EDITION="${LIPI_EDITION:-server}"
cd "$LIPI_HOME"
# Server edition is CLI-only
exec python3 "$LIPI_HOME/main.py" --cli "$@"
EOF
    chmod 755 "${CHROOT_DIR}/usr/local/bin/lipi-os"
  fi

  mkdir -p "${CHROOT_DIR}/root"
  if [[ "${VARIANT}" == "server" ]]; then
    cat >"${CHROOT_DIR}/root/.bashrc" <<'EOF'
# Lipi OS Server
alias lipi='lipi-os'
export PATH="/usr/local/bin:$PATH"
export LIPI_OS=1
export LIPI_EDITION=server
unset debian_chroot 2>/dev/null || true
EOF
  else
    cat >"${CHROOT_DIR}/root/.bashrc" <<'EOF'
# Lipi OS
alias lipi='lipi-os'
export PATH="/usr/local/bin:$PATH"
export LIPI_OS=1
export LIPI_EDITION=desktop
unset debian_chroot 2>/dev/null || true
EOF
  fi

  ln -sfn /usr/local/bin/lipi-os "${CHROOT_DIR}/usr/bin/lipi" 2>/dev/null || \
    ln -sfn /usr/local/bin/lipi-os "${CHROOT_DIR}/bin/lipi"

  # Mark edition inside Lipi tree
  printf '%s\n' "${VARIANT}" >"${CHROOT_DIR}/opt/lipi-os/EDITION"

  if [[ "${VARIANT}" == "server" ]]; then
    chmod 755 "${CHROOT_DIR}/usr/local/sbin/lipi-regen-ssh-keys" 2>/dev/null || true
    chroot "${CHROOT_DIR}" systemctl enable lipi-ssh-hostkeys.service 2>/dev/null || true
  fi
}

make_squashfs() {
  log "Creating squashfs"
  mkdir -p "${IMAGE_DIR}/live" "${IMAGE_DIR}/boot/grub"
  mkdir -p "${CHROOT_DIR}"/{dev,proc,sys,run,tmp,boot,var/tmp}
  chmod 1777 "${CHROOT_DIR}/tmp" "${CHROOT_DIR}/var/tmp" || true
  rm -f "${IMAGE_DIR}/live/filesystem.squashfs"

  local extra_excludes=()
  if [[ "${VARIANT}" == "server" ]]; then
    extra_excludes+=(
      -e usr/share/doc
      -e usr/share/man
      -e usr/share/info
      -e usr/share/gtk-doc
      -e var/cache/apt
      -e var/lib/apt/lists
    )
  fi

  mksquashfs "${CHROOT_DIR}" "${IMAGE_DIR}/live/filesystem.squashfs" \
    -comp xz -e boot/vmlinuz* -e boot/initrd.img* -e boot/*.old \
    -e var/cache/apt/archives -e var/lib/apt/lists \
    "${extra_excludes[@]+"${extra_excludes[@]}"}"
}

copy_kernel() {
  log "Copying kernel, initrd, GRUB config"
  local vmlinuz initrd grub_cfg
  vmlinuz="$(ls -1 "${CHROOT_DIR}/boot"/vmlinuz-* | sort -V | tail -1)"
  initrd="$(ls -1 "${CHROOT_DIR}/boot"/initrd.img-* | sort -V | tail -1)"
  cp -f "${vmlinuz}" "${IMAGE_DIR}/live/vmlinuz"
  cp -f "${initrd}" "${IMAGE_DIR}/live/initrd.img"
  if [[ "${VARIANT}" == "server" ]]; then
    grub_cfg="${ISO_DIR}/grub-server.cfg"
  else
    grub_cfg="${ISO_DIR}/grub.cfg"
  fi
  cp -f "${grub_cfg}" "${IMAGE_DIR}/boot/grub/grub.cfg"
}

make_iso() {
  log "Building hybrid BIOS+UEFI ISO → ${ISO_NAME} (label ${ISO_LABEL})"
  mkdir -p "${DIST_DIR}"
  local out="${DIST_DIR}/${ISO_NAME}"
  rm -f "${out}"
  grub-mkrescue -o "${out}" -V "${ISO_LABEL}" "${IMAGE_DIR}"
  local size
  size="$(du -h "${out}" | awk '{print $1}')"
  log "ISO ready: ${out} (${size})"
  ls -lh "${out}"
  sha256sum "${out}" | tee "${out}.sha256"
}

build_variant() {
  set_variant "$1"
  log "======== Building Lipi OS ${VARIANT} ========"
  install_host_deps
  bootstrap_rootfs
  configure_rootfs
  install_lipi
  finalize_live_rootfs
  make_squashfs
  copy_kernel
  make_iso
}

usage() {
  cat <<EOF
Usage: sudo ./iso/build.sh [desktop|server|all|clean]

  desktop  (default) full Live ISO → dist/lipi-os-live.iso
  server   minimal CLI/SSH ISO  → dist/lipi-os-server.iso
  all      build both variants
  clean    remove iso/.work (keeps dist/)

Server edition drops GUI (no tkinter), keeps settings/console/text_editor,
uses a smaller virtual kernel when available, adds OpenSSH, strips docs.

Environment:
  CODENAME ARCH MIRROR
  ISO_NAME_DESKTOP ISO_NAME_SERVER
EOF
}

main() {
  need_root
  local cmd="${1:-desktop}"
  case "${cmd}" in
    -h|--help)
      usage
      exit 0
      ;;
    clean)
      cleanup_all_work_mounts
      rm -rf "${ISO_DIR}/.work"
      log "Cleaned ${ISO_DIR}/.work"
      ;;
    desktop|live|normal|full)
      build_variant desktop
      ;;
    server|srv|minimal)
      build_variant server
      ;;
    all|both)
      build_variant desktop
      build_variant server
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
