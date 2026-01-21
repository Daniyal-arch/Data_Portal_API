"""
AI Dataset Recommendation Dialog

Provides intelligent dataset recommendations based on the user's analysis needs.
Uses comprehensive workflow templates and EODAG catalog for diverse recommendations.
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
    QTabWidget, QWidget, QScrollArea, QFrame, QSplitter
)
from qgis.PyQt.QtGui import QFont, QColor


# Import geodatahub modules
import sys
plugin_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(plugin_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Try importing new modules
try:
    from geodatahub.workflows import (
        ANALYSIS_WORKFLOWS, SPECTRAL_INDICES, AnalysisCategory,
        match_workflow, get_workflow_recommendation, get_qgis_formula
    )
    from geodatahub.eodag_catalog import (
        EODAG_PROVIDERS, EODAG_PRODUCTS,
        get_providers_for_product, search_products as search_eodag_products
    )
    from geodatahub.provider_config import (
        get_config_manager, check_product_access
    )
    WORKFLOWS_AVAILABLE = True
except ImportError:
    WORKFLOWS_AVAILABLE = False
    ANALYSIS_WORKFLOWS = {}
    SPECTRAL_INDICES = {}

# Fallback to data_sources if workflows not available
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
            if WORKFLOWS_AVAILABLE:
                result = self.get_workflow_recommendation()
            elif self.use_llm:
                result = self.get_llm_recommendation()
            else:
                result = self.get_catalog_recommendation()

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))

    def get_workflow_recommendation(self):
        """Get recommendation using workflow templates."""
        recommendation = get_workflow_recommendation(self.analysis_text)

        if recommendation.get("status") == "no_match":
            return self.get_catalog_recommendation()

        workflow = recommendation.get("recommended_workflow", {})

        # Check provider access
        primary_dataset = workflow.get("primary_dataset", "S2_MSI_L2A")
        provider_check = check_product_access(primary_dataset)

        # Build result
        result = {
            "workflow_id": workflow.get("id"),
            "workflow_name": workflow.get("name"),
            "recommended_datasets": [primary_dataset] + workflow.get("fallback_datasets", []),
            "primary_recommendation": primary_dataset,
            "reasoning": workflow.get("description", ""),
            "suggested_indices": workflow.get("indices", []),
            "processing_workflow": [
                f"{s['order']}. {s['name']}: {s['description']}"
                for s in workflow.get("steps", [])
            ],
            "qgis_steps": workflow.get("steps", []),
            "cloud_cover_max": workflow.get("cloud_cover_max", 20),
            "temporal_requirement": workflow.get("temporal_requirement", "single"),
            "indices_details": recommendation.get("indices_details", []),
            "provider_status": provider_check,
            "alternative_workflows": recommendation.get("alternative_workflows", []),
            "dataset_details": []
        }

        # Add dataset details from EODAG catalog
        for ds_id in result["recommended_datasets"]:
            if ds_id in EODAG_PRODUCTS:
                product = EODAG_PRODUCTS[ds_id]
                result["dataset_details"].append({
                    "id": product.id,
                    "name": product.title,
                    "category": product.sensor_type,
                    "resolution_m": product.resolution_m,
                    "provider": ", ".join(product.providers[:2]),
                    "description": product.description,
                    "platform": product.platform
                })
            elif DATA_SOURCES_AVAILABLE and ds_id in DATA_SOURCES:
                ds = DATA_SOURCES[ds_id]
                result["dataset_details"].append({
                    "id": ds.id,
                    "name": ds.name,
                    "category": ds.category.value,
                    "resolution_m": ds.resolution_m,
                    "provider": ds.provider,
                    "description": ds.description,
                    "pros": ds.pros,
                    "cons": ds.cons
                })

        # Add advice based on workflow
        if workflow.get("category") == "flood" or "sar" in str(workflow).lower():
            result["cloud_cover_advice"] = "SAR works through clouds - no cloud cover filter needed."
        else:
            result["cloud_cover_advice"] = f"Use <{result['cloud_cover_max']}% cloud cover for optical analysis."

        temporal = result["temporal_requirement"]
        if temporal == "before_after":
            result["temporal_advice"] = "You need imagery from before AND after the event for change detection."
        elif temporal == "multi-date":
            result["temporal_advice"] = "Multiple dates recommended for time series analysis."
        else:
            result["temporal_advice"] = "Single date imagery is sufficient for this analysis."

        return result

    def get_llm_recommendation(self):
        """Get recommendation using LLM."""
        try:
            from geodatahub.nlp.llm_client import get_llm_client

            client = get_llm_client()
            if not client:
                return self.get_catalog_recommendation()

            # Build prompt with workflow context
            prompt = self._build_llm_prompt()
            response = client.complete(prompt)

            # Parse JSON from response
            try:
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass

            return self.get_catalog_recommendation()

        except Exception:
            return self.get_catalog_recommendation()

    def _build_llm_prompt(self):
        """Build LLM prompt with workflow context."""
        workflows_str = ""
        for wf_id, wf in ANALYSIS_WORKFLOWS.items():
            workflows_str += f"- {wf.name}: {wf.description} (Dataset: {wf.primary_dataset})\n"

        return f"""You are a remote sensing expert. Recommend datasets for this analysis:

User's analysis: {self.analysis_text}
Location: {self.location or "Not specified"}

Available workflows:
{workflows_str}

Respond in JSON format with recommended_datasets, reasoning, suggested_indices, processing_workflow."""

    def get_catalog_recommendation(self):
        """Get recommendation from data sources catalog."""
        if not DATA_SOURCES_AVAILABLE:
            return self._fallback_recommendation()

        recommended_sources = get_sources_for_analysis(self.analysis_text)

        if not recommended_sources:
            recommended_sources = [DATA_SOURCES.get("S2_MSI_L2A")]

        result = {
            "recommended_datasets": [ds.id for ds in recommended_sources if ds],
            "primary_recommendation": recommended_sources[0].id if recommended_sources else "S2_MSI_L2A",
            "reasoning": "",
            "suggested_indices": [],
            "processing_workflow": [],
            "dataset_details": []
        }

        all_indices = set()
        for ds in recommended_sources:
            if ds:
                all_indices.update(ds.suitable_indices)
                result["dataset_details"].append({
                    "id": ds.id,
                    "name": ds.name,
                    "category": ds.category.value,
                    "resolution_m": ds.resolution_m,
                    "provider": ds.provider,
                    "description": ds.description,
                    "pros": ds.pros,
                    "cons": ds.cons
                })

        result["suggested_indices"] = list(all_indices)[:6]
        result["reasoning"] = "Based on keyword matching with your analysis requirements."

        return result

    def _fallback_recommendation(self):
        """Fallback when no modules available."""
        return {
            "recommended_datasets": ["S2_MSI_L2A"],
            "primary_recommendation": "S2_MSI_L2A",
            "reasoning": "Sentinel-2 is recommended as a versatile optical dataset.",
            "suggested_indices": ["NDVI", "NDWI"],
            "dataset_details": []
        }


class RecommendationDialog(QDialog):
    """Dialog for AI-powered dataset recommendations with QGIS workflow integration."""

    def __init__(self, parent=None, plugin=None):
        super().__init__(parent)
        self.plugin = plugin
        self.current_recommendation = None

        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("AI Dataset Recommendations & Workflows")
        self.setMinimumSize(1000, 800)

        layout = QVBoxLayout(self)

        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: AI Recommendations
        recommend_tab = self.create_recommend_tab()
        tabs.addTab(recommend_tab, "AI Recommendations")

        # Tab 2: Browse Workflows
        workflows_tab = self.create_workflows_tab()
        tabs.addTab(workflows_tab, "Analysis Workflows")

        # Tab 3: Browse Datasets
        browse_tab = self.create_browse_tab()
        tabs.addTab(browse_tab, "Browse Datasets")

        # Tab 4: Provider Status
        provider_tab = self.create_provider_tab()
        tabs.addTab(provider_tab, "Provider Status")

        # Action buttons
        button_layout = QHBoxLayout()

        self.search_btn = QPushButton("Search for Selected Data")
        self.search_btn.clicked.connect(self.search_recommended)
        self.search_btn.setEnabled(False)
        button_layout.addWidget(self.search_btn)

        self.run_workflow_btn = QPushButton("Run Workflow in QGIS")
        self.run_workflow_btn.clicked.connect(self.run_workflow)
        self.run_workflow_btn.setEnabled(False)
        button_layout.addWidget(self.run_workflow_btn)

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
            "Describe your analysis goals and get intelligent recommendations for "
            "datasets, spectral indices, and processing workflows ready for QGIS."
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
            "- I want to monitor crop health and predict yield\n"
            "- Map flood extent after heavy rainfall\n"
            "- Detect deforestation over time\n"
            "- Analyze urban heat islands\n"
            "- Assess fire damage and burn severity"
        )
        self.analysis_input.setMaximumHeight(100)
        input_layout.addWidget(self.analysis_input)

        # Location
        location_layout = QHBoxLayout()
        location_layout.addWidget(QLabel("Location (optional):"))

        self.location_input = QTextEdit()
        self.location_input.setPlaceholderText("e.g., California, USA")
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

        # Results section with splitter
        splitter = QSplitter(Qt.Vertical)

        # Top: Primary info and datasets
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)

        # Primary recommendation
        self.primary_label = QLabel("Primary Dataset: -")
        self.primary_label.setFont(QFont("", 11, QFont.Bold))
        top_layout.addWidget(self.primary_label)

        # Workflow matched
        self.workflow_label = QLabel("Matched Workflow: -")
        top_layout.addWidget(self.workflow_label)

        # Dataset details table
        top_layout.addWidget(QLabel("Recommended Datasets:"))
        self.datasets_table = QTableWidget()
        self.datasets_table.setColumnCount(5)
        self.datasets_table.setHorizontalHeaderLabels([
            "Dataset", "Category", "Resolution", "Provider", "Description"
        ])
        self.datasets_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.datasets_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.datasets_table.setMaximumHeight(120)
        top_layout.addWidget(self.datasets_table)

        splitter.addWidget(top_widget)

        # Middle: Indices and QGIS Steps
        middle_widget = QWidget()
        middle_layout = QHBoxLayout(middle_widget)

        # Indices with formulas
        indices_group = QGroupBox("Spectral Indices & QGIS Formulas")
        indices_layout = QVBoxLayout(indices_group)
        self.indices_table = QTableWidget()
        self.indices_table.setColumnCount(3)
        self.indices_table.setHorizontalHeaderLabels(["Index", "Name", "QGIS Formula"])
        self.indices_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.indices_table.setMaximumHeight(120)
        indices_layout.addWidget(self.indices_table)
        middle_layout.addWidget(indices_group)

        # QGIS Workflow
        workflow_group = QGroupBox("QGIS Processing Steps")
        workflow_layout = QVBoxLayout(workflow_group)
        self.workflow_list = QListWidget()
        self.workflow_list.setMaximumHeight(120)
        workflow_layout.addWidget(self.workflow_list)
        middle_layout.addWidget(workflow_group)

        splitter.addWidget(middle_widget)

        # Bottom: Tips
        bottom_widget = QWidget()
        bottom_layout = QHBoxLayout(bottom_widget)

        # Provider status
        provider_group = QGroupBox("Provider Status")
        provider_layout = QVBoxLayout(provider_group)
        self.provider_status_label = QLabel("-")
        self.provider_status_label.setWordWrap(True)
        provider_layout.addWidget(self.provider_status_label)
        bottom_layout.addWidget(provider_group)

        # Cloud cover advice
        cloud_group = QGroupBox("Cloud Cover")
        cloud_layout = QVBoxLayout(cloud_group)
        self.cloud_label = QLabel("-")
        self.cloud_label.setWordWrap(True)
        cloud_layout.addWidget(self.cloud_label)
        bottom_layout.addWidget(cloud_group)

        # Temporal advice
        temporal_group = QGroupBox("Temporal")
        temporal_layout = QVBoxLayout(temporal_group)
        self.temporal_label = QLabel("-")
        self.temporal_label.setWordWrap(True)
        temporal_layout.addWidget(self.temporal_label)
        bottom_layout.addWidget(temporal_group)

        splitter.addWidget(bottom_widget)

        layout.addWidget(splitter)

        return widget

    def create_workflows_tab(self):
        """Create the workflows browsing tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("Browse predefined analysis workflows:"))

        # Workflows table
        self.workflows_table = QTableWidget()
        self.workflows_table.setColumnCount(5)
        self.workflows_table.setHorizontalHeaderLabels([
            "Workflow", "Category", "Primary Dataset", "Indices", "Description"
        ])
        self.workflows_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.workflows_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.workflows_table.itemSelectionChanged.connect(self.on_workflow_selection)
        layout.addWidget(self.workflows_table)

        # Populate
        if WORKFLOWS_AVAILABLE:
            self.workflows_table.setRowCount(len(ANALYSIS_WORKFLOWS))
            for i, (wf_id, wf) in enumerate(ANALYSIS_WORKFLOWS.items()):
                self.workflows_table.setItem(i, 0, QTableWidgetItem(wf.name))
                self.workflows_table.setItem(i, 1, QTableWidgetItem(wf.category.value))
                self.workflows_table.setItem(i, 2, QTableWidgetItem(wf.primary_dataset))
                self.workflows_table.setItem(i, 3, QTableWidgetItem(", ".join(wf.indices[:3])))
                self.workflows_table.setItem(i, 4, QTableWidgetItem(wf.description[:80] + "..."))

        # Workflow details
        details_group = QGroupBox("Workflow Details")
        details_layout = QVBoxLayout(details_group)
        self.workflow_details = QTextEdit()
        self.workflow_details.setReadOnly(True)
        details_layout.addWidget(self.workflow_details)
        layout.addWidget(details_group)

        return widget

    def create_browse_tab(self):
        """Create the browse all datasets tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter by category
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by:"))

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

    def create_provider_tab(self):
        """Create the provider status tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("EODAG Provider Configuration Status:"))

        # Provider table
        self.provider_table = QTableWidget()
        self.provider_table.setColumnCount(5)
        self.provider_table.setHorizontalHeaderLabels([
            "Provider", "Name", "Free Access", "Configured", "Products"
        ])
        self.provider_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.provider_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.provider_table.itemSelectionChanged.connect(self.on_provider_selection)
        layout.addWidget(self.provider_table)

        # Populate
        if WORKFLOWS_AVAILABLE:
            config_mgr = get_config_manager()
            self.provider_table.setRowCount(len(EODAG_PROVIDERS))

            for i, (prov_id, prov) in enumerate(EODAG_PROVIDERS.items()):
                is_configured = config_mgr.is_provider_configured(prov_id)
                products_count = len([p for p in EODAG_PRODUCTS.values() if prov_id in p.providers])

                self.provider_table.setItem(i, 0, QTableWidgetItem(prov_id))
                self.provider_table.setItem(i, 1, QTableWidgetItem(prov.name))
                self.provider_table.setItem(i, 2, QTableWidgetItem("Yes" if prov.free_access else "No"))

                status_item = QTableWidgetItem("Yes" if is_configured else "No")
                if is_configured:
                    status_item.setBackground(QColor(200, 255, 200))
                else:
                    status_item.setBackground(QColor(255, 200, 200))
                self.provider_table.setItem(i, 3, status_item)

                self.provider_table.setItem(i, 4, QTableWidgetItem(str(products_count)))

        # Setup instructions
        setup_group = QGroupBox("Setup Instructions")
        setup_layout = QVBoxLayout(setup_group)
        self.setup_text = QTextEdit()
        self.setup_text.setReadOnly(True)
        setup_layout.addWidget(self.setup_text)
        layout.addWidget(setup_group)

        return widget

    def populate_browse_table(self, category=None):
        """Populate the browse table with datasets."""
        self.browse_table.setRowCount(0)

        if not DATA_SOURCES_AVAILABLE:
            return

        sources = list(DATA_SOURCES.values())
        if category:
            sources = [ds for ds in sources if ds.category == category]

        self.browse_table.setRowCount(len(sources))

        for i, ds in enumerate(sources):
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
"""
            self.details_text.setHtml(details)
            self.search_btn.setEnabled(True)

    def on_workflow_selection(self):
        """Show workflow details when selected."""
        selected = self.workflows_table.selectedItems()
        if not selected or not WORKFLOWS_AVAILABLE:
            return

        row = selected[0].row()
        wf_name = self.workflows_table.item(row, 0).text()

        # Find workflow by name
        for wf_id, wf in ANALYSIS_WORKFLOWS.items():
            if wf.name == wf_name:
                details = f"""<h3>{wf.name}</h3>
<p><b>Category:</b> {wf.category.value}</p>
<p><b>Description:</b> {wf.description}</p>
<p><b>Primary Dataset:</b> {wf.primary_dataset}</p>
<p><b>Fallback Datasets:</b> {', '.join(wf.fallback_datasets)}</p>
<p><b>Indices:</b> {', '.join(wf.indices)}</p>
<p><b>Cloud Cover Max:</b> {wf.cloud_cover_max}%</p>
<p><b>Temporal Requirement:</b> {wf.temporal_requirement}</p>
<h4>Processing Steps:</h4>
<ol>
"""
                for step in wf.steps:
                    details += f"<li><b>{step.name}</b>: {step.description}</li>"
                details += "</ol>"

                # Add index formulas
                details += "<h4>QGIS Raster Calculator Formulas:</h4>"
                for idx in wf.indices:
                    formula = get_qgis_formula(idx, "sentinel2")
                    details += f"<p><b>{idx}:</b> <code>{formula}</code></p>"

                self.workflow_details.setHtml(details)
                self.run_workflow_btn.setEnabled(True)
                break

    def on_provider_selection(self):
        """Show provider setup instructions."""
        selected = self.provider_table.selectedItems()
        if not selected or not WORKFLOWS_AVAILABLE:
            return

        row = selected[0].row()
        prov_id = self.provider_table.item(row, 0).text()

        if prov_id in EODAG_PROVIDERS:
            prov = EODAG_PROVIDERS[prov_id]
            config_mgr = get_config_manager()

            setup = f"""<h3>{prov.name}</h3>
<p><b>URL:</b> <a href="{prov.url}">{prov.url}</a></p>
<p><b>Free Access:</b> {'Yes' if prov.free_access else 'No'}</p>
<p><b>Currently Configured:</b> {'Yes' if config_mgr.is_provider_configured(prov_id) else 'No'}</p>
"""
            if prov.registration_url:
                setup += f"<p><b>Registration:</b> <a href='{prov.registration_url}'>{prov.registration_url}</a></p>"

            setup += f"""
<h4>Configuration:</h4>
<pre>{config_mgr.generate_config_snippet(prov_id)}</pre>

<h4>Available Products:</h4>
<ul>
"""
            for prod_id, prod in list(EODAG_PRODUCTS.items())[:10]:
                if prov_id in prod.providers:
                    setup += f"<li>{prod.title} ({prod_id})</li>"
            setup += "</ul>"

            self.setup_text.setHtml(setup)

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
        self.primary_label.setText(f"Primary Dataset: {primary}")

        # Update workflow
        wf_name = result.get("workflow_name", "-")
        self.workflow_label.setText(f"Matched Workflow: {wf_name}")

        # Update datasets table
        details = result.get("dataset_details", [])
        self.datasets_table.setRowCount(len(details))

        for i, ds in enumerate(details):
            self.datasets_table.setItem(i, 0, QTableWidgetItem(ds.get("name", ds.get("id", ""))))
            self.datasets_table.setItem(i, 1, QTableWidgetItem(ds.get("category", "")))
            self.datasets_table.setItem(i, 2, QTableWidgetItem(str(ds.get("resolution_m", "N/A"))))
            self.datasets_table.setItem(i, 3, QTableWidgetItem(ds.get("provider", "")))
            desc = ds.get("description", "")[:60] + "..." if len(ds.get("description", "")) > 60 else ds.get("description", "")
            self.datasets_table.setItem(i, 4, QTableWidgetItem(desc))

        # Update indices table with formulas
        indices_details = result.get("indices_details", [])
        suggested = result.get("suggested_indices", [])

        if WORKFLOWS_AVAILABLE and not indices_details:
            indices_details = [
                {
                    "name": idx,
                    "full_name": SPECTRAL_INDICES.get(idx, {}).full_name if idx in SPECTRAL_INDICES else idx,
                    "formula": get_qgis_formula(idx, "sentinel2")
                }
                for idx in suggested if idx in SPECTRAL_INDICES
            ]

        self.indices_table.setRowCount(len(indices_details) or len(suggested))

        for i, idx in enumerate(indices_details or suggested):
            if isinstance(idx, dict):
                self.indices_table.setItem(i, 0, QTableWidgetItem(idx.get("name", "")))
                self.indices_table.setItem(i, 1, QTableWidgetItem(idx.get("full_name", "")))
                self.indices_table.setItem(i, 2, QTableWidgetItem(idx.get("formula", "")))
            else:
                self.indices_table.setItem(i, 0, QTableWidgetItem(idx))
                if WORKFLOWS_AVAILABLE and idx in SPECTRAL_INDICES:
                    si = SPECTRAL_INDICES[idx]
                    self.indices_table.setItem(i, 1, QTableWidgetItem(si.full_name))
                    self.indices_table.setItem(i, 2, QTableWidgetItem(get_qgis_formula(idx, "sentinel2")))

        # Update workflow steps
        self.workflow_list.clear()
        for step in result.get("processing_workflow", []):
            self.workflow_list.addItem(step)

        # Update provider status
        provider_status = result.get("provider_status", {})
        if provider_status.get("status") == "available":
            self.provider_status_label.setText(
                f"Ready to use with: {provider_status.get('recommended_provider', 'Unknown')}"
            )
            self.provider_status_label.setStyleSheet("color: green;")
        elif provider_status.get("status") == "setup_required":
            setup_providers = provider_status.get("setup_required", [])
            names = [p.get("name", p.get("provider", "")) for p in setup_providers[:2]]
            self.provider_status_label.setText(
                f"Setup required. Configure one of: {', '.join(names)}"
            )
            self.provider_status_label.setStyleSheet("color: orange;")
        else:
            self.provider_status_label.setText("-")
            self.provider_status_label.setStyleSheet("")

        # Update tips
        self.cloud_label.setText(result.get("cloud_cover_advice", "-"))
        self.temporal_label.setText(result.get("temporal_advice", "-"))

        self.search_btn.setEnabled(True)
        self.run_workflow_btn.setEnabled(bool(result.get("qgis_steps")))

    def on_recommendation_error(self, error_message):
        """Handle recommendation error."""
        self.recommend_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Failed to get recommendations: {error_message}")

    def search_recommended(self):
        """Open search dialog with recommended dataset."""
        selected_id = None

        if self.current_recommendation:
            selected_id = self.current_recommendation.get("primary_recommendation")

        browse_selected = self.browse_table.selectedItems()
        if browse_selected:
            selected_id = self.browse_table.item(browse_selected[0].row(), 0).text()

        if not selected_id or not self.plugin:
            return

        from .geodatahub_dialog import GeoDataHubDialog

        dlg = GeoDataHubDialog(parent=self.parent(), plugin=self.plugin)
        location = self.location_input.toPlainText().strip()
        query = f"{selected_id} {location}" if location else selected_id
        dlg.search_input.setText(query)
        dlg.show()
        dlg.exec_()

    def run_workflow(self):
        """Show QGIS workflow execution guide."""
        if not self.current_recommendation:
            return

        qgis_steps = self.current_recommendation.get("qgis_steps", [])
        indices = self.current_recommendation.get("suggested_indices", [])

        guide = "<h3>QGIS Workflow Guide</h3>"
        guide += "<p>Follow these steps in QGIS:</p><ol>"

        for step in qgis_steps:
            if isinstance(step, dict):
                guide += f"<li><b>{step.get('name', '')}</b>: {step.get('description', '')}"
                if step.get('qgis_algorithm'):
                    guide += f"<br><i>Algorithm: {step.get('qgis_algorithm')}</i>"
                guide += "</li>"
            else:
                guide += f"<li>{step}</li>"

        guide += "</ol>"

        # Add formulas
        if WORKFLOWS_AVAILABLE:
            guide += "<h4>Copy-paste formulas for Raster Calculator:</h4>"
            for idx in indices:
                if idx in SPECTRAL_INDICES:
                    formula = get_qgis_formula(idx, "sentinel2")
                    guide += f"<p><b>{idx}:</b><br><code>{formula}</code></p>"

        QMessageBox.information(self, "QGIS Workflow Guide", guide)
