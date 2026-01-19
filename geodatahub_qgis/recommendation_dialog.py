"""
AI Dataset Recommendation Dialog

Provides intelligent dataset recommendations based on the user's analysis needs.
"""

import os
import json
from datetime import datetime

from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit,
    QPushButton, QGroupBox, QListWidget, QListWidgetItem,
    QProgressBar, QMessageBox, QComboBox, QCheckBox
)
from qgis.PyQt.QtGui import QFont


# Dataset knowledge base for recommendations
DATASET_KNOWLEDGE = {
    "vegetation": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2"],
        "description": "For vegetation analysis, Sentinel-2 provides excellent multispectral data with 10m resolution, ideal for NDVI, crop monitoring, and forest mapping.",
        "indices": ["NDVI", "EVI", "SAVI", "NDWI"],
        "bands": "Red, NIR, Red Edge bands are most useful"
    },
    "urban": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2"],
        "description": "Urban analysis benefits from high-resolution optical imagery. Use SWIR bands for built-up area detection.",
        "indices": ["NDBI", "UI", "BU"],
        "bands": "SWIR, NIR, Red bands for urban indices"
    },
    "water": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2", "S1_SAR_GRD"],
        "description": "Water body mapping can use optical (NDWI, MNDWI) or SAR data. SAR is useful for flood mapping through clouds.",
        "indices": ["NDWI", "MNDWI", "AWEI"],
        "bands": "Green, NIR, SWIR for optical; VV/VH for SAR"
    },
    "flood": {
        "recommended": ["S1_SAR_GRD", "S2_MSI_L2A"],
        "description": "SAR data is preferred for flood mapping as it can penetrate clouds. Sentinel-1 provides regular revisit times.",
        "indices": ["SAR Water Index", "NDWI"],
        "bands": "VV and VH polarization for SAR"
    },
    "elevation": {
        "recommended": ["COP-DEM_GLO-30"],
        "description": "Copernicus DEM provides 30m global elevation data, suitable for terrain analysis, slope, aspect calculations.",
        "indices": ["Slope", "Aspect", "Hillshade", "TRI"],
        "bands": "Single elevation band"
    },
    "terrain": {
        "recommended": ["COP-DEM_GLO-30"],
        "description": "DEM data for terrain analysis including slope, aspect, watershed delineation, and viewshed analysis.",
        "indices": ["Slope", "Aspect", "Curvature", "TWI"],
        "bands": "Elevation values"
    },
    "agriculture": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2"],
        "description": "Agricultural monitoring requires frequent revisit optical data. Sentinel-2 offers 5-day revisit with 10m resolution.",
        "indices": ["NDVI", "EVI", "NDRE", "GNDVI", "LAI"],
        "bands": "Red, NIR, Red Edge for crop health"
    },
    "forest": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2", "S1_SAR_GRD"],
        "description": "Forest monitoring uses optical for health assessment and SAR for structure. Time series analysis is valuable.",
        "indices": ["NDVI", "NBR", "NDMI"],
        "bands": "NIR, SWIR for moisture; SAR for structure"
    },
    "change_detection": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2", "S1_SAR_GRD"],
        "description": "Change detection requires consistent time series. Choose based on phenomenon: optical for land cover, SAR for surface changes.",
        "indices": ["dNBR", "dNDVI", "CVA"],
        "bands": "Consistent bands across time periods"
    },
    "fire": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2"],
        "description": "Fire and burn scar mapping uses SWIR bands. NBR (Normalized Burn Ratio) is the standard index.",
        "indices": ["NBR", "dNBR", "BAI"],
        "bands": "NIR and SWIR bands"
    },
    "snow": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2"],
        "description": "Snow cover mapping uses NDSI (Normalized Difference Snow Index) with Green and SWIR bands.",
        "indices": ["NDSI", "S3"],
        "bands": "Green and SWIR bands"
    },
    "coastal": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2"],
        "description": "Coastal analysis benefits from high-resolution optical data. Consider atmospheric correction for water applications.",
        "indices": ["NDWI", "SDB", "Turbidity"],
        "bands": "Blue, Green, Coastal Aerosol"
    },
    "sar": {
        "recommended": ["S1_SAR_GRD"],
        "description": "SAR (Synthetic Aperture Radar) works in all weather conditions. Useful for surface roughness, moisture, and deformation.",
        "indices": ["Backscatter analysis", "Coherence"],
        "bands": "VV, VH polarization"
    },
    "land_cover": {
        "recommended": ["S2_MSI_L2A", "LANDSAT_C2L2"],
        "description": "Land cover classification uses multispectral data. More bands generally improve classification accuracy.",
        "indices": ["Multiple indices for training"],
        "bands": "All available spectral bands"
    }
}

# LLM prompt for recommendations
RECOMMENDATION_PROMPT = """You are a remote sensing expert. Based on the user's analysis description, recommend the most suitable satellite datasets and provide guidance.

User's analysis: {analysis_description}
Location: {location}

Available datasets:
- S2_MSI_L2A: Sentinel-2 Level 2A (optical, 10m resolution, 5-day revisit)
- S1_SAR_GRD: Sentinel-1 SAR (radar, 10m resolution, works through clouds)
- LANDSAT_C2L2: Landsat 8/9 (optical, 30m resolution, 16-day revisit)
- COP-DEM_GLO-30: Copernicus DEM (elevation, 30m resolution)

Respond in JSON format:
{{
    "recommended_datasets": ["dataset_code1", "dataset_code2"],
    "primary_recommendation": "dataset_code",
    "reasoning": "explanation of why these datasets are suitable",
    "suggested_indices": ["INDEX1", "INDEX2"],
    "useful_bands": "description of useful bands",
    "cloud_cover_advice": "advice on cloud cover threshold",
    "temporal_advice": "advice on time period selection",
    "processing_tips": "tips for processing the data"
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
                result = self.get_keyword_recommendation()

            self.finished.emit(result)

        except Exception as e:
            self.error.emit(str(e))

    def get_llm_recommendation(self):
        """Get recommendation using LLM."""
        try:
            from geodatahub.nlp.llm_client import get_llm_client

            client = get_llm_client()
            if not client:
                return self.get_keyword_recommendation()

            prompt = RECOMMENDATION_PROMPT.format(
                analysis_description=self.analysis_text,
                location=self.location or "Not specified"
            )

            response = client.complete(prompt)

            # Parse JSON from response
            try:
                # Find JSON in response
                start = response.find('{')
                end = response.rfind('}') + 1
                if start >= 0 and end > start:
                    json_str = response[start:end]
                    return json.loads(json_str)
            except json.JSONDecodeError:
                pass

            # Fall back to keyword-based
            return self.get_keyword_recommendation()

        except Exception:
            return self.get_keyword_recommendation()

    def get_keyword_recommendation(self):
        """Get recommendation based on keywords."""
        text_lower = self.analysis_text.lower()

        # Find matching categories
        matched_categories = []
        for category, info in DATASET_KNOWLEDGE.items():
            if category in text_lower:
                matched_categories.append((category, info))

        # Check for specific keywords
        keyword_mappings = {
            "ndvi": "vegetation",
            "crop": "agriculture",
            "farm": "agriculture",
            "tree": "forest",
            "deforest": "forest",
            "city": "urban",
            "building": "urban",
            "flood": "flood",
            "river": "water",
            "lake": "water",
            "ocean": "coastal",
            "coast": "coastal",
            "dem": "elevation",
            "slope": "terrain",
            "height": "elevation",
            "burn": "fire",
            "wildfire": "fire",
            "snow": "snow",
            "ice": "snow",
            "radar": "sar",
            "cloud-free": "sar",
            "all-weather": "sar",
            "change": "change_detection",
            "monitor": "change_detection",
            "classify": "land_cover",
            "land use": "land_cover"
        }

        for keyword, category in keyword_mappings.items():
            if keyword in text_lower and category not in [m[0] for m in matched_categories]:
                if category in DATASET_KNOWLEDGE:
                    matched_categories.append((category, DATASET_KNOWLEDGE[category]))

        # Default to vegetation/general optical if no match
        if not matched_categories:
            matched_categories.append(("vegetation", DATASET_KNOWLEDGE["vegetation"]))

        # Compile recommendation
        all_datasets = set()
        all_indices = set()
        descriptions = []

        for category, info in matched_categories:
            all_datasets.update(info["recommended"])
            all_indices.update(info["indices"])
            descriptions.append(info["description"])

        primary = matched_categories[0][1]["recommended"][0]

        return {
            "recommended_datasets": list(all_datasets),
            "primary_recommendation": primary,
            "reasoning": " ".join(descriptions),
            "suggested_indices": list(all_indices)[:5],
            "useful_bands": matched_categories[0][1].get("bands", ""),
            "cloud_cover_advice": "For optical data, use <20% cloud cover. SAR works in all conditions.",
            "temporal_advice": "Consider seasonal variations for vegetation analysis.",
            "processing_tips": "Apply atmospheric correction for quantitative analysis."
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
        self.setMinimumSize(700, 600)

        layout = QVBoxLayout(self)

        # Instructions
        instructions = QLabel(
            "Describe your analysis goals and the AI will recommend the most suitable "
            "satellite datasets, spectral indices, and processing tips."
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
            "• I want to monitor vegetation health in agricultural fields\n"
            "• I need to map flood extent after heavy rainfall\n"
            "• I want to detect urban expansion over the last 5 years\n"
            "• I need elevation data for watershed analysis"
        )
        self.analysis_input.setMaximumHeight(120)
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

        # Results section
        results_group = QGroupBox("Recommendations")
        results_layout = QVBoxLayout(results_group)

        # Primary recommendation
        self.primary_label = QLabel("Primary Dataset: -")
        self.primary_label.setFont(QFont("", 12, QFont.Bold))
        results_layout.addWidget(self.primary_label)

        # All recommended datasets
        results_layout.addWidget(QLabel("Recommended Datasets:"))
        self.datasets_list = QListWidget()
        self.datasets_list.setMaximumHeight(80)
        results_layout.addWidget(self.datasets_list)

        # Reasoning
        results_layout.addWidget(QLabel("Why these datasets:"))
        self.reasoning_text = QTextEdit()
        self.reasoning_text.setReadOnly(True)
        self.reasoning_text.setMaximumHeight(80)
        results_layout.addWidget(self.reasoning_text)

        # Indices
        results_layout.addWidget(QLabel("Suggested Indices:"))
        self.indices_list = QListWidget()
        self.indices_list.setMaximumHeight(60)
        results_layout.addWidget(self.indices_list)

        # Tips
        results_layout.addWidget(QLabel("Processing Tips:"))
        self.tips_text = QTextEdit()
        self.tips_text.setReadOnly(True)
        self.tips_text.setMaximumHeight(60)
        results_layout.addWidget(self.tips_text)

        layout.addWidget(results_group)

        # Action buttons
        button_layout = QHBoxLayout()

        self.search_btn = QPushButton("Search for This Data")
        self.search_btn.clicked.connect(self.search_recommended)
        self.search_btn.setEnabled(False)
        button_layout.addWidget(self.search_btn)

        button_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

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

        # Update UI
        primary = result.get("primary_recommendation", "S2_MSI_L2A")
        self.primary_label.setText(f"Primary Dataset: {primary}")

        # Datasets
        self.datasets_list.clear()
        for ds in result.get("recommended_datasets", []):
            self.datasets_list.addItem(ds)

        # Reasoning
        self.reasoning_text.setText(result.get("reasoning", ""))

        # Indices
        self.indices_list.clear()
        for idx in result.get("suggested_indices", []):
            self.indices_list.addItem(idx)

        # Tips
        tips = []
        if result.get("cloud_cover_advice"):
            tips.append(f"Cloud cover: {result['cloud_cover_advice']}")
        if result.get("temporal_advice"):
            tips.append(f"Temporal: {result['temporal_advice']}")
        if result.get("processing_tips"):
            tips.append(f"Processing: {result['processing_tips']}")
        if result.get("useful_bands"):
            tips.append(f"Bands: {result['useful_bands']}")

        self.tips_text.setText("\n".join(tips))

        self.search_btn.setEnabled(True)

    def on_recommendation_error(self, error_message):
        """Handle recommendation error."""
        self.recommend_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Error", f"Failed to get recommendations: {error_message}")

    def search_recommended(self):
        """Open search dialog with recommended dataset."""
        if not self.current_recommendation or not self.plugin:
            return

        # Get the main dialog
        from .geodatahub_dialog import GeoDataHubDialog

        dlg = GeoDataHubDialog(parent=self.parent(), plugin=self.plugin)

        # Pre-fill with recommendation
        primary = self.current_recommendation.get("primary_recommendation", "S2_MSI_L2A")
        location = self.location_input.toPlainText().strip()

        query = f"{primary} {location}" if location else primary
        dlg.search_input.setText(query)

        dlg.show()
        dlg.exec_()
