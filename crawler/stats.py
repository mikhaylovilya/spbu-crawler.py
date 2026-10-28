from crawler.urls import is_document, is_internal, is_subdomain, site_host, url_host


def build_stats(result):
    host = site_host(result.start_url)
    links = [link for page in result.pages for link in page.links]
    internal_subdomains = {
        url_host(url)
        for url in [page.url for page in result.pages] + [link.url for link in links]
        if is_subdomain(url, host)
    }
    external_links = [link for link in links if not is_internal(link.url, host)]
    documents = {link.url for link in links if is_document(link.url)}
    return {
        "total_pages": len(result.pages),
        "total_links": len(links),
        "internal_pages": sum(
            1 for page in result.pages if is_internal(page.url, host)
        ),
        "broken_pages": len(result.failures),
        "internal_subdomains": len(internal_subdomains),
        "external_links": len(external_links),
        "unique_external_resources": len({link.url for link in external_links}),
        "unique_document_links": len(documents),
    }
