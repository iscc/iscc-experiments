#!/usr/bin/python
from iscclib.utils import sample_bytes
import hashlib
import pyblake2
import time


data = [sample_bytes(2048, x) for x in range(10000)]
hashers = (
    hashlib.md5,
    hashlib.sha1,
    hashlib.sha256,
    pyblake2.blake2b,
    pyblake2.blake2s,
)


for hasher in hashers:
    results = []
    start_time = time.time()
    for chunk in data:
        h = hasher(chunk).hexdigest()
    print("--- %s seconds for %s ---" % (time.time() - start_time, hasher.__name__))
