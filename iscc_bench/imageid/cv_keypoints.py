# -*- coding: utf-8 -*-
"""Experiments with OpenCV Key Point Detection"""
from os.path import basename

import cv2

from iscc_bench.imageid.ssc import SSC
from iscc_bench.readers.ukbench import ukbench


def compare(start_idx=468):
    imgs = list(ukbench())
    for idx in range(start_idx, start_idx + 4):
        img_path = imgs[idx]
        img = cv2.imread(img_path)
        det = cv2.ORB_create()
        kps = det.detect(img, None)
        kps_sort = sorted(kps, key=lambda x: -x.response)
        kps_sel = SSC(kps_sort, 16, 0.1, img.shape[1], img.shape[0])
        img_kps = cv2.drawKeypoints(img, kps_sel, None, color=(0, 0, 255), flags=4)
        cv2.imshow(basename(img_path), img_kps)
    cv2.waitKey(0)


if __name__ == '__main__':
    compare()
