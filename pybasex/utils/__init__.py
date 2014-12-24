import logging

LOG_FORMAT = '%(asctime)s|%(levelname)-8s|%(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'


def get_logger(name, level='INFO', file=None, mode='a', silent=False):
    # clean root logger
    _ = logging.getLogger()
    _.handlers = []
    # set logger now
    logger = logging.getLogger(name)
    try:
        level = getattr(logging, level)
    except AttributeError:
        raise ValueError('unsupported literal log level: %s' % level)
    logger.setLevel(level)
    # clear existing handlers
    logger.handlers = []
    if silent:
        handler = logging.NullHandler()
    else:
        if file:
            handler = logging.FileHandler(file, mode=mode)
        else:
            handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
