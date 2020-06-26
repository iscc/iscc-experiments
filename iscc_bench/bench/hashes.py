# -*- coding: utf-8 -*-
import hashlib
from xxhash import xxh64
from iscc_bench.bench.utils import system_info, benchmark, list_files
from iscc_bench.readers.harvard import HARVARD_DATA
from sha3 import keccak_256
from blake3 import blake3


hashers = (
    hashlib.md5,
    hashlib.sha1,
    hashlib.sha256,
    keccak_256,
    hashlib.blake2b,
    hashlib.blake2s,
    blake3,  # Winner
    xxh64,  # Non-Cryptographic
)

READ_SIZE = 1024 * 512


def get_hasher(hfunc):
    """Returns a hashfunc that can process paths"""

    def file_hash_func(fp):
        with open(fp, "rb") as infile:
            data = infile.read(READ_SIZE)
            hasher = hfunc(data)
            if not data:
                hasher.update(b"")
            while data:
                hasher.update(data)
                data = infile.read(READ_SIZE)
        return hasher.hexdigest()

    return file_hash_func


def benchmark_hashes():
    print(system_info())
    files = list_files(HARVARD_DATA)
    for func in hashers:
        benchmark(get_hasher(func), files, func.__name__)


if __name__ == "__main__":
    benchmark_hashes()
