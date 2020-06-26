# -*- coding: utf-8 -*-
"""Benchmark Text Normalization"""
import time
from statistics import mean
import unicodedata
import iscc
from iscc_bench.readers.gutenberg import gutenberg
from iscc_bench.textid.normalize import text_normalize, text_normalize_simple

REMOVE_WHITESPACE = False
REMOVE_ACCENTS = False
REMOVE_PUNCTUATION = False
REMOVE_CASE = True
REMOVE_CONTROL = True
REMOVE_HYPHENS = True


def benchmark(norm_func=iscc.text_normalize):
    fps = list(gutenberg())
    rts_abs = []  # Absolute runtimes
    rts_chr = []  # Runtimes per character
    ratios = []  # Size reduction ratios
    samples = []
    for fp in fps:
        with open(fp, "r", encoding="utf-8") as infile:
            text = infile.read()
        start = time.time()
        text_norm = norm_func(text)
        end = time.time()

        rabs = (end - start) * 1000.0
        rts_abs.append(rabs)

        rchar = rabs / len(text)
        rts_chr.append(rchar)

        ratio = len(text_norm) / len(text)
        ratios.append(ratio)
        samples.append(text_norm[5000:5256])

    print(
        f"Runtime Absolute: Avg {mean(rts_abs):.5f} - Min {min(rts_abs):.5f} - Max {max(rts_abs):.5f}"
    )
    print(
        f"Runtime / Char:   Avg {mean(rts_chr):.5f} - Min {min(rts_chr):.5f} - Max {max(rts_chr):.5f}"
    )
    print(
        f"Size Ratio:       Avg {mean(ratios):.5f} - Min {min(ratios):.5f} - Max {max(ratios):.5f}"
    )


def whitespace_norm(text):
    return " ".join(text.split())


def nfc_norm(text):
    return unicodedata.normalize("NFC", text)


def filter_norm(text):
    """Strip Accents"""
    text = unicodedata.normalize("NFD", text)
    output = []
    for char in text:
        cat = unicodedata.category(char)
        if cat == "Mn":
            continue
        if cat[0] in "LSNZ":
            output.append(char)
    filtered = "".join(output)
    return filtered


def lower(text):
    return text.lower()


def minimal_fast(text):
    text = unicodedata.normalize("NFC", text)
    text = "".join(text.split())
    text = text.lower()
    return text


def norm_filter(text):
    text = minimal_fast(text)
    text = filter_norm(text)
    return text


if __name__ == "__main__":
    # print('Benchmarking iscc reference ...\n')
    # benchmark(iscc.text_normalize)
    #
    # print('\n\nBenchmark minimal_fast (NFC + split & join + lowercase) ...\n')
    # benchmark(minimal_fast)
    #
    # print('\n\nBenchmark filter_norm (remove accents) ... \n')
    # benchmark(norm_filter)

    print("\n\nNew text normalization (v.1.1). Simple reference implementation \n")
    benchmark(text_normalize_simple)

    print("\n\nNew text normalization (v.1.1). Performance optimized implementation \n")
    benchmark(text_normalize)
