# -*- coding: utf-8 -*-
"""
アラート文の組み立てと ChatWork API への送信。
トークンは環境変数 CHATWORK_API_TOKEN で渡す。
"""
import os
from pathlib import Path
from typing import Any

import requests
from jinja2 import Environment, FileSystemLoader


# 環境変数キー（トークン）
CHATWORK_TOKEN_ENV = "CHATWORK_API_TOKEN"

# 1メッセージの最大文字数（ChatWork 制限に合わせて分割する場合用）
MESSAGE_MAX_LENGTH = 10000

# テンプレートディレクトリ（プロジェクトルート）
_TEMPLATE_DIR = Path(__file__).resolve().parent.parent


def build_alert_message(alerts: list[dict[str, Any]], chatwork_config: dict[str, Any] | None = None) -> str:
    """
    アラート一覧から alert_message.tpl を用いて1本のメッセージ文を組み立てる。
    テンプレート変数:
      - mention_members: setting.json の chatwork.mention_members
      - alerts: 各要素は portal_name, product_code, portal_min_product_stock_num, portal_product_stock_num
    """
    mention_members = []
    if chatwork_config:
        mention_members = chatwork_config.get("mention_members") or []

    # テンプレート用にアラートを整形
    template_alerts = [
        {
            "portal_name": a.get("portal_name", ""),
            "product_code": a.get("product_code", ""),
            "portal_min_product_stock_num": a.get("min_stock", 0),
            "portal_product_stock_num": a.get("current_stock", 0),
        }
        for a in alerts
    ]

    env = Environment(loader=FileSystemLoader(_TEMPLATE_DIR))
    template = env.get_template("alert_message.tpl")
    return template.render(mention_members=mention_members, alerts=template_alerts)


def send_to_chatwork(chatwork_config: dict[str, Any], message: str) -> tuple[bool, str | None]:
    """
    setting.json の chatwork 設定とメッセージで ChatWork に送信する。
    トークンは環境変数 CHATWORK_API_TOKEN から取得。
    戻り値: (成功可否, 失敗時のエラー内容)
    """
    token = os.environ.get(CHATWORK_TOKEN_ENV)
    if not token:
        return False, "CHATWORK_API_TOKEN が未設定です。.env を確認してください。"

    base_url = (chatwork_config.get("api_base_url") or "https://api.chatwork.com").rstrip("/")
    room_id = chatwork_config.get("room_id")
    endpoint_tpl = chatwork_config.get("message_endpoint") or "/v2/rooms/{room_id}/messages"
    if not room_id:
        return False, "room_id が未設定です。setting.json を確認してください。"

    endpoint = endpoint_tpl.replace("{room_id}", str(room_id))
    url = f"{base_url}{endpoint}"

    # 長文は分割
    payloads = []
    if len(message) <= MESSAGE_MAX_LENGTH:
        payloads.append(message)
    else:
        start = 0
        while start < len(message):
            payloads.append(message[start : start + MESSAGE_MAX_LENGTH])
            start += MESSAGE_MAX_LENGTH

    for body in payloads:
        try:
            resp = requests.post(
                url,
                headers={"X-ChatWorkToken": token},
                data={"body": body},
                timeout=30,
            )
        except requests.RequestException as e:
            return False, f"通信エラー: {e}"
        if resp.status_code not in (200, 201):
            return False, f"HTTP {resp.status_code}: {resp.text[:500]}"
    return True, None
