from crawler.extract import extract_page


def test_extracts_title_text_and_clean_whitespace():
    html = """
    <html>
      <head><title> Example page </title><style>.x { color: red }</style></head>
      <body>
        <h1>Hello</h1>
        <p> Some    text
        with line breaks. </p>
        <script>alert("ignored")</script>
      </body>
    </html>
    """
    page = extract_page(html, "https://example.com/", 200)
    assert page.title == "Example page"
    assert page.text == "Hello Some text with line breaks."
    assert page.status_code == 200
    assert page.url == "https://example.com/"
    assert page.depth == 0


def test_extracts_absolute_links_and_anchor_text():
    html = '<a href="/about"> About </a><a href="https://other.org/x">Other</a>'
    page = extract_page(html, "https://example.com/news", 200)
    assert [(link.url, link.text, link.internal) for link in page.links] == [
        ("https://example.com/about", "About", True),
        ("https://other.org/x", "Other", False),
    ]


def test_subdomain_links_are_internal():
    html = '<a href="https://news.example.com/a">News</a>'
    page = extract_page(html, "https://www.example.com/", 200)
    assert page.links[0].internal is True


def test_skips_empty_fragment_and_unsupported_links():
    html = """
    <a href="">empty</a>
    <a href="#section">fragment</a>
    <a href="mailto:a@example.com">mail</a>
    <a href="javascript:void(0)">js</a>
    <a href="/real">real</a>
    """
    page = extract_page(html, "https://example.com/", 200)
    assert [link.url for link in page.links] == ["https://example.com/real"]


def test_keeps_duplicate_links():
    html = '<a href="/a">A</a><a href="/a">A again</a>'
    page = extract_page(html, "https://example.com/", 200)
    assert len(page.links) == 2


def test_handles_page_without_title():
    page = extract_page("<html><body><p>Text</p></body></html>", "https://example.com/", 200)
    assert page.title == ""
    assert page.text == "Text"
