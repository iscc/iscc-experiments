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
    # 'Zl', 'Zp', 'Zs',
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


def text_normalize(text: str, keep_ws: bool = False) -> str:
    text = text.strip().lower()
    text = unicodedata.normalize(NFORM, text)
    text = text.translate(TR_TABLE)

    if keep_ws:
        text = ' '.join(text.split())
    else:
        text = ''.join(text.split())

    return text


def text_normalize_simple(text: str, keep_ws: bool = False) -> str:

    text = text.strip().lower()
    text = unicodedata.normalize(NFORM, text)

    chars = []
    for c in text:
        cat = unicodedata.category(c)
        if cat not in FILTR:
            chars.append(c)

    text = ''.join(chars)
    print(text)

    if keep_ws:
        text = ' '.join(text.split())
    else:
        text = ''.join(text.split())

    return text


"""
Always remove leading/trailing whitespace
Always remove duplicate whitspace
Always normalize whitespace (all \t,\r, \n becomes " ")
Optional remove all whitespace
"""


if __name__ == '__main__':
    text = '  Iñtërnâtiôn\nàlizætiøn☃💩 –  is a tric\t ky \u00A0 thing!\r'

    norm = text_normalize(text, keep_ws=False)
    norms = text_normalize_simple(text, keep_ws=False)
    print(norm)
    print(norms)
    assert norm == norms

    norm_kws = text_normalize(text, keep_ws=True)
    norms_kws = text_normalize_simple(text, keep_ws=True)
    print(norm_kws)
    print(norms_kws)
    assert norm_kws == norms_kws

    print(text_normalize_simple('Hello\nWorld', keep_ws=True))

