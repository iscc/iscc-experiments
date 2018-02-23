# -*- coding: utf-8 -*-
"""Test similarity hashing of chomaprint vectors.

Notes: Requires fpcalc on your path (see: https://acoustid.org/chromaprint)
"""
import logging
import subprocess
import json
from typing import Sequence
from itertools import islice
from hashlib import sha256
from iscc_bench.scripts.meta import simhash

SPLIT_MIN_LOWEST = 5
HEAD_CID_A = b'\x14'
SYMBOLS = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
VALUES = ''.join([chr(i) for i in range(58)])
C2VTABLE = str.maketrans(SYMBOLS, VALUES)
V2CTABLE = str.maketrans(VALUES, SYMBOLS)
IDTABLE = str.maketrans(SYMBOLS, SYMBOLS)

log = logging.getLogger(__name__)


def generate_audio_id(filepath):
    vec = get_chroma_vector(filepath)
    byte_features = tuple(v.to_bytes(4, 'big') for v in vec)

    a = byte_features
    b = tuple(sliding_window(byte_features, n=2))
    c = tuple(sliding_window(byte_features, n=3))

    n_grams = a + b + c
    hash_digests = [sha256(s).digest() for s in n_grams]

    splited_digests = []
    for h_dig in hash_digests:
        splited_digests.extend(
            [h_dig[i:i + 8] for i in range(0, len(h_dig), 8)])
    splited_digests.sort()
    min_hash_digests = splited_digests[:SPLIT_MIN_LOWEST]
    # Rehash so we don´t clutter lower hash spaces
    rehashed = [sha256(h).digest() for h in min_hash_digests]
    simhash_digest = simhash(rehashed)
    audio_id_digest = HEAD_CID_A + simhash_digest[:8]
    audio_id_code = encode(audio_id_digest)
    return audio_id_code


def get_chroma_vector(filepath) -> Sequence[int]:
    """Returns 32-bit (4 byte) integers as features"""
    cmd = ['fpcalc', '-raw', '-json', filepath]
    res = subprocess.run(cmd, stdout=subprocess.PIPE)
    vec = json.loads(res.stdout.decode('utf-8'))['fingerprint']
    return vec


def sliding_window(seq: Sequence[bytes], n=2) -> Sequence[bytes]:
    """Returns concatenated byte strings of window size n"""
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield b''.join(result)
    for elem in it:
        result = result[1:] + (elem,)
        yield b''.join(result)


def encode(digest: bytes) -> str:
    assert len(digest) == 9, "ISCC component digest must be 9 bytes."
    digest = reversed(digest)
    value = 0
    numvalues = 1
    for octet in digest:
        octet *= numvalues
        value += octet
        numvalues *= 256
    chars = []
    while numvalues > 0:
        chars.append(value % 58)
        value //= 58
        numvalues //= 58
    return str.translate(''.join([chr(c) for c in reversed(chars)]), V2CTABLE)


def decode(code: str) -> bytes:
    assert len(code) == 13, "ISCC component code must be 13 chars."
    bit_length = 72
    code = reversed(str.translate(code, C2VTABLE))
    value = 0
    numvalues = 1
    for c in code:
        c = ord(c)
        c *= numvalues
        value += c
        numvalues *= 58

    numvalues = 2 ** bit_length
    data = []
    while numvalues > 1:
        data.append(value % 256)
        value //= 256
        numvalues //= 256

    return bytes(reversed(data))


if __name__ == '__main__':
    import os
    from iscc_bench.readers import fma_medium
    import shutil
    from iscc_bench import DATA_DIR

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    DUPES_PATH = os.path.join(DATA_DIR, 'audio_dupes')
    os.makedirs(DUPES_PATH, exist_ok=True)

    aids = {}
    log.info('check fma_medium for duplicate audio ids')
    for filepath in fma_medium():
        try:
            aid = generate_audio_id(filepath)
        except Exception:
            continue
        if aid not in aids:
            aids[aid] = filepath
        else:
            print('Collision for {}: {} -> {}'.format(aid, filepath, aids[aid]))
            srca = filepath
            srcb = aids[aid]
            dsta = os.path.join(DUPES_PATH, aid + '_a.mp3')
            dstb = os.path.join(DUPES_PATH, aid + '_b.mp3')
            shutil.copy(srca, dsta)
            shutil.copy(srcb, dstb)

    log.info('done checking fma_medium for duplicate audio ids')
