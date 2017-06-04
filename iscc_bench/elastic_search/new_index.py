# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch
es = Elasticsearch()

mapping = '''
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

def new_index():
    es.indices.delete(index='iscc_meta')
    es.indices.create(index='iscc_meta', body=mapping)