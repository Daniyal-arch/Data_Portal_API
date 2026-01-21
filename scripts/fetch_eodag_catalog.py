"""
Fetch complete EODAG catalog - all providers and products.
Run this script to generate the full catalog JSON.
"""

from eodag import EODataAccessGateway
import json
from pathlib import Path

def fetch_eodag_catalog():
    """Fetch all providers and products from EODAG."""

    print("Initializing EODAG...")
    dag = EODataAccessGateway()

    # Get all providers
    providers = dag.available_providers()
    print(f"Found {len(providers)} providers")

    # Get all product types
    product_types = dag.list_product_types(fetch_providers=False)
    print(f"Found {len(product_types)} product types (internal catalog)")

    # Fetch extended catalog from providers
    try:
        extended_types = dag.list_product_types(fetch_providers=True)
        print(f"Found {len(extended_types)} product types (extended catalog)")
    except Exception as e:
        print(f"Could not fetch extended catalog: {e}")
        extended_types = product_types

    # Build catalog structure
    catalog = {
        "providers": {},
        "products": {},
        "provider_products": {}  # Which products each provider offers
    }

    # Provider details
    for provider in providers:
        try:
            # Get provider config
            provider_config = dag.providers_config.get(provider, {})
            catalog["providers"][provider] = {
                "name": provider,
                "description": getattr(provider_config, 'description', ''),
                "url": getattr(provider_config, 'url', ''),
                "requires_auth": True,  # Most require auth
                "configured": False  # Will be updated by app
            }
        except Exception as e:
            catalog["providers"][provider] = {
                "name": provider,
                "description": "",
                "requires_auth": True,
                "configured": False
            }

    # Product details
    for product in extended_types:
        product_id = product.get('ID', product.get('id', 'unknown'))
        catalog["products"][product_id] = {
            "id": product_id,
            "title": product.get('title', product.get('productType', product_id)),
            "description": product.get('abstract', product.get('description', '')),
            "platform": product.get('platform', ''),
            "instrument": product.get('instrument', ''),
            "processing_level": product.get('processingLevel', ''),
            "sensor_type": product.get('sensorType', ''),
            "providers": []  # Will be populated below
        }

    # Map products to providers
    for provider in providers:
        try:
            provider_products = dag.list_product_types(provider=provider)
            product_ids = [p.get('ID', p.get('id')) for p in provider_products]
            catalog["provider_products"][provider] = product_ids

            # Update products with provider info
            for pid in product_ids:
                if pid in catalog["products"]:
                    catalog["products"][pid]["providers"].append(provider)
        except Exception as e:
            print(f"Could not get products for {provider}: {e}")
            catalog["provider_products"][provider] = []

    return catalog


def save_catalog(catalog, output_path):
    """Save catalog to JSON file."""
    with open(output_path, 'w') as f:
        json.dump(catalog, f, indent=2)
    print(f"Catalog saved to {output_path}")


def generate_python_module(catalog, output_path):
    """Generate Python module with catalog data."""

    code = '''"""
EODAG Complete Catalog - Auto-generated
Contains all providers and products from EODAG.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class ProviderInfo:
    """EODAG Provider information."""
    name: str
    description: str = ""
    url: str = ""
    requires_auth: bool = True
    configured: bool = False
    auth_guide: str = ""


@dataclass
class ProductInfo:
    """EODAG Product information."""
    id: str
    title: str
    description: str = ""
    platform: str = ""
    instrument: str = ""
    processing_level: str = ""
    sensor_type: str = ""
    providers: List[str] = field(default_factory=list)


# =============================================================================
# PROVIDERS
# =============================================================================

EODAG_PROVIDERS: Dict[str, ProviderInfo] = {
'''

    # Add providers
    for provider_id, provider in catalog["providers"].items():
        code += f'''    "{provider_id}": ProviderInfo(
        name="{provider['name']}",
        description="""{provider.get('description', '')}""",
        requires_auth={provider.get('requires_auth', True)},
    ),
'''

    code += '''}


# =============================================================================
# PRODUCTS
# =============================================================================

EODAG_PRODUCTS: Dict[str, ProductInfo] = {
'''

    # Add products
    for product_id, product in catalog["products"].items():
        providers_list = product.get('providers', [])
        code += f'''    "{product_id}": ProductInfo(
        id="{product_id}",
        title="""{product.get('title', '')}""",
        description="""{product.get('description', '')[:200]}""",
        platform="{product.get('platform', '')}",
        instrument="{product.get('instrument', '')}",
        processing_level="{product.get('processing_level', '')}",
        sensor_type="{product.get('sensor_type', '')}",
        providers={providers_list},
    ),
'''

    code += '''}


# =============================================================================
# PROVIDER-PRODUCT MAPPING
# =============================================================================

PROVIDER_PRODUCTS: Dict[str, List[str]] = {
'''

    # Add provider-product mapping
    for provider, products in catalog["provider_products"].items():
        code += f'''    "{provider}": {products},
'''

    code += '''}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_providers_for_product(product_id: str) -> List[str]:
    """Get all providers that offer a specific product."""
    if product_id in EODAG_PRODUCTS:
        return EODAG_PRODUCTS[product_id].providers
    return []


def get_products_for_provider(provider: str) -> List[str]:
    """Get all products offered by a specific provider."""
    return PROVIDER_PRODUCTS.get(provider, [])


def get_configured_providers() -> List[str]:
    """Get list of configured providers."""
    return [p for p, info in EODAG_PROVIDERS.items() if info.configured]


def get_alternative_providers(product_id: str, exclude_provider: str = None) -> List[str]:
    """Get alternative providers for a product."""
    providers = get_providers_for_product(product_id)
    if exclude_provider:
        providers = [p for p in providers if p != exclude_provider]
    return providers


def search_products(keyword: str) -> List[ProductInfo]:
    """Search products by keyword."""
    keyword = keyword.lower()
    results = []
    for product in EODAG_PRODUCTS.values():
        if (keyword in product.id.lower() or
            keyword in product.title.lower() or
            keyword in product.description.lower() or
            keyword in product.platform.lower()):
            results.append(product)
    return results
'''

    with open(output_path, 'w') as f:
        f.write(code)
    print(f"Python module saved to {output_path}")


if __name__ == "__main__":
    # Output paths
    output_dir = Path(__file__).parent.parent / "geodatahub"
    json_path = output_dir / "eodag_catalog.json"
    python_path = output_dir / "eodag_catalog.py"

    # Fetch and save
    catalog = fetch_eodag_catalog()
    save_catalog(catalog, json_path)
    generate_python_module(catalog, python_path)

    # Summary
    print("\n=== SUMMARY ===")
    print(f"Providers: {len(catalog['providers'])}")
    print(f"Products: {len(catalog['products'])}")
    print(f"\nProvider list:")
    for p in catalog['providers']:
        products_count = len(catalog['provider_products'].get(p, []))
        print(f"  - {p}: {products_count} products")
