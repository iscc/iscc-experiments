# -*- coding: utf-8 -*-
"""WTA-Hash - Winner Takes All

A sparse embedding method based on rank correlation measures.

As presented in:
The Power of Comparative Reasoning
by Jay Yagnik, Dennis Strelow, David A. Ross, Ruei-sung Lin
DOI:10.1109/ICCV.2011.6126527
https://dblp.org/rec/conf/iccv/YagnikSRL11
"""


def wta_hash(vec, m, k=2):
    """Apply WTA-Hash to vector 'vec'

    :param list vec: A vector of 'features' (any type that support 'max()')
    :param list m: A list (dimensions) of lists (permutations)
    :param int k: value range per output feature
    :return int|list: A integer hash with k2 or a list of features with k>2
    """
    h = []
    for perm in m:
        vec_perm = [vec[i] for i in perm]
        max_idx = vec_perm.index(max(vec_perm))
        h.append(max_idx)
    if k == 2:
        whash = 0
        for v in h:
            whash = (whash << 1) | v
        return whash
    return h


def test_wta_hash():
    """
    Test WTA-Hash as described in https://dblp.org/rec/conf/iccv/YagnikSRL11
    """
    vec = [10, 5, 2, 6, 12, 3]
    m = [[1, 4, 2, 5, 0, 3]]
    k = 4
    h = wta_hash(vec, m, k)
    print(f"WTA-Hash for {vec} -> {h}")
    assert h == [1]
    vec = [4, 5, 10, 2, 3, 1]
    h = wta_hash(vec, m, k)
    print(f"WTA-Hash for {vec} -> {h}")
    assert h == [2]
    k = 2
    h = wta_hash(vec, m, k)
    print(f"WTA-Hash for {vec} with k == {k} -> {h}")
    assert h == 2


if __name__ == "__main__":
    test_wta_hash()
