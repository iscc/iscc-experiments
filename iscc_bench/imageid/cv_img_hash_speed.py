# -*- coding: utf-8 -*-
"""Testing speed of OpenCV image hashes

Results:

"""
import time
import cv2 as cv
from iscc_bench.readers.ukbench import ukbench
import itertools


def speed_test():
    """Test OpenCV image hashing speeds"""
    hash_funcs = (
        cv.img_hash.averageHash,
        cv.img_hash.pHash,
        cv.img_hash.blockMeanHash,
        cv.img_hash.colorMomentHash,
        cv.img_hash.marrHildrethHash,
        cv.img_hash.radialVarianceHash
    )

    test_size = 1000

    for hfunc in hash_funcs:
        start = time.time()
        for img_path in itertools.islice(ukbench(), test_size):
            img = cv.imread(img_path)
            ih = hfunc(img)
        end = time.time()
        print(f'Runtime {end - start} for {hfunc.__name__}')


if __name__ == '__main__':
    speed_test()
