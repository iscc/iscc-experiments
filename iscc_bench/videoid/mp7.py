# -*- coding: utf-8 -*-
"""Extract and parse MPEG7 Video Signatures"""
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


def get_frames(file, mc=0) -> Tuple:
    """Get frame signatures.

    :param file: path to video file
    :param mc: filter for frame signatures with 'mc' minimum confidance
    :return: tuple of frame signatures (380 values 0-2)
    """
    frames = []
    root = get_signature(file)
    frame_els = root.xpath("//a:VideoFrame", namespaces=NSMAP)
    for frame_el in frame_els:
        fc = int(frame_el.xpath("./a:FrameConfidence/text()", namespaces=NSMAP)[0])
        if fc >= mc:
            fs = frame_el.xpath("./a:FrameSignature/text()", namespaces=NSMAP)[0]
            frames.append(tuple(int(t) for t in fs.split()))
    log.debug(f"Frames: {len(frames)}")
    return tuple(frames)


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


def wta_permutations(seed=WTA_SEED, vl=380, n=256) -> Tuple:
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
    # perms = wta_permutations(WTA_SEED, vl, hl)
    perms = WTA_PERMUTATIONS
    log.debug(f"WTA vec length: {vl}")
    h = []

    def get_neq_vals(idxs):
        vals = vec[idxs[0]], vec[idxs[1]]
        while vals[0] == vals[1]:
            vals = idxs[0], (idxs[1] + 1) % vl
        return vals

    for n, idxs in enumerate(perms):
        vals = get_neq_vals(idxs)
        h.append(vals.index(max(vals)))
        if n == hl:
            break
    h = bytes([int("".join(map(str, h[i : i + 8])), 2) for i in range(0, len(h), 8)])
    log.debug(f"Hash length {len(h)}")
    return h


def sig_sum(sigs):
    return [sum(col) for col in zip(*sigs)]


def content_id_video(file, partial=False):
    log.debug(f"Processing {basename(file)}")
    sigs = set(get_frames(file))
    log.debug(f"Unique signatures {len(sigs)}")
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
    p2 = "C:/Users/titusz/Code/iscc-experiments/iscc_bench/data/web_video/7_9_Y.flv"
    cidv1 = content_id_video(p1)
    cidv2 = content_id_video(p2)
    print(WTA_SEED, cidv1, cidv2, "- Hamming Distance:", iscc.distance(cidv1, cidv2))
    # pprint(wta_permutations())
