# -*- coding: utf-8 -*-
"""Text normalization"""
import unicodedata
from iscc_bench.textid.const import UNICODE_RANGES

NFORM = 'NFD'  # Unicode Normalization form
LOWER = True   # Make all text lowercase

# Unicode categories to remove during text normalization
FILTR = frozenset({
    'Cc', 'Cf', 'Cn', 'Co', 'Cs',
    'Mc', 'Me', 'Mn',
    'Pc', 'Pd', 'Pe', 'Pf', 'Pi', 'Po', 'Ps',
    'Zl', 'Zp', 'Zs',
})


def chars():
    """Iterate over all unicode characters"""
    for block in UNICODE_RANGES:
        for cp in range(block[0], block[1] + 1):
            yield chr(cp)


def blacklist(filtr=FILTR):
    """Blacklisted unicode characters"""
    return [c for c in chars() if unicodedata.category(c) in filtr]


TR_TABLE = str.maketrans(dict.fromkeys(blacklist()))


def text_normalize(text: str) -> str:
    text = unicodedata.normalize(NFORM, text)
    text = text.translate(TR_TABLE)
    if LOWER:
        text = text.lower()
    return text


if __name__ == '__main__':
    text = 'Iñtërnâtiônàlizætiøn☃💩 – is a "ticky" \u00A0 thing!'
    norm = text_normalize(text)
    assert norm == "internationalizætiøn☃💩isatickything"
    print(text)
    print(norm)

