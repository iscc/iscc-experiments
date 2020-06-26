# -*- coding: utf-8 -*-
"""WIP
Video-ID based on mpeg7 Coarse Signatures.

Idea: The MPEG7 Video coarse signature is composed of 5 binary occurence histograms.
Each of the histograms is 243 bits and a total of 1215 bits per 90 frames of video.
Each signature overlaps by 45 Frames with the previous signature. We project each
coarse signature to a 64bit similarty hash as follows: create a 64bit xxhash over
27bit chunks of the occurence histograms (45 * 64bit integers). Create a simhash over
the xxhashes.
"""
import random
import subprocess
import sys
from os.path import basename, dirname, exists
from pprint import pprint
from statistics import mode
from typing import Tuple
import imageio_ffmpeg
import iscc
import xxhash
from loguru import logger as log
from lxml import etree

from iscc_bench.algos.slide import sliding_window
from iscc_bench.utils import cd


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


def get_segments(file):
    """Get Video Segment Signatures (90 Frames).

    :param file: path to video file
    :return: list of segment sigs (5 BagOfWords per segment concatenated to bitstrings)
    """
    segments = []
    root = get_signature(file)
    seg_els = root.xpath("//a:VSVideoSegment", namespaces=NSMAP)
    for seg_el in seg_els:
        # TODO Collect and Store Frame and Time Position
        seg_sig = []
        seg_bows = seg_el.xpath("./a:BagOfWords/text()", namespaces=NSMAP)
        segments.append("".join(["".join(bow.split()) for bow in seg_bows]))
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


def sig_sum(sigs):
    return [sum(col) for col in zip(*sigs)]


def segmet_to_simh(seg):
    # print(seg)
    hashes = []
    for chunk in sliding_window(seg, 27, 27):
        chunk_string = "".join(chunk)
        # Skip all 0 strings
        if not "1" in chunk_string:
            continue
        print(chunk_string)
        hash_ = xxhash.xxh64_digest(chunk_string)
        print(hash_.hex())
        hashes.append(hash_)
    # print([s.hex() for s in hashes])
    result = iscc.similarity_hash(hashes)
    return result


def content_id_video(file, partial=False):
    log.debug(f"Processing {basename(file)}")
    segment_signatures = get_segments(file)
    segment_simhashes = [segmet_to_simh(seg) for seg in segment_signatures]
    print([s.hex() for s in segment_simhashes])
    sh = iscc.similarity_hash(segment_simhashes)
    if partial:
        content_id_video_digest = iscc.HEAD_CID_V_PCF + sh
    else:
        content_id_video_digest = iscc.HEAD_CID_V + sh
    return iscc.encode(content_id_video_digest)


if __name__ == "__main__":
    p1 = "C:/Users/titusz/Code/iscc-experiments/iscc_bench/data/web_video/7_1_Y.flv"
    p2 = "C:/Users/titusz/Code/iscc-experiments/iscc_bench/data/web_video/7_2_Y.flv"
    cidv1 = content_id_video(p1)
    cidv2 = content_id_video(p2)
    print(cidv1, cidv2, "- Hamming Distance:", iscc.distance(cidv1, cidv2))
    # pprint(wta_permutations())
