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
@click.option('-r', required=False, help='Reader (If no reader is given, all reader are parsed)', default=None)
@click.option('--reset', required=False, type=bool, help='Reset old index', default=False)
def load(reader=None, reset=False):
    """Populate ElasticSearch with given reader."""

    # if reset:
    #     new_data_index()
    if reader and reader in ALL_READERS:
        print(reader)
        # populate_elastic(reader)
    # else:
    #     for reader in ALL_READERS:
    #         populate_elastic(reader)

main.add_command(load)


@click.command()
@click.option('-id_bits', type=int, help='Length of generated Meta-IDs', default=64)
def build(id_bits=64):
    """Generate Meta-IDs for the Meta-Data."""

    new_id_index()
    generate_ids(id_bits)

main.add_command(build)


@click.command()
def run(id_bits):
    """Run Evaluation"""

    evaluate()

main.add_command(run)