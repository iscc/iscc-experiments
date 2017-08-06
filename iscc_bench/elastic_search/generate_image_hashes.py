# -*- coding: utf-8 -*-
#
# test_data should be named with number_errorType.type
# you can use the generate_test_images.py

import time

import math
from PIL import Image
import os
import dhash
from tabulate import tabulate

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from iscc_bench import DATA_DIR
from iscclib.image import ImageID

es = Elasticsearch()

IMAGE_DIR = os.path.join(DATA_DIR, 'images')

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
        "errorType": {
          "type": "keyword",
          "index": "true"
        },
        "aHash": {
          "type": "keyword",
          "index": "true"
        },
        "dHash": {
          "type": "keyword",
          "index": "true"
        },
        "pHash": {
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


def from_image_ahash(image):
    image = Image.open(image)
    image = image.convert("L").resize((8, 8), Image.ANTIALIAS)

    pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)

    bit_array = [pixel > avg for pixel in pixels]
    a_hash = 0
    for bit in bit_array:
        a_hash = (a_hash << 1) | bit
    return ImageID(ident=a_hash, bits=64)


def discrete_cosine_transform(value_list):
    N = len(value_list)
    result = []
    for k in range(N):
        value = 0.0
        for n in range(N):
            value += value_list[n] * math.cos(math.pi * k * (n + 0.5) / N)
        result.append(value)
    return result


def hamming_distance(id1, id2):
    symbols = u"H9ITDKR83F4SV12PAXWBYG57JQ6OCNMLUEZ"
    ident1 = 0
    for i, digit in enumerate(id1):
        ident1 += symbols.index(digit) * (len(symbols) ** i)
    ident2 = 0
    for i, digit in enumerate(id2):
        ident2 += symbols.index(digit) * (len(symbols) ** i)
    x = (ident1 ^ ident2) & ((1 << 64) - 1)
    tot = 0
    while x:
        tot += 1
        x &= x - 1
    return tot


def from_image_phash(image):
    hash_size = 8
    highfreq_factor = 4
    image = Image.open(image)
    img_size = hash_size * highfreq_factor
    image = image.convert("L").resize((img_size, img_size), Image.ANTIALIAS)

    pixels = list(image.getdata())
    pixel_lists = [pixels[x:x + img_size] for x in pixels]
    dct_list = []
    for i, pixel_list in enumerate(pixel_lists):
        if i == hash_size:
            break
        dct_list = dct_list + discrete_cosine_transform(pixel_list)[:hash_size]
    avg = sum(dct_list)/len(dct_list)
    bit_array = [value > avg for value in dct_list]
    p_hash = 0
    for bit in bit_array:
        p_hash = (p_hash << 1) | bit
    return ImageID(ident=p_hash, bits=64)


def get_error_types():
    total = es.count(index='iscc_images')['count']
    group_by = '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "errorType", "size": %s}}}}' % total
    res = es.search('iscc_images', body=group_by)
    buckets = res['aggregations']['group_by_state']['buckets']
    errorTypes = [bucket['key'] for bucket in buckets]
    errorTypes.remove('original')
    errorTypes.sort()
    return errorTypes


def init_index():
    if es.indices.exists(index='iscc_images'):
        es.indices.delete(index='iscc_images')
    es.indices.create(index='iscc_images', body=mapping_image)


def action_generator():
    a_time = 0
    d_time = 0
    p_time = 0
    w_time = 0
    total = 0
    total = es.count(index='iscc_images')['count']
    for image in os.listdir(IMAGE_DIR):
        img_file = os.path.join(IMAGE_DIR, image)
        name = image.split('.')[0]
        if len(name.split('_')) > 1:
            errorType = name.split('_')[1]
        else:
            errorType = 'original'
        start_time = time.time()
        aiid = from_image_ahash(img_file)
        a_time += time.time() - start_time
        start_time = time.time()
        diid = from_image_dhash(img_file)
        d_time += time.time() - start_time
        start_time = time.time()
        piid = from_image_phash(img_file)
        p_time += time.time() - start_time
        start_time = time.time()
        wiid = ImageID.from_image(img_file)
        w_time += time.time() - start_time
        total += 1
        query = {
            "_index": "iscc_images",
            "_type": "default",
            "_source": {"name": name.split('_')[0], "errorType": errorType,
                        "wHash": "{}".format(wiid), "dHash": "{}".format(diid), "aHash": "{}".format(aiid),
                        "pHash": "{}".format(piid)}
        }
        yield query
    print("aHash:", a_time / total)
    print("dHash:", d_time / total)
    print("pHash:", p_time / total)
    print("wHash:", w_time / total)


def generate_ids():
    success = 0
    failed = 0
    for ok, item in helpers.streaming_bulk(es, action_generator(), chunk_size=5000):
        if ok:
            success += 1
        else:
            failed += 1


def check_values(hash):
    total = es.count(index='iscc_images')['count']
    errors = {}
    group_by = '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "name", "size": %s}}}}' % total
    res = es.search('iscc_images', body=group_by)
    buckets = res['aggregations']['group_by_state']['buckets']
    for bucket in buckets:
        if bucket['doc_count'] > 1:
            get_by_key = {"query": {"terms": {'name': [bucket['key']]}}}
            value = None
            for entry in helpers.scan(es, index='iscc_images', query=get_by_key):
                if entry['_source']['errorType'] == "original":
                    value = entry['_source'][hash]
            for entry in helpers.scan(es, index='iscc_images', query=get_by_key):
                if not value == entry['_source'][hash]:
                    errorType = entry['_source']['errorType']
                    imageName = entry['_source']['name']
                    if not errorType in errors:
                        errors[errorType] = [imageName]
                    else:
                        errors[errorType].append(imageName)
    return errors


def get_hamming(hash):
    total = es.count(index='iscc_images')['count']
    distances = {}
    group_by = '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "name", "size": %s}}}}' % total
    res = es.search('iscc_images', body=group_by)
    buckets = res['aggregations']['group_by_state']['buckets']

    for bucket in buckets:
        if bucket['doc_count'] > 1:
            get_by_key = {"query": {"terms": {'name': [bucket['key']]}}}
            value = None
            for entry in helpers.scan(es, index='iscc_images', query=get_by_key):
                if entry['_source']['errorType'] == "original":
                    value = entry['_source'][hash]
            for entry in helpers.scan(es, index='iscc_images', query=get_by_key):
                hamming_dist = hamming_distance(value, entry['_source'][hash])
                errorType = entry['_source']['errorType']
                if not errorType in distances:
                    distances[errorType] = [hamming_dist]
                else:
                    distances[errorType].append(hamming_dist)
    return distances


def evaluate():
    errors = {}
    hamming_distances = {}
    hashes = ['aHash', 'dHash', 'pHash', 'wHash']
    for hash in hashes:
        errors[hash] = check_values(hash)

    errorTypes = get_error_types()
    table_rows = []
    for type in errorTypes:
        table_row = [type]
        for hash in hashes:
            if type in errors[hash]:
                table_row.append(len(errors[hash][type]))
            else:
                table_row.append(0)
        table_rows.append(table_row)
    print("\nDifferent Hashes (higher is worse)")
    print(tabulate(table_rows, headers=['Error Type'] + hashes))

    for hash in hashes:
        hamming_distances[hash] = get_hamming(hash)

    table_rows = []
    for type in errorTypes:
        table_row = [type]
        for hash in hashes:
            if type in hamming_distances[hash]:
                distances = hamming_distances[hash][type]
                table_row.append(sum(distances)/len(distances))
            else:
                table_row.append(0)
        table_rows.append(table_row)
    print("\nAverage Hamming Distances")
    print(tabulate(table_rows, headers=['Error Type'] + hashes))


if __name__ == '__main__':
    init_index()
    generate_ids()
    time.sleep(10)
    evaluate()
