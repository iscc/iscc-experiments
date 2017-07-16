# -*- coding: utf-8 -*-
import os
import csv
from iscc_bench import DATA_DIR, MetaData
import isbnlib
import logging

log = logging.getLogger(__name__)


BXBOOKS_DATA = os.path.join(DATA_DIR, 'BX-Books.csv')


def bxbooks(path=BXBOOKS_DATA):
    """
    Parse, filter and yield data from Book-Crossing Dataset.
    http://www2.informatik.uni-freiburg.de/~cziegler/BX/

    :param str path: file path to bxbooks data
    :yield: MedaData
    """
    with open(path) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';')
        for row in reader:

            if isbnlib.notisbn(row['ISBN']):
                log.info('Skip row with invalid ISBN {}'.format(row['ISBN']))
                continue

            yield MetaData(
                isbn=isbnlib.to_isbn13(row['ISBN']),
                title=row['Book-Title'].split(' : ')[0],
                author=row['Book-Author']
            )


if __name__ == '__main__':
    for entry in bxbooks():
        print(entry)
