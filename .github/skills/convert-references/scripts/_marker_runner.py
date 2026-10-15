#!/usr/bin/env python3
"""Run marker_single with a higher recursion limit (markdownify can exceed the default on deeply nested tables)."""
import sys

sys.setrecursionlimit(10000)
from marker.scripts.convert_single import convert_single_cli

if __name__ == "__main__":
    convert_single_cli()
