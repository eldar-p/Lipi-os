import shutil
from pathlib import Path
def run(args):
    path = Path(args[0]) if args else Path(".")
    try:
        u = shutil.disk_usage(path)
    except OSError as e:
        return f"df: {e}"
    def gb(n): return f"{n / (1024**3):.2f}G"
    return f"Filesystem for {path.resolve()}\n  total={gb(u.total)} used={gb(u.used)} free={gb(u.free)}"
