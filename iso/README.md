# Lipi OS Live ISO

Сборка загрузочного ISO, чтобы запускать Lipi OS на реальном ПК (BIOS и UEFI).

## Что внутри

- Ubuntu Live (`noble`) + Python 3 + Lipi OS в `/opt/lipi-os`
- Автологин `root` на `tty1` и автозапуск `lipi-os --cli`
- Hybrid ISO: можно записать на USB и грузить с флешки

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

Повторная сборка после правок кода (chroot уже есть):

```bash
sudo ./iso/build.sh
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

Замените `/dev/sdX` на устройство флешки (не раздел вроде `/dev/sdX1`). Проверить можно через `lsblk`.

Windows: [Rufus](https://rufus.ie/) → режим DD / Image mode.

macOS:

```bash
diskutil list
diskutil unmountDisk /dev/diskN
sudo dd if=dist/lipi-os-live.iso of=/dev/rdiskN bs=4m
```

## Загрузка на реальном ПК

1. Вставьте USB
2. В BIOS/UEFI включите загрузку с USB (при Secure Boot — отключите Secure Boot или используйте машину без него)
3. Выберите пункт **Lipi OS Live (CLI)**
4. После загрузки откроется оболочка Lipi OS

Выход в обычный Linux shell:

```text
exit
```

Снова запустить Lipi OS:

```bash
lipi-os --cli
```

Пропустить автозапуск при логине:

```bash
LIPI_SKIP_AUTOSTART=1 bash
```

## Важно

- Это Live-система: изменения в файлах не сохраняются после перезагрузки (если не монтировать постоянный диск вручную).
- GUI (`--gui`) на «голом» Live без X-сервера не стартует — по умолчанию CLI. Для GUI нужна отдельная сборка с Xorg.
- ISO занимает сотни мегабайт из‑за ядра Linux и initramfs — Python-оболочке нужен реальный Linux, чтобы грузиться на железе.
