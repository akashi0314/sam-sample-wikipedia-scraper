#!/usr/bin/env python3
"""
統合版Wikipedia目次抽出プログラム
指定されたWikipediaページから目次を抽出して表示します。
robots.txt遵守とレート制限を含む。
"""

import json
import re
import time
import sys
from urllib.parse import urlparse, unquote
import requests
from bs4 import BeautifulSoup


# robots.txt遵守のためのUser-Agent設定
HEADERS = {
    'User-Agent': 'Educational-TOC-Scraper/1.0 (Contact: educational.purpose@example.com)',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ja,en-US,en;q=0.9',  # 日本語を優先
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
    
    # Extract article name and decode URL encoding
    article_name = unquote(parsed.path[6:])  # Remove '/wiki/' prefix and decode
    
    if not article_name:
        return False, "Article name is required"
    
    # Check for forbidden paths (robots.txt compliance)
    forbidden_patterns = [
        r'^Special:',           # Special pages
        r'^特別:',              # Special pages (Japanese)
        r'^User:',              # User pages
        r'^利用者:',            # User pages (Japanese)
        r'^User_talk:',         # User talk pages
        r'^利用者‐会話:',       # User talk pages (Japanese)
        r'^Wikipedia:',         # Wikipedia namespace
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
    
    for pattern in forbidden_patterns:
        if re.match(pattern, article_name, re.IGNORECASE):
            pattern_name = pattern.replace('^', '').replace(':', '')
            return False, f"Access to {pattern_name} pages is prohibited by Wikipedia's robots.txt"
    
    return True, ""


def get_heading_level_from_tag(tag):
    """
    HTMLタグから見出しレベルを取得する
    
    Args:
        tag: BeautifulSoupのタグオブジェクト
        
    Returns:
        int: 見出しレベル (1-6)
    """
    if tag.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
        return int(tag.name[1])
    return 1


def get_heading_level_from_toc_item(link):
    """
    目次アイテムから階層レベルを取得する
    
    Args:
        link: BeautifulSoupのリンク要素
        
    Returns:
        int: 階層レベル（1-6）
    """
    # 親要素を辿ってレベルを判定
    parent_li = link.find_parent('li')
    if parent_li:
        # class名からレベルを推定 (toclevel-1, toclevel-2, など)
        class_names = parent_li.get('class', [])
        for class_name in class_names:
            if class_name.startswith('toclevel-'):
                try:
                    level = int(class_name.split('-')[1])
                    return level
                except (IndexError, ValueError):
                    pass
    
    # フォールバック: ul要素のネストレベルをカウント
    current = link
    level_found = 1
    
    for i in range(5):  # 最大5階層上まで検索
        current = current.parent
        if not current:
            break
            
        if current.name == 'ul':
            # ul要素のネストレベルをカウント
            ul_count = 0
            temp = current
            while temp:
                temp = temp.find_parent('ul')
                if temp:
                    ul_count += 1
            level_found = ul_count + 1
            break
    
    return level_found


def scrape_wikipedia_toc(url, debug=False):
    """
    Wikipedia記事の目次情報を取得する（robots.txt遵守）
    
    Args:
        url (str): Wikipedia article URL
        debug (bool): デバッグ情報を出力するかどうか
        
    Returns:
        dict: TOC information or error
    """
    try:
        # レート制限：最小1秒待機
        time.sleep(MIN_REQUEST_INTERVAL)
        
        # robots.txt準拠のUser-Agentでリクエスト
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # 文字エンコーディングを適切に設定
        if response.encoding is None or response.encoding == 'ISO-8859-1':
            response.encoding = 'utf-8'
        
        # HTMLをパース
        soup = BeautifulSoup(response.content, 'lxml')
        
        # ページタイトルを取得
        title_elem = soup.find('h1', {'class': 'firstHeading'})
        if not title_elem:
            title_elem = soup.find('h1', {'id': 'firstHeading'})
        title = title_elem.get_text().strip() if title_elem else "Unknown"
        
        # 目次を取得
        toc_items = []
        
        # 標準的な目次テーブルから取得
        toc_elem = soup.find('div', {'id': 'toc'})
        
        if toc_elem:
            toc_links = toc_elem.find_all('a')
            
            for link in toc_links:
                href = link.get('href', '')
                
                if href.startswith('#'):
                    level = get_heading_level_from_toc_item(link)
                    
                    # テキスト抽出
                    text_elem = link.find('span', class_='toctext')
                    if text_elem:
                        text = text_elem.get_text(strip=True)
                    else:
                        text = link.get_text(strip=True)
                    
                    # 先頭の数字とドットを除去 (例: "1.2.3 タイトル" -> "タイトル")
                    text = re.sub(r'^\d+(\.\d+)*\s*', '', text)
                    
                    # 不要な空白を清理し、余分なスペースを除去
                    text = re.sub(r'\s+', ' ', text).strip()
                    
                    # 目次自体の項目を除外
                    if text.lower() in ['目次', 'contents', 'table of contents'] or not text:
                        continue
                    
                    # アンカーの清理
                    anchor = href[1:]  # '#'を除去
                    
                    item = {
                        "level": level,
                        "title": text,
                        "anchor": anchor,
                        "href": href
                    }
                    toc_items.append(item)
        
        # 目次が見つからない場合、見出しタグから直接取得
        if not toc_items:
            headings = soup.find_all(['h2', 'h3', 'h4', 'h5', 'h6'])
            
            for heading in headings:
                # 編集リンクを除外
                edit_links = heading.find_all('span', {'class': 'mw-editsection'})
                for edit_link in edit_links:
                    edit_link.decompose()
                
                # テキスト抽出と清理
                text = heading.get_text(strip=True)
                text = re.sub(r'\s+', ' ', text)  # 複数の空白を単一のスペースに
                
                if text and not text.startswith('[編集]') and text.lower() not in ['目次', 'contents']:
                    # IDからアンカーを生成
                    anchor_id = heading.get('id', '')
                    if not anchor_id:
                        # IDがない場合、テキストからアンカーを生成
                        anchor_id = re.sub(r'[^\w\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]', '_', text)
                    
                    level = get_heading_level_from_tag(heading)
                    
                    item = {
                        "level": level,
                        "title": text,
                        "anchor": anchor_id,
                        "href": f"#{anchor_id}"
                    }
                    toc_items.append(item)
        
        return {
            "success": True,
            "url": url,
            "title": title,
            "toc": toc_items,
            "total_items": len(toc_items)
        }
        
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout",
            "message": "Wikipedia page took too long to respond"
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


def print_toc_simple(toc_items):
    """
    目次をシンプルに表示する
    
    Args:
        toc_items (list): 目次項目のリスト
    """
    if not toc_items:
        print("目次が見つかりませんでした。")
        return
    
    print("=" * 60)
    print("目次")
    print("=" * 60)
    
    for item in toc_items:
        # インデントを階層レベルに応じて調整
        indent = "  " * (item['level'] - 1)
        title = item['title']
        print(f"{indent}• {title}")
    
    print("=" * 60)


def print_toc_detailed(toc_items):
    """
    目次を詳細表示する（レベル、アンカー付き）
    
    Args:
        toc_items (list): 目次項目のリスト
    """
    if not toc_items:
        print("目次が見つかりませんでした。")
        return
    
    print("=" * 80)
    print("目次（詳細表示）")
    print("=" * 80)
    
    for i, item in enumerate(toc_items, 1):
        indent = "  " * (item['level'] - 1)
        title = item['title']
        level = item['level']
        href = item['href']
        
        print(f"{i:2d}. {indent}[H{level}] {title}")
        print(f"     {indent}    -> {href}")
        if i < len(toc_items):
            print()
    
    print("=" * 80)


def export_to_json(result, filename=None):
    """
    結果をJSONファイルに出力する
    
    Args:
        result (dict): 抽出結果
        filename (str): 出力ファイル名
    """
    if not filename:
        # URLからファイル名を生成
        if result.get('success') and result.get('url'):
            parsed = urlparse(result['url'])
            article_name = unquote(parsed.path[6:])  # Remove '/wiki/' prefix
            filename = f"{article_name}_toc.json"
        else:
            filename = "wikipedia_toc.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"\n結果を {filename} に保存しました。")
    except Exception as e:
        print(f"\nJSONファイル保存エラー: {e}")


def main():
    """メイン関数"""
    print("Wikipedia目次抽出プログラム")
    print("=" * 50)
    
    # デフォルトURL
    default_url = "https://ja.wikipedia.org/wiki/Amazon_Web_Services"
    
    # コマンドライン引数があれば使用
    if len(sys.argv) > 1:
        url = sys.argv[1]
    else:
        # インタラクティブモード
        url = input(f"Wikipedia URL (デフォルト: AWS): ").strip()
        if not url:
            url = default_url
    
    print(f"\nURL: {url}")
    
    # URL検証
    is_valid, error_message = validate_wikipedia_url(url)
    if not is_valid:
        print(f"エラー: {error_message}")
        return
    
    print("✓ URL検証完了")
    print("目次を抽出中...")
    
    # 目次を抽出（デバッグモード有効）
    result = scrape_wikipedia_toc(url, debug=True)
    
    if not result['success']:
        print(f"エラー: {result['error']}")
        print(f"詳細: {result['message']}")
        return
    
    # 結果を表示
    print(f"\n✓ 抽出完了")
    print(f"ページタイトル: {result['title']}")
    print(f"目次項目数: {result['total_items']}")
    
    if result['toc']:
        # シンプル表示
        print_toc_simple(result['toc'])
        
        # 詳細表示オプション
        while True:
            choice = input("\n表示オプションを選択してください:\n"
                          "1. 詳細表示 (レベル・アンカー付き)\n"
                          "2. JSON出力\n"
                          "3. 終了\n"
                          "選択 (1-3): ").strip()
            
            if choice == '1':
                print_toc_detailed(result['toc'])
            elif choice == '2':
                filename = input("出力ファイル名 (空白でデフォルト): ").strip()
                if not filename:
                    filename = None
                export_to_json(result, filename)
            elif choice == '3':
                break
            else:
                print("1, 2, または3を入力してください。")
    else:
        print("目次が見つかりませんでした。")


def lambda_handler(event, context):
    """
    Lambda function to validate Wikipedia URLs and return TOC information.
    シンプルな教育用API実装
    """
    
    try:
        # HTTPメソッドのチェック
        http_method = event.get('httpMethod', 'GET')
        if http_method != 'GET':
            return {
                "statusCode": 405,
                "headers": {
                    "Content-Type": "application/json",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "success": False,
                    "error": "Method not allowed",
                    "message": "Only GET method is supported"
                })
            }
        
        # Get URL from query parameters
        query_params = event.get('queryStringParameters') or {}
        url = query_params.get('url')
        
        if not url:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "success": False,
                    "error": "URL parameter is required",
                    "message": "Please provide a Wikipedia URL using ?url=<wikipedia_url>",
                    "example": "?url=https://ja.wikipedia.org/wiki/Amazon_Web_Services"
                }, ensure_ascii=False)
            }
        
        # Validate Wikipedia URL
        is_valid, error_message = validate_wikipedia_url(url)
        
        if not is_valid:
            return {
                "statusCode": 400,
                "headers": {
                    "Content-Type": "application/json; charset=utf-8",
                    "Access-Control-Allow-Origin": "*"
                },
                "body": json.dumps({
                    "success": False,
                    "error": "Invalid Wikipedia URL",
                    "message": error_message,
                    "provided_url": url
                }, ensure_ascii=False)
            }
        
        # Scrape TOC information
        result = scrape_wikipedia_toc(url, debug=False)  # 本番環境ではデバッグ無効
        
        # ステータスコードの決定
        status_code = 200 if result["success"] else 500
        if not result["success"] and "timeout" in result.get("error", "").lower():
            status_code = 504
        
        return {
            "statusCode": status_code,
            "headers": {
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "public, max-age=300"  # 5分間キャッシュ
            },
            "body": json.dumps(result, ensure_ascii=False)
        }
        
    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json; charset=utf-8",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": False,
                "error": "Internal server error",
                "message": str(e)
            }, ensure_ascii=False)
        }