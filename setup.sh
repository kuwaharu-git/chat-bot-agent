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
# ターゲットのウェブサイトURL（デフォルト）
TARGET_WEBSITE_URL=https://example.com

# APIサーバー設定
API_HOST=0.0.0.0
API_PORT=8000

# Ollama設定
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL_NAME=gemma
EOL
    echo ".envファイルが作成されました。"
else
    echo ".envファイルはすでに存在します。"
fi

echo "セットアップが完了しました！"
echo "1. 仮想環境を有効化するには、次のコマンドを実行してください: source venv/bin/activate"
echo "2. コマンドラインインターフェースを使用するには: python chatbot.py"
echo "3. Web APIを起動するには: python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload"
echo "4. ウェブインターフェースにアクセスするには: ブラウザで http://localhost:8000 にアクセスしてください"
echo "5. Ollamaが正しく設定されていることを確認してください（デフォルト: http://localhost:11434）"
echo "6. Ollamaで「gemma」モデルをダウンロードしてください: ollama pull gemma"