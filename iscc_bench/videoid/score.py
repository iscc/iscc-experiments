# -*- coding: utf-8 -*-
"""Find a good discriminative random seed for WTA hash.
v1 Winner Seed 10: AvgSim 3.75, AvgDis 29.833333333333332, AvgSpread 26.083333333333332
V2 Winner Seed 70: AvgSim 8.590909090909092, AvgDis 31.59090909090909, AvgSpread 23
"""
from os.path import basename
import iscc
from iscc_bench.readers.web_video import triplets
from iscc_bench.videoid.mp7 import content_id_video
from iscc_bench.videoid import mp7
from iscc_bench.videoid.mp7_v2 import content_id_video as cid_v2
from iscc_bench.videoid import mp7_v2
from loguru import logger as log
from statistics import mean


def score_v1():
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
            log.info(r)
        avg_sim = mean((e["sim"] for e in stats))
        avg_dis = mean((e["dis"] for e in stats))
        avg_spread = mean((e["spr"] for e in stats))
        log.info(
            f"Seed {seed}: AvgSim {avg_sim}, AvgDis {avg_dis}, AvgSpread {avg_spread}"
        )


def score_v2():
    for seed in range(0, 100):
        mp7_v2.WTA_SEED = seed
        stats = []
        for base, similar, unrelated in triplets():
            try:
                bid = cid_v2(base)
                sid = cid_v2(similar)
                uid = cid_v2(unrelated)
            except Exception:
                # log.error('failed signature creation')
                continue
            sim = iscc.distance(bid, sid)
            dis = iscc.distance(bid, uid)
            qid = basename(base).split("_")[0]
            r = dict(qid=qid, sim=sim, dis=dis, spr=dis - sim)
            stats.append(r)
            # log.info(r)
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
    score_v1()
    score_v2()
