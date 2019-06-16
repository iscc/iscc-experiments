# -*- coding: utf-8 -*-
"""Test similarity hashing of chomaprint vectors.

Notes: Requires fpcalc on your path (see: https://acoustid.org/chromaprint)
"""
import logging
import subprocess
import json
from typing import Sequence
from itertools import islice
import iscc

SPLIT_MIN_LOWEST = 5
HEAD_CID_A = b'\x14'
SYMBOLS = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
VALUES = ''.join([chr(i) for i in range(58)])
C2VTABLE = str.maketrans(SYMBOLS, VALUES)
V2CTABLE = str.maketrans(VALUES, SYMBOLS)
IDTABLE = str.maketrans(SYMBOLS, SYMBOLS)


log = logging.getLogger(__name__)


def generate_audio_id(filepath, partial= False):
    features = get_chroma_vector(filepath)
    minhash = iscc.minimum_hash(features, n=64)
    lsb = "".join([str(x & 1) for x in minhash])
    digest = int(lsb, 2).to_bytes(8, "big", signed=False)
    # 7. Prepend component header
    if partial:
        content_id_audio_digest = iscc.HEAD_CID_A_PCF + digest
    else:
        content_id_audio_digest = iscc.HEAD_CID_A + digest

    # 8. Encode and return
    return iscc.encode(content_id_audio_digest)


def get_chroma_vector(filepath) -> Sequence[int]:
    """Returns 32-bit (4 byte) integers as features"""
    cmd = ['fpcalc', filepath, '-raw', '-json']
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


if __name__ == '__main__':
    import os
    from iscc_bench.readers import fma_small
    import shutil
    from iscc_bench import DATA_DIR

    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    DUPES_PATH = os.path.join(DATA_DIR, 'audio_dupes')
    os.makedirs(DUPES_PATH, exist_ok=True)

    aids = {}
    log.info('check fma_medium for duplicate audio ids')
    for filepath in fma_small():
        try:
            aid = generate_audio_id(filepath)
            print(aid, filepath)
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
