#!/usr/bin/env python
"""
Basic usage examples for GeoDataHub
"""

from geodatahub import GeoDataHub, NLParser, search_natural_language
from geodatahub.models.request import DataRequest, DataType


def example_1_natural_language():
    """Example 1: Simple natural language search"""
    print("=" * 80)
    print("Example 1: Natural Language Search")
    print("=" * 80)

    # Use the convenience function
    results = search_natural_language(
        "Sentinel-2 images of Paris from January 2024 with less than 20% cloud cover"
    )

    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results[:3], 1):
        print(f"\n{i}. {result.title}")
        print(f"   Date: {result.datetime[:10]}")
        print(f"   Cloud Cover: {result.cloud_cover}%")
        print(f"   Provider: {result.provider}")


def example_2_explicit_parameters():
    """Example 2: Using explicit parameters"""
    print("\n" + "=" * 80)
    print("Example 2: Explicit Parameters")
    print("=" * 80)

    hub = GeoDataHub()

    request = DataRequest(
        product="S2_MSI_L2A",
        bbox=(2.25, 48.81, 2.42, 48.90),  # Paris bounding box
        start_date="2024-01-01",
        end_date="2024-01-31",
        cloud_cover_max=20.0,
        limit=5
    )

    print(f"\nSearching with: {request}")
    results = hub.search(request)

    print(f"\nFound {len(results)} results:")
    for i, result in enumerate(results, 1):
        print(f"{i}. {result.title} - {result.datetime[:10]}")


def example_3_location_based_search():
    """Example 3: Location-based search using geocoding"""
    print("\n" + "=" * 80)
    print("Example 3: Location-Based Search")
    print("=" * 80)

    parser = NLParser()

    # Parse query with location
    request = parser.parse("Get Landsat 8 data for New York from last month")

    print(f"\nParsed request:")
    print(f"  Product: {request.product}")
    print(f"  Location: {request.location_name}")
    print(f"  BBox: {request.bbox}")
    print(f"  Dates: {request.start_date} to {request.end_date}")

    hub = GeoDataHub()
    results = hub.search(request)

    print(f"\nFound {len(results)} results")


def example_4_different_data_types():
    """Example 4: Searching for different data types"""
    print("\n" + "=" * 80)
    print("Example 4: Different Data Types")
    print("=" * 80)

    queries = [
        "Sentinel-1 SAR data for Tokyo from last week",
        "DEM data for Mount Everest",
        "Land cover data for Amazon rainforest"
    ]

    for query in queries:
        print(f"\nQuery: {query}")
        results = search_natural_language(query)
        if results:
            print(f"  Product: {results[0].product_type}")
            print(f"  Data Type: {results[0].data_type.value}")
            print(f"  Found: {len(results)} results")


def example_5_download():
    """Example 5: Downloading data (commented out - requires authentication)"""
    print("\n" + "=" * 80)
    print("Example 5: Downloading Data (demonstration only)")
    print("=" * 80)

    hub = GeoDataHub()

    # Search first
    request = DataRequest(
        product="S2_MSI_L2A",
        location_name="Paris",
        start_date="2024-01-15",
        end_date="2024-01-16",
        cloud_cover_max=10,
        limit=1
    )

    results = hub.search(request)

    if results:
        print(f"\nFound: {results[0].title}")
        print(f"Size: {results[0].size_mb} MB")
        print(f"\nTo download, uncomment the following line:")
        print(f"# paths = hub.download_all(results, './data')")

        # Uncomment to actually download (requires provider authentication)
        # paths = hub.download_all(results, './data')
        # print(f"Downloaded to: {paths}")
    else:
        print("No results found")


def example_6_list_resources():
    """Example 6: List available products and providers"""
    print("\n" + "=" * 80)
    print("Example 6: List Resources")
    print("=" * 80)

    hub = GeoDataHub()

    # List providers
    print("\nAvailable providers:")
    providers = hub.list_providers()
    for provider in providers[:10]:  # Show first 10
        print(f"  - {provider}")

    # List products
    print("\nAvailable products (first 10):")
    products = hub.list_products()
    for product in products[:10]:
        product_id = product.get('ID', product.get('id', 'Unknown'))
        print(f"  - {product_id}")


if __name__ == "__main__":
    print("\nGeoDataHub Examples")
    print("=" * 80)
    print("\nNote: Some examples require EODAG provider configuration.")
    print("Configure providers in: ~/.config/eodag/eodag.yml")
    print()

    try:
        example_1_natural_language()
        example_2_explicit_parameters()
        example_3_location_based_search()
        example_4_different_data_types()
        example_5_download()
        example_6_list_resources()

        print("\n" + "=" * 80)
        print("Examples completed!")
        print("=" * 80)

    except Exception as e:
        print(f"\nError running examples: {e}")
        print("\nMake sure you have:")
        print("  1. Installed geodatahub: pip install -e .")
        print("  2. Configured EODAG providers (see config/eodag.yml.example)")
