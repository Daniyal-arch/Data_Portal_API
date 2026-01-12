#!/usr/bin/env python
"""
Example client for GeoDataHub REST API
"""

import requests
import json


class GeoDataHubClient:
    """Simple Python client for GeoDataHub API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip('/')

    def search_nl(self, query: str, limit: int = 10):
        """Search using natural language"""
        response = requests.get(
            f"{self.base_url}/search/nl",
            params={"q": query, "limit": limit}
        )
        response.raise_for_status()
        return response.json()

    def search(self, **kwargs):
        """Search with explicit parameters"""
        response = requests.post(
            f"{self.base_url}/search",
            json=kwargs
        )
        response.raise_for_status()
        return response.json()

    def list_products(self, provider=None):
        """List available products"""
        params = {"provider": provider} if provider else {}
        response = requests.get(
            f"{self.base_url}/products",
            params=params
        )
        response.raise_for_status()
        return response.json()

    def list_providers(self):
        """List available providers"""
        response = requests.get(f"{self.base_url}/providers")
        response.raise_for_status()
        return response.json()


def main():
    """Example usage"""
    print("GeoDataHub API Client Examples")
    print("=" * 80)
    print("\nMake sure the API is running:")
    print("  uvicorn geodatahub_api.main:app --reload\n")

    client = GeoDataHubClient()

    # Example 1: Natural language search
    print("Example 1: Natural Language Search")
    print("-" * 80)
    try:
        result = client.search_nl(
            "Sentinel-2 images of Paris from January 2024 with less than 20% clouds",
            limit=5
        )
        print(f"Query: {result['query']}")
        print(f"Found: {result['count']} results")
        print(f"Parsed parameters: {json.dumps(result['parsed'], indent=2)}")

        if result['results']:
            print(f"\nFirst result:")
            first = result['results'][0]
            print(f"  Title: {first['title']}")
            print(f"  Date: {first['datetime'][:10]}")
            print(f"  Cloud Cover: {first.get('cloud_cover')}%")

    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API. Is it running?")
        return
    except Exception as e:
        print(f"Error: {e}")
        return

    # Example 2: Explicit parameters
    print("\n\nExample 2: Search with Explicit Parameters")
    print("-" * 80)
    try:
        result = client.search(
            product="S2_MSI_L2A",
            location="London",
            start_date="2024-01-01",
            end_date="2024-01-31",
            cloud_cover_max=15,
            limit=3
        )
        print(f"Found: {result['count']} results")

        for i, item in enumerate(result['results'], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   Date: {item['datetime'][:10]}")
            print(f"   Provider: {item['provider']}")

    except Exception as e:
        print(f"Error: {e}")

    # Example 3: List resources
    print("\n\nExample 3: List Available Resources")
    print("-" * 80)
    try:
        # List providers
        providers = client.list_providers()
        print(f"Providers ({providers['count']}):")
        for provider in providers['providers'][:5]:
            print(f"  - {provider}")

        # List products
        products = client.list_products()
        print(f"\nProducts ({products['count']}):")
        for product in products['products'][:5]:
            print(f"  - {product['id']}: {product.get('title', 'N/A')}")

    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
