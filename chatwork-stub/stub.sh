#!/bin/sh
# ChatWork API Stub
# POST /v2/rooms/{Int}/messages へのリクエストに対して
# 200 OK と {"message_id": "1234"} を返却する

# Content-Length をパース
CONTENT_LENGTH=0
while read -r line; do
  line=$(printf '%s' "$line" | tr -d '\r')
  [ -z "$line" ] && break
  case "$line" in
    [Cc]ontent-[Ll]ength:\ *)
      CONTENT_LENGTH=$(echo "${line#*:}" | tr -d ' ')
      ;;
  esac
done

# ボディがあれば読み取り、stderr にログ出力（docker compose logs で確認可能）
if [ -n "$CONTENT_LENGTH" ] && [ "$CONTENT_LENGTH" -gt 0 ] 2>/dev/null; then
  BODY_FILE="/tmp/post-body.$$"
  dd bs=1 count="$CONTENT_LENGTH" 2>/dev/null > "$BODY_FILE"
  echo "---- POST body (len=$CONTENT_LENGTH) ----" >&2
  cat "$BODY_FILE" >&2
  echo "" >&2
  echo "----" >&2
  rm -f "$BODY_FILE"
fi

# HTTP 200 レスポンスを返却（body 24 bytes = 22 chars + \r\n）
printf 'HTTP/1.1 200 OK\r\n'
printf 'Content-Type: application/json\r\n'
printf 'Content-Length: 24\r\n'
printf 'Connection: close\r\n'
printf '\r\n'
printf '{"message_id": "1234"}\r\n'
sleep 0.2
