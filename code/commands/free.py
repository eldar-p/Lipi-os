def run(args):
    try:
        import psutil
        v = psutil.virtual_memory()
        s = psutil.swap_memory()
        def m(n): return f"{n / 1024**2:.0f}M"
        return (f"Mem:  total={m(v.total)} used={m(v.used)} free={m(v.available)} ({v.percent}%)\n"
                f"Swap: total={m(s.total)} used={m(s.used)} free={m(s.free)}")
    except Exception as e:
        return f"free: {e} (needs psutil)"
