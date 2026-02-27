# -*- coding: utf-8 -*-
"""
アラート文の組み立てと ChatWork API への送信。
トークンは環境変数 CHATWORK_API_TOKEN で渡す。
"""
import os
from typing import Any

import requests


# 環境変数キー（トークン）
CHATWORK_TOKEN_ENV = "CHATWORK_API_TOKEN"

# 1メッセージの最大文字数（ChatWork 制限に合わせて分割する場合用）
MESSAGE_MAX_LENGTH = 10000


def build_alert_message(alerts: list[dict[str, Any]], chatwork_config: dict[str, Any] | None = None) -> str:
    """
    アラート一覧から1本のメッセージ文を組み立てる。
    各要素: portal_name, product_code, current_stock, min_stock
    chatwork_config に mention_members が含まれる場合、メッセージ先頭に [To:account_id] 名前 を付与する。
    """
    lines: list[str] = []
    if chatwork_config:
        members = chatwork_config.get("mention_members") or []
        for m in members:
            name = (m.get("name") or "").strip()
            account_id = m.get("account_id")
            if account_id is not None:
                lines.append(f"[To:{account_id}]{' ' + name if name else ''}")
    if lines:
        lines.append("")
    lines.append("[info][title]在庫しきい値アラート[/title]")
    for a in alerts:
        shortage = a.get("min_stock", 0) - a.get("current_stock", 0)
        lines.append(
            f"・{a.get('portal_name', '')} / 商品コード: {a.get('product_code', '')} "
            f"現在: {a.get('current_stock', 0)} 最低: {a.get('min_stock', 0)} 不足: {shortage}"
        )
    lines.append("[/info]")
    return "\n".join(lines)


def send_to_chatwork(chatwork_config: dict[str, Any], message: str) -> bool:
    """
    setting.json の chatwork 設定とメッセージで ChatWork に送信する。
    トークンは環境変数 CHATWORK_API_TOKEN から取得。
    """
    token = os.environ.get(CHATWORK_TOKEN_ENV)
    if not token:
        return False

    base_url = (chatwork_config.get("api_base_url") or "https://api.chatwork.com").rstrip("/")
    room_id = chatwork_config.get("room_id")
    endpoint_tpl = chatwork_config.get("message_endpoint") or "/v2/rooms/{room_id}/messages"
    if not room_id:
        return False

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
        resp = requests.post(
            url,
            headers={"X-ChatWorkToken": token},
            data={"body": body},
            timeout=30,
        )
        if resp.status_code not in (200, 201):
            return False
    return True
