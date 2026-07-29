"""Download a URL to a file (curl/wget-like)."""
from pathlib import Path
from urllib.request import Request, urlopen

def run(args):
    if not args:
        return "Usage: download <url> [outfile]"
    url = args[0]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    out = Path(args[1]) if len(args) > 1 else Path(url.rstrip("/").split("/")[-1] or "download.bin")
    try:
        req = Request(url, headers={"User-Agent": "LipiOS/8"})
        with urlopen(req, timeout=60) as resp:
            data = resp.read()
        out.write_bytes(data)
        return f"Saved {len(data)} bytes → {out.resolve()}"
    except Exception as e:
        return f"download: {e}"
