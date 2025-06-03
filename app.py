from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from chatbot import GeminiChatbot
from config import API_HOST, API_PORT
import uvicorn
from db_manager import DBManager

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
chatbot = GeminiChatbot(use_cache=True)

# データベースマネージャー
db_manager = DBManager()

# リクエストモデル
class URLRequest(BaseModel):
    url: str
    include_subpages: bool = True
    max_pages: int = 10
    max_depth: int = 2
    use_cache: bool = True
    force_refresh: bool = False

class QuestionRequest(BaseModel):
    question: str

# レスポンスモデル
class ChatResponse(BaseModel):
    answer: str
    pages_scraped: int = 0
    from_cache: bool = False

class CacheStatsResponse(BaseModel):
    sites_count: int = 0
    urls_count: int = 0
    last_scraped: str = None
    db_size_kb: float = 0

class CachedSiteInfo(BaseModel):
    id: int
    url: str
    title: str
    last_scraped: str
    pages_count: int

@app.post("/initialize", response_model=ChatResponse)
async def initialize_chatbot(request: URLRequest = Body(...)):
    """チャットボットを指定されたURLで初期化する"""
    if not request.url:
        raise HTTPException(status_code=400, detail="URLが指定されていません")
    
    # キャッシュ強制更新の場合、古いデータを削除
    if request.force_refresh and request.use_cache:
        # 実際のDBマネージャーでは特定のURLのデータを削除するメソッドを実装する必要がある
        # ここでは単純化のため、期限切れデータの削除を行う
        db_manager.delete_expired_data()
    
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
    
    # キャッシュから読み込まれたかどうかを判定
    from_cache = "キャッシュから読み込み" in message
        
    return ChatResponse(answer=message, pages_scraped=pages_scraped, from_cache=from_cache)

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

@app.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats():
    """キャッシュの統計情報を取得する"""
    stats = db_manager.get_database_stats()
    return CacheStatsResponse(**stats)

@app.post("/cache/clear")
async def clear_expired_cache():
    """期限切れのキャッシュを削除する"""
    deleted_count = db_manager.delete_expired_data()
    return {"deleted_count": deleted_count}

@app.get("/cache/urls")
async def get_cached_urls():
    """キャッシュに保存されているURLの一覧を取得する"""
    urls = db_manager.get_all_urls()
    return {"urls": urls, "count": len(urls)}

@app.get("/cache/sites", response_model=list[CachedSiteInfo])
async def get_cached_sites():
    """キャッシュに保存されているサイト情報の詳細一覧を取得する"""
    sites = db_manager.get_all_sites_info()
    return sites

@app.post("/initialize/cached/{site_id}", response_model=ChatResponse)
async def initialize_from_cached(site_id: int):
    """キャッシュされたサイトIDを使用してチャットボットを初期化する"""
    # サイトIDからURLを取得
    site_info = db_manager.get_site_info_by_id(site_id)
    
    if not site_info:
        raise HTTPException(status_code=404, detail="指定されたIDのサイトが見つかりません")
    
    url = site_info["url"]
    
    # URLを使用してチャットボットを初期化
    success, message = chatbot.initialize_with_url(url, include_subpages=True)
    
    if not success:
        raise HTTPException(status_code=500, detail=message)
    
    # 取得したページ数を取得
    pages_scraped = len(chatbot.scraper.visited_urls)
    
    return ChatResponse(
        answer=f"キャッシュされたサイト「{site_info['title']}」を読み込みました",
        pages_scraped=pages_scraped,
        from_cache=True
    )

# サーバー起動
if __name__ == "__main__":
    uvicorn.run("app:app", host=API_HOST, port=API_PORT, reload=True) 