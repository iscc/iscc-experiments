# -*- coding: utf-8 -*-
"""Find a good discriminative random seed for WTA hash.
Winner: Seed 10: AvgSim 3.75, AvgDis 29.875, AvgSpread 26.125
"""
from os.path import basename
import iscc
from iscc_bench.readers.web_video import triplets
from iscc_bench.videoid.mp7 import content_id_video
from iscc_bench.videoid import mp7
from loguru import logger as log
from statistics import mean


def score():
    for seed in range(9, 12):
        mp7.WTA_SEED = seed
        stats = []
        for base, similar, unrelated in triplets():
            bid = content_id_video(base)
            sid = content_id_video(similar)
            uid = content_id_video(unrelated)
            sim = iscc.distance(bid, sid)
            dis = iscc.distance(bid, uid)
            qid = basename(base).split("_")[0]
            r = dict(qid=qid, sim=sim, dis=dis, spr=dis - sim)
            stats.append(r)
            log.debug(r)
        avg_sim = mean((e["sim"] for e in stats))
        avg_dis = mean((e["dis"] for e in stats))
        avg_spread = mean((e["spr"] for e in stats))
        log.info(
            f"Seed {seed}: AvgSim {avg_sim}, AvgDis {avg_dis}, AvgSpread {avg_spread}"
        )


if __name__ == "__main__":
    import sys

    log.remove()
    log.add(sys.stderr, level="INFO")
    score()
