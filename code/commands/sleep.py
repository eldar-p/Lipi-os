import time
def run(args):
    if not args:
        return "Usage: sleep <seconds>"
    try:
        time.sleep(float(args[0]))
    except ValueError:
        return "sleep: invalid time"
    return ""
