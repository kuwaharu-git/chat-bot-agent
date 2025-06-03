import requests
from bs4 import BeautifulSoup
import html2text
from config import TARGET_WEBSITE_URL
import time
import re
from urllib.parse import urljoin, urlparse
from db_manager import DBManager
import urllib.robotparser

class WebScraper:
    def __init__(self, url=None, use_cache=True, cache_expire_days=7, respect_robots_txt=True):
        self.url = url or TARGET_WEBSITE_URL
        self.converter = html2text.HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = True
        self.converter.body_width = 0  # 行の折り返しを無効化
        self.visited_urls = set()  # 訪問済みURLを記録
        
        # キャッシュ設定
        self.use_cache = use_cache
        self.cache_expire_days = cache_expire_days
        self.db_manager = DBManager() if use_cache else None
        
        # robots.txt設定
        self.respect_robots_txt = respect_robots_txt
        self.rp = urllib.robotparser.RobotFileParser()
        self.robots_cache = {}  # ドメインごとのrobots.txtキャッシュ
        self.user_agent = 'Mozilla/5.0 (compatible; ChatBotAgent/1.0)'
        
    def check_robots_txt(self, url):
        """robots.txtをチェックして、URLへのアクセスが許可されているかを確認する"""
        if not self.respect_robots_txt:
            return True
            
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # 同じドメインのrobots.txtを既に確認済みの場合はキャッシュを使用
        if domain in self.robots_cache:
            return self.robots_cache[domain].can_fetch(self.user_agent, url)
            
        # robots.txtのURLを構築
        robots_url = f"{parsed_url.scheme}://{domain}/robots.txt"
        
        try:
            # robots.txtを取得して解析
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(robots_url)
            rp.read()
            
            # キャッシュに保存
            self.robots_cache[domain] = rp
            
            # アクセスが許可されているかチェック
            allowed = rp.can_fetch(self.user_agent, url)
            if not allowed:
                print(f"robots.txtによりアクセスが禁止されています: {url}")
            return allowed
            
        except Exception as e:
            print(f"robots.txtの確認中にエラーが発生しました: {e}")
            # エラーが発生した場合は許可されていると仮定
            return True
        
    def fetch_content(self, url=None):
        """指定されたURLからウェブページの内容を取得する"""
        target_url = url or self.url
        
        # robots.txtをチェック
        if not self.check_robots_txt(target_url):
            print(f"robots.txtによりアクセスが禁止されているため、コンテンツを取得しません: {target_url}")
            return None
        
        try:
            headers = {
                'User-Agent': self.user_agent
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
    
    def is_valid_url(self, url, base_url):
        """URLが有効かどうかを判断する"""
        # 完全なURLに変換
        full_url = urljoin(base_url, url)
        
        # URLのパース
        parsed = urlparse(full_url)
        
        # 同じドメインかどうか確認
        base_domain = urlparse(base_url).netloc
        url_domain = parsed.netloc
        
        # 画像、PDF、CSSなどのリソースは除外
        excluded_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.css', '.js', '.ico', '.svg', '.xml', '.json']
        
        # 条件チェック
        is_same_domain = url_domain == base_domain
        is_not_resource = not any(full_url.lower().endswith(ext) for ext in excluded_extensions)
        is_not_anchor = not (parsed.path == '' and parsed.fragment != '')
        is_not_mailto = not full_url.startswith('mailto:')
        is_not_tel = not full_url.startswith('tel:')
        
        return is_same_domain and is_not_resource and is_not_anchor and is_not_mailto and is_not_tel
    
    def scrape(self, url=None):
        """ウェブページをスクレイピングして情報を返す"""
        target_url = url or self.url
        self.url = target_url  # URLを更新
        
        # キャッシュを使用する場合、キャッシュをチェック
        if self.use_cache and self.db_manager:
            cached_data = self.db_manager.get_scraped_data(target_url)
            if cached_data:
                print(f"キャッシュからデータを読み込みました: {target_url}")
                return {
                    "title": cached_data["title"],
                    "content": cached_data["content"],
                    "url": cached_data["url"]
                }
        
        # robots.txtをチェック
        if not self.check_robots_txt(target_url):
            print(f"robots.txtによりアクセスが禁止されています: {target_url}")
            return None
        
        # キャッシュにない場合は新たに取得
        html_content = self.fetch_content(target_url)
        return self.parse_html(html_content)
    
    def extract_links(self, html_content, base_url):
        """HTMLからリンクを抽出する"""
        if not html_content:
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        # aタグからリンクを抽出
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            if self.is_valid_url(href, base_url):
                full_url = urljoin(base_url, href)
                # robots.txtをチェック
                if self.respect_robots_txt and not self.check_robots_txt(full_url):
                    continue
                links.append(full_url)
        
        # 重複を削除
        return list(set(links))
    
    def scrape_with_subpages(self, url=None, max_pages=10, max_depth=2):
        """メインページとサブページをスクレイピングする"""
        target_url = url or self.url
        
        # キャッシュを使用する場合、キャッシュをチェック
        if self.use_cache and self.db_manager:
            cached_data = self.db_manager.get_scraped_data(target_url)
            if cached_data:
                print(f"キャッシュからデータを読み込みました: {target_url} ({cached_data['pages_count']}ページ)")
                self.visited_urls = set(cached_data["visited_urls"])
                return {
                    "title": cached_data["title"],
                    "content": cached_data["content"],
                    "url": cached_data["url"]
                }
        
        # robots.txtをチェック
        if not self.check_robots_txt(target_url):
            print(f"robots.txtによりアクセスが禁止されています: {target_url}")
            return None
        
        # キャッシュにない場合は新たに取得
        self.visited_urls = set()  # 訪問済みURLをリセット
        
        print(f"メインページをスクレイピング: {target_url}")
        main_data = self.scrape(target_url)
        self.visited_urls.add(target_url)
        
        if not main_data:
            return None
        
        all_content = main_data['content']
        
        # 幅優先探索でサブページを探索
        queue = [(target_url, 0)]  # (URL, 深さ)
        index = 0
        
        while index < len(queue) and len(self.visited_urls) < max_pages:
            current_url, depth = queue[index]
            index += 1
            
            # 最大深さに達したら探索を停止
            if depth >= max_depth:
                continue
            
            # 現在のページからリンクを抽出
            if current_url not in self.visited_urls:
                continue
                
            html_content = self.fetch_content(current_url)
            if not html_content:
                continue
                
            links = self.extract_links(html_content, current_url)
            
            # 各リンクを処理
            for link in links:
                # 既に訪問済みならスキップ
                if link in self.visited_urls:
                    continue
                    
                # 最大ページ数に達したら終了
                if len(self.visited_urls) >= max_pages:
                    break
                
                # robots.txtをチェック
                if not self.check_robots_txt(link):
                    continue
                
                print(f"サブページをスクレイピング中 ({len(self.visited_urls)}/{max_pages}): {link}")
                sub_data = self.scrape(link)
                self.visited_urls.add(link)
                
                if sub_data:
                    all_content += f"\n\n--- サブページ: {sub_data['title']} ({link}) ---\n"
                    all_content += sub_data['content']
                
                # 次の深さのリンクをキューに追加
                queue.append((link, depth + 1))
                
                # 連続リクエストによるブロックを避けるため短い待機時間を設ける
                time.sleep(0.5)
        
        main_data['content'] = all_content
        print(f"合計 {len(self.visited_urls)} ページをスクレイピングしました")
        
        # キャッシュに保存
        if self.use_cache and self.db_manager:
            self.db_manager.save_scraped_data(
                target_url,
                main_data['title'],
                main_data['content'],
                list(self.visited_urls),
                self.cache_expire_days
            )
            print(f"データをキャッシュに保存しました: {target_url}")
        
        return main_data

# 使用例
if __name__ == "__main__":
    scraper = WebScraper(use_cache=True, respect_robots_txt=True)
    url = input("スクレイピングするURLを入力してください: ")
    data = scraper.scrape_with_subpages(url, max_pages=10, max_depth=2)
    if data:
        print(f"タイトル: {data['title']}")
        print(f"取得したページ数: {len(scraper.visited_urls)}")
        print(f"コンテンツ（一部）: {data['content'][:200]}...") 