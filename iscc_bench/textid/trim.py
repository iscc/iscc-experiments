# -*- coding: utf-8 -*-
"""Expermients with byte aligned text trimming"""
import time
import random
from iscc_bench.textid.unicode_blocks import load_blocks


INPUT_TRIM = 128
UNICODE_RANGES = list(load_blocks().keys())


def random_text(length: int) -> str:
    """Return random text build from UTF8-encodable random code points"""

    text = ''
    while len(text) < length:
        rng = random.choice(UNICODE_RANGES)
        text += chr(random.randrange(*rng))

    try:
        text.encode('utf-8')
        return text
    except UnicodeEncodeError:
        return random_text(length)


def trim_a(text: str, max_len=INPUT_TRIM) -> str:
    while True:
        data = text.encode('utf-8')
        if len(data) <= max_len:
            return text
        else:
            text = text[:-1]


def trim_b(text: str, max_len=INPUT_TRIM) -> str:
    return text.encode('utf-8')[:max_len].decode('utf-8', 'ignore')


def benchmark(n=1000):
    """Results:
    Runtime for trim_a: 0.07978653907775879
    Runtime for trim_b: 0.001994609832763672
    """
    print('Running benchmark ...')
    texts = [random_text(160) for _ in range(n)]

    start = time.time()
    for s in texts:
        t = trim_a(s)
    end = time.time()
    print(f'Runtime for trim_a: {end - start}')

    start = time.time()
    for s in texts:
        t = trim_b(s)
    end = time.time()
    print(f'Runtime for trim_b: {end - start}')


def test_compat(n=10000):
    print('Testing compatibility ...')
    for _ in range(n):
        text = random_text(160)
        trimmed_a = trim_a(text)
        trimmed_b = trim_b(text)
        if not trimmed_a == trimmed_b:
            print('Incompatible:', trimmed_a, trimmed_b)


def test_ambiguity(n=100000):
    print('Testing ambiguity ...')
    for _ in range(n):
        text = random_text(160)
        trimmed = trim_b(text)
        assert len(trimmed.encode('utf-8')) <= INPUT_TRIM
        assert text.startswith(trimmed)


if __name__ == '__main__':
    benchmark()
    test_compat()
    test_ambiguity()

