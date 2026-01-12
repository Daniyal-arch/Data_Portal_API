from geodatahub.core.downloader import GeoDataHub
from geodatahub.nlp.parser import NLParser
from geodatahub.models.request import DataRequest, DataType, OutputFormat
from geodatahub.models.result import SearchResult

__version__ = "0.1.0"
__all__ = ['GeoDataHub', 'NLParser', 'DataRequest', 'DataType', 'OutputFormat', 'SearchResult', 'search_natural_language']

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
