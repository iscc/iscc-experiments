# -*- coding: utf-8 -*-
"""Benchmark performance of different Minhash implementations.

Results:

minhash_ref       : 6187.46 ms runtime
minhash_ref_opt   : 3317.13 ms runtime
minhash_ref_np    : 614.44 ms runtime
minhash_ref_numba : 86.77 ms runtime
minhash_xor_192   : 11.97 ms runtime
minhash_ref_192   : 131.68 ms runtime
minhash_xor       : 447.82 ms runtime
minhash_xor_np    : 147.60 ms runtime
minhash_xor_numba : 10.97 ms runtime
"""
import time
from itertools import chain
import numpy as np
from xxhash import xxh32_intdigest, xxh64_intdigest
from numba import njit
from statistics import mean, variance

from iscc_bench.algos.const import MINHASH_PERMUTATIONS
from iscc_bench.algos.metrics import jaccard
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.gutenberg import gutenberg
from iscc_bench.readers.mltext import mltext
from iscc_bench.textid.normalize import text_normalize
from iscc_bench.utils import load_text_file

rand = np.random.RandomState(seed=28)

MAX_UINT64 = (1 << 64) - 1
MASKS_64_NP = rand.randint(0, MAX_UINT64, 64, dtype=np.uint64)
MASKS_64 = MASKS_64_NP.tolist()


###############################################################################
# Reference implementation                                                    #
###############################################################################


def minhash_ref(features_32):
    features_32 = features_32.tolist()
    max_int64 = (1 << 64) - 1
    mersenne_prime = (1 << 61) - 1
    max_hash = (1 << 32) - 1
    hashvalues = [max_hash] * 128

    a, b = MINHASH_PERMUTATIONS

    for hv in features_32:
        nhs = []
        for x in range(128):
            nh = (((a[x] * hv + b[x]) & max_int64) % mersenne_prime) & max_hash
            nhs.append(min(nh, hashvalues[x]))
        hashvalues = nhs

    return hashvalues


def minhash_ref_opt(features_32):
    features_32 = features_32.tolist()
    max_int64 = (1 << 64) - 1
    mersenne_prime = (1 << 61) - 1
    max_hash = (1 << 32) - 1
    perms = [*zip(*MINHASH_PERMUTATIONS)]
    return [min(
            (((a * f + b) & max_int64) % mersenne_prime) & max_hash
            for f in features_32
    ) for a, b in perms[:128]]


def minhash_ref_np(features_32):
    _mersenne_prime = (1 << 61) - 1
    _max_hash = (1 << 32) - 1
    _hash_range = (1 << 32)

    hashvalues = np.ones(128, dtype=np.uint64) * _max_hash
    a, b = np.array(
        [MINHASH_PERMUTATIONS[0][:128],
         MINHASH_PERMUTATIONS[1][:128]],
        dtype=np.uint64
    )
    for hv in features_32:
        phv = np.bitwise_and((a * hv + b) % _mersenne_prime, np.uint64(_max_hash))
        hashvalues = np.minimum(phv, hashvalues)
    return hashvalues.tolist()


PERMS_NUMBA = np.array(
        [MINHASH_PERMUTATIONS[0][:128],
         MINHASH_PERMUTATIONS[1][:128]],
        dtype=np.uint64
    )


@njit
def minhash_ref_numba(features_32):
    _mersenne_prime = np.uint64((1 << 61) - 1)
    _max_hash = np.uint32((1 << 32) - 1)

    hashvalues = np.full(128, _max_hash, dtype=np.uint64)

    a = PERMS_NUMBA[0]
    b = PERMS_NUMBA[1]
    for hv in features_32:
        phv = np.bitwise_and((a * hv + b) % _mersenne_prime, np.uint64(_max_hash))
        hashvalues = np.minimum(phv, hashvalues)
    return hashvalues


###############################################################################
# Simplified implementations with XOR based random permutations               #
###############################################################################


def minhash_xor(features, masks=MASKS_64):
    """Pure Python implementation"""
    return [min([f ^ m for f in features.tolist()]) for m in masks]


def minhash_xor_np(features, masks=MASKS_64_NP):
    """Numpy supported implementation"""
    hashes = np.full(64, MAX_UINT64, dtype=np.uint64)
    for f in features:
        hashes = np.minimum(hashes, np.bitwise_xor(masks, f))
    return hashes.tolist()


@njit
def minhash_xor_numba(features, masks=MASKS_64_NP):
    """Numpy & Numba supported implementation"""
    hashes = np.full(64, MAX_UINT64, dtype=np.uint64)
    for f in features:
        hashes = np.minimum(hashes, np.bitwise_xor(masks, f))
    return hashes


###############################################################################
# Compare Universal Hash vs XOR at 192 permutations with 32 bit features      #
###############################################################################
MAX_UINT32 = 2 ** 32 - 1
PERMS_192_NP = rand.randint(0, MAX_UINT32, 192, dtype=np.uint32)


@njit
def minhash_xor_192(features_32, masks=PERMS_192_NP):
    """Numpy & Numba supported implementation"""
    hashes = np.full(192, np.uint32(MAX_UINT32))
    for f in features_32:
        hashes = np.minimum(hashes, np.bitwise_xor(masks, f))
    return hashes


PERMS_192 = np.array(
        [MINHASH_PERMUTATIONS[0][:192],
         MINHASH_PERMUTATIONS[1][:192]],
        dtype=np.uint64
    )

@njit
def minhash_ref_192(features_32):
    _mersenne_prime = np.uint64((1 << 61) - 1)
    _max_hash = np.uint32((1 << 32) - 1)

    hashvalues = np.full(192, _max_hash, dtype=np.uint64)

    a = PERMS_192[0]
    b = PERMS_192[1]
    for hv in features_32:
        phv = np.bitwise_and((a * hv + b) % _mersenne_prime, np.uint64(_max_hash))
        hashvalues = np.minimum(phv, hashvalues)
    return hashvalues


funcs_ref = (
    minhash_ref,
    minhash_ref_opt,
    minhash_ref_np,
    minhash_ref_numba,
)


funcs_xor = (
    minhash_xor,
    minhash_xor_np,
    minhash_xor_numba,
)

funcs_f32 = (
    minhash_ref,
    minhash_ref_opt,
    minhash_ref_np,
    minhash_ref_numba,
    minhash_xor_192,
    minhash_ref_192,
)


def compat():
    """Test compatibility of implementations"""
    features_32 = np.array(
        [xxh32_intdigest(rand.bytes(13)) for _ in range(100)],
        dtype=np.uint32
    )
    results = set()
    print('\nTesting minhash reference compatibility:\n')
    for func in funcs_ref:
        r = tuple(func(features_32))
        print(f'{func.__name__:<18}: {r}')
        results.add(r)
    assert len(results) == 1

    s = np.array(
        [xxh64_intdigest(rand.bytes(13)) for _ in range(100)],
        dtype=np.uint64
    )
    results = set()
    print('\nTesting minhash xor compatibility:\n')
    for func in funcs_xor:
        r = tuple(func(s))
        print(f'{func.__name__:<18}: {r}')
        results.add(r)
    # assert len(results) == 1


def performance():
    """
    Compare performance of xor based implementations with reference

    Results for 100k features:
        minhash_ref       : 6858.04 ms runtime
        minhash_ref_opt   : 3738.82 ms runtime
        minhash_ref_np    :  607.38 ms runtime
        minhash_ref_numba :   90.76 ms runtime
        minhash_xor       :  478.72 ms runtime
        minhash_xor_np    :  153.59 ms runtime
        minhash_xor_numba :   11.97 ms runtime
    """
    nfeat = 10000
    print(f'\nTesting minhash performance with {nfeat} features:\n')

    # Reference
    features_32 = np.array(
        [xxh32_intdigest(rand.bytes(13)) for _ in range(nfeat)],
        dtype=np.uint32
    )
    for func in funcs_f32:
        mh = func(features_32)
        start = time.time()
        mh = func(features_32)
        end = time.time()
        rt = (end - start) * 1000
        print(f'{func.__name__:<18}: {rt:.2f} ms runtime')

    # New versions
    features_64 = np.array(
        [xxh64_intdigest(rand.bytes(13)) for _ in range(nfeat)],
        dtype=np.uint64
    )

    for func in funcs_xor:
        mh = func(features_64)
        start = time.time()
        mh = func(features_64)
        end = time.time()
        rt = (end - start) * 1000
        print(f'{func.__name__:<18}: {rt:.2f} ms runtime')


def quality(seed=298):
    print('\nTesting minhash quality:\n')

    fps = list(chain(gutenberg(), mltext()))

    def chunkify(text):
        return [''.join(c) for c in sliding_window(text, 13)]

    def hashify_32(chunks):
        return np.array([xxh32_intdigest(f) for f in chunks], np.uint32)

    def hashify_64(chunks):
        return np.array([xxh64_intdigest(f) for f in chunks], np.uint64)

    # Minhash XOR 64
    sim_errs_ref = []
    dis_errs_ref = []
    for abc in sliding_window(fps, 3, 2, fillvalue=None):
        abc = list(abc)
        if abc[-1] is None:
            continue
        texts = (load_text_file(t) for t in abc)
        norm_texts = (text_normalize(t) for t in texts)
        chunked_texts = [chunkify(t) for t in norm_texts]
        feature_texts = [hashify_32(f) for f in chunked_texts]
        sim_sim = jaccard(feature_texts[0], feature_texts[1])
        sim_dis = jaccard(feature_texts[0], feature_texts[2])
        mhashes = [minhash_xor_numba(f) for f in feature_texts]
        mh_sim_sim = jaccard(mhashes[0], mhashes[1])
        mh_sim_dis = jaccard(mhashes[0], mhashes[2])
        sim_errs_ref.append(abs(sim_sim - mh_sim_sim))
        dis_errs_ref.append(abs(sim_dis - mh_sim_dis))
    print(
        f'minhash xor 64: '
        f'Error Sim Mean {mean(sim_errs_ref)} - '
        f'Max {max(sim_errs_ref)} - '
        f'Var {variance(sim_errs_ref)} | '
        f'Error Dis Mean {mean(dis_errs_ref)} - '
        f'Max {max(dis_errs_ref)} - '
        f'Var {variance(dis_errs_ref)}'
    )

    # Minhash Ref 64
    sim_errs_ref = []
    dis_errs_ref = []
    for abc in sliding_window(fps, 3, 2, fillvalue=None):
        abc = list(abc)
        if abc[-1] is None:
            continue
        texts = (load_text_file(t) for t in abc)
        norm_texts = (text_normalize(t) for t in texts)
        chunked_texts = [chunkify(t) for t in norm_texts]
        feature_texts = [hashify_32(f) for f in chunked_texts]
        sim_sim = jaccard(feature_texts[0], feature_texts[1])
        sim_dis = jaccard(feature_texts[0], feature_texts[2])
        mhashes = [minhash_ref_numba(f) for f in feature_texts]
        mh_sim_sim = jaccard(mhashes[0], mhashes[1])
        mh_sim_dis = jaccard(mhashes[0], mhashes[2])
        sim_errs_ref.append(abs(sim_sim - mh_sim_sim))
        dis_errs_ref.append(abs(sim_dis - mh_sim_dis))
    print(
        f'minhash ref 64: '
        f'Error Sim Mean {mean(sim_errs_ref)} - '
        f'Max {max(sim_errs_ref)} - '
        f'Var {variance(sim_errs_ref)} | '
        f'Error Dis Mean {mean(dis_errs_ref)} - '
        f'Max {max(dis_errs_ref)} - '
        f'Var {variance(dis_errs_ref)}'
    )

    # Minhash Ref 192
    sim_errs_ref = []
    dis_errs_ref = []
    for abc in sliding_window(fps, 3, 2, fillvalue=None):
        abc = list(abc)
        if abc[-1] is None:
            continue
        texts = (load_text_file(t) for t in abc)
        norm_texts = (text_normalize(t) for t in texts)
        chunked_texts = [chunkify(t) for t in norm_texts]
        feature_texts = [hashify_32(f) for f in chunked_texts]
        sim_sim = jaccard(feature_texts[0], feature_texts[1])
        sim_dis = jaccard(feature_texts[0], feature_texts[2])
        mhashes = [minhash_ref_192(f) for f in feature_texts]
        mh_sim_sim = jaccard(mhashes[0], mhashes[1])
        mh_sim_dis = jaccard(mhashes[0], mhashes[2])
        sim_errs_ref.append(abs(sim_sim - mh_sim_sim))
        dis_errs_ref.append(abs(sim_dis - mh_sim_dis))
    print(
        f'minhash ref 192: '
        f'Error Sim Mean {mean(sim_errs_ref)} - '
        f'Max {max(sim_errs_ref)} - '
        f'Var {variance(sim_errs_ref)} | '
        f'Error Dis Mean {mean(dis_errs_ref)} - '
        f'Max {max(dis_errs_ref)} - '
        f'Var {variance(dis_errs_ref)}'
    )


if __name__ == '__main__':
    compat()
    performance()
    quality(298)
