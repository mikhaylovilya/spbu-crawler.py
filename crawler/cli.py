import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from crawler import __version__
from crawler.crawl import Crawler
from crawler.stats import build_stats


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        prog="crawler",
        description="Web 1.0 crawler with page statistics and JSON export.",
    )
    parser.add_argument("url", help="Start URL, for example https://example.com")
    parser.add_argument(
        "-o",
        "--output",
        default="crawl.json",
        help="Path to the output JSON file (default: crawl.json)",
    )
    parser.add_argument("--max-pages", type=int, default=100)
    parser.add_argument("--max-depth", type=int, default=3)
    parser.add_argument("--delay", type=float, default=0.2)
    parser.add_argument("--timeout", type=float, default=10.0)
    parser.add_argument("--include-subdomains", action="store_true")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser.parse_args(argv)


def save_result(result, output):
    stats = build_stats(result)
    data = result.to_dict()
    payload = {
        "start_url": data["start_url"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "stats": stats,
        "pages": data["pages"],
        "failures": data["failures"],
    }
    path = Path(output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return stats, path


def main(argv=None):
    parser = parse_args(argv)
    try:
        crawler = Crawler(
            parser.url,
            max_pages=parser.max_pages,
            max_depth=parser.max_depth,
            delay=parser.delay,
            include_subdomains=parser.include_subdomains,
            timeout=parser.timeout,
        )
    except ValueError as exc:
        parser.error(str(exc))

    result = crawler.crawl()
    stats, path = save_result(result, parser.output)
    print(json.dumps(stats, ensure_ascii=False, indent=2))
    print(f"Saved {stats['total_pages']} pages to {path}")
    return 0
