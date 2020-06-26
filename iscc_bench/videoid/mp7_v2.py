# -*- coding: utf-8 -*-
"""Extract and parse MPEG7 Video Signatures. Hash based on MPEG7 SEGEMENTS"""
import random
import subprocess
import sys
from os.path import basename, dirname, exists
from statistics import mode
from typing import Tuple
import imageio_ffmpeg
import iscc
from loguru import logger as log
from lxml import etree
from iscc_bench.utils import cd
from iscc_bench.videoid.const import WTA_PERMUTATIONS


WTA_SEED = 10
NSMAP = {
    "a": "urn:mpeg:mpeg7:schema:2001",
    "b": "http://www.w3.org/2001/XMLSchema-instance",
}


def get_segments(file):
    """Get Video Segment Signatures (90 Frames).

    :param file: path to video file
    :return: 243 bit hash sum of bags of words per video segment
    """
    segments = []
    root = get_signature(file)
    seg_els = root.xpath("//a:VSVideoSegment", namespaces=NSMAP)
    for seg_el in seg_els:
        # TODO Collect and Store Frame and Time Position
        seg_bows = seg_el.xpath("./a:BagOfWords/text()", namespaces=NSMAP)
        bin_vecs = []
        for seg_bow in seg_bows:
            bin_vecs.append(tuple(int(s) for s in "".join(seg_bow.split())))
        bow_sum = sig_sum(bin_vecs)
        segments.append(bow_sum)
    return segments


def get_signature(file) -> etree.Element:
    """Extract & Cache MPEG7 Signature from video file"""
    crop = get_crop(file)
    log.debug(f"Crop detection: {crop}")
    sigfile = basename(file) + ".xml"
    folder = dirname(file)
    with cd(folder):
        if not exists(sigfile):
            cmd = [
                imageio_ffmpeg.get_ffmpeg_exe(),
                "-i",
                file,
                "-vf",
                f"{crop},signature=format=xml:filename={sigfile}",
                "-f",
                "null",
                "-",
            ]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        tree = etree.parse(sigfile)
        root = tree.getroot()
        return root


def get_crop(file) -> str:
    """Detect crop value for video"""
    cmd = [
        imageio_ffmpeg.get_ffmpeg_exe(),
        "-i",
        file,
        "-vf",
        f"cropdetect",
        "-f",
        "null",
        "-",
    ]
    res = subprocess.run(cmd, capture_output=True)
    text = res.stderr.decode(encoding=sys.stdout.encoding)
    crops = [
        line.split()[-1]
        for line in text.splitlines()
        if line.startswith("[Parsed_cropdetect")
    ]
    return mode(crops)


def positional_sig(vec):
    """creates positional signature from vector"""
    return [(i, v) for i, v in enumerate(vec)]


def wta_permutations(seed=WTA_SEED, vl=243, n=256) -> Tuple:
    random.seed(seed)
    perms = []
    while len(perms) < n:
        perm = (random.randint(0, vl - 1), random.randint(0, vl - 1))
        if perm[0] != perm[1]:
            perms.append(perm)
    return tuple(perms)


def wta_hash(vec, hl=64) -> bytes:
    """Calculate hl-bit WTA Hash from vector."""
    vl = len(vec)
    perms = wta_permutations(WTA_SEED, vl, hl)
    # perms = WTA_PERMUTATIONS
    log.debug(f"WTA vec length: {vl}")
    h = []
    assert len(set(vec)) > 1, "Vector for wta_hash needs at least 2 different values."

    def get_neq_vals(idxs):
        vals = vec[idxs[0]], vec[idxs[1]]
        while vals[0] == vals[1]:
            idxs = idxs[0], (idxs[1] + 1) % vl
            vals = vec[idxs[0]], vec[idxs[1]]
        return vals

    for idxs in perms:
        vals = get_neq_vals(idxs)
        h.append(vals.index(max(vals)))
        if len(h) == hl:
            break
    h = bytes([int("".join(map(str, h[i : i + 8])), 2) for i in range(0, len(h), 8)])
    log.debug(f"Hash length {len(h)}")
    return h


def sig_sum(sigs):
    return tuple(sum(col) for col in zip(*sigs))


def content_id_video(file, partial=False):
    log.debug(f"Processing {basename(file)}")
    segment_sigs = get_segments(file)
    sigs = set(segment_sigs)
    log.debug(f"Unique segment signatures {len(sigs)} of {len(segment_sigs)}")
    hashsum = sig_sum(sigs)
    log.debug(f"HashSum {len(hashsum)}:{hashsum}")
    sh = wta_hash(hashsum, 64)
    log.debug(f"Raw CID-V {len(sh) * 8}:{sh.hex()}")
    if partial:
        content_id_video_digest = iscc.HEAD_CID_V_PCF + sh[:8]
    else:
        content_id_video_digest = iscc.HEAD_CID_V + sh[:8]
    return iscc.encode(content_id_video_digest)


if __name__ == "__main__":
    p1 = "C:/Users/titusz/Code/iscc-experiments/iscc_bench/data/web_video/7_1_Y.flv"
    p2 = "C:/Users/titusz/Code/iscc-experiments/iscc_bench/data/web_video/7_2_Y.flv"
    cidv1 = content_id_video(p1)
    cidv2 = content_id_video(p2)
    print(WTA_SEED, cidv1, cidv2, "- Hamming Distance:", iscc.distance(cidv1, cidv2))
    # pprint(wta_permutations())
