# -*- coding: utf-8 -*-
import os
import time

from iscc_bench import DATA_DIR
from lxml import etree

GND = os.path.join(DATA_DIR, 'GND.rdf')
dropped = 0


def init_dropped():
    global dropped
    dropped = 0


def drop_elem():
    global dropped
    dropped += 1


def fast_iter(context):
    """Save memory while iterating"""
    counter = 0
    init_dropped()
    start_time = time.time()
    same = 0
    creators = {}

    for event, elem in context:
        if not elem.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"):
            drop_elem()
            continue
        if (elem.getparent().tag == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}RDF"):
            name = extract_creator(elem)
        elif (elem.getparent().tag == "{http://www.w3.org/2002/07/owl#}sameAs"):
            name = extract_creator(elem)
            same += 1
        else:
            drop_elem()
            continue

        if counter % 100000 == 0:
            print(counter)
        counter += 1

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
    end_time = time.time()
    print(creators["1218955-8"])
    print(creators["1218910-8"])
    print(creators["132071-3"])
    print("Dropped: {}".format(dropped))
    print("Same: {}".format(same))
    print("Zeit: {}".format(end_time - start_time))
    del context


def extract_creator(elem):
    preferred = 0
    for child in elem.iterchildren():
        if child.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheCorporateBody":
            preferred += 1
            return child.text
        if child.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheConferenceOrEvent":
            preferred += 1
            return child.text
        if child.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredNameForThePlaceOrGeographicName":
            preferred += 1
            return child.text
        if child.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheSubjectHeading":
            preferred += 1
            return child.text
        if child.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheWork":
            preferred += 1
            return child.text
        if child.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredNameEntityForThePerson":
            preferred += 1
        if child.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredNameForThePerson":
            preferred += 1
            return child.text
        if child.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredNameForTheFamily":
            preferred += 1
            return child.text
        if child.tag == "{http://www.w3.org/2002/07/owl#}sameAs":
            continue
    if preferred == 0:
        drop_elem()
        print("\nNo preffered Name")
        print(elem.attrib.get("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}about"))
        print("\n")
    else:
        print("preferredNameEntityForThePerson without preferredNameForThePerson")


def get_creators():
    context = etree.iterparse(
        GND,
        tag=("{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description"),
        # remove_blank_text=True,
        # remove_comments=True,
        # remove_pis=True,
        # recover=True,
        # huge_tree=True
    )
    return fast_iter(context)


if __name__ == "__main__":
    get_creators()
