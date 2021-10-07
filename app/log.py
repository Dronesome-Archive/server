import logging


def warn(*args):
    logging.getLogger().warning(' '.join([str(arg) for arg in args]))


def info(*args):
    logging.getLogger().info(' '.join([str(arg) for arg in args]))
