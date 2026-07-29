import time
def run(args):
    try:
        import psutil
        boot = psutil.boot_time()
        sec = int(time.time() - boot)
        d, rem = divmod(sec, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        return f"up {d}d {h}h {m}m {s}s"
    except Exception as e:
        return f"uptime: {e}"
