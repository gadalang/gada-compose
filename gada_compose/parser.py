"""This module is used for parsing the program configuration and
evaluating expressions contained within ``${{ }}`` blocks.
"""
from __future__ import annotations

__all__ = ["evaluate", "execute"]
import re
from typing import Optional


def evaluate(value: str, env: Optional[dict] = None) -> any:
    """Parse a string containing one or multiple ``${{ }}`` blocks
    and ``eval`` the expressions.

    Simple strings are left unchanged:

    .. code-block:: python

        >>> from gada_compose import parser
        >>>
        >>> parser.evaluate("foo")
        'foo'
        >>>

    Expressions in ``${{ }}`` blocks are evaluated as Python objects:

    .. code-block:: python

        >>> from gada_compose import parser
        >>>
        >>> parser.evaluate("${{ True }}")
        True
        >>>

    This allows for evaluating variables or simple arithmetic:

    .. code-block:: python

        >>> from gada_compose import parser
        >>>
        >>> parser.evaluate("${{ a + 1 }}", env={"a": 1})
        2
        >>>

    Or injecting a variable into a string:

    .. code-block:: python

        >>> from gada_compose import parser
        >>>
        >>> parser.evaluate("hello ${{ name }} !", env={"name": "john"})
        'hello john !'
        >>>

    .. note::

        Unlike ``execute``, the ``env`` dictionary will be left
        unmodified when evaluating an expression.

    :param value: string expression
    :param env: environment variables
    :return: result
    """

    def replace(o):
        return str(eval(o.group(1).strip(), {}, env))

    try:
        # Whole ${{ ... }} block
        m = re.match(r"^\$\{\{(.*?)\}\}$", value)
        if m:
            return eval(m.group(1).strip(), {}, env)

        # String mixed with ${{ ... }} blocks
        old_value = None
        new_value = value
        while old_value != new_value:
            old_value = new_value
            new_value = re.sub(r"\$\{\{(.*?)\}\}", replace, old_value)

        return new_value
    except Exception as e:
        raise Exception(f"failed to evaluate {value}") from e


def execute(value: str, env: Optional[dict] = None):
    """Parse a string containing a single ``${{ }}`` block and ``exec``
    the expression:

    .. code-block:: python

        >>> from gada_compose import parser
        >>>
        >>> env = {}
        >>> parser.execute("${{ a = True }}", env=env)
        >>> env
        {'a': True}
        >>>

    This allows for evaluating variables or simple arithmetic:

    .. code-block:: python

        >>> from gada_compose import parser
        >>>
        >>> env = {"b": 1}
        >>> parser.execute("${{ a = b + 1 }}", env=env)
        >>> env["a"]
        2
        >>>

    .. note::

        Unlike ``evaluate``, the ``env`` dictionary will be modified when
        executing the expression.

    :param value: string expression
    :param env: environment variables
    """
    try:
        # Whole ${{ ... }} block
        m = re.match(r"^\$\{\{(.*?)\}\}$", value)
        if not m:
            raise Exception(f"can't execute {value}")

        exec(m.group(1).strip(), {}, env)
    except Exception as e:
        raise Exception(f"failed to execute {value}") from e
