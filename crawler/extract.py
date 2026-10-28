import re

from bs4 import BeautifulSoup

from crawler.models import Link, Page
from crawler.urls import is_internal, normalize_url, site_host

IGNORED_TAGS = ("script", "style", "noscript", "template", "svg")
WHITESPACE = re.compile(r"\s+")


def clean_text(value):
    return WHITESPACE.sub(" ", value).strip()


def extract_page(html, url, status_code, depth=0, fetched_at=""):
    soup = BeautifulSoup(html, "html.parser")
    title = clean_text(soup.title.get_text(" ")) if soup.title else ""
    for tag in soup(IGNORED_TAGS):
        tag.decompose()
    if soup.head:
        soup.head.decompose()
    text = clean_text(soup.get_text(" "))
    host = site_host(url)
    links = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        if not href or href.startswith("#"):
            continue
        target = normalize_url(href, url)
        if target is None:
            continue
        links.append(
            Link(
                url=target,
                text=clean_text(anchor.get_text(" ")),
                internal=is_internal(target, host),
            )
        )
    return Page(
        url=url,
        status_code=status_code,
        title=title,
        text=text,
        links=links,
        depth=depth,
        fetched_at=fetched_at,
    )
