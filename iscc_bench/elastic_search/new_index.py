# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch

es = Elasticsearch()

mapping_data = """
{
  "mappings": {
    "default": {
      "dynamic": "strict",
      "properties": {
        "isbn": {
          "type": "keyword",
          "index": "true"
        },
        "title": {
          "type": "keyword",
          "index": "true"
        },
        "creator": {
          "type": "keyword",
          "index": "true"
        },
        "source": {
          "type": "keyword",
          "index": "true"
        },
        "meta_id": {
          "type": "keyword",
          "index": "true"
        }
      }
    }
  }
}"""

mapping_id = """
{
  "mappings": {
    "default": {
      "dynamic": "strict",
      "properties": {
        "meta_id": {
          "type": "keyword",
          "index": "true"
        },
        "meta_data": {
          "type": "keyword",
          "index": "true"
        }
      }
    }
  }
}"""

mapping_result = """
{
  "mappings": {
    "default": {
      "dynamic": "strict",
      "properties": {
        "bit_length": {
          "type": "keyword",
          "index": "true"
        },
        "shingle_size": {
          "type": "keyword",
          "index": "true"
        },
        "total": {
          "type": "keyword",
          "index": "true"
        },
        "mid_groups": {
          "type": "keyword",
          "index": "true"
        },
        "same_isbn": {
          "type": "keyword",
          "index": "true"
        },
        "isbn_groups": {
          "type": "keyword",
          "index": "true"
        },
        "same_mid": {
          "type": "keyword",
          "index": "true"
        },
        "entry_sources": {
          "type": "keyword",
          "index": "true"
        }
      }
    }
  }
}"""


def new_data_index():
    if es.indices.exists(index="iscc_meta_data"):
        es.indices.delete(index="iscc_meta_data")
    es.indices.create(index="iscc_meta_data", body=mapping_data)


def new_id_index():
    if es.indices.exists(index="iscc_meta_id"):
        es.indices.delete(index="iscc_meta_id")
    es.indices.create(index="iscc_meta_id", body=mapping_id)


def new_result_index():
    if es.indices.exists(index="iscc_result"):
        es.indices.delete(index="iscc_result")
    es.indices.create(index="iscc_result", body=mapping_result)


if __name__ == "__main__":
    new_data_index()
    new_id_index()
    new_result_index()
