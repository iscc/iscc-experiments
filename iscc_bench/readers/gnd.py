# -*- coding: utf-8 -*-
import os
import pickle

from iscc_bench import DATA_DIR
from lxml import etree


GND = os.path.join(DATA_DIR, 'GND.rdf')
PICKLE = os.path.join(DATA_DIR, 'gnd.pickle')


def get_creators():
    """extract creators from gnd and save memory while iterating"""
    context = etree.iterparse(
        GND,
        tag=("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description"),
        # remove_blank_text=True,
        # remove_comments=True,
        # remove_pis=True,
        # recover=True,
        # huge_tree=True
    )
    creators = {}
    for event, elem in context:
        if not elem.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"):
            continue
        if (elem.getparent().tag == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF"):
            name = extract_creator(elem)
        elif (elem.getparent().tag == "{http://www.w3.org/2002/07/owl#}sameAs"):
            name = extract_creator(elem)
        else:
            continue

        if name is not None:
            creator_id = \
                str(elem.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about")).split('http://d-nb.info/gnd/')[1]
            creators[creator_id] = name

        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    with open(PICKLE, 'wb') as f:
        pickle.dump(creators, f, pickle.HIGHEST_PROTOCOL)
    del context


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
    get_creators()