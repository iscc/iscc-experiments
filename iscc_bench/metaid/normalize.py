# -*- coding: utf-8 -*-
"""Text Normalization for Meta-ID"""
import unicodedata


def test_normalize_meta(text):

    # Decode
    if isinstance(text, bytes):
        text = text.decode('utf-8')

    # Lowercase, remove leading, trainling and duplicate whitespace
    text = ' '.join(text.split()).strip().lower()

    # NFC Normalization
    text = unicodedata.normalize('NFD', text)

    # Remove C, M, P
    chars = []
    for c in text:
        cat = unicodedata.category(c)
        if cat[0] in 'CMP':
            continue
        chars.append(c)

    text = ''.join(chars)
    text = unicodedata.normalize('NFKC', text)

    return text


if __name__ == '__main__':
    s = ' Iñtërnâtiônàlizætiøn☃ and   string éscaping are ticky &#160; things '
    print(s)
    print(test_normalize_meta(s))
    print(len(test_normalize_meta(s)))
