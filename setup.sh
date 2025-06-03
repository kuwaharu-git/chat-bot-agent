#!/bin/bash

# エラーがあればスクリプトを停止
set -e

echo "ウェブサイト情報チャットボットのセットアップを開始します..."

# Pythonが利用可能か確認
if ! command -v python3 &> /dev/null; then
    echo "Python 3がインストールされていません。インストールしてください。"
    exit 1
fi

# 仮想環境の作成
echo "Python仮想環境を作成しています..."
python3 -m venv venv

# 仮想環境の有効化
echo "仮想環境を有効化しています..."
source venv/bin/activate

# 依存関係のインストール
echo "依存関係をインストールしています..."
pip install --upgrade pip
pip install -r requirements.txt

# .envファイルの作成
if [ ! -f .env ]; then
    echo "環境変数ファイル(.env)を作成しています..."
    cat > .env << EOL
# Google Gemini APIキー
GOOGLE_API_KEY=your_google_api_key_here

# ターゲットのウェブサイトURL（デフォルト）
TARGET_WEBSITE_URL=https://example.com

# APIサーバー設定
API_HOST=0.0.0.0
API_PORT=8000

# Geminiモデル設定
GEMINI_MODEL_NAME=gemini-pro
EOL
    echo ".envファイルが作成されました。APIキーを設定してください。"
else
    echo ".envファイルはすでに存在します。"
fi

echo "セットアップが完了しました！"
echo "1. .envファイルにGemini APIキーを設定してください。"
echo "2. 仮想環境を有効化するには、次のコマンドを実行してください: source venv/bin/activate"
echo "3. コマンドラインインターフェースを使用するには: python chatbot.py"
echo "4. Web APIを起動するには: python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload"
echo "5. ウェブインターフェースにアクセスするには: ブラウザで http://localhost:8000 にアクセスしてください" 