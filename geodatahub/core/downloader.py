from eodag import EODataAccessGateway
from eodag.api.search_result import SearchResult as EODAGSearchResult
from typing import List, Optional, Dict, Any
from pathlib import Path
from geodatahub.models.request import DataRequest, DataType
from geodatahub.models.result import SearchResult


class GeoDataHub:
    """
    Main interface for searching and downloading geospatial data.

    This class integrates with EODAG to provide unified access to multiple
    geospatial data providers with a consistent interface.

    Args:
        config_path: Optional path to EODAG configuration file

    Example:
        >>> hub = GeoDataHub()
        >>> request = DataRequest(
        ...     product="S2_MSI_L2A",
        ...     bbox=(2.3, 48.8, 2.4, 48.9),
        ...     start_date="2024-01-01",
        ...     end_date="2024-01-31"
        ... )
        >>> results = hub.search(request)
        >>> paths = hub.download_all(results, "./data")
    """

    def __init__(self, config_path: Optional[str] = None):
        """Initialize GeoDataHub with optional EODAG config"""
        self.dag = EODataAccessGateway(user_conf_file_path=config_path)
        self._product_type_mapping = self._build_product_mapping()

    def search(self, request: DataRequest) -> List[SearchResult]:
        """
        Search for products matching the request.

        Args:
            request: DataRequest object with search parameters

        Returns:
            List of SearchResult objects

        Example:
            >>> hub = GeoDataHub()
            >>> request = DataRequest(product="S2_MSI_L2A", location_name="Paris")
            >>> results = hub.search(request)
        """

        # Build EODAG search parameters
        search_params = {}

        # Product type
        if request.product:
            search_params['productType'] = request.product
        else:
            # Default to Sentinel-2 if no product specified
            search_params['productType'] = 'S2_MSI_L2A'

        # Geometry/bbox
        if request.bbox:
            search_params['geom'] = {
                'lonmin': request.bbox[0],
                'latmin': request.bbox[1],
                'lonmax': request.bbox[2],
                'latmax': request.bbox[3]
            }
        elif request.geometry:
            search_params['geom'] = request.geometry

        # Date range
        if request.start_date:
            search_params['start'] = request.start_date

        if request.end_date:
            search_params['end'] = request.end_date

        # Cloud cover
        if request.cloud_cover_max is not None:
            search_params['cloudCover'] = request.cloud_cover_max

        # Provider
        if request.provider:
            search_params['provider'] = request.provider

        # Execute search
        try:
            print(f"Searching with parameters: {search_params}")
            eodag_results = self.dag.search(**search_params)

            if not eodag_results:
                print("No results found")
                return []

            print(f"Found {len(eodag_results)} results from EODAG")

        except Exception as e:
            print(f"Search failed: {e}")
            return []

        # Convert to our result format
        results = []
        for item in eodag_results[:request.limit]:
            result = self._convert_result(item, request.data_type)
            results.append(result)

        return results

    def download(self, result: SearchResult, output_dir: str) -> str:
        """
        Download a single product.

        Args:
            result: SearchResult to download
            output_dir: Directory to save downloaded files

        Returns:
            Path to downloaded file

        Example:
            >>> hub = GeoDataHub()
            >>> path = hub.download(result, "./data")
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        if result._eodag_product:
            try:
                print(f"Downloading {result.title}...")
                path = self.dag.download(
                    result._eodag_product,
                    outputs_prefix=str(output_path)
                )
                print(f"Downloaded to: {path}")
                return path
            except Exception as e:
                raise Exception(f"Download failed: {e}")
        else:
            raise ValueError("Result does not have associated EODAG product")

    def download_all(self, results: List[SearchResult], output_dir: str, skip_errors: bool = True) -> List[str]:
        """
        Download multiple products.

        Args:
            results: List of SearchResults to download
            output_dir: Directory to save downloaded files
            skip_errors: If True, continue downloading even if some fail

        Returns:
            List of paths to successfully downloaded files

        Example:
            >>> hub = GeoDataHub()
            >>> paths = hub.download_all(results, "./data")
        """
        paths = []
        total = len(results)

        for i, result in enumerate(results, 1):
            try:
                print(f"\n[{i}/{total}] Downloading {result.id}")
                path = self.download(result, output_dir)
                paths.append(path)
            except Exception as e:
                print(f"Failed to download {result.id}: {e}")
                if not skip_errors:
                    raise

        return paths

    def list_products(self, provider: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List available product types.

        Args:
            provider: Optional provider name to filter by

        Returns:
            List of product type dictionaries

        Example:
            >>> hub = GeoDataHub()
            >>> products = hub.list_products()
            >>> for p in products:
            ...     print(p['ID'])
        """
        try:
            products = self.dag.list_product_types(provider=provider)
            return products
        except Exception as e:
            print(f"Failed to list products: {e}")
            return []

    def list_providers(self) -> List[str]:
        """
        List available providers.

        Returns:
            List of provider names

        Example:
            >>> hub = GeoDataHub()
            >>> providers = hub.list_providers()
            >>> print(providers)
            ['cop_dataspace', 'usgs', 'aws_eos', ...]
        """
        try:
            return self.dag.available_providers()
        except Exception as e:
            print(f"Failed to list providers: {e}")
            return []

    def _convert_result(self, eodag_product: Any, data_type: Optional[DataType]) -> SearchResult:
        """
        Convert EODAG product to our SearchResult model.

        Args:
            eodag_product: EODAG product object
            data_type: Optional data type hint

        Returns:
            SearchResult object
        """

        props = eodag_product.properties

        # Extract geometry
        geometry = eodag_product.geometry
        bbox = None

        # Try to extract bbox from geometry
        if hasattr(geometry, 'bounds'):
            # Shapely geometry
            bounds = geometry.bounds
            bbox = (bounds[0], bounds[1], bounds[2], bounds[3])
        elif isinstance(geometry, dict):
            # GeoJSON geometry
            if 'bbox' in geometry:
                bbox = tuple(geometry['bbox'])
            # Convert to dict if needed
            geometry = geometry
        else:
            # Try to get as dict
            try:
                geometry = dict(geometry)
            except:
                geometry = {"type": "Polygon", "coordinates": []}

        # Infer data type from product type if not provided
        if not data_type:
            product_type = eodag_product.product_type
            if 'S2' in product_type or 'LANDSAT' in product_type or 'MODIS' in product_type:
                data_type = DataType.OPTICAL
            elif 'S1' in product_type or 'SAR' in product_type:
                data_type = DataType.SAR
            elif 'DEM' in product_type or 'SRTM' in product_type:
                data_type = DataType.DEM
            elif 'WORLDCOVER' in product_type or 'CORINE' in product_type:
                data_type = DataType.LAND_COVER
            else:
                data_type = DataType.OPTICAL

        # Extract common fields with fallbacks
        product_id = props.get('id', props.get('title', str(eodag_product)))
        title = props.get('title', product_id)
        datetime_str = props.get('startTimeFromAscendingNode',
                                  props.get('datetime',
                                           props.get('acquisitionDate', '')))

        return SearchResult(
            id=product_id,
            title=title,
            provider=eodag_product.provider,
            product_type=eodag_product.product_type,
            data_type=data_type,
            geometry=geometry,
            bbox=bbox,
            datetime=datetime_str,
            cloud_cover=props.get('cloudCover'),
            thumbnail_url=props.get('quicklook'),
            size_mb=props.get('size'),
            metadata=props,
            _eodag_product=eodag_product
        )

    def _build_product_mapping(self) -> Dict[str, str]:
        """
        Build mapping of common names to EODAG product types.

        Returns:
            Dictionary mapping common names to product type codes
        """
        return {
            'sentinel-2': 'S2_MSI_L2A',
            'sentinel-1': 'S1_SAR_GRD',
            'landsat-8': 'LANDSAT_C2L2',
            'landsat-9': 'LANDSAT_C2L2',
            'dem': 'COP-DEM_GLO-30',
            'srtm': 'SRTM_DEM',
            'land-cover': 'ESA_WORLDCOVER',
            'modis': 'MODIS_MOD09GA',
        }

    def get_product_info(self, product_type: str, provider: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a product type.

        Args:
            product_type: Product type code
            provider: Optional provider name

        Returns:
            Dictionary with product information or None
        """
        products = self.list_products(provider=provider)
        for product in products:
            if product.get('ID') == product_type or product.get('id') == product_type:
                return product
        return None
