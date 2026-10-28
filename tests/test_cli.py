import json

from crawler.cli import main, parse_args
from crawler.models import CrawlResult


def test_parse_args_defaults():
    args = parse_args(["https://example.com"])
    assert args.url == "https://example.com"
    assert args.output == "crawl.json"
    assert args.max_pages == 100
    assert args.max_depth == 3
    assert args.delay == 0.2
    assert args.include_subdomains is False


def test_main_crawls_and_writes_json(site, tmp_path, capsys):
    base_url, routes, _ = site
    routes["/"] = (
        200,
        "text/html",
        "<html><head><title>Home</title></head><body>"
        "<p>Hello world</p><a href='/other'>Other</a></body></html>",
    )
    routes["/other"] = (200, "text/html", "<html><body>Other page</body></html>")
    output = tmp_path / "nested" / "result.json"

    exit_code = main(
        [
            f"{base_url}/",
            "--output",
            str(output),
            "--max-pages",
            "10",
            "--delay",
            "0",
        ]
    )

    assert exit_code == 0
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["start_url"] == f"{base_url}/"
    assert data["stats"]["total_pages"] == 2
    assert data["stats"]["total_links"] == 1
    assert data["stats"]["broken_pages"] == 0
    assert data["pages"][0]["title"] == "Home"
    assert data["pages"][0]["text"] == "Hello world Other"
    assert data["failures"] == []
    assert "generated_at" in data
    assert "Saved 2 pages" in capsys.readouterr().out


def test_save_result_shape(tmp_path):
    from crawler.cli import save_result

    result = CrawlResult(start_url="https://example.com/")
    stats, path = save_result(result, tmp_path / "out.json")
    data = json.loads(path.read_text(encoding="utf-8"))

    assert stats["total_pages"] == 0
    assert set(data) == {"start_url", "generated_at", "stats", "pages", "failures"}
