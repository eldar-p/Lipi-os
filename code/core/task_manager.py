# task_manager.py
import os
import sys
import json
import psutil
from pathlib import Path

# ======================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ======================

def load_language():
    """Загружает язык из настроек"""
    config_path = Path("settings/config.json")
    lang_code = "en"
    if config_path.exists():
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                lang_code = config.get("language", "en")
        except Exception:
            pass

    lang_file = Path(f"settings/lang/{lang_code}.json")
    fallback = {
        "title": "Task Manager",
        "pid": "PID",
        "name": "Name",
        "cpu": "CPU %",
        "memory": "Memory (MB)",
        "terminate": "Terminate PID:",
        "killed": "Process {} terminated.",
        "not_found": "Process with PID {} not found.",
        "invalid_pid": "Invalid PID: {}",
        "help": "Enter PID to kill or 'q' to quit."
    }

    if lang_file.exists():
        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                lang = json.load(f)
                # Дополняем недостающие ключи из fallback
                for key in fallback:
                    if key not in lang:
                        lang[key] = fallback[key]
                return lang
        except Exception:
            pass
    return fallback

LANG = load_language()

def get_processes():
    """Возвращает список словарей с информацией о процессах"""
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            # Запрашиваем данные дважды для точности 
            proc.cpu_percent()  # первый вызов 
            # пауза не нужна в CLI, но для GUI можно добавить задержку
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    # Второй проход — получаем реальные значения
    for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info']):
        try:
            pid = proc.info['pid']
            name = proc.info['name'] or "Unknown"
            cpu = proc.info['cpu_percent'] or 0.0
            mem_mb = round((proc.info['memory_info'].rss / (1024 * 1024)), 1) if proc.info['memory_info'] else 0.0
            processes.append({
                'pid': pid,
                'name': name,
                'cpu': cpu,
                'memory': mem_mb
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return processes

def terminate_process(pid):
    """Завершает процесс по PID"""
    try:
        proc = psutil.Process(pid)
        proc.terminate()  # graceful
        proc.wait(timeout=3)
        return True
    except psutil.NoSuchProcess:
        return False
    except psutil.TimeoutExpired:
        try:
            proc.kill()  # принудительно
            return True
        except:
            return False
    except Exception:
        return False

# ======================
# CLI-РЕЖИМ (по умолчанию)
# ======================

def print_table(processes):
    """Печатает таблицу процессов в консоль"""
    print(f"\n{LANG['title']}")
    print("-" * 70)
    print(f"{LANG['pid']:<8} {LANG['name']:<25} {LANG['cpu']:<10} {LANG['memory']}")
    print("-" * 70)
    for p in processes[:30]:  # ограничим для читаемости
        print(f"{p['pid']:<8} {p['name']:<25} {p['cpu']:<10.1f} {p['memory']}")

def cli_mode():
    """Запуск диспетчера задач в консоли"""
    while True:
        processes = get_processes()
        print_table(processes)
        print(f"\n{LANG['help']}")
        user_input = input().strip()

        if user_input.lower() in ('q', 'quit', 'exit'):
            break

        if not user_input.isdigit():
            print(LANG['invalid_pid'].format(user_input))
            continue

        pid = int(user_input)
        if terminate_process(pid):
            print(LANG['killed'].format(pid))
        else:
            print(LANG['not_found'].format(pid))

# ======================
# GUI-РЕЖИМ (опционально)
# ======================

def create_gui_task_manager():
    """Создаёт GUI-версию через LipiWindow (если gui_engine.py доступен)"""
    try:
        from gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Run in CLI mode.")
        return cli_mode()

    win = LipiWindow(LANG['title'], 700, 500)

    # Создаём таблицу в виджете 
    from tkinter import Text, Scrollbar, END, Button, Entry, Label

    text_area = Text(win.content, wrap="none", font=("Courier", 10))
    scrollbar = Scrollbar(win.content, command=text_area.yview)
    text_area.config(yscrollcommand=scrollbar.set)

    text_area.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
    scrollbar.grid(row=0, column=3, sticky="ns")

    # Поле ввода PID
    Label(win.content, text=LANG['terminate'], bg="white").grid(row=1, column=0, sticky="w", padx=5)
    pid_entry = Entry(win.content, width=10)
    pid_entry.grid(row=1, column=1, padx=5)

    def refresh():
        text_area.delete(1.0, END)
        processes = get_processes()
        header = f"{'PID':<8} {'Name':<25} {'CPU %':<10} {'Memory (MB)'}\n"
        header += "-" * 60 + "\n"
        text_area.insert(END, header)
        for p in processes[:50]:
            line = f"{p['pid']:<8} {p['name']:<25} {p['cpu']:<10.1f} {p['memory']}\n"
            text_area.insert(END, line)

    def kill_process():
        pid_str = pid_entry.get().strip()
        if not pid_str.isdigit():
            return
        pid = int(pid_str)
        if terminate_process(pid):
            refresh()
            pid_entry.delete(0, END)

    Button(win.content, text="Kill", command=kill_process).grid(row=1, column=2, padx=5)
    Button(win.content, text="Refresh", command=refresh).grid(row=2, column=0, pady=5)

    # Настройка растягивания
    win.content.grid_rowconfigure(0, weight=1)
    win.content.grid_columnconfigure(0, weight=1)

    refresh()
    win.mainloop()

# ======================
# ТОЧКА ВХОДА
# ======================

if __name__ == "__main__":
    # Если запущен напрямую — CLI
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_task_manager()
    else:
        cli_mode()
