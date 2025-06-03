import sqlite3
import json
import os
import time
from datetime import datetime, timedelta

class DBManager:
    def __init__(self, db_path="scraping_data.db"):
        """DBManagerの初期化"""
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """データベースの初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # スクレイピングデータを保存するテーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS scraped_sites (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE,
            title TEXT,
            content TEXT,
            pages_count INTEGER,
            last_scraped TIMESTAMP,
            expire_time TIMESTAMP
        )
        ''')
        
        # 訪問済みURLを保存するテーブル
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS visited_urls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            site_id INTEGER,
            url TEXT,
            FOREIGN KEY (site_id) REFERENCES scraped_sites(id) ON DELETE CASCADE,
            UNIQUE(site_id, url)
        )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_scraped_data(self, url, title, content, visited_urls, expire_days=7):
        """スクレイピングしたデータを保存する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now()
        expire_time = now + timedelta(days=expire_days)
        
        try:
            # メインのスクレイピングデータを保存
            cursor.execute('''
            INSERT OR REPLACE INTO scraped_sites 
            (url, title, content, pages_count, last_scraped, expire_time) 
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (url, title, content, len(visited_urls), now, expire_time))
            
            site_id = cursor.lastrowid
            
            # 既存の訪問済みURLを削除
            cursor.execute('DELETE FROM visited_urls WHERE site_id = ?', (site_id,))
            
            # 訪問済みURLを保存
            for visited_url in visited_urls:
                cursor.execute('''
                INSERT INTO visited_urls (site_id, url) VALUES (?, ?)
                ''', (site_id, visited_url))
            
            conn.commit()
            return True
            
        except Exception as e:
            print(f"データベース保存エラー: {e}")
            conn.rollback()
            return False
            
        finally:
            conn.close()
    
    def get_scraped_data(self, url):
        """URLに対応するスクレイピングデータを取得する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # メインのスクレイピングデータを取得
            cursor.execute('''
            SELECT id, title, content, pages_count, last_scraped, expire_time 
            FROM scraped_sites 
            WHERE url = ?
            ''', (url,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
                
            site_id, title, content, pages_count, last_scraped, expire_time = result
            
            # 有効期限をチェック
            if datetime.now() > datetime.fromisoformat(expire_time):
                print(f"データの有効期限が切れています: {url}")
                return None
            
            # 訪問済みURLを取得
            cursor.execute('SELECT url FROM visited_urls WHERE site_id = ?', (site_id,))
            visited_urls = [row[0] for row in cursor.fetchall()]
            
            return {
                "url": url,
                "title": title,
                "content": content,
                "pages_count": pages_count,
                "last_scraped": last_scraped,
                "visited_urls": visited_urls
            }
            
        except Exception as e:
            print(f"データベース取得エラー: {e}")
            return None
            
        finally:
            conn.close()
    
    def is_data_fresh(self, url, max_age_days=7):
        """URLに対応するデータが新鮮かどうかを確認する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT last_scraped FROM scraped_sites WHERE url = ?
            ''', (url,))
            
            result = cursor.fetchone()
            
            if not result:
                return False
                
            last_scraped = datetime.fromisoformat(result[0])
            max_age = timedelta(days=max_age_days)
            
            return datetime.now() - last_scraped < max_age
            
        except Exception as e:
            print(f"データベースチェックエラー: {e}")
            return False
            
        finally:
            conn.close()
    
    def delete_expired_data(self):
        """有効期限が切れたデータを削除する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            now = datetime.now()
            
            # 有効期限切れのサイトIDを取得
            cursor.execute('''
            SELECT id FROM scraped_sites WHERE expire_time < ?
            ''', (now,))
            
            expired_ids = [row[0] for row in cursor.fetchall()]
            
            # 有効期限切れのサイトを削除
            cursor.execute('''
            DELETE FROM scraped_sites WHERE expire_time < ?
            ''', (now,))
            
            deleted_count = cursor.rowcount
            
            conn.commit()
            return deleted_count
            
        except Exception as e:
            print(f"期限切れデータ削除エラー: {e}")
            conn.rollback()
            return 0
            
        finally:
            conn.close()
    
    def get_all_urls(self):
        """保存されているすべてのURLを取得する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT url FROM scraped_sites')
            urls = [row[0] for row in cursor.fetchall()]
            return urls
            
        except Exception as e:
            print(f"URL取得エラー: {e}")
            return []
            
        finally:
            conn.close()
            
    def get_database_stats(self):
        """データベースの統計情報を取得する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # サイト数を取得
            cursor.execute('SELECT COUNT(*) FROM scraped_sites')
            sites_count = cursor.fetchone()[0]
            
            # 訪問済みURL数を取得
            cursor.execute('SELECT COUNT(*) FROM visited_urls')
            urls_count = cursor.fetchone()[0]
            
            # 最新のスクレイピング日時を取得
            cursor.execute('SELECT MAX(last_scraped) FROM scraped_sites')
            last_scraped = cursor.fetchone()[0]
            
            # DBファイルサイズを取得
            db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
            
            return {
                "sites_count": sites_count,
                "urls_count": urls_count,
                "last_scraped": last_scraped,
                "db_size_kb": db_size / 1024
            }
            
        except Exception as e:
            print(f"統計情報取得エラー: {e}")
            return {
                "sites_count": 0,
                "urls_count": 0,
                "last_scraped": None,
                "db_size_kb": 0
            }
            
        finally:
            conn.close()
            
    def get_all_sites_info(self):
        """保存されているすべてのサイト情報を取得する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT id, url, title, pages_count, last_scraped 
            FROM scraped_sites
            WHERE datetime('now') < expire_time
            ORDER BY last_scraped DESC
            ''')
            
            sites = []
            for row in cursor.fetchall():
                site_id, url, title, pages_count, last_scraped = row
                sites.append({
                    "id": site_id,
                    "url": url,
                    "title": title,
                    "pages_count": pages_count,
                    "last_scraped": last_scraped
                })
                
            return sites
            
        except Exception as e:
            print(f"サイト情報取得エラー: {e}")
            return []
            
        finally:
            conn.close()
            
    def get_site_info_by_id(self, site_id):
        """サイトIDからサイト情報を取得する"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
            SELECT id, url, title, pages_count, last_scraped 
            FROM scraped_sites 
            WHERE id = ? AND datetime('now') < expire_time
            ''', (site_id,))
            
            result = cursor.fetchone()
            
            if not result:
                return None
                
            site_id, url, title, pages_count, last_scraped = result
            
            return {
                "id": site_id,
                "url": url,
                "title": title,
                "pages_count": pages_count,
                "last_scraped": last_scraped
            }
            
        except Exception as e:
            print(f"サイト情報取得エラー: {e}")
            return None
            
        finally:
            conn.close()

# 使用例
if __name__ == "__main__":
    db = DBManager()
    
    # データベースの統計情報を表示
    stats = db.get_database_stats()
    print(f"データベース統計:")
    print(f"保存サイト数: {stats['sites_count']}")
    print(f"訪問済みURL数: {stats['urls_count']}")
    print(f"最終スクレイピング: {stats['last_scraped']}")
    print(f"DBサイズ: {stats['db_size_kb']:.2f} KB")
    
    # 期限切れデータを削除
    deleted = db.delete_expired_data()
    print(f"{deleted}件の期限切れデータを削除しました")