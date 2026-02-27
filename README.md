# 在庫しきい値アラート

ポータルが指定した最低在庫数未満の商品があった場合、ChatWork にアラートを通知するツールです。

## 基本的な使い方

### 1. 環境変数に API トークンをセットする

ChatWork API トークンを環境変数 `CHATWORK_API_TOKEN` に設定してください。

- コマンドプロンプトやタスクスケジューラから実行する場合: システム環境変数またはユーザー環境変数に追加
- `.env` ファイルで `CHATWORK_API_TOKEN=トークン値` を指定することも可能（プロジェクト直下に配置）

### 2. メッセージの対象者を setting.json に記載する

`setting.json` の `chatwork.mention_members` にアラートの通知先を指定します。

```json
"mention_members": [
  {
    "name": "表示名",
    "account_id": 12345678
  }
]
```

- `account_id`: ChatWork のアカウント ID（数値）
- 複数指定可能

### 3. 最低在庫数 CSV の配置を確認する

各ポータルの `portals.{ポータル名}.min_stock_base_path` に、ポータルが指定する最低在庫数 CSV の**ファイルパス**を設定します。

- CSV には「返礼品コード」または「商品コード」列と「最低在庫数」列が必要
- パスが空のポータルは処理対象外となります

### 4. 実行する

**ポータル単体で実行:**

```text
python main.py <ポータル名のディレクトリ> [setting.json のパス]
```

例: `python main.py "D:\在庫\2025-10-10\Amazon"`

**複数ポータルを一括実行:**

```text
run_all_portals.bat [ベースディレクトリ] [setting.json のパス]
```

- 引数なし: `G:\共有ドライブ\★OD\99_Ops\アーカイブ(Stock)` 配下の直近日付（yyyy-MM-dd）を自動で対象
- 引数あり: 第 1 引数をベースディレクトリとして使用
