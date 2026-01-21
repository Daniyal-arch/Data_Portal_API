"""
EODAG Complete Catalog
Contains all providers and products supported by EODAG.
Reference: https://eodag.readthedocs.io/en/stable/
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum


class ProviderStatus(Enum):
    """Provider configuration status."""
    NOT_CONFIGURED = "not_configured"
    CONFIGURED = "configured"
    TESTED = "tested"
    ERROR = "error"


@dataclass
class ProviderInfo:
    """EODAG Provider information."""
    name: str
    description: str = ""
    url: str = ""
    requires_auth: bool = True
    free_access: bool = True
    status: ProviderStatus = ProviderStatus.NOT_CONFIGURED
    auth_type: str = "credentials"  # credentials, api_key, oauth
    registration_url: str = ""
    auth_guide: str = ""
    priority: int = 0  # Higher = preferred


@dataclass
class ProductInfo:
    """EODAG Product information."""
    id: str
    title: str
    description: str = ""
    platform: str = ""
    instrument: str = ""
    processing_level: str = ""
    sensor_type: str = ""  # optical, sar, dem, etc.
    resolution_m: Optional[float] = None
    providers: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


# =============================================================================
# EODAG PROVIDERS (15+ providers)
# =============================================================================

EODAG_PROVIDERS: Dict[str, ProviderInfo] = {
    # ---------------------------------------------------------------------
    # COPERNICUS / ESA
    # ---------------------------------------------------------------------
    "cop_dataspace": ProviderInfo(
        name="Copernicus Data Space",
        description="ESA's new unified platform for all Copernicus Sentinel data",
        url="https://dataspace.copernicus.eu/",
        requires_auth=True,
        free_access=True,
        auth_type="credentials",
        registration_url="https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/auth",
        auth_guide="Register at dataspace.copernicus.eu, then add credentials to eodag.yml",
        priority=10
    ),

    "creodias": ProviderInfo(
        name="CREODIAS",
        description="CloudFerro DIAS - Commercial cloud with Copernicus data",
        url="https://creodias.eu/",
        requires_auth=True,
        free_access=False,
        auth_type="credentials",
        registration_url="https://creodias.eu/register",
        priority=5
    ),

    # ---------------------------------------------------------------------
    # NASA / USGS
    # ---------------------------------------------------------------------
    "usgs": ProviderInfo(
        name="USGS Earth Explorer",
        description="US Geological Survey - Landsat and more",
        url="https://earthexplorer.usgs.gov/",
        requires_auth=True,
        free_access=True,
        auth_type="credentials",
        registration_url="https://ers.cr.usgs.gov/register",
        auth_guide="Register at USGS EROS, add username/password to eodag.yml",
        priority=8
    ),

    "usgs_satapi_aws": ProviderInfo(
        name="USGS STAC on AWS",
        description="USGS data via STAC API on AWS (Landsat Collection 2)",
        url="https://landsatlook.usgs.gov/stac-server",
        requires_auth=False,
        free_access=True,
        auth_type="none",
        priority=7
    ),

    "planetary_computer": ProviderInfo(
        name="Microsoft Planetary Computer",
        description="Microsoft's geospatial data platform with many free datasets",
        url="https://planetarycomputer.microsoft.com/",
        requires_auth=False,
        free_access=True,
        auth_type="api_key",
        registration_url="https://planetarycomputer.microsoft.com/account/request",
        auth_guide="Optional API key for higher rate limits",
        priority=9
    ),

    "earth_search": ProviderInfo(
        name="Earth Search (AWS)",
        description="Element84 STAC API - Sentinel, Landsat on AWS",
        url="https://earth-search.aws.element84.com/v1",
        requires_auth=False,
        free_access=True,
        auth_type="none",
        priority=8
    ),

    "earth_search_gcs": ProviderInfo(
        name="Earth Search (Google Cloud)",
        description="Element84 STAC API on Google Cloud",
        url="https://earth-search.storage.googleapis.com/",
        requires_auth=False,
        free_access=True,
        auth_type="none",
        priority=6
    ),

    # ---------------------------------------------------------------------
    # FRENCH SPACE AGENCY (CNES)
    # ---------------------------------------------------------------------
    "peps": ProviderInfo(
        name="PEPS",
        description="French CNES platform for Copernicus Sentinel data",
        url="https://peps.cnes.fr/",
        requires_auth=True,
        free_access=True,
        auth_type="credentials",
        registration_url="https://peps.cnes.fr/rocket/#/register",
        priority=6
    ),

    "theia": ProviderInfo(
        name="Theia",
        description="French land data center - Sentinel, Landsat, Pleiades",
        url="https://theia.cnes.fr/",
        requires_auth=True,
        free_access=True,
        auth_type="credentials",
        registration_url="https://theia.cnes.fr/atdistrib/rocket/#/register",
        priority=5
    ),

    # ---------------------------------------------------------------------
    # OTHER PROVIDERS
    # ---------------------------------------------------------------------
    "onda": ProviderInfo(
        name="ONDA DIAS",
        description="Serco DIAS platform",
        url="https://www.onda-dias.eu/",
        requires_auth=True,
        free_access=False,
        auth_type="credentials",
        priority=3
    ),

    "astraea_eod": ProviderInfo(
        name="Astraea Earth OnDemand",
        description="Astraea's Earth observation data platform",
        url="https://earthondemand.astraea.earth/",
        requires_auth=True,
        free_access=False,
        auth_type="api_key",
        priority=3
    ),

    "cop_cds": ProviderInfo(
        name="Copernicus Climate Data Store",
        description="Climate reanalysis data (ERA5, seasonal forecasts)",
        url="https://cds.climate.copernicus.eu/",
        requires_auth=True,
        free_access=True,
        auth_type="api_key",
        registration_url="https://cds.climate.copernicus.eu/user/register",
        auth_guide="Register and get API key from CDS portal",
        priority=7
    ),

    "cop_ads": ProviderInfo(
        name="Copernicus Atmosphere Data Store",
        description="Atmospheric data (CAMS)",
        url="https://ads.atmosphere.copernicus.eu/",
        requires_auth=True,
        free_access=True,
        auth_type="api_key",
        registration_url="https://ads.atmosphere.copernicus.eu/user/register",
        priority=6
    ),

    "cop_marine": ProviderInfo(
        name="Copernicus Marine Service",
        description="Ocean data products",
        url="https://marine.copernicus.eu/",
        requires_auth=True,
        free_access=True,
        auth_type="credentials",
        registration_url="https://marine.copernicus.eu/register",
        priority=6
    ),

    "hydroweb_next": ProviderInfo(
        name="Hydroweb.next",
        description="CNES hydrology data - lake/river levels",
        url="https://hydroweb.next.theia-land.fr/",
        requires_auth=True,
        free_access=True,
        auth_type="credentials",
        priority=4
    ),

    "wekeo": ProviderInfo(
        name="WEkEO",
        description="EU Copernicus DIAS with harmonized data access",
        url="https://www.wekeo.eu/",
        requires_auth=True,
        free_access=True,
        auth_type="credentials",
        registration_url="https://www.wekeo.eu/register",
        priority=5
    ),
}


# =============================================================================
# EODAG PRODUCTS (Major product types)
# =============================================================================

EODAG_PRODUCTS: Dict[str, ProductInfo] = {
    # -------------------------------------------------------------------------
    # SENTINEL-2 (Optical)
    # -------------------------------------------------------------------------
    "S2_MSI_L1C": ProductInfo(
        id="S2_MSI_L1C",
        title="Sentinel-2 MSI Level-1C",
        description="Top-of-atmosphere reflectance in cartographic geometry",
        platform="Sentinel-2",
        instrument="MSI",
        processing_level="L1C",
        sensor_type="optical",
        resolution_m=10,
        providers=["cop_dataspace", "earth_search", "planetary_computer", "peps", "creodias"],
        keywords=["optical", "multispectral", "sentinel", "vegetation", "agriculture"]
    ),
    "S2_MSI_L2A": ProductInfo(
        id="S2_MSI_L2A",
        title="Sentinel-2 MSI Level-2A",
        description="Bottom-of-atmosphere reflectance with atmospheric correction",
        platform="Sentinel-2",
        instrument="MSI",
        processing_level="L2A",
        sensor_type="optical",
        resolution_m=10,
        providers=["cop_dataspace", "earth_search", "planetary_computer", "peps", "creodias", "theia"],
        keywords=["optical", "multispectral", "sentinel", "vegetation", "agriculture", "ndvi"]
    ),

    # -------------------------------------------------------------------------
    # SENTINEL-1 (SAR)
    # -------------------------------------------------------------------------
    "S1_SAR_GRD": ProductInfo(
        id="S1_SAR_GRD",
        title="Sentinel-1 SAR GRD",
        description="Ground Range Detected SAR data",
        platform="Sentinel-1",
        instrument="SAR",
        processing_level="GRD",
        sensor_type="sar",
        resolution_m=10,
        providers=["cop_dataspace", "earth_search", "planetary_computer", "peps", "creodias"],
        keywords=["sar", "radar", "flood", "ship", "oil spill", "all-weather"]
    ),
    "S1_SAR_SLC": ProductInfo(
        id="S1_SAR_SLC",
        title="Sentinel-1 SAR SLC",
        description="Single Look Complex SAR data for interferometry",
        platform="Sentinel-1",
        instrument="SAR",
        processing_level="SLC",
        sensor_type="sar",
        resolution_m=5,
        providers=["cop_dataspace", "peps", "creodias"],
        keywords=["sar", "insar", "deformation", "subsidence"]
    ),

    # -------------------------------------------------------------------------
    # SENTINEL-3 (Ocean/Land)
    # -------------------------------------------------------------------------
    "S3_OLCI_L1B": ProductInfo(
        id="S3_OLCI_L1B",
        title="Sentinel-3 OLCI Level-1B",
        description="Ocean and Land Colour Instrument radiances",
        platform="Sentinel-3",
        instrument="OLCI",
        processing_level="L1B",
        sensor_type="optical",
        resolution_m=300,
        providers=["cop_dataspace", "creodias"],
        keywords=["ocean", "chlorophyll", "water quality"]
    ),
    "S3_OLCI_L2_LFR": ProductInfo(
        id="S3_OLCI_L2_LFR",
        title="Sentinel-3 OLCI Level-2 Land",
        description="Land Full Resolution products",
        platform="Sentinel-3",
        instrument="OLCI",
        processing_level="L2",
        sensor_type="optical",
        resolution_m=300,
        providers=["cop_dataspace", "creodias"],
        keywords=["land", "vegetation", "fapar"]
    ),
    "S3_SLSTR_L1B": ProductInfo(
        id="S3_SLSTR_L1B",
        title="Sentinel-3 SLSTR Level-1B",
        description="Sea and Land Surface Temperature Radiometer",
        platform="Sentinel-3",
        instrument="SLSTR",
        processing_level="L1B",
        sensor_type="thermal",
        resolution_m=500,
        providers=["cop_dataspace", "creodias"],
        keywords=["temperature", "thermal", "fire", "lst"]
    ),

    # -------------------------------------------------------------------------
    # SENTINEL-5P (Atmosphere)
    # -------------------------------------------------------------------------
    "S5P_L2_NO2": ProductInfo(
        id="S5P_L2_NO2",
        title="Sentinel-5P NO2",
        description="Nitrogen dioxide column",
        platform="Sentinel-5P",
        instrument="TROPOMI",
        processing_level="L2",
        sensor_type="atmosphere",
        resolution_m=7000,
        providers=["cop_dataspace", "creodias"],
        keywords=["air quality", "no2", "pollution", "atmosphere"]
    ),
    "S5P_L2_O3": ProductInfo(
        id="S5P_L2_O3",
        title="Sentinel-5P O3",
        description="Ozone column",
        platform="Sentinel-5P",
        instrument="TROPOMI",
        processing_level="L2",
        sensor_type="atmosphere",
        resolution_m=7000,
        providers=["cop_dataspace", "creodias"],
        keywords=["ozone", "atmosphere", "uv"]
    ),
    "S5P_L2_CO": ProductInfo(
        id="S5P_L2_CO",
        title="Sentinel-5P CO",
        description="Carbon monoxide column",
        platform="Sentinel-5P",
        instrument="TROPOMI",
        processing_level="L2",
        sensor_type="atmosphere",
        resolution_m=7000,
        providers=["cop_dataspace"],
        keywords=["carbon monoxide", "fire", "pollution"]
    ),
    "S5P_L2_CH4": ProductInfo(
        id="S5P_L2_CH4",
        title="Sentinel-5P CH4",
        description="Methane column",
        platform="Sentinel-5P",
        instrument="TROPOMI",
        processing_level="L2",
        sensor_type="atmosphere",
        resolution_m=7000,
        providers=["cop_dataspace"],
        keywords=["methane", "greenhouse gas", "climate"]
    ),

    # -------------------------------------------------------------------------
    # LANDSAT (USGS)
    # -------------------------------------------------------------------------
    "LANDSAT_C2L1": ProductInfo(
        id="LANDSAT_C2L1",
        title="Landsat Collection 2 Level-1",
        description="Top-of-atmosphere reflectance",
        platform="Landsat-8/9",
        instrument="OLI/TIRS",
        processing_level="L1",
        sensor_type="optical",
        resolution_m=30,
        providers=["usgs", "usgs_satapi_aws", "planetary_computer", "earth_search"],
        keywords=["landsat", "optical", "long-term", "archive"]
    ),
    "LANDSAT_C2L2": ProductInfo(
        id="LANDSAT_C2L2",
        title="Landsat Collection 2 Level-2",
        description="Surface reflectance and surface temperature",
        platform="Landsat-8/9",
        instrument="OLI/TIRS",
        processing_level="L2",
        sensor_type="optical",
        resolution_m=30,
        providers=["usgs", "usgs_satapi_aws", "planetary_computer", "earth_search"],
        keywords=["landsat", "optical", "surface reflectance", "temperature"]
    ),

    # -------------------------------------------------------------------------
    # MODIS
    # -------------------------------------------------------------------------
    "MODIS_MOD09GA": ProductInfo(
        id="MODIS_MOD09GA",
        title="MODIS Daily Surface Reflectance",
        description="Terra MODIS daily surface reflectance",
        platform="Terra",
        instrument="MODIS",
        processing_level="L2",
        sensor_type="optical",
        resolution_m=500,
        providers=["planetary_computer"],
        keywords=["modis", "daily", "global", "vegetation"]
    ),
    "MODIS_MCD43A4": ProductInfo(
        id="MODIS_MCD43A4",
        title="MODIS BRDF-Adjusted Reflectance",
        description="Nadir BRDF-Adjusted Reflectance (NBAR)",
        platform="Terra/Aqua",
        instrument="MODIS",
        processing_level="L3",
        sensor_type="optical",
        resolution_m=500,
        providers=["planetary_computer"],
        keywords=["modis", "brdf", "global"]
    ),

    # -------------------------------------------------------------------------
    # DEM
    # -------------------------------------------------------------------------
    "COP_DEM_GLO30": ProductInfo(
        id="COP_DEM_GLO30",
        title="Copernicus DEM 30m",
        description="Global 30m Digital Elevation Model",
        platform="TanDEM-X",
        instrument="SAR",
        processing_level="DEM",
        sensor_type="dem",
        resolution_m=30,
        providers=["cop_dataspace", "planetary_computer"],
        keywords=["dem", "elevation", "terrain", "slope"]
    ),
    "COP_DEM_GLO90": ProductInfo(
        id="COP_DEM_GLO90",
        title="Copernicus DEM 90m",
        description="Global 90m Digital Elevation Model",
        platform="TanDEM-X",
        instrument="SAR",
        processing_level="DEM",
        sensor_type="dem",
        resolution_m=90,
        providers=["cop_dataspace", "planetary_computer"],
        keywords=["dem", "elevation", "terrain"]
    ),
    "SRTM_DEM": ProductInfo(
        id="SRTM_DEM",
        title="SRTM Digital Elevation",
        description="Shuttle Radar Topography Mission DEM",
        platform="SRTM",
        instrument="SAR",
        processing_level="DEM",
        sensor_type="dem",
        resolution_m=30,
        providers=["usgs", "planetary_computer"],
        keywords=["dem", "srtm", "elevation"]
    ),

    # -------------------------------------------------------------------------
    # LAND COVER
    # -------------------------------------------------------------------------
    "ESA_WORLDCOVER": ProductInfo(
        id="ESA_WORLDCOVER",
        title="ESA WorldCover",
        description="10m global land cover map",
        platform="Sentinel-1/2",
        instrument="MSI/SAR",
        processing_level="L4",
        sensor_type="land_cover",
        resolution_m=10,
        providers=["planetary_computer"],
        keywords=["land cover", "classification", "global"]
    ),
    "CORINE": ProductInfo(
        id="CORINE",
        title="CORINE Land Cover",
        description="European land cover/land use database",
        platform="Derived",
        instrument="",
        processing_level="L4",
        sensor_type="land_cover",
        resolution_m=100,
        providers=["cop_dataspace"],
        keywords=["land cover", "europe", "corine"]
    ),

    # -------------------------------------------------------------------------
    # CLIMATE/REANALYSIS
    # -------------------------------------------------------------------------
    "ERA5": ProductInfo(
        id="ERA5",
        title="ERA5 Reanalysis",
        description="ECMWF global climate reanalysis",
        platform="Reanalysis",
        instrument="",
        processing_level="L4",
        sensor_type="climate",
        resolution_m=31000,
        providers=["cop_cds"],
        keywords=["climate", "temperature", "precipitation", "wind", "reanalysis"]
    ),
    "ERA5_LAND": ProductInfo(
        id="ERA5_LAND",
        title="ERA5-Land",
        description="Enhanced land surface reanalysis",
        platform="Reanalysis",
        instrument="",
        processing_level="L4",
        sensor_type="climate",
        resolution_m=9000,
        providers=["cop_cds"],
        keywords=["climate", "land", "soil moisture", "temperature"]
    ),

    # -------------------------------------------------------------------------
    # NIGHTTIME LIGHTS
    # -------------------------------------------------------------------------
    "VIIRS_DNB": ProductInfo(
        id="VIIRS_DNB",
        title="VIIRS Day/Night Band",
        description="Nighttime lights from VIIRS",
        platform="Suomi NPP / NOAA-20",
        instrument="VIIRS",
        processing_level="L2",
        sensor_type="nighttime",
        resolution_m=500,
        providers=["planetary_computer"],
        keywords=["nighttime", "lights", "urban", "population"]
    ),

    # -------------------------------------------------------------------------
    # ADDITIONAL PRODUCTS
    # -------------------------------------------------------------------------
    "NAIP": ProductInfo(
        id="NAIP",
        title="NAIP Imagery",
        description="National Agriculture Imagery Program (US)",
        platform="Aerial",
        instrument="Camera",
        processing_level="L2",
        sensor_type="optical",
        resolution_m=1,
        providers=["planetary_computer"],
        keywords=["aerial", "agriculture", "usa", "high resolution"]
    ),
    "ALOS_PALSAR": ProductInfo(
        id="ALOS_PALSAR",
        title="ALOS PALSAR",
        description="L-band SAR for forest and terrain",
        platform="ALOS",
        instrument="PALSAR",
        processing_level="L1",
        sensor_type="sar",
        resolution_m=25,
        providers=["planetary_computer"],
        keywords=["sar", "forest", "biomass", "l-band"]
    ),
}


# =============================================================================
# PROVIDER-PRODUCT MAPPING
# =============================================================================

def get_provider_products() -> Dict[str, List[str]]:
    """Build provider to products mapping."""
    mapping = {p: [] for p in EODAG_PROVIDERS}
    for product_id, product in EODAG_PRODUCTS.items():
        for provider in product.providers:
            if provider in mapping:
                mapping[provider].append(product_id)
    return mapping


PROVIDER_PRODUCTS = get_provider_products()


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_providers_for_product(product_id: str) -> List[str]:
    """Get all providers that offer a specific product."""
    if product_id in EODAG_PRODUCTS:
        return EODAG_PRODUCTS[product_id].providers
    return []


def get_products_for_provider(provider: str) -> List[str]:
    """Get all products offered by a specific provider."""
    return PROVIDER_PRODUCTS.get(provider, [])


def get_configured_providers() -> List[ProviderInfo]:
    """Get list of configured providers."""
    return [p for p in EODAG_PROVIDERS.values() if p.status != ProviderStatus.NOT_CONFIGURED]


def get_free_providers() -> List[str]:
    """Get providers that offer free access."""
    return [name for name, info in EODAG_PROVIDERS.items() if info.free_access]


def get_alternative_providers(product_id: str, exclude_provider: str = None) -> List[str]:
    """Get alternative providers for a product."""
    providers = get_providers_for_product(product_id)
    if exclude_provider:
        providers = [p for p in providers if p != exclude_provider]
    return providers


def search_products(keyword: str) -> List[ProductInfo]:
    """Search products by keyword."""
    keyword = keyword.lower()
    results = []
    for product in EODAG_PRODUCTS.values():
        if (keyword in product.id.lower() or
            keyword in product.title.lower() or
            keyword in product.description.lower() or
            keyword in product.platform.lower() or
            any(keyword in kw for kw in product.keywords)):
            results.append(product)
    return results


def get_products_by_sensor_type(sensor_type: str) -> List[ProductInfo]:
    """Get products by sensor type (optical, sar, dem, etc.)."""
    return [p for p in EODAG_PRODUCTS.values() if p.sensor_type == sensor_type]


def get_provider_auth_guide(provider: str) -> str:
    """Get authentication guide for a provider."""
    if provider in EODAG_PROVIDERS:
        info = EODAG_PROVIDERS[provider]
        guide = f"Provider: {info.name}\n"
        guide += f"URL: {info.url}\n"
        if info.registration_url:
            guide += f"Registration: {info.registration_url}\n"
        if info.auth_guide:
            guide += f"Setup: {info.auth_guide}\n"
        guide += f"\nAdd to ~/.config/eodag/eodag.yml:\n"
        guide += f"  {provider}:\n"
        if info.auth_type == "credentials":
            guide += f"    auth:\n"
            guide += f"      credentials:\n"
            guide += f"        username: YOUR_USERNAME\n"
            guide += f"        password: YOUR_PASSWORD\n"
        elif info.auth_type == "api_key":
            guide += f"    auth:\n"
            guide += f"      api_key: YOUR_API_KEY\n"
        return guide
    return f"Provider '{provider}' not found."


# =============================================================================
# CATALOG SUMMARY
# =============================================================================

def get_catalog_summary() -> Dict:
    """Get summary of the EODAG catalog."""
    return {
        "total_providers": len(EODAG_PROVIDERS),
        "total_products": len(EODAG_PRODUCTS),
        "free_providers": len(get_free_providers()),
        "sensor_types": list(set(p.sensor_type for p in EODAG_PRODUCTS.values())),
        "providers": list(EODAG_PROVIDERS.keys()),
        "products_by_type": {
            st: len(get_products_by_sensor_type(st))
            for st in set(p.sensor_type for p in EODAG_PRODUCTS.values())
        }
    }
