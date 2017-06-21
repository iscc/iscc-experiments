# -*- coding: utf-8 -*-
from iscc_bench.readers import ALL_READERS

from elasticsearch import Elasticsearch
from elasticsearch import helpers

es = Elasticsearch()


def action_generator(reader):
    for entry in reader():
        yield {
            "_index": "iscc_meta_data",
            "_type": "default",
            "_id": entry.key,
            "_source": {"isbn": entry.isbn, "title": entry.title, "creator": entry.author, "source": reader.__name__}
        }

def populate_elastic(reader):
    success = 0
    failed = 0
    for ok, item in helpers.streaming_bulk(es, action_generator(reader), chunk_size=10000):
        if ok:
            success += 1
        else:
            failed += 1
    print('Successful: {}'.format(success))
    print('Failed: {}'.format(failed))


if __name__ == '__main__':
    for reader in ALL_READERS:
        populate_elastic(reader)