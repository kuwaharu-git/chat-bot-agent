import os
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# ターゲットのウェブサイトURL
TARGET_WEBSITE_URL = os.getenv("TARGET_WEBSITE_URL", "https://example.com")

# APIのホストとポート
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8000"))

# Ollama設定
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "gemma") 