"""Simple text editor for Lipi OS."""
from __future__ import annotations

import sys
from pathlib import Path

_CODE = Path(__file__).resolve().parents[2]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from sdk import run_app_main


def run_gui(initial: str | None = None) -> None:
    import tkinter as tk
    from tkinter import filedialog, messagebox, scrolledtext

    root = tk.Tk()
    root.title("Lipi Text Editor")
    root.geometry("800x560")

    current = {"path": Path(initial).resolve() if initial else None}

    text = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 12))
    text.pack(fill=tk.BOTH, expand=True)

    status = tk.StringVar(value="Untitled")
    tk.Label(root, textvariable=status, anchor="w").pack(fill=tk.X)

    def set_title() -> None:
        name = current["path"].name if current["path"] else "Untitled"
        root.title(f"{name} — Lipi Text Editor")
        status.set(str(current["path"]) if current["path"] else "Untitled")

    def open_file(path: Path | None = None) -> None:
        if path is None:
            picked = filedialog.askopenfilename(
                title="Open",
                filetypes=[("Text", "*.txt *.md *.py *.json *.cfg *.ini *"), ("All", "*.*")],
            )
            if not picked:
                return
            path = Path(picked)
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            messagebox.showerror("Open", str(e))
            return
        text.delete("1.0", tk.END)
        text.insert("1.0", content)
        current["path"] = path
        set_title()

    def save_as() -> None:
        picked = filedialog.asksaveasfilename(
            title="Save As",
            defaultextension=".txt",
            filetypes=[("Text", "*.txt"), ("Python", "*.py"), ("All", "*.*")],
        )
        if not picked:
            return
        current["path"] = Path(picked)
        save_file()

    def save_file() -> None:
        if current["path"] is None:
            save_as()
            return
        try:
            current["path"].write_text(text.get("1.0", tk.END), encoding="utf-8")
            set_title()
            status.set(f"Saved: {current['path']}")
        except OSError as e:
            messagebox.showerror("Save", str(e))

    menubar = tk.Menu(root)
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Open…", command=open_file, accelerator="Ctrl+O")
    file_menu.add_command(label="Save", command=save_file, accelerator="Ctrl+S")
    file_menu.add_command(label="Save As…", command=save_as)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)
    root.config(menu=menubar)

    root.bind("<Control-o>", lambda e: open_file())
    root.bind("<Control-s>", lambda e: save_file())

    if current["path"]:
        open_file(current["path"])
    else:
        set_title()

    root.mainloop()


def run_cli(initial: str | None = None) -> None:
    path = Path(initial) if initial else None
    if path is None:
        try:
            name = input("File path (empty = new buffer): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        path = Path(name) if name else None

    lines: list[str] = []
    if path and path.exists():
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        print(f"Loaded {path} ({len(lines)} lines)")
        print("Commands: .p print | .w write | .q quit | or type a line to append")
    else:
        print("New buffer. Commands: .p print | .w [path] write | .q quit")

    while True:
        try:
            line = input()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if line == ".q":
            break
        if line == ".p":
            print("\n".join(lines))
            continue
        if line.startswith(".w"):
            parts = line.split(maxsplit=1)
            target = Path(parts[1]) if len(parts) > 1 else path
            if target is None:
                print("Usage: .w <path>")
                continue
            target.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")
            path = target
            print(f"Wrote {target}")
            continue
        lines.append(line)


if __name__ == "__main__":
    file_arg = next((a for a in sys.argv[1:] if not a.startswith("-")), None)
    if "--cli" in sys.argv:
        run_cli(file_arg)
    else:
        try:
            run_gui(file_arg)
        except Exception:
            run_cli(file_arg)
