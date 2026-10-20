"""Vercel entry point.

Vercel's Flask support looks for a Flask instance named `app` in a root
`index.py` and routes every request to it (no vercel.json rewrites needed).
The Flask app expects to be imported from within `sol_main/` (blueprint and
`data`/`config` imports are relative to that directory), so we add it to
sys.path first.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sol_main'))

from app import create_app  # noqa: E402

app = create_app()
