"""Collect ISBN intersections between different data_sources"""
import os
import iscc_bench
from iscc_bench.readers import ALL_READERS
from itertools import combinations


def print_data_source_intersections():
    for combo in [c for c in combinations(ALL_READERS, 2)]:
        a_isbns = set(load_isbns(combo[0]))
        b_isbns = set(load_isbns(combo[1]))
        matches = a_isbns.intersection(b_isbns)
        print('{} identical isbns in {}/{}'.format(
            len(matches), combo[0].__name__, combo[1].__name__)
        )


def dump_isbns(rebuild=False):
    """Dump isbns for all readers to disk"""
    readers = [r() for r in ALL_READERS]
    for reader in readers:
        name = reader.__name__
        fp = os.path.join(iscc_bench.DATA_DIR, name + '.isbns')
        if not rebuild and os.path.exists(fp):
            print('Skip existing {}.isbns'.format(name))
            continue

        print('######### Dumping {}.isbns'.format(name))
        with open(fp, 'w') as outf:
            for entry in reader:
                if entry.isbn:
                    outf.write('{}\n'.format(entry.isbn))


def load_isbns(reader):

    if hasattr(reader, '__name__'):
        name = reader.__name__
    else:
        name = reader

    fp = os.path.join(iscc_bench.DATA_DIR, name + '.isbns')
    with open(fp) as f:
        return f.read().split()


def print_isbn_stats():
    from terminaltables import AsciiTable

    data = [['Reader', 'Total ISBNs', 'Unique ISBNs']]

    for reader in ALL_READERS:
        isbns = load_isbns(reader)
        total = len(isbns)
        unique = len(set(isbns))
        data.append([reader.__name__, total, unique])
    table = AsciiTable(data)
    print(table.table)


def get_intersecting_isbns():

    isbn_sets = []
    for reader in ALL_READERS:
        isbns = load_isbns(reader)
        isbn_sets.append(set(isbns))
    return set.intersection(*isbn_sets)


if __name__ == '__main__':
    # print(reader_combinations())
    # dump_isbns()
    print_isbn_stats()
    # print('Total all intersecting isbns: {}'.format(len(get_intersecting_isbns())))
    print_data_source_intersections()
