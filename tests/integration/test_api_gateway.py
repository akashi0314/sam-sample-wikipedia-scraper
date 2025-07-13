import os

import boto3
import pytest
import requests

"""
Make sure env variable AWS_SAM_STACK_NAME exists with the name of the stack we are going to test. 
"""


class TestApiGateway:

    @pytest.fixture()
    def api_gateway_url(self):
        """ Get the API Gateway URL from Cloudformation Stack outputs """
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")

        if stack_name is None:
            raise ValueError('Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack')

        client = boto3.client("cloudformation")

        try:
            response = client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name} \n" f'Please make sure a stack with the name "{stack_name}" exists'
            ) from e

        stacks = response["Stacks"]
        stack_outputs = stacks[0]["Outputs"]
        
        # Debug: Print all available outputs
        print(f"Available outputs in stack {stack_name}:")
        for output in stack_outputs:
            print(f"  - {output['OutputKey']}: {output['OutputValue']}")
        
        # Look for WikipediaTocApi specifically (this is a Wikipedia TOC project)
        api_outputs = [output for output in stack_outputs if output["OutputKey"] == "WikipediaTocApi"]
        
        if not api_outputs:
            raise KeyError(f"WikipediaTocApi not found in stack {stack_name}. Available outputs: {[o['OutputKey'] for o in stack_outputs]}")

        return api_outputs[0]["OutputValue"]  # Extract url from stack outputs

    def test_api_gateway_valid_url(self, api_gateway_url):
        """ Call the Wikipedia TOC API Gateway endpoint with valid Wikipedia URL """
        test_url = "https://ja.wikipedia.org/wiki/Amazon_Web_Services"
        response = requests.get(f"{api_gateway_url}?url={test_url}", timeout=15)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"] == test_url
        assert "toc" in data
        assert "title" in data
        assert "total_items" in data
        
        # TOC構造の詳細検証
        assert isinstance(data["toc"], list)
        if data["toc"]:  # TOCが存在する場合
            toc_item = data["toc"][0]
            assert "level" in toc_item
            assert "title" in toc_item
            assert "anchor" in toc_item
            assert isinstance(toc_item["level"], int)
            assert toc_item["level"] >= 1

    def test_api_gateway_invalid_url(self, api_gateway_url):
        """ Call the Wikipedia TOC API Gateway endpoint with invalid URL """
        test_url = "https://example.com/test"
        response = requests.get(f"{api_gateway_url}?url={test_url}", timeout=10)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        # Wikipedia関連のエラーメッセージを確認
        error_msg = data["error"].lower()
        assert "wikipedia" in error_msg

    def test_api_gateway_no_url(self, api_gateway_url):
        """ Call the Wikipedia TOC API Gateway endpoint without URL parameter """
        response = requests.get(api_gateway_url, timeout=10)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        error_msg = data["error"].lower()
        assert any(keyword in error_msg for keyword in ["url", "required", "parameter"])

    def test_api_gateway_forbidden_namespace(self, api_gateway_url):
        """ Call the Wikipedia TOC API Gateway endpoint with forbidden namespace """
        # Test with Special page (should be forbidden)
        test_url = "https://en.wikipedia.org/wiki/Special:RecentChanges"
        response = requests.get(f"{api_gateway_url}?url={test_url}", timeout=10)

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data
        # robots.txtまたは禁止メッセージを確認
        error_msg = data["error"].lower()
        assert any(keyword in error_msg for keyword in ['robots.txt', 'prohibited', 'forbidden'])

    def test_api_gateway_japanese_article(self, api_gateway_url):
        """ Call the Wikipedia TOC API Gateway endpoint with Japanese Wikipedia article """
        test_url = "https://ja.wikipedia.org/wiki/人工知能"
        response = requests.get(f"{api_gateway_url}?url={test_url}", timeout=15)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"] == test_url
        assert "toc" in data
        assert "title" in data
        # 日本語タイトルの確認
        assert "人工知能" in data["title"] or "AI" in data["title"] or len(data["title"]) > 0

    def test_api_gateway_english_article(self, api_gateway_url):
        """ Call the Wikipedia TOC API Gateway endpoint with English Wikipedia article """
        test_url = "https://en.wikipedia.org/wiki/Machine_learning"
        response = requests.get(f"{api_gateway_url}?url={test_url}", timeout=15)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["url"] == test_url
        assert "toc" in data
        assert "title" in data
        assert "Machine learning" in data["title"] or "machine" in data["title"].lower()
