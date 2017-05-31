# -*- coding: utf-8 -*-

from iscc_bench.readers.bxbooks import bxbooks
from iscc_bench.readers.dnbrdf import iter_isbns
from iscc_bench.readers.harvard import harvard


ALL_READERS = (bxbooks, iter_isbns, harvard)
