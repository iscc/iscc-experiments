# -*- coding: utf-8 -*-
#
# test_data should be named with number_errorType.type
# you can use the generate_test_images.py

import math
import os
import time

from PIL import Image
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from iscc_bench import DATA_DIR
from iscc_bench.readers.blockhash import blockhash
from iscclib.image import ImageID
from tabulate import tabulate

es = Elasticsearch()

IMAGE_DIR = os.path.join(DATA_DIR, "images")

mapping_image = """
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
        "bHash": {
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
}"""


def discrete_cosine_transform(value_list):
    N = len(value_list)
    result = []
    for k in range(N):
        value = 0.0
        for n in range(N):
            value += 2 * value_list[n] * math.cos(math.pi * k * (2 * n + 1) / (2 * N))
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


def my_median(lst):
    lst = sorted(lst)
    n = len(lst)
    if n < 1:
        return None
    if n % 2 == 1:
        return lst[n // 2]
    else:
        return sum(lst[n // 2 - 1 : n // 2 + 1]) / 2.0


def wavelet2d(data):
    N = int(len(data) / 2)
    while N > 1:
        # cut vertical
        for j, row in enumerate(data):
            output = [entry for entry in row]
            for i in range(N):
                output[i] = row[2 * i] + row[2 * i + 1]
                output[i + N] = row[2 * i] - row[2 * i + 1]
            data[j] = output
        # cut horizontal
        data_t = list(map(list, zip(*data)))
        for j, row in enumerate(data_t):
            output = [entry for entry in row]
            for i in range(N):
                output[i] = row[2 * i] + row[2 * i + 1]
                output[i + N] = row[2 * i] - row[2 * i + 1]
            data_t[j] = output
        data = list(map(list, zip(*data_t)))

        N = int(N / 2)
    return data


def a_hash(img_file):
    image = Image.open(img_file)
    image = image.convert("L").resize((8, 8), Image.BICUBIC)

    pixels = list(image.getdata())
    avg = sum(pixels) / len(pixels)

    bit_array = [pixel > avg for pixel in pixels]
    bitstring = ""
    for bit in bit_array:
        if bit:
            bitstring += "1"
        else:
            bitstring += "0"
    return ImageID(ident=int(bitstring, 2), bits=64)


def b_hash(img_file):
    image = Image.open(img_file)
    image = image.convert("L").resize(
        (min(image.size[0], 256), min(image.size[1], 256)), Image.BICUBIC
    )
    image = image.convert("RGB")
    b_hash = blockhash(image, 8)
    b_hash = int(b_hash, 16)
    return ImageID(ident=b_hash, bits=64)


def d_hash(img_file):
    image = Image.open(img_file)
    image = image.convert("L").resize((9, 8), Image.BICUBIC)
    pixel = list(image.getdata())
    bitstring = ""
    for row in range(8):
        for col in range(8):
            if pixel[9 * row + col] < pixel[9 * row + col + 1]:
                bitstring += "1"
            else:
                bitstring += "0"

    return ImageID(ident=int(bitstring, 2), bits=64)


def p_hash(img_file):
    hash_size = 8
    highfreq_factor = 4
    image = Image.open(img_file)
    img_size = hash_size * highfreq_factor
    image = image.convert("L").resize((img_size, img_size), Image.BICUBIC)

    pixels = list(image.getdata())
    pixel_lists = [[pixels[32 * i + j] for j in range(32)] for i in range(32)]
    dct_lists = []
    for pixel_list in pixel_lists:
        dct_lists.append(discrete_cosine_transform(pixel_list))
    dct_lists_t = list(map(list, zip(*dct_lists)))
    dct_lists_2_t = []
    for dct_list in dct_lists_t:
        dct_lists_2_t.append(discrete_cosine_transform(dct_list))
    dct_lists_2 = list(map(list, zip(*dct_lists_2_t)))
    result = []
    for index in range(hash_size):
        result = result + dct_lists_2[index][:8]

    median = my_median(result)
    bit_array = [value > median for value in result]
    p_hash = 0
    for bit in bit_array:
        p_hash = (p_hash << 1) | bit
    return ImageID(ident=p_hash, bits=64)


def w_hash(img_file):
    image = Image.open(img_file)
    image = image.convert("L").resize((8, 8), Image.ANTIALIAS)

    pixels = list(image.getdata())
    pixels = [[pixels[8 * i + j] for j in range(8)] for i in range(8)]

    w2d = wavelet2d(pixels)
    for iteration in range(3):
        w2d[0] = [0 for x in w2d[0]]
        w2d = wavelet2d(w2d)
    w2d_flat = []
    for row in w2d:
        w2d_flat += row

    # Substract median and compute hash
    med = my_median(w2d_flat)
    diff = [w2d_flat[i] > med for i in range(64)]
    bitstring = ""
    for bit in diff:
        if bit:
            bitstring = bitstring + "1"
        else:
            bitstring = bitstring + "0"
    return ImageID(ident=int(bitstring, 2), bits=64)


def get_error_types():
    total = es.count(index="iscc_images")["count"]
    group_by = (
        '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "errorType", "size": %s}}}}'
        % total
    )
    res = es.search("iscc_images", body=group_by)
    buckets = res["aggregations"]["group_by_state"]["buckets"]
    errorTypes = [bucket["key"] for bucket in buckets]
    errorTypes.remove("original")
    errorTypes.sort()
    return errorTypes


def init_index():
    if es.indices.exists(index="iscc_images"):
        es.indices.delete(index="iscc_images")
    es.indices.create(index="iscc_images", body=mapping_image)


def action_generator():
    a_time = 0
    b_time = 0
    d_time = 0
    p_time = 0
    w_time = 0
    total = 0
    total = es.count(index="iscc_images")["count"]
    for image in os.listdir(IMAGE_DIR):
        img_file = os.path.join(IMAGE_DIR, image)
        name = image.split(".")[0]
        if len(name.split("_")) > 1:
            errorType = name.split("_")[1]
        else:
            errorType = "original"
        start_time = time.time()
        aiid = a_hash(img_file)
        a_time += time.time() - start_time
        start_time = time.time()
        biid = b_hash(img_file)
        b_time += time.time() - start_time
        start_time = time.time()
        diid = d_hash(img_file)
        d_time += time.time() - start_time
        start_time = time.time()
        piid = p_hash(img_file)
        p_time += time.time() - start_time
        start_time = time.time()
        wiid = w_hash(img_file)
        w_time += time.time() - start_time
        total += 1
        query = {
            "_index": "iscc_images",
            "_type": "default",
            "_source": {
                "name": name.split("_")[0],
                "errorType": errorType,
                "wHash": "{}".format(wiid),
                "dHash": "{}".format(diid),
                "aHash": "{}".format(aiid),
                "pHash": "{}".format(piid),
                "bHash": "{}".format(biid),
            },
        }
        yield query
    print("aHash:", a_time / total)
    print("bHash:", b_time / total)
    print("dHash:", d_time / total)
    print("pHash:", p_time / total)
    print("wHash:", w_time / total)


def generate_ids():
    success = 0
    failed = 0
    for ok, item in helpers.streaming_bulk(es, action_generator(), chunk_size=100):
        if ok:
            success += 1
        else:
            failed += 1


def check_values(hash):
    total = es.count(index="iscc_images")["count"]
    errors = {}
    group_by = (
        '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "name", "size": %s}}}}'
        % total
    )
    res = es.search("iscc_images", body=group_by)
    buckets = res["aggregations"]["group_by_state"]["buckets"]
    for bucket in buckets:
        if bucket["doc_count"] > 1:
            get_by_key = {"query": {"terms": {"name": [bucket["key"]]}}}
            value = None
            for entry in helpers.scan(es, index="iscc_images", query=get_by_key):
                if entry["_source"]["errorType"] == "original":
                    value = entry["_source"][hash]
            for entry in helpers.scan(es, index="iscc_images", query=get_by_key):
                if not value == entry["_source"][hash]:
                    errorType = entry["_source"]["errorType"]
                    imageName = entry["_source"]["name"]
                    if not errorType in errors:
                        errors[errorType] = [imageName]
                    else:
                        errors[errorType].append(imageName)
    return errors


def get_hamming(hash):
    total = es.count(index="iscc_images")["count"]
    distances = {}
    group_by = (
        '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "name", "size": %s}}}}'
        % total
    )
    res = es.search("iscc_images", body=group_by)
    buckets = res["aggregations"]["group_by_state"]["buckets"]

    for bucket in buckets:
        if bucket["doc_count"] > 1:
            get_by_key = {"query": {"terms": {"name": [bucket["key"]]}}}
            value = None
            for entry in helpers.scan(es, index="iscc_images", query=get_by_key):
                if entry["_source"]["errorType"] == "original":
                    value = entry["_source"][hash]
            for entry in helpers.scan(es, index="iscc_images", query=get_by_key):
                hamming_dist = hamming_distance(value, entry["_source"][hash])
                errorType = entry["_source"]["errorType"]
                if not errorType in distances:
                    distances[errorType] = [hamming_dist]
                else:
                    distances[errorType].append(hamming_dist)
    return distances


def evaluate():
    errors = {}
    hamming_distances = {}
    hashes = ["aHash", "bHash", "dHash", "pHash", "wHash"]
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

    totals = ["Total"]
    for hash in hashes:
        hash_sum = 0
        for type in errorTypes:
            if type in errors[hash]:
                hash_sum += len(errors[hash][type])
        totals.append(hash_sum)
    table_rows.append(totals)
    print(tabulate(table_rows, headers=["Error Type"] + hashes))

    for hash in hashes:
        hamming_distances[hash] = get_hamming(hash)

    table_rows = []
    for type in errorTypes:
        table_row = [type]
        for hash in hashes:
            if type in hamming_distances[hash]:
                distances = hamming_distances[hash][type]
                table_row.append(sum(distances) / len(distances))
            else:
                table_row.append(0)
        table_rows.append(table_row)
    averages = ["Average"]
    for hash in hashes:
        hamming_sum = 0
        for type in errorTypes:
            if type in hamming_distances[hash]:
                hamming_sum += sum(hamming_distances[hash][type]) / len(
                    hamming_distances[hash][type]
                )
        averages.append(hamming_sum / len(errorTypes))
    table_rows.append(averages)
    print("\nAverage Hamming Distances")
    print(tabulate(table_rows, headers=["Error Type"] + hashes))


def find_hash_collisions(hash):
    collisions = 0
    total = es.count(index="iscc_images")["count"]
    group_by = (
        '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "%s", "size": %s}}}}'
        % (hash, total)
    )
    res = es.search("iscc_images", body=group_by)
    buckets = res["aggregations"]["group_by_state"]["buckets"]
    for bucket in buckets:
        if bucket["doc_count"] > 1:
            get_by_key = {"query": {"terms": {hash: [bucket["key"]]}}}
            name = None
            error_type = None
            for entry in helpers.scan(es, index="iscc_images", query=get_by_key):
                entry_name = entry["_source"]["name"]
                entry_error_type = entry["_source"]["errorType"]
                if name is None:
                    name = entry["_source"]["name"]
                    error_type = entry_error_type
                else:
                    if name != entry_name:
                        collisions += 1
                        print(
                            "\nCollision in hash {} = {}:".format(hash, bucket["key"])
                        )
                        print("Image 1: %s with error %s" % (name, error_type))
                        print(
                            "Image 2: %s with error %s" % (entry_name, entry_error_type)
                        )
    return collisions


def count_collisions():
    hashes = ["aHash", "bHash", "dHash", "pHash", "wHash"]
    collisions = {}
    for hash in hashes:
        collisions[hash] = find_hash_collisions(hash)

    print("\n")
    for hash, collision_count in collisions.items():
        print("%s collisions in hash %s" % (collision_count, hash))


if __name__ == "__main__":
    init_index()
    generate_ids()
    time.sleep(10)
    evaluate()
    count_collisions()
