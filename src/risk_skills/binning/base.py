"""Shared binning helpers."""

from __future__ import absolute_import

import math

import pandas as pd


MISSING_LABEL = "99_MISSING"
OTHER_LABEL = "97_OTHER"


def is_missing(value):
    return pd.isna(value) or value == ""


def format_number(value):
    if value == float("-inf"):
        return "-inf"
    if value == float("inf"):
        return "inf"
    if pd.isna(value):
        return "nan"
    value = float(value)
    if abs(value) >= 1000 or (abs(value) > 0 and abs(value) < 0.001):
        return "{0:.6g}".format(value)
    text = "{0:.6f}".format(value).rstrip("0").rstrip(".")
    return text or "0"


def safe_label(value, max_len=48):
    text = str(value).strip()
    if not text:
        text = "EMPTY"
    text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    return text[:max_len]
