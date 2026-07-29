import getpass
def run(args):
    try:
        return getpass.getuser()
    except Exception as e:
        return str(e)
