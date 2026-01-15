#!/usr/bin/env python
"""Entry point for running GeoDataHub MCP Server as a module."""

from geodatahub_mcp.server import main
import asyncio

if __name__ == "__main__":
    asyncio.run(main())
