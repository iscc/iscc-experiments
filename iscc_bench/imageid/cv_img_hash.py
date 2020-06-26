# -*- coding: utf-8 -*-
"""Evaluating OpenCV image hashes

Results:

Runtime  4.67 for pHash
Runtime  4.98 for averageHash
Runtime  5.46 for blockMeanHash
Runtime  5.49 for radialVarianceHash
Runtime  7.44 for colorMomentHash
Runtime 10.00 for marrHildrethHash

pHash: Collisions: 0 - Mean: 1 - Median: 1.0 - Min 1 - Max 1
averageHash: Collisions: 4 - Mean: 1.00078 - Median: 1.0 - Min 1 - Max 6
blockMeanHash: Collisions: 0 - Mean: 1 - Median: 1.0 - Min 1 - Max 1
radialVarianceHash: Collisions: 0 - Mean: 1 - Median: 1.0 - Min 1 - Max 1
colorMomentHash: Collisions: 0 - Mean: 1 - Median: 1.0 - Min 1 - Max 1
marrHildrethHash: Collisions: 0 - Mean: 1 - Median: 1.0 - Min 1 - Max 1

ahash, phash implementations of OpenCV and ImageHash are not compatible

"""
import os
import time
from collections import defaultdict
import cv2 as cv
from tqdm import tqdm
from iscc_bench.readers.ukbench import ukbench
import itertools
from statistics import *


hash_funcs = (
    cv.img_hash.averageHash,
    cv.img_hash.pHash,
    cv.img_hash.blockMeanHash,
    cv.img_hash.colorMomentHash,
    cv.img_hash.marrHildrethHash,
    cv.img_hash.radialVarianceHash,
)


def speed():
    """Test the speed of the various image hashing functions"""

    test_size = 1000

    for hfunc in hash_funcs:
        start = time.time()
        for img_path in itertools.islice(ukbench(), test_size):
            img = cv.imread(img_path)
            ih = hfunc(img)
        end = time.time()
        print(f"Runtime {end - start} for {hfunc.__name__}")


def collisions():
    """Test number of collisions in ukbench image set"""

    for hfunc in hash_funcs:
        img_hashes = defaultdict(list)

        for img_path in tqdm(ukbench(), total=10200, leave=False):
            img = cv.imread(img_path)
            img_hash = tuple(hfunc(img).flatten())
            img_hashes[img_hash].append(os.path.basename(img_path))
        print()
        matches = 0
        ncol = []
        for k, v in img_hashes.items():
            if len(v) > 1:
                matches += 1
            ncol.append(len(v))
        print(
            f"\n{hfunc.__name__}: "
            f"Collisions: {matches} - "
            f"Mean: {mean(ncol)} - "
            f"Median: {median(ncol)} - "
            f"Min {min(ncol)} - "
            f"Max {max(ncol)}"
        )


def compat():
    """Test for compat with ImageHash Lib"""
    from PIL import Image
    import imagehash

    img_path = list(ukbench())[0]
    img = cv.imread(img_path)
    avg_hash_cv = cv.img_hash.averageHash(img)
    avg_hash_ih = imagehash.average_hash(Image.open(img_path))

    print(avg_hash_cv.flatten())
    print(list(bytearray.fromhex(str(avg_hash_ih))))

    phash_cv = cv.img_hash.pHash(img)
    phash_ih = imagehash.phash(Image.open(img_path))

    print(phash_cv.flatten())
    print(list(bytearray.fromhex(str(phash_ih))))


if __name__ == "__main__":
    speed()
    collisions()
    compat()
