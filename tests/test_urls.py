from crawler.urls import (
    is_document,
    is_internal,
    is_subdomain,
    normalize_url,
    site_host,
    url_host,
)


def test_normalize_relative_url():
    assert normalize_url("/about", "https://example.com/news") == "https://example.com/about"


def test_normalize_lowercases_scheme_and_host():
    assert normalize_url("HTTP://Example.COM:80/Path#top") == "http://example.com/Path"


def test_normalize_keeps_non_default_port():
    assert normalize_url("https://example.com:8443/a") == "https://example.com:8443/a"


def test_normalize_adds_root_path():
    assert normalize_url("https://example.com") == "https://example.com/"


def test_normalize_rejects_unsupported_schemes():
    assert normalize_url("mailto:test@example.com") is None
    assert normalize_url("javascript:void(0)") is None


def test_normalize_removes_fragment_and_keeps_query():
    assert normalize_url("https://example.com/a?q=1#part") == "https://example.com/a?q=1"


def test_site_host_strips_www():
    assert site_host("https://www.example.com/a") == "example.com"
    assert site_host("https://Example.COM/a") == "example.com"


def test_internal_urls_include_subdomains():
    assert is_internal("https://example.com/a", "example.com")
    assert is_internal("https://news.example.com/a", "example.com")
    assert not is_internal("https://example.org/a", "example.com")
    assert not is_internal("https://notexample.com/a", "example.com")


def test_subdomain_detection():
    assert is_subdomain("https://news.example.com/a", "example.com")
    assert not is_subdomain("https://example.com/a", "example.com")
    assert not is_subdomain("https://www.example.com/a", "example.com")


def test_url_host():
    assert url_host("https://WWW.Example.com./a") == "www.example.com"


def test_document_detection():
    assert is_document("https://example.com/report.pdf")
    assert is_document("https://example.com/report.DOCX?download=1")
    assert not is_document("https://example.com/report.html")


def test_normalize_rejects_malformed_urls():
    assert normalize_url("http://[broken") is None
    assert normalize_url("https://example.com:bad/a") is None
