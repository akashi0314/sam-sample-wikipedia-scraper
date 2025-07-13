import pytest
import requests
import os

def test_hello_world_api_basic():
    """HelloWorld API の基本テスト（互換性）"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    print(f"Testing HelloWorld API: {api_url}")
    response = requests.get(api_url, timeout=10)
    assert response.status_code == 200
    
    json_response = response.json()
    # HelloWorld APIは単純な 'message' を返す
    assert 'message' in json_response
    assert json_response['message'] == 'hello world'
    print(f"HelloWorld Response: {json_response}")

def test_hello_world_api_response_format():
    """HelloWorld APIレスポンス形式の検証"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    response = requests.get(api_url, timeout=10)
    assert response.status_code == 200
    
    # Content-Typeがjsonであることを確認
    content_type = response.headers.get('content-type', '')
    assert 'application/json' in content_type.lower()
    
    # HelloWorld specific response structure validation
    json_response = response.json()
    assert isinstance(json_response, dict)
    assert 'message' in json_response

def test_hello_world_api_with_parameters():
    """HelloWorld API パラメータ付きテスト（互換性）"""
    api_url = os.environ.get('API_URL', '')
    if not api_url:
        pytest.skip("API_URL環境変数が設定されていません")
    
    # HelloWorld APIは通常パラメータを無視して同じレスポンスを返す
    response = requests.get(f"{api_url}?test=parameter", timeout=10)
    assert response.status_code == 200
    
    json_response = response.json()
    assert 'message' in json_response
    print(f"HelloWorld Response with parameters: {json_response}")
