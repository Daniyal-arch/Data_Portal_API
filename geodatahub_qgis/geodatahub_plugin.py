"""
GeoDataHub QGIS Plugin - Main Plugin Class

This module contains the main plugin class that integrates with QGIS.
"""

import os
import sys

from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QToolBar
from qgis.core import QgsProject, QgsRasterLayer, QgsMessageLog, Qgis

# Add parent directory to path for geodatahub imports
plugin_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(plugin_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


class GeoDataHubPlugin:
    """
    QGIS Plugin Implementation for GeoDataHub.

    Provides AI-powered satellite data search and download with natural
    language queries and smart dataset recommendations.
    """

    def __init__(self, iface):
        """
        Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface

        # Initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # Initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'geodatahub_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&GeoDataHub')
        self.toolbar = self.iface.addToolBar('GeoDataHub')
        self.toolbar.setObjectName('GeoDataHub')

        # Dialog instance
        self.dlg = None

        # Initialize GeoDataHub core (lazy loading)
        self._hub = None
        self._parser = None

    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('GeoDataHub', message)

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None
    ):
        """Add a toolbar icon to the toolbar."""
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToRasterMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = os.path.join(self.plugin_dir, 'icons', 'icon.png')

        # Main search action
        self.add_action(
            icon_path,
            text=self.tr('GeoDataHub - Search Satellite Data'),
            callback=self.run,
            parent=self.iface.mainWindow(),
            status_tip=self.tr('Search and download satellite data using natural language')
        )

        # AI Recommendations action
        self.add_action(
            icon_path,
            text=self.tr('AI Dataset Recommendations'),
            callback=self.run_recommendations,
            parent=self.iface.mainWindow(),
            status_tip=self.tr('Get AI-powered dataset recommendations for your analysis')
        )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginRasterMenu(
                self.tr('&GeoDataHub'),
                action)
            self.iface.removeToolBarIcon(action)

        # Remove the toolbar
        del self.toolbar

    def get_hub(self):
        """Lazy load GeoDataHub instance."""
        if self._hub is None:
            try:
                from geodatahub import GeoDataHub
                self._hub = GeoDataHub()
            except ImportError as e:
                self.log_message(f"Failed to import GeoDataHub: {e}", Qgis.Critical)
                return None
        return self._hub

    def get_parser(self):
        """Lazy load NLParser instance."""
        if self._parser is None:
            try:
                from geodatahub import NLParser
                self._parser = NLParser()
            except ImportError as e:
                self.log_message(f"Failed to import NLParser: {e}", Qgis.Critical)
                return None
        return self._parser

    def log_message(self, message, level=Qgis.Info):
        """Log a message to QGIS message log."""
        QgsMessageLog.logMessage(message, 'GeoDataHub', level)

    def get_canvas_extent(self):
        """Get the current map canvas extent as bbox tuple."""
        canvas = self.iface.mapCanvas()
        extent = canvas.extent()

        # Transform to WGS84 if needed
        crs = canvas.mapSettings().destinationCrs()
        if crs.authid() != 'EPSG:4326':
            from qgis.core import QgsCoordinateTransform, QgsCoordinateReferenceSystem
            transform = QgsCoordinateTransform(
                crs,
                QgsCoordinateReferenceSystem('EPSG:4326'),
                QgsProject.instance()
            )
            extent = transform.transformBoundingBox(extent)

        return (extent.xMinimum(), extent.yMinimum(),
                extent.xMaximum(), extent.yMaximum())

    def add_raster_layer(self, file_path, layer_name=None):
        """Add a downloaded raster file as a QGIS layer."""
        if not os.path.exists(file_path):
            self.log_message(f"File not found: {file_path}", Qgis.Warning)
            return None

        if layer_name is None:
            layer_name = os.path.basename(file_path)

        layer = QgsRasterLayer(file_path, layer_name)

        if layer.isValid():
            QgsProject.instance().addMapLayer(layer)
            self.log_message(f"Added layer: {layer_name}")
            return layer
        else:
            self.log_message(f"Failed to load layer: {file_path}", Qgis.Warning)
            return None

    def run(self):
        """Run method that performs the main plugin action."""
        # Import dialog here to avoid import errors at plugin load time
        from .geodatahub_dialog import GeoDataHubDialog

        # Create the dialog if not exists
        if self.dlg is None:
            self.dlg = GeoDataHubDialog(
                parent=self.iface.mainWindow(),
                plugin=self
            )

        # Show the dialog
        self.dlg.show()

        # Run the dialog event loop
        result = self.dlg.exec_()

        # Handle dialog result if needed
        if result:
            pass  # User clicked OK/Download

    def run_recommendations(self):
        """Run the AI recommendations dialog."""
        from .recommendation_dialog import RecommendationDialog

        dlg = RecommendationDialog(
            parent=self.iface.mainWindow(),
            plugin=self
        )
        dlg.show()
        dlg.exec_()
