"""Console / terminal app for Lipi OS."""
from __future__ import annotations

import os
import subprocess
import sys
import threading
from pathlib import Path

_CODE = Path(__file__).resolve().parents[2]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from sdk import run_app_main


def _run_line(line: str, cwd: Path) -> tuple[str, Path]:
    """Execute one line via Lipi shell builtins when possible, else host shell."""
    line = line.strip()
    if not line:
        return "", cwd

    # Prefer Lipi shell so `ls`, `apps`, `open` work the same as CLI mode
    try:
        from core.shell import run_command

        # cd must affect our tracked cwd
        if line.startswith("cd ") or line == "cd":
            os.chdir(str(cwd))
            out = run_command(line) or ""
            return out, Path(os.getcwd())
        os.chdir(str(cwd))
        out = run_command(line)
        return (out or ""), Path(os.getcwd())
    except Exception:
        pass

    # Fallback: host shell
    try:
        proc = subprocess.run(
            line,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
        )
        text = (proc.stdout or "") + (proc.stderr or "")
        return text.rstrip("\n"), cwd
    except OSError as e:
        return f"error: {e}", cwd


def run_gui() -> None:
    import tkinter as tk
    from tkinter import scrolledtext

    root = tk.Tk()
    root.title("Lipi Console")
    root.geometry("860x520")
    root.configure(bg="#0f0f1b")

    state = {"cwd": Path.cwd()}

    out = scrolledtext.ScrolledText(
        root,
        wrap=tk.WORD,
        font=("Consolas", 11),
        bg="#0f0f1b",
        fg="#d7ffe0",
        insertbackground="#d7ffe0",
    )
    out.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
    out.insert(tk.END, "Lipi Console — type Lipi or system commands. `exit` closes.\n")
    out.insert(tk.END, f"{state['cwd']}$ ")
    out.mark_set("input_start", "insert")

    def write(text: str) -> None:
        out.insert(tk.END, text)
        out.see(tk.END)

    def on_enter(event=None):
        line = out.get("input_start", "end-1c")
        write("\n")
        cmd = line.strip()
        if cmd in ("exit", "quit"):
            root.destroy()
            return "break"
        if cmd == "clear":
            out.delete("1.0", tk.END)
            write(f"{state['cwd']}$ ")
            out.mark_set("input_start", "insert")
            return "break"

        def worker():
            # Interactive Lipi commands (settings/tasks/store/compile) need the UI thread.
            interactive = cmd.split(None, 1)[0].lower() in {
                "settings",
                "tasks",
                "store",
                "compile",
                "open",
            }
            if interactive:

                def run_interactive():
                    result, new_cwd = _run_line(cmd, state["cwd"])
                    state["cwd"] = new_cwd
                    if result:
                        write(result + "\n")
                    write(f"{state['cwd']}$ ")
                    out.mark_set("input_start", "insert")

                root.after(0, run_interactive)
                return

            result, new_cwd = _run_line(cmd, state["cwd"])
            state["cwd"] = new_cwd

            def done():
                if result:
                    write(result + "\n")
                write(f"{state['cwd']}$ ")
                out.mark_set("input_start", "insert")

            root.after(0, done)

        threading.Thread(target=worker, daemon=True).start()
        return "break"

    out.bind("<Return>", on_enter)
    out.focus_set()
    root.mainloop()


def run_cli() -> None:
    from core.shell import start_shell

    print("Lipi Console (CLI) — starting Lipi shell…")
    start_shell()


if __name__ == "__main__":
    run_app_main(run_gui, run_cli)
