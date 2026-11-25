"""Sprint 0 minimal laptop server: a /health route only.

Binds to all network interfaces so a phone on the same network can reach it.
No upload endpoint and no web page yet (Sprint 1).
"""
import argparse
import sys
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path.split("?", 1)[0] == "/health":
            body = b"OK\n"
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)
        else:
            body = b"Not found\n"
            self.send_response(404)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def log_message(self, fmt, *args):
        # One line per request, including the client IP, to stderr.
        stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
        sys.stderr.write(f"{stamp} {self.client_address[0]} {fmt % args}\n")
        sys.stderr.flush()


def main():
    parser = argparse.ArgumentParser(description="Sprint 0 /health server")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address (default: all interfaces)")
    parser.add_argument("--port", type=int, default=8790)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), HealthHandler)
    print(f"Health server listening on http://{args.host}:{args.port}/health", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
