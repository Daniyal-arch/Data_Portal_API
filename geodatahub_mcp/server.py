#!/usr/bin/env python
"""
GeoDataHub MCP Server

A Model Context Protocol (MCP) server that exposes GeoDataHub functionality
to AI assistants like Claude, enabling natural language satellite data search
and download capabilities.

Usage:
    python -m geodatahub_mcp.server

Or via MCP configuration in Claude Desktop/Code.
"""

import os
import sys
import json
from typing import Any, Optional
from datetime import datetime, timedelta

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import GeoDataHub components
from geodatahub import GeoDataHub, NLParser, DataRequest, SearchResult
from geodatahub.nlp.geocoder import Geocoder


# Initialize MCP server
mcp_server = Server("geodatahub")

# Global instances (initialized lazily)
_hub: Optional[GeoDataHub] = None
_parser: Optional[NLParser] = None
_geocoder: Optional[Geocoder] = None
_last_search_results: list = []


def get_hub() -> GeoDataHub:
    """Get or create GeoDataHub instance."""
    global _hub
    if _hub is None:
        _hub = GeoDataHub()
    return _hub


def get_parser() -> NLParser:
    """Get or create NLParser instance."""
    global _parser
    if _parser is None:
        _parser = NLParser()
    return _parser


def get_geocoder() -> Geocoder:
    """Get or create Geocoder instance."""
    global _geocoder
    if _geocoder is None:
        _geocoder = Geocoder()
    return _geocoder


def format_results_for_display(results: list[SearchResult]) -> str:
    """Format search results for human-readable display."""
    if not results:
        return "No results found."

    output = [f"Found {len(results)} results:\n"]

    for i, result in enumerate(results, 1):
        lines = [
            f"\n{i}. {result.title}",
            f"   ID: {result.id}",
            f"   Provider: {result.provider} | Type: {result.product_type}",
            f"   Date: {result.datetime[:10] if result.datetime else 'Unknown'}"
        ]

        if result.cloud_cover is not None:
            lines.append(f"   Cloud Cover: {result.cloud_cover:.1f}%")

        if result.bbox:
            lines.append(f"   BBox: ({result.bbox[0]:.2f}, {result.bbox[1]:.2f}, {result.bbox[2]:.2f}, {result.bbox[3]:.2f})")

        if result.size_mb:
            lines.append(f"   Size: {result.size_mb:.1f} MB")

        output.append("\n".join(lines))

    return "\n".join(output)


@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """List available MCP tools."""
    return [
        Tool(
            name="search_satellite_data",
            description="""Search for satellite imagery and geospatial data using natural language.

Examples:
- "Sentinel-2 images of Paris from January 2024 with less than 20% cloud cover"
- "Landsat 8 data for New York from last month"
- "DEM data for Mount Everest"
- "Sentinel-1 SAR data for Tokyo"

Supports: Sentinel-2, Sentinel-1, Landsat, DEM, and more via Copernicus, USGS, AWS.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Natural language query describing the satellite data you want to find"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results to return (default: 10)",
                        "default": 10
                    }
                },
                "required": ["query"]
            }
        ),
        Tool(
            name="search_satellite_data_structured",
            description="""Search for satellite data using structured parameters for precise queries.

Use this when you need exact control over search parameters.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "product": {
                        "type": "string",
                        "description": "Product type code (e.g., S2_MSI_L2A, LANDSAT_C2L2, S1_SAR_GRD)",
                        "enum": ["S2_MSI_L2A", "S1_SAR_GRD", "LANDSAT_C2L2", "COP-DEM_GLO-30"]
                    },
                    "location": {
                        "type": "string",
                        "description": "Location name to search (will be geocoded to coordinates)"
                    },
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Bounding box as [min_lon, min_lat, max_lon, max_lat]",
                        "minItems": 4,
                        "maxItems": 4
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date in YYYY-MM-DD format"
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date in YYYY-MM-DD format"
                    },
                    "cloud_cover_max": {
                        "type": "number",
                        "description": "Maximum cloud cover percentage (0-100)",
                        "minimum": 0,
                        "maximum": 100
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results",
                        "default": 10
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="download_satellite_data",
            description="""Download satellite data from a previous search.

Use the result index (1-based) from the last search to specify which product to download.
Downloads are saved to the configured output directory.""",
            inputSchema={
                "type": "object",
                "properties": {
                    "result_index": {
                        "type": "integer",
                        "description": "Index of the result to download (1-based, from last search)",
                        "minimum": 1
                    },
                    "output_dir": {
                        "type": "string",
                        "description": "Output directory path (optional, uses default if not specified)"
                    }
                },
                "required": ["result_index"]
            }
        ),
        Tool(
            name="list_data_providers",
            description="List all available satellite data providers and their status.",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),
        Tool(
            name="list_products",
            description="List available satellite products/datasets that can be searched.",
            inputSchema={
                "type": "object",
                "properties": {
                    "provider": {
                        "type": "string",
                        "description": "Filter products by provider name (optional)"
                    }
                },
                "required": []
            }
        ),
        Tool(
            name="geocode_location",
            description="Convert a location name to geographic coordinates (bounding box).",
            inputSchema={
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "Location name to geocode (e.g., 'Paris, France', 'Mount Everest')"
                    }
                },
                "required": ["location"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    """Handle tool calls."""
    global _last_search_results

    try:
        if name == "search_satellite_data":
            # Natural language search
            query = arguments.get("query", "")
            limit = arguments.get("limit", 10)

            parser = get_parser()
            hub = get_hub()

            # Parse natural language query
            request = parser.parse(query)
            request.limit = limit

            # Execute search
            results = hub.search(request)
            _last_search_results = results

            # Format output
            output = f"Query: {query}\n"
            output += f"Parsed as: {request}\n\n"
            output += format_results_for_display(results)

            if results:
                output += f"\n\nUse download_satellite_data with result_index (1-{len(results)}) to download."

            return [TextContent(type="text", text=output)]

        elif name == "search_satellite_data_structured":
            # Structured search
            hub = get_hub()
            geocoder = get_geocoder()

            # Build request
            bbox = None
            if "bbox" in arguments and arguments["bbox"]:
                bbox = tuple(arguments["bbox"])
            elif "location" in arguments and arguments["location"]:
                geo_result = geocoder.geocode(arguments["location"])
                if geo_result:
                    bbox = geo_result.get("bbox")

            request = DataRequest(
                product=arguments.get("product"),
                bbox=bbox,
                start_date=arguments.get("start_date"),
                end_date=arguments.get("end_date"),
                cloud_cover_max=arguments.get("cloud_cover_max"),
                limit=arguments.get("limit", 10)
            )

            # Execute search
            results = hub.search(request)
            _last_search_results = results

            # Format output
            output = f"Search parameters: {request}\n\n"
            output += format_results_for_display(results)

            if results:
                output += f"\n\nUse download_satellite_data with result_index (1-{len(results)}) to download."

            return [TextContent(type="text", text=output)]

        elif name == "download_satellite_data":
            # Download from previous search
            result_index = arguments.get("result_index", 1)
            output_dir = arguments.get("output_dir", "f:\\Automating_data_portal\\downloads")

            if not _last_search_results:
                return [TextContent(type="text", text="No previous search results. Please search first.")]

            if result_index < 1 or result_index > len(_last_search_results):
                return [TextContent(type="text", text=f"Invalid index. Choose between 1 and {len(_last_search_results)}.")]

            result = _last_search_results[result_index - 1]
            hub = get_hub()

            output = f"Downloading: {result.title}\n"
            output += f"Product ID: {result.id}\n"
            output += f"Output directory: {output_dir}\n\n"

            try:
                path = hub.download(result, output_dir)
                output += f"Download complete!\nSaved to: {path}"
            except Exception as e:
                output += f"Download failed: {str(e)}"

            return [TextContent(type="text", text=output)]

        elif name == "list_data_providers":
            hub = get_hub()
            providers = hub.list_providers()

            output = f"Available Data Providers ({len(providers)}):\n\n"
            for provider in providers:
                output += f"  - {provider}\n"

            output += "\nNote: cop_dataspace (Copernicus) is configured as primary provider."

            return [TextContent(type="text", text=output)]

        elif name == "list_products":
            hub = get_hub()
            provider = arguments.get("provider")
            products = hub.list_products(provider=provider)

            output = f"Available Products"
            if provider:
                output += f" (from {provider})"
            output += f" ({len(products)} total):\n\n"

            # Group common products
            common_products = {
                "S2_MSI_L2A": "Sentinel-2 Level-2A (optical, 10m resolution)",
                "S1_SAR_GRD": "Sentinel-1 SAR Ground Range Detected",
                "LANDSAT_C2L2": "Landsat 8/9 Collection 2 Level-2",
                "COP-DEM_GLO-30": "Copernicus DEM 30m"
            }

            output += "Common Products:\n"
            for pid, desc in common_products.items():
                output += f"  - {pid}: {desc}\n"

            output += f"\nTotal {len(products)} product types available. Use search with specific product codes."

            return [TextContent(type="text", text=output)]

        elif name == "geocode_location":
            location = arguments.get("location", "")
            geocoder = get_geocoder()

            result = geocoder.geocode(location)

            if result:
                output = f"Location: {location}\n"
                output += f"Display Name: {result.get('display_name', 'N/A')}\n"
                output += f"Coordinates: ({result.get('lat', 'N/A')}, {result.get('lon', 'N/A')})\n"
                output += f"Bounding Box: {result.get('bbox', 'N/A')}\n"
            else:
                output = f"Could not geocode location: {location}"

            return [TextContent(type="text", text=output)]

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

    except Exception as e:
        return [TextContent(type="text", text=f"Error executing {name}: {str(e)}")]


async def main():
    """Run the MCP server."""
    async with stdio_server() as (read_stream, write_stream):
        await mcp_server.run(
            read_stream,
            write_stream,
            mcp_server.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
