# -*- coding: utf-8 -*-
"""Test minhash forward compatibility.

Unintended collisions will rise with a growing set of similarity hashes.
This can only be mitigated by growing the hash size. We want to account for this
by calculating larger similarity vectors from the beginning and only keep part of it.
Should collisions require bigger fingerprints we can grow them while also staying
backward compatible.

Compare Error Rates of full minhash vector against full  and first 64 LSB-hash:

Results Gutenberg:
Minhash Vector:  Error Sim Mean 0.022 - Max 0.208 - Var 0.0020
Minhash 192 bit: Error Sim Mean 0.010 - Max 0.310 - Var 0.0011
Minhash 64 bit:  Error Sim Mean 0.016 - Max 0.391 - Var 0.0018

Results Mltext:
Minhash Vector:  Error Sim Mean 0.0141 - Max 0.137 - Var 0.00085
Minhash 192 bit: Error Sim Mean 0.0092 - Max 0.086 - Var 0.00027
Minhash 64 bit:  Error Sim Mean 0.0118 - Max 0.106 - Var 0.00062
"""
import numpy as np
from xxhash.cpython import xxh32_intdigest
from statistics import mean, variance

from iscc_bench.algos.metrics import jaccard
from iscc_bench.algos.minhash import minhash_ref_192
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.mltext import mltext
from iscc_bench.textid.normalize import text_normalize
from iscc_bench.utils import load_text_file


def chunkify(text):
    return ["".join(c) for c in sliding_window(text, 13)]


def featurize(chunks):
    return np.array([xxh32_intdigest(f) for f in chunks], np.uint32)


def bbitize(mh_sig, bits=192):
    mhashes = mh_sig.tolist()[:bits]
    return [(i, x & 1) for i, x in enumerate(mhashes)]


def main():
    fps = list(mltext())
    sim_errs_ref = []
    sim64_errs_ref = []
    sim192_errs_ref = []

    for ab in sliding_window(fps, 2, 2, fillvalue=None):
        ab = list(ab)
        if ab[-1] is None:
            continue
        texts = (load_text_file(t) for t in ab)
        norm_texts = (text_normalize(t) for t in texts)
        chunked_texts = [chunkify(t) for t in norm_texts]
        feature_texts = [featurize(f) for f in chunked_texts]
        sim_sim = jaccard(feature_texts[0], feature_texts[1])
        mhashes = [minhash_ref_192(f) for f in feature_texts]
        mh_sim_sim = jaccard(mhashes[0], mhashes[1])
        mh64_sim_sim = jaccard(bbitize(mhashes[0], 64), bbitize(mhashes[1], 64))
        mh192_sim_sim = jaccard(bbitize(mhashes[0], 192), bbitize(mhashes[1], 192))
        sim_errs_ref.append(abs(sim_sim - mh_sim_sim))
        sim64_errs_ref.append(abs(sim_sim - mh64_sim_sim))
        sim192_errs_ref.append(abs(sim_sim - mh192_sim_sim))

    print(
        f"Minhash Vector:"
        f"Error Sim Mean {mean(sim_errs_ref)} - "
        f"Max {max(sim_errs_ref)} - "
        f"Var {variance(sim_errs_ref)}\n"
    )

    print(
        f"Minhash 192 bit:"
        f"Error Sim Mean {mean(sim192_errs_ref)} - "
        f"Max {max(sim192_errs_ref)} - "
        f"Var {variance(sim192_errs_ref)}\n"
    )

    print(
        f"Minhash 64 bit:"
        f"Error Sim Mean {mean(sim64_errs_ref)} - "
        f"Max {max(sim64_errs_ref)} - "
        f"Var {variance(sim64_errs_ref)}\n"
    )


if __name__ == "__main__":
    main()
