import importlib

import click

from freezeyt.freezing import freeze


@click.command()
@click.argument('module_name')
@click.argument('dest_path')
def main(module_name, dest_path):
    """
    MODULE_NAME
        Name of the Python web app module which will be frozen.

    DEST_PATH
        Absolute or relative path to the directory to which the files
    will be frozen.

    Example use:
        python -m freezeyt demo_app build
    """
    module = importlib.import_module(module_name)
    app = module.app

    freeze(app, dest_path)