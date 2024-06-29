import click

from autocarter.__about__ import __version__


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="autocarter")
def autocarter():
    click.echo("Hello world!")
