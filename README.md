# セキュリティフィード監視システム

セキュリティ脆弱性情報、モバイルアプリ審査情報、パッケージアップデート情報などをRSSフィードから自動収集し、Discordに通知するシステムです。

## 機能

- **複数のRSSフィード監視** - NVD、JPCERT、GitHub Advisory、Android/iOS開発者情報など（各フィード先頭5件を取得）
- **キーワードベースのフィルタリング** - セキュリティキーワード、言語名、重要度でフィルタ
- **優先度付け（0-10段階）** - High Priority（優先度8以上）のみ通知、Low Priority（7以下）はスキップ
- **重複排除** - SQLiteで既読管理、同じエントリは二度通知しない
- **Discord Webhook通知** - High Priorityアラートを個別に赤色で強調表示
- **🤖 AI要約機能（Ollama統合）** - 完全無料、オプション機能
  - 英語タイトルを日本語に自動翻訳（本文から内容を理解して適切なタイトルを生成）
  - 記事本文から日本語要約を自動生成（2-3文）
  - High Priority通知のみ適用
  - Ollama未起動時は自動的に無効化

## カバーしている言語・エコシステム

### プログラミング言語
- **Node.js / JavaScript / TypeScript** - npm, Node.js Security Releases, GitHub Advisory
- **Python** - pip, PyPI (GitHub Advisory経由)
- **Dart / Flutter** - pub.dev (GitHub Advisory経由)
- **Kotlin / Java** - Maven, Gradle (GitHub Advisory経由)
- **Ruby** - RubyGems, Ruby Security, GitHub Advisory
- **Swift / iOS** - CocoaPods, Apple Developer News
- **Shell / Bash / Zsh** - Linux Security (Ubuntu Security経由)

### プラットフォーム
- **Android** - Android Developers Blog, Google Play Console関連
- **iOS** - Apple Developer News, App Store審査関連
- **Docker** - Container Security (GitHub Advisory経由)
- **Linux / Ubuntu** - Ubuntu Security Notices

### セキュリティ情報源
- **NVD** - National Vulnerability Database (全般的なCVE情報)
- **JPCERT/CC** - 日本のセキュリティ情報
- **IPA** - 情報処理推進機構のセキュリティアラート
- **GitHub Advisory** - 多言語対応のパッケージ脆弱性情報
- **窓の杜** - 日本語の技術ニュース（High Severityのみ）

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
│   ├── summarizer.py      # AI要約（Ollama）
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
3. `.env`ファイルを作成して設定

```bash
# .env.example をコピー
cp .env.example .env

# .env ファイルを編集して、実際のWebhook URLを設定
# DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ACTUAL_WEBHOOK_URL
```

**または**、環境変数として直接設定：

```bash
# Linux/macOS
export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"

# または .bashrc / .zshrc に追記
echo 'export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"' >> ~/.bashrc
source ~/.bashrc
```

### 4. Ollama（AI要約）のセットアップ（オプション）

High Priority通知に日本語タイトル＆要約を自動追加する機能です（完全無料）。

**📝 AI要約機能の動作:**
1. **英語タイトルの日本語化**
   - 英語タイトルを検出（日本語文字が含まれていない場合）
   - 記事本文を読み込んで内容を理解
   - 適切な日本語タイトルを生成（20文字以内推奨）
   - 例: `CVE-2018-25092` → `DiscordSailv2脆弱性：不正アクセスリスク`

2. **日本語要約の生成**
   - 記事URLから本文を自動取得（BeautifulSoup4）
   - Ollama APIで日本語要約を生成（2-3文）
   - Discord通知の説明欄に追加

3. **対象**
   - High Priority（優先度8以上）通知のみ
   - Ollama未起動時は自動的に無効化（通常通知は継続）

**Ollamaのインストール**

```bash
# Linux/macOS
curl -fsSL https://ollama.com/install.sh | sh

# または https://ollama.com/download からダウンロード
```

**モデルのダウンロード**

```bash
# 推奨: gemma2（日本語対応、軽量で高速）
ollama pull gemma2

# または llama3.2
ollama pull llama3.2
```

**モデルの変更方法**

デフォルトは `gemma2:9b` です。環境変数で変更できます：

```bash
# .env ファイルに追記
OLLAMA_MODEL=qwen2.5:0.5b  # VPS/低スペック向け軽量版

# または直接環境変数を設定
export OLLAMA_MODEL=qwen2.5:0.5b
```

**推奨モデル（スペック別）:**
- **低スペック（メモリ1-2GB）**: `qwen2.5:0.5b` - 約400MB、軽量で高速
- **中スペック（メモリ2-4GB）**: `gemma2:2b` - 約1.5GB
- **高スペック（メモリ6GB以上）**: `gemma2:9b` - 約5.4GB、高精度（デフォルト）

**Ollamaサーバーの起動**

```bash
# バックグラウンドで自動起動（通常は自動で起動済み）
ollama serve
```

**動作確認**

```bash
curl http://localhost:11434/api/tags
```

JSONレスポンスが返ってくればOKです。

### 5. テスト実行

```bash
python3 src/main.py
```

**初回実行時の注意:**
- 各フィードから先頭5件を取得し、High Priority（優先度8以上）のみ通知
- 初回は15-20件程度の通知が送信される可能性があります
- Ollama有効時、各通知に5-10秒程度かかります（AI要約生成のため）
- Discord Rate Limit（429エラー）が発生する場合がありますが、正常動作です
- 2回目以降は新規エントリのみ通知されます（通常0-3件程度）

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

**フィルタ構造:**
- `global`: すべてのフィードに適用
  - `include_keywords`: High/Critical Severityキーワード（critical, high, severe, RCE, zero-day, exploit など）
  - `exclude_keywords`: 除外キーワード（low severity, minor など）
- `categories`: カテゴリ別のフィルタ
  - `package`: 言語・パッケージマネージャー名（npm, pip, maven など）+ セキュリティキーワード必須
  - `cve`: モバイル・OS・言語・コンテナ関連（android, ios, linux, docker など）
  - `mobile`: アプリ審査関連（Play Console, App Store, 審査ガイドライン など）
- `per_feed`: 特定フィード専用のフィルタ
  - Node.js Security Releases: デフォルト優先度10（公式セキュリティリリース）
  - JPCERT/CC, IPA: タイトルのみフィード用の特別処理

**優先度ルール:**
- 優先度8以上のみDiscord通知（High Priority）
- 優先度7以下はスキップ（ログには記録）
- CVE番号を含む: 優先度7以上
- priority_keywordsにマッチ: 優先度10
- high_severity_keywordsにマッチ: 優先度8以上

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

**cronを止める場合:**

```bash
# cron設定を編集して該当行を削除またはコメントアウト
crontab -e

# または全削除
crontab -r

# 設定を確認
crontab -l
```

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

**有効化:**

```bash
sudo systemctl enable tech_news.timer
sudo systemctl start tech_news.timer

# 確認
sudo systemctl status tech_news.timer
```

**停止・無効化:**

```bash
# タイマーを停止
sudo systemctl stop tech_news.timer

# タイマーを無効化（自動起動を停止）
sudo systemctl disable tech_news.timer

# サービスも停止（実行中の場合）
sudo systemctl stop tech_news.service

# 状態確認
sudo systemctl status tech_news.timer
sudo systemctl status tech_news.service
```

## データベース管理

### seen.db（SQLite）の操作

既読管理に使用しているSQLiteデータベースを直接操作できます。

**データベースを開く:**

```bash
sqlite3 data/seen.db
```

**よく使うSQLコマンド:**

```sql
-- テーブル構造を確認
.schema

-- 全件表示
SELECT * FROM seen;

-- 件数確認
SELECT COUNT(*) FROM seen;

-- 最近の既読エントリ（10件）
SELECT id, seen_at FROM seen ORDER BY seen_at DESC LIMIT 10;

-- 特定のIDを検索
SELECT * FROM seen WHERE id = 'xxxxx';

-- 古いエントリを削除（30日以前）
DELETE FROM seen WHERE seen_at < datetime('now', '-30 days');

-- 全削除（初期化）
DELETE FROM seen;

-- データベースを最適化
VACUUM;

-- 終了
.exit
```

**便利なコマンド:**

```bash
# ヘッダー付きで表示
sqlite3 data/seen.db -header -column "SELECT * FROM seen LIMIT 10;"

# CSVエクスポート
sqlite3 data/seen.db -csv "SELECT * FROM seen;" > seen_backup.csv

# 件数だけ確認
sqlite3 data/seen.db "SELECT COUNT(*) FROM seen;"

# データベースのバックアップ
cp data/seen.db data/seen.db.backup_$(date +%Y%m%d)

# データベースを完全リセット（再取得したい場合）
rm data/seen.db
# 次回実行時に自動再作成されます
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
3. 手動実行でエラーが出ないか確認: `python3 src/main.py`
4. High Priority（優先度8以上）のエントリがあるか確認（7以下は通知されない仕様）

### フィードが取得できない

- ネットワーク接続を確認
- フィードのURLが正しいか確認
- ログでエラーメッセージを確認

### 重複した通知が届く

- `data/seen.db` が正しく機能しているか確認
- データベースファイルの権限を確認

### AI要約が生成されない

1. **Ollamaが起動しているか確認**
   ```bash
   curl http://localhost:11434/api/tags
   ```
   エラーが出る場合は `ollama serve` で起動

2. **モデルがダウンロードされているか確認**
   ```bash
   ollama list
   ```
   `gemma2:9b` または `llama3.2` が表示されるか確認

3. **ログを確認**
   - `Generating Japanese title for: ...` が出力されているか
   - `Ollama API failed: ...` エラーがないか確認

4. **High Priority通知のみ対象**
   - 優先度7以下の通知にはAI要約は追加されません

### AI要約の精度が低い

- より大きなモデルに変更: `ollama pull llama3.1:70b`（要高スペックマシン）
- プロンプトを調整: `src/summarizer.py` の `_generate_summary()` を編集

## ライセンス

MIT License

## 拡張アイデア

- **Slack/Teams対応** - 他のチャットツールへの通知
- **Web UI** - フィード閲覧、フィルタ編集、統計表示
- **スクレイピング対応** - RSSがないサイトからも情報収集
- **CVSS自動取得** - NVD APIでCVSSスコアを自動取得して優先度判定
- **メール通知** - 重要度に応じてメール送信
- **多言語AI要約** - 英語・中国語・韓国語記事の日本語要約
- **AI分類** - 脆弱性の影響範囲や修正方法を自動分類
- **通知のグルーピング** - 関連する脆弱性をまとめて通知
- **Webhook送信** - 他のシステムとの連携
