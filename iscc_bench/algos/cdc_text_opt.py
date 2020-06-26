# -*- coding: utf-8 -*-
"""Hyperoptimized Shift Invariant Text Chunking"""
import random
import logging
from io import StringIO
from typing import TextIO
from os.path import basename
from statistics import mean
from xxhash import xxh64_intdigest
from hyperopt import hp, fmin, tpe, Trials
import math

from iscc_bench.algos.metrics import jaccard
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.mltext import mltext
from iscc_bench.textid.normalize import text_normalize
from iscc_bench.utils import load_text_file

logr = logging.getLogger(__name__)


INT_MAX = (1 << 31) - 1


def get_gear(seed=1):
    random.seed(seed)
    return [random.randint(0, INT_MAX) for _ in range(256)]


def get_masks(seed=1, a=11, b=9):
    random.seed(seed)
    return random.getrandbits(a), random.getrandbits(b)


def chunk_length(text, norm, gear, MASK_1, MASK_2):
    NORM = norm
    MIN = round(NORM / 4)
    MAX = NORM * 8

    data_length = len(text)
    i = MIN
    pattern = 0

    if data_length <= MIN:
        return data_length

    barrier = min(NORM, data_length)
    while i < barrier:
        pattern = ((pattern >> 1) + gear[ord(text[i]) % 256]) & INT_MAX
        if not pattern & MASK_1:
            return i
        i += 1

    barrier = min(MAX, data_length)
    while i < barrier:
        pattern = ((pattern >> 1) + gear[ord(text[i]) % 256]) & INT_MAX
        if not pattern & MASK_2:
            return i
        i += 1
    return i


def chunk_text(stream: TextIO, NORM, GEAR, MASK_1, MASK_2):
    MAX = NORM * 8
    section = stream.read(MAX)
    while True:
        if len(section) < MAX:
            section += stream.read(MAX)
        if len(section) == 0:
            break
        boundary = chunk_length(section, NORM, GEAR, MASK_1, MASK_2)

        yield section[:boundary]
        section = section[boundary:]


def objective(space):
    fps = list(mltext())

    NORM = int(space["NORM"])
    SEED = int(space["SEED"])
    GEAR = get_gear(SEED)
    a = int(space["MASK_1"])
    b = int(space["MASK_2"])
    MASK_1, MASK_2 = get_masks(SEED, a, b)

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

        chunks_a = StringIO(text_normalize(load_text_file(fp_a)))
        chunks_b = StringIO(text_normalize(load_text_file(fp_b)))
        chunks_c = StringIO(text_normalize(load_text_file(fp_c)))

        chunks_a = list(chunk_text(chunks_a, NORM, GEAR, MASK_1, MASK_2))
        chunks_b = list(chunk_text(chunks_b, NORM, GEAR, MASK_1, MASK_2))
        chunks_c = list(chunk_text(chunks_c, NORM, GEAR, MASK_1, MASK_2))

        chunk_sizes.extend(len(c) for c in chunks_a)

        # select cutpoint regions only

        chunks_hashes_a = [xxh64_intdigest(c) for c in chunks_a]
        chunks_hashes_b = [xxh64_intdigest(c) for c in chunks_b]
        chunks_hashes_c = [xxh64_intdigest(c) for c in chunks_c]

        num_chunks.append(len(chunks_hashes_a))

        sim_sim = jaccard(chunks_hashes_a, chunks_hashes_b)
        similarities.append(sim_sim)

        sim_dif = jaccard(chunks_hashes_a, chunks_hashes_c)
        dissimilarities.append(sim_dif)
        loss = (sim_dif or 0.00001) / (sim_sim or 0.00001)
        logr.debug(
            f"Loss: {loss:.8f} Sim: {sim_sim:.3f} Dif: {sim_dif:.3f} ({basename(fp_a)})"
        )
        losses.append(loss)
    return {
        "status": "ok",
        "loss": mean(losses),
        "avg_num_chunks": mean(num_chunks),
        "avg_chunk_size": mean(chunk_sizes),
        "max_chunk_size": max(chunk_sizes),
        "avg_sim": mean(similarities),
        "avg_dis": mean(dissimilarities),
        "chunk_sizes": chunk_sizes,
    }


def optimize():
    space = {
        "NORM": hp.qloguniform("NORM", math.log(1024), math.log(8192), 1),
        "SEED": hp.qloguniform("SEED", math.log(1), math.log(1000), 1),
        "MASK_1": hp.quniform("MASK_1", 9, 15, 1),
        "MASK_2": hp.quniform("MASK_2", 5, 13, 1),
    }

    trials = Trials()

    best = fmin(
        fn=objective, space=space, algo=tpe.suggest, max_evals=30, trials=trials,
    )
    print(f"Best Parameters: {best}")
    return trials.best_trial


if __name__ == "__main__":
    import matplotlib.pyplot as plt

    best = optimize()
    cs = best["result"]["chunk_sizes"]
    plt.hist(cs, color="blue", edgecolor="black", bins=int(8192 / 32))
    plt.show()
