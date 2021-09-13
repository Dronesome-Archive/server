from logging import getLogger


def warn(*args):
    getLogger().warning(' '.join([str(arg) for arg in args]))


def info(*args):
    getLogger().info(' '.join([str(arg) for arg in args]))
