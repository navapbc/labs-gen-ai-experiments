import functools
import importlib
import inspect
import logging
import pkgutil
import pprint
import textwrap
import time


def timer(func):
    module = inspect.getmodule(func)
    if module:
        logger = logging.getLogger(module.__name__)
    else:
        logger = logging.getLogger(f"chatbot.{func.__name__}")

    @functools.wraps(func)
    def wrapper_timer(*args, **kwargs):
        tic = time.perf_counter()
        value = func(*args, **kwargs)
        toc = time.perf_counter()
        elapsed_time = toc - tic
        logger.info("%s ran in %.1f seconds", func.__name__, elapsed_time)
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
            logger.info("%s ran in %.1f seconds", func.__name__, elapsed_time)
            logger.debug("%s returned: \n%s", func.__name__, textwrap.indent(pprint.pformat(value, indent=2), "  "))
            return value

        return wrapper_timer

    return timer_decorator


def scan_modules(ns_pkg):
    # From https://packaging.python.org/en/latest/guides/creating-and-discovering-plugins/#using-namespace-packages
    itr = pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")
    return {name: import_module_if_possible(name) for _, name, _ in itr}


def import_module_if_possible(name):
    try:
        return importlib.import_module(name)
    except ImportError:
        # logging.warning("Could not import module: %s", name)
        return None
