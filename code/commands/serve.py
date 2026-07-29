"""Tiny static HTTP server (for HTML projects)."""
import http.server
import socketserver
import threading
from pathlib import Path

def run(args):
    port = 8080
    directory = Path(".")
    if args:
        if args[0].isdigit():
            port = int(args[0])
            if len(args) > 1:
                directory = Path(args[1])
        else:
            directory = Path(args[0])
            if len(args) > 1 and args[1].isdigit():
                port = int(args[1])
    directory = directory.resolve()
    handler = http.server.SimpleHTTPRequestHandler
    class Handler(handler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=str(directory), **k)
    try:
        httpd = socketserver.TCPServer(("0.0.0.0", port), Handler)
    except OSError as e:
        return f"serve: {e}"
    print(f"Serving {directory} on http://127.0.0.1:{port}/  (Ctrl+C to stop)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.shutdown()
        return "stopped"
    return ""
