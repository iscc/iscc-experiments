# -*- coding: utf-8 -*-
"""Read image data from Caltech 101.

Records: 30607 Images
Size: 1.2 GB
Info: http://www.vision.caltech.edu/Image_Datasets/Caltech256/
Data: http://www.vision.caltech.edu/Image_Datasets/Caltech256/256_ObjectCategories.tar

Instructions:
    First iteration over caltech_256 will download and extract images.
"""
import os
import logging
import tarfile
from iscc_bench import DATA_DIR
from iscc_bench.readers import utils

DOWNLOAD_URL = "http://www.vision.caltech.edu/Image_Datasets/Caltech256/256_ObjectCategories.tar"
DATA_PATH = os.path.join(DATA_DIR, 'caltech256')
DATA_FILE_PATH = os.path.join(DATA_PATH, '256_ObjectCategories.tar')

log = logging.getLogger(__name__)


def caltech_256():
    """Yield file paths to caltech 256 images."""

    try:
        os.makedirs(DATA_PATH)
        log.info('Created data directory: {}'.format(DATA_PATH))
    except FileExistsError:
        pass

    if not os.path.exists(DATA_FILE_PATH):
        log.info('Downloading image data: {}'.format(DATA_FILE_PATH))
        utils.download(DOWNLOAD_URL, DATA_FILE_PATH)

        log.info('Unpacking image data: {}'.format(DATA_FILE_PATH))
        with tarfile.open(DATA_FILE_PATH) as tar:
            tar.extractall(DATA_PATH)

    for fp in utils.iter_files(DATA_PATH, exts=['jpg'], recursive=True):
        yield fp


if __name__ == '__main__':
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    for image_path in caltech_256():
        print(image_path)


