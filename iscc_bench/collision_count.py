# -*- coding: utf-8 -*-
import time
from iscclib.meta import MetaID
import csv
import re


def count_collisions_csv(path, title_field, author_field, isbn_field, skip_first_line, skip):
    start_time = time.time()
    collisions = dict()
    duplicates = 0
    with open(path) as csv_file:
        reader = csv.DictReader(csv_file, delimiter=';') # todo: read delimiter or give it as parameter
        for i, row in enumerate(reader):
            if skip_first_line and i == 0:
                continue
            if skip:
                if i % (int(skip) + 1) != 0:
                    continue
            mid = MetaID.from_meta(
                row[str(title_field)], row[str(author_field)]
            )
            if str(mid) in collisions:
                duplicates += 1
                collisions[str(mid)]['collisions'] += 1
                collisions[str(mid)]['articles'].update(
                    {collisions[str(mid)]['collisions']: {'title': row[title_field], 'author': row[author_field],
                                                          'isbn': row[isbn_field]}}
                )
            else:
                entry = {
                    'articles': {0: {'title': row[title_field], 'author': row[author_field], 'isbn': row[isbn_field]}},
                    'collisions': 0}
                collisions[str(mid)] = entry

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
