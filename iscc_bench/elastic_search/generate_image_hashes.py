# -*- coding: utf-8 -*-
import time
from PIL import Image
import os
import dhash

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from iscc_bench import DATA_DIR
from iscclib.image import ImageID

es = Elasticsearch()

IMAGE_DIR = os.path.join(DATA_DIR, 'images\src')

mapping_image = '''
{
  "mappings": {
    "default": {
      "dynamic": "strict",
      "properties": {
        "name": {
          "type": "keyword",
          "index": "true"
        },
        "type": {
          "type": "keyword",
          "index": "true"
        },
        "dHash": {
          "type": "keyword",
          "index": "true"
        },
        "wHash": {
          "type": "keyword",
          "index": "true"
        }
      }
    }
  }
}'''


def from_image_dhash(image):
    image = Image.open(image)
    d_hash = dhash.dhash_int(image, 5)
    return ImageID(ident=d_hash, bits=64)

def init_index():
    if es.indices.exists(index='iscc_images'):
        es.indices.delete(index='iscc_images')
    es.indices.create(index='iscc_images', body=mapping_image)


def action_generator():
    for image in os.listdir(IMAGE_DIR):
        img_file = os.path.join(IMAGE_DIR, image)
        wiid = ImageID.from_image(img_file)
        diid = from_image_dhash(img_file)
        query = {
            "_index": "iscc_images",
            "_type": "default",
            "_source": {"name": image.split('.')[0].split('_')[0], "type": image.split('.')[1],
                        "wHash": "{}".format(wiid), "dHash": "{}".format(diid)}
        }
        yield query


def generate_ids():
    success = 0
    failed = 0
    for ok, item in helpers.streaming_bulk(es, action_generator(), chunk_size=5000):
        if ok:
            success += 1
        else:
            failed += 1


def check_values(type1, type2):
    passed = True
    group_by = '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "%s", "size": 1000}}}}' % type1
    res = es.search('iscc_images', body=group_by)
    buckets = res['aggregations']['group_by_state']['buckets']
    for bucket in buckets:
        if bucket['doc_count'] > 1:
            get_by_key = {"query": {"terms": {type1: [bucket['key']]}}}
            value = None
            for entry in helpers.scan(es, index='iscc_images', query=get_by_key):
                if value:
                    if not value == entry['_source'][type2]:
                        passed = False
                        print('Fail with %s %s' % (type1, bucket['key']))
                else:
                    value = entry['_source'][type2]
    return passed


def evaluate():
    check_1 = check_values('name', 'wHash')
    check_2 = check_values('name', 'dHash')
    check_3 = check_values('wHash', 'name')
    check_4= check_values('dHash', 'name')
    if check_1 and check_2 and check_3 and check_4:
        print('All tests passed.')


if __name__ == '__main__':
    init_index()
    generate_ids()
    time.sleep(10)
    evaluate()
