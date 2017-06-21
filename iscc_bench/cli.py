import click
from iscc_bench.readers import ALL_READERS
from iscc_bench.elastic_search.fill_elasticsearch import populate_elastic
from iscc_bench.elastic_search.new_index import new_data_index, new_id_index
from iscc_bench.elastic_search.generate_meta_ids import generate_ids
from iscc_bench.elastic_search.evaluate import evaluate


@click.group()
def main():
    """ISCC Benchmarking."""
    pass


@click.command()
@click.option('--reader', '-r', required=False, help='Reader (If no reader is given, all reader are parsed)', default=None)
@click.option('--kill', '-k', required=False, type=bool, help='Reset old index', default=False)
def load(reader, kill):
    """Populate ElasticSearch with given reader."""

    if kill:
        new_data_index()
    if not reader:
        for reader in ALL_READERS:
            populate_elastic(reader)
    else:
        reader_names = {r.__name__: r for r in ALL_READERS}
        if not reader in reader_names:
            pass
        else:
            populate_elastic(reader_names[reader])



main.add_command(load)


@click.command()
@click.option('--id_bits', type=int, help='Length of generated Meta-IDs', default=64)
@click.option('--shingle_size', type=int, help='Shingle Size', default=4)
def build(id_bits, shingle_size):
    """Generate Meta-IDs for the Meta-Data."""

    new_id_index()
    generate_ids(id_bits, shinglesize=shingle_size)


main.add_command(build)


@click.command()
def run():
    """Run Evaluation"""

    evaluate()


main.add_command(run)
