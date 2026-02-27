# -*- coding: utf-8 -*-
"""
在庫しきい値アラート エントリポイント。
引数: ポータル名のディレクトリ（必須。在庫データの CSV/TSV/txt が格納されたフォルダ。ディレクトリ名で setting.json と Excel を検索）
      設定ファイルパス（任意、省略時は setting.json）
"""
import json
import sys
from pathlib import Path

from app.alert_sender import build_alert_message, send_to_chatwork
from app.stock_parser import parse_portal_stock
from app.threshold_loader import load_thresholds


def load_settings(settings_path: Path) -> dict:
    """setting.json を読み込む。"""
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_portal_config(portals: dict, portal_name: str) -> dict | None:
    """portals.{ポータル名} を大文字小文字を無視して検索する。"""
    key = portal_name.strip()
    if key in portals:
        return portals[key]
    key_lower = key.lower()
    for k, v in portals.items():
        if (k or "").lower() == key_lower:
            return v
    return None


def run(portal_dir: Path, settings_path: Path) -> None:
    """
    渡したポータルディレクトリ名で setting.json と最低在庫 Excel を検索し、
    在庫パース → 最低在庫取得 → 比較 → アラートがあれば ChatWork 送信を行う。
    """
    settings = load_settings(settings_path)
    chatwork_config = settings.get("chatwork") or {}
    excel_base_path = settings.get("excel_base_path") or r"G:\共有ドライブ\★OD\99_在庫管理\しきい値アラート"
    portals = settings.get("portals") or {}

    portal_name = portal_dir.name
    portal_config = _find_portal_config(portals, portal_name)
    if not portal_config:
        print(f"エラー: setting.json にポータル名「{portal_name}」の定義がありません。", file=sys.stderr)
        sys.exit(1)

    # 在庫: 渡したポータルディレクトリ配下の CSV/TSV/txt を商品コードで合算
    stock_by_code = parse_portal_stock(portal_dir, portal_config)
    # 最低在庫: ポータル名で Excel を検索（{excel_base_path}/{portal_name}/stock_manage.xlsx）
    min_by_code = load_thresholds(excel_base_path, portal_name, portal_config)

    alerts: list[dict] = []
    for product_code, min_stock in min_by_code.items():
        current = stock_by_code.get(product_code, 0)
        if current < min_stock:
            alerts.append({
                "portal_name": portal_name,
                "product_code": product_code,
                "current_stock": current,
                "min_stock": min_stock,
            })

    if not alerts:
        return

    message = build_alert_message(alerts, chatwork_config)
    if send_to_chatwork(chatwork_config, message):
        print("ChatWork にアラートを送信しました。")
    else:
        print("ChatWork への送信に失敗しました。環境変数 CHATWORK_API_TOKEN を確認してください。", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print("用法: python main.py <ポータル名のディレクトリ> [setting.json のパス]", file=sys.stderr)
        sys.exit(1)

    portal_dir = Path(sys.argv[1]).resolve()
    if not portal_dir.is_dir():
        print(f"エラー: ディレクトリが見つかりません: {portal_dir}", file=sys.stderr)
        sys.exit(1)

    settings_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / "setting.json"
    if not settings_path.exists():
        print(f"エラー: 設定ファイルが見つかりません: {settings_path}", file=sys.stderr)
        sys.exit(1)

    run(portal_dir, settings_path)


if __name__ == "__main__":
    main()
