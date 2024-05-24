import pprint
import functools
import time
import textwrap
import logging


def timer(func):
    logger = logging.getLogger(func.__name__)

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        logger.info("ran in %.4f seconds", elapsed_time)
        return value

    return wrapper_timer


# https://stackoverflow.com/a/10176276/23458508
def verbose_timer(logger):
    def timer_decorator(func):
        @functools.wraps(func)
        def wrapper_timer(*args, **kwargs):
            tic = time.perf_counter()
            value = func(*args, **kwargs)
            toc = time.perf_counter()
            elapsed_time = toc - tic
            logger.info("%s ran in %.4f seconds", func.__name__, elapsed_time)
            logger.debug("%s returned: \n%s", func.__name__, textwrap.indent(pprint.pformat(value, indent=2), "  "))
            return value

        return wrapper_timer

    return timer_decorator
