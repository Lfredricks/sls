"""Vercel serverless entry point.

Vercel imports `app` from this module and serves it as a WSGI app. The Flask
app expects to be imported from within `sol_main/` (blueprint and `data`/`config`
imports are relative to that directory), so we add it to sys.path first.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'sol_main'))

from app import create_app  # noqa: E402

app = create_app()
