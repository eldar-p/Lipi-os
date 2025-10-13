# gui_engine.py
import tkinter as tk
from tkinter import ttk
import json
from pathlib import Path

class LipiWindow:
    def __init__(self, title="Lipi App", width=600, height=400):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(True, True)
        
        # Загрузка языка
        self.lang = self.load_language()
        
        # Стиль окна (имитация заголовка)
        self.title_bar = tk.Frame(self.root, bg="#2e2e2e", relief='raised', bd=0)
        self.title_bar.pack(fill=tk.X)
        
        self.title_label = tk.Label(
            self.title_bar, 
            text=title, 
            bg="#2e2e2e", 
            fg="white",
            font=("Segoe UI", 10, "bold")
        )
        self.title_label.pack(side=tk.LEFT, padx=5)
        
        # Кнопки управления
        self.close_btn = tk.Button(
            self.title_bar,
            text="✕",
            bg="#ff5f57",
            fg="white",
            bd=0,
            width=3,
            command=self.root.destroy
        )
        self.close_btn.pack(side=tk.RIGHT)
        
        # Область содержимого
        self.content = tk.Frame(self.root, bg="white")
        self.content.pack(fill=tk.BOTH, expand=True)
        
        # Перетаскивание окна
        self.title_bar.bind("<ButtonPress-1>", self.start_move)
        self.title_bar.bind("<ButtonRelease-1>", self.stop_move)
        self.title_bar.bind("<B1-Motion>", self.do_move)
        
        self.x = 0
        self.y = 0

    def load_language(self):
        config_path = Path("settings/config.json")
        lang = "en"
        if config_path.exists():
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                lang = config.get("language", "en")
        lang_file = Path(f"settings/lang/{lang}.json")
        if lang_file.exists():
            with open(lang_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
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

    def mainloop(self):
        self.root.mainloop()

# Пример использования
if __name__ == "__main__":
    win = LipiWindow("Lipi OS", 500, 300)
    win.add_label("Добро пожаловать в Lipi OS!", row=0, col=0)
    win.add_button("Закрыть", win.root.destroy, row=1, col=0)
    win.mainloop()
