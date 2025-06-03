# ウェブサイト情報チャットボット

このプロジェクトは、指定したウェブサイトの情報を取得し、その内容に基づいて質問に答えるチャットボットです。Google Gemini APIを使用して自然言語処理を行います。

## 機能

- 指定されたURLからウェブサイトの内容を抽出
- 抽出した情報を基にユーザーの質問に回答
- コマンドラインインターフェース
- Web API（FastAPI）による提供

## 前提条件

- Python 3.8以上
- Google Gemini API キー

## セットアップ

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd chat-bot-agent
```

### 2. 仮想環境の作成と有効化

```bash
python -m venv venv

# Windowsの場合
venv\Scripts\activate

# macOS/Linuxの場合
source venv/bin/activate
```

### 3. 依存関係のインストール

```bash
pip install -r requirements.txt
```

### 4. 環境変数の設定

`.env`ファイルをプロジェクトのルートディレクトリに作成し、以下の内容を設定します：

```
# Google Gemini APIキー
GOOGLE_API_KEY=your_google_api_key_here

# ターゲットのウェブサイトURL（デフォルト）
TARGET_WEBSITE_URL=https://example.com

# APIサーバー設定
API_HOST=0.0.0.0
API_PORT=8000

# Geminiモデル設定
GEMINI_MODEL_NAME=gemini-pro
```

## 使用方法

### コマンドラインインターフェース

```bash
python chatbot.py
```

### Web API

```bash
python app.py
```

APIエンドポイント:
- `POST /initialize` - チャットボットを特定のURLで初期化
- `POST /ask` - 質問を送信して回答を取得
- `GET /history` - チャット履歴を取得

## APIリクエスト例

### チャットボットの初期化

```bash
curl -X POST "http://localhost:8000/initialize" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com"}'
```

### 質問の送信

```bash
curl -X POST "http://localhost:8000/ask" \
     -H "Content-Type: application/json" \
     -d '{"question": "このウェブサイトについて教えてください"}'
```

### チャット履歴の取得

```bash
curl -X GET "http://localhost:8000/history"
```

## プロジェクト構造

- `scraper.py` - ウェブサイトのスクレイピング機能
- `chatbot.py` - Gemini APIを使用したチャットボット機能
- `app.py` - FastAPIを使用したWeb API
- `config.py` - 設定ファイル
- `requirements.txt` - 依存関係リスト

## ライセンス

[LICENSE](LICENSE)ファイルを参照してください。 