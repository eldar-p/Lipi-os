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

- Shell: `ls`, `cd`, `pwd`, `mkdir`, `cat`, `echo`, `touch`, `cp`, `mv`, `rm`, `date`, `run`, `apps`, `open`, `help`, `exit`
- Системные команды: `settings`, `tasks`, `store`, `compile`
- Приложения: Calculator, File Manager, Settings, Text Editor, Console, IDE, Browser
- SDK для приложений (`code/sdk`)
- Настройки языка (ru/en) и темы
- Диспетчер задач, магазин (.lipi / zip), Compiler Hub

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
├── README.md
└── LICENSE
```

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
