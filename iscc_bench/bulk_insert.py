# -*- coding: utf-8 -*-

from elasticsearch import Elasticsearch
from elasticsearch import helpers
es = Elasticsearch()

def send_bulk_request(entries, src):
    actions = [
        {
            "_index": "iscc_meta",
            "_type": "default",
            "_source": {"isbn": entry.isbn, "title": entry.title, "creator": entry.author, "source": src}
        }
        for entry in entries
    ]
    helpers.bulk(es, actions)