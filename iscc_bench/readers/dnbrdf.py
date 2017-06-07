# -*- coding: utf-8 -*-
"""Read data from 'German National Library'.

Records: 14.1 Million
Size: 2.6 GB (compressed),
Info: http://datendienst.dnb.de/cgi-bin/mabit.pl?userID=opendata&pass=opendata&cmd=login
Data:
    http://datendienst.dnb.de/cgi-bin/mabit.pl?cmd=fetch&userID=opendata&pass=opendata&mabheft=DNBTitel.rdf.gz
    http://datendienst.dnb.de/cgi-bin/mabit.pl?cmd=fetch&userID=opendata&pass=opendata&mabheft=GND.rdf.gz

Instructions:
    Download datafiles and place them at (without decompressing):
    ./data/DNBTitel.rdf.gz
    ./data/GND.rdf.gz

Notes:
    First run will automatically index authors.
"""
import os
import gzip
import logging
from lxml import etree

import isbnlib
from sqlitedict import SqliteDict

from iscc_bench import DATA_DIR, MetaData


log = logging.getLogger(__name__)


DATA_FILE = os.path.join(DATA_DIR, 'DNBtitel.rdf.gz')
DATA_FILE_AUTHORS = os.path.join(DATA_DIR, 'GND.rdf.gz')
INDEX_FILE_AUTHORS = os.path.join(DATA_DIR, 'gnd.sqlite')


def dnbrdf(path=DATA_FILE):
    """Return a generator that iterates over all metadata.

    :param str path: path to directory with DNBtitel.rdf.gz file
    :return: Generator[:class:`MetaData`] (filtered for records that have all metadata)
    """
    context = etree.iterparse(
        gzip.open(path),
        tag=(
            "{http://purl.org/ontology/bibo/}isbn10",
            "{http://purl.org/ontology/bibo/}isbn13"),
    )
    parent = None

    authors = get_or_build_author_index(INDEX_FILE_AUTHORS)

    # loop over every isbn10 or isbn13 element
    for event, elem in context:
        if parent == elem.getparent():  # we iter over two tags so sometimes we visit the same parent more than one time
            continue
        else:
            parent = elem.getparent()

        for entry in process_entry(parent, authors):
            yield entry
        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    del context


def get_or_build_author_index(index_file=INDEX_FILE_AUTHORS):
    """Return a dict like object that maps author_ids to author names.

    :param str index_file: path to persistent index file (sqlite)
    :return: SqliteDict
    """
    return SqliteDict(index_file,  flag='r') if os.path.exists(INDEX_FILE_AUTHORS) else index_authors()


def process_entry(elem, authors):
    titles = []
    creators = []
    isbns = []
    for child in elem.iterchildren():
        # get title
        if child.tag == "{http://purl.org/dc/elements/1.1/}title":
            titles.append(child.text)
        # get creators
        if child.tag == "{http://purl.org/dc/terms/}creator":
            resource = child.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
            if resource is not None:
                creator_id = str(resource).split('http://d-nb.info/gnd/')[1]
                if authors[creator_id] is not None:
                    creators.append(authors[creator_id])
            else:
                for description_tag in child.iterchildren():
                    if description_tag.tag == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description":
                        for creator_tag in description_tag.iterchildren():
                            if creator_tag.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredName" and creator_tag.text is not None:
                                creators.append(creator_tag.text)
                            else:
                                log.info('No Text in Creator Tag: Line {}'.format(description_tag.sourceline))
                    else:
                        log.info('No description Tag in Creator: Line {}'.format(description_tag.sourceline))
        # get isbns
        if child.tag == "{http://purl.org/ontology/bibo/}isbn10" and child.text is not None:
            isbns.append(isbnlib.to_isbn13(child.text))
        if child.tag == "{http://purl.org/ontology/bibo/}isbn13" and child.text is not None:
            isbns.append(child.text)
    if len(titles) == 1 and len(creators) > 0:  # we need a title and a creator
        # add one entry for every different isbn
        for isbn in list(set(isbns)):
            if isbn is not None:
                meta = MetaData(isbn, titles[0], ";".join(creators))
                log.debug(meta)
                yield meta
    else:
        if len(titles) > 1:
            log.warning('More than one title: Line {}'.format(elem.sourceline))


def index_authors(data_file=DATA_FILE_AUTHORS, index_file=INDEX_FILE_AUTHORS):
    """extract creators from gnd and save memory while iterating"""
    context = etree.iterparse(
        gzip.open(data_file), tag="{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description",
    )

    indexed = 0
    authors_idx = SqliteDict(index_file, autocommit=False)

    log.info('Indexing GND authors (~13.6 Million)')

    for event, elem in context:
        if not elem.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"):
            continue
        if elem.getparent().tag == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF":
            name = extract_creator(elem)
        elif elem.getparent().tag == "{http://www.w3.org/2002/07/owl#}sameAs":
            name = extract_creator(elem)
        else:
            continue

        if name is not None:
            creator_id = \
                str(elem.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")).split('http://d-nb.info/gnd/')[1]
            authors_idx[creator_id] = name
            log.debug('Indexing GND Author {} -> {}'.format(creator_id, name))

            indexed += 1
            if not indexed % 100000:
                log.info('Indexed {:,} authors'.format(indexed))

        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]

    authors_idx.commit()
    log.info('Indexed {:,} authors'.format(len(authors_idx)))

    del context
    return authors_idx


def extract_creator(elem):
    preferred = 0
    preferred_tags = [
        "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheCorporateBody",
        "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheConferenceOrEvent",
        "{http://d-nb.info/standards/elementset/gnd#}preferredNameForThePlaceOrGeographicName",
        "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheSubjectHeading",
        "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheWork",
        "{http://d-nb.info/standards/elementset/gnd#}preferredNameForThePerson",
        "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheFamily"
    ]
    for child in elem.iterchildren():
        if child.tag in preferred_tags:
            preferred += 1
            return child.text

if __name__ == "__main__":
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)

    for md in dnbrdf():
        pass

