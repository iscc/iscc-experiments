# -*- coding: utf-8 -*-
"""Test unicode normalization performance.

Results:

norm_nfc function took 1389.312 ms
Normalized character count 116760763

norm_nfd function took 3024.914 ms
Normalized character count 119273103

norm_nfkc function took 4382.253 ms
Normalized character count 116826911

norm_nfkd function took 3148.581 ms
Normalized character count 119339249

filter_ws_stream function took 1245.701 ms
filter_ws_stream2 function took 1273.562 ms
filter_ws_stream3 function took 429.852 ms
filter_ws_stream4 function took 834.768 ms
"""
import unicodedata
from iscc_bench.readers.gutenberg import gutenberg
from iscc_bench.utils import timing

whitespace = {
    "\u0009",
    "\u000A",
    "\u000B",
    "\u000C",
    "\u000D",
    "\u0020",
    "\u0085",
    "\u00A0",
    "\u1680",
    "\u2000",
    "\u2001",
    "\u2002",
    "\u2003",
    "\u2004",
    "\u2005",
    "\u2006",
    "\u2007",
    "\u2008",
    "\u2009",
    "\u200A",
    "\u2028",
    "\u2029",
    "\u202F",
    "\u205F",
    "\u3000",
}


def is_ws(char):
    """Checks whether `char` is a whitespace character."""
    # \t, \n, and \r are control characters but we treat them as whitespace.
    if char == " " or char == "\t" or char == "\n" or char == "\r":
        return True
    cat = unicodedata.category(char)
    if cat == "Zs":
        return True
    return False


@timing
def filter_ws_stream():
    result = []
    for fp in list(gutenberg())[:20]:
        with open(fp, "r", encoding="utf-8") as stream:
            text = stream.read()
        for c in text:
            if not is_ws(c):
                result.append(c)


@timing
def filter_ws_stream2():
    result = []
    for fp in list(gutenberg())[:20]:
        with open(fp, "r", encoding="utf-8") as stream:
            while True:
                text = stream.read(4096)
                if not text:
                    break
                for c in text:
                    if not is_ws(c):
                        result.append(c)


@timing
def filter_ws_stream3():
    result = []
    for fp in list(gutenberg())[:20]:
        text = open(fp, "r", encoding="utf-8").read()
        for c in text:
            if c not in whitespace:
                result.append(c)


@timing
def filter_ws_stream4():
    result = []
    for fp in list(gutenberg())[:20]:
        text = open(fp, "r", encoding="utf-8").read()
        for c in text:
            if unicodedata.category(c) != "Zs":
                result.append(c)


@timing
def norm_nfd():
    tl = []
    for fp in list(gutenberg()):
        text = open(fp, "r", encoding="utf-8").read()
        nt = unicodedata.normalize("NFD", text)
        tl.append(len(nt))
    print(f"Normalized character count {sum(tl)}")


@timing
def norm_nfc():
    tl = []
    for fp in list(gutenberg()):
        text = open(fp, "r", encoding="utf-8").read()
        nt = unicodedata.normalize("NFC", text)
        tl.append(len(nt))
    print(f"Normalized character count {sum(tl)}")


@timing
def norm_nfkc():
    tl = []
    for fp in list(gutenberg()):
        text = open(fp, "r", encoding="utf-8").read()
        nt = unicodedata.normalize("NFKC", text)
        tl.append(len(nt))
    print(f"Normalized character count {sum(tl)}")


@timing
def norm_nfkd():
    tl = []
    for fp in list(gutenberg()):
        text = open(fp, "r", encoding="utf-8").read()
        nt = unicodedata.normalize("NFKD", text)
        tl.append(len(nt))
    print(f"Normalized character count {sum(tl)}")


if __name__ == "__main__":
    norm_nfc()
    norm_nfd()
    norm_nfkc()
    norm_nfkd()
    filter_ws_stream()
    filter_ws_stream2()
    filter_ws_stream3()
    filter_ws_stream4()
