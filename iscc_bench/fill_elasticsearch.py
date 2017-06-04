# -*- coding: utf-8 -*-
from iscc_bench.readers import ALL_READERS
# from iscc_bench.elastic_search.bulk_insert import send_bulk_request
from iscc_bench.readers.dnbrdf import iter_isbns
from iscc_bench.readers import bxbooks

from elasticsearch import Elasticsearch
from elasticsearch import helpers

es = Elasticsearch()


def action_generator():
    src = "bx_books"
    for entry in bxbooks():
        yield {
            "_index": "iscc_meta",
            "_type": "default",
            "_id": entry.key,
            "_source": {"isbn": entry.isbn, "title": entry.title, "creator": entry.author, "source": src}
        }

import sys

def populate_elastic():
    for ok, item in helpers.streaming_bulk(es, action_generator(), chunk_size="50"):
        sys.stdout.write("test")
        sys.stdout.flush()
        # print(ok, item)
        # print("test")

if __name__ == '__main__':
    populate_elastic()