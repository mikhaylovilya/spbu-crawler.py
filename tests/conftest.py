import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest


@pytest.fixture
def site():
    routes = {}
    requests_seen = []

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            requests_seen.append(self.path)
            status, content_type, body = routes.get(
                self.path, (404, "text/html", "<html><body>Not found</body></html>")
            )
            payload = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, format, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_port}"
    try:
        yield base_url, routes, requests_seen
    finally:
        server.shutdown()
        thread.join()
        server.server_close()
