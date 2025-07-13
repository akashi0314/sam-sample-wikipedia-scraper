import json
import re
from urllib.parse import urlparse, parse_qs

def validate_wikipedia_url(url):
    """
    Validate if the URL is a valid Wikipedia article URL.
    
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
    
    # Check if path starts with /wiki/
    if not parsed.path.startswith('/wiki/'):
        return False, "URL must be a Wikipedia article (/wiki/article_name)"
    
    # Extract article name
    article_name = parsed.path[6:]  # Remove '/wiki/' prefix
    
    if not article_name:
        return False, "Article name is required"
    
    # Check for forbidden paths
    forbidden_patterns = [
        r'^Special:',           # Special pages
        r'^利用者:',            # User pages (Japanese)
        r'^User:',              # User pages (English)
        r'^User_talk:',         # User talk pages (English)
        r'^ノート:',            # Talk pages (Japanese)
        r'^Talk:',              # Talk pages (English)
        r'^Wikipedia:',         # Wikipedia namespace
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
    ]
    
    for pattern in forbidden_patterns:
        if re.match(pattern, article_name, re.IGNORECASE):
            return False, f"Access to {pattern.replace('^', '').replace(':', '')} pages is not allowed"
    
    return True, ""

def lambda_handler(event, context):
    """
    Lambda function to validate Wikipedia URLs and return TOC information.
    
    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format
    context: object, required
        Lambda Context runtime methods and attributes
        
    Returns
    -------
    API Gateway Lambda Proxy Output Format: dict
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
                    "message": "Please provide a Wikipedia URL using ?url=<wikipedia_url>"
                })
            }
        
        # Validate Wikipedia URL
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
                    "error": "Invalid Wikipedia URL",
                    "message": error_message,
                    "provided_url": url
                })
            }
        
        # For now, return a success response with the validated URL
        # TODO: Implement actual TOC scraping
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*"
            },
            "body": json.dumps({
                "success": True,
                "url": url,
                "message": "Valid Wikipedia URL - TOC scraping not yet implemented",
                "validation": "passed"
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
                "message": str(e)
            })
        }
