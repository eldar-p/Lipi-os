"""Print the current date/time."""
from datetime import datetime


def run(args):
    now = datetime.now().astimezone()
    return now.strftime("%a %b %d %H:%M:%S %Z %Y")
