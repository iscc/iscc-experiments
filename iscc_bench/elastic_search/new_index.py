# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch
es = Elasticsearch()

mapping_data = '''
{
  "mappings": {
    "default": {
      "dynamic": "strict",
      "properties": {
        "isbn": {
          "type": "string",
          "index": "not_analyzed"
        },
        "title": {
          "type": "string",
          "index": "not_analyzed"
        },
        "creator": {
          "type": "string",
          "index": "not_analyzed"
        },
        "source": {
          "type": "string",
          "index": "not_analyzed"
        },
        "meta_id": {
          "type": "string",
          "index": "not_analyzed"
        }
      }
    }
  }
}'''

mapping_id = '''
{
  "mappings": {
    "default": {
      "dynamic": "strict",
      "properties": {
        "meta_id": {
          "type": "string",
          "index": "not_analyzed"
        },
        "meta_data": {
          "type": "string",
          "index": "not_analyzed"
        }
      }
    }
  }
}'''

def new_index():
    if es.indices.exists(index='iscc_meta_data'):
        es.indices.delete(index='iscc_meta_data')
    es.indices.create(index='iscc_meta_data', body=mapping_data)
    if es.indices.exists(index='iscc_meta_id'):
        es.indices.delete(index='iscc_meta_id')
    es.indices.create(index='iscc_meta_id', body=mapping_id)

if __name__ == '__main__':
    new_index()