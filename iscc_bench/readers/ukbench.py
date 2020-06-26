# -*- coding: utf-8 -*-
"""Read image data from ukbench

Records: 10200 Images at 640x480
Size: 1.5 GB (compressed)
Info: https://archive.org/details/ukbench
Data: https://archive.org/download/ukbench/ukbench.zip
"""
import os
import logging
import zipfile

from iscc_bench import DATA_DIR
from iscc_bench.readers import utils


DOWNLOAD_URL = "https://archive.org/download/ukbench/ukbench.zip"
DATA_PATH = os.path.join(DATA_DIR, "ukbench")
DATA_FILE_PATH = os.path.join(DATA_PATH, "ukbench.zip")


log = logging.getLogger(__name__)


def ukbench():
    """Yield file paths to ukbench images."""
    try:
        os.makedirs(DATA_PATH)
        log.info("Created data directory: {}".format(DATA_PATH))
    except FileExistsError:
        pass

    if not os.path.exists(DATA_FILE_PATH):

        log.info("Downloading image data: {}".format(DATA_FILE_PATH))
        utils.download(DOWNLOAD_URL, DATA_FILE_PATH)

        log.info("Unpacking image data: {}".format(DATA_FILE_PATH))
        with zipfile.ZipFile(DATA_FILE_PATH) as zf:
            zf.extractall(DATA_PATH)

    image_path = os.path.join(DATA_PATH, "full")
    for fp in utils.iter_files(image_path, exts=["jpg"], recursive=True):
        yield fp


if __name__ == "__main__":
    from hashlib import sha1

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    sigs = {}
    log.info("check ukbench for exact duplicate images")
    for file_path in ukbench():
        fname = os.path.basename(file_path)
        sig = sha1(open(file_path, "rb").read()).hexdigest()
        print(fname, sig)
        if sig not in sigs:
            sigs[sig] = file_path
        else:
            print("Collision: {} -> {}".format(file_path, sigs[sig]))
    log.info("done checking ukbench for exact duplicate tracks")
