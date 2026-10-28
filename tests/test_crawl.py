import pytest
import requests

from crawler.crawl import Crawler
from crawler.models import CrawlResult


def make_crawler(url, **kwargs):
    kwargs.setdefault("max_pages", 20)
    kwargs.setdefault("max_depth", 3)
    kwargs.setdefault("delay", 0)
    return Crawler(url, **kwargs)


def test_crawl_follows_internal_links_once(site):
    base_url, routes, seen = site
    routes["/"] = (
        200,
        "text/html",
        """
        <html><head><title>Home</title></head><body>
          <a href="/a">A</a>
          <a href="/a">A again</a>
          <a href="/broken">Broken</a>
          <a href="https://example.org/external">External</a>
        </body></html>
        """,
    )
    routes["/a"] = (
        200,
        "text/html",
        """
        <html><head><title>Page A</title></head><body>
          <a href="/b">B</a>
          <a href="/files/report.pdf">Report</a>
          <a href="mailto:test@example.org">Mail</a>
        </body></html>
        """,
    )
    routes["/b"] = (200, "text/html", "<html><body><a href='/'>Home</a></body></html>")

    result = make_crawler(f"{base_url}/").crawl()

    assert [page.url for page in result.pages] == [
        f"{base_url}/",
        f"{base_url}/a",
        f"{base_url}/b",
    ]
    assert [failure.url for failure in result.failures] == [f"{base_url}/broken"]
    assert result.failures[0].status_code == 404
    assert seen == ["/", "/a", "/broken", "/b"]
    assert result.pages[0].title == "Home"
    assert result.pages[1].depth == 1
    assert result.pages[2].depth == 2
    assert result.pages[0].links[3].internal is False


def test_crawl_respects_max_depth(site):
    base_url, routes, seen = site
    routes["/"] = (200, "text/html", "<html><body><a href='/a'>A</a></body></html>")
    routes["/a"] = (200, "text/html", "<html><body>Page A</body></html>")

    result = make_crawler(f"{base_url}/", max_depth=0).crawl()

    assert len(result.pages) == 1
    assert seen == ["/"]


def test_crawl_respects_max_pages(site):
    base_url, routes, seen = site
    routes["/"] = (
        200,
        "text/html",
        "<html><body><a href='/a'>A</a><a href='/b'>B</a></body></html>",
    )
    routes["/a"] = (200, "text/html", "<html><body>A</body></html>")
    routes["/b"] = (200, "text/html", "<html><body>B</body></html>")

    result = make_crawler(f"{base_url}/", max_pages=2).crawl()

    assert len(result.pages) == 2
    assert seen == ["/", "/a"]


def test_crawl_accepts_content_type_with_spaces(site):
    base_url, routes, seen = site
    routes["/"] = (200, " text/html ; charset=UTF-8 ", "<html><body>Hi</body></html>")

    result = make_crawler(f"{base_url}/").crawl()

    assert len(result.pages) == 1
    assert seen == ["/"]


def test_crawl_uses_redirected_url(site):
    base_url, routes, seen = site
    routes["/"] = (302, "text/html", "", {"Location": "/a"})
    routes["/a"] = (200, "text/html", "<html><body>A</body></html>")

    result = make_crawler(f"{base_url}/").crawl()

    assert [page.url for page in result.pages] == [f"{base_url}/a"]
    assert seen == ["/", "/a"]


def test_crawl_skips_redirects_to_external_sites():
    class FakeResponse:
        status_code = 200
        headers = {"Content-Type": "text/html"}
        content = b"<html><body>External</body></html>"
        url = "https://external.example/page"

    class RedirectingSession:
        headers = {}

        def get(self, url, **kwargs):
            return FakeResponse()

    result = make_crawler(
        "https://example.com/", session=RedirectingSession()
    ).crawl()

    assert result.pages == []
    assert result.failures == []


def test_crawl_skips_documents_and_non_html_responses(site):
    base_url, routes, seen = site
    routes["/"] = (
        200,
        "text/html",
        """
        <html><body>
          <a href="/files/report.pdf">PDF</a>
          <a href="/download">Download</a>
        </body></html>
        """,
    )
    routes["/download"] = (200, "application/pdf", "not really a pdf")

    result = make_crawler(f"{base_url}/").crawl()

    assert len(result.pages) == 1
    assert result.failures == []
    assert seen == ["/", "/download"]


def test_crawl_records_network_errors():
    class FailingSession:
        headers = {}

        def get(self, url, **kwargs):
            raise requests.ConnectionError("boom")

    result = make_crawler(
        "https://example.com/", session=FailingSession()
    ).crawl()

    assert result.pages == []
    assert len(result.failures) == 1
    assert result.failures[0].error == "ConnectionError: boom"
    assert result.failures[0].status_code is None


def test_crawl_rejects_invalid_start_url():
    with pytest.raises(ValueError):
        Crawler("mailto:test@example.com")


def test_crawl_validates_limits():
    with pytest.raises(ValueError):
        Crawler("https://example.com", max_pages=0)
    with pytest.raises(ValueError):
        Crawler("https://example.com", max_depth=-1)
    with pytest.raises(ValueError):
        Crawler("https://example.com", delay=-1)


def test_crawl_can_include_subdomains():
    crawler = make_crawler("https://www.example.com/")
    assert crawler._can_crawl("https://example.com/about")
    assert crawler._can_crawl("https://www.example.com/about")
    assert not crawler._can_crawl("https://news.example.com/about")
    assert not crawler._can_crawl("https://example.org/about")
    assert not crawler._can_crawl("https://example.com/report.pdf")

    crawler.include_subdomains = True
    assert crawler._can_crawl("https://news.example.com/about")


def test_crawl_result_serializes_to_dict(site):
    base_url, routes, _ = site
    routes["/"] = (200, "text/html", "<html><body><p>Hello</p></body></html>")
    result = make_crawler(f"{base_url}/").crawl()

    data = result.to_dict()

    assert isinstance(result, CrawlResult)
    assert data["start_url"] == f"{base_url}/"
    assert data["pages"][0]["text"] == "Hello"
    assert data["failures"] == []
