# -*- coding: utf-8 -*-
from iscclib.meta import MetaID

from elasticsearch import Elasticsearch
from elasticsearch import helpers

es = Elasticsearch()


def action_generator(id_bits, shinglesize):
    for data in helpers.scan(es, index='iscc_meta_data', query={"query": {"match_all": {}}}):
        mid = MetaID.from_meta(
            data['_source']['title'], data['_source']['creator'], bits=id_bits, shinglesize=shinglesize
        )
        query = {
            "_index": "iscc_meta_id",
            "_id": 'meta_{}'.format(data['_id']),
            "_type": "default",
            "_source": {"meta_id": "{}".format(mid), "meta_data": data['_id']}
        }
        yield query


def generate_ids(id_bits, shinglesize):
    success = 0
    failed = 0
    for ok, item in helpers.streaming_bulk(es, action_generator(id_bits, shinglesize), chunk_size=50000,
                                           request_timeout=50):
        if ok:
            success += 1
        else:
            failed += 1

    print('Successful: {}'.format(success))
    print('Failed: {}'.format(failed))
    no_total_query = '{"query": {"bool": {"must_not": {"exists": {"field": "total"}}}}}'
    es.delete_by_query(index='iscc_result', body=no_total_query)
    results = {
        "bit_length": id_bits,
        "shingle_size": shinglesize
    }
    es.index(index='iscc_result', doc_type="default", body=results)


if __name__ == '__main__':
    generate_ids(24, 4)
