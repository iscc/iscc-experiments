# -*- coding: utf-8 -*-
from iscc_bench.readers import ALL_READERS


if __name__ == '__main__':
    for reader in ALL_READERS:
        for entry in reader():
            print(entry)
