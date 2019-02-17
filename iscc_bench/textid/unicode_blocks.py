# -*- coding: utf-8 -*-
"""Blocks of unicode ranges"""
from pprint import pprint

import requests
URL = "https://www.unicode.org/Public/UCD/latest/ucd/Blocks.txt"


def load_blocks():
    blocks = {}
    data = requests.get(URL).text
    for line in data.splitlines():
        if line and not line.startswith('#'):
            hex_range, name = line.split(';')
            int_range = tuple(int(i, 16) for i in hex_range.split('..'))
            blocks[int_range] = name.strip()
    return blocks


if __name__ == '__main__':
    b = load_blocks()
    pprint(b)
