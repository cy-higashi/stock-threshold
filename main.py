# -*- coding: utf-8 -*-
"""
在庫しきい値アラート エントリポイント。
1ポータル単位で検出する。

引数:
  - 日次在庫数ディレクトリ（必須）: 例 G:\\...\\2025-10-10\\Amazon
    末尾のディレクトリ名（Amazon）が対象ポータル名となる
  - 設定ファイルパス（任意、省略時は setting.json）
"""
import json
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from app.alert_sender import build_alert_message, send_to_chatwork
from app.stock_parser import parse_portal_stock
from app.threshold_loader import load_thresholds


def load_settings(settings_path: Path) -> dict:
    """setting.json を読み込む。"""
    with open(settings_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _find_portal_config(portals: dict, portal_name: str) -> dict | None:
    """portals.{ポータル名} を検索する。ポータル名は小文字に正規化済み。キーは大文字小文字を区別せず照合。"""
    if portal_name in portals:
        return portals[portal_name]
    key_lower = portal_name.lower()
    for k, v in portals.items():
        if (k or "").lower() == key_lower:
            return v
    return None


def run(daily_stock_dir: Path, settings_path: Path) -> None:
    """
    日次在庫数ディレクトリの末尾をポータル名とし、
    1. 日次在庫数ファイルを再帰検索し、setting.json で定義したカラムから商品コードと在庫数を取得
    2. 最低在庫数定義CSV/Excel を参照
    3. 在庫数 <= 最低在庫数 の返礼品コードをアラート対象（最低在庫数CSVに無い返礼品コードはスキップ）
    4. アラートがあれば ChatWork 送信
    """
    settings = load_settings(settings_path)
    chatwork_config = settings.get("chatwork") or {}
    portals = settings.get("portals") or {}

    # 末尾のディレクトリ名をポータル名とし、小文字に正規化して比較
    portal_name = daily_stock_dir.name.strip().lower()
    portal_config = _find_portal_config(portals, portal_name)
    if not portal_config:
        print(f"エラー: setting.json にポータル名「{portal_name}」の定義がありません。", file=sys.stderr)
        sys.exit(1)

    portal_min_stock_path = portal_config.get("min_stock_base_path")
    if not portal_min_stock_path:
        print(f"エラー: ポータル「{portal_name}」に min_stock_base_path が設定されていません。", file=sys.stderr)
        sys.exit(1)

    # 1. 日次在庫数ディレクトリを再帰的に検索し、設定で指定したカラムから商品コードと在庫数を取得
    stock_by_code = parse_portal_stock(daily_stock_dir, portal_config)

    # 2. 最低在庫数定義ファイル（portals.{ポータル名}.min_stock_base_path で指定した CSV/XLSX）を読み込み
    min_by_code = load_thresholds(portal_min_stock_path, portal_config)

    # 3. 在庫数 <= 最低在庫数 の返礼品コードをアラート対象にする。最低在庫数CSVに存在しない返礼品コードはスキップ
    alerts: list[dict] = []
    for product_code, current in stock_by_code.items():
        if product_code not in min_by_code:
            continue
        min_stock = min_by_code[product_code]
        if current <= min_stock:
            alerts.append({
                "portal_name": portal_name,
                "product_code": product_code,
                "current_stock": current,
                "min_stock": min_stock,
            })

    if not alerts:
        return

    # 4. テンプレートと setting.json の API で ChatWork 送信
    message = build_alert_message(alerts, chatwork_config)
    ok, err = send_to_chatwork(chatwork_config, message)
    if ok:
        print("ChatWork にアラートを送信しました。")
    else:
        print(f"ChatWork への送信に失敗しました。{err}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    if len(sys.argv) < 2:
        print(
            "用法: python main.py <日次在庫数ディレクトリ> [setting.json のパス]\n"
            "  例: python main.py \"G:\\共有ドライブ\\★OD\\99_Ops\\アーカイブ(Stock)\\2025-10-10\\Amazon\"",
            file=sys.stderr,
        )
        sys.exit(1)

    daily_stock_dir = Path(sys.argv[1]).resolve()
    if not daily_stock_dir.is_dir():
        print(f"エラー: ディレクトリが見つかりません: {daily_stock_dir}", file=sys.stderr)
        sys.exit(1)

    settings_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent / "setting.json"
    if not settings_path.exists():
        print(f"エラー: 設定ファイルが見つかりません: {settings_path}", file=sys.stderr)
        sys.exit(1)

    run(daily_stock_dir, settings_path)


if __name__ == "__main__":
    main()
