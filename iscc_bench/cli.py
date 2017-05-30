import click
from .collision_count import count_collisions_csv


@click.group()
def main():
    """ISCC Benchmarking."""
    pass

@click.command()
@click.argument('path')
@click.argument('title_field')
@click.argument('author_field')
@click.argument('skip_first_line')
@click.argument('skip')
def check_meta_collisions(path, title_field=0, author_field=1, skip_first_line=False, skip=0):
    """Calculate collisions in given file."""
    count_collisions_csv(path, title_field, author_field, skip_first_line, skip)

main.add_command(check_meta_collisions)