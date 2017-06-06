# -*- coding: utf-8 -*-
import os
import pickle
import logging
from lxml import etree

import isbnlib
from iscc_bench import DATA_DIR, MetaData

DNB_TITLES = os.path.join(DATA_DIR, 'DNBtitel.rdf')
creators_gnd_file = os.path.join(DATA_DIR, 'gnd.pickle')
creators_gnd = pickle.load(open(creators_gnd_file, 'rb'))

log = logging.getLogger(__name__)


def dnbrdf():
    """Iter over isbn tags and save memory while iterating"""
    context = etree.iterparse(
        DNB_TITLES,
        tag=("{http://purl.org/ontology/bibo/}isbn10", "{http://purl.org/ontology/bibo/}isbn13"),
        # remove_blank_text=True,
        # remove_comments=True,
        # remove_pis=True,
        # recover=True,
        # huge_tree=True
    )
    parent = None
    # loop over every isbn10 or isbn13 element
    for event, elem in context:
        if parent == elem.getparent():  # we iter over two tags so sometimes we visit the same parent more than one time
            continue
        else:
            parent = elem.getparent()

        for entry in process_entry(parent):
            yield entry
        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    del context


def process_entry(elem):
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
                if creators_gnd[creator_id] is not None:
                    creators.append(creators_gnd[creator_id])
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
                yield MetaData(isbn, ", ".join(titles), ", ".join(creators))
    else:
        if len(titles) > 1:
            log.info('More than one title: Line {}'.format(elem.sourceline))


if __name__ == "__main__":
    dnbrdf()
