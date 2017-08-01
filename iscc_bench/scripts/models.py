# -*- coding: utf-8 -*-
import os
from iscc_bench import DATA_DIR
from pony import orm

from iscc_bench.readers import ALL_READERS

DB_PATH = os.path.join(DATA_DIR, 'metadata.sqlite')
_db = orm.Database()


class MetaRecord(_db.Entity):

    id = orm.PrimaryKey(int, auto=True)

    source = orm.Required(str, 16)
    isbn = orm.Required(str, 13)
    title = orm.Required(str)
    creators = orm.Required(str)

    # hash = orm.Required(int, unique=True)
    # meta = orm.Optional(int, size=64, unsigned=True)
    # orm.composite_key(title, creators)
    # orm.composite_index(source, isbn)


def database():
    """Return an initialized database connection"""
    _db.bind('sqlite', DB_PATH, create_db=True)
    _db.generate_mapping(create_tables=True)
    return _db

db = database()


@orm.db_session
def dump_to_db():
    """Dump all datasources to db"""
    readers = [r() for r in ALL_READERS]
    for reader in readers:
        rname = reader.__name__
        c = 0
        for entry in reader:
            obj = MetaRecord(
                source=rname,
                isbn=entry.isbn,
                title=entry.title,
                creators=entry.author,
            )
            c += 1
            if not c % 100:
                db.commit()
                c = 9

dump_to_db()
