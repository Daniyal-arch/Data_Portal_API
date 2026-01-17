from dataclasses import dataclass, field
from typing import Optional, Any
from geodatahub.models.request import DataType


@dataclass
class SearchResult:
    """
    Unified search result from any data provider.

    This class represents a single search result with standardized fields
    across all data providers.

    Attributes:
        id: Unique identifier for the product
        title: Human-readable title
        provider: Data provider name (e.g., cop_dataspace, usgs)
        product_type: Product type code (e.g., S2_MSI_L2A)
        data_type: Type of data (optical, SAR, DEM, etc.)
        geometry: GeoJSON geometry representing the product footprint
        bbox: Bounding box as (minx, miny, maxx, maxy)
        datetime: Acquisition datetime in ISO format
        cloud_cover: Cloud cover percentage (0-100), if applicable
        thumbnail_url: URL to preview/quicklook image
        size_mb: Product size in megabytes
        metadata: Additional provider-specific metadata
        _eodag_product: Internal reference to EODAG product object

    Example:
        >>> result = SearchResult(
        ...     id="S2A_MSIL2A_20240115T103321_N0510_R108_T31UDQ_20240115T144655",
        ...     title="Sentinel-2 L2A Image",
        ...     provider="cop_dataspace",
        ...     product_type="S2_MSI_L2A",
        ...     data_type=DataType.OPTICAL,
        ...     geometry={...},
        ...     bbox=(2.3, 48.8, 2.4, 48.9),
        ...     datetime="2024-01-15T10:33:21Z",
        ...     cloud_cover=15.2
        ... )
    """
    id: str
    title: str
    provider: str
    product_type: str
    data_type: DataType
    geometry: dict                          # GeoJSON footprint
    bbox: Optional[tuple] = None            # (minx, miny, maxx, maxy)
    datetime: str = ""
    cloud_cover: Optional[float] = None
    thumbnail_url: Optional[str] = None
    size_mb: Optional[float] = None
    metadata: dict = field(default_factory=dict)

    # Internal - for download
    _eodag_product: Any = None

    def __post_init__(self):
        """Validate and process data after initialization"""
        # Ensure bbox is tuple if provided
        if self.bbox is not None and not isinstance(self.bbox, tuple):
            if isinstance(self.bbox, list) and len(self.bbox) == 4:
                self.bbox = tuple(self.bbox)

        # Convert string to DataType enum if needed
        if isinstance(self.data_type, str):
            try:
                self.data_type = DataType(self.data_type.lower())
            except ValueError:
                # Default to optical if unknown
                self.data_type = DataType.OPTICAL

    def __repr__(self):
        """String representation for debugging"""
        parts = [
            f"id={self.id[:50]}..." if len(self.id) > 50 else f"id={self.id}",
            f"provider={self.provider}",
            f"type={self.product_type}",
            f"date={self.datetime[:10]}" if self.datetime else "date=unknown"
        ]
        if self.cloud_cover is not None:
            parts.append(f"clouds={self.cloud_cover:.1f}%")

        return f"SearchResult({', '.join(parts)})"

    def to_dict(self) -> dict:
        """
        Convert to dictionary (excluding internal fields).

        Returns:
            Dictionary representation suitable for JSON serialization
        """
        # Handle geometry - convert Shapely objects to GeoJSON dict
        geometry = self.geometry
        if geometry is not None and not isinstance(geometry, dict):
            # Shapely geometry object
            if hasattr(geometry, '__geo_interface__'):
                geometry = dict(geometry.__geo_interface__)
            elif hasattr(geometry, 'mapping'):
                from shapely.geometry import mapping
                geometry = mapping(geometry)
            else:
                geometry = None

        return {
            "id": self.id,
            "title": self.title,
            "provider": self.provider,
            "product_type": self.product_type,
            "data_type": self.data_type.value if isinstance(self.data_type, DataType) else self.data_type,
            "geometry": geometry,
            "bbox": list(self.bbox) if self.bbox else None,
            "datetime": self.datetime,
            "cloud_cover": self.cloud_cover,
            "thumbnail_url": self.thumbnail_url,
            "size_mb": self.size_mb
        }

    @property
    def date(self) -> str:
        """Extract date portion from datetime string"""
        if self.datetime:
            return self.datetime[:10]
        return ""

    @property
    def year(self) -> Optional[int]:
        """Extract year from datetime"""
        if self.datetime and len(self.datetime) >= 4:
            try:
                return int(self.datetime[:4])
            except ValueError:
                return None
        return None
