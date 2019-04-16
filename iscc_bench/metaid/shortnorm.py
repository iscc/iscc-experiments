# -*- coding: utf-8 -*-
import unicodedata


def shortest_normalization_form():
    """
    Find unicode normalization that generates shortest utf8 encoded text.

    Result NFKC
    """
    s = 'Iñtërnâtiônàlizætiøn☃ and string escaping are ticky &#160; things'
    nfc = unicodedata.normalize('NFC', s)
    nfd = unicodedata.normalize('NFD', s)
    nfkc = unicodedata.normalize('NFKC', s)
    nfkd = unicodedata.normalize('NFKD', s)
    nfd_nfkc = unicodedata.normalize('NFKC', nfd)

    print('UTF-8 length of normalized strings:\n')
    print(f'NFC: {len(nfc.encode("utf8"))}')
    print(f'NFD: {len(nfd.encode("utf8"))}')
    print(f'NFKC: {len(nfkc.encode("utf8"))}')
    print(f'NFKD: {len(nfkd.encode("utf8"))}')
    print(f'NFD_NFKC: {len(nfd_nfkc.encode("utf8"))}')


if __name__ == '__main__':
    shortest_normalization_form()
