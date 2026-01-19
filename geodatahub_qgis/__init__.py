"""
GeoDataHub QGIS Plugin

AI-powered satellite data search and download with natural language queries.
"""


def classFactory(iface):
    """
    Load GeoDataHubPlugin class from file geodatahub_plugin.

    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    from .geodatahub_plugin import GeoDataHubPlugin
    return GeoDataHubPlugin(iface)
