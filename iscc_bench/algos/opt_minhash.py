# -*- coding: utf-8 -*-
"""Optimize Accuracy of Minhash function"""
import time
from statistics import mean, variance
import numpy as np
from xxhash import xxh32_intdigest
from iscc_bench.algos.metrics import jaccard
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.mltext import mltext
from iscc_bench.utils import load_text_file
from iscc_bench.textid.normalize import text_normalize


R = np.random.RandomState(seed=23)
MASKS_32_NP = R.randint(0, 2 ** 32 - 1, 64, dtype=np.uint32)


def minhash_xor(features):
    masks = MASKS_32_NP
    features = np.array(hashify_32(features), np.uint32)

    hashes = np.empty(64, dtype=np.uint32)
    hashes.fill(2 ** 32 - 1)

    for f in features:
        hashes = np.minimum(hashes, np.bitwise_xor(masks, f), dtype=np.uint32)
    return hashes.tolist()


def minhash_xxh(features):
    return [min([xxh32_intdigest(f, h) for f in features]) for h in range(64)]


MERSENNE_PRIME = (1 << 61) - 1
MAX_HASH = (1 << 32) - 1

PERMUTATIONS = np.array(
    [
        (R.randint(1, MERSENNE_PRIME, dtype=np.uint64),
         R.randint(0, MERSENNE_PRIME, dtype=np.uint64))
        for _ in range(64)
    ],
    dtype=np.uint64).T

PERMUTATIONS[0] = np.bitwise_or(PERMUTATIONS[0], 1)


def minhash_uvh(features):
    """
    see: https://stackoverflow.com/a/40117398/51627
    """
    features = np.array(hashify_32(features), np.uint32)
    a, b = PERMUTATIONS
    hashes = np.ones(64, dtype=np.uint64) * MAX_HASH

    for value in features:
        phv = np.bitwise_and((a * value + b) % MERSENNE_PRIME, np.uint64(MAX_HASH))
        hashes = np.minimum(phv, hashes)
    return hashes.tolist()


def featurize(text):
    return [''.join(c).encode('utf8') for c in sliding_window(text, 13)]


def hashify_32(features):
    return [xxh32_intdigest(f) for f in features]


funcs = (
    minhash_xor,
    minhash_xxh,
    minhash_uvh,
)


def benchmark(mh_func):
    """Benchmark accuracy of minhash function"""
    fps = list(mltext())
    sim_errs = []
    dis_errs = []
    runtimes = []
    for abc in sliding_window(fps, 3, 2, fillvalue=None):
        abc = list(abc)
        if abc[-1] is None:
            continue
        texts = (load_text_file(t) for t in abc)
        n_texts = (text_normalize(t) for t in texts)
        features = [featurize(t) for t in n_texts]
        hf = [hashify_32(f) for f in features]
        sim_sim = jaccard(hf[0], hf[1])
        sim_dis = jaccard(hf[0], hf[2])

        start = time.time()
        mhashes = [mh_func(f) for f in features]
        end = time.time()
        runtimes.append((end - start) * 1000)
        mh_sim_sim = jaccard(mhashes[0], mhashes[1])
        mh_sim_dis = jaccard(mhashes[0], mhashes[2])
        sim_errs.append(abs(sim_sim - mh_sim_sim))
        dis_errs.append(abs(sim_dis - mh_sim_dis))
    print(
        f'{mh_func.__name__}\t\t\t'
        f'Rt: {mean(runtimes):.2f} - '
        f'Error Sim Mean {mean(sim_errs)} - Max {max(sim_errs)} Var {variance(sim_errs)}| '
        f'Error Dis Mean {mean(dis_errs)} - Max {max(dis_errs)} Var {variance(dis_errs)}'
    )


if __name__ == '__main__':
    for func in funcs:
        benchmark(func)
