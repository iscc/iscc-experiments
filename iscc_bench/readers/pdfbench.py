# -*- coding: utf-8 -*-
"""Text extracted from Scientific PDF Papers with different tools

Records: 12099 Academic Paper extracted with 13 PDF extraction tools
Info: https://github.com/ckorzen/pdf-text-extraction-benchmark
Data: http://arxiv-benchmark.informatik.uni-freiburg.de/data/
"""
import logging
from xxhash import xxh64_intdigest
from os import makedirs
from os.path import join, exists, basename
import htmllistparse
from iscc_bench import DATA_DIR
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers import utils
from iscc_bench.utils import timing

DOWNLOAD_URL = "http://arxiv-benchmark.informatik.uni-freiburg.de/data/"
DATA_PATH = join(DATA_DIR, 'pdfbench')


log = logging.getLogger(__name__)


def pdfbench():
    """Yield file path (pairwise sorted) to gutenberg extracted texts"""
    for fp in sorted(utils.iter_files(DATA_PATH, exts=['txt'])):
        yield fp


def download_groundtruth():
    """Clean textfiles generated from TeX source"""
    makedirs(DATA_PATH, exist_ok=True)
    log.info(f'Created text directory: {DATA_PATH}')
    endpoint = DOWNLOAD_URL + 'benchmark/groundtruth/'
    cwd, listing = htmllistparse.fetch_listing(endpoint, timeout=30)
    subdirs = [f.name for f in listing]
    for subdir in subdirs:
        cwd, files = htmllistparse.fetch_listing(endpoint + subdir, timeout=30)
        for f in files:
            if not f.name.endswith('.body.txt'):
                continue

            url = endpoint + subdir + f.name
            outfile = join(DATA_PATH, subdir.rstrip('/') + '_' + f.name.replace('.body.txt', '_gndt.txt'))
            utils.download(url, outfile)


def download_pdfbox():
    """Textfiles extracted from PDFs with pdfbox"""
    makedirs(DATA_PATH, exist_ok=True)
    log.info(f'Created text directory: {DATA_PATH}')
    endpoint = DOWNLOAD_URL + 'evaluation/output/pdfbox/'
    cwd, listing = htmllistparse.fetch_listing(endpoint, timeout=30)
    subdirs = [f.name for f in listing]
    for subdir in subdirs:
        cwd, files = htmllistparse.fetch_listing(endpoint + subdir, timeout=30)
        for f in files:
            if not f.name.endswith('.final.txt'):
                continue

            url = endpoint + subdir + f.name
            outfile = join(DATA_PATH, subdir.rstrip('/') + '_' + f.name.replace('.final.txt', '_pdfbox.txt'))
            if not exists(outfile):
                utils.download(url, outfile)


@timing
def check_dupes():
    log.info('check pdfbench for exact duplicate files')
    sigs = {}
    for file_path in pdfbench():
        sig = xxh64_intdigest(open(file_path, 'rb').read())
        if sig not in sigs:
            sigs[sig] = file_path
        else:
            log.info('Collision: {} -> {}'.format(file_path, sigs[sig]))
    log.info(f'Done checking {len(sigs)} pdfbench for exact duplicate tracks')


@timing
def check_sequence():
    log.info('check pdfbench for pairwise sequence')
    for fpa, fpb in sliding_window(pdfbench(), 2, 2):
        fpa = basename(fpa).split('_')[:2]
        fpb = basename(fpb).split('_')[:2]
        if not fpa == fpb:
            log.warning(f'{fpa} != {fpb}')
    log.info(f'Done checking pdfbench for pairwise sequence')


if __name__ == '__main__':
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    # download_pdfbox()
    check_dupes()
    check_sequence()
