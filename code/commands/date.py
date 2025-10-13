from datetime import datetime

def run(args):
    return datetime.now().strftime("%a %b %d %H:%M:%S %Z %Y")
