# -*- coding: utf-8 -*-
import time
from iscclib.meta import MetaID

from elasticsearch import Elasticsearch
from elasticsearch import helpers

es = Elasticsearch()

def action_generator():
    for data in helpers.scan(es, index='iscc_meta_data', query={"query": {"match_all": {}}}):
        mid = MetaID.from_meta(
            data['_source']['title'], data['_source']['creator']
        )
        query = {
            "_index": "iscc_meta_id",
            "_id": 'meta_{}'.format(data['_id']),
            "_type": "default",
            "_source": {"meta_id": "{}".format(mid), "meta_data": data['_id']}
        }
        yield query

start_time = time.time()
success = 0
failed = 0
for ok, item in helpers.streaming_bulk(es, action_generator(), chunk_size=50000):
    if ok:
        success += 1
    else:
        failed += 1

print('Successful: {}'.format(success))
print('Failed: {}'.format(failed))
print("Time: {}".format(time.time() - start_time))

