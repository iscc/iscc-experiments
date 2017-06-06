# -*- coding: utf-8 -*-
from elasticsearch import Elasticsearch
from elasticsearch import helpers
es = Elasticsearch()

total = es.count(index='iscc_meta_data')

group_by_meta_id = '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "meta_id", "size": %s}}}}' % total['count']
group_by_isbn = '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "isbn", "size": %s}}}}' % total['count']

def get_meta_data(id):
    meta_id_query = {
      "query": {
        "terms": {
          "meta_id": [
            id
          ]
        }
      }
    }
    for entry in helpers.scan(es, index='iscc_meta_id', query=meta_id_query):
        meta_data_id = entry['_source']['meta_data']
        meta_data = es.get(index='iscc_meta_data', id=meta_data_id)
        yield meta_data['_source']

def get_meta_ids(isbn):
    meta_data_query = {
      "query": {
        "terms": {
          "isbn": [
            isbn
          ]
        }
      }
    }
    for entry in helpers.scan(es, index='iscc_meta_data', query=meta_data_query):
        meta_data_id = entry['_id']
        meta_id_entries = es.get(index='iscc_meta_id', id='meta_{}'.format(meta_data_id))
        yield meta_id_entries['_source']


def positives():
    res = es.search('iscc_meta_id', body=group_by_meta_id)
    buckets = res['aggregations']['group_by_state']['buckets']

    false_pos = 0
    true_pos = 0

    for bucket in buckets:
        if bucket['doc_count'] > 1:
            meta_data = get_meta_data(bucket['key'])
            isbn_list = [entry['isbn'] for entry in meta_data]
            if len(set(isbn_list)) > 1:
                false_pos += 1
            else:
                true_pos += 1
    print('True Positives: {}'.format(true_pos))
    print('False Positives: {}'.format(false_pos))


def negatives():
    res = es.search('iscc_meta_data', body=group_by_isbn)
    buckets = res['aggregations']['group_by_state']['buckets']

    false_neg = 0

    for bucket in buckets:
        if bucket['doc_count'] > 1:
            meta_ids = get_meta_ids(bucket['key'])
            meta_id_list = [entry['meta_id'] for entry in meta_ids]
            if len(set(meta_id_list)) > 1:
                false_neg += 1
    print('False Negatives: {}'.format(false_neg))


if __name__ == '__main__':
    print('Entries: {}'.format(total['count']))
    positives()
    negatives()
