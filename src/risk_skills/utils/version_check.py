"""Runtime version helpers."""

import sys


def python_version_tuple():
    return sys.version_info[:3]
