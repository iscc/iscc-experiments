# -*- coding: utf-8 -*-
import math
import os

from loguru import logger as log
import varint
import iscc
from iscc_bench.shortid.utils import (
    iscc_decode,
    HEAD_SID_PU,
    HEAD_SID_CB,
    b58i_encode,
    b58i_decode,
)


def short_id(code: str, chain: bytes = HEAD_SID_PU, count: int = 0) -> str:
    """Create Short-ID from full ISCC for given chain with counter 0"""
    digest = iscc_decode(code)
    cid = digest[10:13]
    did = digest[20:22]
    iid = digest[29:31]
    return iscc.encode(chain + cid + did + iid + varint.encode(count))


def incr(short_id: str) -> str:
    """Increment Short-ID"""
    digest = b58i_decode(short_id[:2]) + b58i_decode(short_id[2:])
    old_count = varint.decode_bytes(digest[8:])
    new_count = varint.encode(old_count + 1)
    head = b58i_encode(digest[:1])
    tail = b58i_encode(digest[1:8] + new_count)
    return head + tail


def chars_from_nbytes(nbytes):
    """To how many characters do n-bytes encode with Base58-ISCC?"""
    return math.ceil(math.log(256 ** nbytes, 58))


def code_length():
    """Demonstrate code length calculation"""
    for x in range(2, 37):
        b = os.urandom(x)
        head = b58i_encode(b[:1])
        tail = b58i_encode(b[1:])
        log.info("A: %s bytes = %s chars" % (x, len(head + tail)))
        log.info(
            "B: %s bytes = %s chars"
            % (x, chars_from_nbytes(1) + chars_from_nbytes(len(b) - 1))
        )
        log.info("C: %s sample = %s" % (x, head + tail))


def demo():
    """Varint Short-ID demo (create & increment)"""
    log.info("varint 0 %s" % varint.encode(0))
    log.info("varint 1 %s" % varint.encode(1))
    log.info("varint 127 %s" % varint.encode(127))
    log.info("varint 128 %s" % varint.encode(128))
    log.info("SID Header Private Use Hex: %s" % HEAD_SID_PU.hex())
    log.info("SID Header Private Use Base58-ISCC: %s" % iscc.encode(HEAD_SID_PU))
    log.info("SID Header Chain 1 Hex: %s" % HEAD_SID_CB.hex())
    log.info("SID Header Chain 1 Base58-ISCC: %s" % iscc.encode(HEAD_SID_CB))
    sc = short_id("CCHMv6dBdaeRt-CTFZ83Wzeqni5-CDjCodB8XmwhX-CRLTbsya3b7WP")
    log.info("Short-ID %s" % sc)
    sc = short_id("CCEHYMWPvwFJ9-CTTptP3nH1B1f-CDZfMns823tas-CRNqPhtfATiXX")
    log.info("Short-ID %s" % sc)
    for x in range(1, 260):
        sc = incr(sc)
        log.info("Short Code %s: %s" % (x, sc))


if __name__ == "__main__":
    code_length()
    demo()
