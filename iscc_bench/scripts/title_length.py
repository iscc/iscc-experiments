# -*- coding: utf-8 -*-
"""Script to measure basic title length statisics"""
import unicodedata
from itertools import cycle
import numpy as np
from iscc_bench.readers import ALL_READERS


def iter_titles():
    """Iterate over titles"""
    readers = [r() for r in ALL_READERS]
    for reader in cycle(readers):
        meta = next(reader)
        yield meta.title


def reject_outliers(data, m=2.0):
    """Remove outliers from data."""
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d / mdev if mdev else 0.0
    return data[s < m]


def check_subtitles():
    readers = [r() for r in ALL_READERS]
    for reader in cycle(readers):
        meta = next(reader)
        if " : " in meta.title:
            print(reader.__name__, meta.title)


if __name__ == "__main__":
    SAMPLE_SIZE = 100000

    title_sizes = []
    title_sizes_bytes = []
    for n, title in enumerate(iter_titles()):
        norm_title = unicodedata.normalize("NFKC", title)
        title_sizes.append(len(norm_title))
        title_sizes_bytes.append(len(norm_title.encode("utf-8")))
        if n > SAMPLE_SIZE:
            break

    data = np.array(title_sizes, dtype=np.uint16)
    abs_max = max(data)
    print("Longest title in {} samples had {} chars.".format(SAMPLE_SIZE, abs_max))
    print(
        "Longest title in {} samples had {} bytes.".format(
            SAMPLE_SIZE, max(title_sizes_bytes)
        )
    )
    print("The mean title length of all titles is {} chars ".format(data.mean()))

    cleaned = reject_outliers(data)
    max_real = max(cleaned)
    print("The longest title without outliers is {} chars.".format(max_real))
    print("The mean title length without outliers is {} chars.".format(cleaned.mean()))
