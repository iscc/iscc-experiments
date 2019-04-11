# -*- coding: utf-8 -*-
"""Benchmark Text-ID for discriminative quality"""
import logging
import time
import iscc
from statistics import mean
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.gutenberg import gutenberg
from os.path import basename
from iscc_bench.textid import textid
from iscc_bench.utils import load_text_file

logr = logging.getLogger(__name__)


def benchmark():
    fps = list(gutenberg())
    cids = []  # Content IDs
    rts_abs = []  # Absolute runtimes
    rts_chr = []  # Runtimes per character
    matches = []
    sims = []
    diss = []
    losses = []
    for a, b, c in sliding_window(fps, 3, 2, fillvalue=None):
        if c is None:
            continue
        ta, tb, tc = load_text_file(a), load_text_file(b), load_text_file(c)
        for t in (ta, tb, tc):
            start = time.time()
            cid = textid.content_id_text(t)
            end = time.time()

            cids.append(cid)
            rabs = (end - start) * 1000.0
            rts_abs.append(rabs)
            rchar = rabs / len(t)
            rts_chr.append(rchar)

        matches.append(cids[-3] == cids[-2])
        sim_sim = iscc.distance(cids[-3], cids[-2])
        sim_dif = iscc.distance(cids[-3], cids[-1])
        sims.append(sim_sim)
        diss.append(sim_dif)
        loss = sim_sim / (sim_dif or 0.00001)
        losses.append(loss)
        logr.debug(f"Loss: {loss:.8f} Sim: {sim_sim} Dif: {sim_dif} ({basename(a)})")

    print(
        f"Runtime Absolute: Avg {mean(rts_abs):.5f} - Min {min(rts_abs):.5f} - Max {max(rts_abs):.5f}"
    )
    print(
        f"Runtime / Char:   Avg {mean(rts_chr):.5f} - Min {min(rts_chr):.5f} - Max {max(rts_chr):.5f}"
    )
    print(f"Matches {matches.count(True)} - Non-Matches {matches.count(False)}")
    print(
        f"Similarities:     Avg {mean(sims):.5f} - Min {min(sims):.5f} - Max {max(sims):.5f}"
    )
    print(
        f"Dissimilarities:  Avg {mean(diss):.5f} - Min {min(diss):.5f} - Max {max(diss):.5f}"
    )
    print(
        f"Losses:  Avg {mean(losses):.5f} - Min {min(losses):.5f} - Max {max(losses):.5f}"
    )


if __name__ == "__main__":
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    logging.basicConfig(level=logging.DEBUG, format=log_format)
    benchmark()
