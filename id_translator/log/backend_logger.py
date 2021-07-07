import logging
import os

LOGFILE = "/tmp/idtranslator/backend.log"

def create_logger():
    """
    Creates a logging object and returns it
    """
    logger = logging.getLogger("backend_logger")
    logger.setLevel(logging.DEBUG)

    try:
        # create the logging file handler
        fh = logging.FileHandler(r'{}'.format(LOGFILE))
    except FileNotFoundError:
        os.mkdir('/tmp/idtranslator')

        fh = logging.FileHandler(r'{}'.format(LOGFILE))

    fmt = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(fmt)
    fh.setFormatter(formatter)

    fh.setLevel(logging.DEBUG)

    # add handler to logger object
    logger.addHandler(fh)
    return logger


logger = create_logger()
