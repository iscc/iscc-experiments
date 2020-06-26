# -*- coding: utf-8 -*-
"""
Comparison of mime type detection tools for python.

Requirements:
https://pypi.org/project/filetype/
https://pypi.org/project/python-magic-bin/
https://pypi.org/project/mimesniff/
https://pypi.org/project/tika/

"""
from dataclasses import dataclass
from os.path import basename, splitext
from typing import Callable
from tika.detector import from_buffer
import filetype
import mimesniff
import magic
from iscc_bench.readers.utils import iter_files


def filetype_detector(data):
    return filetype.guess_mime(data)


def magic_detector(data):
    f = magic.Magic(mime=True, uncompress=True)
    return f.from_buffer(data)


def mimesniff_detector(data):
    return mimesniff.what(data)


def tika_detector(data):
    try:
        return from_buffer(data)
    except Exception:
        print("tika detection error")
        return None


def detect(detector, data):
    return detector(data)


@dataclass
class Detector:
    name: str
    func: Callable


detectors = [
    Detector("ftyp", filetype_detector),
    Detector("magi", magic_detector),
    Detector("msnf", mimesniff_detector),
    Detector("tika", tika_detector),
]


def compare(path, recursive=False):
    """List occurences where different detectors yield different results."""
    seen = set()
    for fp in iter_files(path, recursive=recursive):
        results = []
        mime_types = set()
        ext = splitext(fp)[-1]
        with open(fp, "rb") as infile:
            data = infile.read(2048)
        for detector in detectors:
            mime = detector.func(data)
            mime_types.add(mime)
            results.append((detector.name, ext, str(mime)))
        unique_result = tuple(results)
        if unique_result in seen:
            continue
        if len(mime_types) > 1:
            print(basename(fp))
            for result in results:
                print(" ".join(result))
            print("\n")
        seen.add(unique_result)


if __name__ == "__main__":
    compare("../../", recursive=True)
