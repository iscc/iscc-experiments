# -*- coding: utf-8 -*-
import re
import base64
from hashlib import sha256
import unicodedata
from typing import List, ByteString, Sequence


# Magic Constants
NGRAM_SIZE = 4

SPLIT_MIN_ALGO = True
SPLIT_MIN_LOWEST = 6


INPUT_TRIM_TITLE = 128
INPUT_TRIM_CREATORS = 0
INPUT_TRIM_EXTRA = 128

REMOVE_PARANTHESE = True
REMOVE_BRACKETS = True
REMOVE_SPACES = True

CUT_AFTER_COLON = True
CUT_AFTER_SEMICOLON = True
CUT_AFTER_SLASH = True
CUT_AFTER_DASH = False
CUT_AFTER_DOT = True
CUT_AFTER_COMMA = True

RGX_PARANTHESE = re.compile(r'\([^()]*\)', flags=re.UNICODE)
RGX_BRACKETS = re.compile(r'\[[^\]]*\]', flags=re.UNICODE)


def generate_meta_id(title: str, creators: str='', extra: str='', version: int=0) -> str:

    assert version == 0, "Only version 0 supported"

    title = unicodedata.normalize('NFKC', title)
    creators = unicodedata.normalize('NFKC', creators)
    extra = unicodedata.normalize('NFKC', extra)

    if REMOVE_PARANTHESE:
        title = re.sub(RGX_PARANTHESE, '', title)
        creators = re.sub(RGX_PARANTHESE, '', creators)
    if REMOVE_BRACKETS:
        title = re.sub(RGX_BRACKETS, '', title)
        creators = re.sub(RGX_BRACKETS, '', creators)

    if CUT_AFTER_COLON:
        title = title.split(':')[0].strip()
    if CUT_AFTER_SEMICOLON:
        title = title.split(';')[0].strip()
    if CUT_AFTER_SLASH:
        title = title.split('/')[0].strip()
    if CUT_AFTER_DASH:
        title = title.split('-')[0].strip()
    if CUT_AFTER_DOT:
        title = title.split('.')[0].strip()
    if CUT_AFTER_COMMA:
        title = title.split(',')[0].strip()

    title = title[:INPUT_TRIM_TITLE]
    extra = extra[:INPUT_TRIM_EXTRA]

    title = normalize_text(title)
    creators = normalize_creators(creators)
    creators = creators[:INPUT_TRIM_CREATORS]
    extra = normalize_text(extra)

    concat = '\u0020'.join((title, creators, extra)).rstrip('\u007C')

    a = sliding_window(concat, width=2)
    b = sliding_window(concat, width=3)
    c = sliding_window(concat, width=4)

    n_grams = a + b + c

    hash_digests = [sha256(s.encode('utf-8')).digest() for s in n_grams]

    if SPLIT_MIN_ALGO:
        # Trick: split digests to 8 byte chunks take the lowest x as features
        splited_digests = []
        for h_dig in hash_digests:
            splited_digests.extend([h_dig[i:i+8] for i in range(0, len(h_dig), 8)])
        splited_digests.sort()
        hash_digests = splited_digests[:SPLIT_MIN_LOWEST]
        # Rehash so we don´t clutter lower hash spaces
        hash_digests = [sha256(h).digest() for h in hash_digests]

    simhash_digest = simhash(hash_digests)
    prefix = b'\x00'
    suffix = simhash_digest[:7]
    meta_id_digest = prefix + suffix
    meta_id_code = base64.b32encode(meta_id_digest).rstrip(b'=').decode('ascii')

    return meta_id_code


def normalize_text(text: str) -> str:

    whitelist = 'LNS'
    decomposed = unicodedata.normalize('NFD', text)
    chars = []

    for c in decomposed:
        cat = unicodedata.category(c)
        if cat.startswith('Z'):
            chars.append(' ')
        elif cat[0] in whitelist:
            chars.append(c.lower())

    filtered = ''.join(chars)
    if REMOVE_SPACES:
        collapsed = ''.join(filtered.split())
    else:
        collapsed = '\u0020'.join(filtered.split())
    normalized = unicodedata.normalize('NFC', collapsed)

    return normalized


def normalize_creators(text: str) -> str:

    nonum = re.sub("\d+", "", text, flags=re.UNICODE)

    creators = []

    for creator in nonum.split(';'):

        if ',' in creator:
            creator = ' '.join(reversed(creator.split(',')[:2]))
        ncreators = normalize_text(creator)

        tokens = ncreators.split()
        if not tokens:
            continue
        if tokens[0] == tokens[-1]:
            abridged = tokens[0]
        else:
            abridged = tokens[0][0] + tokens[-1]
        creators.append(abridged)

    return '\u0020'.join(sorted(creators))


def sliding_window(text: str, width: int) -> List:

    assert width >= 2, "Sliding window width must be 2 or bigger."
    idx = range(max(len(text) - width + 1, 1))
    return [text[i:i + width] for i in idx]


def simhash(hash_digests: Sequence[ByteString]) -> ByteString:

    n_bytes = len(hash_digests[0])
    hashbits = (n_bytes * 8)

    vector = [0] * hashbits
    for token in hash_digests:

        assert len(token) == n_bytes, 'All digests must have the same number of bytes'

        h = int.from_bytes(token, 'big', signed=False)

        for i in range(hashbits):
            vector[i] += h & 1
            h >>= 1

    minfeatures = len(hash_digests) * 1. / 2

    shash = 0
    for i in range(hashbits):
        shash |= int(vector[i] >= minfeatures) << i

    return shash.to_bytes(n_bytes, 'big', signed=False)


def c2d(code: str) -> ByteString:

    return base64.b32decode(code + '===')


def c2i(code):

    digest = c2d(code)
    return int.from_bytes(digest[1:8], 'big', signed=False)


def hamming_distance(code1: str, code2: str) -> int:

    return bin(c2i(code1) ^ c2i(code2)).count('1')


if __name__ == '__main__':
    import os
    import statistics
    from iscc_bench import DATA_DIR

    def iter_pairs():
        fp = os.path.join(DATA_DIR, 'metapairs_10000.sample')
        with open(fp, encoding='UTF-8') as sample_file:
            for line in sample_file:
                yield tuple(line.strip('\n').split('|')[1:])

    hamming_distances = []
    true_positives = 0
    total = 0
    for row in iter_pairs():
        mid1 = generate_meta_id(row[0], row[1])
        mid2 = generate_meta_id(row[2], row[3])
        hd = hamming_distance(mid1, mid2)
        total += 1
        hamming_distances.append(hd)
        if mid1 == mid2:
            true_positives += 1
        else:
            print(mid1, mid2, hd, '\t', row)

    print('Max Hamming Distance %s' % max(hamming_distances))
    print('Mean Hamming Distance %s' % statistics.mean(hamming_distances))
    print('True Positives {} out of {}  ({}%)'.format(true_positives, total, true_positives/total * 100))
