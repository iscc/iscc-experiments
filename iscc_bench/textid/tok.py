# -*- coding: utf-8 -*-
"""Test various tokenization strategies"""
from os.path import basename
from statistics import mean
import iscc
from iscc_bench.algos.metrics import containment
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.gutenberg import gutenberg


def split_ref(file_path):
    text = open(file_path, encoding="UTF8").read()

    # 1. Pre-normalize
    text = iscc.text_pre_normalize(text)

    # 2. Normalize
    text = iscc.text_normalize(text)

    # 3. Split to words
    w = text.split()

    # 4. Create 5 word shingles
    shingles = [
        "\u0020".join(l) for l in iscc.sliding_window(w, iscc.WINDOW_SIZE_CID_T)
    ]
    return shingles


def evaluate():
    fps = sorted(list(gutenberg()))
    cont_sim = []
    cont_dis = []
    for a, b, c in sliding_window(fps, size=3, step=2, fillvalue=None):
        if b is None:
            break
        if c is None:
            c = fps[0]
        print(basename(a), basename(b), basename(c))
        a, b, c = split_ref(a), split_ref(b), split_ref(c)
        print(len(a), a[2000:2003])
        print(len(b), b[2000:2003])
        print(len(c), c[2000:2003])
        a_b = containment(a, b)
        a_c = containment(a, c)
        print(f"Recall: {a_b}, Disc {a_c}", end="\n\n")
        cont_sim.append(a_b)
        cont_dis.append(a_c)
    print(f"AVG Sim {mean(cont_sim)}, AVG Dis {mean(cont_dis)}")


if __name__ == "__main__":
    evaluate()
