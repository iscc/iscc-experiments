# -*- coding: utf-8 -*-
import math
import os
from loguru import logger as log
import varint
import iscc
from iscc_bench.shortid import bech32
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


def demo_code_length():
    """Demo code length calculation"""
    log.info("Code length calculation demo:")
    for x in range(2, 37):
        log.info(
            "B: %s bytes = %s calculated chars"
            % (x, chars_from_nbytes(1) + chars_from_nbytes(x - 1))
        )
        b = os.urandom(x)
        head = b58i_encode(b[:1])
        tail = b58i_encode(b[1:])
        log.info("A: %s bytes = %s actual chars" % (x, len(head + tail)))


def demo_varint():
    """Demo how varints are encoded"""
    log.info("Varint Demo:")
    for n in (0, 1, 15, 65, 127, 128, 255, 256, 512, 1024, 4097):
        log.info("varint %s = %s" % (n, varint.encode(n).hex()))
    log.info("-------------------------")


def demo_short_id():
    """Short-ID demo (create & increment)"""
    log.info("Short-ID Demo:")
    log.info("SID Header Private Use Hex: %s" % HEAD_SID_PU.hex())
    log.info("SID Header Private Use Base58-ISCC: %s" % iscc.encode(HEAD_SID_PU))
    log.info("SID Header Chain 1 Hex: %s" % HEAD_SID_CB.hex())
    log.info("SID Header Chain 1 Base58-ISCC: %s" % iscc.encode(HEAD_SID_CB))
    iscc_full = "CCHMv6dBdaeRt-CTFZ83Wzeqni5-CDjCodB8XmwhX-CRLTbsya3b7WP"
    sc = short_id(iscc_full)
    log.info("ISCC Code: %s" % iscc_full)
    log.info("Short-ID:  %s" % sc)
    iscc_full = "CCEHYMWPvwFJ9-CTTptP3nH1B1f-CDZfMns823tas-CRNqPhtfATiXX"
    sc = short_id(iscc_full, HEAD_SID_PU)
    log.info("ISCC Code: %s" % iscc_full)
    log.info("Short-ID:  %s" % sc)
    for x in range(1, 10):
        sc = incr(sc)
        log.info("Short-ID (private) %s: %s" % (x, sc))
    sc = short_id(iscc_full, HEAD_SID_CB)
    for x in range(1, 10):
        sc = incr(sc)
        log.info("Short-ID (coblo) %s: %s" % (x, sc))
    log.info("-------------------------")


def demo_bech32():
    byte_sizes = (8, 9, 36, 54)
    hrp = "cc"
    log.info("bech32-encoding")
    for x in byte_sizes:
        data_iscc = bech32.convertbits(os.urandom(x), 8, 5)
        iscc_bcoded = "".join([bech32.CHARSET[d] for d in data_iscc])
        log.info(f"ISCC-{x}: {iscc_bcoded.upper()} ({len(iscc_bcoded)} chars).")
        iscc_bcoded = bech32.bech32_encode(hrp, data_iscc)
        log.info(f"ISCC-{x}-HC: {iscc_bcoded.upper()} ({len(iscc_bcoded)} chars).")


def run_demos():
    demo_code_length()
    demo_varint()
    demo_short_id()
    demo_bech32()


if __name__ == "__main__":
    run_demos()
