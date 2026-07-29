"""Lightweight IDE for Lipi OS — file tree + editor + run output."""
from __future__ import annotations

import subprocess
import sys
import threading
from pathlib import Path

_CODE = Path(__file__).resolve().parents[2]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from sdk import run_app_main


LANG_BY_EXT = {
    ".py": "python",
    ".js": "javascript",
    ".c": "c",
    ".cpp": "cpp",
    ".cc": "cpp",
    ".rs": "rust",
    ".cs": "cs",
    ".asm": "asm",
    ".s": "asm",
}


def run_gui(start_dir: str | None = None) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext, ttk

    root = tk.Tk()
    root.title("Lipi IDE")
    root.geometry("1000x640")

    project = {"dir": Path(start_dir).resolve() if start_dir else Path.cwd()}
    current_file: dict[str, Path | None] = {"path": None}

    paned = ttk.Panedwindow(root, orient=tk.HORIZONTAL)
    paned.pack(fill=tk.BOTH, expand=True)

    left = ttk.Frame(paned, width=220)
    right = ttk.Frame(paned)
    paned.add(left, weight=1)
    paned.add(right, weight=4)

    tk.Label(left, text="Project").pack(anchor="w", padx=4, pady=4)
    tree = ttk.Treeview(left, show="tree")
    tree.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)

    editor = scrolledtext.ScrolledText(right, wrap=tk.NONE, font=("Consolas", 12))
    editor.pack(fill=tk.BOTH, expand=True)

    output = scrolledtext.ScrolledText(right, height=10, wrap=tk.WORD, font=("Consolas", 10))
    output.pack(fill=tk.BOTH, expand=False)

    status = tk.StringVar(value="No file")
    tk.Label(root, textvariable=status, anchor="w").pack(fill=tk.X)

    def log(msg: str) -> None:
        output.insert(tk.END, msg + "\n")
        output.see(tk.END)

    def refresh_tree() -> None:
        tree.delete(*tree.get_children())
        root_id = tree.insert("", "end", text=str(project["dir"].name), open=True)
        try:
            entries = sorted(project["dir"].iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as e:
            log(f"Error: {e}")
            return
        for entry in entries:
            if entry.name.startswith(".") or entry.name == "__pycache__":
                continue
            tree.insert(root_id, "end", text=entry.name, values=(str(entry),))

    def open_path(path: Path) -> None:
        if path.is_dir():
            return
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            messagebox.showerror("Open", str(e))
            return
        editor.delete("1.0", tk.END)
        editor.insert("1.0", content)
        current_file["path"] = path
        status.set(str(path))
        root.title(f"{path.name} — Lipi IDE")

    def on_tree_open(_event=None) -> None:
        sel = tree.selection()
        if not sel:
            return
        vals = tree.item(sel[0], "values")
        if not vals:
            return
        open_path(Path(vals[0]))

    def save_file() -> None:
        path = current_file["path"]
        if path is None:
            picked = filedialog.asksaveasfilename(initialdir=str(project["dir"]))
            if not picked:
                return
            path = Path(picked)
            current_file["path"] = path
        path.write_text(editor.get("1.0", "end-1c"), encoding="utf-8")
        status.set(f"Saved {path}")
        refresh_tree()

    def open_folder() -> None:
        picked = filedialog.askdirectory(initialdir=str(project["dir"]))
        if not picked:
            return
        project["dir"] = Path(picked)
        current_file["path"] = None
        editor.delete("1.0", tk.END)
        refresh_tree()
        status.set(str(project["dir"]))

    def run_code() -> None:
        path = current_file["path"]
        if path is None:
            messagebox.showinfo("Run", "Open a file first")
            return
        save_file()
        code = path.read_text(encoding="utf-8", errors="replace")
        lang = LANG_BY_EXT.get(path.suffix.lower())
        output.delete("1.0", tk.END)
        log(f"Running {path.name} ({lang or 'unknown'})…")

        def worker():
            if lang == "python":
                proc = subprocess.run(
                    [sys.executable, str(path)],
                    cwd=str(path.parent),
                    capture_output=True,
                    text=True,
                )
                text = (proc.stdout or "") + (proc.stderr or "")
                root.after(0, lambda: log(text or f"(exit {proc.returncode})"))
                return
            if lang == "javascript":
                proc = subprocess.run(
                    ["node", str(path)],
                    cwd=str(path.parent),
                    capture_output=True,
                    text=True,
                )
                text = (proc.stdout or "") + (proc.stderr or "")
                root.after(0, lambda: log(text or f"(exit {proc.returncode})"))
                return
            if lang:
                try:
                    from core.compiler_hub import compile_and_run

                    ok, result = compile_and_run(lang, code)
                    root.after(0, lambda: log(("OK\n" if ok else "FAIL\n") + result))
                except Exception as e:
                    root.after(0, lambda: log(f"Error: {e}"))
                return
            root.after(0, lambda: log("No runner for this file type"))

        threading.Thread(target=worker, daemon=True).start()

    menubar = tk.Menu(root)
    file_m = tk.Menu(menubar, tearoff=0)
    file_m.add_command(label="Open Folder…", command=open_folder)
    file_m.add_command(label="Save", command=save_file, accelerator="Ctrl+S")
    file_m.add_separator()
    file_m.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_m)
    run_m = tk.Menu(menubar, tearoff=0)
    run_m.add_command(label="Run current file", command=run_code, accelerator="F5")
    menubar.add_cascade(label="Run", menu=run_m)
    root.config(menu=menubar)
    root.bind("<Control-s>", lambda e: save_file())
    root.bind("<F5>", lambda e: run_code())
    tree.bind("<Double-1>", on_tree_open)

    refresh_tree()
    root.mainloop()


def run_cli(start_dir: str | None = None) -> None:
    print("Lipi IDE (CLI)")
    print("Commands: ls | open <file> | edit (prints path tip) | run <file> | cd <dir> | q")
    cwd = Path(start_dir).resolve() if start_dir else Path.cwd()
    while True:
        try:
            line = input(f"ide:{cwd}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line or line in ("q", "quit", "exit"):
            break
        if line == "ls":
            for p in sorted(cwd.iterdir()):
                print(("d " if p.is_dir() else "f ") + p.name)
            continue
        if line.startswith("cd "):
            target = (cwd / line[3:].strip()).resolve()
            if target.is_dir():
                cwd = target
            else:
                print("Not a directory")
            continue
        if line.startswith("open ") or line.startswith("run "):
            path = (cwd / line.split(maxsplit=1)[1]).resolve()
            if not path.exists():
                print("File not found")
                continue
            if line.startswith("open "):
                print(path.read_text(encoding="utf-8", errors="replace"))
                continue
            lang = LANG_BY_EXT.get(path.suffix.lower())
            if lang == "python":
                subprocess.call([sys.executable, str(path)], cwd=str(path.parent))
            elif lang == "javascript":
                subprocess.call(["node", str(path)], cwd=str(path.parent))
            elif lang:
                from core.compiler_hub import compile_and_run

                ok, result = compile_and_run(lang, path.read_text(encoding="utf-8", errors="replace"))
                print(("OK\n" if ok else "FAIL\n") + result)
            else:
                print("Unsupported type")
            continue
        print("Unknown command")


if __name__ == "__main__":
    arg = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    if "--cli" in sys.argv:
        run_cli(arg)
    else:
        try:
            run_gui(arg)
        except Exception:
            run_cli(arg)
