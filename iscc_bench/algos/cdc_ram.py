# -*- coding: utf-8 -*-
"""Rapid Asymetric Maximung Chunking

see: https://www.sciencedirect.com/science/article/pii/S0167739X16305829
"""
import logging
from math import log
from pprint import pprint
from typing import List
from statistics import mean
from hyperopt import hp, fmin, tpe, Trials
from iscc_bench.algos.metrics import containment
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.gutenberg import gutenberg
from os.path import basename
from iscc_bench.textid.normalize import normalize

logr = logging.getLogger(__name__)

CHUNK_MIN_SIZE = 8
SAMPLES = 16  # Number of samples to eval (even number below 476)


def cut_point(data: bytes, min_size=CHUNK_MIN_SIZE) -> int:
    """Find first cut point in byte string"""
    prefix = data[:min_size - 1]
    max_byte = max(prefix)
    i = min_size
    while i < len(data):
        if data[i] >= max_byte:
            return i
        i += 1
    return i


def cut_point2(data: bytes, min_size=6, max_size=1000, shift=4) -> int:
    """Find first cut point in byte string"""
    prefix = data[:min_size - 1]
    max_byte = max(prefix)
    max_byte2 = max_byte - shift
    secondary = None
    opt = int((max_size - min_size) / 4)
    nbytes = len(data)
    i = min_size
    while i < nbytes:
        cur_byte = data[i]
        if cur_byte >= max_byte:
            return i
        if cur_byte >= max_byte2:
            secondary = i
        i += 1
        if i >= opt and secondary:
            return secondary
        if i == max_size:
            return i
    return i


def chunk_text(text: str, min_size: int = CHUNK_MIN_SIZE) -> List[str]:
    """Return a list of shift invariant text chunks.

    Note: Cutpoints may occur within multibyte characters. Those characters
    will be skipped by this chunking method.
    """
    data = text.encode('utf-8')
    chunks = []
    while data:
        cp = cut_point(data, min_size=min_size)
        chunks.append(data[:cp].decode('utf-8', 'ignore'))
        data = data[cp:]
    return chunks


def chunk_data(data, min_size, max_size, shift) -> List[bytes]:
    """Return a list of shift invariant text chunks.

    Note: Cutpoints may occur within multibyte characters. Those characters
    will be skipped by this chunking method.
    """
    chunks = []
    while data:
        cp = cut_point2(data, min_size, max_size, shift)
        chunks.append(data[:cp])
        data = data[cp:]
    return chunks


def objective(space):
    fps = list(gutenberg())[:SAMPLES]

    min_size = int(space['min_size'])
    max_size = int(space['max_size'])
    shift = int(space['shift'])

    logr.info(f'Evaluate chunking with min {min_size} ({SAMPLES} samples).')
    losses = []
    chunk_sizes = []
    num_chunks = []
    similarities = []
    dissimilarities = []
    for fp_a, fp_b, fp_c in sliding_window(fps, size=3, step=2, fillvalue=None):
        if fp_b is None:
            break
        if fp_c is None:
            fp_c = fps[0]

        text_a = open(fp_a, 'rb').read()
        text_b = open(fp_b, 'rb').read()
        text_c = open(fp_c, 'rb').read()

        chunks_a = chunk_data(text_a, min_size, max_size, shift)
        chunks_b = chunk_data(text_b, min_size, max_size, shift)
        chunks_c = chunk_data(text_c, min_size, max_size, shift)
        chunk_sizes.extend(len(c) for c in chunks_a)
        num_chunks.append(len(chunks_a))

        def cut_regions(chunks):
            regs = []
            for a, b in sliding_window(chunks, size=2, step=1):
                regs.append(a[-4:] + b[:4])
            return regs

        # select cutpoint regions only
        chunks_a = cut_regions(chunks_a)
        chunks_b = cut_regions(chunks_b)
        chunks_c = cut_regions(chunks_c)

        sim_sim = containment(chunks_a, chunks_b)
        similarities.append(sim_sim)

        sim_dif = containment(chunks_a, chunks_c)
        dissimilarities.append(sim_dif)
        loss = sim_sim / (sim_dif or 0.00001)

        logr.debug(f'Loss: {loss:.3f} Sim: {sim_sim:.3f} Dif: {sim_dif:.3f} ({basename(fp_a)})')
        losses.append(loss)
    loss = mean(losses)
    return {
        'status': 'ok',
        'loss': loss,
        'avg_num_chunks': mean(num_chunks),
        'avg_chunk_size': mean(chunk_sizes),
        'max_chunk_size': max(chunk_sizes),
        'avg_sim': mean(similarities),
        'avg_dis': mean(dissimilarities),
    }


def optimize():
    space = {
        'min_size': hp.qloguniform('min_size', log(40), log(256), 1),
        'max_size': hp.qloguniform('max_size', log(512), log(8000), 1),
        'shift': hp.qloguniform('shift', log(2), log(16), 1)
    }

    trials = Trials()

    best = fmin(
        fn=objective,
        space=space,
        algo=tpe.suggest,
        max_evals=32,
        trials=trials,
    )
    pprint(trials.best_trial)
    print(f'Best Parameters: {best}')


if __name__ == '__main__':
    # log_format = '%(asctime)s - %(levelname)s - %(message)s'
    # logging.basicConfig(level=logging.DEBUG, format=log_format)
    optimize()
