"""Show basic network interfaces / addresses."""
def run(args):
    try:
        import psutil
        lines = []
        for name, addrs in psutil.net_if_addrs().items():
            for a in addrs:
                if getattr(a, "family", None) and "AF_INET" in str(a.family):
                    lines.append(f"{name}: {a.address}")
        stats = psutil.net_io_counters()
        lines.append(f"bytes_sent={stats.bytes_sent} bytes_recv={stats.bytes_recv}")
        return "\n".join(lines) if lines else "no interfaces"
    except Exception as e:
        return f"netinfo: {e}"
