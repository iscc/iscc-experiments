# -*- coding: utf-8 -*-
import math
from collections import Counter


def jaccard(seq1, seq2):
    set1, set2 = set(seq1), set(seq2)
    inter = set1.intersection(set2)
    union = set1.union(set2)
    return float(len(inter) / len(union))


def cosine(seq1, seq2):

    vec1 = Counter(seq1)
    vec2 = Counter(seq2)

    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])

    sum1 = sum([vec1[x] ** 2 for x in vec1.keys()])
    sum2 = sum([vec2[x] ** 2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)

    if not denominator:
        return 0.0
    else:
        return float(numerator) / denominator


def containment(seq1, seq2):
    set1, set2 = set(seq1), set(seq2)
    if not all((set1, set2)):
        raise ValueError("Empty set")
    inter = set1.intersection(set2)
    l_inter = len(inter)
    return max(l_inter / len(set1), l_inter / len(set2))


if __name__ == "__main__":
    print("Jac iden:\t", jaccard("ABCD", "ABCD"))
    print("Cos iden:\t", cosine("ABCD", "ABCD"))
    print("Con iden:\t", containment("ABCD", "ABCD"))
    print("Jac simi:\t", jaccard("ABCDFFF", "AEDCF"))
    print("Cos simi:\t", cosine("ABCDFFF", "AEDCF"))
    print("Con simi:\t", containment("ABCDFFF", "AEDCF"))
    print("Jac diff:\t", jaccard("ABCD", "EFGHI"))
    print("Cos diff:\t", cosine("ABCD", "EFGHI"))
    print("Con diff:\t", containment("ABCD", "EFGHI"))
