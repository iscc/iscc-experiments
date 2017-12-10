# -*- coding: utf-8 -*-

from iscc_bench.readers.bxbooks import bxbooks
from iscc_bench.readers.dnbrdf import dnbrdf
from iscc_bench.readers.harvard import harvard
from iscc_bench.readers.openlibrary import openlibrary
from iscc_bench.readers.libgen import libgen
from iscc_bench.readers.caltech101 import caltech_101
from iscc_bench.readers.caltech256 import caltech_256

ALL_READERS = (bxbooks, dnbrdf, harvard, openlibrary, libgen)
ALL_IMAGE_READERS = (caltech_101, caltech_256)
