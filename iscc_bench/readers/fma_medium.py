# -*- coding: utf-8 -*-
"""Read audio data from Free Music Archive (FMA).

Records: 25000 tracks of 30s
Size: 22 GiB (compressed)
Info: https://github.com/mdeff/fma
Data: https://os.unil.cloud.switch.ch/fma/fma_medium.zip

Instructions:
    First iteration over fma_medium will download and extract audio files.
"""
import os
import logging
import zipfile
from iscc_bench import DATA_DIR
from iscc_bench.readers import utils


DOWNLOAD_URL = "https://os.unil.cloud.switch.ch/fma/fma_medium.zip"
DATA_PATH = os.path.join(DATA_DIR, 'fma_medium')
DATA_FILE_PATH = os.path.join(DATA_PATH, 'fma_medium.zip')

log = logging.getLogger(__name__)


def fma_medium():
    """Yield file path to all audio tracks from fma_medium dataset."""
    try:
        os.makedirs(DATA_PATH)
        log.info('Created data directory: {}'.format(DATA_PATH))
    except FileExistsError:
        pass

    if not os.path.exists(DATA_FILE_PATH):

        log.info('Downloading fma_medium data: {}'.format(DATA_FILE_PATH))
        utils.download(DOWNLOAD_URL, DATA_FILE_PATH)

        log.info('Unpacking audio tracks: {}'.format(DATA_FILE_PATH))
        with zipfile.ZipFile(DATA_FILE_PATH) as zf:
            zf.extractall(DATA_PATH)

    for fp in utils.iter_files(DATA_PATH, exts=['mp3'], recursive=True):
        yield fp


if __name__ == '__main__':
    from hashlib import sha1
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    sigs = {}
    log.info('check fma_medium for exact duplicate tracks')
    for image_path in fma_medium():
        sig = sha1(open(image_path, 'rb').read()).hexdigest()
        if sig not in sigs:
            sigs[sig] = image_path
        else:
            print('Collision: {} -> {}'.format(image_path, sigs[sig]))
    log.info('done checking fma_medium for exact duplicate tracks')

