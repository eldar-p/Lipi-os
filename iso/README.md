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

## Windows — в 1–2 клика

Один раз поставьте **WSL2 + Ubuntu** или **Docker Desktop**. Дальше:

| Действие | Файл |
|----------|------|
| Двойной клик → обе ISO | `build-iso.bat` |
| Только desktop | `iso\build-desktop.bat` |
| Только server | `iso\build-server.bat` |
| Обе явно | `iso\build-all.bat` |

Что делает скрипт сам:

1. Ищет WSL и запускает сборку от **root** (без пароля sudo)
2. Или Docker: тянет `ubuntu:24.04`, ставит пакеты, собирает
3. Скачивает все apt-зависимости
4. Пишет лог в `dist\build-windows.log`
5. По успеху открывает папку `dist\`

```bat
build-iso.bat
build-iso.bat desktop
build-iso.bat server
build-iso.bat menu
```

Первый запуск WSL: в PowerShell от Администратора  
`wsl --install -d Ubuntu` → перезагрузка → снова `build-iso.bat`.

### Если `.bat` сыпет `'…' is not recognized`

Это почти всегда **LF вместо CRLF** (Git/редактор сохранил Unix-переводы строк).  
`cmd.exe` тогда режет UTF-8 и воспринимает куски строк как команды.

В репозитории `*.bat` зафиксированы как **CRLF** (см. `.gitattributes`).  
После `git pull` проверьте:

```bat
git checkout -- build-iso.bat iso\*.bat
```

или заново склонируйте репозиторий. Не открывайте `.bat` в редакторах, которые принудительно ставят LF.

### Если путь к репо содержит `(1)` / пробелы

Windows часто кладёт zip в `...\Lipi-os-...(1)\...`.

Раньше ломалось дважды:

1. `env LIPI_WSL_ROOT=...` — bash видел `(` как синтаксис  
2. обычный `wsl cmd args` — WSL склеивает args в одну строку для shell

Сейчас скрипт:

- вызывает `wsl --exec` (настоящий argv, без склейки)
- копирует репо в `/var/tmp/lipi-os-build` и собирает там
- копирует готовые `.iso` обратно в `dist\`

Папку с `(1)` переименовывать не нужно.

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
