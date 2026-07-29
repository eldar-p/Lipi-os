# Руководство разработчика Lipi OS

Полная инструкция: как устроена система, как писать приложения, команды, настройки, API ядра.

---

## 1. Архитектура

```
lipi-os/
├── code/
│   ├── main.py              # Точка входа (CLI / GUI desktop)
│   ├── paths.py             # Пути: apps/, settings/, commands/
│   ├── i18n.py              # Локализация (ru / en)
│   ├── sdk/                 # SDK для приложений
│   ├── core/                # Ядро ОС
│   │   ├── shell.py         # Командный интерпретатор
│   │   ├── gui_engine.py    # Окна (Tkinter)
│   │   ├── settings_manager.py
│   │   ├── task_manager.py
│   │   ├── app_store.py
│   │   └── compiler_hub.py
│   ├── commands/            # Внешние shell-команды (файл = команда)
│   ├── apps/                # Установленные приложения
│   └── settings/
│       ├── config.json
│       └── lang/ru.json, en.json
├── docs/DEVELOPER.md        # Этот файл
└── iso/                     # Live ISO (отдельная ветка/PR)
```

Запуск:

```bash
cd code
pip install -r requirements.txt
python main.py --cli      # оболочка
python main.py --gui      # рабочий стол
```

---

## 2. Формат приложения

Каждое приложение — папка в `code/apps/<id>/`:

```
apps/my_app/
├── description.json    # обязательно
└── main.py             # обязательно (точка входа)
```

Опционально: иконки, `README`, данные, подмодули.

### 2.1. `description.json`

```json
{
  "name": "My App",
  "name_ru": "Моё приложение",
  "name_en": "My App",
  "version": "1.0.0",
  "author": "You",
  "description": "Short description in English",
  "category": "productivity",
  "entry": "main.py"
}
```

| Поле | Обязательно | Назначение |
|------|-------------|------------|
| `name` | да* | Отображаемое имя / база для id при установке из магазина |
| `name_ru` / `name_en` | нет | Локализованные названия |
| `version` | рекомендуется | Версия |
| `author` | нет | Автор |
| `description` | рекомендуется | Краткое описание |
| `category` | нет | `system`, `productivity`, `development`, `internet`, … |
| `entry` | нет | Имя entry-файла (по умолчанию `main.py`) |

\* Для установки через магазин нужны и `description.json`, и `main.py`.

**Id приложения** = имя папки (`calculator`, `text_editor`). Команда запуска:

```text
open text_editor
open browser https://example.com
open ide --cli
```

### 2.2. `main.py` — контракт

Приложение — обычный Python-скрипт. Рабочий стол запускает его так:

```python
subprocess.Popen([sys.executable, "main.py"], cwd=app_folder)
```

Рекомендуемый шаблон (GUI + CLI):

```python
import sys
from pathlib import Path

# Чтобы `import sdk` / `import core` работали при cwd=папка приложения
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

Флаг `--cli` принудительно включает консольный режим. Без флага сначала пробуется GUI, при ошибке — CLI.

Аргументы после имени приложения передаются в `sys.argv` (например `open browser https://a.com`).

---

## 3. App SDK (`code/sdk`)

```python
from sdk import (
    ensure_import_path,  # уже вызывается при import sdk
    lipi_root,           # Path к code/
    is_cli,              # "--cli" в argv?
    load_description,    # description.json
    display_name,        # имя с учётом языка
    get_config,          # settings/config.json
    get_lang,            # строки локализации
    apps_directory,      # каталог apps/
    list_apps,           # [{id, path, main, meta, name}, ...]
    find_app,            # поиск по id / имени
    launch_app,          # subprocess Popen
    run_app_main,        # стандартный вход GUI/CLI
)
```

Из приложения всегда можно:

```python
from sdk import get_config, get_lang
from core.gui_engine import LipiWindow
from paths import APPS_DIR, TEMP_DIR
```

`import sdk` сам добавляет `code/` в `sys.path`.

---

## 4. Команды shell

### 4.1. Встроенные (`core/shell.py`)

| Команда | Описание |
|---------|----------|
| `ls`, `cd`, `pwd`, `mkdir`, `cat`, `echo`, `clear` | Файловая система |
| `help`, `exit` | Справка / выход |
| `settings [--gui]` | Настройки |
| `tasks [--gui]` | Диспетчер задач |
| `store [--gui]` | Магазин приложений |
| `compile [--gui]` | Compiler Hub |

### 4.2. Внешние (`commands/<имя>.py`)

Файл `commands/foo.py` становится командой `foo`, если в нём есть:

```python
def run(args: list[str]) -> str | None:
    """args — аргументы без имени команды. Вернуть текст в stdout или None."""
    return "ok"
```

Примеры: `apps`, `open`, `run`, `cp`, `mv`, `rm`, `touch`, `date`.

### 4.3. Работа с приложениями

```text
apps              # список id и имён
apps -v           # подробно (версия, путь, описание)
open <id>         # запуск (GUI в фоне)
open <id> --cli   # запуск в этой же консоли
open              # справка + список
run path.py       # запуск произвольного скрипта по пути
```

---

## 5. Настройки

Файл: `settings/config.json`

```json
{
  "language": "ru",
  "theme": "dark",
  "compiler_paths": {
    "gcc": "/usr/bin/gcc"
  },
  "app_directory": "apps"
}
```

| Ключ | Значения | Смысл |
|------|----------|--------|
| `language` | `ru`, `en` | Язык интерфейса |
| `theme` | `light`, `dark` | Тема (сохраняется; применение в UI развивается) |
| `compiler_paths` | объект имя→путь | Ручные пути для Compiler Hub |
| `app_directory` | путь | Где искать приложения |

API:

```python
from core.settings_manager import load_config, save_config, get_config
from core.settings_manager import cli_settings, create_gui_settings

cfg = load_config()
cfg["language"] = "ru"
save_config(cfg)
```

Локализация:

```python
from i18n import get_language_strings, t

lang = get_language_strings()   # dict строк
print(t("welcome"))            # с подстановкой args
```

Строки лежат в `settings/lang/ru.json` и `en.json` (поверх дефолтов из `i18n.DEFAULT_STRINGS`).

Приложение **Настройки**: `open settings` или меню Applications → Settings / команда `settings`.

---

## 6. GUI API (`LipiWindow`)

```python
from core.gui_engine import LipiWindow

win = LipiWindow("Title", 640, 480)          # своё окно + mainloop
# win = LipiWindow("Title", 640, 480, master=parent)  # Toplevel на desktop

win.add_label("Hello", row=0, col=0)
win.add_entry(row=1, col=0)
win.add_button("OK", command=win.close, row=2, col=0)
# или свободно: виджеты на win.content / win.root
win.mainloop()
```

Для сложных UI (редактор, IDE, браузер) обычно используют чистый `tkinter` — это нормально.

---

## 7. Магазин приложений и пакеты

Установка из папки / zip / `.lipi` (zip с другим расширением):

Внутри архива должны быть `description.json` + `main.py` (в корне или в одной вложенной папке — см. `install_from_path`).

```python
from core.app_store import install_from_path, uninstall_app, get_installed_apps
ok, msg = install_from_path(Path("my_app.lipi"))
```

CLI: `store` · GUI: `store --gui` / меню App Store.

Онлайн-каталог по умолчанию: URL из lang-ключа `online_repo`.

---

## 8. Compiler Hub

```python
from core.compiler_hub import compile_and_run, SUPPORTED_LANGUAGES

ok, output = compile_and_run("python", "print(1+1)")
ok, output = compile_and_run("cpp", 'int main(){return 0;}')
```

Поддержка: `python`, `javascript`, `c`, `cpp`, `cs`, `rust`, `asm`.  
Пути к компиляторам — в `config.compiler_paths` или автопоиск в `PATH`.

---

## 9. Диспетчер задач

```python
from core.task_manager import get_processes, terminate_process
for p in get_processes():
    print(p["pid"], p["name"], p["cpu"], p["memory"])
```

Нужен пакет `psutil`.

---

## 10. Встроенные приложения

| Id | Название | Назначение |
|----|----------|------------|
| `calculator` | Calculator | Калькулятор |
| `file_manager` | File Manager | Файлы |
| `settings` | Settings | Настройки ОС |
| `text_editor` | Text Editor | Редактор текста |
| `console` | Console | Консоль (Lipi shell + команды) |
| `ide` | IDE | Файлы + редактор + Run (F5) |
| `browser` | Browser | Просмотр URL (текст/HTML) + системный браузер |

Примеры:

```text
open calculator
open text_editor notes.txt
open ide /path/to/project
open browser https://example.com
open console
open settings --cli
```

---

## 11. Как создать приложение с нуля

### Шаг 1 — папка и метаданные

```bash
mkdir -p code/apps/hello
```

`code/apps/hello/description.json`:

```json
{
  "name": "Hello",
  "name_ru": "Привет",
  "version": "0.1.0",
  "author": "You",
  "description": "Demo app",
  "category": "demo"
}
```

### Шаг 2 — код

`code/apps/hello/main.py`:

```python
import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parents[2]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from sdk import get_lang, run_app_main

def run_gui():
    import tkinter as tk
    root = tk.Tk()
    root.title("Hello")
    tk.Label(root, text=get_lang().get("welcome", "Hello"), font=("Segoe UI", 16)).pack(padx=20, pady=20)
    tk.Button(root, text="OK", command=root.destroy).pack(pady=10)
    root.mainloop()

def run_cli():
    print(get_lang().get("welcome", "Hello from Lipi!"))

if __name__ == "__main__":
    run_app_main(run_gui, run_cli)
```

### Шаг 3 — проверка

```bash
cd code
python main.py --cli
# lipi@os: open hello
# lipi@os: apps -v
```

### Шаг 4 — пакет для магазина

```bash
cd code/apps/hello
zip -r ../../hello.lipi description.json main.py
# store → install путь/к/hello.lipi
```

---

## 12. Как добавить shell-команду

1. Создайте `code/commands/greet.py`:

```python
def run(args):
    name = args[0] if args else "friend"
    return f"Hello, {name}!"
```

2. Перезапустите shell — команда `greet` подхватится автоматически (`_load_external_commands`).

---

## 13. Рабочий стол (GUI)

`main.py → launch_gui()`:
- сканирует `apps/*/description.json`;
- пункты меню запускают `main.py` через `Popen`;
- Settings / Task Manager / App Store / Compiler Hub открываются как окна ядра.

Имена в меню берут `name` / `name_en` (при языке `ru` предпочтителен `name_ru`, если задан).

---

## 14. Live ISO (реальные ПК)

Две редакции:

```bash
sudo ./iso/build.sh desktop   # полная → dist/lipi-os-live.iso
sudo ./iso/build.sh server    # CLI+SSH, без GUI → dist/lipi-os-server.iso
sudo ./iso/build.sh all
```

Подробности: `iso/README.md`.

---

## 15. Чеклист качественного приложения

- [ ] Есть `description.json` с `name`, `version`, `description`
- [ ] Есть `name_ru` для русской локали
- [ ] Поддержаны GUI и `--cli`
- [ ] Используется `sdk` для путей/конфига
- [ ] Нет абсолютных путей «чужого» пользователя
- [ ] Ошибки показываются пользователю, процесс не падает молча
- [ ] Для долгих операций — поток + обновление UI через `root.after`

---

## 16. Быстрый справочник API

```text
SDK:     sdk.list_apps / find_app / launch_app / run_app_main / get_config / get_lang
Shell:   commands/<cmd>.py → def run(args)
GUI:     core.gui_engine.LipiWindow
Config:  core.settings_manager.load_config / save_config
Store:   core.app_store.install_from_path / uninstall_app
Tasks:   core.task_manager.get_processes / terminate_process
Compile: core.compiler_hub.compile_and_run
i18n:    i18n.get_language_strings / t
Paths:   paths.APPS_DIR / CONFIG_FILE / BASE_DIR
```

Если чего-то нет в ядре — расширяйте `core/` или выносите в приложение в `apps/`. Приложения не должны ломать контракт `description.json` + `main.py`.
