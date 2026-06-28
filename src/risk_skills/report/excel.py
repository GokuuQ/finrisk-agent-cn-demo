"""Simple Excel report export."""

from __future__ import absolute_import

from pathlib import Path

import pandas as pd

from risk_skills.report.naming import safe_sheet_name


def write_excel_report(path, tables):
    """Write mapping of sheet name to DataFrame-like table."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = set()
    with pd.ExcelWriter(str(output_path), engine="openpyxl") as writer:
        for name, table in tables.items():
            sheet = safe_sheet_name(name, existing)
            existing.add(sheet)
            df = _to_frame(table)
            df.to_excel(writer, sheet_name=sheet, index=False)
            worksheet = writer.sheets[sheet]
            worksheet.freeze_panes = "A2"
            worksheet.auto_filter.ref = worksheet.dimensions
            for col_cells in worksheet.columns:
                values = [str(cell.value) if cell.value is not None else "" for cell in col_cells]
                width = min(max([len(v) for v in values] + [8]) + 2, 40)
                worksheet.column_dimensions[col_cells[0].column_letter].width = width
    return str(output_path)


def _to_frame(table):
    if isinstance(table, pd.DataFrame):
        return table
    if isinstance(table, pd.Series):
        return table.reset_index()
    if isinstance(table, dict):
        return pd.DataFrame([table])
    return pd.DataFrame(table)
