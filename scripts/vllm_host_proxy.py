#!/usr/bin/env python3
"""Local reverse proxy that fixes the `Host` header for a self-hosted vLLM router.

A vLLM router that dispatches on `Host` returns 404 on every path unless the
header names the vhost it knows - which is not the hostname you actually connect
to when you reach it over Tailscale or a tunnel. OpenEvolve builds its OpenAI
client from a bare `api_base` string and cannot set custom headers, so this sits
in between and rewrites it:

    openevolve -> 127.0.0.1:PROXY_PORT (this) -> UPSTREAM_HOST:PORT -> router

Endpoints come from the environment so that no private hostname is committed.
Set them in `.env` (gitignored); see `.env.example` for the shape.

Responses stream through unbuffered, which matters because qwen3.6-35b emits a
long `delta.reasoning` phase before any `delta.content`.

    python scripts/vllm_host_proxy.py &
"""

from __future__ import annotations

import argparse
import http.client
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Hop-by-hop headers must not be forwarded (RFC 2616 13.5.1).
HOP_BY_HOP = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade",
}

ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


def _load_env_file(path: Path) -> None:
    """Populate os.environ from a KEY=value file, without overriding real env vars."""
    if not path.is_file():
        return
    for raw in path.read_text().splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


_load_env_file(ENV_FILE)

# The host you can actually reach (Tailscale node, tunnel, LAN address).
UPSTREAM_HOST = os.environ.get("VLLM_UPSTREAM_HOST", "vllm.internal.example")
UPSTREAM_PORT = int(os.environ.get("VLLM_UPSTREAM_PORT", "80"))
# The vhost the router matches on, sent as `Host`.
ROUTER_HOST = os.environ.get("VLLM_ROUTER_HOST", UPSTREAM_HOST)
TIMEOUT = float(os.environ.get("VLLM_TIMEOUT", "900"))


class Handler(BaseHTTPRequestHandler):
    """Forwards each request upstream with the router's `Host` header."""

    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: object) -> None:
        """Prefix the stock access log so it is identifiable in a shared terminal."""
        sys.stderr.write("proxy: %s\n" % (fmt % args))

    def _forward(self) -> None:
        """Relay one request upstream and stream the response straight back."""
        body = None
        length = self.headers.get("Content-Length")
        if length:
            body = self.rfile.read(int(length))

        headers = {
            k: v for k, v in self.headers.items()
            if k.lower() not in HOP_BY_HOP and k.lower() != "host"
        }
        headers["Host"] = ROUTER_HOST

        conn = http.client.HTTPConnection(UPSTREAM_HOST, UPSTREAM_PORT, timeout=TIMEOUT)
        try:
            conn.request(self.command, self.path, body=body, headers=headers)
            upstream = conn.getresponse()

            self.send_response(upstream.status, upstream.reason)
            for k, v in upstream.getheaders():
                if k.lower() in HOP_BY_HOP or k.lower() == "content-length":
                    continue
                self.send_header(k, v)
            # Length is unknown when we stream, so always chunk-free close-delimited.
            self.send_header("Connection", "close")
            self.end_headers()

            while True:
                chunk = upstream.read(1)
                if not chunk:
                    break
                self.wfile.write(chunk)
                self.wfile.flush()
        except Exception as exc:  # noqa: BLE001 - surface upstream failure to the client
            self.log_message("upstream error: %s", exc)
            try:
                self.send_error(502, f"upstream error: {exc}")
            except Exception as nested:  # noqa: BLE001 - client already gone
                self.log_message("could not report error to client: %s", nested)
        finally:
            conn.close()

    # BaseHTTPRequestHandler dispatches on these exact names; ruff's casing rule
    # does not apply to a contract we do not own.
    do_GET = _forward  # noqa: N815
    do_POST = _forward  # noqa: N815
    do_DELETE = _forward  # noqa: N815
    do_PUT = _forward  # noqa: N815


def main() -> int:
    """Parse arguments and serve until interrupted."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--port", type=int, default=int(os.environ.get("VLLM_PROXY_PORT", "8082"))
    )
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    server.daemon_threads = True
    sys.stderr.write(
        f"proxy: {args.host}:{args.port} -> {UPSTREAM_HOST}:{UPSTREAM_PORT} "
        f"(Host: {ROUTER_HOST})\n"
    )
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
