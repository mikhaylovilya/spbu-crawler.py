from crawler.models import CrawlResult, Failure, Link, Page
from crawler.stats import build_stats


def make_page(url, links):
    return Page(url=url, status_code=200, title="", text="", links=links)


def test_build_stats_counts_pages_links_and_failures():
    result = CrawlResult(
        start_url="https://example.com/",
        pages=[
            make_page(
                "https://example.com/",
                [
                    Link("https://example.com/a", "A", True),
                    Link("https://news.example.com/b", "B", True),
                    Link("https://other.org/x", "X", False),
                    Link("https://other.org/x", "X again", False),
                ],
            ),
            make_page(
                "https://example.com/a",
                [
                    Link("https://example.com/files/report.pdf", "PDF", True),
                    Link("https://other.org/paper.DOC", "DOC", False),
                ],
            ),
        ],
        failures=[
            Failure("https://example.com/missing", "HTTP 404", 404),
            Failure("https://example.com/error", "timeout"),
        ],
    )

    assert build_stats(result) == {
        "total_pages": 2,
        "total_links": 6,
        "internal_pages": 2,
        "broken_pages": 2,
        "internal_subdomains": 1,
        "external_links": 3,
        "unique_external_resources": 2,
        "unique_document_links": 2,
    }


def test_build_stats_on_empty_result():
    result = CrawlResult(start_url="https://example.com/")
    assert build_stats(result) == {
        "total_pages": 0,
        "total_links": 0,
        "internal_pages": 0,
        "broken_pages": 0,
        "internal_subdomains": 0,
        "external_links": 0,
        "unique_external_resources": 0,
        "unique_document_links": 0,
    }


def test_www_is_not_counted_as_subdomain():
    result = CrawlResult(
        start_url="https://www.example.com/",
        pages=[
            make_page(
                "https://www.example.com/",
                [Link("https://example.com/about", "About", True)],
            )
        ],
    )
    assert build_stats(result)["internal_subdomains"] == 0
