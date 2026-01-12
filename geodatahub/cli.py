#!/usr/bin/env python
"""
GeoDataHub Command Line Interface

A unified CLI for searching and downloading geospatial data using natural language.

Usage:
    geodatahub search "Sentinel-2 images of Paris from last month"
    geodatahub download "Sentinel-2 images of London" -o ./data
    geodatahub list products
    geodatahub list providers
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List

try:
    from geodatahub import GeoDataHub, NLParser, DataRequest
    from geodatahub.models.result import SearchResult
except ImportError:
    print("Error: geodatahub package not found. Please install it first:")
    print("  pip install -e .")
    sys.exit(1)


def format_result(result: SearchResult, index: int) -> str:
    """Format a search result for display"""
    lines = [
        f"\n{index}. {result.title}",
        f"   ID: {result.id}",
        f"   Provider: {result.provider} | Type: {result.product_type}",
        f"   Date: {result.datetime[:10] if result.datetime else 'Unknown'}"
    ]

    if result.cloud_cover is not None:
        lines.append(f"   Cloud Cover: {result.cloud_cover:.1f}%")

    if result.bbox:
        lines.append(f"   BBox: {result.bbox}")

    if result.thumbnail_url:
        lines.append(f"   Preview: {result.thumbnail_url}")

    if result.size_mb:
        lines.append(f"   Size: {result.size_mb:.1f} MB")

    return "\n".join(lines)


def cmd_search(args):
    """Handle search command"""
    hub = GeoDataHub()
    nl_parser = NLParser()

    # Build request from either natural language or explicit parameters
    if args.query:
        print(f"Parsing query: '{args.query}'")
        request = nl_parser.parse(args.query)

        # Override with explicit parameters if provided
        if args.product:
            request.product = args.product
        if args.bbox:
            request.bbox = tuple(args.bbox)
        if args.location:
            request.location_name = args.location
        if args.start:
            request.start_date = args.start
        if args.end:
            request.end_date = args.end
        if args.cloud is not None:
            request.cloud_cover_max = args.cloud
        if args.limit:
            request.limit = args.limit

    else:
        # Build request from explicit parameters only
        request = DataRequest(
            product=args.product,
            bbox=tuple(args.bbox) if args.bbox else None,
            location_name=args.location,
            start_date=args.start,
            end_date=args.end,
            cloud_cover_max=args.cloud,
            limit=args.limit or 10
        )

    print(f"\nSearching with: {request}\n")
    print("=" * 80)

    # Execute search
    results = hub.search(request)

    # Display results
    if not results:
        print("\nNo results found.")
        return

    print(f"\nFound {len(results)} results:")
    print("=" * 80)

    for i, result in enumerate(results, 1):
        print(format_result(result, i))

    print("\n" + "=" * 80)

    # Save to file if requested
    if args.output:
        output_path = Path(args.output)
        results_data = [r.to_dict() for r in results]

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_data, f, indent=2, default=str)

        print(f"\nResults saved to: {output_path}")


def cmd_download(args):
    """Handle download command"""
    hub = GeoDataHub()
    nl_parser = NLParser()

    # Parse query
    print(f"Parsing query: '{args.query}'")
    request = nl_parser.parse(args.query)

    # Override limit if specified
    if args.limit:
        request.limit = args.limit

    print(f"\nSearching with: {request}\n")

    # Search for products
    results = hub.search(request)

    if not results:
        print("No results found.")
        return

    print(f"Found {len(results)} products")

    # Ask for confirmation
    if not args.yes:
        print("\nProducts to download:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result.title} ({result.datetime[:10]})")

        response = input(f"\nDownload {len(results)} products to '{args.output_dir}'? [y/N] ")
        if response.lower() not in ['y', 'yes']:
            print("Download cancelled.")
            return

    # Download
    print(f"\nDownloading to: {args.output_dir}")
    print("=" * 80)

    paths = hub.download_all(results, args.output_dir)

    print("\n" + "=" * 80)
    print(f"\nSuccessfully downloaded {len(paths)} out of {len(results)} products")

    if paths:
        print("\nDownloaded files:")
        for path in paths:
            print(f"  - {path}")


def cmd_list(args):
    """Handle list command"""
    hub = GeoDataHub()

    if args.type == 'products':
        print("Listing available products...")
        print("=" * 80)

        products = hub.list_products(provider=args.provider)

        if not products:
            print("No products found.")
            return

        print(f"\nFound {len(products)} product types:\n")

        for product in products:
            product_id = product.get('ID', product.get('id', 'Unknown'))
            title = product.get('title', product.get('productType', ''))
            provider = product.get('provider', '')

            print(f"  {product_id}")
            if title and title != product_id:
                print(f"    Title: {title}")
            if provider:
                print(f"    Provider: {provider}")
            print()

    elif args.type == 'providers':
        print("Listing available providers...")
        print("=" * 80)

        providers = hub.list_providers()

        if not providers:
            print("No providers found.")
            return

        print(f"\nFound {len(providers)} providers:\n")

        for provider in providers:
            print(f"  - {provider}")

    print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='GeoData Hub - Unified Geospatial Data Download',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Search using natural language
  geodatahub search "Sentinel-2 images of Paris from January 2024 with less than 20%% cloud cover"

  # Search with explicit parameters
  geodatahub search --product S2_MSI_L2A --location "London" --start 2024-01-01 --end 2024-01-31

  # Download data
  geodatahub download "Sentinel-2 images of London from last week" -o ./data

  # List available products and providers
  geodatahub list products
  geodatahub list providers
        '''
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Search command
    search_parser = subparsers.add_parser('search', help='Search for geospatial data')
    search_parser.add_argument(
        'query',
        nargs='?',
        help='Natural language query (e.g., "Sentinel-2 images of Paris from last month")'
    )
    search_parser.add_argument(
        '--product', '-p',
        help='Product type (e.g., S2_MSI_L2A, LANDSAT_C2L2)'
    )
    search_parser.add_argument(
        '--bbox', '-b',
        nargs=4,
        type=float,
        metavar=('MINX', 'MINY', 'MAXX', 'MAXY'),
        help='Bounding box coordinates'
    )
    search_parser.add_argument(
        '--location', '-l',
        help='Location name (will be geocoded)'
    )
    search_parser.add_argument(
        '--start', '-s',
        help='Start date (YYYY-MM-DD)'
    )
    search_parser.add_argument(
        '--end', '-e',
        help='End date (YYYY-MM-DD)'
    )
    search_parser.add_argument(
        '--cloud', '-c',
        type=float,
        help='Maximum cloud cover percentage (0-100)'
    )
    search_parser.add_argument(
        '--limit', '-n',
        type=int,
        default=10,
        help='Maximum number of results (default: 10)'
    )
    search_parser.add_argument(
        '--output', '-o',
        help='Save results to JSON file'
    )
    search_parser.set_defaults(func=cmd_search)

    # Download command
    dl_parser = subparsers.add_parser('download', help='Download geospatial data')
    dl_parser.add_argument(
        'query',
        help='Natural language query or search criteria'
    )
    dl_parser.add_argument(
        '--output-dir', '-o',
        required=True,
        help='Output directory for downloaded files'
    )
    dl_parser.add_argument(
        '--limit', '-n',
        type=int,
        help='Maximum number of products to download'
    )
    dl_parser.add_argument(
        '--yes', '-y',
        action='store_true',
        help='Skip confirmation prompt'
    )
    dl_parser.set_defaults(func=cmd_download)

    # List command
    list_parser = subparsers.add_parser('list', help='List available products or providers')
    list_parser.add_argument(
        'type',
        choices=['products', 'providers'],
        help='What to list'
    )
    list_parser.add_argument(
        '--provider', '-p',
        help='Filter products by provider'
    )
    list_parser.set_defaults(func=cmd_list)

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Execute command
    try:
        args.func(args)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
