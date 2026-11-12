"""Backward-compatible STDIO entry point. Never print to stdout."""
import logging
import sys
from application import create_server

logging.basicConfig(stream=sys.stderr, level=logging.INFO)
mcp = create_server()

if __name__ == "__main__":
    mcp.run(transport="stdio")
