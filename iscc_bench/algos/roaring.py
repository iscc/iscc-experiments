# -*- coding: utf-8 -*-
"""Evaluate raoring bitmaps for 32-bit feature storage in ISCC metadata.

Dependencies:
    https://pypi.org/project/pyroaring/0.2.6/
    https://pypi.org/project/humanfriendly/4.17/


Results:

For 100 32-bit ints we need 1.01 KB storage instead of 400 bytes
For 1000 32-bit ints we need 9.98 KB storage instead of 4 KB
For 10000 32-bit ints we need 94.4 KB storage instead of 40 KB
For 100000 32-bit ints we need 609.37 KB storage instead of 400 KB
For 1000000 32-bit ints we need 2.52 MB storage instead of 4 MB

For orientation: An avarage novel has around 100.000 Words
"""
from pyroaring import BitMap
import struct
import os
from humanfriendly import format_size


def ints(amount=1000000):
    return [struct.unpack("<L", os.urandom(4))[0] for _ in range(amount)]


def main():
    for x in (100, 1000, 10000, 100000, 1000000):
        bm = BitMap(ints(x))
        data = bm.serialize()
        size = format_size(len(data))
        print(
            "For {} 32-bit ints we need {} storage instead of {}".format(
                x, size, format_size(4 * x)
            )
        )


if __name__ == "__main__":
    main()
