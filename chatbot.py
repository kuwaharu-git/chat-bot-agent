import google.generativeai as genai
from config import GOOGLE_API_KEY, GEMINI_MODEL_NAME
from scraper import WebScraper
import json

class GeminiChatbot:
    def __init__(self, use_cache=True, cache_expire_days=7):
        # Google Gemini APIの初期化
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # モデルの設定
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        # スクレイパーの初期化（キャッシュ設定を渡す）
        self.scraper = WebScraper(use_cache=use_cache, cache_expire_days=cache_expire_days)
        
        # 会話履歴
        self.chat_history = []
        
        # チャットインスタンス
        self.chat = None
        
        # キャッシュ設定
        self.use_cache = use_cache
        self.cache_expire_days = cache_expire_days
        
    def initialize_with_url(self, url, include_subpages=True, max_pages=10, max_depth=2):
        """指定したURLでスクレイパーを初期化する"""
        try:
            # スクレイパーの初期化
            self.scraper = WebScraper(url=url, use_cache=self.use_cache, cache_expire_days=7, respect_robots_txt=True)
            
            # URLが有効かどうかを確認
            if not url.startswith(('http://', 'https://')):
                return False, "エラー: 有効なURLを入力してください（http://またはhttps://で始まるURL）"
            
            # ウェブサイトからコンテンツを取得
            print(f"ウェブサイト {url} からコンテンツを取得しています...")
            
            if include_subpages:
                # サブページも含めて取得
                print(f"サブページも含めてスクレイピングします（最大{max_pages}ページ、深さ{max_depth}まで）...")
                scraped_data = self.scraper.scrape_with_subpages(url, max_pages=max_pages, max_depth=max_depth)
                pages_count = len(self.scraper.visited_urls)
                print(f"合計 {pages_count} ページの情報を取得しました。")
            else:
                # メインページのみ取得
                scraped_data = self.scraper.scrape(url)
                pages_count = 1
            
            if not scraped_data:
                return False, "ウェブサイトからの情報取得に失敗しました。"
            
            # システムプロンプトを作成
            system_prompt = f"""
あなたは次のウェブページの内容に基づいて質問に答えるアシスタントです。
ウェブページのタイトル: {scraped_data['title']}
ウェブページのURL: {scraped_data['url']}
取得したページ数: {pages_count}

ウェブページの内容を以下に示します:
{scraped_data['content']}

このウェブページの情報のみを使用して質問に答えてください。
ウェブページに記載されていない情報については、「ウェブページにその情報は記載されていません」と答えてください。
回答は簡潔かつ正確に行ってください。

回答はマークダウン形式で提供してください。以下のマークダウン記法を活用してください：
- 見出しには `#`, `##`, `###` などを使用
- 箇条書きには `-` または `*` を使用
- 強調には `**太字**` や `*斜体*` を使用
- コードブロックには ``` で囲む
- 表が必要な場合はマークダウンの表記法を使用
- 引用には `>` を使用

回答は構造化し、読みやすく整形してください。
"""
            
            # 会話を初期化
            self.chat = self.model.start_chat(history=[])
            
            # システムプロンプトを送信
            print("チャットボットを初期化しています...")
            self.chat.send_message(system_prompt)
            
            # 会話履歴をクリア
            self.chat_history = []
            
            # キャッシュ情報を表示
            cache_status = "キャッシュから読み込み" if self.use_cache and any(url in str(self.scraper.visited_urls) for url in self.scraper.visited_urls) else "新規取得"
            
            return True, f"{pages_count}ページの情報を取得しました（{cache_status}）。チャットボットの準備ができました。"
        except Exception as e:
            return False, f"エラーが発生しました: {str(e)}"
    
    def ask(self, question):
        """質問を受け取り、回答を返す"""
        if not self.chat:
            return "チャットボットがまだ初期化されていません。URLを指定してください。"
            
        try:
            # 質問を送信して回答を取得
            response = self.chat.send_message(question)
            
            # 会話履歴に追加
            self.chat_history.append({"role": "user", "content": question})
            self.chat_history.append({"role": "assistant", "content": response.text})
            
            return response.text
        except Exception as e:
            return f"エラーが発生しました: {str(e)}"
    
    def get_chat_history(self):
        """会話履歴を取得する"""
        return self.chat_history
        
    def get_cache_stats(self):
        """キャッシュの統計情報を取得する"""
        if not self.use_cache:
            return {"enabled": False}
            
        if hasattr(self.scraper, "db_manager") and self.scraper.db_manager:
            stats = self.scraper.db_manager.get_database_stats()
            stats["enabled"] = True
            return stats
            
        return {"enabled": True, "error": "統計情報を取得できません"}


# 使用例
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # .envファイルから環境変数を読み込む
    load_dotenv()
    
    # キャッシュを使用するかどうか
    print("キャッシュを使用しますか？ (y/n): ")
    use_cache = input().lower() == 'y'
    
    chatbot = GeminiChatbot(use_cache=use_cache)
    
    if use_cache:
        # キャッシュの統計情報を表示
        stats = chatbot.get_cache_stats()
        if stats["sites_count"] > 0:
            print(f"キャッシュ統計: {stats['sites_count']}サイト, {stats['urls_count']}URL")
    
    # テスト用のURL
    url = input("解析するウェブサイトのURLを入力してください: ")
    
    print("サブページも含めてスクレイピングしますか？ (y/n): ")
    include_subpages = input().lower() == 'y'
    
    max_pages = 10
    max_depth = 2
    
    if include_subpages:
        print("取得する最大ページ数を入力してください（デフォルト: 10）: ")
        max_pages_input = input()
        if max_pages_input.isdigit():
            max_pages = int(max_pages_input)
            
        print("探索する最大深さを入力してください（デフォルト: 2）: ")
        max_depth_input = input()
        if max_depth_input.isdigit():
            max_depth = int(max_depth_input)
    
    success, message = chatbot.initialize_with_url(url, include_subpages, max_pages, max_depth)
    
    if success:
        print(message)
        print("質問を入力してください（終了するには 'exit' と入力）")
        
        while True:
            question = input("\nあなた: ")
            
            if question.lower() == 'exit':
                break
                
            answer = chatbot.ask(question)
            print(f"\nチャットボット: {answer}") 