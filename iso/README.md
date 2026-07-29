# Lipi OS Live ISO

Два образа своей ОС на ядре Linux (BIOS / UEFI).

| Образ | Команда сборки | Для чего |
|-------|----------------|----------|
| **Desktop** `lipi-os-live.iso` | `sudo ./iso/build.sh desktop` | Обычная полная версия (GUI-приложения, tkinter) |
| **Server** `lipi-os-server.iso` | `sudo ./iso/build.sh server` | Урезанная CLI-версия + SSH |

```bash
sudo ./iso/build.sh all      # оба сразу
sudo ./iso/build.sh clean    # снести iso/.work
```

## Архитектура

```
┌─────────────────────────────────────┐
│     Lipi OS (desktop / server)      │
│  shell · apps · settings · store    │
├─────────────────────────────────────┤
│     userspace (systemd, python…)    │
├─────────────────────────────────────┤
│         Linux kernel                │
└─────────────────────────────────────┘
```

## Desktop (обычная)

- Ядро `linux-image-generic`
- Python + **tkinter**
- Все приложения: calculator, file_manager, settings, text_editor, console, ide, browser
- Автозапуск Lipi CLI (GUI-приложения через `open …`)

## Server (оптимизированная)

Что убрано / упрощено:

- Нет GUI: без `python3-tk`, без browser / ide / file_manager / calculator
- Меньше ядро: `linux-image-virtual` (если есть в репозитории)
- Вырезаны doc/man/лишние locale при сборке
- Остаются: **settings**, **console**, **text_editor** (CLI)
- Добавлен **OpenSSH** (root live-login для лаборатории)
- Hostname: `lipi-server`
- Лаунчер всегда `--cli`

## Запись на флешку

```bash
sudo dd if=dist/lipi-os-live.iso of=/dev/sdX bs=4M status=progress oflag=sync
# или
sudo dd if=dist/lipi-os-server.iso of=/dev/sdX bs=4M status=progress oflag=sync
```

Windows: Rufus (DD mode). Secure Boot при необходимости отключить.

## После загрузки

```bash
apps                 # список приложений
open settings --cli
open console --cli
exit                 # системный shell
cat /etc/os-release  # Desktop или Server
```

Server по SSH (после получения IP, Live с пустым паролем root — только для тестов):

```bash
ssh root@<ip>
```

## Важно

- Live: изменения не сохраняются после перезагрузки.
- ISO в git не хранится — только скрипты сборки (`dist/` в `.gitignore`).
