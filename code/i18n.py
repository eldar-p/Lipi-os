"""Shared internationalization helpers for Lipi OS."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from paths import CONFIG_FILE, LANG_DIR

DEFAULT_STRINGS: dict[str, dict[str, str]] = {
    "en": {
        "language_name": "English",
        "settings_title": "Lipi OS Settings",
        "language": "Language",
        "theme": "Theme",
        "light": "Light",
        "dark": "Dark",
        "compiler_paths": "Compiler Paths",
        "app_directory": "App Directory",
        "save": "Save",
        "cancel": "Cancel",
        "restart_required": "Some changes require restart.",
        "browse": "Browse...",
        "back": "Back",
        "exit": "Exit",
        "prompt": "lipi@os:",
        "unknown_command": "Command not found: {}",
        "exit_message": "Goodbye!",
        "welcome": "Welcome to Lipi OS!",
        "desktop_hint": "Open Applications to launch programs",
        "applications": "Applications",
        "task_manager": "Task Manager",
        "app_store": "App Store",
        "compiler_hub": "Compiler Hub",
        "settings": "Settings",
        "title": "Task Manager",
        "pid": "PID",
        "name": "Name",
        "cpu": "CPU %",
        "memory": "Memory (MB)",
        "terminate": "Terminate PID:",
        "killed": "Process {} terminated.",
        "not_found": "Not found",
        "process_not_found": "Process with PID {} not found.",
        "invalid_pid": "Invalid PID: {}",
        "help": "Enter PID to kill or 'q' to quit.",
        "kill": "Kill",
        "refresh": "Refresh",
        "store_title": "Lipi App Store",
        "installed": "Installed Apps",
        "online": "Online Catalog",
        "install": "Install",
        "uninstall": "Uninstall",
        "version": "Version",
        "author": "Author",
        "description": "Description",
        "enter_url": "Enter .lipi URL or local path:",
        "invalid_package": "Invalid package: missing description.json or main.py",
        "already_installed": "App already installed: {}",
        "installed_success": "Successfully installed: {}",
        "uninstalled": "Uninstalled: {}",
        "loading": "Loading...",
        "online_repo": "https://raw.githubusercontent.com/lipi-os/apps/main/catalog.json",
        "compiler_hub_title": "Compiler Hub",
        "select_lang": "Select language:",
        "enter_code": "Enter your code (press Ctrl+D / Ctrl+Z then Enter to finish):",
        "compiling": "Compiling...",
        "running": "Running...",
        "success": "Execution completed.",
        "error_compile": "Compilation error:\n{}",
        "error_run": "Runtime error:\n{}",
        "compiler_not_found": "Compiler '{}' not found. Install it or set the path in settings.",
        "run": "Run",
        "empty_code": "Empty code",
        "invalid_choice": "Invalid choice",
        "available_commands": "Available commands: {}",
        "use_exit": "Use 'exit' to quit.",
    },
    "ru": {
        "language_name": "Русский",
        "settings_title": "Настройки Lipi OS",
        "language": "Язык",
        "theme": "Тема",
        "light": "Светлая",
        "dark": "Тёмная",
        "compiler_paths": "Пути к компиляторам",
        "app_directory": "Каталог приложений",
        "save": "Сохранить",
        "cancel": "Отмена",
        "restart_required": "Некоторые изменения требуют перезапуска.",
        "browse": "Обзор...",
        "back": "Назад",
        "exit": "Выход",
        "prompt": "lipi@os:",
        "unknown_command": "Команда не найдена: {}",
        "exit_message": "До свидания!",
        "welcome": "Добро пожаловать в Lipi OS!",
        "desktop_hint": "Откройте «Приложения», чтобы запустить программы",
        "applications": "Приложения",
        "task_manager": "Диспетчер задач",
        "app_store": "Магазин приложений",
        "compiler_hub": "Центр компиляции",
        "settings": "Настройки",
        "title": "Диспетчер задач",
        "pid": "ПИД",
        "name": "Имя",
        "cpu": "ЦП %",
        "memory": "Память (МБ)",
        "terminate": "Завершить ПИД:",
        "killed": "Процесс {} завершён.",
        "not_found": "Не найдено",
        "process_not_found": "Процесс с ПИД {} не найден.",
        "invalid_pid": "Неверный ПИД: {}",
        "help": "Введите ПИД для завершения или 'q' для выхода.",
        "kill": "Завершить",
        "refresh": "Обновить",
        "store_title": "Магазин приложений Lipi",
        "installed": "Установленные приложения",
        "online": "Онлайн-каталог",
        "install": "Установить",
        "uninstall": "Удалить",
        "version": "Версия",
        "author": "Автор",
        "description": "Описание",
        "enter_url": "Введите URL .lipi или локальный путь:",
        "invalid_package": "Неверный пакет: отсутствует description.json или main.py",
        "already_installed": "Приложение уже установлено: {}",
        "installed_success": "Успешно установлено: {}",
        "uninstalled": "Удалено: {}",
        "loading": "Загрузка...",
        "online_repo": "https://raw.githubusercontent.com/lipi-os/apps/main/catalog.json",
        "compiler_hub_title": "Центр компиляции",
        "select_lang": "Выберите язык:",
        "enter_code": "Введите код (Ctrl+D / Ctrl+Z и Enter для завершения):",
        "compiling": "Компиляция...",
        "running": "Выполнение...",
        "success": "Выполнение завершено.",
        "error_compile": "Ошибка компиляции:\n{}",
        "error_run": "Ошибка выполнения:\n{}",
        "compiler_not_found": "Компилятор '{}' не найден. Установите его или укажите путь в настройках.",
        "run": "Запуск",
        "empty_code": "Пустой код",
        "invalid_choice": "Неверный выбор",
        "available_commands": "Доступные команды: {}",
        "use_exit": "Для выхода используйте 'exit'.",
    },
}


def ensure_lang_files() -> None:
    """Write default language files when missing."""
    LANG_DIR.mkdir(parents=True, exist_ok=True)
    for lang_code, data in DEFAULT_STRINGS.items():
        lang_file = LANG_DIR / f"{lang_code}.json"
        if not lang_file.exists():
            with open(lang_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)


def load_config_language() -> str:
    """Return the configured language code (en/ru)."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
            lang = str(config.get("language", "en")).lower()
            if lang in DEFAULT_STRINGS:
                return lang
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return "en"


def get_language_strings(lang_code: str | None = None) -> dict[str, Any]:
    """Load strings for a language, merging defaults for missing keys."""
    code = (lang_code or load_config_language()).lower()
    defaults = DEFAULT_STRINGS.get(code, DEFAULT_STRINGS["en"]).copy()
    lang_file = LANG_DIR / f"{code}.json"
    if lang_file.exists():
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                defaults.update({k: v for k, v in loaded.items() if isinstance(v, str)})
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass
    return defaults


def t(key: str, *args: Any, lang_code: str | None = None) -> str:
    """Translate a key; optionally format with args."""
    strings = get_language_strings(lang_code)
    value = strings.get(key, DEFAULT_STRINGS["en"].get(key, key))
    if args:
        try:
            return value.format(*args)
        except (IndexError, KeyError, ValueError):
            return value
    return value
