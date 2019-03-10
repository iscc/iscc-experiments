# -*- coding: utf-8 -*-
import os
from collections import namedtuple
from hashlib import sha1

PACKAGE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(PACKAGE_DIR, 'data')
BIN_DIR = os.path.join(PACKAGE_DIR, 'bin')


MetaDataBase = namedtuple('Meta', 'isbn title author')


class MetaData(MetaDataBase):
    """Go and extend if you like ..."""

    @property
    def key(self):
        """The primary key of the metadata"""
        return sha1(''.join([self.title, self.author]).encode('utf-8')).hexdigest()


if __name__ == '__main__':
    m = MetaData('9783906847122', 'Besondere Umstände', 'Kasperski, Gabrieala')
    print(m)
    print(m.key)
