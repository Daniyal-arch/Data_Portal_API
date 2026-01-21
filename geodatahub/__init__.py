from geodatahub.core.downloader import GeoDataHub
from geodatahub.nlp.parser import NLParser
from geodatahub.models.request import DataRequest, DataType, OutputFormat
from geodatahub.models.result import SearchResult

# EODAG catalog and provider management
from geodatahub.eodag_catalog import (
    EODAG_PROVIDERS, EODAG_PRODUCTS,
    get_providers_for_product, get_products_for_provider,
    search_products as search_eodag_products,
    get_catalog_summary
)
from geodatahub.provider_config import (
    ProviderConfigManager, get_config_manager,
    check_product_access, get_setup_instructions
)
from geodatahub.workflows import (
    ANALYSIS_WORKFLOWS, SPECTRAL_INDICES,
    match_workflow, get_workflow_recommendation, get_qgis_formula
)

__version__ = "0.1.0"
__all__ = [
    # Core
    'GeoDataHub', 'NLParser', 'DataRequest', 'DataType', 'OutputFormat', 'SearchResult',
    'search_natural_language',
    # EODAG Catalog
    'EODAG_PROVIDERS', 'EODAG_PRODUCTS',
    'get_providers_for_product', 'get_products_for_provider',
    'search_eodag_products', 'get_catalog_summary',
    # Provider Config
    'ProviderConfigManager', 'get_config_manager',
    'check_product_access', 'get_setup_instructions',
    # Workflows
    'ANALYSIS_WORKFLOWS', 'SPECTRAL_INDICES',
    'match_workflow', 'get_workflow_recommendation', 'get_qgis_formula'
]

def search_natural_language(query: str, **kwargs):
    """
    Convenience function for natural language search.

    Args:
        query: Natural language query (e.g., "Sentinel-2 images of Paris from last month")
        **kwargs: Additional parameters to override parsed values

    Returns:
        List of SearchResult objects

    Example:
        >>> results = search_natural_language("Sentinel-2 images of London from January 2024")
        >>> for result in results:
        ...     print(result.title, result.datetime)
    """
    parser = NLParser()
    request = parser.parse(query)

    # Override with any explicit kwargs
    for key, value in kwargs.items():
        if hasattr(request, key):
            setattr(request, key, value)

    hub = GeoDataHub()
    return hub.search(request)
