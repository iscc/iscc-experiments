# -*- coding: utf-8 -*-
"""Blocks of unicode ranges"""
import unicodedata
from pprint import pprint

import requests
URL = "https://www.unicode.org/Public/UCD/latest/ucd/Blocks.txt"


def load_blocks():
    """Load and parse unicode blocks from unicode standard"""
    blocks = {}
    data = requests.get(URL).text
    for line in data.splitlines():
        if line and not line.startswith('#'):
            hex_range, name = line.split(';')
            int_range = tuple(int(i, 16) for i in hex_range.split('..'))
            blocks[int_range] = name.strip()
    return blocks


def codepoints():
    """A list of all Unicode codepoints"""
    cps = []
    for block in load_blocks():
        for cp in range(block[0], block[1] + 1):
            cps.append(cp)
    return cps


def whitespace_codes():
    """All whitespace character codes"""
    ws = []
    for cp in codepoints():
        if unicodedata.category(chr(cp)) == 'Zs':
            ws.append(cp)
    return ws


def control_codes():
    """All control character codes"""
    cc = []
    for cp in codepoints():
        if unicodedata.category(chr(cp)).startswith("C"):
            cc.append(cp)
    return cc


if __name__ == '__main__':
    pprint(load_blocks())

