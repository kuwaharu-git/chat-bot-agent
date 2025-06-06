@echo off
setlocal

echo ウェブサイト情報チャットボットのセットアップを開始します...

REM Pythonが利用可能か確認
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Python 3がインストールされていません。インストールしてください。
    exit /b 1
)

REM 仮想環境の作成
echo Python仮想環境を作成しています...
python -m venv venv

REM 仮想環境の有効化
echo 仮想環境を有効化しています...
call venv\Scripts\activate

REM 依存関係のインストール
echo 依存関係をインストールしています...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM .envファイルの作成
if not exist .env (
    echo 環境変数ファイル(.env)を作成しています...
    (
        echo # ターゲットのウェブサイトURL（デフォルト）
        echo TARGET_WEBSITE_URL=https://example.com
        echo.
        echo # APIサーバー設定
        echo API_HOST=0.0.0.0
        echo API_PORT=8000
        echo.
        echo # Ollama設定
        echo OLLAMA_BASE_URL=http://localhost:11434
        echo OLLAMA_MODEL_NAME=gemma
    ) > .env
    echo .envファイルが作成されました。
) else (
    echo .envファイルはすでに存在します。
)

echo セットアップが完了しました！
echo 1. 仮想環境を有効化するには、次のコマンドを実行してください: venv\Scripts\activate
echo 2. コマンドラインインターフェースを使用するには: python chatbot.py
echo 3. Web APIを起動するには: python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
echo 4. ウェブインターフェースにアクセスするには: ブラウザで http://localhost:8000 にアクセスしてください
echo 5. Ollamaが正しく設定されていることを確認してください（デフォルト: http://localhost:11434）
echo 6. Ollamaで「gemma」モデルをダウンロードしてください: ollama pull gemma

endlocal 