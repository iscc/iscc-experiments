# -*- coding: utf-8 -*-
"""Read video data from CC_WEB_VIDEO: Near-Duplicate Web Video Dataset.

Records: 13,137 videos
Size: 85 GB
Info: http://vireo.cs.cityu.edu.hk/webvideo/Download.htm
Data: http://vireo.cs.cityu.edu.hk/webvideo/Info/Video_Complete.txt
"""
import csv
import hashlib
import os
import re
import zipfile
from os.path import basename, exists, join
from typing import List

import requests
from loguru import logger as log

from iscc_bench import DATA_DIR
from iscc_bench.readers import utils
from iscc_bench.readers.utils import download


DOWNLOAD_URL = "http://vireo.cs.cityu.edu.hk/webvideo/Info/Video_Complete.txt"
DATA_PATH = os.path.join(DATA_DIR, "web_video")
DATA_FILE_PATH = os.path.join(DATA_PATH, "video_complete.txt")
DOWNLOAD_TPL = "http://vireo.cs.cityu.edu.hk/webvideo/videos/{QueryID}/{VideoName}"


def get_seeds():
    """Download, parse and return IDs of seed videos."""
    resp = requests.get("http://vireo.cs.cityu.edu.hk/webvideo/Info/Seed.txt")
    seeds = {}
    for line in resp.text.splitlines():
        seed_id, video_id = line.split()
        seed_id = seed_id.strip("*")
        seeds[seed_id] = video_id
    return seeds


def get_meta():
    """Download and return parsed metadata"""
    try:
        os.makedirs(DATA_PATH)
        log.info("Created data directory: {}".format(DATA_PATH))
    except FileExistsError:
        pass

    if not os.path.exists(DATA_FILE_PATH):
        log.info("Downloading web_video data: {}".format(DATA_FILE_PATH))
        utils.download(DOWNLOAD_URL, DATA_FILE_PATH)

    with open(DATA_FILE_PATH, mode="r", encoding="latin") as csvfile:
        reader = csv.DictReader(csvfile, delimiter="\t")
        data = {d["ID"]: d for d in reader}

    for id_, entry in data.items():
        entry["vurl"] = DOWNLOAD_TPL.format(
            QueryID=entry["TopicID"], VideoName=entry["VideoName"]
        )

    return data


def get_seed_urls():
    meta = get_meta()
    sv = {}
    for seed_id, video_id in get_seeds().items():
        url = meta[video_id]["vurl"]
        sv[seed_id] = url
    return sv


def seed_videos() -> List[str]:
    """Iter - download if neccessary - seed videos"""
    videos = []
    for sid, url in get_seed_urls().items():
        fpath = join(DATA_PATH, basename(url))
        if not exists(fpath):
            download(url, fpath)
        videos.append(fpath)
    return videos


def ground_truth():
    """Download and parse ground truth data.

    A list of triplets with:
        qid: QueryID
        vid: VideoID
        status: Relation code from qid to vid.

    Status codes:
        E  - Exactly duplicate
        S  - Similar video
        V  - Different version
        M  - Major change
        L  - Long version
        X  - Dissimilar video
        -1 - Video does not exist

    returns: [(qid, vid, status)]
    """
    remote = "http://vireo.cs.cityu.edu.hk/webvideo/Info/Ground.zip"
    local = join(DATA_PATH, "Ground.zip")
    if not exists(local):
        download(remote, local)
    gt = []
    with zipfile.ZipFile(local) as gt_zip:
        for path in gt_zip.namelist():
            if path.startswith("GT/GT") and path.endswith(".rst"):
                query_id = re.findall(r"\d+", path)[0]
                data = gt_zip.open(path).read()
                for line in data.strip().splitlines():
                    v = line.split()
                    video_id, status = v[0], v[1]
                    gt.append((int(query_id), int(video_id), status.decode()))
    return gt


def iter_related(query_id=6, rel="S"):
    """Iterate over local file path of related videos."""
    meta = get_meta()
    d = []
    hashes = set()
    for source_id, target_id, relation in ground_truth():
        if relation == rel and source_id == query_id:
            url = meta[str(target_id)]["vurl"]
            fname = basename(url)
            fpath = join(DATA_PATH, fname)
            if not exists(fpath):
                download(url, fpath)
            # skip exact duplicates
            cid = hashlib.sha3_256(open(fpath, "rb").read()).hexdigest()
            if cid not in hashes:
                yield fpath
            hashes.add(cid)
    return d


def triplets():
    """Return triplets of local video filepath for comparison benchmarking.

    ::return list of [(query-video, similar-video, unrelated-video) ...]
    """
    log.debug("Video Triplets")
    result = []
    for file_path in seed_videos():
        qp = file_path
        seed_qid, seed_vid = basename(file_path).split("_")[:2]
        log.debug(f"Seed Video {seed_qid}_{seed_vid}")
        for similar_file_path in iter_related(int(seed_qid), rel="S"):
            sp = similar_file_path
            s_seed_qid, s_seed_vid = basename(similar_file_path).split("_")[:2]
            log.debug(f"Similar Video {s_seed_qid}_{s_seed_vid}")
            break
        for unrelated_file_path in iter_related(int(seed_qid), rel="X"):
            up = unrelated_file_path
            u_seed_qid, u_seed_vid = basename(unrelated_file_path).split("_")[:2]
            log.debug(f"Unrelated Video {u_seed_qid}_{u_seed_vid}\n")
            break
        result.append((qp, sp, up))
    return result


if __name__ == "__main__":
    from pprint import pprint

    pprint(get_meta())
