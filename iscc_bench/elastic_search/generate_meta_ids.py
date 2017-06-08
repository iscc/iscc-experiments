# -*- coding: utf-8 -*-
import time
from iscclib.meta import MetaID

from elasticsearch import Elasticsearch
from elasticsearch import helpers

es = Elasticsearch()

def action_generator(id_bits):
    for data in helpers.scan(es, index='iscc_meta_data', query={"query": {"match_all": {}}}):
        mid = MetaID.from_meta(
            data['_source']['title'], data['_source']['creator'], bits=id_bits
        )
        query = {
            "_index": "iscc_meta_id",
            "_id": 'meta_{}'.format(data['_id']),
            "_type": "default",
            "_source": {"meta_id": "{}".format(mid), "meta_data": data['_id']}
        }
        yield query

def generate_ids(id_bits):
    success = 0
    failed = 0
    for ok, item in helpers.streaming_bulk(es, action_generator(id_bits), chunk_size=50000):
        if ok:
            success += 1
        else:
            failed += 1

    print('Successful: {}'.format(success))
    print('Failed: {}'.format(failed))


if __name__ == '__main__':
    generate_ids(64)
