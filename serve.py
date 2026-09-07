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
ROOT = SITE.parent


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(SITE), **kwargs)

    def translate_path(self, path):
        # Local-only dev tool: the naming workbench lives at the project root
        # and must never be deployed to the public site.
        clean = path.split("?", 1)[0].split("#", 1)[0]
        if clean in ("/name-editor.html", "/name-editor"):
            return str(ROOT / "name-editor.html")
        return super().translate_path(path)

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
