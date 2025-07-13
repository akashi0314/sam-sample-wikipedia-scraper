import json
import pytest
from toc_scraper import app


@pytest.fixture()
def apigw_event_with_valid_url():
    """Generates API GW Event with valid Wikipedia URL"""

    return {
        "body": None,
        "resource": "/toc",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/toc",
            "httpMethod": "GET",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "stage": "prod",
        },
        "queryStringParameters": {"url": "https://ja.wikipedia.org/wiki/Amazon_Web_Services"},
        "headers": {
            "Accept": "application/json",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
        },
        "pathParameters": None,
        "httpMethod": "GET",
        "path": "/toc",
    }


@pytest.fixture()
def apigw_event_with_invalid_url():
    """Generates API GW Event with invalid URL"""

    return {
        "body": None,
        "resource": "/toc",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/toc",
            "httpMethod": "GET",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "stage": "prod",
        },
        "queryStringParameters": {"url": "https://example.com/test"},
        "headers": {
            "Accept": "application/json",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
        },
        "pathParameters": None,
        "httpMethod": "GET",
        "path": "/toc",
    }


@pytest.fixture()
def apigw_event_no_url():
    """Generates API GW Event without URL parameter"""

    return {
        "body": None,
        "resource": "/toc",
        "requestContext": {
            "resourceId": "123456",
            "apiId": "1234567890",
            "resourcePath": "/toc",
            "httpMethod": "GET",
            "requestId": "c6af9ac6-7b61-11e6-9a41-93e8deadbeef",
            "accountId": "123456789012",
            "stage": "prod",
        },
        "queryStringParameters": None,
        "headers": {
            "Accept": "application/json",
            "Host": "1234567890.execute-api.us-east-1.amazonaws.com",
        },
        "pathParameters": None,
        "httpMethod": "GET",
        "path": "/toc",
    }


def test_lambda_handler_valid_url(apigw_event_with_valid_url):
    """Test with valid Wikipedia URL"""

    ret = app.lambda_handler(apigw_event_with_valid_url, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 200
    assert data["success"] is True
    assert data["url"] == "https://ja.wikipedia.org/wiki/Amazon_Web_Services"
    assert data["validation"] == "passed"


def test_lambda_handler_invalid_url(apigw_event_with_invalid_url):
    """Test with invalid URL"""

    ret = app.lambda_handler(apigw_event_with_invalid_url, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 400
    assert data["success"] is False
    assert "Invalid Wikipedia URL" in data["error"]


def test_lambda_handler_no_url(apigw_event_no_url):
    """Test without URL parameter"""

    ret = app.lambda_handler(apigw_event_no_url, "")
    data = json.loads(ret["body"])

    assert ret["statusCode"] == 400
    assert data["success"] is False
    assert "URL parameter is required" in data["error"]


def test_validate_wikipedia_url():
    """Test URL validation function directly"""

    # Valid URLs
    assert app.validate_wikipedia_url("https://ja.wikipedia.org/wiki/Amazon_Web_Services")[0] is True
    assert app.validate_wikipedia_url("https://en.wikipedia.org/wiki/Python")[0] is True

    # Invalid URLs
    assert app.validate_wikipedia_url("https://example.com/test")[0] is False
    assert app.validate_wikipedia_url("https://ja.wikipedia.org/wiki/Special:RecentChanges")[0] is False
    assert app.validate_wikipedia_url("https://ja.wikipedia.org/wiki/利用者:TestUser")[0] is False
    assert app.validate_wikipedia_url("")[0] is False
