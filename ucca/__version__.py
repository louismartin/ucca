VERSION = "1.2.3"
# noinspection PyBroadException
try:
    from subprocess import check_output, DEVNULL
    GIT_VERSION = check_output(["git", "describe", "--tags", "--always"], stderr=DEVNULL).decode().strip().lstrip("v")
except:
    GIT_VERSION = VERSION
