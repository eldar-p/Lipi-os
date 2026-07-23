"""Minimal window toolkit for Lipi OS (Tkinter-based)."""
from __future__ import annotations

import tkinter as tk

from i18n import get_language_strings


class LipiWindow:
    """A simple framed window.

    When ``master`` is provided, opens as a Toplevel of an existing root
    (required when launching apps from the desktop). Otherwise creates Tk().
    """

    def __init__(
        self,
        title: str = "Lipi App",
        width: int = 600,
        height: int = 400,
        master=None,
    ):
        if master is not None:
            self.root = tk.Toplevel(master)
            self._owns_mainloop = False
        else:
            self.root = tk.Tk()
            self._owns_mainloop = True

        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(True, True)

        self.lang = get_language_strings()

        self.title_bar = tk.Frame(self.root, bg="#2e2e2e", relief="raised", bd=0)
        self.title_bar.pack(fill=tk.X)

        self.title_label = tk.Label(
            self.title_bar,
            text=title,
            bg="#2e2e2e",
            fg="white",
            font=("Segoe UI", 10, "bold"),
        )
        self.title_label.pack(side=tk.LEFT, padx=5)

        self.close_btn = tk.Button(
            self.title_bar,
            text="✕",
            bg="#ff5f57",
            fg="white",
            bd=0,
            width=3,
            command=self.close,
        )
        self.close_btn.pack(side=tk.RIGHT)

        self.content = tk.Frame(self.root, bg="white")
        self.content.pack(fill=tk.BOTH, expand=True)

        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)

        self._drag_x = 0
        self._drag_y = 0

    def close(self) -> None:
        self.root.destroy()

    def start_move(self, event) -> None:
        self._drag_x = event.x
        self._drag_y = event.y

    def stop_move(self, event) -> None:
        self._drag_x = 0
        self._drag_y = 0

    def do_move(self, event) -> None:
        deltax = event.x - self._drag_x
        deltay = event.y - self._drag_y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")

    def add_label(self, text, row=0, col=0, **kwargs):
        label = tk.Label(self.content, text=text, bg="white", **kwargs)
        label.grid(row=row, column=col, sticky="w", padx=10, pady=5)
        return label

    def add_button(self, text, command, row=0, col=0, **kwargs):
        btn = tk.Button(self.content, text=text, command=command, **kwargs)
        btn.grid(row=row, column=col, padx=5, pady=5)
        return btn

    def add_entry(self, row=0, col=0, **kwargs):
        entry = tk.Entry(self.content, **kwargs)
        entry.grid(row=row, column=col, padx=5, pady=5)
        return entry

    def mainloop(self) -> None:
        if self._owns_mainloop:
            self.root.mainloop()
        else:
            # Child window: wait until closed without nesting another mainloop
            self.root.transient(self.root.master)
            self.root.grab_set()
            self.root.wait_window()


if __name__ == "__main__":
    win = LipiWindow("Lipi OS", 500, 300)
    win.add_label("Welcome to Lipi OS!", row=0, col=0)
    win.add_button("Close", win.close, row=1, col=0)
    win.mainloop()
