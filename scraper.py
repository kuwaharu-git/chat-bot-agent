import requests
from bs4 import BeautifulSoup
import html2text
from config import TARGET_WEBSITE_URL
import time
import re

class WebScraper:
    def __init__(self, url=None):
        self.url = url or TARGET_WEBSITE_URL
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = True
        self.converter.body_width = 0  # 行の折り返しを無効化
        
    def fetch_content(self, url=None):
        """指定されたURLからウェブページの内容を取得する"""
        target_url = url or self.url
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(target_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"エラー: コンテンツの取得に失敗しました: {e}")
            return None
    
    def parse_html(self, html_content):
        """HTMLコンテンツをパースして必要な情報を抽出する"""
        if not html_content:
            return None
            
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # タイトルを取得
        title = soup.title.text if soup.title else "タイトルなし"
        
        # メタデータの抽出
        meta_description = ""
        meta_tag = soup.find("meta", attrs={"name": "description"})
        if meta_tag and meta_tag.get("content"):
            meta_description = meta_tag.get("content")
        
        # 不要なタグを削除
        for tag in soup.find_all(['script', 'style', 'noscript', 'iframe', 'svg']):
            tag.decompose()
        
        # メインコンテンツの抽出（複数の方法を試す）
        content_text = ""
        
        # 1. articleタグを探す
        articles = soup.find_all('article')
        if articles:
            for article in articles:
                content_text += self.converter.handle(str(article)) + "\n\n"
        
        # 2. mainタグを探す
        main_content = soup.find('main')
        if main_content:
            content_text += self.converter.handle(str(main_content)) + "\n\n"
        
        # 3. contentクラスを持つ要素を探す
        content_elements = soup.find_all(class_=re.compile('(content|main|article)'))
        if content_elements:
            for element in content_elements:
                content_text += self.converter.handle(str(element)) + "\n\n"
        
        # 4. セクションやdivを探す
        sections = soup.find_all(['section', 'div'])
        if sections and not content_text:
            for section in sections:
                # クラス名に基づいて重要なセクションを判断
                class_name = section.get('class', [])
                class_str = ' '.join(class_name).lower() if class_name else ''
                if any(keyword in class_str for keyword in ['content', 'main', 'article', 'body', 'text']):
                    content_text += self.converter.handle(str(section)) + "\n\n"
        
        # 5. ヘッダー情報を取得
        headers = soup.find_all(['h1', 'h2', 'h3'])
        header_text = ""
        for header in headers:
            header_text += header.text + "\n"
        
        # 6. リンクテキストを収集（ナビゲーションなどの情報を取得するため）
        nav = soup.find('nav')
        nav_text = ""
        if nav:
            links = nav.find_all('a')
            for link in links:
                if link.text.strip():
                    nav_text += link.text.strip() + "\n"
        
        # 十分なコンテンツが取得できなかった場合は、bodyから直接取得
        if not content_text:
            # ヘッダーとフッターを除外
            header_tag = soup.find('header')
            if header_tag:
                header_tag.extract()
                
            footer = soup.find('footer')
            if footer:
                footer.extract()
                
            nav = soup.find('nav')
            if nav:
                nav.extract()
                
            content_text = self.converter.handle(str(soup.body))
        
        # 最終的なコンテンツを組み合わせる
        final_content = ""
        if meta_description:
            final_content += f"サイト概要: {meta_description}\n\n"
        
        if header_text:
            final_content += f"主要見出し:\n{header_text}\n\n"
        
        if nav_text:
            final_content += f"ナビゲーションメニュー:\n{nav_text}\n\n"
        
        final_content += content_text
        
        # 重複する改行を削除
        final_content = re.sub(r'\n{3,}', '\n\n', final_content)
        
        return {
            "title": title,
            "content": final_content,
            "url": self.url
        }
    
    def scrape(self, url=None):
        """ウェブページをスクレイピングして情報を返す"""
        target_url = url or self.url
        self.url = target_url  # URLを更新
        html_content = self.fetch_content(target_url)
        return self.parse_html(html_content)
    
    def scrape_with_subpages(self, url=None, max_pages=3):
        """メインページとサブページをスクレイピングする"""
        target_url = url or self.url
        main_data = self.scrape(target_url)
        
        if not main_data:
            return None
        
        # メインページからリンクを抽出
        try:
            html_content = self.fetch_content(target_url)
            if html_content:
                soup = BeautifulSoup(html_content, 'html.parser')
                base_url = '/'.join(target_url.split('/')[:3])  # http(s)://domain.com
                
                # 同じドメインの内部リンクを収集
                internal_links = []
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if href.startswith('/') or target_url in href:
                        if href.startswith('/'):
                            full_url = base_url + href
                        else:
                            full_url = href
                        
                        # 画像、PDF、CSSなどのリソースは除外
                        if not any(ext in full_url for ext in ['.jpg', '.png', '.gif', '.pdf', '.css', '.js']):
                            internal_links.append(full_url)
                
                # 重複を削除
                internal_links = list(set(internal_links))
                
                # 最大ページ数まで制限
                internal_links = internal_links[:max_pages]
                
                # サブページの内容を取得
                all_content = main_data['content']
                
                for link in internal_links:
                    print(f"サブページをスクレイピング中: {link}")
                    sub_data = self.scrape(link)
                    if sub_data:
                        all_content += f"\n\n--- サブページ: {sub_data['title']} ({link}) ---\n"
                        all_content += sub_data['content']
                    
                    # 連続リクエストによるブロックを避けるため短い待機時間を設ける
                    time.sleep(1)
                
                main_data['content'] = all_content
        except Exception as e:
            print(f"サブページのスクレイピング中にエラーが発生しました: {e}")
        
        return main_data

# 使用例
if __name__ == "__main__":
    scraper = WebScraper()
    data = scraper.scrape()
    if data:
        print(f"タイトル: {data['title']}")
        print(f"コンテンツ（一部）: {data['content'][:200]}...") 