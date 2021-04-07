"""This module is for running program steps.

A step configuration looks like:

.. code-block:: yaml

    steps:
    - node: somenode
    in:
      param1: val1
      param2: val2
    out:
      result1: ${{ ... }}
      result2: ${{ ... }}

"""
from __future__ import annotations

__all__ = ["load_values", "store_values", "run"]
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
                    node, stdin=stdin.reader, stdout=stdout, stderr=stderr
                )

                await proc.wait()

                # Avoid any deadlock
                stdout.eof()
                stderr.eof()

                if proc.returncode != 0:
                    raise Exception("error during node execution") from Exception(
                        await stderr.read()
                    )

                return await pygada_runtime.read_json(stdout)


def parse_value(value: str, env: dict) -> any:
    if isinstance(value, str):
        return parser.evaluate(value, env)

    return value


def store_value(value: str, env: dict):
    parser.execute(value, env)


def load_values(params: dict, env: Optional[dict] = None) -> dict:
    """Load input values required for running a single step based on ``params`` bindings.

    For a single step taking two parameters ``a`` and ``b``, the configuration
    will be something like:

    .. code-block:: yaml

        steps:
        - node: somenode
          in:
            a: 1
            b: 2

    For builtin types, this function will just return the values unchanged:

    .. code-block:: python

        >>> from gada_compose import step
        >>>
        >>> step.load_values({"a": 1, "b": 2})
        {'a': 1, 'b': 2}
        >>>

    It's also possible to use a ``${{ }}`` block as parameter value:

    .. code-block:: yaml

        steps:
        - node: somenode
          in:
            a: ${{ 1 + 1 }}

    This function will evaluate and return the results of ``${{ }}`` blocks:

    .. code-block:: python

        >>> from gada_compose import step
        >>>
        >>> step.load_values({"a": "${{ 1 + 1 }}"})
        {'a': 2}
        >>>

    This also allows for accessing variables passed in the ``env`` dictionary:

    .. code-block:: python

        >>> from gada_compose import step
        >>>
        >>> step.load_values({"a": "${{ B }}"}, env={"B": True})
        {'a': True}
        >>>

    .. note::

        The ``env`` dictionary is left unchanged.

    :param params: a mapping {parameter: value}
    :param env: environment variables
    :return: a mapping {parameter: value}
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


def store_values(params: dict, values: dict, env: Optional[dict] = None):
    """Store output values produced by a single step based on ``params`` bindings.

    For a single step producing two parameters ``a`` and ``b``, the configuration
    will be something like:

    .. code-block:: yaml

        steps:
        - node: somenode
          out:
            a: ${{ A = value }}
            b: ${{ B = value }}

    This function will execute ``${{ }}`` blocks for storing ``values`` in
    the ``env`` dictionary:

    .. code-block:: python

        >>> from gada_compose import step
        >>>
        >>> env = {}
        >>> step.store_values(
        ...     {"a": "${{ A = value }}" ,"b": "${{ B = value }}"},
        ...     values={"a": 1, "b": 2},
        ...     env=env
        ... )
        >>> env
        {'A': 1, 'B': 2}
        >>>

    .. note::

        The ``env`` dictionary is modified with new values.

    :param params: a mapping {parameter: expression}
    :param values: output values produced by a step
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
    """Run a single step, storing output values to the ``env`` dictionary:

    .. code-block:: python

        >>> from gada_compose import step, test_utils
        >>>
        >>> env = {}
        >>> step.run({
        ...     "node": "testnodes.json",
        ...     "in": {"input": test_utils.data_path()},
        ...     "out": {"data": "${{ data = value }}"}
        ... }, env=env)
        >>> env
        {'data': {'a': '1', 'b': 2}}
        >>>

    :param step: step configuration
    :param env: environment variables
    """
    if "node" not in step:
        raise Exception("missing node attribute on step")

    # Load input values from env
    args = load_values(step.get("in", None), env)

    # Run node
    result = asyncio.run(_run(step["node"], args))

    # Store output values to env
    store_values(step.get("out", None), result, env)
