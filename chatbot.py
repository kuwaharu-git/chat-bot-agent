import google.generativeai as genai
from config import GOOGLE_API_KEY, GEMINI_MODEL_NAME
from scraper import WebScraper
import json

class GeminiChatbot:
    def __init__(self):
        # Google Gemini APIの初期化
        genai.configure(api_key=GOOGLE_API_KEY)
        
        # モデルの設定
        self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        
        # スクレイパーの初期化
        self.scraper = WebScraper()
        
        # 会話履歴
        self.chat_history = []
        
        # チャットインスタンス
        self.chat = None
        
    def initialize_with_url(self, url=None, include_subpages=True):
        """指定されたURLからコンテンツを取得してチャットボットを初期化する"""
        # ウェブサイトからコンテンツを取得
        print(f"ウェブサイト {url} からコンテンツを取得しています...")
        
        if include_subpages:
            # サブページも含めて取得
            print("サブページも含めてスクレイピングします...")
            scraped_data = self.scraper.scrape_with_subpages(url, max_pages=3)
        else:
            # メインページのみ取得
            scraped_data = self.scraper.scrape(url)
        
        if not scraped_data:
            return False
            
        # システムプロンプトを作成
        system_prompt = f"""
あなたは次のウェブページの内容に基づいて質問に答えるアシスタントです。
ウェブページのタイトル: {scraped_data['title']}
ウェブページのURL: {scraped_data['url']}

ウェブページの内容を以下に示します:
{scraped_data['content']}

このウェブページの情報のみを使用して質問に答えてください。
ウェブページに記載されていない情報については、「ウェブページにその情報は記載されていません」と答えてください。
回答は簡潔かつ正確に行ってください。
"""
        
        # 会話を初期化
        self.chat = self.model.start_chat(history=[])
        
        # システムプロンプトを送信
        print("チャットボットを初期化しています...")
        self.chat.send_message(system_prompt)
        
        # 会話履歴をクリア
        self.chat_history = []
        
        return True
    
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


# 使用例
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # .envファイルから環境変数を読み込む
    load_dotenv()
    
    chatbot = GeminiChatbot()
    
    # テスト用のURL
    url = input("解析するウェブサイトのURLを入力してください: ")
    
    print("サブページも含めてスクレイピングしますか？ (y/n): ")
    include_subpages = input().lower() == 'y'
    
    if chatbot.initialize_with_url(url, include_subpages):
        print("チャットボットの準備ができました。質問を入力してください（終了するには 'exit' と入力）")
        
        while True:
            question = input("\nあなた: ")
            
            if question.lower() == 'exit':
                break
                
            answer = chatbot.ask(question)
            print(f"\nチャットボット: {answer}") 