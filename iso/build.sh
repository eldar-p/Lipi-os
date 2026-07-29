#!/usr/bin/env bash
# Build a BIOS+UEFI bootable Live ISO that launches Lipi OS on real PCs.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ISO_DIR="${ROOT_DIR}/iso"
DIST_DIR="${ROOT_DIR}/dist"
WORK_DIR="${ISO_DIR}/.work"
OVERLAY_DIR="${ISO_DIR}/overlay"

CODENAME="${CODENAME:-noble}"
ARCH="${ARCH:-amd64}"
ISO_LABEL="${ISO_LABEL:-LIPIOS}"
ISO_NAME="${ISO_NAME:-lipi-os-live.iso}"
MIRROR="${MIRROR:-http://archive.ubuntu.com/ubuntu}"

CHROOT_DIR="${WORK_DIR}/chroot"
IMAGE_DIR="${WORK_DIR}/image"
CACHE_DIR="${WORK_DIR}/cache"

need_root() {
  if [[ "${EUID}" -ne 0 ]]; then
    echo "Run as root: sudo ./iso/build.sh"
    exit 1
  fi
}

log() {
  printf '\n==> %s\n' "$*"
}

cleanup_mounts() {
  if [[ -d "${CHROOT_DIR}" ]]; then
    umount -lf "${CHROOT_DIR}/dev/pts" 2>/dev/null || true
    umount -lf "${CHROOT_DIR}/dev" 2>/dev/null || true
    umount -lf "${CHROOT_DIR}/proc" 2>/dev/null || true
    umount -lf "${CHROOT_DIR}/sys" 2>/dev/null || true
    umount -lf "${CHROOT_DIR}/run" 2>/dev/null || true
  fi
}

trap cleanup_mounts EXIT

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
  log "Bootstrapping Linux userspace base (${CODENAME}/${ARCH}) for Lipi OS"
  mkdir -p "${CACHE_DIR}" "${CHROOT_DIR}"
  if [[ ! -d "${CHROOT_DIR}/bin" ]]; then
    debootstrap --arch="${ARCH}" --variant=minbase \
      --cache-dir="${CACHE_DIR}" \
      "${CODENAME}" "${CHROOT_DIR}" "${MIRROR}"
  else
    log "Reusing existing chroot at ${CHROOT_DIR}"
  fi
}

configure_rootfs() {
  log "Installing Linux kernel + Live boot into Lipi OS rootfs"
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

  cp /etc/resolv.conf "${CHROOT_DIR}/etc/resolv.conf"

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
  kmod

# Locale / keyboard defaults
sed -i 's/^# *en_US.UTF-8/en_US.UTF-8/' /etc/locale.gen || true
sed -i 's/^# *ru_RU.UTF-8/ru_RU.UTF-8/' /etc/locale.gen || true
locale-gen
update-locale LANG=en_US.UTF-8

# Live user convenience: empty root password for console recovery
passwd -d root

# Enable networking on boot when available
systemctl enable systemd-networkd.service || true
systemctl enable systemd-resolved.service 2>/dev/null || true

# Rebuild initramfs so live-boot hooks are present
update-initramfs -u

apt-get clean
rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
CHROOT

  cleanup_mounts
}

apply_lipi_identity() {
  log "Applying Lipi OS identity (own distro on Linux kernel)"

  # Replace vendor os-release (often a symlink into /usr/lib)
  rm -f "${CHROOT_DIR}/etc/os-release" "${CHROOT_DIR}/usr/lib/os-release" \
    "${CHROOT_DIR}/etc/lsb-release"
  cp -f "${OVERLAY_DIR}/etc/os-release" "${CHROOT_DIR}/usr/lib/os-release"
  cp -f "${OVERLAY_DIR}/etc/os-release" "${CHROOT_DIR}/etc/os-release"
  cp -f "${OVERLAY_DIR}/etc/lsb-release" "${CHROOT_DIR}/etc/lsb-release"
  cp -f "${OVERLAY_DIR}/etc/lipi-release" "${CHROOT_DIR}/etc/lipi-release"

  # Hide Ubuntu/Debian MOTD noise
  mkdir -p "${CHROOT_DIR}/etc/update-motd.d"
  if compgen -G "${CHROOT_DIR}/etc/update-motd.d/*" >/dev/null; then
    chmod a-x "${CHROOT_DIR}/etc/update-motd.d/"* 2>/dev/null || true
  fi
  cp -f "${OVERLAY_DIR}/etc/update-motd.d/00-lipi-header" \
    "${CHROOT_DIR}/etc/update-motd.d/00-lipi-header"
  chmod 755 "${CHROOT_DIR}/etc/update-motd.d/00-lipi-header"
  rm -f "${CHROOT_DIR}/etc/legal"
  : >"${CHROOT_DIR}/etc/motd.dynamic" 2>/dev/null || true

  # Machine identity
  printf 'lipi-os\n' >"${CHROOT_DIR}/etc/hostname"
  cat >"${CHROOT_DIR}/etc/hosts" <<'EOF'
127.0.0.1	localhost
127.0.1.1	lipi-os
::1		localhost ip6-localhost ip6-loopback
ff02::1		ip6-allnodes
ff02::2		ip6-allrouters
EOF
}

install_lipi() {
  log "Installing Lipi OS shell into /opt/lipi-os"
  rm -rf "${CHROOT_DIR}/opt/lipi-os"
  mkdir -p "${CHROOT_DIR}/opt/lipi-os"
  rsync -a --delete \
    --exclude '__pycache__/' \
    --exclude '*.pyc' \
    --exclude '.venv/' \
    --exclude 'venv/' \
    "${ROOT_DIR}/code/" "${CHROOT_DIR}/opt/lipi-os/"

  # Overlay: autologin, launcher, issue, hostname, branding
  rsync -a "${OVERLAY_DIR}/" "${CHROOT_DIR}/"
  chmod 755 "${CHROOT_DIR}/usr/local/bin/lipi-os"
  chmod 755 "${CHROOT_DIR}/etc/update-motd.d/00-lipi-header" 2>/dev/null || true

  apply_lipi_identity

  # Writable home-like settings path on Live (tmpfs overlay handles writes)
  mkdir -p "${CHROOT_DIR}/root"
  cat >"${CHROOT_DIR}/root/.bashrc" <<'EOF'
# Lipi OS
alias lipi='lipi-os'
export PATH="/usr/local/bin:$PATH"
export LIPI_OS=1
# Quiet Ubuntu remnants if any still print
unset debian_chroot 2>/dev/null || true
EOF

  # Make /usr/bin/lipi available as short name
  ln -sfn /usr/local/bin/lipi-os "${CHROOT_DIR}/usr/bin/lipi" 2>/dev/null || \
    ln -sfn /usr/local/bin/lipi-os "${CHROOT_DIR}/bin/lipi"
}

make_squashfs() {
  log "Creating squashfs"
  mkdir -p "${IMAGE_DIR}/live" "${IMAGE_DIR}/boot/grub"
  # live-boot needs empty mountpoint directories inside the image
  mkdir -p "${CHROOT_DIR}"/{dev,proc,sys,run,tmp,boot,var/tmp}
  chmod 1777 "${CHROOT_DIR}/tmp" "${CHROOT_DIR}/var/tmp" || true
  rm -f "${IMAGE_DIR}/live/filesystem.squashfs"
  # Do NOT exclude dev/proc/sys/run/tmp — those directories must exist as mountpoints.
  # Exclude only heavy/unnecessary boot payloads (kernel copied separately).
  mksquashfs "${CHROOT_DIR}" "${IMAGE_DIR}/live/filesystem.squashfs" \
    -comp xz -e boot/vmlinuz* -e boot/initrd.img* -e boot/*.old \
    -e var/cache/apt/archives -e var/lib/apt/lists
}

copy_kernel() {
  log "Copying kernel and initrd"
  local vmlinuz initrd
  vmlinuz="$(ls -1 "${CHROOT_DIR}/boot"/vmlinuz-* | sort -V | tail -1)"
  initrd="$(ls -1 "${CHROOT_DIR}/boot"/initrd.img-* | sort -V | tail -1)"
  cp -f "${vmlinuz}" "${IMAGE_DIR}/live/vmlinuz"
  cp -f "${initrd}" "${IMAGE_DIR}/live/initrd.img"
  cp -f "${ISO_DIR}/grub.cfg" "${IMAGE_DIR}/boot/grub/grub.cfg"
}

make_iso() {
  log "Building hybrid BIOS+UEFI ISO"
  mkdir -p "${DIST_DIR}"
  local out="${DIST_DIR}/${ISO_NAME}"
  rm -f "${out}"

  # Do NOT pass `--` here: it switches xorriso into native mode and breaks
  # grub-mkrescue's mkisofs-compatible arguments.
  grub-mkrescue -o "${out}" "${IMAGE_DIR}"

  local size
  size="$(du -h "${out}" | awk '{print $1}')"
  log "ISO ready: ${out} (${size})"
  ls -lh "${out}"
  sha256sum "${out}" | tee "${out}.sha256"
}

usage() {
  cat <<EOF
Usage: sudo ./iso/build.sh [clean|all]

  all    (default) build dist/lipi-os-live.iso
  clean  remove iso/.work build tree (keeps dist/)

Environment overrides:
  CODENAME=noble ARCH=amd64 MIRROR=http://archive.ubuntu.com/ubuntu
  ISO_NAME=lipi-os-live.iso
EOF
}

main() {
  need_root
  local cmd="${1:-all}"
  case "${cmd}" in
    clean)
      cleanup_mounts
      rm -rf "${WORK_DIR}"
      log "Cleaned ${WORK_DIR}"
      ;;
    all|-h|--help)
      if [[ "${cmd}" == "-h" || "${cmd}" == "--help" ]]; then
        usage
        exit 0
      fi
      install_host_deps
      bootstrap_rootfs
      configure_rootfs
      install_lipi
      make_squashfs
      copy_kernel
      make_iso
      ;;
    *)
      usage
      exit 1
      ;;
  esac
}

main "$@"
