"""
GeoDataHub Search Dialog

Main dialog for searching and downloading satellite data.
"""

import os
from datetime import datetime, timedelta

from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QTableWidget, QTableWidgetItem, QProgressBar,
    QComboBox, QSpinBox, QDoubleSpinBox, QGroupBox, QCheckBox,
    QFileDialog, QMessageBox, QHeaderView, QAbstractItemView,
    QDateEdit, QTextEdit, QSplitter, QWidget, QTabWidget
)
from qgis.PyQt.QtGui import QFont
from qgis.core import Qgis


class SearchWorker(QThread):
    """Background worker for search operations."""

    finished = pyqtSignal(list)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)

    def __init__(self, hub, parser, query, limit, bbox=None):
        super().__init__()
        self.hub = hub
        self.parser = parser
        self.query = query
        self.limit = limit
        self.bbox = bbox

    def run(self):
        try:
            self.progress.emit("Parsing query...")

            # Parse natural language query
            request = self.parser.parse(self.query)
            request.limit = self.limit

            # Override bbox if provided
            if self.bbox:
                request.bbox = self.bbox

            self.progress.emit("Searching for data...")

            # Execute search
            results = self.hub.search(request)

            self.finished.emit(results)

        except Exception as e:
            self.error.emit(str(e))


class DownloadWorker(QThread):
    """Background worker for download operations."""

    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    progress = pyqtSignal(str, int)

    def __init__(self, hub, result, output_dir):
        super().__init__()
        self.hub = hub
        self.result = result
        self.output_dir = output_dir

    def run(self):
        try:
            self.progress.emit(f"Downloading {self.result.title}...", 0)

            # Download
            file_path = self.hub.download(self.result, self.output_dir)

            self.progress.emit("Download complete!", 100)
            self.finished.emit(str(file_path))

        except Exception as e:
            self.error.emit(str(e))


class GeoDataHubDialog(QDialog):
    """Main dialog for GeoDataHub plugin."""

    def __init__(self, parent=None, plugin=None):
        super().__init__(parent)
        self.plugin = plugin
        self.search_results = []
        self.search_worker = None
        self.download_worker = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("GeoDataHub - Satellite Data Search")
        self.setMinimumSize(800, 600)

        layout = QVBoxLayout(self)

        # Create tab widget
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: Natural Language Search
        nl_tab = self.create_nl_search_tab()
        tabs.addTab(nl_tab, "Natural Language Search")

        # Tab 2: Advanced Search
        adv_tab = self.create_advanced_search_tab()
        tabs.addTab(adv_tab, "Advanced Search")

        # Results section (shared)
        results_group = self.create_results_section()
        layout.addWidget(results_group)

        # Progress and status
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Ready")
        layout.addWidget(self.status_label)

        # Bottom buttons
        button_layout = QHBoxLayout()

        self.download_btn = QPushButton("Download Selected")
        self.download_btn.clicked.connect(self.download_selected)
        self.download_btn.setEnabled(False)
        button_layout.addWidget(self.download_btn)

        self.add_layer_btn = QPushButton("Download && Add to Map")
        self.add_layer_btn.clicked.connect(self.download_and_add_layer)
        self.add_layer_btn.setEnabled(False)
        button_layout.addWidget(self.add_layer_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def create_nl_search_tab(self):
        """Create the natural language search tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Instructions
        instructions = QLabel(
            "Enter a natural language query to search for satellite data.\n"
            "Examples:\n"
            "  • Sentinel-2 images of Paris from January 2024 with less than 20% cloud cover\n"
            "  • Landsat 8 data for London from last month\n"
            "  • DEM data for Mount Everest"
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Search input
        search_layout = QHBoxLayout()

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter your search query...")
        self.search_input.returnPressed.connect(self.search_nl)
        search_layout.addWidget(self.search_input)

        self.search_btn = QPushButton("Search")
        self.search_btn.clicked.connect(self.search_nl)
        search_layout.addWidget(self.search_btn)

        layout.addLayout(search_layout)

        # Options
        options_layout = QHBoxLayout()

        options_layout.addWidget(QLabel("Max Results:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 100)
        self.limit_spin.setValue(10)
        options_layout.addWidget(self.limit_spin)

        self.use_extent_cb = QCheckBox("Use current map extent")
        self.use_extent_cb.setChecked(False)
        options_layout.addWidget(self.use_extent_cb)

        options_layout.addStretch()

        layout.addLayout(options_layout)
        layout.addStretch()

        return widget

    def create_advanced_search_tab(self):
        """Create the advanced search tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Product selection
        product_layout = QHBoxLayout()
        product_layout.addWidget(QLabel("Product:"))

        self.product_combo = QComboBox()
        self.product_combo.addItems([
            "S2_MSI_L2A - Sentinel-2 Level 2A",
            "S1_SAR_GRD - Sentinel-1 SAR",
            "LANDSAT_C2L2 - Landsat 8/9",
            "COP-DEM_GLO-30 - Copernicus DEM"
        ])
        product_layout.addWidget(self.product_combo)
        product_layout.addStretch()

        layout.addLayout(product_layout)

        # Location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Location:"))

        self.location_input = QLineEdit()
        self.location_input.setPlaceholderText("Enter location name (e.g., Paris, France)")
        location_layout.addWidget(self.location_input)

        self.use_extent_adv_cb = QCheckBox("Use map extent")
        location_layout.addWidget(self.use_extent_adv_cb)

        layout.addLayout(location_layout)

        # Date range
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date Range:"))

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate((datetime.now() - timedelta(days=30)).date())
        date_layout.addWidget(self.start_date)

        date_layout.addWidget(QLabel("to"))

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(datetime.now().date())
        date_layout.addWidget(self.end_date)

        date_layout.addStretch()

        layout.addLayout(date_layout)

        # Cloud cover
        cloud_layout = QHBoxLayout()
        cloud_layout.addWidget(QLabel("Max Cloud Cover (%):"))

        self.cloud_spin = QDoubleSpinBox()
        self.cloud_spin.setRange(0, 100)
        self.cloud_spin.setValue(20)
        cloud_layout.addWidget(self.cloud_spin)

        cloud_layout.addStretch()

        layout.addLayout(cloud_layout)

        # Search button
        search_adv_btn = QPushButton("Search")
        search_adv_btn.clicked.connect(self.search_advanced)
        layout.addWidget(search_adv_btn)

        layout.addStretch()

        return widget

    def create_results_section(self):
        """Create the results table section."""
        group = QGroupBox("Search Results")
        layout = QVBoxLayout(group)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Title", "Date", "Cloud %", "Provider", "Product", "ID"
        ])
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.results_table.itemSelectionChanged.connect(self.on_selection_changed)

        layout.addWidget(self.results_table)

        # Output directory
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("Download to:"))

        self.output_dir_input = QLineEdit()
        self.output_dir_input.setText(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "downloads"
        ))
        output_layout.addWidget(self.output_dir_input)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self.browse_output_dir)
        output_layout.addWidget(browse_btn)

        layout.addLayout(output_layout)

        return group

    def search_nl(self):
        """Execute natural language search."""
        query = self.search_input.text().strip()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter a search query.")
            return

        hub = self.plugin.get_hub()
        parser = self.plugin.get_parser()

        if not hub or not parser:
            QMessageBox.critical(self, "Error", "Failed to initialize GeoDataHub.")
            return

        # Get bbox if using map extent
        bbox = None
        if self.use_extent_cb.isChecked():
            bbox = self.plugin.get_canvas_extent()

        # Start search worker
        self.search_worker = SearchWorker(
            hub, parser, query,
            self.limit_spin.value(),
            bbox
        )
        self.search_worker.finished.connect(self.on_search_finished)
        self.search_worker.error.connect(self.on_search_error)
        self.search_worker.progress.connect(self.on_search_progress)

        self.search_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate

        self.search_worker.start()

    def search_advanced(self):
        """Execute advanced search."""
        hub = self.plugin.get_hub()
        parser = self.plugin.get_parser()

        if not hub or not parser:
            QMessageBox.critical(self, "Error", "Failed to initialize GeoDataHub.")
            return

        # Build query from form fields
        product = self.product_combo.currentText().split(" - ")[0]
        location = self.location_input.text().strip()
        start = self.start_date.date().toString("yyyy-MM-dd")
        end = self.end_date.date().toString("yyyy-MM-dd")
        cloud = self.cloud_spin.value()

        # Build natural language query
        query = f"{product}"
        if location:
            query += f" {location}"
        query += f" from {start} to {end}"
        query += f" with less than {cloud}% cloud cover"

        # Get bbox if using map extent
        bbox = None
        if self.use_extent_adv_cb.isChecked():
            bbox = self.plugin.get_canvas_extent()

        # Start search
        self.search_worker = SearchWorker(
            hub, parser, query,
            self.limit_spin.value(),
            bbox
        )
        self.search_worker.finished.connect(self.on_search_finished)
        self.search_worker.error.connect(self.on_search_error)
        self.search_worker.progress.connect(self.on_search_progress)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.search_worker.start()

    def on_search_progress(self, message):
        """Handle search progress update."""
        self.status_label.setText(message)

    def on_search_finished(self, results):
        """Handle search completion."""
        self.search_results = results
        self.populate_results_table(results)

        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"Found {len(results)} results")

    def on_search_error(self, error_message):
        """Handle search error."""
        self.search_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Search failed")

        QMessageBox.critical(self, "Search Error", error_message)

    def populate_results_table(self, results):
        """Populate results table with search results."""
        self.results_table.setRowCount(len(results))

        for i, result in enumerate(results):
            self.results_table.setItem(i, 0, QTableWidgetItem(result.title[:50]))
            self.results_table.setItem(i, 1, QTableWidgetItem(result.date))

            cloud_str = f"{result.cloud_cover:.1f}" if result.cloud_cover else "N/A"
            self.results_table.setItem(i, 2, QTableWidgetItem(cloud_str))

            self.results_table.setItem(i, 3, QTableWidgetItem(result.provider))
            self.results_table.setItem(i, 4, QTableWidgetItem(result.product_type))
            self.results_table.setItem(i, 5, QTableWidgetItem(result.id))

    def on_selection_changed(self):
        """Handle table selection change."""
        has_selection = len(self.results_table.selectedItems()) > 0
        self.download_btn.setEnabled(has_selection)
        self.add_layer_btn.setEnabled(has_selection)

    def browse_output_dir(self):
        """Browse for output directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Output Directory",
            self.output_dir_input.text()
        )
        if directory:
            self.output_dir_input.setText(directory)

    def get_selected_results(self):
        """Get the selected search results."""
        selected_rows = set()
        for item in self.results_table.selectedItems():
            selected_rows.add(item.row())

        return [self.search_results[row] for row in sorted(selected_rows)]

    def download_selected(self):
        """Download selected products."""
        selected = self.get_selected_results()
        if not selected:
            return

        output_dir = self.output_dir_input.text()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        hub = self.plugin.get_hub()

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(selected))

        for i, result in enumerate(selected):
            self.status_label.setText(f"Downloading {i+1}/{len(selected)}: {result.title[:30]}...")
            self.progress_bar.setValue(i)

            try:
                hub.download(result, output_dir)
            except Exception as e:
                QMessageBox.warning(
                    self, "Download Error",
                    f"Failed to download {result.title}: {e}"
                )

        self.progress_bar.setValue(len(selected))
        self.status_label.setText(f"Downloaded {len(selected)} products to {output_dir}")
        self.progress_bar.setVisible(False)

        QMessageBox.information(
            self, "Download Complete",
            f"Downloaded {len(selected)} products to:\n{output_dir}"
        )

    def download_and_add_layer(self):
        """Download selected products and add them as layers."""
        selected = self.get_selected_results()
        if not selected:
            return

        output_dir = self.output_dir_input.text()
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        hub = self.plugin.get_hub()

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(selected))

        added_layers = 0
        for i, result in enumerate(selected):
            self.status_label.setText(f"Downloading {i+1}/{len(selected)}: {result.title[:30]}...")
            self.progress_bar.setValue(i)

            try:
                file_path = hub.download(result, output_dir)

                # Add as layer
                layer = self.plugin.add_raster_layer(str(file_path), result.title[:50])
                if layer:
                    added_layers += 1

            except Exception as e:
                QMessageBox.warning(
                    self, "Error",
                    f"Failed to download/add {result.title}: {e}"
                )

        self.progress_bar.setValue(len(selected))
        self.status_label.setText(f"Added {added_layers} layers to map")
        self.progress_bar.setVisible(False)

        QMessageBox.information(
            self, "Complete",
            f"Downloaded and added {added_layers} layers to the map."
        )
