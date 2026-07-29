# Lipi OS Live ISO

Своя ОС на ядре Linux: загрузочный образ для реального ПК (BIOS / UEFI).

## Архитектура

```
┌─────────────────────────────────────┐
│            Lipi OS (своя)           │
│  shell · apps · settings · store    │
├─────────────────────────────────────┤
│     userspace (systemd, python…)    │
├─────────────────────────────────────┤
│         Linux kernel                │
└─────────────────────────────────────┘
```

Это не «программа внутри Ubuntu», а **свой дистрибутив Lipi OS**:
- своё имя (`/etc/os-release`, hostname `lipi-os`, GRUB «Lipi OS»)
- своя оболочка как основной интерфейс после загрузки
- под капотом — ядро Linux (иначе на железе не загрузиться без написания своего ядра)

Пакеты ядра и базовый userspace берутся из Debian/Ubuntu-репозиториев только как фундамент; идентичность системы — Lipi.

## Что внутри образа

- Linux kernel + Live initramfs
- Python 3 и Lipi OS в `/opt/lipi-os`
- Автологин и автозапуск `lipi-os --cli`
- Hybrid ISO (USB / DVD, BIOS + UEFI)

## Сборка

На Ubuntu/Debian (нужен root):

```bash
sudo ./iso/build.sh
```

Готовый образ:

```
dist/lipi-os-live.iso
dist/lipi-os-live.iso.sha256
```

Полная пересборка rootfs:

```bash
sudo ./iso/build.sh clean
sudo ./iso/build.sh
```

## Запись на флешку

Linux:

```bash
sudo dd if=dist/lipi-os-live.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

Замените `/dev/sdX` на устройство флешки (`lsblk`). На Windows — [Rufus](https://rufus.ie/) в режиме DD.

## Загрузка

1. USB → Boot Menu → **Lipi OS (Live)**
2. При Secure Boot — отключите его в UEFI
3. Откроется оболочка Lipi OS

```bash
exit                 # системный shell Linux
lipi-os --cli        # снова Lipi
LIPI_SKIP_AUTOSTART=1 bash   # войти без автозапуска
cat /etc/os-release  # PRETTY_NAME="Lipi OS 8+"
uname -s             # Linux
```

## Важно

- Live: изменения не сохраняются после перезагрузки.
- GUI (`--gui`) без Xorg в этой сборке не стартует — по умолчанию CLI.
- Своё ядро с нуля (не Linux) — отдельный огромный проект; здесь сознательно выбран Linux как ядро, а «своя» часть — всё, что выше него.
