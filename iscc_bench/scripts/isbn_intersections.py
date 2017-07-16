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
        return [int(line.strip()) for line in f]


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


def build_metadata_pairs(samples=1000000):
    """
    Build sample data in format:
        isbn, title_a, authors_a, title_b, authors_b

    Where:
        isbn is in both datasets
        title_a + authors_a != title_b + authors_b
    """
    from itertools import cycle
    import gc
    gc.disable()

    combos = [c for c in combinations(ALL_READERS, 2)]
    samples_per_combo = int(samples/len(combos))
    print("Creating ~%s samples per data source pair" % samples_per_combo)

    fp = os.path.join(iscc_bench.DATA_DIR, 'metapairs_%s.sample' % samples)
    total_samples = 0

    with open(fp, 'wb') as outf:
        for combo in combos:
            gc.collect()
            combo_name = '%s-%s' % (combo[0].__name__, combo[1].__name__)
            a_isbns = set(load_isbns(combo[0]))
            b_isbns = set(load_isbns(combo[1]))
            relevant_isbns = a_isbns.intersection(b_isbns)
            data = {}
            counter = 0
            reader_combo = cycle((combo[0](), combo[1]()))
            print('Collecting %s combo' % combo_name)
            for reader in reader_combo:
                try:
                    entry = next(reader)
                except StopIteration:
                    print('!!!! StopIteration')
                    break

                isbn = int(entry.isbn)

                if isbn in relevant_isbns:
                    title = entry.title
                    author = entry.author
                    if isbn not in data:
                        data[isbn] = {'title': title, 'author': author}
                        continue
                    if title != data[isbn]['title'] or author != data[isbn]['author']:
                        row = data[isbn]
                        out_data = '{}|{}|{}|{}|{}\n'.format(
                            isbn,
                            row['title'].replace('|', ''),
                            row['author'].replace('|', ''),
                            title.replace('|', ''),
                            author.replace('|', ''),
                        )
                        print(out_data)
                        outf.write(out_data.encode('utf-8'))
                        total_samples += 1
                        relevant_isbns.remove(isbn)
                        del data[isbn]
                        if counter == samples_per_combo:
                            print('Finished samples for %s' % combo_name)
                            break
                        if not relevant_isbns:
                            print('Out of relevant ISBNs at %s samples for %s', (counter, combo_name))
                            break
                        counter += 1
    print('Collected %s total samples' % total_samples)

if __name__ == '__main__':
    dump_isbns()
    # print_isbn_stats()
    # print('Total all intersecting isbns: {}'.format(len(get_intersecting_isbns())))
    # print_data_source_intersections()
    build_metadata_pairs()
