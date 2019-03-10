# -*- coding: utf-8 -*-
"""Multilingual Text extractions from PDF/EPUB/MOBI

This is copyrighted text and is not provided publicly.
"""
import os
from iscc_bench import DATA_DIR
from iscc_bench.readers import utils

DATA_PATH = os.path.join(DATA_DIR, 'mltext')


def mltext():
    """Yield file paths to text files"""
    for fp in utils.iter_files(DATA_PATH, exts=['txt'], recursive=False):
        yield fp


if __name__ == '__main__':
    print(list(mltext()))
