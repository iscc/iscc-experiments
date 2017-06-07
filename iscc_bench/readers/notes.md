# Metadata Readers

Each modules implements a reader for a specific datasource. Readers should be
implemented as generators that yield MetaData objects. Readers must only
yield data that has IBSN, Title and Author information. For datasources that
track multiple authors per entry should concatenate authors with a ';'.
