# -*- coding: utf-8 -*-
"""Read data from 'Open Library Data Dumps'.

Records: 25.5 Million
Size: 5.53 GB (compressed),
Info: https://openlibrary.org/developers/dumps
Data:
    https://openlibrary.org/data/ol_dump_authors_latest.txt.gz
    https://openlibrary.org/data/ol_dump_editions_latest.txt.gz


Instructions:
    Download datafiles and place them at (without decompressing):
    ./data/ol_dump_authors.txt.gz
    ./data/ol_dump_editions.txt.gz

Notes:
    First run will automatically index authors.

    There is also a `ol_dump_works_latest.txt.gz` file available that
    that might be usefull for futher research. It contains abstract
    works without isbns. Some editions link to these works.
"""
import os
import gzip
import json
import logging

import isbnlib
from sqlitedict import SqliteDict

from iscc_bench import DATA_DIR, MetaData


log = logging.getLogger(__name__)


DATA_FILE = os.path.join(DATA_DIR, 'ol_dump_editions.txt.gz')
DATA_FILE_AUTHORS = os.path.join(DATA_DIR, 'ol_dump_authors.txt.gz')
INDEX_FILE_AUTHORS = os.path.join(DATA_DIR, 'ol_dump_authors.sqlite')


def openlibrary(path=DATA_FILE):
    """Return a generator that iterates over all open library that have ISBN data.

    :param str path: path to directory with ol_dump_editions.txt.gz file
    :return: Generator[:class:`MetaData`] (filtered for records that have ISBNs)
    """

    skipped = 0
    authors = get_or_build_author_index(INDEX_FILE_AUTHORS)
    get_author_name = lambda ar: authors.get(ar['key'].split('/')[-1], '').strip()

    for line in iter_gz_lines(path, filter='isbn'):
        data = json.loads(line.split('\t')[4])
        raw_isbns = data.get('isbn_13') or data.get('isbn_10')
        if raw_isbns:
            try:
                title = data['title'].split(' : ')[0]
            except KeyError:
                log.debug('Skip entry (no title): {}'.format(data))
                skipped += 1
                continue

            author = ';'.join([get_author_name(ar) for ar in data.get('authors', [])])

            if not author.strip():
                log.debug('Skip entry (no author): {}'.format(data))
                skipped += 1
                continue

            for isbn in raw_isbns:
                if not isbnlib.notisbn(isbn):
                    isbn13 = isbnlib.to_isbn13(isbn)
                    meta = MetaData(isbn13, title, author)
                    yield meta

    log.info('Openlibrary skipped {} entries.'.format(skipped))


def get_or_build_author_index(index_file=INDEX_FILE_AUTHORS):
    """Return a dict like object that maps openlibrary author_ids to author names.

    :param str index_file: path to persistent index file (sqlite)
    :return: SqliteDict
    """
    return SqliteDict(index_file,  flag='r') if os.path.exists(INDEX_FILE_AUTHORS) else index_authors()


def index_authors(data_file=DATA_FILE_AUTHORS, index_file=INDEX_FILE_AUTHORS):
    """Index author data from ol_dump_authors.txt.gz into a sqlite database.

    :param str data_file: path to open library authors dump file
    :param str index_file: path to sqlite index file
    :return SqliteDict: dict like object that maps openlibrary author_ids to author names
    """

    indexed = 0
    authors_idx = SqliteDict(index_file, autocommit=False)

    log.info('Indexing authors (~6 Million)')

    for line in iter_gz_lines(data_file):

        data = json.loads(line.split('\t')[4])
        key = data['key'].split('/')[-1]
        author_name = (
            data.get('name') or
            data.get('personal_name') or
            data.get('fuller_name') or
            data.get('alternate_name')
        )

        if not author_name:
            log.debug('No author name: {}'.format(data))
            continue

        authors_idx[key] = author_name.strip()

        indexed += 1
        if not indexed % 1000000:
            log.info('Indexed {:,} authors'.format(indexed))

    authors_idx.commit()
    log.info('Indexed {:,} authors'.format(len(authors_idx)))

    return authors_idx


def iter_gz_lines(path=DATA_FILE, encoding='utf-8', filter=None):
    """Iterate over lines from .gz compressed textfile.
    :param str filter: Only yield lines that contain this string
    :return: Generator[str]
    """
    with gzip.open(path, 'rt', encoding=encoding) as gzfile:
        for line in gzfile:
            if filter:
                if filter in line:
                    yield line
            else:
                yield line


def count_records():
    """Count the number of records in data file."""
    with gzip.open(DATA_FILE) as f:
        for i, _ in enumerate(f):
            pass
    return i + 1


if __name__ == '__main__':
    # log_format = '%(asctime)s - %(levelname)s - %(message)s'
    # logging.basicConfig(level=logging.DEBUG, format=log_format)

    for md in openlibrary():
        print(md)
