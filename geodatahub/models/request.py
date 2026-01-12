from dataclasses import dataclass, field
from typing import Optional, List, Union
from enum import Enum
from datetime import datetime


class DataType(Enum):
    """Types of geospatial data"""
    OPTICAL = "optical"
    SAR = "sar"
    DEM = "dem"
    LAND_COVER = "land_cover"
    CLIMATE = "climate"
    POPULATION = "population"
    AIR_QUALITY = "air_quality"


class OutputFormat(Enum):
    """Output format for downloaded data"""
    GEOTIFF = "geotiff"
    COG = "cog"
    NETCDF = "netcdf"
    RAW = "raw"


@dataclass
class DataRequest:
    """
    Unified request model for all interfaces.

    This class represents a structured data request that can be created
    programmatically or parsed from natural language queries.

    Attributes:
        data_type: Type of data to search for (optical, SAR, DEM, etc.)
        product: Specific product code (e.g., S2_MSI_L2A, LANDSAT_C2L2)
        provider: Preferred data provider (e.g., cop_dataspace, usgs)
        geometry: GeoJSON geometry object defining the area of interest
        bbox: Bounding box as (minx, miny, maxx, maxy) tuple
        location_name: Location name to be geocoded (alternative to geometry/bbox)
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        cloud_cover_max: Maximum cloud cover percentage (0-100)
        limit: Maximum number of results to return
        output_format: Desired output format for downloads

    Example:
        >>> request = DataRequest(
        ...     data_type=DataType.OPTICAL,
        ...     product="S2_MSI_L2A",
        ...     location_name="Paris",
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31",
        ...     cloud_cover_max=20,
        ...     limit=10
        ... )
    """
    data_type: Optional[DataType] = None
    product: Optional[str] = None
    provider: Optional[str] = None
    geometry: Optional[dict] = None          # GeoJSON geometry
    bbox: Optional[tuple] = None             # (minx, miny, maxx, maxy)
    location_name: Optional[str] = None      # Will be geocoded
    start_date: Optional[str] = None         # YYYY-MM-DD
    end_date: Optional[str] = None           # YYYY-MM-DD
    cloud_cover_max: Optional[float] = None  # 0-100
    limit: int = 10
    output_format: OutputFormat = OutputFormat.GEOTIFF

    def __post_init__(self):
        """Validate and convert data types after initialization"""
        # Convert string to DataType enum if needed
        if isinstance(self.data_type, str):
            try:
                self.data_type = DataType(self.data_type.lower())
            except ValueError:
                pass  # Keep as string, will be handled later

        # Convert string to OutputFormat enum if needed
        if isinstance(self.output_format, str):
            try:
                self.output_format = OutputFormat(self.output_format.lower())
            except ValueError:
                pass  # Keep as string

        # Validate bbox format
        if self.bbox is not None:
            if not isinstance(self.bbox, (tuple, list)) or len(self.bbox) != 4:
                raise ValueError("bbox must be a tuple/list of 4 values: (minx, miny, maxx, maxy)")
            self.bbox = tuple(self.bbox)

        # Validate cloud cover range
        if self.cloud_cover_max is not None:
            if not 0 <= self.cloud_cover_max <= 100:
                raise ValueError("cloud_cover_max must be between 0 and 100")

    def __repr__(self):
        """String representation for debugging"""
        parts = []
        if self.product:
            parts.append(f"product={self.product}")
        if self.data_type:
            parts.append(f"type={self.data_type.value if isinstance(self.data_type, DataType) else self.data_type}")
        if self.location_name:
            parts.append(f"location={self.location_name}")
        elif self.bbox:
            parts.append(f"bbox={self.bbox}")
        if self.start_date and self.end_date:
            parts.append(f"dates={self.start_date} to {self.end_date}")
        if self.cloud_cover_max is not None:
            parts.append(f"clouds<{self.cloud_cover_max}%")
        parts.append(f"limit={self.limit}")

        return f"DataRequest({', '.join(parts)})"
