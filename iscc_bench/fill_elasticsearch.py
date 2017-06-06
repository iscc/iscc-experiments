# -*- coding: utf-8 -*-
from iscc_bench.readers import ALL_READERS

from elasticsearch import Elasticsearch
from elasticsearch import helpers

es = Elasticsearch()


def action_generator():
    for reader in ALL_READERS:
        for entry in reader():
            yield {
                "_index": "iscc_meta_data",
                "_type": "default",
                "_id": entry.key,
                "_source": {"isbn": entry.isbn, "title": entry.title, "creator": entry.author, "source": reader.__name__}
            }

def populate_elastic():
    for item in helpers.streaming_bulk(es, action_generator(), chunk_size=1000):
        print(item)

if __name__ == '__main__':
    populate_elastic()