# -*- coding: utf-8 -*-
"""Some utility tools used in tests.
"""
from __future__ import annotations

__all__ = ["testnodes_path", "prog_path", "data_path", "data2_path"]
import os
import yaml
from typing import Optional
import gada_compose


def testnodes_path() -> str:
    """Get the absolute path to ``gada_compose/test/gadalang_testnodes``.

    :return: path to testnodes directory
    """
    return os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "test", "gadalang_testnodes")
    )


def prog_path() -> str:
    """Get the absolute path to ``gada_compose/test/gadalang_testnodes/prog.yml``.

    :return: path to prog.yml
    """
    return os.path.join(testnodes_path(), "prog.yml")


def data_path() -> str:
    """Get the absolute path to ``gada_compose/test/gadalang_testnodes/data.json``.

    :return: path to data.json
    """
    return os.path.join(testnodes_path(), "data.json")


def data2_path() -> str:
    """Get the absolute path to ``gada_compose/test/gadalang_testnodes/data2.json``.

    :return: path to data2.json
    """
    return os.path.join(testnodes_path(), "data2.json")
