# -*- coding: utf-8 -*-
"""Read audio data from Free Music Archive (FMA).

Records: 8000 tracks of 30s
Size: 7.2 GiB (compressed) - 7.44 GB uncompressed
Info: https://github.com/mdeff/fma
Data: https://os.unil.cloud.switch.ch/fma/fma_small.zip

Instructions:
    First iteration over fma_small will download and extract audio files.
"""
import os
import logging
import zipfile
from iscc_bench import DATA_DIR
from iscc_bench.readers import utils


DOWNLOAD_URL = "https://os.unil.cloud.switch.ch/fma/fma_small.zip"
DATA_PATH = os.path.join(DATA_DIR, "fma_small")
DATA_FILE_PATH = os.path.join(DATA_PATH, "fma_small.zip")

log = logging.getLogger(__name__)


def fma_small():
    """Yield file path to all audio tracks from fma_small dataset."""
    try:
        os.makedirs(DATA_PATH)
        log.info("Created data directory: {}".format(DATA_PATH))
    except FileExistsError:
        pass

    if not os.path.exists(DATA_FILE_PATH):

        log.info("Downloading fma_small data: {}".format(DATA_FILE_PATH))
        utils.download(DOWNLOAD_URL, DATA_FILE_PATH)

        log.info("Unpacking audio tracks: {}".format(DATA_FILE_PATH))
        with zipfile.ZipFile(DATA_FILE_PATH) as zf:
            zf.extractall(DATA_PATH)

    for fp in utils.iter_files(DATA_PATH, exts=["mp3"], recursive=True):
        yield fp


if __name__ == "__main__":
    from hashlib import sha1

    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)

    sigs = {}
    log.info("check fma_small for exact duplicate tracks")
    for image_path in fma_small():
        sig = sha1(open(image_path, "rb").read()).hexdigest()
        if sig not in sigs:
            sigs[sig] = image_path
        else:
            print("Collision: {} -> {}".format(image_path, sigs[sig]))
    log.info("done checking fma_small for exact duplicate tracks")
