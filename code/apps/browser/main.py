"""Simple browser for Lipi OS — fetch URL, show text/HTML, open system browser."""
from __future__ import annotations

import html
import re
import sys
import threading
import urllib.error
import urllib.request
import webbrowser
from html.parser import HTMLParser
from pathlib import Path

_CODE = Path(__file__).resolve().parents[2]
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))

from sdk import run_app_main

USER_AGENT = "LipiBrowser/1.0 (+https://github.com/eldar-p/Lipi-os)"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._chunks: list[str] = []
        self._skip = False

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "noscript"):
            self._skip = True
        if tag in ("p", "div", "br", "li", "h1", "h2", "h3", "tr"):
            self._chunks.append("\n")
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self._chunks.append(f" [link:{href}] ")

    def handle_endtag(self, tag):
        if tag in ("script", "style", "noscript"):
            self._skip = False
        if tag in ("p", "div", "li", "h1", "h2", "h3"):
            self._chunks.append("\n")

    def handle_data(self, data):
        if not self._skip:
            self._chunks.append(data)

    def text(self) -> str:
        raw = "".join(self._chunks)
        raw = html.unescape(raw)
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def fetch_url(url: str, timeout: float = 15.0) -> tuple[str, str]:
    if not re.match(r"^https?://", url, re.I):
        url = "https://" + url
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        charset = resp.headers.get_content_charset() or "utf-8"
        data = resp.read()
        final = resp.geturl()
    text = data.decode(charset, errors="replace")
    return final, text


def html_to_text(document: str) -> str:
    parser = _TextExtractor()
    try:
        parser.feed(document)
        parser.close()
    except Exception:
        return document
    return parser.text() or document


def run_gui(start_url: str | None = None) -> None:
    import tkinter as tk
    from tkinter import messagebox, scrolledtext

    root = tk.Tk()
    root.title("Lipi Browser")
    root.geometry("920x640")

    top = tk.Frame(root)
    top.pack(fill=tk.X, padx=6, pady=6)

    url_var = tk.StringVar(value=start_url or "https://example.com")
    entry = tk.Entry(top, textvariable=url_var, font=("Segoe UI", 11))
    entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

    mode = tk.StringVar(value="text")
    body = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=("Consolas", 11))
    body.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)
    status = tk.StringVar(value="Ready")
    tk.Label(root, textvariable=status, anchor="w").pack(fill=tk.X)

    state = {"raw": "", "url": ""}

    def render() -> None:
        body.delete("1.0", tk.END)
        if mode.get() == "raw":
            body.insert("1.0", state["raw"])
        else:
            body.insert("1.0", html_to_text(state["raw"]))

    def navigate(url: str | None = None) -> None:
        url = (url or url_var.get()).strip()
        if not url:
            return
        status.set(f"Loading {url}…")
        body.delete("1.0", tk.END)

        def worker():
            try:
                final, document = fetch_url(url)
                state["raw"] = document
                state["url"] = final

                def done():
                    url_var.set(final)
                    render()
                    status.set(f"Loaded {final} ({len(document)} bytes)")

                root.after(0, done)
            except Exception as e:
                root.after(0, lambda: (status.set("Error"), messagebox.showerror("Browser", str(e))))

        threading.Thread(target=worker, daemon=True).start()

    def open_system() -> None:
        url = url_var.get().strip()
        if url:
            webbrowser.open(url)

    tk.Button(top, text="Go", command=navigate).pack(side=tk.LEFT, padx=4)
    tk.Button(top, text="Text", command=lambda: (mode.set("text"), render())).pack(side=tk.LEFT)
    tk.Button(top, text="HTML", command=lambda: (mode.set("raw"), render())).pack(side=tk.LEFT)
    tk.Button(top, text="System browser", command=open_system).pack(side=tk.LEFT, padx=4)

    entry.bind("<Return>", lambda e: navigate())
    if start_url:
        root.after(100, lambda: navigate(start_url))
    root.mainloop()


def run_cli(start_url: str | None = None) -> None:
    print("Lipi Browser (CLI)")
    print("Commands: go <url> | text | raw | open | q")
    state = {"raw": "", "url": start_url or ""}
    if start_url:
        try:
            final, document = fetch_url(start_url)
            state["url"], state["raw"] = final, document
            print(f"Loaded {final}")
            print(html_to_text(document)[:2000])
        except Exception as e:
            print(f"Error: {e}")

    while True:
        try:
            line = input("browser> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line or line in ("q", "quit", "exit"):
            break
        if line.startswith("go "):
            url = line[3:].strip()
            try:
                final, document = fetch_url(url)
                state["url"], state["raw"] = final, document
                print(f"Loaded {final} ({len(document)} bytes)")
            except Exception as e:
                print(f"Error: {e}")
            continue
        if line == "text":
            print(html_to_text(state["raw"])[:4000] or "(empty)")
            continue
        if line == "raw":
            print(state["raw"][:4000] or "(empty)")
            continue
        if line == "open":
            if state["url"]:
                webbrowser.open(state["url"])
                print(f"Opened {state['url']}")
            else:
                print("No URL loaded")
            continue
        print("Unknown command")


if __name__ == "__main__":
    arg = next((a for a in sys.argv[1:] if not a.startswith("-") and a != "--cli"), None)
    if "--cli" in sys.argv:
        run_cli(arg)
    else:
        try:
            run_gui(arg)
        except Exception:
            run_cli(arg)
