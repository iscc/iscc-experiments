# -*- coding: utf-8 -*-
"""Read data from libgen catalog dump

Records: 1686652
Size: 968 MB (uncompressed)
Info: http://libgen.io/
Data: http://libgen.io/content/libgen_content.rar

Instructions:
    Download datafile, unrar and place at:
    ./data/libgen_content.csv
"""
import os
import csv
import logging
import isbnlib
from iscc_bench import DATA_DIR, MetaData


log = logging.getLogger(__name__)


LIBGEN_DATA = os.path.join(DATA_DIR, 'libgen_content.csv')


def libgen(path=LIBGEN_DATA):

    with open(path, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile, delimiter=',')
        for row in reader:

            title, creators, isbns = row[1].strip(), row[5].strip(), row[16].strip()

            if not all((title, creators, isbns)):
                log.info('Skip incomplete record {}'.format(row[0]))
                continue

            title = title.split(' : ')[0]
            creators = ';'.join(creators.split(','))

            for s in isbns.split(','):
                if not isbnlib.notisbn(s.strip()):
                    isbn = isbnlib.to_isbn13(s.strip())
                    yield MetaData(isbn, title, creators)
                    break


if __name__ == '__main__':
    for entry in libgen():
        print(entry)
