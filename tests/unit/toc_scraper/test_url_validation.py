"""
Wikipedia TOC Scraper API Test Suite

This test suite demonstrates comprehensive testing practices for web scraping applications:
- Input validation and security testing
- URL parsing and protocol validation
- Multi-language support testing
- Error handling verification
- Performance and reliability testing

Educational Focus:
- Learn how to validate URLs safely
- Understand robots.txt compliance
- Practice comprehensive test coverage
- Explore internationalization testing
"""

import pytest
import time
from unittest.mock import Mock, patch
from toc_scraper.app import validate_wikipedia_url, scrape_wikipedia_toc, lambda_handler


# Test Helper Functions - Educational Pattern: DRY Principle
def assert_url_rejected(url, expected_keywords=None):
    """
    Helper function to verify URL rejection with optional keyword validation
    
    Educational Note: Helper functions reduce code duplication and improve test readability
    """
    is_valid, error_msg = validate_wikipedia_url(url)
    assert is_valid == False, f"Should reject URL: {url}"
    
    if expected_keywords:
        if isinstance(expected_keywords, str):
            expected_keywords = [expected_keywords]
        
        keyword_found = any(keyword.lower() in error_msg.lower() for keyword in expected_keywords)
        assert keyword_found, f"Error message should contain one of {expected_keywords}: {error_msg}"
    
    return error_msg


def assert_url_accepted(url):
    """
    Helper function to verify URL acceptance
    
    Educational Note: Positive test cases are as important as negative ones
    """
    is_valid, error_msg = validate_wikipedia_url(url)
    assert is_valid == True, f"Should accept URL: {url}, Error: {error_msg}"


class TestValidWikipediaUrls:
    """
    Testing Valid Wikipedia URLs
    
    Educational Focus: Learn what constitutes a valid Wikipedia URL
    - Protocol requirements (HTTPS)
    - Domain validation
    - Path structure
    - Multi-language support
    """
    
    def test_valid_japanese_wikipedia(self):
        """Test Japanese Wikipedia article URL validation"""
        assert_url_accepted("https://ja.wikipedia.org/wiki/Amazon_Web_Services")
    
    def test_valid_english_wikipedia(self):
        """Test English Wikipedia article URL validation"""
        assert_url_accepted("https://en.wikipedia.org/wiki/Python")
    
    def test_valid_multilingual_support(self):
        """
        Test multi-language Wikipedia support
        
        Educational Note: Web applications often need to handle multiple languages
        """
        valid_urls = [
            "https://de.wikipedia.org/wiki/Künstliche_Intelligenz",
            "https://es.wikipedia.org/wiki/Inteligencia_artificial",
            "https://fr.wikipedia.org/wiki/Intelligence_artificielle",
            "https://zh.wikipedia.org/wiki/人工智能",
            "https://ru.wikipedia.org/wiki/Искусственный_интеллект"
        ]
        for url in valid_urls:
            assert_url_accepted(url)
    
    def test_valid_article_name_patterns(self):
        """
        Test various article naming patterns
        
        Educational Note: Real-world URLs contain special characters, numbers, and symbols
        """
        valid_patterns = [
            "https://en.wikipedia.org/wiki/Machine_learning",  # アンダースコア
            "https://en.wikipedia.org/wiki/Python_(programming_language)",  # 括弧
            "https://en.wikipedia.org/wiki/World_War_II",  # 数字
            "https://en.wikipedia.org/wiki/AC/DC",  # スラッシュ
            "https://en.wikipedia.org/wiki/2023",  # 数字開始
            "https://en.wikipedia.org/wiki/COVID-19"  # ハイフンと数字
        ]
        for url in valid_patterns:
            assert_url_accepted(url)
    
    def test_valid_url_with_query_and_fragment(self):
        """
        Test URLs with query parameters and fragments
        
        Educational Note: URLs often contain additional parameters that should be handled gracefully
        """
        urls_with_extras = [
            "https://en.wikipedia.org/wiki/Test?action=edit",
            "https://en.wikipedia.org/wiki/Test#section",
            "https://en.wikipedia.org/wiki/Test?oldid=123456#history"
        ]
        for url in urls_with_extras:
            assert_url_accepted(url)


class TestRobotsTxtCompliance:
    """
    Testing robots.txt Compliance
    
    Educational Focus: Learn about web scraping ethics and legal requirements
    - Understanding robots.txt protocol
    - Respecting website policies
    - Avoiding prohibited paths
    
    Why This Matters: Proper robots.txt compliance prevents legal issues and maintains good relationships with website owners
    """
    
    def test_forbidden_system_paths(self):
        """
        Test rejection of system-level paths
        
        Educational Note: System paths like /w/ and /api/ are typically reserved for internal use
        """
        forbidden_paths = [
            ("https://en.wikipedia.org/w/index.php?title=Test", "/w/"),  # /w/
            ("https://en.wikipedia.org/api/rest_v1/page/summary/Test", "/api/"),  # /api/
            ("https://en.wikipedia.org/trap/test", "/trap/")  # /trap/
        ]
        for url, path_type in forbidden_paths:
            is_valid, error_msg = validate_wikipedia_url(url)
            assert is_valid == False, f"Should reject system path: {url}"
            # app.pyの実際のエラーメッセージに合わせて検証
            assert ("robots.txt" in error_msg.lower() or 
                    "prohibited" in error_msg.lower() or
                    "article" in error_msg.lower()), f"Error message should indicate forbidden path: {error_msg}"
    
    def test_protocol_and_domain_validation(self):
        """
        Test strict protocol and domain validation
        
        Educational Note: Security best practices require HTTPS and domain verification
        """
        invalid_urls = [
            ("http://en.wikipedia.org/wiki/Test", ["HTTPS"]),  # HTTP禁止
            ("https://example.com/wiki/Test", ["Wikipedia"]),  # 非Wikipediaドメイン
            ("https://m.wikipedia.org/wiki/Test", ["Mobile", "supported"]),  # モバイル版
            ("https://commons.wikipedia.org/wiki/Test", ["Commons", "supported"])  # Commons
        ]
        for url, expected_keywords in invalid_urls:
            assert_url_rejected(url, expected_keywords)
    
    def test_path_structure_validation(self):
        """
        Test Wikipedia-specific path structure requirements
        
        Educational Note: Different websites have different URL patterns
        """
        invalid_paths = [
            ("https://en.wikipedia.org/", ["article", "required"]),  # パスなし
            ("https://en.wikipedia.org/wiki/", ["article", "required"]),  # 記事名なし
            ("https://en.wikipedia.org/index.php", ["article", "/wiki/"])  # 非/wiki/パス
        ]
        for url, expected_keywords in invalid_paths:
            assert_url_rejected(url, expected_keywords)


class TestForbiddenNamespaces:
    """
    Testing Forbidden Namespaces
    
    Educational Focus: Learn about Wikipedia's namespace system
    - Understanding MediaWiki namespaces
    - Distinguishing content from administrative pages
    - Handling internationalization in namespace detection
    
    Key Concept: Namespaces separate different types of content (articles, user pages, discussions, etc.)
    """
    
    def test_english_forbidden_namespaces(self):
        """
        Test English namespace prohibition
        
        Educational Note: Each namespace serves a specific purpose and may not be suitable for scraping
        """
        forbidden_namespaces = [
            "https://en.wikipedia.org/wiki/Special:RecentChanges",
            "https://en.wikipedia.org/wiki/User:TestUser",
            "https://en.wikipedia.org/wiki/User_talk:Example",
            "https://en.wikipedia.org/wiki/Talk:Example",
            "https://en.wikipedia.org/wiki/File:Example.jpg",
            "https://en.wikipedia.org/wiki/Media:Example.ogg",
            "https://en.wikipedia.org/wiki/Category:Example",
            "https://en.wikipedia.org/wiki/Template:Infobox",
            "https://en.wikipedia.org/wiki/Help:Contents",
            "https://en.wikipedia.org/wiki/Portal:Technology",
            "https://en.wikipedia.org/wiki/Draft:Example",
            "https://en.wikipedia.org/wiki/Book:Example",
            "https://en.wikipedia.org/wiki/Module:Test",
            "https://en.wikipedia.org/wiki/MediaWiki:Test",
            "https://en.wikipedia.org/wiki/Project:Test",
            "https://en.wikipedia.org/wiki/Wikipedia:About"
        ]
        for url in forbidden_namespaces:
            is_valid, error_msg = validate_wikipedia_url(url)
            assert is_valid == False, f"Should reject forbidden namespace: {url}"
            assert ("robots.txt" in error_msg.lower() or 
                    "prohibited" in error_msg.lower()), f"Error should mention prohibition: {error_msg}"
    
    def test_japanese_forbidden_namespaces(self):
        """
        Test Japanese namespace prohibition
        
        Educational Note: Namespace names are localized in different language versions of Wikipedia
        """
        japanese_forbidden = [
            "https://ja.wikipedia.org/wiki/特別:最近の更新",
            "https://ja.wikipedia.org/wiki/利用者:TestUser",
            "https://ja.wikipedia.org/wiki/利用者‐会話:TestUser",
            "https://ja.wikipedia.org/wiki/ノート:テスト",
            "https://ja.wikipedia.org/wiki/ファイル:Example.jpg",
            "https://ja.wikipedia.org/wiki/カテゴリ:テスト"
        ]
        for url in japanese_forbidden:
            assert validate_wikipedia_url(url)[0] == False, f"Should reject Japanese forbidden namespace: {url}"
    
    def test_case_insensitive_validation(self):
        """
        Test case-insensitive namespace detection
        
        Educational Note: URLs can have various capitalizations, so robust validation is needed
        """
        case_variations = [
            "https://en.wikipedia.org/wiki/SPECIAL:RecentChanges",
            "https://en.wikipedia.org/wiki/special:RecentChanges",
            "https://en.wikipedia.org/wiki/Special:RECENTCHANGES",
            "https://en.wikipedia.org/wiki/USER:TestUser",
            "https://en.wikipedia.org/wiki/user:testuser"
        ]
        for url in case_variations:
            assert validate_wikipedia_url(url)[0] == False, f"Should reject case variation: {url}"


class TestUrlEncodingSupport:
    """
    Testing URL Encoding Support
    
    Educational Focus: Learn about URL encoding and internationalization
    - Understanding percent encoding
    - Handling non-ASCII characters
    - Supporting international domain names
    
    Key Concept: URLs must encode special characters to be transmitted safely over the internet
    """
    
    def test_encoded_japanese_articles(self):
        """
        Test handling of URL-encoded Japanese characters
        
        Educational Note: Non-ASCII characters are encoded as percent sequences (e.g., %E4%BA%BA)
        """
        encoded_articles = [
            "https://ja.wikipedia.org/wiki/%E4%BA%BA%E5%B7%A5%E7%9F%A5%E8%83%BD",  # 人工知能
            "https://ja.wikipedia.org/wiki/Amazon%20Web%20Services",  # スペース
            "https://ja.wikipedia.org/wiki/C%2B%2B"  # C++
        ]
        for url in encoded_articles:
            assert validate_wikipedia_url(url)[0] == True, f"Should accept encoded article: {url}"
    
    def test_encoded_forbidden_namespaces(self):
        """
        Test detection of encoded forbidden namespaces
        
        Educational Note: Security validation must work even when input is encoded
        """
        encoded_forbidden = [
            "https://ja.wikipedia.org/wiki/%E5%88%A9%E7%94%A8%E8%80%85:TestUser",  # 利用者
            "https://ja.wikipedia.org/wiki/%E7%89%B9%E5%88%A5:RecentChanges",  # 特別
            "https://en.wikipedia.org/wiki/User%3ATestUser"  # User:
        ]
        for url in encoded_forbidden:
            assert validate_wikipedia_url(url)[0] == False, f"Should reject encoded forbidden: {url}"
    
    def test_special_character_handling(self):
        """
        Test handling of special characters in article names
        
        Educational Note: Real-world data contains various special characters that need proper handling
        """
        special_chars = [
            "https://en.wikipedia.org/wiki/AT%26T",  # &
            "https://en.wikipedia.org/wiki/C%23_%28programming_language%29",  # C#
            "https://fr.wikipedia.org/wiki/Caf%C3%A9"  # Café
        ]
        for url in special_chars:
            assert validate_wikipedia_url(url)[0] == True, f"Should handle special chars: {url}"


class TestInputValidation:
    """
    Testing Input Validation and Security
    
    Educational Focus: Learn defensive programming practices
    - Handling edge cases and invalid input
    - Preventing security vulnerabilities
    - Graceful error handling
    
    Security Principle: Never trust user input - always validate and sanitize
    """
    
    def test_null_and_empty_inputs(self):
        """
        Test handling of null and empty inputs
        
        Educational Note: Edge cases like null/empty values often cause application crashes
        """
        invalid_inputs = [None, "", "   ", "\t\n"]
        for invalid_input in invalid_inputs:
            is_valid, error_msg = validate_wikipedia_url(invalid_input)
            assert is_valid == False, f"Should reject invalid input: {repr(invalid_input)}"
            assert "required" in error_msg.lower(), f"Error should mention requirement: {error_msg}"
    
    def test_malformed_urls(self):
        """
        Test handling of malformed URLs
        
        Educational Note: Invalid input should be rejected gracefully with helpful error messages
        """
        malformed_urls = [
            "not_a_url",
            "https://",
            "wikipedia.org/wiki/Test",
            "https:/en.wikipedia.org/wiki/Test",  # スラッシュ不足
            "https://en.wikipedia.org//wiki/Test"  # スラッシュ重複
        ]
        for url in malformed_urls:
            assert validate_wikipedia_url(url)[0] == False, f"Should reject malformed URL: {url}"
    
    def test_extremely_long_inputs(self):
        """
        Test handling of extremely long inputs
        
        Educational Note: Long inputs can cause memory issues or buffer overflows
        """
        long_title = "A" * 2000
        long_url = f"https://en.wikipedia.org/wiki/{long_title}"
        
        # 長すぎる入力でもクラッシュしないことを確認
        is_valid, error_msg = validate_wikipedia_url(long_url)
        # 実装によって受け入れるか拒否するかは異なるが、クラッシュしないことが重要
        assert isinstance(is_valid, bool)
        assert isinstance(error_msg, str)


class TestErrorHandling:
    """
    Testing Error Handling and User Experience
    
    Educational Focus: Learn about proper error handling
    - Providing meaningful error messages
    - Consistent error response format
    - Debugging and troubleshooting support
    
    UX Principle: Good error messages help users understand and fix problems
    """
    
    def test_error_message_content(self):
        """
        Test that error messages contain relevant information
        
        Educational Note: Error messages should be specific enough to help users fix the problem
        """
        test_cases = [
            ("https://example.com/wiki/Test", "Wikipedia"),
            ("https://en.wikipedia.org/wiki/Special:Test", ["Special", "robots.txt", "prohibited"]),
            ("https://en.wikipedia.org/wiki/User:Test", ["User", "robots.txt", "prohibited"]),
            ("http://en.wikipedia.org/wiki/Test", "HTTPS")
        ]
        
        for url, expected_keywords in test_cases:
            is_valid, error_msg = validate_wikipedia_url(url)
            assert is_valid == False
            
            if isinstance(expected_keywords, str):
                expected_keywords = [expected_keywords]
            
            keyword_found = any(keyword.lower() in error_msg.lower() for keyword in expected_keywords)
            assert keyword_found, f"Error message should contain one of {expected_keywords}: {error_msg}"
    
    def test_error_message_structure(self):
        """
        Test error message formatting and structure
        
        Educational Note: Consistent formatting makes error handling more predictable
        """
        is_valid, error_msg = validate_wikipedia_url("https://example.com/wiki/Test")
        
        assert is_valid == False
        assert isinstance(error_msg, str)
        assert len(error_msg) > 0
        assert not error_msg.startswith(" ")  # 先頭空白なし
        assert not error_msg.endswith(" ")    # 末尾空白なし


class TestPerformanceAndReliability:
    """
    Testing Performance and Reliability
    
    Educational Focus: Learn about performance testing
    - Measuring execution time
    - Memory usage monitoring
    - Scalability considerations
    
    Performance Principle: Validation should be fast enough for real-time use
    """
    
    def test_validation_performance(self):
        """
        Test URL validation performance under load
        
        Educational Note: Performance testing helps identify bottlenecks before production
        """
        test_urls = [
            "https://ja.wikipedia.org/wiki/Amazon_Web_Services",
            "https://en.wikipedia.org/wiki/Python",
            "https://de.wikipedia.org/wiki/Künstliche_Intelligenz",
            "https://en.wikipedia.org/wiki/Special:RecentChanges",
            "https://ja.wikipedia.org/wiki/利用者:TestUser"
        ] * 20  # 100回のテスト
        
        start_time = time.time()
        for url in test_urls:
            validate_wikipedia_url(url)
        end_time = time.time()
        
        # 100回の検証が1秒以内に完了することを確認
        execution_time = end_time - start_time
        assert execution_time < 1.0, f"Validation took too long: {execution_time:.3f}s"
    
    def test_memory_efficiency(self):
        """
        Test memory usage efficiency
        
        Educational Note: Memory leaks can cause long-running applications to crash
        """
        import gc
        
        # ガベージコレクション実行
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # 大量のURL検証を実行
        for i in range(1000):
            validate_wikipedia_url(f"https://en.wikipedia.org/wiki/Test_{i}")
        
        # 再度ガベージコレクション
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # オブジェクト数の増加が合理的な範囲内であることを確認
        object_increase = final_objects - initial_objects
        assert object_increase < 100, f"Too many objects created: {object_increase}"


class TestLambdaIntegration:
    """
    Testing Lambda Function Integration
    
    Educational Focus: Learn about serverless testing
    - API Gateway integration
    - HTTP request/response handling
    - Status code management
    - JSON serialization
    
    Serverless Concept: Functions should handle HTTP events and return proper responses
    """
    
    def test_lambda_handler_success_case(self):
        """
        Test successful Lambda function execution
        
        Educational Note: Success cases should return 200 status with proper JSON structure
        """
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'url': 'https://ja.wikipedia.org/wiki/Amazon_Web_Services'
            }
        }
        context = Mock()
        
        with patch('toc_scraper.app.scrape_wikipedia_toc') as mock_scrape:
            mock_scrape.return_value = {
                'success': True,
                'url': 'https://ja.wikipedia.org/wiki/Amazon_Web_Services',
                'title': 'Amazon Web Services',
                'toc': [
                    {
                        'level': 1,
                        'title': 'Overview',
                        'anchor': 'Overview',
                        'href': '#Overview'
                    }
                ],
                'total_items': 1
            }
            
            response = lambda_handler(event, context)
            
            assert response['statusCode'] == 200
            assert 'application/json' in response['headers']['Content-Type']
            
            import json
            body = json.loads(response['body'])
            assert body['success'] == True
            assert 'title' in body
            assert 'toc' in body
            assert body['url'] == 'https://ja.wikipedia.org/wiki/Amazon_Web_Services'
    
    def test_lambda_handler_invalid_url(self):
        """
        Test Lambda function with invalid URL input
        
        Educational Note: Invalid input should return 400 (Bad Request) status
        """
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'url': 'https://example.com/wiki/Test'
            }
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        
        import json
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'error' in body
        assert 'message' in body
    
    def test_lambda_handler_missing_url(self):
        """
        Test Lambda function with missing URL parameter
        
        Educational Note: Missing required parameters should return clear error messages
        """
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': None
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        
        import json
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'error' in body
        assert ('required' in body['error'].lower() or 
                'required' in body['message'].lower()), f"Error should indicate missing URL: {body}"
    
    def test_lambda_handler_empty_query_params(self):
        """
        Test Lambda function with empty query parameters
        """
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {}
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 400
        
        import json
        body = json.loads(response['body'])
        assert body['success'] == False
    
    def test_lambda_handler_method_not_allowed(self):
        """
        Test Lambda function with unsupported HTTP method
        
        Educational Note: Unsupported methods should return 405 (Method Not Allowed)
        """
        event = {
            'httpMethod': 'POST',
            'queryStringParameters': {
                'url': 'https://ja.wikipedia.org/wiki/Test'
            }
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 405
        
        import json
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'method' in body['error'].lower()
    
    @patch('toc_scraper.app.scrape_wikipedia_toc')
    def test_lambda_handler_scraping_error(self, mock_scrape):
        """
        Test Lambda function when scraping fails
        """
        mock_scrape.return_value = {
            'success': False,
            'error': 'Failed to fetch Wikipedia page',
            'message': 'Connection timeout'
        }
        
        event = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'url': 'https://ja.wikipedia.org/wiki/Test'
            }
        }
        context = Mock()
        
        response = lambda_handler(event, context)
        
        assert response['statusCode'] == 500
        
        import json
        body = json.loads(response['body'])
        assert body['success'] == False
        assert 'error' in body


# テスト実行時の設定
@pytest.fixture(scope="session", autouse=True)
def test_environment_setup():
    """
    Set up test environment
    
    Educational Note: Fixtures help set up consistent test environments
    """
    import os
    os.environ['ENVIRONMENT'] = 'test'
    os.environ['LOG_LEVEL'] = 'DEBUG'
    yield
    # teardown処理があればここに記述


# Test Organization and Categorization
# Educational Note: Test markers help organize and run specific test categories
# Example usage: pytest -m "unit" or pytest -m "robots_compliance"
# 
# These would be defined in pytest.ini:
# [tool:pytest]
# markers =
#     unit: Unit tests
#     integration: Integration tests
#     performance: Performance tests
#     robots_compliance: Tests for robots.txt compliance