from urllib.parse import urljoin, urlsplit, urlunsplit

DEFAULT_PORTS = {"http": "80", "https": "443"}
DOCUMENT_SUFFIXES = (".doc", ".docx", ".pdf")


def normalize_url(url, base=None):
    try:
        value = url.strip()
        if base is not None:
            value = urljoin(base, value)
        parts = urlsplit(value)
        scheme = parts.scheme.lower()
        if scheme not in DEFAULT_PORTS:
            return None
        host = parts.hostname
        if not host:
            return None
        host = host.lower().rstrip(".")
        if ":" in host:
            host = f"[{host}]"
        port = parts.port
        if port is not None and str(port) != DEFAULT_PORTS[scheme]:
            host = f"{host}:{port}"
        path = parts.path or "/"
        return urlunsplit((scheme, host, path, parts.query, ""))
    except ValueError:
        return None


def site_host(url):
    host = urlsplit(url).hostname or ""
    host = host.lower().rstrip(".")
    if host.startswith("www."):
        host = host[4:]
    return host


def url_host(url):
    return (urlsplit(url).hostname or "").lower().rstrip(".")


def is_internal(url, host):
    target = url_host(url)
    return target == host or target.endswith(f".{host}")


def is_subdomain(url, host):
    target = url_host(url)
    if target.startswith("www."):
        target = target[4:]
    return target != host and target.endswith(f".{host}")


def is_document(url):
    return urlsplit(url).path.lower().endswith(DOCUMENT_SUFFIXES)
