# -*- coding: utf-8 -*-
"""Find optimal window size for character n-grams:
Results with mltext:

Loss @ wsize 3: Mean 0.20117338217301212 - Min 0.015625 - Max 0.6935483870967742
Loss @ wsize 4: Mean 0.07995781400608308 - Min 0.0001 - Max 0.31666666666666665
Loss @ wsize 5: Mean 0.024160525979283035 - Min 0.0001 - Max 0.171875
Loss @ wsize 6: Mean 0.012285342217138626 - Min 0.0001 - Max 0.0625
Loss @ wsize 7: Mean 0.01360537774371701 - Min 0.0001 - Max 0.06349206349206349
Loss @ wsize 8: Mean 0.012737835358927722 - Min 0.0001 - Max 0.05084745762711865
Loss @ wsize 9: Mean 0.0035452797973165276 - Min 0.0001 - Max 0.031746031746031744
Loss @ wsize 10: Mean 0.0020080400013746855 - Min 0.0001 - Max 0.015873015873015872
Loss @ wsize 11: Mean 0.0027660155732893736 - Min 0.0001 - Max 0.015873015873015872
Loss @ wsize 12: Mean 0.004315988896252274 - Min 0.0001 - Max 0.03225806451612903
Loss @ wsize 13: Mean 0.00048059458498185445 - Min 0.0001 - Max 0.015625
Loss @ wsize 14: Mean 0.00204982670505105 - Min 0.0001 - Max 0.017543859649122806
"""
from iscc_bench.algos.metrics import containment
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.mltext import mltext
from iscc_bench.textid.normalize import text_normalize
from iscc_bench.textid.textid import minimum_hash_text
from iscc_bench.utils import load_text_file
from statistics import mean

WINDOW_SIZES = range(3, 40)


def test_with(ws=13, dataset=mltext, n_samples=100000):
    fps = list(dataset())[:n_samples]
    losses = []
    for a, b, c in sliding_window(fps, 3, 2, fillvalue=None):
        if c is None:
            continue
        ta, tb, tc = load_text_file(a), load_text_file(b), load_text_file(c)
        mha = minimum_hash_text(text_normalize(ta), ws)
        mhb = minimum_hash_text(text_normalize(tb), ws)
        mhc = minimum_hash_text(text_normalize(tc), ws)
        sim = containment(mha, mhb)
        dis = containment(mha, mhc)
        loss = (dis or 0.0001) / (sim or 0.0001)
        losses.append(loss)
    print(
        f"Loss @ wsize {ws}: Mean {mean(losses)} - Min {min(losses)} - Max {max(losses)}"
    )


if __name__ == "__main__":
    for ws in WINDOW_SIZES:
        test_with(ws)
