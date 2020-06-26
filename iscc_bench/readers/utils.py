# -*- coding: utf-8 -*-
"""Data aquisition utilities"""
import os
import logging
from tqdm import tqdm
import requests


log = logging.getLogger(__name__)


def download(url, save_to, chunk_size=1000000):
    """Large (streaming) file download with progress output.

    :param str url: download url
    :param str save_to: file path to save file
    :param int chunk_size: chunk size in bytes
    """

    log.info("Downloading %s -> %s" % (url, save_to))
    r = requests.get(url, stream=True)
    with open(save_to, "wb") as f:
        pbar = tqdm(unit="B", total=int(r.headers["Content-Length"]))
        for chunk in r.iter_content(chunk_size=chunk_size):
            if chunk:
                pbar.update(len(chunk))
                f.write(chunk)
        pbar.close()
    return save_to


def iter_files(root, exts=None, recursive=False):
    """
    Iterate (recursive) over file paths within root filtered by specified extensions.

    :param str root: Root folder to start collecting files
    :param iterable exts: Restrict results to given file extensions
    :param bool recursive: Wether to walk the complete directory tree
    :rtype collections.Iterable[str]: absolute file paths with given extensions
    """

    if exts is not None:
        exts = set((x.lower() for x in exts))

    def matches(e):
        return (exts is None) or (e in exts)

    if recursive is False:
        for entry in os.scandir(root):
            ext = os.path.splitext(entry.name)[-1].lstrip(".").lower()
            if entry.is_file() and matches(ext):
                yield entry.path
    else:
        for root, folders, files in os.walk(root):
            for f in files:
                ext = os.path.splitext(f)[-1].lstrip(".").lower()
                if matches(ext):
                    yield os.path.join(root, f)


def iter_bytes(filepath, chunksize=8192):
    """Buffered byte by byte iteration over files"""
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(chunksize)
            if chunk:
                for b in chunk:
                    yield b
            else:
                break
