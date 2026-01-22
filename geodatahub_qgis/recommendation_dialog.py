"""
AI Dataset Recommendation Dialog - Chat-based Interface

Provides an intelligent chatbot interface for:
- Natural language conversations about remote sensing analysis
- AI-powered dataset recommendations
- Workflow suggestions with QGIS formulas
- Knowledge-based answers about satellite data
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
    QTabWidget, QWidget, QScrollArea, QFrame, QSplitter,
    QLineEdit, QTextBrowser
)
from qgis.PyQt.QtGui import QFont, QColor, QTextCursor


# Import geodatahub modules
import sys
plugin_dir = os.path.dirname(__file__)
parent_dir = os.path.dirname(plugin_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Debug: Log the import path
_IMPORT_ERROR = None
_IMPORT_DEBUG = f"Plugin dir: {plugin_dir}, Parent dir: {parent_dir}"

# Try importing modules
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
except ImportError as e:
    _IMPORT_ERROR = str(e)
    WORKFLOWS_AVAILABLE = False
    ANALYSIS_WORKFLOWS = {}
    SPECTRAL_INDICES = {}
    EODAG_PROVIDERS = {}
    EODAG_PRODUCTS = {}

    def get_workflow_recommendation(query):
        return {"status": "no_match"}

    def get_qgis_formula(index_name, sensor="sentinel2"):
        return ""

    def check_product_access(product_id):
        return {"status": "unknown"}

    def get_config_manager():
        return None

# Try importing LLM client
try:
    from geodatahub.nlp.llm_client import get_llm_client
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    def get_llm_client(provider="auto"):
        return None


# =============================================================================
# REMOTE SENSING KNOWLEDGE BASE
# =============================================================================

REMOTE_SENSING_KNOWLEDGE = """
You are an expert remote sensing and GIS analyst assistant integrated into QGIS.
You help users with satellite data analysis, dataset selection, and processing workflows.

## Your Capabilities:
1. Recommend appropriate satellite datasets for specific analyses
2. Explain spectral indices and their applications
3. Provide QGIS processing workflow guidance
4. Answer questions about remote sensing concepts
5. Help with data provider setup and configuration

## Available Datasets (EODAG):
- **Sentinel-2 MSI (S2_MSI_L2A)**: 10m optical, best for vegetation, agriculture, land cover
- **Sentinel-1 SAR (S1_SAR_GRD)**: 10m radar, works through clouds, flood/water mapping
- **Landsat Collection 2 (LANDSAT_C2L2)**: 30m optical, long historical archive since 1972
- **MODIS (MODIS_MOD09GA)**: 500m daily, large area monitoring
- **Copernicus DEM (COP_DEM_GLO30)**: 30m elevation data
- **Sentinel-3 OLCI**: 300m, ocean color and water quality
- **Sentinel-5P**: Atmospheric data (NO2, O3, CO, CH4)
- **ERA5**: Climate reanalysis data
- **VIIRS DNB**: Nighttime lights

## Key Spectral Indices:
- **NDVI** = (NIR-RED)/(NIR+RED): Vegetation health, values 0.2-0.8 = healthy vegetation
- **NDWI** = (GREEN-NIR)/(GREEN+NIR): Water detection, >0.3 = water
- **MNDWI** = (GREEN-SWIR)/(GREEN+SWIR): Better water/urban discrimination
- **NDBI** = (SWIR-NIR)/(SWIR+NIR): Built-up areas, >0 = urban
- **NBR** = (NIR-SWIR2)/(NIR+SWIR2): Burn severity assessment
- **EVI**: Enhanced vegetation index, better for high biomass areas
- **SAVI**: Soil-adjusted vegetation index for sparse vegetation

## Analysis Workflows:
1. **Vegetation/Crop Health**: Use Sentinel-2, calculate NDVI/EVI, multi-temporal analysis
2. **Water Detection**: Use Sentinel-2 with MNDWI, or Sentinel-1 SAR for cloudy conditions
3. **Urban Mapping**: Use Sentinel-2 with NDBI and NDVI combination
4. **Flood Mapping**: Use Sentinel-1 SAR (all-weather), compare pre/post images
5. **Fire/Burn Assessment**: Use Sentinel-2 with NBR, calculate dNBR for severity
6. **Terrain Analysis**: Use Copernicus DEM for slope, aspect, hillshade

## QGIS Raster Calculator Formulas (Sentinel-2):
- NDVI: (B08@1 - B04@1) / (B08@1 + B04@1)
- NDWI: (B03@1 - B08@1) / (B03@1 + B08@1)
- MNDWI: (B03@1 - B11@1) / (B03@1 + B11@1)
- NDBI: (B11@1 - B08@1) / (B11@1 + B08@1)
- NBR: (B08@1 - B12@1) / (B08@1 + B12@1)

## Data Providers:
- **Copernicus Data Space**: Free, requires registration, all Sentinel data
- **Earth Search (AWS)**: Free, no auth needed for some products
- **Planetary Computer**: Free, Microsoft's geospatial platform
- **USGS Earth Explorer**: Free, Landsat data

When recommending datasets, always consider:
1. Required spatial resolution
2. Temporal requirements (single date vs time series)
3. Cloud cover constraints (suggest SAR for cloudy regions)
4. Data availability and access
"""


def build_ai_prompt(user_message: str, conversation_history: list) -> str:
    """Build a comprehensive prompt for the AI."""

    # Build available data context
    datasets_info = ""
    if WORKFLOWS_AVAILABLE and EODAG_PRODUCTS:
        datasets_info = "\n## Currently Available Datasets:\n"
        for pid, p in list(EODAG_PRODUCTS.items())[:15]:
            datasets_info += f"- {p.title} ({pid}): {p.resolution_m}m, {p.sensor_type}, providers: {', '.join(p.providers[:2])}\n"

    workflows_info = ""
    if WORKFLOWS_AVAILABLE and ANALYSIS_WORKFLOWS:
        workflows_info = "\n## Predefined Workflows:\n"
        for wid, w in ANALYSIS_WORKFLOWS.items():
            workflows_info += f"- {w.name}: {w.description[:100]}... Indices: {', '.join(w.indices)}\n"

    # Build conversation context
    history_text = ""
    if conversation_history:
        history_text = "\n## Previous Conversation:\n"
        for msg in conversation_history[-6:]:  # Last 6 messages
            role = "User" if msg["role"] == "user" else "Assistant"
            history_text += f"{role}: {msg['content'][:300]}\n"

    prompt = f"""{REMOTE_SENSING_KNOWLEDGE}
{datasets_info}
{workflows_info}
{history_text}

## Current User Message:
{user_message}

## Instructions:
- If the user asks about analysis or datasets, recommend specific datasets with IDs (like S2_MSI_L2A)
- If recommending spectral indices, provide the QGIS raster calculator formula
- If the user has a complex question, answer from your remote sensing knowledge
- Be conversational and helpful
- Always be specific with dataset names and processing steps
- If suggesting workflows, include step-by-step QGIS instructions

Respond naturally and helpfully:"""

    return prompt


class AIWorker(QThread):
    """Background worker for AI responses."""

    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt: str):
        super().__init__()
        self.prompt = prompt

    def run(self):
        try:
            client = get_llm_client("auto")
            if client:
                response = client.complete(self.prompt)
                self.response_ready.emit(response)
            else:
                # Fallback to rule-based response
                response = self.generate_fallback_response()
                self.response_ready.emit(response)
        except Exception as e:
            self.error_occurred.emit(str(e))

    def generate_fallback_response(self):
        """Generate rule-based response when LLM not available."""
        prompt_lower = self.prompt.lower()

        # Check for workflow matches
        if WORKFLOWS_AVAILABLE:
            rec = get_workflow_recommendation(prompt_lower)
            if rec.get("status") == "matched":
                wf = rec.get("recommended_workflow", {})
                indices_info = ""
                for idx in wf.get("indices", []):
                    formula = get_qgis_formula(idx, "sentinel2")
                    if formula:
                        indices_info += f"\n- **{idx}**: `{formula}`"

                return f"""Based on your query, I recommend the **{wf.get('name')}** workflow.

**Primary Dataset:** {wf.get('primary_dataset')}
**Alternative Datasets:** {', '.join(wf.get('fallback_datasets', []))}

**Recommended Spectral Indices:**{indices_info}

**Processing Steps:**
{chr(10).join(f"{i+1}. {s.get('name')}: {s.get('description')}" for i, s in enumerate(wf.get('steps', [])))}

**Tips:**
- Use cloud cover < {wf.get('cloud_cover_max', 20)}% for optical data
- Temporal requirement: {wf.get('temporal_requirement', 'single')}

Would you like more details about any of these steps?"""

        # Generic helpful response
        return """I can help you with remote sensing analysis! Here are some things I can assist with:

1. **Dataset Recommendations** - Tell me what you want to analyze (vegetation, water, urban areas, etc.)
2. **Spectral Indices** - I can provide QGIS formulas for NDVI, NDWI, NDBI, NBR, etc.
3. **Workflow Guidance** - Step-by-step processing instructions for QGIS
4. **Data Access** - Help with setting up data providers

Try asking something like:
- "I want to monitor crop health in my farm"
- "How do I detect water bodies?"
- "What's the best data for flood mapping?"
- "Give me the NDVI formula for Sentinel-2"

Note: For full AI capabilities, please configure your GROQ_API_KEY."""


class RecommendationDialog(QDialog):
    """Chat-based AI recommendation dialog for QGIS."""

    def __init__(self, parent=None, plugin=None):
        super().__init__(parent)
        self.plugin = plugin
        self.conversation_history = []
        self.current_recommendations = {}

        self.setup_ui()

    def setup_ui(self):
        """Set up the dialog UI."""
        self.setWindowTitle("GeoDataHub AI Assistant")
        self.setMinimumSize(900, 700)

        layout = QVBoxLayout(self)

        # Create tabs
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # Tab 1: AI Chat (Main)
        chat_tab = self.create_chat_tab()
        tabs.addTab(chat_tab, "AI Assistant")

        # Tab 2: Browse Datasets
        browse_tab = self.create_browse_tab()
        tabs.addTab(browse_tab, "Browse Datasets")

        # Tab 3: Provider Status
        provider_tab = self.create_provider_tab()
        tabs.addTab(provider_tab, "Provider Status")

        # Status bar
        self.status_label = QLabel("")
        layout.addWidget(self.status_label)

    def create_chat_tab(self):
        """Create the main AI chat interface."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Header with status
        header_layout = QHBoxLayout()

        title = QLabel("<h3>GeoDataHub AI Assistant</h3>")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # LLM status indicator
        if LLM_AVAILABLE:
            client = get_llm_client("auto")
            if client:
                status = QLabel("AI: Connected")
                status.setStyleSheet("color: green; font-weight: bold;")
            else:
                status = QLabel("AI: Using fallback (set GROQ_API_KEY for full AI)")
                status.setStyleSheet("color: orange;")
        else:
            status = QLabel("AI: Limited mode")
            status.setStyleSheet("color: orange;")
        header_layout.addWidget(status)

        layout.addLayout(header_layout)

        # Chat display area
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setMinimumHeight(350)

        # Welcome message
        welcome = """<div style="padding: 10px; background-color: #e8f4f8; border-radius: 8px; margin: 5px;">
<b>Welcome to GeoDataHub AI Assistant!</b><br><br>
I'm your intelligent remote sensing analyst. I can help you with:
<ul>
<li><b>Dataset recommendations</b> - Tell me what you want to analyze</li>
<li><b>Spectral indices</b> - NDVI, NDWI, NDBI formulas for QGIS</li>
<li><b>Processing workflows</b> - Step-by-step QGIS guidance</li>
<li><b>Remote sensing questions</b> - Ask me anything!</li>
</ul>
<br>
<b>Try asking:</b>
<ul>
<li>"I want to monitor vegetation health in agricultural fields"</li>
<li>"What's the best satellite data for flood mapping?"</li>
<li>"How do I calculate NDVI in QGIS?"</li>
<li>"Compare Sentinel-2 and Landsat for my analysis"</li>
</ul>
</div>"""
        self.chat_display.setHtml(welcome)
        layout.addWidget(self.chat_display)

        # Recommendations panel (collapsible)
        self.rec_panel = QGroupBox("Current Recommendations")
        rec_layout = QVBoxLayout(self.rec_panel)

        self.rec_table = QTableWidget()
        self.rec_table.setColumnCount(4)
        self.rec_table.setHorizontalHeaderLabels(["Dataset", "Resolution", "Type", "Use For"])
        self.rec_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.rec_table.setMaximumHeight(120)
        self.rec_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        rec_layout.addWidget(self.rec_table)

        self.rec_panel.setVisible(False)
        layout.addWidget(self.rec_panel)

        # Input area
        input_group = QGroupBox("Ask me anything about remote sensing analysis")
        input_layout = QVBoxLayout(input_group)

        # Message input
        msg_layout = QHBoxLayout()

        self.message_input = QLineEdit()
        self.message_input.setPlaceholderText("Type your question here... (e.g., 'I want to detect deforestation over time')")
        self.message_input.returnPressed.connect(self.send_message)
        msg_layout.addWidget(self.message_input)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setMinimumWidth(80)
        msg_layout.addWidget(self.send_btn)

        input_layout.addLayout(msg_layout)

        # Quick action buttons
        quick_layout = QHBoxLayout()
        quick_layout.addWidget(QLabel("Quick:"))

        quick_buttons = [
            ("Vegetation Analysis", "What datasets and indices should I use for vegetation health monitoring?"),
            ("Water Detection", "How do I detect and map water bodies?"),
            ("Urban Mapping", "What's the best approach for mapping urban areas?"),
            ("Flood Mapping", "I need to map flood extent, what should I use?"),
        ]

        for label, query in quick_buttons:
            btn = QPushButton(label)
            btn.setMaximumWidth(120)
            btn.clicked.connect(lambda checked, q=query: self.quick_query(q))
            quick_layout.addWidget(btn)

        quick_layout.addStretch()
        input_layout.addLayout(quick_layout)

        layout.addWidget(input_group)

        # Progress
        self.progress = QProgressBar()
        self.progress.setVisible(False)
        layout.addWidget(self.progress)

        # Action buttons
        action_layout = QHBoxLayout()

        self.search_btn = QPushButton("Search for Recommended Data")
        self.search_btn.clicked.connect(self.search_recommended)
        self.search_btn.setEnabled(False)
        action_layout.addWidget(self.search_btn)

        clear_btn = QPushButton("Clear Chat")
        clear_btn.clicked.connect(self.clear_chat)
        action_layout.addWidget(clear_btn)

        action_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        action_layout.addWidget(close_btn)

        layout.addLayout(action_layout)

        return widget

    def create_browse_tab(self):
        """Create the browse datasets tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Filter
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter by sensor type:"))

        self.sensor_combo = QComboBox()
        self.sensor_combo.addItem("All Types", None)
        if WORKFLOWS_AVAILABLE and EODAG_PRODUCTS:
            sensor_types = sorted(set(p.sensor_type for p in EODAG_PRODUCTS.values() if p.sensor_type))
            for st in sensor_types:
                self.sensor_combo.addItem(st.title(), st)
        self.sensor_combo.currentIndexChanged.connect(self.filter_datasets)
        filter_layout.addWidget(self.sensor_combo)

        filter_layout.addStretch()
        layout.addLayout(filter_layout)

        # Datasets table
        self.browse_table = QTableWidget()
        self.browse_table.setColumnCount(6)
        self.browse_table.setHorizontalHeaderLabels([
            "ID", "Name", "Type", "Resolution", "Providers", "Keywords"
        ])
        self.browse_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.browse_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.browse_table.itemSelectionChanged.connect(self.on_dataset_selected)
        layout.addWidget(self.browse_table)

        # Dataset details
        details_group = QGroupBox("Dataset Details")
        details_layout = QVBoxLayout(details_group)
        self.dataset_details = QTextBrowser()
        self.dataset_details.setMaximumHeight(150)
        details_layout.addWidget(self.dataset_details)
        layout.addWidget(details_group)

        # Populate
        self.populate_datasets()

        return widget

    def create_provider_tab(self):
        """Create provider status tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        layout.addWidget(QLabel("EODAG Provider Configuration Status:"))

        self.provider_table = QTableWidget()
        self.provider_table.setColumnCount(5)
        self.provider_table.setHorizontalHeaderLabels([
            "Provider", "Name", "Free", "Configured", "Products"
        ])
        self.provider_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.provider_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.provider_table.itemSelectionChanged.connect(self.on_provider_selected)
        layout.addWidget(self.provider_table)

        # Setup instructions
        setup_group = QGroupBox("Setup Instructions")
        setup_layout = QVBoxLayout(setup_group)
        self.setup_text = QTextBrowser()
        setup_layout.addWidget(self.setup_text)
        layout.addWidget(setup_group)

        # Populate providers
        self.populate_providers()

        return widget

    def populate_datasets(self, sensor_type=None):
        """Populate datasets table."""
        self.browse_table.setRowCount(0)

        if not WORKFLOWS_AVAILABLE or not EODAG_PRODUCTS:
            return

        products = list(EODAG_PRODUCTS.values())
        if sensor_type:
            products = [p for p in products if p.sensor_type == sensor_type]

        self.browse_table.setRowCount(len(products))

        for i, p in enumerate(products):
            self.browse_table.setItem(i, 0, QTableWidgetItem(p.id))
            self.browse_table.setItem(i, 1, QTableWidgetItem(p.title))
            self.browse_table.setItem(i, 2, QTableWidgetItem(p.sensor_type))
            self.browse_table.setItem(i, 3, QTableWidgetItem(f"{p.resolution_m}m" if p.resolution_m else "N/A"))
            self.browse_table.setItem(i, 4, QTableWidgetItem(", ".join(p.providers[:2])))
            self.browse_table.setItem(i, 5, QTableWidgetItem(", ".join(p.keywords[:3])))

    def populate_providers(self):
        """Populate providers table."""
        self.provider_table.setRowCount(0)

        if not WORKFLOWS_AVAILABLE or not EODAG_PROVIDERS:
            return

        config_mgr = get_config_manager()
        self.provider_table.setRowCount(len(EODAG_PROVIDERS))

        for i, (prov_id, prov) in enumerate(EODAG_PROVIDERS.items()):
            is_configured = config_mgr.is_provider_configured(prov_id) if config_mgr else False
            products_count = len([p for p in EODAG_PRODUCTS.values() if prov_id in p.providers])

            self.provider_table.setItem(i, 0, QTableWidgetItem(prov_id))
            self.provider_table.setItem(i, 1, QTableWidgetItem(prov.name))
            self.provider_table.setItem(i, 2, QTableWidgetItem("Yes" if prov.free_access else "No"))

            status_item = QTableWidgetItem("Yes" if is_configured else "No")
            status_item.setBackground(QColor(200, 255, 200) if is_configured else QColor(255, 200, 200))
            self.provider_table.setItem(i, 3, status_item)

            self.provider_table.setItem(i, 4, QTableWidgetItem(str(products_count)))

    def filter_datasets(self):
        """Filter datasets by sensor type."""
        sensor_type = self.sensor_combo.currentData()
        self.populate_datasets(sensor_type)

    def on_dataset_selected(self):
        """Show dataset details."""
        selected = self.browse_table.selectedItems()
        if not selected or not WORKFLOWS_AVAILABLE:
            return

        row = selected[0].row()
        ds_id = self.browse_table.item(row, 0).text()

        if ds_id in EODAG_PRODUCTS:
            p = EODAG_PRODUCTS[ds_id]
            details = f"""<h3>{p.title}</h3>
<p><b>ID:</b> {p.id}</p>
<p><b>Platform:</b> {p.platform} | <b>Instrument:</b> {p.instrument}</p>
<p><b>Sensor Type:</b> {p.sensor_type} | <b>Resolution:</b> {p.resolution_m}m</p>
<p><b>Description:</b> {p.description}</p>
<p><b>Providers:</b> {', '.join(p.providers)}</p>
<p><b>Keywords:</b> {', '.join(p.keywords)}</p>"""
            self.dataset_details.setHtml(details)
            self.search_btn.setEnabled(True)

    def on_provider_selected(self):
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
<p><b>Configured:</b> {'Yes' if config_mgr and config_mgr.is_provider_configured(prov_id) else 'No'}</p>
"""
            if prov.registration_url:
                setup += f"<p><b>Register at:</b> <a href='{prov.registration_url}'>{prov.registration_url}</a></p>"

            if config_mgr:
                setup += f"<h4>Configuration (add to eodag.yml):</h4><pre>{config_mgr.generate_config_snippet(prov_id)}</pre>"

            self.setup_text.setHtml(setup)

    def quick_query(self, query):
        """Handle quick query button click."""
        self.message_input.setText(query)
        self.send_message()

    def send_message(self):
        """Send message to AI."""
        message = self.message_input.text().strip()
        if not message:
            return

        # Add user message to chat
        self.add_message("user", message)
        self.message_input.clear()

        # Store in history
        self.conversation_history.append({"role": "user", "content": message})

        # Build prompt and send to AI
        prompt = build_ai_prompt(message, self.conversation_history)

        self.progress.setVisible(True)
        self.progress.setRange(0, 0)
        self.send_btn.setEnabled(False)
        self.status_label.setText("AI is thinking...")

        self.worker = AIWorker(prompt)
        self.worker.response_ready.connect(self.on_ai_response)
        self.worker.error_occurred.connect(self.on_ai_error)
        self.worker.start()

    def on_ai_response(self, response):
        """Handle AI response."""
        self.progress.setVisible(False)
        self.send_btn.setEnabled(True)
        self.status_label.setText("")

        # Add AI response to chat
        self.add_message("assistant", response)

        # Store in history
        self.conversation_history.append({"role": "assistant", "content": response})

        # Extract and display recommendations
        self.extract_recommendations(response)

    def on_ai_error(self, error):
        """Handle AI error."""
        self.progress.setVisible(False)
        self.send_btn.setEnabled(True)
        self.status_label.setText(f"Error: {error}")

        self.add_message("system", f"Sorry, I encountered an error: {error}\n\nPlease try again or rephrase your question.")

    def add_message(self, role, content):
        """Add a message to the chat display."""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(QTextCursor.End)

        # Format based on role
        if role == "user":
            html = f"""<div style="background-color: #e3f2fd; padding: 10px; border-radius: 8px; margin: 5px 50px 5px 5px;">
<b>You:</b><br>{content.replace(chr(10), '<br>')}
</div>"""
        elif role == "assistant":
            # Convert markdown-style formatting
            formatted = content.replace("\n", "<br>")
            formatted = formatted.replace("**", "<b>").replace("</b><b>", "")
            formatted = formatted.replace("`", "<code>").replace("</code><code>", "")

            html = f"""<div style="background-color: #f5f5f5; padding: 10px; border-radius: 8px; margin: 5px 5px 5px 50px;">
<b>AI Assistant:</b><br>{formatted}
</div>"""
        else:  # system
            html = f"""<div style="background-color: #ffebee; padding: 10px; border-radius: 8px; margin: 5px;">
<b>System:</b><br>{content.replace(chr(10), '<br>')}
</div>"""

        self.chat_display.append(html)

        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def extract_recommendations(self, response):
        """Extract dataset recommendations from AI response."""
        response_lower = response.lower()

        found_datasets = []
        if WORKFLOWS_AVAILABLE and EODAG_PRODUCTS:
            for ds_id, ds in EODAG_PRODUCTS.items():
                if ds_id.lower() in response_lower or ds.title.lower() in response_lower:
                    found_datasets.append(ds)

        if found_datasets:
            self.rec_panel.setVisible(True)
            self.rec_table.setRowCount(len(found_datasets))

            for i, ds in enumerate(found_datasets[:5]):
                self.rec_table.setItem(i, 0, QTableWidgetItem(ds.id))
                self.rec_table.setItem(i, 1, QTableWidgetItem(f"{ds.resolution_m}m" if ds.resolution_m else "N/A"))
                self.rec_table.setItem(i, 2, QTableWidgetItem(ds.sensor_type))
                self.rec_table.setItem(i, 3, QTableWidgetItem(", ".join(ds.keywords[:3])))

            self.current_recommendations = {ds.id: ds for ds in found_datasets}
            self.search_btn.setEnabled(True)
        else:
            self.rec_panel.setVisible(False)

    def clear_chat(self):
        """Clear the chat history."""
        self.conversation_history = []
        self.chat_display.clear()
        self.rec_panel.setVisible(False)
        self.search_btn.setEnabled(False)

        # Re-add welcome message
        welcome = """<div style="padding: 10px; background-color: #e8f4f8; border-radius: 8px; margin: 5px;">
<b>Chat cleared!</b> How can I help you with your remote sensing analysis?
</div>"""
        self.chat_display.setHtml(welcome)

    def search_recommended(self):
        """Open search dialog with recommended dataset."""
        selected = self.rec_table.selectedItems()
        if selected:
            ds_id = self.rec_table.item(selected[0].row(), 0).text()
        elif self.current_recommendations:
            ds_id = list(self.current_recommendations.keys())[0]
        else:
            return

        if self.plugin:
            try:
                from .geodatahub_dialog import GeoDataHubDialog
                dlg = GeoDataHubDialog(parent=self.parent(), plugin=self.plugin)
                dlg.search_input.setText(ds_id)
                dlg.show()
                dlg.exec_()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not open search dialog: {e}")
