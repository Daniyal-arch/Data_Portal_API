"""
AI Dataset Recommendation Dialog

Provides intelligent dataset recommendations based on the user's analysis needs.
Uses comprehensive data source catalog for diverse recommendations.
"""

import os
import json
from datetime import datetime

from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QGroupBox, QListWidget, QListWidgetItem,
    QProgressBar, QMessageBox, QComboBox, QCheckBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QTabWidget, QWidget, QScrollArea, QFrame
)
from qgis.PyQt.QtGui import QFont, QColor


# Import data sources catalog
import sys
plugin_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(plugin_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from geodatahub.data_sources import (
        DATA_SOURCES, DataSource, DataCategory,
        get_sources_for_analysis, get_sources_by_category,
        get_all_sources_summary
    )
    DATA_SOURCES_AVAILABLE = True
except ImportError:
    DATA_SOURCES_AVAILABLE = False
    DATA_SOURCES = {}


# LLM prompt for advanced recommendations
RECOMMENDATION_PROMPT = """You are a remote sensing and GIS expert. Based on the user's analysis description, recommend the most suitable satellite datasets.

User's analysis: {analysis_description}
Location: {location}

Available datasets:
{available_datasets}

Respond in JSON format:
{{
    "recommended_datasets": ["dataset_id1", "dataset_id2"],
    "primary_recommendation": "dataset_id",
    "reasoning": "explanation of why these datasets are suitable",
    "suggested_indices": ["INDEX1", "INDEX2"],
    "processing_workflow": ["step1", "step2", "step3"],
    "cloud_cover_advice": "advice on cloud cover threshold",
    "temporal_advice": "advice on time period selection",
    "alternative_approach": "alternative methodology if primary doesn't work"
}}
"""


class RecommendationWorker(QThread):
    """Background worker for AI recommendations."""

    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, analysis_text, location, use_llm=True):
        super().__init__()
        self.analysis_text = analysis_text
        self.location = location
        self.use_llm = use_llm

    def run(self):
        try:
            if self.use_llm:
                result = self.get_llm_recommendation()
            else:
                result = self.get_catalog_recommendation()

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))

    def get_llm_recommendation(self):
        """Get recommendation using LLM."""
        try:
            from geodatahub.nlp.llm_client import get_llm_client

            client = get_llm_client()
            if not client:
                return self.get_catalog_recommendation()

            # Build available datasets string
            datasets_str = ""
            for ds_id, ds in DATA_SOURCES.items():
                datasets_str += f"- {ds_id}: {ds.name} ({ds.category.value}, {ds.resolution_m}m) - {ds.description[:100]}...\n"

            prompt = RECOMMENDATION_PROMPT.format(
                analysis_description=self.analysis_text,
                location=self.location or "Not specified",
                available_datasets=datasets_str
            )

            response = client.complete(prompt)

            # Parse JSON from response
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    result = json.loads(json_str)

                    # Enrich with data source details
                    result["dataset_details"] = []
                    for ds_id in result.get("recommended_datasets", []):
                        if ds_id in DATA_SOURCES:
                            ds = DATA_SOURCES[ds_id]
                            result["dataset_details"].append({
                                "id": ds.id,
                                "name": ds.name,
                                "category": ds.category.value,
                                "resolution_m": ds.resolution_m,
                                "provider": ds.provider,
                                "pros": ds.pros,
                                "cons": ds.cons,
                                "use_cases": ds.use_cases,
                                "suitable_indices": ds.suitable_indices
                            })

                    return result

            except json.JSONDecodeError:
                pass

            return self.get_catalog_recommendation()

        except Exception:
            return self.get_catalog_recommendation()

    def get_catalog_recommendation(self):
        """Get recommendation from data sources catalog."""
        if not DATA_SOURCES_AVAILABLE:
            return self._fallback_recommendation()

        # Use catalog-based recommendation
        recommended_sources = get_sources_for_analysis(self.analysis_text)

        if not recommended_sources:
            recommended_sources = [DATA_SOURCES.get("S2_MSI_L2A")]

        # Build result
        result = {
            "recommended_datasets": [ds.id for ds in recommended_sources if ds],
            "primary_recommendation": recommended_sources[0].id if recommended_sources else "S2_MSI_L2A",
            "reasoning": "",
            "suggested_indices": [],
            "processing_workflow": [],
            "dataset_details": []
        }

        # Compile info from recommended sources
        all_indices = set()
        all_use_cases = []
        pros_list = []

        for ds in recommended_sources:
            if ds:
                all_indices.update(ds.suitable_indices)
                all_use_cases.extend(ds.use_cases[:2])
                pros_list.extend(ds.pros[:2])

                result["dataset_details"].append({
                    "id": ds.id,
                    "name": ds.name,
                    "category": ds.category.value,
                    "resolution_m": ds.resolution_m,
                    "provider": ds.provider,
                    "description": ds.description,
                    "pros": ds.pros,
                    "cons": ds.cons,
                    "use_cases": ds.use_cases,
                    "suitable_indices": ds.suitable_indices
                })

        result["suggested_indices"] = list(all_indices)[:6]
        result["reasoning"] = f"Based on your analysis requirements, these datasets are recommended. " \
                             f"Key advantages: {', '.join(pros_list[:4])}"

        # Add workflow suggestions
        result["processing_workflow"] = [
            "1. Download data for your area of interest",
            "2. Apply atmospheric correction (if needed)",
            f"3. Calculate indices: {', '.join(list(all_indices)[:3])}",
            "4. Perform classification or analysis",
            "5. Validate results"
        ]

        # Add advice
        primary = DATA_SOURCES.get(result["primary_recommendation"])
        if primary:
            if primary.category == DataCategory.OPTICAL:
                result["cloud_cover_advice"] = "Use <20% cloud cover for optical analysis. Consider compositing multiple dates."
            elif primary.category == DataCategory.SAR:
                result["cloud_cover_advice"] = "SAR works through clouds - no cloud cover filter needed."
            else:
                result["cloud_cover_advice"] = "N/A for this data type."

            result["temporal_advice"] = f"Data available from {primary.start_date or 'varies'}. " \
                                       f"Revisit time: {primary.revisit_days or 'N/A'} days."

        return result

    def _fallback_recommendation(self):
        """Fallback when data sources not available."""
        return {
            "recommended_datasets": ["S2_MSI_L2A"],
            "primary_recommendation": "S2_MSI_L2A",
            "reasoning": "Sentinel-2 is recommended as a versatile optical dataset.",
            "suggested_indices": ["NDVI", "NDWI"],
            "dataset_details": []
        }


class RecommendationDialog(QDialog):
    """Dialog for AI-powered dataset recommendations."""

    def __init__(self, parent=None, plugin=None):
        super().__init__(parent)
        self.plugin = plugin
        self.current_recommendation = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("AI Dataset Recommendations")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout(self)

        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: AI Recommendations
        recommend_tab = self.create_recommend_tab()
        tabs.addTab(recommend_tab, "AI Recommendations")

        # Tab 2: Browse All Datasets
        browse_tab = self.create_browse_tab()
        tabs.addTab(browse_tab, "Browse All Datasets")

        # Action buttons
        button_layout = QHBoxLayout()

        self.search_btn = QPushButton("Search for Selected Data")
        self.search_btn.clicked.connect(self.search_recommended)
        self.search_btn.setEnabled(False)
        button_layout.addWidget(self.search_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def create_recommend_tab(self):
        """Create the AI recommendations tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Instructions
        instructions = QLabel(
            "Describe your analysis goals and the AI will recommend the most suitable "
            "satellite datasets, spectral indices, and processing workflow."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        # Input section
        input_group = QGroupBox("Describe Your Analysis")
        input_layout = QVBoxLayout(input_group)

        input_layout.addWidget(QLabel("What do you want to analyze?"))

        self.analysis_input = QTextEdit()
        self.analysis_input.setPlaceholderText(
            "Examples:\n"
            "• I want to monitor crop health and predict yield in agricultural fields\n"
            "• I need to map flood extent after heavy rainfall, even through clouds\n"
            "• I want to analyze urban heat islands and temperature patterns\n"
            "• I need to detect deforestation and forest degradation over time\n"
            "• I want to monitor air quality and pollution levels in my city\n"
            "• I need elevation data for watershed delineation and flood modeling"
        )
        self.analysis_input.setMaximumHeight(100)
        input_layout.addWidget(self.analysis_input)

        # Location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Location (optional):"))

        self.location_input = QTextEdit()
        self.location_input.setPlaceholderText("e.g., California, USA or leave empty for global")
        self.location_input.setMaximumHeight(30)
        location_layout.addWidget(self.location_input)

        self.use_map_extent = QCheckBox("Use current map extent")
        location_layout.addWidget(self.use_map_extent)

        input_layout.addLayout(location_layout)

        layout.addWidget(input_group)

        # Get recommendations button
        self.recommend_btn = QPushButton("Get AI Recommendations")
        self.recommend_btn.clicked.connect(self.get_recommendations)
        layout.addWidget(self.recommend_btn)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Results section
        results_group = QGroupBox("Recommendations")
        results_layout = QVBoxLayout(results_group)

        # Primary recommendation
        self.primary_label = QLabel("Primary Dataset: -")
        self.primary_label.setFont(QFont("", 11, QFont.Bold))
        results_layout.addWidget(self.primary_label)

        # Dataset details table
        results_layout.addWidget(QLabel("Recommended Datasets:"))
        self.datasets_table = QTableWidget()
        self.datasets_table.setColumnCount(5)
        self.datasets_table.setHorizontalHeaderLabels([
            "Dataset", "Category", "Resolution", "Provider", "Description"
        ])
        self.datasets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.datasets_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.datasets_table.setMaximumHeight(150)
        results_layout.addWidget(self.datasets_table)

        # Two columns for indices and workflow
        details_layout = QHBoxLayout()

        # Indices
        indices_group = QGroupBox("Suggested Indices")
        indices_layout = QVBoxLayout(indices_group)
        self.indices_list = QListWidget()
        self.indices_list.setMaximumHeight(100)
        indices_layout.addWidget(self.indices_list)
        details_layout.addWidget(indices_group)

        # Workflow
        workflow_group = QGroupBox("Processing Workflow")
        workflow_layout = QVBoxLayout(workflow_group)
        self.workflow_list = QListWidget()
        self.workflow_list.setMaximumHeight(100)
        workflow_layout.addWidget(self.workflow_list)
        details_layout.addWidget(workflow_group)

        results_layout.addLayout(details_layout)

        # Reasoning
        results_layout.addWidget(QLabel("Why these datasets:"))
        self.reasoning_text = QTextEdit()
        self.reasoning_text.setReadOnly(True)
        self.reasoning_text.setMaximumHeight(60)
        results_layout.addWidget(self.reasoning_text)

        # Tips
        tips_layout = QHBoxLayout()

        cloud_group = QGroupBox("Cloud Cover Advice")
        cloud_layout = QVBoxLayout(cloud_group)
        self.cloud_label = QLabel("-")
        self.cloud_label.setWordWrap(True)
        cloud_layout.addWidget(self.cloud_label)
        tips_layout.addWidget(cloud_group)

        temporal_group = QGroupBox("Temporal Advice")
        temporal_layout = QVBoxLayout(temporal_group)
        self.temporal_label = QLabel("-")
        self.temporal_label.setWordWrap(True)
        temporal_layout.addWidget(self.temporal_label)
        tips_layout.addWidget(temporal_group)

        results_layout.addLayout(tips_layout)

        layout.addWidget(results_group)

        return widget

    def create_browse_tab(self):
        """Create the browse all datasets tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter by category
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by category:"))

        self.category_combo = QComboBox()
        self.category_combo.addItem("All Categories", None)
        if DATA_SOURCES_AVAILABLE:
            for cat in DataCategory:
                self.category_combo.addItem(cat.value.title(), cat)
        self.category_combo.currentIndexChanged.connect(self.filter_datasets)
        filter_layout.addWidget(self.category_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Datasets table
        self.browse_table = QTableWidget()
        self.browse_table.setColumnCount(6)
        self.browse_table.setHorizontalHeaderLabels([
            "ID", "Name", "Category", "Resolution (m)", "Provider", "Use Cases"
        ])
        self.browse_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.browse_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.Stretch)
        self.browse_table.itemSelectionChanged.connect(self.on_browse_selection)
        layout.addWidget(self.browse_table)

        # Dataset details
        details_group = QGroupBox("Dataset Details")
        details_layout = QVBoxLayout(details_group)

        self.details_text = QTextEdit()
        self.details_text.setReadOnly(True)
        self.details_text.setMaximumHeight(150)
        details_layout.addWidget(self.details_text)

        layout.addWidget(details_group)

        # Populate table
        self.populate_browse_table()

        return widget

    def populate_browse_table(self, category=None):
        """Populate the browse table with datasets."""
        self.browse_table.setRowCount(0)

        if not DATA_SOURCES_AVAILABLE:
            return

        sources = DATA_SOURCES.values()
        if category:
            sources = [ds for ds in sources if ds.category == category]

        self.browse_table.setRowCount(len(list(sources)))

        for i, ds in enumerate(DATA_SOURCES.values()):
            if category and ds.category != category:
                continue

            row = self.browse_table.rowCount() - 1
            self.browse_table.insertRow(row)

            self.browse_table.setItem(i, 0, QTableWidgetItem(ds.id))
            self.browse_table.setItem(i, 1, QTableWidgetItem(ds.name))
            self.browse_table.setItem(i, 2, QTableWidgetItem(ds.category.value))
            self.browse_table.setItem(i, 3, QTableWidgetItem(str(ds.resolution_m) if ds.resolution_m else "N/A"))
            self.browse_table.setItem(i, 4, QTableWidgetItem(ds.provider))
            self.browse_table.setItem(i, 5, QTableWidgetItem(", ".join(ds.use_cases[:3])))

    def filter_datasets(self):
        """Filter datasets by category."""
        category = self.category_combo.currentData()
        self.populate_browse_table(category)

    def on_browse_selection(self):
        """Show details for selected dataset."""
        selected = self.browse_table.selectedItems()
        if not selected:
            return

        row = selected[0].row()
        ds_id = self.browse_table.item(row, 0).text()

        if ds_id in DATA_SOURCES:
            ds = DATA_SOURCES[ds_id]
            details = f"""<b>{ds.name}</b> ({ds.id})
<br><br>
<b>Description:</b> {ds.description}
<br><br>
<b>Category:</b> {ds.category.value} | <b>Resolution:</b> {ds.resolution_m}m | <b>Revisit:</b> {ds.revisit_days or 'N/A'} days
<br><br>
<b>Pros:</b> {', '.join(ds.pros)}
<br><br>
<b>Cons:</b> {', '.join(ds.cons)}
<br><br>
<b>Suitable Indices:</b> {', '.join(ds.suitable_indices)}
<br><br>
<b>Bands:</b> {', '.join(ds.bands[:10])}{'...' if len(ds.bands) > 10 else ''}
"""
            self.details_text.setHtml(details)
            self.search_btn.setEnabled(True)

    def get_recommendations(self):
        """Get AI recommendations."""
        analysis_text = self.analysis_input.toPlainText().strip()
        if not analysis_text:
            QMessageBox.warning(self, "Warning", "Please describe your analysis.")
            return

        location = self.location_input.toPlainText().strip()
        if self.use_map_extent.isChecked() and self.plugin:
            bbox = self.plugin.get_canvas_extent()
            location = f"bbox: {bbox}"

        self.recommend_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        self.worker = RecommendationWorker(analysis_text, location)
        self.worker.finished.connect(self.on_recommendation_finished)
        self.worker.error.connect(self.on_recommendation_error)
        self.worker.start()

    def on_recommendation_finished(self, result):
        """Handle recommendation completion."""
        self.current_recommendation = result
        self.recommend_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        # Update primary
        primary = result.get("primary_recommendation", "S2_MSI_L2A")
        primary_name = DATA_SOURCES.get(primary, {})
        if hasattr(primary_name, 'name'):
            self.primary_label.setText(f"Primary Dataset: {primary_name.name} ({primary})")
        else:
            self.primary_label.setText(f"Primary Dataset: {primary}")

        # Update datasets table
        details = result.get("dataset_details", [])
        self.datasets_table.setRowCount(len(details))

        for i, ds in enumerate(details):
            self.datasets_table.setItem(i, 0, QTableWidgetItem(ds.get("name", ds.get("id", ""))))
            self.datasets_table.setItem(i, 1, QTableWidgetItem(ds.get("category", "")))
            self.datasets_table.setItem(i, 2, QTableWidgetItem(str(ds.get("resolution_m", "N/A"))))
            self.datasets_table.setItem(i, 3, QTableWidgetItem(ds.get("provider", "")))
            desc = ds.get("description", "")[:80] + "..." if len(ds.get("description", "")) > 80 else ds.get("description", "")
            self.datasets_table.setItem(i, 4, QTableWidgetItem(desc))

        # Update indices
        self.indices_list.clear()
        for idx in result.get("suggested_indices", []):
            self.indices_list.addItem(idx)

        # Update workflow
        self.workflow_list.clear()
        for step in result.get("processing_workflow", []):
            self.workflow_list.addItem(step)

        # Update reasoning
        self.reasoning_text.setText(result.get("reasoning", ""))

        # Update tips
        self.cloud_label.setText(result.get("cloud_cover_advice", "-"))
        self.temporal_label.setText(result.get("temporal_advice", "-"))

        self.search_btn.setEnabled(True)

    def on_recommendation_error(self, error_message):
        """Handle recommendation error."""
        self.recommend_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Failed to get recommendations: {error_message}")

    def search_recommended(self):
        """Open search dialog with recommended dataset."""
        # Get selected dataset
        selected_id = None

        if self.current_recommendation:
            selected_id = self.current_recommendation.get("primary_recommendation")

        # Check browse table selection
        browse_selected = self.browse_table.selectedItems()
        if browse_selected:
            selected_id = self.browse_table.item(browse_selected[0].row(), 0).text()

        if not selected_id or not self.plugin:
            return

        # Get the main dialog
        from .geodatahub_dialog import GeoDataHubDialog

        dlg = GeoDataHubDialog(parent=self.parent(), plugin=self.plugin)

        # Pre-fill with recommendation
        location = self.location_input.toPlainText().strip()
        query = f"{selected_id} {location}" if location else selected_id
        dlg.search_input.setText(query)

        dlg.show()
        dlg.exec_()
