"""
Analysis Workflow Templates

Basic workflows for common geospatial analysis tasks.
Each workflow defines:
- Keywords to match user intent
- Required datasets
- Spectral indices
- QGIS processing steps
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class AnalysisCategory(Enum):
    """Categories of geospatial analysis."""
    VEGETATION = "vegetation"
    WATER = "water"
    URBAN = "urban"
    FLOOD = "flood"
    TERRAIN = "terrain"
    FIRE = "fire"


@dataclass
class SpectralIndex:
    """Definition of a spectral index."""
    name: str
    full_name: str
    formula: str
    description: str
    bands_sentinel2: Dict[str, str]  # variable -> band
    bands_landsat: Dict[str, str]
    value_range: tuple = (-1, 1)
    interpretation: Dict[str, str] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """A single step in a processing workflow."""
    order: int
    name: str
    description: str
    qgis_algorithm: Optional[str] = None  # QGIS processing algorithm ID
    parameters: Dict = field(default_factory=dict)
    optional: bool = False


@dataclass
class AnalysisWorkflow:
    """Complete workflow for an analysis type."""
    id: str
    name: str
    description: str
    category: AnalysisCategory
    keywords: List[str]

    # Data requirements
    primary_dataset: str
    fallback_datasets: List[str]
    alternate_dataset_sar: Optional[str] = None  # For cloud-free alternative

    # Processing
    indices: List[str]
    steps: List[WorkflowStep] = field(default_factory=list)

    # Recommendations
    cloud_cover_max: int = 20
    temporal_requirement: str = "single"  # single, multi-date, before_after
    min_resolution_m: int = 30


# =============================================================================
# SPECTRAL INDICES LIBRARY
# =============================================================================

SPECTRAL_INDICES: Dict[str, SpectralIndex] = {
    # -------------------------------------------------------------------------
    # VEGETATION INDICES
    # -------------------------------------------------------------------------
    "NDVI": SpectralIndex(
        name="NDVI",
        full_name="Normalized Difference Vegetation Index",
        formula="(NIR - RED) / (NIR + RED)",
        description="Most common vegetation health indicator",
        bands_sentinel2={"NIR": "B08", "RED": "B04"},
        bands_landsat={"NIR": "B5", "RED": "B4"},
        value_range=(-1, 1),
        interpretation={
            "<0": "Water, snow, clouds",
            "0-0.1": "Bare soil, rock",
            "0.1-0.2": "Sparse vegetation",
            "0.2-0.4": "Moderate vegetation",
            "0.4-0.6": "Dense vegetation",
            ">0.6": "Very healthy, dense vegetation"
        }
    ),

    "EVI": SpectralIndex(
        name="EVI",
        full_name="Enhanced Vegetation Index",
        formula="2.5 * (NIR - RED) / (NIR + 6*RED - 7.5*BLUE + 1)",
        description="Better for high biomass areas, reduces atmospheric effects",
        bands_sentinel2={"NIR": "B08", "RED": "B04", "BLUE": "B02"},
        bands_landsat={"NIR": "B5", "RED": "B4", "BLUE": "B2"},
        value_range=(-1, 1),
        interpretation={
            "<0.2": "Low vegetation",
            "0.2-0.4": "Moderate vegetation",
            ">0.4": "High vegetation"
        }
    ),

    "SAVI": SpectralIndex(
        name="SAVI",
        full_name="Soil Adjusted Vegetation Index",
        formula="((NIR - RED) / (NIR + RED + 0.5)) * 1.5",
        description="Minimizes soil brightness influence",
        bands_sentinel2={"NIR": "B08", "RED": "B04"},
        bands_landsat={"NIR": "B5", "RED": "B4"},
        value_range=(-1, 1),
        interpretation={
            "<0.2": "Bare soil",
            "0.2-0.4": "Sparse vegetation",
            ">0.4": "Dense vegetation"
        }
    ),

    "NDRE": SpectralIndex(
        name="NDRE",
        full_name="Normalized Difference Red Edge",
        formula="(NIR - RED_EDGE) / (NIR + RED_EDGE)",
        description="Sensitive to chlorophyll content, good for crop stress",
        bands_sentinel2={"NIR": "B08", "RED_EDGE": "B05"},
        bands_landsat={},  # Not available
        value_range=(-1, 1),
        interpretation={
            "<0.2": "Stressed vegetation",
            "0.2-0.4": "Moderate health",
            ">0.4": "Healthy vegetation"
        }
    ),

    # -------------------------------------------------------------------------
    # WATER INDICES
    # -------------------------------------------------------------------------
    "NDWI": SpectralIndex(
        name="NDWI",
        full_name="Normalized Difference Water Index",
        formula="(GREEN - NIR) / (GREEN + NIR)",
        description="Detects water bodies, sensitive to vegetation moisture",
        bands_sentinel2={"GREEN": "B03", "NIR": "B08"},
        bands_landsat={"GREEN": "B3", "NIR": "B5"},
        value_range=(-1, 1),
        interpretation={
            ">0.3": "Water",
            "0-0.3": "Wet/moist",
            "<0": "Non-water"
        }
    ),

    "MNDWI": SpectralIndex(
        name="MNDWI",
        full_name="Modified NDWI",
        formula="(GREEN - SWIR) / (GREEN + SWIR)",
        description="Better discrimination of water from built-up areas",
        bands_sentinel2={"GREEN": "B03", "SWIR": "B11"},
        bands_landsat={"GREEN": "B3", "SWIR": "B6"},
        value_range=(-1, 1),
        interpretation={
            ">0": "Water",
            "<0": "Non-water"
        }
    ),

    # -------------------------------------------------------------------------
    # URBAN/BUILT-UP INDICES
    # -------------------------------------------------------------------------
    "NDBI": SpectralIndex(
        name="NDBI",
        full_name="Normalized Difference Built-up Index",
        formula="(SWIR - NIR) / (SWIR + NIR)",
        description="Highlights urban/built-up areas",
        bands_sentinel2={"SWIR": "B11", "NIR": "B08"},
        bands_landsat={"SWIR": "B6", "NIR": "B5"},
        value_range=(-1, 1),
        interpretation={
            ">0": "Built-up area",
            "<0": "Non-built-up"
        }
    ),

    "UI": SpectralIndex(
        name="UI",
        full_name="Urban Index",
        formula="(SWIR2 - NIR) / (SWIR2 + NIR)",
        description="Urban area detection",
        bands_sentinel2={"SWIR2": "B12", "NIR": "B08"},
        bands_landsat={"SWIR2": "B7", "NIR": "B5"},
        value_range=(-1, 1),
        interpretation={
            ">0": "Urban",
            "<0": "Non-urban"
        }
    ),

    # -------------------------------------------------------------------------
    # FIRE/BURN INDICES
    # -------------------------------------------------------------------------
    "NBR": SpectralIndex(
        name="NBR",
        full_name="Normalized Burn Ratio",
        formula="(NIR - SWIR) / (NIR + SWIR)",
        description="Burn severity assessment",
        bands_sentinel2={"NIR": "B08", "SWIR": "B12"},
        bands_landsat={"NIR": "B5", "SWIR": "B7"},
        value_range=(-1, 1),
        interpretation={
            ">0.1": "Unburned",
            "0 to 0.1": "Low severity",
            "-0.1 to 0": "Moderate severity",
            "<-0.1": "High severity"
        }
    ),

    "dNBR": SpectralIndex(
        name="dNBR",
        full_name="Differenced NBR",
        formula="NBR_pre - NBR_post",
        description="Change in burn ratio between pre and post fire",
        bands_sentinel2={"NIR": "B08", "SWIR": "B12"},
        bands_landsat={"NIR": "B5", "SWIR": "B7"},
        value_range=(-2, 2),
        interpretation={
            "<-0.25": "High post-fire regrowth",
            "-0.25 to 0.1": "Unburned",
            "0.1 to 0.27": "Low severity",
            "0.27 to 0.44": "Moderate-low severity",
            "0.44 to 0.66": "Moderate-high severity",
            ">0.66": "High severity"
        }
    ),

    # -------------------------------------------------------------------------
    # MOISTURE INDICES
    # -------------------------------------------------------------------------
    "NDMI": SpectralIndex(
        name="NDMI",
        full_name="Normalized Difference Moisture Index",
        formula="(NIR - SWIR) / (NIR + SWIR)",
        description="Vegetation water content",
        bands_sentinel2={"NIR": "B08", "SWIR": "B11"},
        bands_landsat={"NIR": "B5", "SWIR": "B6"},
        value_range=(-1, 1),
        interpretation={
            ">0.4": "High moisture",
            "0.2-0.4": "Moderate moisture",
            "0-0.2": "Low moisture",
            "<0": "Water stress"
        }
    ),
}


# =============================================================================
# ANALYSIS WORKFLOWS (Basic - 6 Categories)
# =============================================================================

ANALYSIS_WORKFLOWS: Dict[str, AnalysisWorkflow] = {
    # -------------------------------------------------------------------------
    # 1. VEGETATION / CROP HEALTH
    # -------------------------------------------------------------------------
    "vegetation_health": AnalysisWorkflow(
        id="vegetation_health",
        name="Vegetation & Crop Health Analysis",
        description="Assess vegetation health, crop condition, and agricultural monitoring",
        category=AnalysisCategory.VEGETATION,
        keywords=[
            "vegetation", "crop", "agriculture", "plant", "forest", "tree",
            "ndvi", "greenness", "health", "farm", "field", "biomass",
            "chlorophyll", "growth", "phenology", "harvest", "yield"
        ],
        primary_dataset="S2_MSI_L2A",
        fallback_datasets=["LANDSAT_C2L2", "MODIS_MOD09GA"],
        indices=["NDVI", "EVI", "SAVI", "NDRE"],
        cloud_cover_max=20,
        temporal_requirement="multi-date",
        steps=[
            WorkflowStep(
                order=1,
                name="Load imagery",
                description="Load Sentinel-2 or Landsat imagery into QGIS",
                qgis_algorithm="native:loadlayer"
            ),
            WorkflowStep(
                order=2,
                name="Calculate NDVI",
                description="Compute NDVI using raster calculator: (B08-B04)/(B08+B04)",
                qgis_algorithm="qgis:rastercalculator",
                parameters={
                    "EXPRESSION": "(B08@1 - B04@1) / (B08@1 + B04@1)",
                    "OUTPUT": "ndvi.tif"
                }
            ),
            WorkflowStep(
                order=3,
                name="Classify vegetation",
                description="Reclassify NDVI into vegetation classes",
                qgis_algorithm="native:reclassifybytable",
                parameters={
                    "TABLE": [-1, 0.1, 1, 0.1, 0.2, 2, 0.2, 0.4, 3, 0.4, 0.6, 4, 0.6, 1, 5]
                }
            ),
            WorkflowStep(
                order=4,
                name="Calculate statistics",
                description="Compute zonal statistics for your area of interest",
                qgis_algorithm="native:zonalstatisticsfb",
                optional=True
            )
        ]
    ),

    # -------------------------------------------------------------------------
    # 2. WATER BODY DETECTION
    # -------------------------------------------------------------------------
    "water_detection": AnalysisWorkflow(
        id="water_detection",
        name="Water Body Detection",
        description="Map water bodies, lakes, rivers, and reservoirs",
        category=AnalysisCategory.WATER,
        keywords=[
            "water", "lake", "river", "reservoir", "pond", "wetland",
            "stream", "ocean", "sea", "coast", "flood", "aquatic",
            "hydrological", "watershed", "dam"
        ],
        primary_dataset="S2_MSI_L2A",
        fallback_datasets=["LANDSAT_C2L2"],
        alternate_dataset_sar="S1_SAR_GRD",
        indices=["NDWI", "MNDWI"],
        cloud_cover_max=20,
        temporal_requirement="single",
        steps=[
            WorkflowStep(
                order=1,
                name="Load imagery",
                description="Load optical or SAR imagery",
            ),
            WorkflowStep(
                order=2,
                name="Calculate MNDWI",
                description="Compute MNDWI: (B03-B11)/(B03+B11)",
                qgis_algorithm="qgis:rastercalculator",
                parameters={
                    "EXPRESSION": "(B03@1 - B11@1) / (B03@1 + B11@1)",
                    "OUTPUT": "mndwi.tif"
                }
            ),
            WorkflowStep(
                order=3,
                name="Threshold water",
                description="Apply threshold (>0) to extract water pixels",
                qgis_algorithm="native:reclassifybytable",
                parameters={
                    "TABLE": [-1, 0, 0, 0, 1, 1]
                }
            ),
            WorkflowStep(
                order=4,
                name="Vectorize",
                description="Convert water mask to vector polygons",
                qgis_algorithm="gdal:polygonize",
                optional=True
            )
        ]
    ),

    # -------------------------------------------------------------------------
    # 3. URBAN / BUILT-UP MAPPING
    # -------------------------------------------------------------------------
    "urban_mapping": AnalysisWorkflow(
        id="urban_mapping",
        name="Urban & Built-up Area Mapping",
        description="Map urban extent, buildings, and infrastructure",
        category=AnalysisCategory.URBAN,
        keywords=[
            "urban", "city", "town", "building", "settlement", "infrastructure",
            "road", "construction", "development", "built-up", "impervious",
            "concrete", "asphalt", "residential", "commercial", "industrial"
        ],
        primary_dataset="S2_MSI_L2A",
        fallback_datasets=["LANDSAT_C2L2"],
        indices=["NDBI", "UI", "NDVI"],
        cloud_cover_max=15,
        temporal_requirement="single",
        steps=[
            WorkflowStep(
                order=1,
                name="Load imagery",
                description="Load Sentinel-2 imagery",
            ),
            WorkflowStep(
                order=2,
                name="Calculate NDBI",
                description="Compute NDBI: (B11-B08)/(B11+B08)",
                qgis_algorithm="qgis:rastercalculator",
                parameters={
                    "EXPRESSION": "(B11@1 - B08@1) / (B11@1 + B08@1)",
                    "OUTPUT": "ndbi.tif"
                }
            ),
            WorkflowStep(
                order=3,
                name="Calculate NDVI",
                description="Calculate NDVI to mask vegetation",
                qgis_algorithm="qgis:rastercalculator"
            ),
            WorkflowStep(
                order=4,
                name="Extract built-up",
                description="Built-up where NDBI > 0 AND NDVI < 0.2",
                qgis_algorithm="qgis:rastercalculator",
                parameters={
                    "EXPRESSION": "(NDBI@1 > 0) AND (NDVI@1 < 0.2)"
                }
            )
        ]
    ),

    # -------------------------------------------------------------------------
    # 4. FLOOD MAPPING
    # -------------------------------------------------------------------------
    "flood_mapping": AnalysisWorkflow(
        id="flood_mapping",
        name="Flood Extent Mapping",
        description="Map flood extent using SAR or optical imagery",
        category=AnalysisCategory.FLOOD,
        keywords=[
            "flood", "inundation", "disaster", "emergency", "overflow",
            "flooding", "floodplain", "waterlogging", "submersion",
            "hurricane", "cyclone", "monsoon", "dam break"
        ],
        primary_dataset="S1_SAR_GRD",  # SAR preferred for floods
        fallback_datasets=["S2_MSI_L2A"],
        indices=["MNDWI"],
        cloud_cover_max=100,  # SAR works through clouds
        temporal_requirement="before_after",
        steps=[
            WorkflowStep(
                order=1,
                name="Load pre-flood SAR",
                description="Load Sentinel-1 image before flood event",
            ),
            WorkflowStep(
                order=2,
                name="Load post-flood SAR",
                description="Load Sentinel-1 image during/after flood",
            ),
            WorkflowStep(
                order=3,
                name="Apply speckle filter",
                description="Reduce SAR speckle noise",
                qgis_algorithm="gdal:gdalfilter",
                parameters={"FILTER": "median", "SIZE": 5}
            ),
            WorkflowStep(
                order=4,
                name="Threshold VH band",
                description="Apply threshold to detect water (low backscatter)",
                qgis_algorithm="qgis:rastercalculator",
                parameters={
                    "EXPRESSION": "VH@1 < -20"
                }
            ),
            WorkflowStep(
                order=5,
                name="Change detection",
                description="Compare pre and post to find new water",
                qgis_algorithm="qgis:rastercalculator"
            )
        ]
    ),

    # -------------------------------------------------------------------------
    # 5. TERRAIN ANALYSIS
    # -------------------------------------------------------------------------
    "terrain_analysis": AnalysisWorkflow(
        id="terrain_analysis",
        name="Terrain & Elevation Analysis",
        description="Analyze topography, slope, aspect, and elevation",
        category=AnalysisCategory.TERRAIN,
        keywords=[
            "terrain", "elevation", "dem", "slope", "aspect", "topography",
            "hill", "mountain", "valley", "watershed", "drainage",
            "contour", "relief", "height", "altitude", "hillshade"
        ],
        primary_dataset="COP_DEM_GLO30",
        fallback_datasets=["COP_DEM_GLO90", "SRTM_DEM"],
        indices=[],
        cloud_cover_max=100,  # DEM not affected by clouds
        temporal_requirement="single",
        steps=[
            WorkflowStep(
                order=1,
                name="Load DEM",
                description="Load Copernicus or SRTM DEM",
            ),
            WorkflowStep(
                order=2,
                name="Calculate slope",
                description="Generate slope map in degrees",
                qgis_algorithm="native:slope",
                parameters={"OUTPUT": "slope.tif"}
            ),
            WorkflowStep(
                order=3,
                name="Calculate aspect",
                description="Generate aspect (direction of slope)",
                qgis_algorithm="native:aspect",
                parameters={"OUTPUT": "aspect.tif"}
            ),
            WorkflowStep(
                order=4,
                name="Generate hillshade",
                description="Create hillshade for visualization",
                qgis_algorithm="native:hillshade",
                optional=True
            ),
            WorkflowStep(
                order=5,
                name="Extract contours",
                description="Generate contour lines",
                qgis_algorithm="gdal:contour",
                optional=True
            )
        ]
    ),

    # -------------------------------------------------------------------------
    # 6. FIRE / BURN SEVERITY
    # -------------------------------------------------------------------------
    "fire_analysis": AnalysisWorkflow(
        id="fire_analysis",
        name="Fire & Burn Severity Analysis",
        description="Assess fire damage and burn severity",
        category=AnalysisCategory.FIRE,
        keywords=[
            "fire", "burn", "wildfire", "forest fire", "bushfire",
            "burned", "combustion", "blaze", "flame", "scorch",
            "char", "ash", "smoke", "fire scar", "post-fire"
        ],
        primary_dataset="S2_MSI_L2A",
        fallback_datasets=["LANDSAT_C2L2"],
        indices=["NBR", "dNBR", "NDVI"],
        cloud_cover_max=30,
        temporal_requirement="before_after",
        steps=[
            WorkflowStep(
                order=1,
                name="Load pre-fire imagery",
                description="Load image from before the fire",
            ),
            WorkflowStep(
                order=2,
                name="Load post-fire imagery",
                description="Load image after the fire",
            ),
            WorkflowStep(
                order=3,
                name="Calculate pre-fire NBR",
                description="NBR = (B08-B12)/(B08+B12)",
                qgis_algorithm="qgis:rastercalculator",
                parameters={
                    "EXPRESSION": "(B08@1 - B12@1) / (B08@1 + B12@1)",
                    "OUTPUT": "nbr_pre.tif"
                }
            ),
            WorkflowStep(
                order=4,
                name="Calculate post-fire NBR",
                description="Calculate NBR for post-fire image",
                qgis_algorithm="qgis:rastercalculator"
            ),
            WorkflowStep(
                order=5,
                name="Calculate dNBR",
                description="dNBR = NBR_pre - NBR_post",
                qgis_algorithm="qgis:rastercalculator",
                parameters={
                    "EXPRESSION": "NBR_pre@1 - NBR_post@1",
                    "OUTPUT": "dnbr.tif"
                }
            ),
            WorkflowStep(
                order=6,
                name="Classify burn severity",
                description="Classify dNBR into severity classes",
                qgis_algorithm="native:reclassifybytable"
            )
        ]
    ),
}


# =============================================================================
# WORKFLOW MATCHING
# =============================================================================

def match_workflow(user_query: str) -> List[AnalysisWorkflow]:
    """
    Match user query to relevant workflows.
    Returns list of workflows sorted by relevance.
    """
    query_lower = user_query.lower()
    scores = {}

    for workflow_id, workflow in ANALYSIS_WORKFLOWS.items():
        score = 0
        matched_keywords = []

        for keyword in workflow.keywords:
            if keyword in query_lower:
                score += 2
                matched_keywords.append(keyword)

        # Partial matches
        for word in query_lower.split():
            if len(word) > 3:
                for keyword in workflow.keywords:
                    if word in keyword or keyword in word:
                        score += 1

        if score > 0:
            scores[workflow_id] = {
                "score": score,
                "workflow": workflow,
                "matched_keywords": matched_keywords
            }

    # Sort by score
    sorted_results = sorted(scores.values(), key=lambda x: x["score"], reverse=True)
    return [r["workflow"] for r in sorted_results]


def get_workflow_recommendation(user_query: str) -> Dict:
    """
    Get complete workflow recommendation for a user query.
    """
    workflows = match_workflow(user_query)

    if not workflows:
        return {
            "status": "no_match",
            "message": "No matching workflow found. Please describe your analysis goal.",
            "available_categories": [c.value for c in AnalysisCategory]
        }

    primary_workflow = workflows[0]

    return {
        "status": "matched",
        "query": user_query,
        "recommended_workflow": {
            "id": primary_workflow.id,
            "name": primary_workflow.name,
            "description": primary_workflow.description,
            "category": primary_workflow.category.value,
            "primary_dataset": primary_workflow.primary_dataset,
            "fallback_datasets": primary_workflow.fallback_datasets,
            "indices": primary_workflow.indices,
            "steps": [
                {
                    "order": s.order,
                    "name": s.name,
                    "description": s.description,
                    "optional": s.optional
                }
                for s in primary_workflow.steps
            ],
            "cloud_cover_max": primary_workflow.cloud_cover_max,
            "temporal_requirement": primary_workflow.temporal_requirement
        },
        "indices_details": [
            {
                "name": idx,
                "full_name": SPECTRAL_INDICES[idx].full_name,
                "formula": SPECTRAL_INDICES[idx].formula,
                "interpretation": SPECTRAL_INDICES[idx].interpretation
            }
            for idx in primary_workflow.indices
            if idx in SPECTRAL_INDICES
        ],
        "alternative_workflows": [
            {"id": w.id, "name": w.name}
            for w in workflows[1:3]
        ] if len(workflows) > 1 else []
    }


def get_qgis_formula(index_name: str, sensor: str = "sentinel2") -> str:
    """
    Get QGIS raster calculator formula for an index.
    """
    if index_name not in SPECTRAL_INDICES:
        return ""

    index = SPECTRAL_INDICES[index_name]
    bands = index.bands_sentinel2 if sensor == "sentinel2" else index.bands_landsat

    if not bands:
        return f"# {index_name} not available for {sensor}"

    formula = index.formula
    for var, band in bands.items():
        formula = formula.replace(var, f"{band}@1")

    return formula
