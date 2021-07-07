import logging
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure


def conn_exception(logger):
    def conn_decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)

            except ServerSelectionTimeoutError as servererr:
                logger.error('MongoDB server failed to respond for '.format(func.__name__))
                logger.error(servererr)
            except RuntimeError as err:
                logger.critical(err)
        return wrapper
    return conn_decorator
