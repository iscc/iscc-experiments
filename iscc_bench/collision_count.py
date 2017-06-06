
import time

from iscclib.meta import MetaID
import re
from iscc_bench.readers.bxbooks import bxbooks
from iscc_bench.readers.dnbrdf import dnbrdf


def count_collisions(reader=dnbrdf, skip=0):
    start_time = time.time()
    collisions = dict()
    duplicates = 0

    data = reader()
    for i, entry in enumerate(data):
        if skip:
            if i % (int(skip) + 1) != 0:
                continue
        mid = MetaID.from_meta(entry.title, entry.author)

        if mid.code in collisions:
            duplicates += 1
            collisions[mid.code]['collisions'] += 1
            collisions[mid.code]['articles'].update(
                {collisions[mid.code]['collisions']:
                     entry._asdict()
            }
            )
        else:
            entry = {
                'articles': {0: entry._asdict()},
                'collisions': 0}
            collisions[mid.code] = entry

    # count real collisions
    isbn_collisions = 0
    real_collisions = 0
    for entry in collisions:
        if collisions[entry]['collisions'] > 0:
            collision_article = False
            first_article = collisions[entry]['articles'][0]
            for key, article in collisions[entry]['articles'].items():
                if article['isbn'] != first_article['isbn']:
                    isbn_collisions += 1
                    if clear_string(article['title']) != clear_string(first_article['title']):
                        collision_article = True
                    if different_author(article['author'], first_article['author']):
                        collision_article = True

            if collision_article:
                real_collisions += 1
                print("\n Meta-ID collision:")
                for key, article in collisions[entry]['articles'].items():
                    print("\n Record " + str(key) + ": " + article['isbn'] + " - " + article['title'] + " - " + article['author'])

    # console output
    end_time = time.time()
    print("\nConsidered records: " + str(len(collisions) + duplicates))
    print("Duplicate Meta-IDs: " + str(duplicates))
    print("ISBN Collisions: " + str(isbn_collisions))
    print("\"Real\" Collisions: " + str(real_collisions))
    print("Time: " + str(round(end_time - start_time, 2)) + " seconds")


# Remove all special characters, punctuation and spaces from string and lower all characters
def clear_string(old_string):
    return ''.join(e for e in old_string.lower() if e.isalnum())


# check if author is the same, but names are written different
def different_author(author_one, author_two):
    if clear_string(author_one) == clear_string(author_two):
        return False

    # ignore second names
    author_one_names = author_one.lower().split(' ')
    author_two_names = author_two.lower().split(' ')
    if author_one_names[0] == author_two_names[0] and author_one_names[-1] == author_two_names[-1]:
        return False

    # if first name of author is shortened
    if re.match('^[a-z]\.', author_one_names[0]) or re.match('^[a-z]\.', author_two_names[0]):
        if author_one_names[0][0] == author_two_names[0][0]:
            return False

    return True


if __name__ == '__main__':
    count_collisions()