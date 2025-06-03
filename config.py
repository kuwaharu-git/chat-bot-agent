import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# Google Gemini APIキー
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# ターゲットのウェブサイトURL
TARGET_WEBSITE_URL = os.getenv("TARGET_WEBSITE_URL", "https://example.com")

# APIのホストとポート
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# モデル設定
GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-pro") 