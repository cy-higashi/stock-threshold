# -*- coding: utf-8 -*-
"""
Excel（stock_manage.xlsx）から商品コードと最低在庫数を読み込む。
"""
from pathlib import Path
from typing import Any

from openpyxl import load_workbook


def load_thresholds(
    excel_base_path: str,
    portal_name: str,
    portal_config: dict[str, Any],
) -> dict[str, int]:
    """
    ポータル用 stock_manage.xlsx を開き、
    商品コードをキー・最低在庫数を値とした辞書を返す。
    パス: {excel_base_path}/{portal_name}/stock_manage.xlsx
    """
    mapping = portal_config.get("mapping") or {}
    product_column = mapping.get("product_code_column") or "商品コード"
    # 最低在庫数は実行のたびに Excel から読み出すため setting.json には持たない。Excel の列名は固定。
    min_stock_column = "最低在庫数"
    path = Path(excel_base_path) / portal_name / "stock_manage.xlsx"

    result: dict[str, int] = {}
    if not path.exists():
        return result

    wb = load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        rows = list(ws.iter_rows(values_only=True))
        if not rows:
            return result
        header = [str(c).strip() if c is not None else "" for c in rows[0]]
        try:
            code_idx = header.index(product_column)
        except ValueError:
            code_idx = 0
        try:
            min_idx = header.index(min_stock_column)
        except ValueError:
            min_idx = 1 if code_idx == 0 else 0

        for row in rows[1:]:
            if row is None or len(row) <= max(code_idx, min_idx):
                continue
            code = row[code_idx]
            min_val = row[min_idx]
            if code is None or str(code).strip() == "":
                continue
            try:
                min_stock = int(float(str(min_val).replace(",", "").strip()))
            except (ValueError, TypeError):
                continue
            result[str(code).strip()] = min_stock
    finally:
        wb.close()

    return result
