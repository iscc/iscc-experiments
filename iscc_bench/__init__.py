# -*- coding: utf-8 -*-
import os
from collections import namedtuple

PACKAGE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(PACKAGE_DIR, 'data')


MetaDataBase = namedtuple('Meta', 'isbn title author')


class MetaData(MetaDataBase):
    """Go and extend if you like ..."""
