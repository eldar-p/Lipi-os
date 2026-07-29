# Lipi OS

Операционная система-оболочка на Python (CLI + GUI на Tkinter). Можно собрать Live ISO на ядре Linux для реальных ПК.

## Запуск

```bash
cd code
pip install -r requirements.txt
python main.py --cli      # консоль
python main.py --gui      # GUI (нужен tkinter)
python main.py            # GUI если доступен, иначе CLI
```

## Что умеет сейчас (v8+)

- Shell: файлы (`ls`, `cp`, `grep`, `tree`…), система (`sysinfo`, `ps`, `free`…), сеть (`ping`, `fetch`, `serve`…)
- `help` / `help files` — каталог команд; `history` — история
- `langs` / `compile langs` — языки и тулчейны
- Compiler Hub: Python, JS/TS, HTML/CSS, C/C++, Java, Rust, Go, C#, ASM, Kotlin, Lua, Ruby, PHP, Bash, Perl, Zig…
- Установка компиляторов: `compilers install` или `sudo ./code/scripts/install-compilers.sh`
- Приложения: Calculator, File Manager, Settings, Text Editor, Console, IDE, Browser
- SDK, настройки ru/en, магазин, Live ISO (desktop/server)

## Документация для разработчиков

Подробно (API, создание приложений, команды, настройки, IDE/браузер и т.д.):

→ **[docs/DEVELOPER.md](docs/DEVELOPER.md)**

Кратко:

```bash
# список приложений
apps
apps -v

# запуск
open calculator
open text_editor
open console
open ide
open browser https://example.com
open settings --cli
```

## Структура

```
lipi-os/
├── code/
│   ├── main.py
│   ├── sdk/                 # App SDK
│   ├── core/
│   ├── commands/
│   ├── apps/
│   └── settings/
├── docs/DEVELOPER.md
├── iso/                   # Live ISO builder for real PCs
│   ├── build.sh
│   ├── grub.cfg
│   └── overlay/
├── dist/                  # output: lipi-os-live.iso (after build)
├── README.md
└── LICENSE
```

## Загрузка на реальном ПК (Live ISO)

Две сборки на ядре Linux:

```bash
sudo ./iso/build.sh desktop   # обычная → dist/lipi-os-live.iso
sudo ./iso/build.sh server    # урезанная CLI+SSH → dist/lipi-os-server.iso
sudo ./iso/build.sh all       # обе
```

На **Windows** (один раз: WSL2 или Docker Desktop, дальше 1–2 клика):

```bat
build-iso.bat                 :: обе ISO, автостарт через 5 сек
iso\build-desktop.bat         :: только обычная
iso\build-server.bat          :: только серверная
```

Скрипт сам ставит зависимости, собирает без пароля sudo (`wsl -u root`) или через Docker и открывает `dist\`.

## Формат приложения

```
apps/my_app/
  main.py
  description.json
```

```json
{
  "name": "My App",
  "name_ru": "Моё приложение",
  "version": "1.0.0",
  "author": "You",
  "description": "Short description",
  "category": "productivity"
}
```

Шаблон `main.py`:

```python
import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parents[2]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from sdk import run_app_main

def run_gui():
    ...

def run_cli():
    ...

if __name__ == "__main__":
    run_app_main(run_gui, run_cli)
```
