# -*- coding: utf-8 -*-
"""Read a sample of books from Gutenberg collection.

We collect sample data over as many languages as possible. We also collect
multiple formats per book and extract text with tika and calibre so we can
test with real world text extractions of similar contents from different file
formats.

Warning: You will have to use a VPN do access gutenberg data from germany ;(.

Records: 238 titles each in two different extractions, 50 languages, 476 files
Size: 330 MB (including raw ebook downloads)
Info: http://www.gutenberg.org/
Data: http://hugovk.github.io/gutenberg-metadata/gutenberg-metadata.json
"""
import json
import os
import logging
import shutil
from hashlib import sha1
from collections import Counter
import random
from os.path import join, exists, basename
from iscc_bench import DATA_DIR, BIN_DIR
from iscc_bench.readers import utils
from subprocess import run, PIPE


DOWNLOAD_URL = "http://hugovk.github.io/gutenberg-metadata/gutenberg-metadata.json"
DATA_PATH = join(DATA_DIR, 'gutenberg')
DATA_FILE_PATH = join(DATA_PATH, 'gutenberg-metadata.json')
DATA_RAW = join(DATA_PATH, 'raw')
DATA_TEXT = join(DATA_PATH, 'text')
CALIBRE = join(BIN_DIR, 'ebook-convert.exe')


log = logging.getLogger(__name__)


# Max number of documents to collect per language
DOCS_PER_LANG = 8

# Priotized list of file endings mapped to file extension
PRIO = {
    'pdf.pdf': 'pdf',
    'epub.noimages': 'epub',
    'txt.utf-8': 'txt',
    'kindle.noimages': 'mobi',
}

# Skip erroneous titles with these gutenbert ids:
SKIP_GIDS = ('22242', '31552', '17424', '39121')


def gutenberg(lang=None):
    """Yield file path (pairwise sorted) to gutenberg extracted texts"""
    for fp in sorted(utils.iter_files(DATA_TEXT, exts=['txt'])):
        if lang is None:
            yield fp
        else:
            file_lang = basename(fp).split('_')[1]
            if lang.lower() == file_lang.lower():
                yield fp


def extract_text():
    """Extract texts from ebooks in DATA_RAW to DATA_TEXT"""
    from tika import tika, parser

    os.makedirs(DATA_TEXT, exist_ok=True)
    log.info(f'Created text directory: {DATA_TEXT}')
    log.info(f'Extracting with Tika {tika.TikaVersion}')

    for fp in os.listdir(DATA_RAW):

        log.info(f'Extracting {fp}')
        base, ext = os.path.splitext(fp)
        infile = join(DATA_RAW, fp)
        outfile = base.replace('.', '_') + '_' + ext.lstrip('.') + '.txt'
        outfile = join(DATA_TEXT, outfile)
        if exists(outfile):
            log.info(f'Skip existing {outfile}')
            continue
        if ext == '.mobi':
            cmd = [CALIBRE, infile, outfile]
            try:
                run(cmd, check=True, timeout=240, stdout=PIPE)
            except Exception as e:
                log.error("Calibre failed with %s" % repr(e))
        elif ext in ('.pdf', '.epub'):
            parsed = parser.from_file(infile)
            content = parsed.get('content')
            if not content:
                log.error(f'No content extracted. Skipping {infile}')
                continue
            with open(outfile, 'w', encoding='utf-8') as of:
                of.write(content)
        else:
            shutil.copy(infile, outfile)


def download_ebooks(entries=None):
    """Download ebooks. Entries needs 'selected_uris' field."""
    os.makedirs(DATA_RAW, exist_ok=True)
    log.info('Created raw directory: {}'.format(DATA_RAW))

    if not entries:
        entries = select_entries()

    downloads = 0
    errors = 0

    for gid, meta in entries.items():
        for uri in meta['selected_uris']:
            ext = None
            for ending in PRIO.keys():
                if uri.endswith(ending):
                    ext = PRIO[ending]
                    break
            outf = f"{gid}_{meta['language'][0].lower()}.{ext}"
            outp = os.path.join(DATA_RAW, outf)
            if os.path.exists(outp):
                log.info(f'Skip download of existing file {outf}.')
                continue
            try:
                utils.download(uri, outp)
                downloads += 1
            except Exception as e:
                errors += 1
                log.error(f'Failed download of {uri} with {e}.')
                try:
                    os.remove(outp)
                except Exception:
                    pass

    log.info(f'Downloaded {downloads} ebook files with {errors} errors.')


def select_entries(docs_per_lang=DOCS_PER_LANG) -> dict:
    """Create a selection of titles from Gutenberg Catalog."""
    data = get_metadata()
    langs = Counter()
    gids = list(data.keys())
    # Repeatable random sort
    random.Random(4).shuffle(gids)

    filtered = {}

    for fname_sig in PRIO.keys():
        for gid in gids:

            if gid in SKIP_GIDS or gid in filtered:
                continue

            meta = data[gid]
            if fname_sig not in ''.join(meta.get('formaturi', [])):
                continue

            lang = meta.get('language', [])
            if len(lang) != 1:
                continue
            lang = lang[0]
            if langs[lang] == docs_per_lang:
                continue

            uris = []
            for suffix, ext in PRIO.items():
                if len(uris) == 2:
                    break
                for uri in meta.get('formaturi', []):
                    if uri.endswith(suffix):
                        uris.append(uri)

            if not len(uris) == 2:
                continue

            filtered[gid] = meta.copy()
            filtered[gid]['selected_uris'] = uris

            langs[lang] += 1
    log.info(
        f'Selected {len(filtered)} titles from gutenberg metadata - '
        f'including {len(langs)} different languages - '
        f'with max {docs_per_lang} titles per language.'
    )

    return filtered


def get_metadata() -> dict:
    """Download and return deserialized Gutenberg metadata as python dict."""

    os.makedirs(DATA_PATH, exist_ok=True)

    if not os.path.exists(DATA_FILE_PATH):
        log.info('Downloading metadata: {}'.format(DATA_FILE_PATH))
        utils.download(DOWNLOAD_URL, DATA_FILE_PATH)

    with open(DATA_FILE_PATH) as f:
        data = json.load(f)

    return data


if __name__ == '__main__':
    log_format = '%(asctime)s - %(levelname)s - %(message)s'
    logging.basicConfig(level=logging.INFO, format=log_format)
    download_ebooks()
    extract_text()
    log.info('check gutenberg for exact duplicate files')
    sigs = {}
    for file_path in gutenberg():
        fname = basename(file_path)
        sig = sha1(open(file_path, 'rb').read()).hexdigest()
        if sig not in sigs:
            sigs[sig] = file_path
        else:
            log.info('Collision: {} -> {}'.format(file_path, sigs[sig]))
    log.info(f'Done checking {len(sigs)} gutenberg for exact duplicate tracks')
