import os, subprocess, shutil
def run(args):
    if not args:
        return "Usage: ping <host>"
    host = args[0]
    count = "4"
    ping = shutil.which("ping")
    if not ping:
        return "ping: system ping not found"
    cmd = [ping, "-n" if os.name == "nt" else "-c", count, host]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return f"ping: {e}"
