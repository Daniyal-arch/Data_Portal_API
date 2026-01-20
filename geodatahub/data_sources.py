"""
GeoDataHub Data Sources Configuration

Comprehensive catalog of available satellite and geospatial data sources
with metadata for AI-powered recommendations.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class DataCategory(Enum):
    """Categories of geospatial data."""
    OPTICAL = "optical"
    SAR = "sar"
    DEM = "dem"
    LAND_COVER = "land_cover"
    CLIMATE = "climate"
    OCEAN = "ocean"
    ATMOSPHERE = "atmosphere"
    VEGETATION = "vegetation"
    NIGHTTIME = "nighttime"
    HYPERSPECTRAL = "hyperspectral"


@dataclass
class DataSource:
    """Represents a satellite/geospatial data source."""

    # Basic info
    id: str
    name: str
    description: str
    provider: str
    category: DataCategory

    # Technical specs
    resolution_m: Optional[float] = None  # Spatial resolution in meters
    revisit_days: Optional[int] = None    # Temporal revisit in days
    bands: List[str] = field(default_factory=list)

    # Coverage
    global_coverage: bool = True
    start_date: Optional[str] = None      # Data availability start

    # Access
    requires_auth: bool = True
    free_access: bool = True
    eodag_product: Optional[str] = None   # EODAG product type code

    # Use cases
    use_cases: List[str] = field(default_factory=list)
    suitable_indices: List[str] = field(default_factory=list)

    # AI recommendation metadata
    keywords: List[str] = field(default_factory=list)
    pros: List[str] = field(default_factory=list)
    cons: List[str] = field(default_factory=list)


# =============================================================================
# COMPREHENSIVE DATA SOURCE CATALOG
# =============================================================================

DATA_SOURCES: Dict[str, DataSource] = {

    # =========================================================================
    # OPTICAL SATELLITES
    # =========================================================================

    "S2_MSI_L2A": DataSource(
        id="S2_MSI_L2A",
        name="Sentinel-2 Level-2A",
        description="High-resolution multispectral imagery with atmospheric correction. "
                    "Ideal for vegetation, agriculture, water bodies, and land cover mapping.",
        provider="cop_dataspace",
        category=DataCategory.OPTICAL,
        resolution_m=10,
        revisit_days=5,
        bands=["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B11", "B12"],
        start_date="2015-06-23",
        eodag_product="S2_MSI_L2A",
        use_cases=[
            "Vegetation monitoring", "Crop health assessment", "Water quality",
            "Urban mapping", "Forest monitoring", "Land cover classification",
            "Change detection", "Disaster response"
        ],
        suitable_indices=["NDVI", "EVI", "NDWI", "MNDWI", "NDBI", "NBR", "SAVI", "NDRE"],
        keywords=["vegetation", "agriculture", "crop", "forest", "urban", "water", "ndvi",
                  "land cover", "multispectral", "optical", "sentinel"],
        pros=["High resolution (10m)", "Free data", "5-day revisit", "13 spectral bands",
              "Atmospheric correction included"],
        cons=["Affected by clouds", "No thermal band"]
    ),

    "S2_MSI_L1C": DataSource(
        id="S2_MSI_L1C",
        name="Sentinel-2 Level-1C",
        description="Top-of-atmosphere reflectance imagery. Use when you need raw data "
                    "or want to apply custom atmospheric correction.",
        provider="cop_dataspace",
        category=DataCategory.OPTICAL,
        resolution_m=10,
        revisit_days=5,
        bands=["B01", "B02", "B03", "B04", "B05", "B06", "B07", "B08", "B8A", "B09", "B10", "B11", "B12"],
        start_date="2015-06-23",
        eodag_product="S2_MSI_L1C",
        use_cases=["Custom atmospheric correction", "Cloud detection research", "TOA analysis"],
        suitable_indices=["NDVI", "EVI", "NDWI"],
        keywords=["toa", "top of atmosphere", "raw", "sentinel"],
        pros=["Raw data available", "Includes cirrus band"],
        cons=["Requires atmospheric correction", "Affected by clouds"]
    ),

    "LANDSAT_C2L2": DataSource(
        id="LANDSAT_C2L2",
        name="Landsat 8/9 Collection 2 Level-2",
        description="Long-term Earth observation with thermal bands. Excellent for "
                    "historical analysis and temperature-related studies.",
        provider="usgs",
        category=DataCategory.OPTICAL,
        resolution_m=30,
        revisit_days=16,
        bands=["B1", "B2", "B3", "B4", "B5", "B6", "B7", "B10", "B11"],
        start_date="2013-02-11",
        eodag_product="LANDSAT_C2L2",
        use_cases=[
            "Long-term monitoring", "Temperature mapping", "Thermal analysis",
            "Historical change detection", "Urban heat island", "Fire detection",
            "Water temperature"
        ],
        suitable_indices=["NDVI", "NDWI", "NBR", "LST", "NDBI"],
        keywords=["landsat", "thermal", "temperature", "historical", "long-term",
                  "heat", "fire", "lst"],
        pros=["Thermal bands", "40+ years archive (with older Landsat)", "Free data",
              "Well-calibrated"],
        cons=["Lower resolution (30m)", "16-day revisit", "Affected by clouds"]
    ),

    "MODIS_MOD09GA": DataSource(
        id="MODIS_MOD09GA",
        name="MODIS Daily Surface Reflectance",
        description="Daily global coverage at moderate resolution. Perfect for "
                    "large-scale vegetation and atmospheric studies.",
        provider="planetary_computer",
        category=DataCategory.OPTICAL,
        resolution_m=500,
        revisit_days=1,
        bands=["B01", "B02", "B03", "B04", "B05", "B06", "B07"],
        start_date="2000-02-24",
        eodag_product="MODIS_MOD09GA",
        use_cases=[
            "Daily monitoring", "Large-scale vegetation", "Phenology",
            "Global studies", "Fire detection", "Aerosol studies"
        ],
        suitable_indices=["NDVI", "EVI", "LAI"],
        keywords=["modis", "daily", "global", "phenology", "large-scale", "vegetation"],
        pros=["Daily coverage", "Global data", "Long archive (2000+)", "Consistent quality"],
        cons=["Low resolution (500m)", "Mixed pixels in heterogeneous areas"]
    ),

    # =========================================================================
    # SAR (RADAR) SATELLITES
    # =========================================================================

    "S1_SAR_GRD": DataSource(
        id="S1_SAR_GRD",
        name="Sentinel-1 SAR Ground Range Detected",
        description="All-weather, day-night radar imagery. Essential for flood mapping, "
                    "ship detection, and monitoring through clouds.",
        provider="cop_dataspace",
        category=DataCategory.SAR,
        resolution_m=10,
        revisit_days=6,
        bands=["VV", "VH"],
        start_date="2014-04-03",
        eodag_product="S1_SAR_GRD",
        use_cases=[
            "Flood mapping", "Ship detection", "Oil spill detection",
            "Deformation monitoring", "Soil moisture", "Rice paddy mapping",
            "All-weather monitoring", "Forest structure"
        ],
        suitable_indices=["RVI", "Water mask", "Backscatter ratio"],
        keywords=["sar", "radar", "flood", "ship", "oil spill", "all-weather",
                  "cloud-free", "deformation", "moisture", "sentinel-1"],
        pros=["Works through clouds", "Day and night", "Sensitive to water",
              "Detects surface changes"],
        cons=["Complex interpretation", "Speckle noise", "No color information"]
    ),

    "S1_SAR_SLC": DataSource(
        id="S1_SAR_SLC",
        name="Sentinel-1 SAR Single Look Complex",
        description="Complex SAR data with phase information. Required for "
                    "interferometric applications (InSAR).",
        provider="cop_dataspace",
        category=DataCategory.SAR,
        resolution_m=5,
        revisit_days=6,
        bands=["VV", "VH"],
        start_date="2014-04-03",
        eodag_product="S1_SAR_SLC",
        use_cases=[
            "InSAR", "Ground deformation", "Subsidence monitoring",
            "Earthquake analysis", "Volcano monitoring", "Glacier movement"
        ],
        suitable_indices=["Coherence", "Interferogram"],
        keywords=["insar", "interferometry", "deformation", "subsidence",
                  "earthquake", "volcano", "glacier"],
        pros=["Phase information", "High precision deformation", "Sub-cm accuracy"],
        cons=["Complex processing", "Large file sizes", "Requires expertise"]
    ),

    # =========================================================================
    # ELEVATION / DEM
    # =========================================================================

    "COP-DEM_GLO-30": DataSource(
        id="COP-DEM_GLO-30",
        name="Copernicus DEM 30m",
        description="Global digital elevation model at 30m resolution. Derived from "
                    "TanDEM-X mission, ideal for terrain analysis.",
        provider="cop_dataspace",
        category=DataCategory.DEM,
        resolution_m=30,
        revisit_days=None,  # Static dataset
        bands=["DEM"],
        start_date="2021-01-01",
        eodag_product="COP-DEM_GLO-30",
        use_cases=[
            "Terrain analysis", "Slope calculation", "Watershed delineation",
            "Viewshed analysis", "Flood modeling", "Infrastructure planning",
            "3D visualization", "Hillshade generation"
        ],
        suitable_indices=["Slope", "Aspect", "TRI", "TPI", "Hillshade", "Curvature"],
        keywords=["dem", "elevation", "terrain", "slope", "aspect", "height",
                  "topography", "watershed", "hillshade"],
        pros=["Global coverage", "Free access", "High quality", "Regular updates"],
        cons=["Static (no temporal)", "May have voids in steep terrain"]
    ),

    "COP-DEM_GLO-90": DataSource(
        id="COP-DEM_GLO-90",
        name="Copernicus DEM 90m",
        description="Global DEM at 90m resolution. Good for large-scale terrain analysis "
                    "with smaller file sizes.",
        provider="cop_dataspace",
        category=DataCategory.DEM,
        resolution_m=90,
        bands=["DEM"],
        eodag_product="COP-DEM_GLO-90",
        use_cases=["Regional terrain analysis", "Hydrological modeling", "Climate modeling"],
        suitable_indices=["Slope", "Aspect", "TWI"],
        keywords=["dem", "elevation", "terrain", "regional"],
        pros=["Smaller file sizes", "Global coverage", "Free"],
        cons=["Lower resolution than GLO-30"]
    ),

    "SRTM_DEM": DataSource(
        id="SRTM_DEM",
        name="SRTM Digital Elevation Model",
        description="NASA Shuttle Radar Topography Mission DEM. Historical reference "
                    "elevation data from 2000.",
        provider="usgs",
        category=DataCategory.DEM,
        resolution_m=30,
        bands=["DEM"],
        start_date="2000-02-11",
        eodag_product="SRTM_DEM",
        use_cases=["Historical terrain reference", "Change in elevation studies"],
        suitable_indices=["Slope", "Aspect"],
        keywords=["srtm", "dem", "elevation", "historical", "nasa"],
        pros=["Well-documented", "Widely used reference"],
        cons=["Data from 2000 only", "Coverage 60N-56S only"]
    ),

    # =========================================================================
    # LAND COVER
    # =========================================================================

    "ESA_WORLDCOVER": DataSource(
        id="ESA_WORLDCOVER",
        name="ESA WorldCover",
        description="Global land cover map at 10m resolution. 11 land cover classes "
                    "derived from Sentinel-1 and Sentinel-2.",
        provider="planetary_computer",
        category=DataCategory.LAND_COVER,
        resolution_m=10,
        bands=["LC"],
        start_date="2020-01-01",
        eodag_product="ESA_WORLDCOVER",
        use_cases=[
            "Land cover mapping", "Baseline classification", "Urban extent",
            "Forest mapping", "Wetland mapping", "Change detection baseline"
        ],
        suitable_indices=["Land cover statistics"],
        keywords=["land cover", "classification", "worldcover", "urban", "forest",
                  "wetland", "baseline"],
        pros=["10m resolution", "Global coverage", "11 classes", "Free"],
        cons=["Annual updates only", "May have classification errors"]
    ),

    "CORINE_LC": DataSource(
        id="CORINE_LC",
        name="CORINE Land Cover",
        description="European land cover database with 44 classes. Detailed classification "
                    "for Europe only.",
        provider="cop_dataspace",
        category=DataCategory.LAND_COVER,
        resolution_m=100,
        bands=["LC"],
        start_date="1990-01-01",
        eodag_product="CORINE_LC",
        use_cases=["European land cover", "Policy support", "Environmental reporting"],
        suitable_indices=["Land cover statistics"],
        keywords=["corine", "europe", "land cover", "detailed classification"],
        pros=["44 detailed classes", "Historical data (1990+)", "Consistent methodology"],
        cons=["Europe only", "100m resolution", "Multi-year update cycle"]
    ),

    # =========================================================================
    # CLIMATE / ATMOSPHERE
    # =========================================================================

    "ERA5_REANALYSIS": DataSource(
        id="ERA5_REANALYSIS",
        name="ERA5 Climate Reanalysis",
        description="Global climate reanalysis data. Temperature, precipitation, wind, "
                    "humidity and more at hourly resolution.",
        provider="cop_cds",
        category=DataCategory.CLIMATE,
        resolution_m=31000,  # ~31km
        revisit_days=1,
        bands=["temperature", "precipitation", "wind", "humidity", "pressure"],
        start_date="1979-01-01",
        eodag_product="ERA5_REANALYSIS",
        requires_auth=True,
        use_cases=[
            "Climate analysis", "Weather patterns", "Historical climate",
            "Agricultural planning", "Renewable energy assessment", "Drought monitoring"
        ],
        suitable_indices=["Temperature anomaly", "SPI", "SPEI"],
        keywords=["climate", "weather", "temperature", "precipitation", "wind",
                  "era5", "reanalysis", "historical weather"],
        pros=["Hourly data", "1979-present", "Consistent global coverage", "Many variables"],
        cons=["Coarse resolution (31km)", "Modeled data not observations"]
    ),

    "S5P_L2": DataSource(
        id="S5P_L2",
        name="Sentinel-5P Atmospheric",
        description="Atmospheric composition data. NO2, O3, SO2, CO, CH4, aerosols "
                    "for air quality monitoring.",
        provider="cop_dataspace",
        category=DataCategory.ATMOSPHERE,
        resolution_m=7000,  # 7km
        revisit_days=1,
        bands=["NO2", "O3", "SO2", "CO", "CH4", "HCHO", "Aerosol"],
        start_date="2018-07-05",
        eodag_product="S5P_L2",
        use_cases=[
            "Air quality monitoring", "Pollution tracking", "Methane detection",
            "Ozone monitoring", "Volcanic SO2", "Industrial emissions"
        ],
        suitable_indices=["AQI", "Tropospheric NO2"],
        keywords=["air quality", "pollution", "no2", "ozone", "methane", "atmosphere",
                  "sentinel-5p", "emissions"],
        pros=["Daily global coverage", "Multiple pollutants", "Near real-time"],
        cons=["Coarse resolution (7km)", "Affected by clouds"]
    ),

    # =========================================================================
    # OCEAN
    # =========================================================================

    "S3_OLCI": DataSource(
        id="S3_OLCI",
        name="Sentinel-3 OLCI Ocean Color",
        description="Ocean and land color instrument. Chlorophyll, water quality, "
                    "and coastal monitoring.",
        provider="cop_dataspace",
        category=DataCategory.OCEAN,
        resolution_m=300,
        revisit_days=2,
        bands=["Oa01", "Oa02", "Oa03", "Oa04", "Oa05", "Oa06", "Oa07", "Oa08",
               "Oa09", "Oa10", "Oa11", "Oa12", "Oa13", "Oa14", "Oa15", "Oa16",
               "Oa17", "Oa18", "Oa19", "Oa20", "Oa21"],
        start_date="2016-02-16",
        eodag_product="S3_OLCI",
        use_cases=[
            "Ocean color", "Chlorophyll mapping", "Algal blooms",
            "Water quality", "Coastal monitoring", "Lake monitoring"
        ],
        suitable_indices=["Chlorophyll-a", "TSM", "CDOM", "Turbidity"],
        keywords=["ocean", "chlorophyll", "water quality", "algae", "coastal",
                  "lake", "sentinel-3"],
        pros=["21 spectral bands", "Optimized for water", "Daily coastal coverage"],
        cons=["300m resolution", "Complex atmospheric correction over water"]
    ),

    # =========================================================================
    # VEGETATION PRODUCTS
    # =========================================================================

    "VEGETATION_NDVI": DataSource(
        id="VEGETATION_NDVI",
        name="Global Vegetation Index (NDVI)",
        description="Pre-computed NDVI product for vegetation monitoring. "
                    "Ready-to-use vegetation health indicator.",
        provider="cop_dataspace",
        category=DataCategory.VEGETATION,
        resolution_m=1000,
        revisit_days=10,
        bands=["NDVI"],
        start_date="1998-01-01",
        eodag_product="VEGETATION_NDVI",
        use_cases=[
            "Vegetation monitoring", "Drought assessment", "Crop yield prediction",
            "Phenology studies", "Desertification monitoring"
        ],
        suitable_indices=["NDVI anomaly", "VCI"],
        keywords=["ndvi", "vegetation", "greenness", "drought", "phenology"],
        pros=["Ready-to-use", "Long time series", "Consistent processing"],
        cons=["1km resolution", "Pre-aggregated data"]
    ),

    # =========================================================================
    # NIGHTTIME LIGHTS
    # =========================================================================

    "VIIRS_DNB": DataSource(
        id="VIIRS_DNB",
        name="VIIRS Nighttime Lights",
        description="Nighttime light emissions imagery. Excellent for urban extent, "
                    "economic activity, and power outage monitoring.",
        provider="planetary_computer",
        category=DataCategory.NIGHTTIME,
        resolution_m=500,
        revisit_days=1,
        bands=["DNB"],
        start_date="2012-01-01",
        eodag_product="VIIRS_DNB",
        use_cases=[
            "Urban mapping", "Economic activity", "Power outage detection",
            "Light pollution", "Population estimation", "Development monitoring"
        ],
        suitable_indices=["Light intensity", "Urban extent"],
        keywords=["nighttime", "lights", "urban", "economic", "power", "population",
                  "viirs", "night"],
        pros=["Unique nighttime perspective", "Daily global coverage", "Correlates with GDP"],
        cons=["500m resolution", "Affected by moon phase", "Cloud interference"]
    ),
}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_data_source(source_id: str) -> Optional[DataSource]:
    """Get a data source by ID."""
    return DATA_SOURCES.get(source_id)


def get_sources_by_category(category: DataCategory) -> List[DataSource]:
    """Get all data sources in a category."""
    return [ds for ds in DATA_SOURCES.values() if ds.category == category]


def get_sources_by_keyword(keyword: str) -> List[DataSource]:
    """Find data sources matching a keyword."""
    keyword_lower = keyword.lower()
    matching = []

    for ds in DATA_SOURCES.values():
        # Check keywords
        if any(keyword_lower in kw.lower() for kw in ds.keywords):
            matching.append(ds)
            continue
        # Check use cases
        if any(keyword_lower in uc.lower() for uc in ds.use_cases):
            matching.append(ds)
            continue
        # Check description
        if keyword_lower in ds.description.lower():
            matching.append(ds)

    return matching


def get_sources_for_analysis(analysis_text: str) -> List[DataSource]:
    """
    Recommend data sources based on analysis description.
    Uses keyword matching for fast recommendations.
    """
    text_lower = analysis_text.lower()
    scores = {}

    for source_id, ds in DATA_SOURCES.items():
        score = 0

        # Check keywords
        for keyword in ds.keywords:
            if keyword in text_lower:
                score += 2

        # Check use cases
        for use_case in ds.use_cases:
            if any(word in text_lower for word in use_case.lower().split()):
                score += 1

        # Check suitable indices
        for index in ds.suitable_indices:
            if index.lower() in text_lower:
                score += 3

        if score > 0:
            scores[source_id] = score

    # Sort by score and return top sources
    sorted_sources = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [DATA_SOURCES[source_id] for source_id, _ in sorted_sources[:5]]


def get_all_sources_summary() -> List[Dict]:
    """Get a summary of all available data sources."""
    return [
        {
            "id": ds.id,
            "name": ds.name,
            "category": ds.category.value,
            "resolution_m": ds.resolution_m,
            "provider": ds.provider,
            "description": ds.description[:100] + "..." if len(ds.description) > 100 else ds.description
        }
        for ds in DATA_SOURCES.values()
    ]
