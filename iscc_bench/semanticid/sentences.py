# -*- coding: utf-8 -*-
"""Experiment with sentence segmentation"""
from os.path import basename

from loguru import logger as log
from iscc_bench.readers.gutenberg import gutenberg
from syntok import segmenter


def main():
    for fp in gutenberg('de'):
        log.info(basename(fp))
        doc = open(fp, 'rt', encoding='UTF-8').read()
        log.info(doc.strip()[:200])
        for para in segmenter.analyze(doc):
            p = []
            for sent in para:
                s = []
                for tok in sent:
                    s.extend([tok.spacing, tok.value])
                fs = ''.join(s)
                log.info(fs)
                p.append(fs)
            log.info('PARAGRAPH BREAK')


if __name__ == '__main__':
    main()
