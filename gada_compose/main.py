from __future__ import annotations

__all__ = ["run", "main"]
import os
import sys
import io
import argparse
from typing import Optional
import yaml
import pygada_runtime
from gada_compose import program


def split_unknown_args(argv: list[str]) -> tuple[list[str], list[str]]:
    """Separate known command-line arguments from unknown one.
    Unknown arguments are separated from known arguments by
    the special **--** argument.
    :param argv: command-line arguments
    :return: tuple (known_args, unknown_args)
    """
    for i in range(len(argv)):
        if argv[i] == "--":
            return argv[:i], argv[i + 1 :]

    return argv, []


def run(
    prog: str,
    argv: Optional[list[str]] = None,
    *,
    stdin=None,
    stdout=None,
    stderr=None,
):
    """Run a program:

    .. code-block:: python

        >>> import gada_compose
        >>> from gada_compose import test_utils
        >>>
        >>> gada_compose.run(test_utils.prog_path(), [test_utils.data_path()])
        >>>

    The three parameters ``stdin``, ``stdout`` or ``stderr`` are provided as a convenience
    for writing unit tests when you can't use ``sys.stdin`` or ``sys.stdout``, or simply
    when you want to be able to read from the output.

    :param prog: file-like object or str
    :param argv: additional CLI arguments
    :param stdin: input stream
    :param stdout: output stream
    :param stderr: error stream
    """
    program.run(prog, argv)


def main(
    argv: Optional[list[str]] = None,
    *,
    stdin=None,
    stdout=None,
    stderr=None,
):
    """Main entrypoint:

    .. code-block:: python

        >>> import gada_compose
        >>> from gada_compose import test_utils
        >>>
        >>> gada_compose.main(["gada-compose", test_utils.prog_path(), test_utils.data_path()])
        >>>

    The three parameters ``stdin``, ``stdout`` or ``stderr`` are provided as a convenience
    for writing unit tests when you can't use ``sys.stdin`` or ``sys.stdout``, or simply
    when you want to be able to read from the output.

    :param argv: command line arguments
    :param stdin: input stream
    :param stdout: output stream
    :param stderr: error stream
    """
    argv = sys.argv if argv is None else argv

    parser = argparse.ArgumentParser(prog="gada-compose", description="Help")
    parser.add_argument("prog", type=str, help="program file")
    parser.add_argument(
        "argv", type=str, nargs=argparse.REMAINDER, help="additional CLI arguments"
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbosity level")
    args = parser.parse_args(args=argv[1:])
    prog_argv, main_argv = split_unknown_args(args.argv)

    run(prog=args.prog, argv=prog_argv, stdin=stdin, stdout=stdout, stderr=stderr)


if __name__ == "__main__":
    main(sys.argv)
