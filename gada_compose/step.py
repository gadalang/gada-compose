"""This module is for running program steps.
"""
from __future__ import annotations
__all__ = ["load_in_params", "store_out_params", "run"]
import sys
import os
import asyncio
import argparse
import re
from typing import Optional
from gada_compose import parser
import pygada_runtime


async def _run(node: str, data: dict):
    with pygada_runtime.PipeStream() as stdin:
        with pygada_runtime.PipeStream() as stdout:     
            with pygada_runtime.PipeStream(rmode="r") as stderr:
                pygada_runtime.write_json(stdin, data)
                stdin.eof()

                proc = await pygada_runtime.run(
                    node,
                    stdin=stdin.reader,
                    stdout=stdout,
                    stderr=stderr
                )

                await proc.wait()

                stdout.eof()
                stderr.eof()

                if proc.returncode != 0:
                    raise Exception("error during node execution") from Exception(await stderr.read())

                return await pygada_runtime.read_json(stdout)


def parse_value(value: str, env: dict) -> any:
    if isinstance(value, str):
        return parser.evaluate(value, env)

    return value


def store_value(value: str, env: dict):
    parser.execute(value, env)


def load_in_params(params: dict, env: Optional[dict] = None) -> dict:
    """Load input parameters based on step configuration.

    For builtin types, just return the same dict:

    .. code-block:: python

        >>> from gada_compose import step
        >>>
        >>> step.load_in_params({"a": 1, "b": 2})
        {'a': 1, 'b': 2}
        >>>

    Evaluate and return the result of ``${{ }}`` blocks:

    .. code-block:: python

        >>> from gada_compose import step
        >>>
        >>> step.load_in_params({"a": "${{ B }}"}, {"B": 1})
        {'a': 1}
        >>>

    :param params: input parameters from step configuration
    :param env: environment variables
    :return: loaded parameters
    """
    if not params:
        return {}
    if isinstance(params, str):
        # Plain string
        return parse_value(params, env)
    if isinstance(params, dict):
        # Dict object
        return {k: parse_value(v, env) for k, v in params.items()}
    
    raise Exception("expected a dict or str")


def store_out_params(params: dict, values: dict, env: Optional[dict] = None) -> dict:
    """Store output parameters based on step configuration:

    .. code-block:: python

        >>> from gada_compose import step
        >>>
        >>> env = {}
        >>> step.store_out_params({"data": "${{ data = value }}"}, {"data": 1}, env=env)
        >>> env
        {'data': 1}
        >>>

    :param params: input parameters from step configuration
    :param values: accessible values
    :param env: environment variables
    """
    if not params:
        return

    env = env if env is not None else {}

    if isinstance(params, str):
        # Plain string
        env["value"] = values
        store_value(params, env)
        del env["value"]
    elif isinstance(params, dict):
        # Dict object
        for k, v in params.items():
            env["value"] = values.get(k, None)
            store_value(v, env)
            del env["value"]
    else:
        raise Exception("expected a dict or str")


def run(step: dict, env: Optional[dict] = None):
    if "node" not in step:
        raise Exception("missing node attribute on step")

    # Build input params
    args = load_in_params(step.get("in", None), env)

    # Run node
    result = asyncio.run(_run(step["node"], args))

    store_out_params(step.get("out", None), result, env)
