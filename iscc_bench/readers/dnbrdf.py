# -*- coding: utf-8 -*-
import operator
import os

import time

import isbnlib
from iscc_bench import DATA_DIR, MetaData
from collections import namedtuple
from lxml import etree

DNB_TITLES = os.path.join(DATA_DIR, 'DNBtitel.rdf')

BaseTitle = namedtuple('Title', 'title subtitle authors')

# @prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
# @prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
# @prefix owl: <http://www.w3.org/2002/07/owl#> .
# @prefix dc: <http://purl.org/dc/elements/1.1/> .
nsmap = {'dc': 'http://purl.org/dc/elements/1.1/'}

dropped = 0


def init_dropped():
    global dropped
    dropped = 0


def drop_elem():
    global dropped
    dropped += 1


class Title(BaseTitle):
    pass


def fast_iter(context, func, *args, **kwargs):
    """Save memory while iterating"""
    counter = 0
    init_dropped()
    start_time = time.time()
    entries = []
    last_parent = None
    for event, elem in context:
        if counter >= 1000:
            break
        if last_parent == elem.getparent():  # we iter over two tags so sometimes we visit the sam parent more than one time
            continue
        else:
            counter += 1
            last_parent = elem.getparent()

        function_entries = func(elem.getparent(), *args, **kwargs)
        if function_entries is not None:
            for entry in function_entries:
                entries.append(MetaData(
                    isbn=entry["isbn"],
                    title=entry["title"],
                    author=entry["author"]
                ))
        # It's safe to call clear() here because no descendants will be
        # accessed
        elem.clear()
        # Also eliminate now-empty references from the root node to elem
        for ancestor in elem.xpath('ancestor-or-self::*'):
            while ancestor.getprevious() is not None:
                del ancestor.getparent()[0]
    end_time = time.time()
    print("\nEinträge: " + str(counter))
    print("Dropped: " + str(dropped))
    print("Zeit: " + str(end_time - start_time))
    del context
    return entries


def process_entry(elem):
    title_count = 0
    creator_count = 0
    for child in elem.iterchildren():
        if child.tag == "{http://purl.org/dc/elements/1.1/}title":
            title_count += 1
        if child.tag == "{http://purl.org/dc/terms/}creator":
            resource = child.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
            if resource is not None:
                creator_count += 1
            else:
                crazy_creator = False
                for creatorchild in child.iterchildren():
                    if creatorchild.tag == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description":
                        for descriptionchild in creatorchild.iterchildren():
                            if descriptionchild.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredName" and descriptionchild.text is not None:
                                creator_count += 1
                            else:
                                crazy_creator = True
                    else:
                        crazy_creator = True
                    if crazy_creator:
                        print("\n\nCRAZY CREATOR\n\n")
    if title_count > 0 and creator_count > 0:
        if title_count > 1:
            print("\n\nCRAZY TITLE\n\n")
            drop_elem()
            return None
        entries = []
        titles = []
        creators = []
        isbns = []
        for child in elem.iterchildren():
            if child.tag == "{http://purl.org/dc/elements/1.1/}title":
                titles.append(child.text)

            if child.tag == "{http://purl.org/dc/terms/}creator":
                resource = child.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource')
                if resource is not None:
                    creators.append(child.attrib.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource'))
                else:
                    for creatorchild in child.iterchildren():
                        if creatorchild.tag == "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}Description":
                            for descriptionchild in creatorchild.iterchildren():
                                if descriptionchild.tag == "{http://d-nb.info/standards/elementset/gnd#}preferredName":
                                    creators.append(descriptionchild.text)

            if child.tag == "{http://purl.org/ontology/bibo/}isbn10" and child.text is not None:
                isbns.append(isbnlib.to_isbn13(child.text))
            if child.tag == "{http://purl.org/ontology/bibo/}isbn13" and child.text is not None:
                isbns.append(child.text)
        if len(isbns) == 0 or len(titles) == 0 or len(creators) == 0:
            print("Something went wrong.")
            drop_elem()
            return None
        # remove duplicate isbns
        isbns = list(set(isbns))
        for isbn in isbns:
            if isbn is not None:
                entries.append({
                    "isbn": isbn,
                    "title": ", ".join(titles),
                    "author": ", ".join(creators)
                })
        if len(entries) > 0:
            return entries
        else:
            drop_elem()
            return None
    else:
        drop_elem()
        return None


def iter_isbns():
    context = etree.iterparse(
        DNB_TITLES,
        tag=("{http://purl.org/ontology/bibo/}isbn10", "{http://purl.org/ontology/bibo/}isbn13"),
        # remove_blank_text=True,
        # remove_comments=True,
        # remove_pis=True,
        # recover=True,
        # huge_tree=True
    )
    return fast_iter(context, process_entry)


if __name__ == "__main__":
    iter_isbns()
