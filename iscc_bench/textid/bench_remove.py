# -*- coding: utf-8 -*-
"""Benchmark Character Removals

[Cc]	Other, Control
[Cf]	Other, Format
[Cn]	Other, Not Assigned (no characters in the file have this property)
[Co]	Other, Private Use
[Cs]	Other, Surrogate
[LC]	Letter, Cased
[Ll]	Letter, Lowercase
[Lm]	Letter, Modifier
[Lo]	Letter, Other
[Lt]	Letter, Titlecase
[Lu]	Letter, Uppercase
[Mc]	Mark, Spacing Combining
[Me]	Mark, Enclosing
[Mn]	Mark, Nonspacing
[Nd]	Number, Decimal Digit
[Nl]	Number, Letter
[No]	Number, Other
[Pc]	Punctuation, Connector
[Pd]	Punctuation, Dash
[Pe]	Punctuation, Close
[Pf]	Punctuation, Final quote (may behave like Ps or Pe depending on usage)
[Pi]	Punctuation, Initial quote (may behave like Ps or Pe depending on usage)
[Po]	Punctuation, Other
[Ps]	Punctuation, Open
[Sc]	Symbol, Currency
[Sk]	Symbol, Modifier
[Sm]	Symbol, Math
[So]	Symbol, Other
[Zl]	Separator, Line
[Zp]	Separator, Paragraph
[Zs]	Separator, Space


Benchmark Results:

Total 150.59351921081543 ms for remove_translate
Total 236.33980751037598 ms for remove_loop_set
Total 471.7671871185303 ms for remove_loop_cat
Total 212651.8795490265 ms for remove_regex
"""
import re
import time
import unicodedata
from os.path import exists

from tqdm import tqdm

from iscc_bench.readers.gutenberg import gutenberg
from iscc_bench.textid.unicode_blocks import codepoints
from iscc_bench.utils import load_text_file

FILTER_CATEGORIES = "CPZ"


def generate_blacklist() -> str:
    all_chars = (chr(i) for i in codepoints())
    bl = "".join(
        c for c in all_chars if unicodedata.category(c)[0] in FILTER_CATEGORIES
    )
    return bl


def save_blacklist():
    data = generate_blacklist().encode("utf8", "ignore")
    with open(f"blacklist_{FILTER_CATEGORIES}.txt", "wb") as outf:
        outf.write(data)


def load_blacklist():
    fname = f"blacklist_{FILTER_CATEGORIES}.txt"
    if not exists(fname):
        save_blacklist()
    with open(fname, "r", encoding="utf8") as infile:
        bl = infile.read()
    return bl


all_chars = (chr(i) for i in codepoints())
blacklist = "".join(
    c for c in all_chars if unicodedata.category(c)[0] in FILTER_CATEGORIES
)
blset = {c for c in blacklist}
blacklist_tbl = str.maketrans(dict.fromkeys(blset))
blacklist_re = re.compile("[%s]" % re.escape(blacklist))

print(f"Size of blacklisted character set: {len(blset)}\n")


def remove_translate(text):
    text = unicodedata.normalize("NFC", text)
    text = text.translate(blacklist_tbl)
    return text.lower()


def remove_loop_set(text):
    text = unicodedata.normalize("NFC", text)
    out = []
    for c in text:
        if c not in blset:
            out.append(c.lower())
    return "".join(out)


def remove_loop_cat(text):
    text = unicodedata.normalize("NFC", text)
    out = []
    for c in text:
        if unicodedata.category(c)[0] not in FILTER_CATEGORIES:
            out.append(c.lower())
    return "".join(out)


def remove_regex(text):
    text = unicodedata.normalize("NFC", text)
    text = text.lower()
    return blacklist_re.sub("", text)


funcs = (remove_loop_cat, remove_loop_set, remove_translate, remove_regex)


def benchmark():
    for func in funcs:
        rt = 0
        print(f"Benchmarking {func.__name__}:")
        for fp in list(gutenberg())[:3]:
            text = load_text_file(fp)
            start = time.time()
            result = func(text)
            end = time.time()
            rt += (end - start) * 1000
        print(f"Total {rt} ms for {func.__name__}\n\n")


if __name__ == "__main__":
    benchmark()
