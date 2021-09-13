from logging import getLogger


def warn(*args):
    getLogger().warning(' '.join(args))


def info(*args):
    getLogger().info(' '.join(args))
