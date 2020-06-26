# -*- coding: utf-8 -*-
from collections import deque
from itertools import islice


def sliding_window(iterable, size=2, step=1, fillvalue=None):
    if size < 0 or step < 1:
        raise ValueError
    it = iter(iterable)
    q = deque(islice(it, size), maxlen=size)
    if not q:
        return
    q.extend(fillvalue for _ in range(size - len(q)))
    while True:
        yield iter(q)
        try:
            q.append(next(it))
        except StopIteration:
            return
        q.extend(next(it, fillvalue) for _ in range(step - 1))


if __name__ == "__main__":
    from iscc_bench.readers.utils import iter_bytes

    s = "ABCDEFGH"
    r = [list(c) for c in sliding_window(s, size=3, step=2, fillvalue=None)]
    print(r)
    assert r == [["A", "B", "C"], ["C", "D", "E"], ["E", "F", "G"], ["G", "H", None]]

    bi = iter_bytes(__file__)
    for chunk in sliding_window(bi, size=8, step=3, fillvalue=""):
        print(bytes(chunk).decode("utf-8", "ignore"))
