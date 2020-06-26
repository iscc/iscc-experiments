# -*- coding: utf-8 -*-
import json
import os

from elasticsearch import Elasticsearch
from elasticsearch import helpers
from iscc_bench import PACKAGE_DIR

es = Elasticsearch()

COLLISION_MID = os.path.join(PACKAGE_DIR, "collision_meta_ids.txt")
COLLISION_ISBN = os.path.join(PACKAGE_DIR, "collision_isbns.txt")
total = es.count(index="iscc_meta_data")

group_by_meta_id = (
    '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "meta_id", "size": %s}}}}'
    % total["count"]
)
group_by_isbn = (
    '{"size": 0, "aggs": {"group_by_state": {"terms": {"field": "isbn", "size": %s}}}}'
    % total["count"]
)
group_by_source = (
    '{"size": 0, "aggs": { "group_by_state": { "terms": { "field": "source", "size": %s}}}}'
    % total["count"]
)


def same_source_by_meta_id(mid):
    mid_query = {"query": {"terms": {"meta_id": [mid]}}}
    source_list = []
    for entry in helpers.scan(es, index="iscc_meta_id", query=mid_query):
        meta_data_id = entry["_source"]["meta_data"]
        meta_data = es.get(index="iscc_meta_data", id=meta_data_id)
        source_list.append(meta_data["_source"]["source"])
    return len(set(source_list)) == 1


def same_source_by_isbn(isbn):
    isbn_query = {"query": {"terms": {"isbn": [isbn]}}}
    source_list = []
    for entry in helpers.scan(es, index="iscc_meta_data", query=isbn_query):
        source_list.append(entry["_source"]["source"])
    return len(set(source_list)) == 1


def get_meta_data(id):
    meta_id_query = {"query": {"terms": {"meta_id": [id]}}}
    for entry in helpers.scan(es, index="iscc_meta_id", query=meta_id_query):
        meta_data_id = entry["_source"]["meta_data"]
        meta_data = es.get(index="iscc_meta_data", id=meta_data_id)
        yield meta_data["_source"]


def get_meta_ids(isbn):
    meta_data_query = {"query": {"terms": {"isbn": [isbn]}}}
    for entry in helpers.scan(es, index="iscc_meta_data", query=meta_data_query):
        meta_data_id = entry["_id"]
        meta_id_entries = es.get(
            index="iscc_meta_id", id="meta_{}".format(meta_data_id)
        )
        yield meta_id_entries["_source"]


def entry_groups(id):
    res = es.search("iscc_meta_data", body=group_by_source, request_timeout=60)
    sources = {}
    for bucket in res["aggregations"]["group_by_state"]["buckets"]:
        sources[bucket["key"]] = bucket["doc_count"]

    results = {"doc": {"total": total["count"], "entry_sources": json.dumps(sources)}}
    es.update(index="iscc_result", id=id, doc_type="default", body=results)


def positives(id):
    res = es.search("iscc_meta_id", body=group_by_meta_id, request_timeout=60)
    buckets = res["aggregations"]["group_by_state"]["buckets"]

    one_diff = 0
    all_same = 0
    total_entries = 0
    total_subgroups = 0
    collision_objects = []

    for bucket in buckets:
        if bucket["doc_count"] > 1:
            if same_source_by_meta_id(bucket["key"]):
                continue
            meta_data = get_meta_data(bucket["key"])
            isbn_list = [entry["isbn"] for entry in meta_data]
            total_entries += len(isbn_list)
            total_subgroups += len(set(isbn_list))
            if len(set(isbn_list)) > 1:
                one_diff += 1
                collision_objects.append(bucket["key"])
            else:
                all_same += 1

    with open(COLLISION_MID, "w") as collision_file:
        collision_file.write("\n".join(collision_objects))

    results = {"doc": {"mid_groups": all_same + one_diff, "same_isbn": all_same,}}
    es.update(index="iscc_result", id=id, doc_type="default", body=results)


def negatives(id):
    res = es.search("iscc_meta_data", body=group_by_isbn, request_timeout=60)
    buckets = res["aggregations"]["group_by_state"]["buckets"]

    one_diff = 0
    all_same = 0
    total_entries = 0
    total_subgroups = 0
    collision_objects = []

    for bucket in buckets:
        if bucket["doc_count"] > 1:
            if same_source_by_isbn(bucket["key"]):
                continue
            meta_ids = get_meta_ids(bucket["key"])
            meta_id_list = [entry["meta_id"] for entry in meta_ids]
            total_entries += len(meta_id_list)
            total_subgroups += len(set(meta_id_list))
            if len(set(meta_id_list)) > 1:
                one_diff += 1
                collision_objects.append(bucket["key"])
            else:
                all_same += 1

    results = {"doc": {"isbn_groups": all_same + one_diff, "same_mid": all_same}}
    es.update(index="iscc_result", id=id, doc_type="default", body=results)

    with open(COLLISION_ISBN, "w") as collision_file:
        collision_file.write("\n".join(collision_objects))


def evaluate():
    no_total_query = '{"query": {"bool": {"must_not": {"exists": {"field": "total"}}}}}'
    empty_results = es.search(index="iscc_result", body=no_total_query)["hits"]["hits"]
    if len(empty_results) > 0:
        id = empty_results[0]["_id"]
        entry_groups(id)
        positives(id)
        negatives(id)
    else:
        print("ID´s already tested.")


def get_results():
    pass


if __name__ == "__main__":
    evaluate()
