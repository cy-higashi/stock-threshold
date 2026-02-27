# -*- coding: utf-8 -*-
"""
CSV/TSV/txt のパースと商品コード別在庫合算。
"""
import csv
from pathlib import Path
from typing import Any


# 対象拡張子
DATA_EXTENSIONS = (".csv", ".tsv", ".txt")

# エンコーディングのフォールバック順
ENCODINGS = ("utf-8", "utf-8-sig", "cp932")


def _detect_delimiter(sample: str) -> str:
    """先頭行から区切り文字を推定。"""
    if "\t" in sample and sample.count("\t") >= sample.count(","):
        return "\t"
    return ","


def _read_rows(path: Path, has_header: bool) -> list[dict[str, Any]]:
    """
    1ファイルをパースして辞書のリストで返す。
    文字コード・デリミタは自動判別（UTF-8 / UTF-8 BOM / CP932 の順で試行、先頭行から区切りを推定）。
    ヘッダーあり: 1行目をキーとした辞書。
    ヘッダーなし: 列番号を文字列キー（"0", "1", ...）とした辞書。
    """
    for enc in ENCODINGS:
        try:
            with open(path, "r", encoding=enc, newline="") as f:
                sample = f.readline()
                f.seek(0)
                delimiter = _detect_delimiter(sample)
                if has_header:
                    reader = csv.DictReader(f, delimiter=delimiter)
                    rows = list(reader)
                else:
                    reader = csv.reader(f, delimiter=delimiter)
                    rows = [
                        {str(i): cell for i, cell in enumerate(row)}
                        for row in reader
                    ]
                if not rows and has_header:
                    return []
                return rows
        except (UnicodeDecodeError, csv.Error):
            continue
    return []


def parse_portal_stock(
    portal_dir: Path,
    portal_config: dict[str, Any],
) -> dict[str, int]:
    """
    ポータル用サブディレクトリ内の CSV/TSV/txt をパースし、
    商品コードで在庫数を合算した辞書を返す。
    portal_config は setting.json の portals.{ポータル名} の値（mapping を含む）。
    文字コード・デリミタは自動判別する。
    """
    mapping = portal_config.get("mapping") or {}
    has_header = mapping.get("has_header", portal_config.get("has_header", True))
    if has_header:
        product_column = mapping.get("product_code_column") or "商品コード"
        stock_column = mapping.get("stock_column") or "在庫数"
    else:
        product_column = str(mapping.get("product_code_column_index", 0))
        stock_column = str(mapping.get("stock_column_index", 1))

    aggregated: dict[str, int] = {}

    if not portal_dir.is_dir():
        return aggregated

    for path in portal_dir.iterdir():
        if path.suffix.lower() not in DATA_EXTENSIONS or not path.is_file():
            continue
        rows = _read_rows(path, has_header)
        for row in rows:
            code = row.get(product_column)
            stock_raw = row.get(stock_column)
            if code is None or code == "" or stock_raw is None:
                continue
            try:
                stock = int(float(str(stock_raw).replace(",", "").strip()))
            except (ValueError, TypeError):
                continue
            key = str(code).strip()
            if key:
                aggregated[key] = aggregated.get(key, 0) + stock

    return aggregated
