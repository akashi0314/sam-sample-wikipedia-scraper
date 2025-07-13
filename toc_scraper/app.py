import json
import re
import time
from urllib.parse import urlparse, parse_qs
import requests
from bs4 import BeautifulSoup

# robots.txt遵守のためのUser-Agent設定
HEADERS = {
    'User-Agent': 'Educational-TOC-Scraper/1.0 (Contact: educational.purpose@example.com)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive'
}

# レート制限のための最小待機時間（秒）
MIN_REQUEST_INTERVAL = 1.0

def validate_wikipedia_url(url):
    """
    Validate if the URL is a valid Wikipedia article URL and complies with robots.txt.
    
    Args:
        url (str): URL to validate
        
    Returns:
        tuple: (is_valid: bool, error_message: str)
    """
    if not url:
        return False, "URL is required"
    
    # Strip whitespace
    url = url.strip()
    if not url:
        return False, "URL is required"
    
    try:
        parsed = urlparse(url)
    except Exception:
        return False, "Invalid URL format"
    
    # Check if URL uses HTTPS
    if parsed.scheme != 'https':
        return False, "URL must use HTTPS"
    
    # Check if domain is Wikipedia
    if not parsed.netloc.endswith('.wikipedia.org'):
        return False, "URL must be from Wikipedia (*.wikipedia.org)"
    
    # Check for mobile or commons subdomains
    if parsed.netloc.startswith('m.') or parsed.netloc.startswith('commons.'):
        return False, "Mobile and Commons Wikipedia URLs are not supported"
    
    # robots.txt禁止パスの詳細チェック
    if not parsed.path.startswith('/wiki/'):
        return False, "URL must be a Wikipedia article (/wiki/article_name)"
    
    # /w/ パスは robots.txt で禁止されている
    if parsed.path.startswith('/w/'):
        return False, "Access to /w/ paths is prohibited by robots.txt"
    
    # /api/ パスも禁止
    if parsed.path.startswith('/api/'):
        return False, "Access to /api/ paths is prohibited by robots.txt"
    
    # /trap/ パスも禁止
    if parsed.path.startswith('/trap/'):
        return False, "Access to /trap/ paths is prohibited by robots.txt"
    
    # Extract article name
    article_name = parsed.path[6:]  # Remove '/wiki/' prefix
    
    if not article_name:
        return False, "Article name is required"
    
    # Check for forbidden paths (robots.txt compliance)
    # 基本的な禁止パターン
    basic_forbidden_patterns = [
        r'^Special:',           # Special pages - robots.txt明示的禁止
        r'^Spezial:',          # Special pages (German)
        r'^Spesial:',          # Special pages (Norwegian)
        r'^Special%3A',        # URL encoded Special:
        r'^Spezial%3A',        # URL encoded Spezial:
        r'^Spesial%3A',        # URL encoded Spesial:
        r'^特別:',              # Special pages (Japanese)
        r'^%E7%89%B9%E5%88%A5:', # URL encoded 特別:
        r'^%E7%89%B9%E5%88%A5%3A:', # URL encoded 特別%3A:
    ]
    
    # 利用者/ユーザーページ関連
    user_forbidden_patterns = [
        r'^User:',              # User pages (English)  
        r'^User%3A',            # URL encoded User:
        r'^User_talk:',         # User talk pages (English)
        r'^User_talk%3A',       # URL encoded User_talk:
        r'^利用者:',            # User pages (Japanese)
        r'^%E5%88%A9%E7%94%A8%E8%80%85:', # URL encoded 利用者:
        r'^%E5%88%A9%E7%94%A8%E8%80%85%3A', # URL encoded 利用者%3A
        r'^利用者‐会話:',       # User talk pages (Japanese)
        r'^%E5%88%A9%E7%94%A8%E8%80%85%E2%80%90%E4%BC%9A%E8%A9%B1:', # URL encoded
        r'^%E5%88%A9%E7%94%A8%E8%80%85%E2%80%90%E4%BC%9A%E8%A9%B1%3A', # URL encoded
    ]
    
    # Wikipedia名前空間とショートカット
    wikipedia_namespace_patterns = [
        r'^Wikipedia:',         # Wikipedia namespace
        r'^Wikipedia%3A',       # URL encoded Wikipedia:
        r'^WP:',               # Wikipedia shortcut (Japanese)
        r'^WP%3A',             # URL encoded WP:
        r'^ノート:WP',          # Wikipedia talk shortcut
        r'^%E3%83%8E%E3%83%BC%E3%83%88:WP:', # URL encoded
        r'^%E3%83%8E%E3%83%BC%E3%83%88%3AWP%3A', # URL encoded
        r'^LTA:',              # Long Term Abuse
        r'^LTA%3A',            # URL encoded LTA:
    ]
    
    # 削除依頼関連（日本語Wikipedia特有）
    deletion_patterns = [
        r'^削除依頼',           # 削除依頼 shortcut
        r'^%E5%89%8A%E9%99%A4%E4%BE%9D%E9%A0%BC', # URL encoded
        r'^削除の復帰依頼',      # 削除の復帰依頼 shortcut
        r'^%E5%89%8A%E9%99%A4%E3%81%AE%E5%BE%A9%E5%B8%B0%E4%BE%9D%E9%A0%BC', # URL encoded
        r'^復帰依頼',           # 復帰依頼 shortcut
        r'^%E5%BE%A9%E5%B8%B0%E4%BE%9D%E9%A0%BC', # URL encoded
        r'^ブロック依頼',        # ブロック依頼 shortcut
        r'^%E3%83%96%E3%83%AD%E3%83%83%E3%82%AF%E4%BE%9D%E9%A0%BC', # URL encoded
        r'^投稿ブロック依頼',     # 投稿ブロック依頼 shortcut
        r'^%E6%8A%95%E7%A8%BF%E3%83%96%E3%83%AD%E3%83%83%E3%82%AF%E4%BE%9D%E9%A0%BC', # URL encoded
        r'^管理者伝言板',        # 管理者伝言板 shortcut
        r'^%E7%AE%A1%E7%90%86%E8%80%85%E4%BC%9D%E8%A8%80%E6%9D%BF', # URL encoded
    ]
    
    # その他の禁止パターン
    other_forbidden_patterns = [
        r'^ノート:',            # Talk pages (Japanese)
        r'^Talk:',              # Talk pages (English)
        r'^ファイル:',          # File pages (Japanese)
        r'^File:',              # File pages (English)
        r'^Media:',             # Media pages
        r'^カテゴリ:',          # Category pages (Japanese)
        r'^Category:',          # Category pages (English)
        r'^Template:',          # Template pages
        r'^Help:',              # Help pages
        r'^Portal:',            # Portal pages
        r'^Draft:',             # Draft pages
        r'^Book:',              # Book pages
        r'^Module:',            # Module pages
        r'^MediaWiki:',         # MediaWiki namespace
        r'^Project:',           # Project pages
    ]
    
    # 全ての禁止パターンを統合
    all_forbidden_patterns = (
        basic_forbidden_patterns + 
        user_forbidden_patterns + 
        wikipedia_namespace_patterns + 
        deletion_patterns + 
        other_forbidden_patterns
    )
    
    for pattern in all_forbidden_patterns:
        if re.match(pattern, article_name, re.IGNORECASE):
            pattern_name = pattern.replace('^', '').replace(':', '').replace('%3A', '').replace('%E', '').replace('%', '')
            return False, f"Access to {pattern_name} pages is prohibited by Wikipedia's robots.txt"
    
    return True, ""

def scrape_wikipedia_toc(url):
    """
    Wikipedia記事の目次情報を取得する（robots.txt遵守）
    
    Args:
        url (str): Wikipedia article URL
        
    Returns:
        dict: TOC information or error
    """
    try:
        # レート制限：最小1秒待機
        time.sleep(MIN_REQUEST_INTERVAL)
        
        # robots.txt準拠のUser-Agentでリクエスト
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        
        # HTMLをパース
        soup = BeautifulSoup(response.content, 'lxml')
        
        # ページタイトルを取得
        title_elem = soup.find('h1', {'class': 'firstHeading'})
        title = title_elem.get_text().strip() if title_elem else "Unknown"
        
        # 目次要素を取得
        toc_elem = soup.find('div', {'id': 'toc'})
        if not toc_elem:
            return {
                "success": True,
                "url": url,
                "title": title,
                "toc": [],
                "message": "No table of contents found on this page"
            }
        
        # 目次項目を解析
        toc_items = []
        toc_links = toc_elem.find_all('a')
        
        for link in toc_links:
            href = link.get('href', '')
            if href.startswith('#'):
                # レベルを親要素から判定
                parent_li = link.find_parent('li')
                if parent_li:
                    # class名からレベルを推定 (toclevel-1, toclevel-2, など)
                    class_names = parent_li.get('class', [])
                    level = 1
                    for class_name in class_names:
                        if class_name.startswith('toclevel-'):
                            try:
                                level = int(class_name.split('-')[1])
                            except (IndexError, ValueError):
                                level = 1
                            break
                    
                    toc_items.append({
                        "level": level,
                        "title": link.get_text().strip(),
                        "anchor": href[1:],  # '#'を除去
                        "href": href
                    })
        
        return {
            "success": True,
            "url": url,
            "title": title,
            "toc": toc_items,
            "total_items": len(toc_items)
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": "Failed to fetch Wikipedia page",
            "message": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Failed to parse Wikipedia content",
            "message": str(e)
        }

def lambda_handler(event, context):
    """
    Lambda function to validate Wikipedia URLs and return TOC information.
    robots.txt遵守を重視した実装
    """
    
    try:
        # Get URL from query parameters
        query_params = event.get('queryStringParameters') or {}
        url = query_params.get('url')
        
        if not url:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "success": False,
                    "error": "URL parameter is required",
                    "message": "Please provide a Wikipedia URL using ?url=<wikipedia_url>",
                    "robots_compliance": "This service respects Wikipedia's robots.txt"
                })
            }
        
        # Validate Wikipedia URL (robots.txt compliance check)
        is_valid, error_message = validate_wikipedia_url(url)
        
        if not is_valid:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "success": False,
                    "error": "Invalid Wikipedia URL or robots.txt violation",
                    "message": error_message,
                    "provided_url": url,
                    "robots_compliance": "This service respects Wikipedia's robots.txt"
                })
            }
        
        # Scrape TOC information
        result = scrape_wikipedia_toc(url)
        
        return {
            "statusCode": 200 if result["success"] else 400,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                **result,
                "robots_compliance": "This service respects Wikipedia's robots.txt",
                "user_agent": HEADERS['User-Agent']
            })
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": "Internal server error",
                "message": str(e),
                "robots_compliance": "This service respects Wikipedia's robots.txt"
            })
        }
