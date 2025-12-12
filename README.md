# セキュリティフィード監視システム

セキュリティ脆弱性情報、モバイルアプリ審査情報、パッケージアップデート情報などをRSSフィードから自動収集し、Discordに通知するシステムです。

## 機能

- 複数のRSSフィード（NVD、JPCERT、GitHub Advisory、Android/iOS開発者情報など）から情報を自動収集
- キーワードベースのフィルタリング
- 優先度付け（高優先度のアラートは個別通知）
- 重複排除（SQLiteで既読管理）
- Discord Webhook経由での通知

## ディレクトリ構成

```
tech_news/
├── config/
│   ├── feeds.yaml          # フィード定義
│   └── filters.yaml        # フィルタルール
├── src/
│   ├── main.py            # メインスクリプト
│   ├── feed_parser.py     # RSSパーサー
│   ├── filter_engine.py   # フィルタエンジン
│   ├── notifier.py        # Discord通知
│   └── db.py              # 既読管理DB
├── data/
│   └── seen.db            # SQLite（自動生成）
├── logs/
│   └── feed.log           # ログファイル（自動生成）
├── requirements.txt
└── README.md
```

## セットアップ

### 1. Python環境の準備

```bash
# Python 3.8以上が必要
python3 --version

# 仮想環境の作成（推奨）
python3 -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

### 2. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 3. Discord Webhookの設定

1. Discordサーバーの設定から「連携サービス」→「ウェブフック」を作成
2. ウェブフックURLをコピー
3. 環境変数に設定

```bash
# Linux/macOS
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"

# または .bashrc / .zshrc に追記
echo 'export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"' >> ~/.bashrc
source ~/.bashrc
```

### 4. テスト実行

```bash
python src/main.py
```

初回実行時は多くの通知が送信される可能性があります。

## 設定ファイル

### feeds.yaml

監視するRSSフィードを定義します。

```yaml
feeds:
  - name: "フィード名"
    url: "https://example.com/feed.rss"
    category: "cve"  # cve, security, mobile, package, os, general
    enabled: true    # false にすると無効化
```

### filters.yaml

フィルタリングルールを定義します。

- `global`: すべてのフィードに適用
- `categories`: カテゴリ別のフィルタ
- `per_feed`: 特定フィード専用のフィルタ

キーワードは大文字小文字を区別しません。

## cron設定（定期実行）

### VPSで定期実行する場合

```bash
crontab -e
```

以下を追加：

```bash
# 環境変数
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxx/yyyy

# 6時間ごとに実行
0 */6 * * * cd /path/to/tech_news && /path/to/venv/bin/python src/main.py >> logs/cron.log 2>&1

# または1日2回（朝9時と夜9時）
0 9,21 * * * cd /path/to/tech_news && /path/to/venv/bin/python src/main.py >> logs/cron.log 2>&1
```

**注意**: パスは絶対パスで指定してください。

### systemdタイマーで実行する場合（推奨）

**tech_news.service**

```ini
[Unit]
Description=Security Feed Monitor
After=network.target

[Service]
Type=oneshot
User=your-username
WorkingDirectory=/path/to/tech_news
Environment="DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/xxxx/yyyy"
ExecStart=/path/to/venv/bin/python src/main.py

[Install]
WantedBy=multi-user.target
```

**tech_news.timer**

```ini
[Unit]
Description=Security Feed Monitor Timer

[Timer]
OnCalendar=*-*-* 00/6:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

有効化：

```bash
sudo systemctl enable tech_news.timer
sudo systemctl start tech_news.timer

# 確認
sudo systemctl status tech_news.timer
```

## カスタマイズ

### フィードの追加

`config/feeds.yaml` に新しいフィードを追加：

```yaml
- name: "My Custom Feed"
  url: "https://example.com/rss"
  category: "security"
```

### フィルタの調整

`config/filters.yaml` でキーワードを追加・削除：

```yaml
global:
  include_keywords:
    - "新しいキーワード"
    - "another keyword"
```

### 通知先の変更

Slack など他のサービスに通知したい場合は、`src/notifier.py` を編集してください。

## トラブルシューティング

### 通知が送信されない

1. `DISCORD_WEBHOOK_URL` が正しく設定されているか確認
2. ログファイル `logs/feed.log` を確認
3. 手動実行でエラーが出ないか確認: `python src/main.py`

### フィードが取得できない

- ネットワーク接続を確認
- フィードのURLが正しいか確認
- ログでエラーメッセージを確認

### 重複した通知が届く

- `data/seen.db` が正しく機能しているか確認
- データベースファイルの権限を確認

## ライセンス

MIT License

## 拡張アイデア

- Slack対応
- Web UI（閲覧・フィルタ編集）
- RSSがないサイトのスクレイピング対応
- NVD APIでCVSSスコア自動取得
- メール通知対応
