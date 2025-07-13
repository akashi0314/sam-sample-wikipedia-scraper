import pytest
import requests
import os

def test_wikipedia_toc_api_basic():
    """Wikipedia TOC API Gatewayエンドポイントの基本テスト"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    print(f"Testing Wikipedia TOC API: {api_url}")
    
    # Valid Wikipedia URL for testing
    test_url = "https://ja.wikipedia.org/wiki/Amazon_Web_Services"
    response = requests.get(f"{api_url}?url={test_url}", timeout=15)
    assert response.status_code == 200
    
    # JSONレスポンスの検証
    json_response = response.json()
    assert 'success' in json_response
    assert json_response['success'] is True
    assert 'toc' in json_response
    assert 'title' in json_response
    assert 'total_items' in json_response
    print(f"Response: {json_response}")

def test_wikipedia_toc_api_response_format():
    """Wikipedia TOC APIレスポンス形式の検証"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    # Valid Wikipedia URL for testing
    test_url = "https://ja.wikipedia.org/wiki/Amazon_Web_Services"
    response = requests.get(f"{api_url}?url={test_url}", timeout=15)
    assert response.status_code == 200
    
    # Content-Typeがjsonであることを確認
    content_type = response.headers.get('content-type', '')
    assert 'application/json' in content_type.lower()
    
    # Wikipedia TOC specific response structure validation
    json_response = response.json()
    assert 'success' in json_response
    assert 'url' in json_response
    if json_response['success']:
        assert 'toc' in json_response
        assert 'title' in json_response
        assert 'total_items' in json_response
        assert isinstance(json_response['toc'], list)
        # TOCアイテムの構造を確認
        if json_response['toc']:
            toc_item = json_response['toc'][0]
            assert 'level' in toc_item
            assert 'title' in toc_item
            assert 'anchor' in toc_item

def test_wikipedia_toc_api_invalid_url():
    """無効なURLでのテスト"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    test_url = "https://example.com/test"
    response = requests.get(f"{api_url}?url={test_url}", timeout=10)
    assert response.status_code == 400
    
    json_response = response.json()
    assert 'success' in json_response
    assert json_response['success'] is False
    assert 'error' in json_response

def test_wikipedia_toc_api_no_url():
    """URLパラメータなしのテスト"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    response = requests.get(api_url, timeout=10)
    assert response.status_code == 400
    
    json_response = response.json()
    assert 'success' in json_response
    assert json_response['success'] is False
    assert 'error' in json_response

def test_wikipedia_toc_api_forbidden_namespace():
    """禁止されたWikipediaネームスペースでのテスト"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    # 禁止されたネームスペース（ユーザーページ）
    test_url = "https://ja.wikipedia.org/wiki/利用者:TestUser"
    response = requests.get(f"{api_url}?url={test_url}", timeout=10)
    assert response.status_code == 400
    
    json_response = response.json()
    assert 'success' in json_response
    assert json_response['success'] is False
    assert 'error' in json_response
    # 実際のエラーメッセージに基づいて調整
    error_msg = json_response['error'].lower()
    assert any(keyword in error_msg for keyword in ['wikipedia', 'url', 'invalid', 'not allowed', 'forbidden'])

def test_wikipedia_toc_api_multilingual():
    """多言語Wikipedia記事でのテスト"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    # 英語Wikipedia記事
    test_url = "https://en.wikipedia.org/wiki/Python_(programming_language)"
    response = requests.get(f"{api_url}?url={test_url}", timeout=15)
    assert response.status_code == 200
    
    json_response = response.json()
    assert json_response['success'] is True
    assert 'toc' in json_response
    assert 'title' in json_response
    print(f"English article title: {json_response.get('title', 'N/A')}")
