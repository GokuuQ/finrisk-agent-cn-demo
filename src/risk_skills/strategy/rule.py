"""Rule objects and expression exporters."""

from __future__ import absolute_import

from dataclasses import dataclass, field
from typing import Any, List, Optional

import pandas as pd


@dataclass
class Rule:
    rule_id: str
    feature: str
    operator: str
    threshold: Any = None
    values: Optional[List[Any]] = None
    lower_bound: Any = None
    upper_bound: Any = None
    description_cn: Optional[str] = None

    def evaluate(self, data):
        series = data[self.feature]
        if self.operator == ">=":
            return pd.to_numeric(series, errors="coerce") >= self.threshold
        if self.operator == ">":
            return pd.to_numeric(series, errors="coerce") > self.threshold
        if self.operator == "<=":
            return pd.to_numeric(series, errors="coerce") <= self.threshold
        if self.operator == "<":
            return pd.to_numeric(series, errors="coerce") < self.threshold
        if self.operator == "between":
            numeric = pd.to_numeric(series, errors="coerce")
            return (numeric >= self.lower_bound) & (numeric < self.upper_bound)
        if self.operator == "in":
            return series.astype(str).isin([str(v) for v in self.values or []])
        if self.operator == "missing":
            return series.isna() | (series.astype(str) == "")
        raise ValueError("unsupported operator: {0}".format(self.operator))

    def to_python(self):
        col = 'df[{0!r}]'.format(self.feature)
        if self.operator in (">=", ">", "<=", "<"):
            return "({0} {1} {2!r})".format(col, self.operator, self.threshold)
        if self.operator == "between":
            return "(({0} >= {1!r}) & ({0} < {2!r}))".format(col, self.lower_bound, self.upper_bound)
        if self.operator == "in":
            return "({0}.astype(str).isin({1!r}))".format(col, [str(v) for v in self.values or []])
        if self.operator == "missing":
            return "({0}.isna() | ({0}.astype(str) == ''))".format(col)
        return ""

    def to_sql(self):
        col = _quote_identifier(self.feature)
        if self.operator in (">=", ">", "<=", "<"):
            return "({0} {1} {2})".format(col, self.operator, _sql_literal(self.threshold))
        if self.operator == "between":
            return "({0} >= {1} AND {0} < {2})".format(
                col, _sql_literal(self.lower_bound), _sql_literal(self.upper_bound)
            )
        if self.operator == "in":
            values = ", ".join(_sql_literal(str(v)) for v in self.values or [])
            return "({0} IN ({1}))".format(col, values)
        if self.operator == "missing":
            return "({0} IS NULL OR CAST({0} AS VARCHAR) = '')".format(col)
        return ""

    def label(self):
        if self.description_cn:
            return self.description_cn
        if self.operator in (">=", ">", "<=", "<"):
            return "{0} {1} {2}".format(self.feature, self.operator, self.threshold)
        if self.operator == "between":
            return "{0} in [{1}, {2})".format(self.feature, self.lower_bound, self.upper_bound)
        if self.operator == "in":
            return "{0} in {1}".format(self.feature, self.values)
        if self.operator == "missing":
            return "{0} is missing".format(self.feature)
        return self.rule_id


@dataclass
class CompositeRule:
    rule_id: str
    rules: List[Rule] = field(default_factory=list)
    logic: str = "AND"

    def evaluate(self, data):
        if not self.rules:
            return pd.Series(False, index=data.index)
        mask = self.rules[0].evaluate(data)
        for rule in self.rules[1:]:
            mask = mask & rule.evaluate(data)
        return mask

    def to_python(self):
        return " & ".join(rule.to_python() for rule in self.rules)

    def to_sql(self):
        return "(" + " AND ".join(rule.to_sql().strip("()") for rule in self.rules) + ")"

    def label(self):
        return " AND ".join(rule.label() for rule in self.rules)


def _quote_identifier(name):
    return '"' + str(name).replace('"', '""') + '"'


def _sql_literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)) and not pd.isna(value):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"
