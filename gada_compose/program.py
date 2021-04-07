"""This module is for running programs.

A program configuration looks like:

.. code-block:: yaml

    params:
    - name: target
    type: str
    help: required parameter
    - name: --output
    type: str
    help: optional parameter
    steps:
    - node: node1
      in:
        param: val
      out:
        result: ${{ }}
    - node: node2
      in:
        param: val
      out:
        result: ${{ }}

"""
from __future__ import annotations

__all__ = ["get_parser", "parse_args", "load", "run"]
import sys
import os
import asyncio
import argparse
import yaml
from typing import Optional
import pygada_runtime
from gada_compose import step


def _get_param_type(name: str, value: str) -> type:
    """Map parameter type to Python type.

    :param name: parameter name
    :param value: parameter type
    :return: Python type
    """
    t = {"str": str, "int": int}.get(value, None)

    if not t:
        raise Exception(f"unknown type {value} for param {name}")

    return t


def get_parser(prog: str, params: list[dict]) -> argparse.ArgumentParser:
    """Get a parser based on program parameters:

    .. code-block:: python

        >>> from gada_compose import program
        >>>
        >>> parser = program.get_parser("prog", [
        ...     {"name": "--input", "type": "str", "help": "input file"},
        ...     {"name": "foo", "type": "str", "help": "parameter"}
        ... ])
        >>> parser.print_help()
        usage: prog [-h] [--input INPUT] foo
        <BLANKLINE>
        Help
        <BLANKLINE>
        positional arguments:
          foo            parameter
        <BLANKLINE>
        optional arguments:
          -h, --help     show this help message and exit
          --input INPUT  input file
        >>>

    :param prog: program name
    :param params: list of program parameters
    :return: parser
    """
    parser = argparse.ArgumentParser(prog, description="Help")

    for _ in params:
        parser.add_argument(
            _["name"],
            help=_.get("help", None),
            type=_get_param_type(_["name"], _.get("type", "str")),
            default=_.get("default", None),
        )

    return parser


def parse_args(prog: str, params: list[dict], argv: list[str]) -> dict:
    """Parse command line arguments based on program parameters:

    .. code-block:: python

        >>> from gada_compose import program
        >>>
        >>> program.parse_args("prog", [
        ...     {"name": "--input", "type": "str", "help": "input file"},
        ...     {"name": "foo", "type": "str", "help": "parameter"}
        ... ], ["--input", "a", "b"])
        {'input': 'a', 'foo': 'b'}
        >>>

    :param prog: program name
    :param params: list of program parameters
    :param argv: command line arguments
    :return: parsed arguments
    """
    parser = get_parser(prog, params)
    return vars(parser.parse_args(argv))


def load(prog: any) -> dict:
    """Load a program as a JSON object:

    .. code-block:: python

        >>> from gada_compose import program, test_utils
        >>>
        >>> program.load(test_utils.prog_path())
        {'name': 'test_prog', 'params': [...], 'steps': [...]}
        >>>

    This method also accept file-like objects:

    .. code-block:: python

        >>> from gada_compose import program, test_utils
        >>>
        >>> with open(test_utils.prog_path(), "r") as f:
        ...     program.load(f)
        {'name': 'test_prog', 'params': [...], 'steps': [...]}
        >>>

    :param prog: file-like object or string
    :return: loaded program
    """
    if hasattr(prog, "read"):
        # Handle file-like objects
        return yaml.safe_load(prog.read())
    if isinstance(prog, str):
        # Load from filename
        with open(prog, "r") as f:
            return yaml.safe_load(f.read())
    if isinstance(prog, dict):
        # JSON object
        return prog

    raise Exception("expected a file-like object or str")


def run(prog: any, argv: list[str]):
    """Run a program:

    .. code-block:: python

        >>> from gada_compose import program, test_utils
        >>>
        >>> program.run(
        ...     test_utils.prog_path(),
        ...     ["--output", test_utils.data2_path(), test_utils.data_path()]
        ... )
        >>>

    :param prog: file-like object or string
    :param argv: command line arguments
    """
    # Load program
    config = load(prog)

    # Parse arguments
    env = parse_args(
        prog=config.get("name", "prog"), params=config.get("params", []), argv=argv
    )

    for _ in config.get("steps", []):
        step.run(_, env)
