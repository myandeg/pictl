"""The PICTL module"""

import os

import click
from rich import print as rprint

from pictl import __version__
from pictl.config import Config
from pictl.pic import compress as pcom
from pictl.upload import upload as pup

CONTEXT_SETTINGS = {"help_option_names": ["-h", "--help"]}


def get_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    click.echo(f"PICTL {__version__}")
    ctx.exit()


@click.group(context_settings=CONTEXT_SETTINGS)
@click.option(
    "-V",
    "--version",
    help="Show the pictl version.",
    callback=get_version,
    expose_value=False,
    is_eager=True,
    is_flag=True,
)
def cli():
    """A command line tool for image processing and uploading (ex. S3-type).

    \b
    Now it supports:
      - transformation from other image types to `webp` image as well as
        image compression.
      - image file uploading to AWS S3 or Cloudflare R2.
    """


@click.group()
def config():
    """Operations for the config file `~/.pictlrc`."""


@config.command()
def info():
    """Check the configs."""
    try:
        c = Config()
        settings = c.read()
        rprint(settings)
    except FileNotFoundError:
        rprint(f"{c.rc} doesn't exsit. Please check it.")


@config.command()
def add():
    """Add configs to the config file."""
    try:
        c = Config()
        c.read()
        c.add()
    except FileNotFoundError:
        c.init()
        c.add()


@config.command()
@click.option("-g", "--group", help="The specified group name.")
def delete(group: str = None):
    """Delete config group from the config file."""
    try:
        c = Config()
        c.read()
        c.delete(group)
    except FileNotFoundError:
        rprint(f"{c.rc} doesn't exsit. Please check it.")


@config.command()
def init():
    """Initialize config file with default configs."""
    Config().init()


@click.command()
@click.argument("filenames", nargs=-1, required=True)
@click.option("-g", "--group", required=True, help="The group in the config file you want to use.")
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Only print the resulting URL(s), one per line, in input order.",
)
def cup(filenames: tuple, group: str, quiet: bool):
    """Compress image(s) and upload to remote storage (compress and upload).

    \b
    FILENAMES is one or more files to compress and upload.
    """
    failed = False
    for filename in filenames:
        output = pcom(filename, quiet=quiet)
        if output is None:
            failed = True
            click.echo(f"Failed to compress: {filename}", err=True)
            continue
        url = pup(output, group, quiet=quiet)
        try:
            os.remove(output)
        except OSError:
            pass
        if url is None:
            failed = True
            click.echo(f"Failed to upload: {filename}", err=True)
            continue
        if quiet:
            click.echo(url)
    if failed:
        raise SystemExit(1)


@click.command()
@click.argument("filename")
@click.option("-o", "--output", help="The output filename.")
def compress(filename, output: str = None):
    """Compress any image into `webp` image.

    FILENAME is the name of the file to compress.
    """
    pcom(filename, output)


@click.command()
@click.argument("filenames", nargs=-1, required=True)
@click.option("-g", "--group", required=True, help="The group in the config file you want to use.")
@click.option(
    "-q",
    "--quiet",
    is_flag=True,
    help="Only print the resulting URL(s), one per line, in input order.",
)
def upload(filenames: tuple, group: str, quiet: bool):
    """Upload the file(s) to remote storage.

    \b
    FILENAMES is one or more files to upload.
    """
    failed = False
    for filename in filenames:
        url = pup(filename, group, quiet=quiet)
        if url is None:
            failed = True
            click.echo(f"Failed to upload: {filename}", err=True)
            continue
        if quiet:
            click.echo(url)
    if failed:
        raise SystemExit(1)


cli.add_command(config)
cli.add_command(upload)
cli.add_command(compress)
cli.add_command(cup)

if __name__ == "__main__":
    cli()
