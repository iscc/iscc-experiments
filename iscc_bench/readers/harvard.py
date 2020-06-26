# -*- coding: utf-8 -*-
"""Read data from 'Harvard Library Open Metadata'.

Records: ~12 Million
Size: 12.8 GigaByte (Unpacked)
Info: http://library.harvard.edu/open-metadata
Data: https://s3.amazonaws.com/hlom/harvard.tar.gz

Instructions:
    Download datafile and run `tar xvf harvard.tar.gz` to extract marc21 files.
    After moving the .mrc files to the /data/harvard folder you should be able
    to run this script and see log output of parsed data.
"""
import os
import logging

import isbnlib
from pymarc import MARCReader

from iscc_bench import DATA_DIR, MetaData


log = logging.getLogger(__name__)


HARVARD_DATA = os.path.join(DATA_DIR, "harvard")


def harvard(path=HARVARD_DATA):
    """Return a generator that iterates over all harvard records with complete metadata.

    :param str path: path to directory with harvard .mrc files
    :return: Generator[:class:`MetaData`] (filtered for records that have ISBNs)
    """

    for meta in marc21_dir_reader(path):
        if all((meta.isbn, meta.title, meta.author)) and not isbnlib.notisbn(meta.isbn):
            # Basic cleanup
            try:
                isbn = isbnlib.to_isbn13(meta.isbn)
                title = meta.title.strip("/").strip().split(" : ")[0]
                cleaned = MetaData(isbn, title, meta.author)
            except Exception:
                log.exception("Error parsing data")
                continue

            log.debug(cleaned)
            yield cleaned


def marc21_dir_reader(path=HARVARD_DATA):
    """Return a generator that iterates over all harvard marc21 files in a
    directory and yields parsed MetaData objects from those files.

    :param str path: path to directory with harvard .mrc files
    :return: Generator[:class:`MetaData`]
    """

    for marc21_file_name in os.listdir(path):

        marc21_file_path = os.path.join(path, marc21_file_name)
        log.info("Reading harvard marc21 file: {}".format(marc21_file_name))

        for meta_record in marc21_file_reader(marc21_file_path):
            yield meta_record


def marc21_file_reader(file_path):
    """Return a generator that yields parsed MetaData records from a harvard marc21 file.

    :param str file_path: path to harvard marc21 file
    :return: Generator[:class:`MetaData`]
    """

    with open(file_path, "rb") as mf:

        reader = MARCReader(mf, utf8_handling="ignore")

        while True:
            try:
                record = next(reader)
                yield MetaData(record.isbn(), record.title(), record.author())
            except UnicodeDecodeError as e:
                log.error(e)
                continue
            except StopIteration:
                break


if __name__ == "__main__":
    """Demo usage."""

    # logging.basicConfig(level=logging.DEBUG)

    for entry in harvard():
        # Do something with entry (MetaData object)
        print(entry)
