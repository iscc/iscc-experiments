import click
from iscc_bench.elastic_search.new_index import new_index
from .collision_count import count_collisions


@click.group()
def main():
    """ISCC Benchmarking."""
    pass

@click.command()
@click.argument('reader', required=False)
@click.argument('skip', required=False)
def check_meta_collisions(reader, skip):
    """Calculate collisions in given file."""
    count_collisions()

main.add_command(check_meta_collisions)

@click.command()
def new_index():
    """Delete old Index and add new."""
    ok = input("Really delete old index? ")
    if ok.lower() == "yes" or ok.lower() == "y":
        new_index()

main.add_command(new_index)