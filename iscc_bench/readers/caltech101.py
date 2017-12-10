# -*- coding: utf-8 -*-
"""Read image data from Caltech 101.

Records: 9145 Images at ~ 300 x 200 pixels
Size: 131 MB (compressed)
Info: http://www.vision.caltech.edu/Image_Datasets/Caltech101/
Data: http://www.vision.caltech.edu/Image_Datasets/Caltech101/101_ObjectCategories.tar.gz

Instructions:
    First iteration over caltech_101 will download and extract images.
"""
import os
import logging
import tarfile
from iscc_bench import DATA_DIR
from iscc_bench.readers import utils


DOWNLOAD_URL = "http://www.vision.caltech.edu/Image_Datasets/Caltech101/101_ObjectCategories.tar.gz"
DATA_PATH = os.path.join(DATA_DIR, 'caltech101')
DATA_FILE_PATH = os.path.join(DATA_PATH, '101_ObjectCategories.tar.gz')

log = logging.getLogger(__name__)


def caltech_101():
    """Yield file paths to caltech 101 images."""

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

    for image_path in caltech_101():
        print(image_path)


