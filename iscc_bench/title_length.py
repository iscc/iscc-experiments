# -*- coding: utf-8 -*-
"""Script to measure title length statisics"""
from itertools import cycle
import numpy as np
from iscc_bench.readers import ALL_READERS


def iter_titles():
    """Iterate over titles"""
    readers = [r() for r in ALL_READERS]
    for reader in cycle(readers):
        meta = next(reader)
        yield meta.title


def reject_outliers(data, m=2.):
    """Remove outliers from data."""
    d = np.abs(data - np.median(data))
    mdev = np.median(d)
    s = d/mdev if mdev else 0.
    return data[s < m]


if __name__ == '__main__':

    SAMPLE_SIZE = 1000000

    title_sizes = []
    for n, title in enumerate(iter_titles()):
        title_sizes.append(len(title))
        if n > SAMPLE_SIZE:
            break

    data = np.array(title_sizes, dtype=np.uint16)
    abs_max = max(data)
    print('Longest title in {} samples had {} chars.'.format(SAMPLE_SIZE, abs_max))
    print('The mean title length of all titles is {} chars '.format(data.mean()))

    cleaned = reject_outliers(data)
    max_real = max(cleaned)
    print('The longest title without outliers is {} chars.'.format(max_real))
    print('The mean title length without outliers is {} chars.'.format(cleaned.mean()))

