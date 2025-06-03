from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import GeminiChatbot
from config import API_HOST, API_PORT
import uvicorn

app = FastAPI(title="ウェブサイト情報チャットボットAPI")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 本番環境では適切に制限すべき
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# グローバルチャットボットインスタンス
chatbot = GeminiChatbot()

# リクエストモデル
class URLRequest(BaseModel):
    url: str
    include_subpages: bool = True
    max_pages: int = 10
    max_depth: int = 2

class QuestionRequest(BaseModel):
    question: str

# レスポンスモデル
class ChatResponse(BaseModel):
    answer: str
    pages_scraped: int = 0

@app.post("/initialize", response_model=ChatResponse)
async def initialize_chatbot(request: URLRequest = Body(...)):
    """チャットボットを指定されたURLで初期化する"""
    if not request.url:
        raise HTTPException(status_code=400, detail="URLが指定されていません")
        
    success, message = chatbot.initialize_with_url(
        request.url, 
        request.include_subpages, 
        request.max_pages, 
        request.max_depth
    )
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
    
    # 取得したページ数を取得
    pages_scraped = len(chatbot.scraper.visited_urls) if request.include_subpages else 1
        
    return ChatResponse(answer=message, pages_scraped=pages_scraped)

@app.post("/ask", response_model=ChatResponse)
async def ask_question(request: QuestionRequest = Body(...)):
    """チャットボットに質問する"""
    if not request.question:
        raise HTTPException(status_code=400, detail="質問が指定されていません")
        
    answer = chatbot.ask(request.question)
    
    # 取得したページ数を取得
    pages_scraped = len(chatbot.scraper.visited_urls) if hasattr(chatbot.scraper, 'visited_urls') else 0
    
    return ChatResponse(answer=answer, pages_scraped=pages_scraped)

@app.get("/history")
async def get_history():
    """チャット履歴を取得する"""
    return chatbot.get_chat_history()

# サーバー起動
if __name__ == "__main__":
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True) 