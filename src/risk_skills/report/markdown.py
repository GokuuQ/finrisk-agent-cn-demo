"""Markdown report rendering."""

from __future__ import absolute_import

from pathlib import Path


def write_markdown_report(path, title, summary_lines, metadata=None, warnings=None):
    """Write a compact Markdown report."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = ["# {0}".format(title), "", "## 1. 执行摘要", ""]
    lines.extend("- {0}".format(line) for line in summary_lines)
    if warnings:
        lines.extend(["", "## 2. 风险与限制", ""])
        lines.extend("- {0}".format(item) for item in warnings)
    if metadata:
        lines.extend(["", "## 3. 运行信息", ""])
        for key in sorted(metadata):
            lines.append("- `{0}`: {1}".format(key, metadata[key]))
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(output_path)
