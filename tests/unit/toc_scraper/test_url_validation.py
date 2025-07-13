import pytest
from toc_scraper.app import validate_wikipedia_url

def test_valid_url():
    assert validate_wikipedia_url("https://ja.wikipedia.org/wiki/Amazon_Web_Services")[0] == True

def test_invalid_url():
    assert validate_wikipedia_url("https://example.com/test")[0] == False

def test_invalid_help_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Help:Contents")[0] == False

def test_invalid_project_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Wikipedia:About")[0] == False

def test_invalid_template_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Template:Infobox")[0] == False

def test_invalid_user_talk_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/User_talk:Example")[0] == False

def test_invalid_file_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/File:Example.jpg")[0] == False

def test_invalid_media_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Media:Example.ogg")[0] == False

def test_valid_german_wikipedia():
    assert validate_wikipedia_url("https://de.wikipedia.org/wiki/Künstliche_Intelligenz")[0] == True

def test_valid_spanish_wikipedia():
    assert validate_wikipedia_url("https://es.wikipedia.org/wiki/Inteligencia_artificial")[0] == True

def test_invalid_mobile_subdomain():
    assert validate_wikipedia_url("https://m.wikipedia.org/wiki/Test")[0] == False

def test_invalid_commons_subdomain():
    assert validate_wikipedia_url("https://commons.wikipedia.org/wiki/Test")[0] == False

def test_valid_article_with_numbers():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/World_War_II")[0] == True

def test_valid_article_with_slash():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/AC/DC")[0] == True

def test_invalid_malformed_url():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/")[0] == False

def test_invalid_query_parameters():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Test?action=edit")[0] == True  # Query params should be allowed

def test_invalid_fragment():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Test#section")[0] == True  # Fragments should be allowed

def test_edge_case_very_long_url():
    long_title = "A" * 1000
    assert validate_wikipedia_url(f"https://en.wikipedia.org/wiki/{long_title}")[0] == True

def test_invalid_whitespace_only():
    assert validate_wikipedia_url("   ")[0] == False

def test_invalid_draft_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Draft:Example")[0] == False

def test_invalid_portal_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Portal:Technology")[0] == False

def test_invalid_book_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Book:Example")[0] == False

def test_invalid_none():
    assert validate_wikipedia_url(None)[0] == False

def test_invalid_empty_string():
    assert validate_wikipedia_url("")[0] == False

def test_invalid_no_https():
    assert validate_wikipedia_url("http://en.wikipedia.org/wiki/Test")[0] == False

def test_invalid_no_wiki_path():
    assert validate_wikipedia_url("https://en.wikipedia.org/w/index.php")[0] == False

def test_invalid_special_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Special:RecentChanges")[0] == False

def test_invalid_user_page():
    assert validate_wikipedia_url("https://ja.wikipedia.org/wiki/利用者:TestUser")[0] == False

def test_invalid_talk_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Talk:Example")[0] == False

def test_invalid_category_page():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Category:Example")[0] == False

def test_invalid_wrong_domain():
    assert validate_wikipedia_url("https://example.com/wiki/Test")[0] == False

def test_valid_english_wikipedia():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Python")[0] == True

def test_valid_french_wikipedia():
    assert validate_wikipedia_url("https://fr.wikipedia.org/wiki/Intelligence_artificielle")[0] == True

def test_valid_article_with_underscores():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Machine_learning")[0] == True

def test_valid_article_with_parentheses():
    assert validate_wikipedia_url("https://en.wikipedia.org/wiki/Python_(programming_language)")[0] == True