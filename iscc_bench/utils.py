# -*- coding: utf-8 -*-
import contextlib
import io
import os
import time
from datetime import datetime
from functools import lru_cache


def timing(func):
    """Decorator to measure and print runtime of a function"""

    def wrap(*args):
        start = time.time()
        ret = func(*args)
        end = time.time()
        print(f"{func.__name__} function took {(end - start) * 1000.0:.3f} ms\n")
        return ret

    return wrap


@lru_cache(maxsize=500)
def load_text_file(fp):
    return open(fp, "r", encoding="utf8").read()


def stream_binary(f):
    """
    Create a data stream from a file path (str), raw bytes, or stream.
    """
    if isinstance(f, str):
        return open(f, "rb")

    if isinstance(f, bytes):
        return io.BytesIO(f)

    if hasattr(f, "read"):
        if hasattr(f, "seek"):
            f.seek(0)
        return f


class cd:
    """Context manager for changing the current working directory"""

    def __init__(self, newPath):
        self.newPath = os.path.expanduser(newPath)

    def __enter__(self):
        self.savedPath = os.getcwd()
        os.chdir(self.newPath)

    def __exit__(self, etype, value, traceback):
        os.chdir(self.savedPath)


@contextlib.contextmanager
def record_time():
    try:
        start_time = datetime.now()
        yield
    finally:
        print(datetime.now() - start_time)
