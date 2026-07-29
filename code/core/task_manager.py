"""Lipi OS task manager (CLI + GUI)."""
from __future__ import annotations

import os
import sys

from i18n import get_language_strings

try:
    import psutil
except ImportError:  # pragma: no cover
    psutil = None


def _lang() -> dict:
    return get_language_strings()


def get_processes() -> list[dict]:
    """Return process info list. Requires psutil."""
    if psutil is None:
        return []

    import time

    # Prime cpu_percent counters, then wait so samples are meaningful
    procs = []
    for proc in psutil.process_iter(["pid"]):
        try:
            proc.cpu_percent(None)
            procs.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    time.sleep(0.15)

    processes = []
    for proc in procs:
        try:
            with proc.oneshot():
                cpu = float(proc.cpu_percent(None) or 0.0)
                mem = proc.memory_info()
                mem_mb = round(mem.rss / (1024 * 1024), 1) if mem else 0.0
                processes.append(
                    {
                        "pid": proc.pid,
                        "name": proc.name() or "Unknown",
                        "cpu": cpu,
                        "memory": mem_mb,
                    }
                )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue

    processes.sort(key=lambda p: p["cpu"], reverse=True)
    return processes


def terminate_process(pid: int) -> bool:
    if psutil is None:
        return False
    try:
        proc = psutil.Process(pid)
        # Refuse to kill the current Lipi process / init
        if pid in (0, 1) or pid == os.getpid():
            return False
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except psutil.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=3)
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        return False
    except Exception:
        return False


def print_table(processes: list[dict]) -> None:
    lang = _lang()
    print(f"\n{lang['title']}")
    print("-" * 70)
    print(f"{lang['pid']:<8} {lang['name']:<25} {lang['cpu']:<10} {lang['memory']}")
    print("-" * 70)
    for p in processes[:30]:
        print(f"{p['pid']:<8} {p['name']:<25} {p['cpu']:<10.1f} {p['memory']}")


def cli_mode() -> None:
    lang = _lang()
    if psutil is None:
        print("psutil is not installed. Run: pip install psutil")
        return

    while True:
        processes = get_processes()
        print_table(processes)
        print(f"\n{lang['help']}")
        user_input = input().strip()

        if user_input.lower() in ("q", "quit", "exit"):
            break

        if not user_input.isdigit():
            print(lang["invalid_pid"].format(user_input))
            continue

        pid = int(user_input)
        if terminate_process(pid):
            print(lang["killed"].format(pid))
        else:
            print(lang.get("process_not_found", lang["not_found"]).format(pid))


def create_gui_task_manager(master=None) -> None:
    try:
        from core.gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Run in CLI mode.")
        return cli_mode()

    if psutil is None:
        print("psutil is not installed. Run: pip install psutil")
        return

    lang = _lang()
    win = LipiWindow(lang["title"], 700, 500, master=master)
    from tkinter import END, Button, Entry, Label, Scrollbar, Text

    text_area = Text(win.content, wrap="none", font=("Courier", 10))
    scrollbar = Scrollbar(win.content, command=text_area.yview)
    text_area.config(yscrollcommand=scrollbar.set)
    text_area.grid(row=0, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
    scrollbar.grid(row=0, column=3, sticky="ns")

    Label(win.content, text=lang["terminate"], bg="white").grid(
        row=1, column=0, sticky="w", padx=5
    )
    pid_entry = Entry(win.content, width=10)
    pid_entry.grid(row=1, column=1, padx=5)

    def refresh() -> None:
        text_area.delete(1.0, END)
        processes = get_processes()
        header = f"{'PID':<8} {'Name':<25} {'CPU %':<10} {'Memory (MB)'}\n"
        header += "-" * 60 + "\n"
        text_area.insert(END, header)
        for p in processes[:50]:
            line = f"{p['pid']:<8} {p['name']:<25} {p['cpu']:<10.1f} {p['memory']}\n"
            text_area.insert(END, line)

    def kill_process() -> None:
        pid_str = pid_entry.get().strip()
        if not pid_str.isdigit():
            return
        if terminate_process(int(pid_str)):
            refresh()
            pid_entry.delete(0, END)

    Button(win.content, text=lang.get("kill", "Kill"), command=kill_process).grid(
        row=1, column=2, padx=5
    )
    Button(win.content, text=lang.get("refresh", "Refresh"), command=refresh).grid(
        row=2, column=0, pady=5
    )

    win.content.grid_rowconfigure(0, weight=1)
    win.content.grid_columnconfigure(0, weight=1)

    refresh()
    win.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_task_manager()
    else:
        cli_mode()
