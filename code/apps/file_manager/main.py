"""Simple file manager for Lipi OS."""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


class FileManager:
    def __init__(self, root):
        import tkinter as tk
        from tkinter import Listbox, Scrollbar

        self.tk = tk
        self.messagebox = __import__("tkinter.messagebox", fromlist=["messagebox"])

        self.root = root
        self.root.title("Lipi File Manager")
        self.root.geometry("700x450")
        self.path = Path.cwd().resolve()

        top = tk.Frame(root)
        top.pack(fill="x", padx=8, pady=8)

        self.path_var = tk.StringVar(value=str(self.path))
        tk.Entry(top, textvariable=self.path_var).pack(
            side="left", fill="x", expand=True, padx=(0, 8)
        )
        tk.Button(top, text="Go", command=self.go_path).pack(side="left", padx=2)
        tk.Button(top, text="Up", command=self.go_up).pack(side="left", padx=2)
        tk.Button(top, text="Refresh", command=self.refresh).pack(side="left", padx=2)

        body = tk.Frame(root)
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.listbox = Listbox(body, font=("Courier", 11))
        scroll = Scrollbar(body, command=self.listbox.yview)
        self.listbox.config(yscrollcommand=scroll.set)
        self.listbox.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.listbox.bind("<Double-Button-1>", self.open_selected)

        self.refresh()

    def go_path(self) -> None:
        target = Path(self.path_var.get()).expanduser()
        if target.exists() and target.is_dir():
            self.path = target.resolve()
            self.refresh()
        else:
            self.messagebox.showerror("File Manager", f"Not a directory: {target}")

    def go_up(self) -> None:
        self.path = self.path.parent
        self.refresh()

    def refresh(self) -> None:
        self.path_var.set(str(self.path))
        self.listbox.delete(0, self.tk.END)
        try:
            entries = sorted(self.path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError as e:
            self.messagebox.showerror("File Manager", str(e))
            return

        if self.path.parent != self.path:
            self.listbox.insert(self.tk.END, "../")

        for entry in entries:
            suffix = "/" if entry.is_dir() else ""
            self.listbox.insert(self.tk.END, entry.name + suffix)

    def open_selected(self, _event=None) -> None:
        sel = self.listbox.curselection()
        if not sel:
            return
        name = self.listbox.get(sel[0])
        if name == "../":
            self.go_up()
            return
        target = self.path / name.rstrip("/")
        if target.is_dir():
            self.path = target.resolve()
            self.refresh()
            return
        if target.suffix.lower() == ".py":
            subprocess.Popen([sys.executable, str(target)], cwd=str(target.parent))
        else:
            try:
                if os.name == "nt":
                    os.startfile(target)  # type: ignore[attr-defined]
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(target)])
                else:
                    subprocess.Popen(["xdg-open", str(target)])
            except Exception as e:
                self.messagebox.showinfo("File Manager", f"Selected: {target}\n{e}")


def run_cli() -> None:
    path = Path.cwd()
    print("Lipi File Manager (commands: ls, cd <dir>, up, open <name>, q)")
    while True:
        try:
            line = input(f"{path}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line or line in ("q", "quit", "exit"):
            break
        if line == "ls":
            for p in sorted(path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
                print(("  [dir] " if p.is_dir() else "  ") + p.name)
        elif line == "up":
            path = path.parent
        elif line.startswith("cd "):
            target = (path / line[3:].strip()).resolve()
            if target.is_dir():
                path = target
            else:
                print("Not a directory")
        elif line.startswith("open "):
            target = path / line[5:].strip()
            print(f"Selected: {target}")
        else:
            print("Unknown command")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        try:
            import tkinter as tk

            root = tk.Tk()
            FileManager(root)
            root.mainloop()
        except Exception:
            run_cli()
