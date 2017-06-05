# ISCC Benchmarks

We use the `iscc_bench` package for automated testing of accuracy and performance of the different ISCC components.

## MetaID Benchmark

The main purpose of the MetaID component is to serve as a high level grouping component of the full ISCC. It is created from minimal metadata (title, creators) and supposed to identify an "abstract creation" while being helpfull with data deduplication and disambiguation. 

### Benchmark Approach

For accurate measurment we define four cases:

- **True Positive (TP)**
  Two different sets of metadata for the same work result in the same MetaID

- **True Negative (TN)**
  Two different sets of metadata for different works result in different MetaIDs

- **False Positive (FP)**
  Two different sets of metadata for different works result in the same MetaID

- **False Negative (FN)**
  Two different sets of metadata for the same work result in different MetaIDs



The benchmarking is intended to help us **maximize true positives and true negatives** while **minimizing false positives and false negatives**.

For automated benchmarking we need reference data from different sources with a common identifier. The wide availability of bibliographic metadata and the common ISBN identifier is a good fit.

### Todo:

- Collect datasets
- Write streaming parsers that filter incomplete datasets and yield normalized data
- Collect all data in one file/db with fields (id, source, isbn, title, creators)
- Create MetaIDs from data collection and count TP, TN, FP, FN
- Test with different bit-lenght, metadata-normalization, shingle sizes, simhash/minhash

### Datasets

All datasets with at least ISBN, Title, Creators fields qualify for MetaID testing.

| Name         | # Records | Format                   | Url                                      |
| ------------ | --------- | ------------------------ | ---------------------------------------- |
| Open Library | 25 M      | TSV, JSON                | https://openlibrary.org/developers/dumps |
| EU Library   | 109 M     | Dublin Core, Rdf, Turtle | http://www.theeuropeanlibrary.org/tel4/access/data/opendata/details |
| DNB Titel    | 14 M      | JSON-LD, RDF, TURTLE     | http://datendienst.dnb.de/cgi-bin/mabit.pl?userID=opendata&pass=opendata&cmd=login |
| Harvard      | 12 M      | MARC21                   | http://library.harvard.edu/open-metadata |
| Hathi Trust  | ?         | CSV                      | https://www.hathitrust.org/hathifiles    |
| Google Books | 3 M       | XML                      | https://www.lib.msu.edu/gds/             |
| BX Books     | 271.379   | CSV                      | http://www2.informatik.uni-freiburg.de/~cziegler/BX/ |
| DBLP Dataset | 50.000    | XML                      | https://hpi.de/naumann/projects/repeatability/datasets/dblp-dataset.html |
