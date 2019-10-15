# -*- coding: utf-8 -*-
"""Reads fingerprint data from acoustid.org project.

Data: http://data.acoustid.org/replication/
"""
import bz2
import logging
from os import makedirs
from os.path import join, exists, getsize
import requests
from lxml import etree
from iscc_bench import DATA_DIR
import lxml.html
from iscc_bench.readers.utils import download
import numpy as np
import blosc

DOWNLOAD_URL = "http://data.acoustid.org/replication/"
DATA_PATH = join(DATA_DIR, "acoustid")


log = logging.getLogger(__name__)


def compress(fingerprints):
    arr = np.int32(fingerprints)
    bytes_array = arr.tostring()
    return blosc.compress(
        bytes_array, typesize=4, cname="zstd", shuffle=blosc.SHUFFLE, clevel=9
    )


def decompress(data):
    return np.fromstring(blosc.decompress(data), dtype=np.int32).tolist()


def iter_data():
    for local_path in iter_data_files():
        input_file = bz2.BZ2File(local_path, "rb")
        parser = etree.XMLParser(recover=True)
        root = etree.parse(input_file, parser)
        fingerprints = root.xpath(
            '/packet/transaction/event[@op="I" and @table="fingerprint"]'
        )
        log.info(f"Found {len(fingerprints)} new inserts.")
        for fp_el in fingerprints:
            track_id = int(fp_el.xpath('./values/column[@name="track_id"]')[0].text)
            fingerprint = fp_el.xpath('./values/column[@name="fingerprint"]')[0].text[
                1:-1
            ]
            fingerprint = [int(f) for f in fingerprint.split(",")]
            yield {"track_id": track_id, "fingerprint": fingerprint}


def iter_data_files(reverse=False):
    """Yield local file paths to data files.

    Iterate over all data files, downloading them if required
    and yield local file paths.
    """
    makedirs(DATA_PATH, exist_ok=True)
    for idx, row in remote_data_files(reverse).items():
        filename = row[0]
        # Skip corrupted files
        if filename in (
            "acoustid-update-26562.xml.bz2",
            "acoustid-update-44845.xml.bz2",
        ):
            continue

        remote_path = DOWNLOAD_URL + filename
        local_path = join(DATA_PATH, row[0])
        if not exists(local_path):
            download(remote_path, local_path, chunk_size=1024)
        local_size = getsize(local_path)
        remote_size = int(row[-1])
        if local_size != remote_size:
            log.warning(f"Local: {local_size} | Remote: {remote_size}")
            download(remote_path, local_path, chunk_size=1024)
        yield local_path


def remote_data_files(reverse=True):
    """
    returns sorted dict
    {
     37859: ['acoustid-update-37859.xml.bz2', '25-Apr-2016', '08:00', '1426513'],
     ...
    }
    """
    r = requests.get(DOWNLOAD_URL)
    doc = lxml.html.fromstring(r.content)
    rows = []
    for link in doc.xpath("//a"):
        rows.append((link.text + link.tail).split())
    index = {}
    for row in rows[1:]:
        filename = row[0]
        if filename.endswith("xml.bz2"):
            if "musicbrainz" not in filename:
                fid = int(filename.split(".")[0].split("-")[-1])
                index[fid] = row
    log.info(f"Found {len(index)} acoustid update files.")

    # Sort and filter small/empty files
    sindex = {
        k: index[k]
        for k in sorted(index.keys(), reverse=reverse)
        if int(index[k][-1]) > 400
    }
    log.info(f"Found {len(sindex)} acoustid update files with actual data.")
    return sindex


if __name__ == "__main__":
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)
    for entry in iter_data():
        print(entry)
