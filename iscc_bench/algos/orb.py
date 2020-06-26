# -*- coding: utf-8 -*-
"""Test similarity hashing of opencv ORB based vectors.

Notes: Requires opencv-python==3.4.0.12
"""
import logging
from hashlib import sha256
import cv2 as cv
from iscc_bench.algos.chroma import simhash, encode


log = logging.getLogger(__name__)


SPLIT_MIN_LOWEST = 10
HEAD_CID_I = b"\x12"


def generate_image_id(filepath):
    img = cv.imread(filepath, 0)
    orb = cv.ORB_create()
    kp, des = orb.detectAndCompute(img, None)
    hash_digests = tuple(v.tobytes() for v in des)
    splited_digests = []
    for h_dig in hash_digests:
        splited_digests.extend([h_dig[i : i + 8] for i in range(0, len(h_dig), 8)])
    splited_digests.sort()
    min_hash_digests = splited_digests[:SPLIT_MIN_LOWEST]
    # Rehash so we don´t clutter lower hash spaces
    rehashed = [sha256(h).digest() for h in min_hash_digests]
    simhash_digest = simhash(rehashed)
    image_id_digest = HEAD_CID_I + simhash_digest[:8]
    image_id_code = encode(image_id_digest)
    return image_id_code


if __name__ == "__main__":
    import os
    from iscc_bench.readers import caltech_101
    import shutil
    from iscc_bench import DATA_DIR

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    DUPES_PATH = os.path.join(DATA_DIR, "image_dupes")
    os.makedirs(DUPES_PATH, exist_ok=True)

    iids = {}
    log.info("check caltech_101 for duplicate image ids")
    for filepath in caltech_101():
        try:
            iid = generate_image_id(filepath)
            print(iid)
        except Exception as e:
            print(repr(e))
            continue
        if iid not in iids:
            iids[iid] = filepath
        else:
            print("Collision for {}: {} -> {}".format(iid, filepath, iids[iid]))
            srca = filepath
            srcb = iids[iid]
            dsta = os.path.join(DUPES_PATH, iid + "_a.jpg")
            dstb = os.path.join(DUPES_PATH, iid + "_b.jpg")
            shutil.copy(srca, dsta)
            shutil.copy(srcb, dstb)
