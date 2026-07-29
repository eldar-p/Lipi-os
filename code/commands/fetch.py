"""Fetch URL and print text body."""
from urllib.request import Request, urlopen

def run(args):
    if not args:
        return "Usage: fetch <url>"
    url = args[0]
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    try:
        req = Request(url, headers={"User-Agent": "LipiOS/8"})
        with urlopen(req, timeout=30) as resp:
            data = resp.read(200_000)
            charset = resp.headers.get_content_charset() or "utf-8"
        return data.decode(charset, errors="replace")
    except Exception as e:
        return f"fetch: {e}"
