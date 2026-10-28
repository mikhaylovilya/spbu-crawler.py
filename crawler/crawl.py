import time
from collections import deque
from datetime import datetime, timezone

import requests

from crawler.extract import extract_page
from crawler.models import CrawlResult, Failure
from crawler.urls import is_document, is_internal, is_subdomain, normalize_url, site_host

DEFAULT_USER_AGENT = "spbu-crawler/0.1"
HTML_TYPES = {"text/html", "application/xhtml+xml"}


class Crawler:
    def __init__(
        self,
        start_url,
        max_pages=100,
        max_depth=3,
        delay=0.2,
        include_subdomains=False,
        timeout=10.0,
        session=None,
        sleep=time.sleep,
    ):
        normalized = normalize_url(start_url)
        if normalized is None:
            raise ValueError(f"Unsupported start URL: {start_url}")
        if max_pages < 1:
            raise ValueError("max_pages must be at least 1")
        if max_depth < 0:
            raise ValueError("max_depth must be non-negative")
        if delay < 0:
            raise ValueError("delay must be non-negative")
        self.start_url = normalized
        self.max_pages = max_pages
        self.max_depth = max_depth
        self.delay = delay
        self.include_subdomains = include_subdomains
        self.timeout = timeout
        self.host = site_host(normalized)
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", DEFAULT_USER_AGENT)
        self.sleep = sleep

    def crawl(self):
        result = CrawlResult(start_url=self.start_url)
        queue = deque([(self.start_url, 0)])
        seen = {self.start_url}
        processed = 0
        first_request = True

        while queue and processed < self.max_pages:
            url, depth = queue.popleft()
            if not first_request and self.delay:
                self.sleep(self.delay)
            first_request = False
            processed += 1

            try:
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=True
                )
            except requests.RequestException as exc:
                result.failures.append(
                    Failure(url=url, error=f"{type(exc).__name__}: {exc}")
                )
                continue

            if response.status_code >= 400:
                result.failures.append(
                    Failure(
                        url=url,
                        error=f"HTTP {response.status_code}",
                        status_code=response.status_code,
                    )
                )
                continue

            content_type = (
                response.headers.get("Content-Type", "").split(";")[0].strip().lower()
            )
            if content_type and content_type not in HTML_TYPES:
                continue

            final_url = normalize_url(response.url) or url
            if not self._can_crawl(final_url):
                continue
            seen.add(final_url)
            page = extract_page(
                response.content,
                final_url,
                response.status_code,
                depth=depth,
                fetched_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
            result.pages.append(page)

            if depth >= self.max_depth:
                continue
            for link in page.links:
                if not self._can_crawl(link.url) or link.url in seen:
                    continue
                seen.add(link.url)
                queue.append((link.url, depth + 1))

        return result

    def _can_crawl(self, url):
        if not is_internal(url, self.host) or is_document(url):
            return False
        if not self.include_subdomains and is_subdomain(url, self.host):
            return False
        return True
