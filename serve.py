"""Local preview server with caching fully disabled.

Usage: python serve.py [port]   (default port 4174)
Serves the _site directory with `Cache-Control: no-store` so the browser
always fetches the latest files - no stale-asset confusion during testing.
"""
import http.server
import socketserver
import sys
from pathlib import Path

SITE = Path(__file__).resolve().parent / "_site"


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, *args):
        pass


def main():
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 4174
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("127.0.0.1", port), NoCacheHandler) as httpd:
        print(f"serving {SITE} at http://127.0.0.1:{port} (cache disabled)")
        httpd.serve_forever()


if __name__ == "__main__":
    main()
