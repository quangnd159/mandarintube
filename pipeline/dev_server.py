#!/usr/bin/env python3
"""Local preview at http://localhost:8787"""
import functools
import http.server
import pathlib

SITE = pathlib.Path(__file__).resolve().parent.parent / "site"
http.server.ThreadingHTTPServer(("127.0.0.1", 8787), functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(SITE))).serve_forever()
