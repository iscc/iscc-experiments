# -*- coding: utf-8 -*-

import json

import numpy as np
import matplotlib.pyplot as plt

from elasticsearch import Elasticsearch

es = Elasticsearch()


def autolabel(rects, totals, bottom=None):
    """
    Attach a text label above each bar displaying its height
    """
    for i, rect in enumerate(rects):
        if bottom:
            bottom_height = bottom[i]
        else:
            bottom_height = 0
        height = rect.get_height()
        width = rect.get_width()
        plt.text(
            rect.get_x() + width / 2.0,
            bottom_height + 0.4 * height,
            "%d\n(%s)" % (int(height), "{:.2%}".format(height / totals[i])),
            ha="center",
            va="bottom",
        )


valid_query = '{"query": {"bool": {"must": {"exists": {"field": "isbn_groups"}}}}}'
results = es.search(index="iscc_result", body=valid_query)["hits"]["hits"]

first = results[0]["_source"]
print("%s total entries" % first["total"])
sources = json.loads(first["entry_sources"])
for name, amount in sources.items():
    print("%s from %s" % (amount, name))

# sort by bit length and shingle size
results = sorted(
    results, key=lambda k: (k["_source"]["bit_length"], k["_source"]["shingle_size"])
)

N = len(results)

TP, FP, TN, FN, names = [], [], [], [], []

for result in results:
    source = result["_source"]
    TP.append(source["same_isbn"])
    FP.append(source["mid_groups"] - source["same_isbn"])
    TN.append(source["same_mid"])
    FN.append(source["isbn_groups"] - source["same_mid"])
    names.append(
        "Bit Length: %s\nShingle Size: %s"
        % (source["bit_length"], source["shingle_size"])
    )

plt.figure(1, figsize=(8, 9))

ind = np.arange(N)
width = 0.35
totals_P = [x + y for x, y in zip(TP, FP)]
totals_N = [x + y for x, y in zip(TN, FN)]

plt.subplot(211)

p1 = plt.bar(ind, TP, width, color="g")
p2 = plt.bar(ind, FP, width, color="r", bottom=TP)

autolabel(p1, totals_P)
autolabel(p2, totals_P, TP)

plt.title("Positives")
plt.xticks(ind, names)
plt.yticks(np.arange(0, 90000, 10000))
plt.legend((p1[0], p2[0]), ("True Positives", "False Positives"), loc=0)

plt.subplot(212)

p1 = plt.bar(ind, TN, width, color="g")
p2 = plt.bar(ind, FN, width, color="r", bottom=TN)

autolabel(p1, totals_N)
autolabel(p2, totals_N, TN)

plt.title("Negatives")
plt.xticks(ind, names)
plt.yticks(np.arange(0, 90000, 10000))
plt.legend((p1[0], p2[0]), ("True Negatives", "False Negatives"), loc=0)

plt.show()
