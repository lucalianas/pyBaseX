import logging

LOG_FORMAT = '%(asctime)s|%(levelname)-8s|%(message)s'
LOG_DATEFMT = '%Y-%m-%d %H:%M:%S'


def get_logger(name, log_level='INFO', log_file=None, mode='a'):
    logger = logging.getLogger(name)
    try:
        log_level = getattr(logging, log_level)
    except AttributeError:
        raise ValueError('unsupported literal log level: %s' % log_level)
    logger.setLevel(log_level)
    # clear existing handlers
    logger.handlers = []
    if log_file:
        handler = logging.FileHandler(log_file, mode=mode)
    else:
        handler = logging.StreamHandler()
    formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATEFMT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
