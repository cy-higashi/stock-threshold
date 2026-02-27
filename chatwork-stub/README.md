# ChatWork API Stub

ChatWork API のスタブサーバー。Apache をリバースプロキシとして前置し、リクエストログを取得できる。

## 起動

```bash
docker compose up -d
```

- **8080**: Apache（リバースプロキシ）→ chatwork-stub へ転送

## API 通信ログの確認

**アクセスログ（Apache）**
```bash
docker compose logs -f apache
```
アクセスログ（Apache の Combined Log Format）が標準出力に出力される。

**POST ボディ（chatwork-stub）**
```bash
docker compose logs -f chatwork-stub
```
POST リクエストのボディが stderr に出力される。
