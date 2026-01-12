import json
import re
from typing import Optional, Tuple
from datetime import datetime, timedelta
from geodatahub.models.request import DataRequest, DataType
from geodatahub.nlp.geocoder import Geocoder
from geodatahub.nlp.llm_client import get_llm_client, BaseLLMClient


class NLParser:
    """
    Parse natural language queries to structured DataRequest objects.

    This parser uses LLM-based extraction with regex fallback for robust
    natural language understanding.

    Args:
        llm_provider: LLM provider to use
            - "groq": Use Groq API (fast, free tier)
            - "ollama": Use local Ollama
            - "openrouter": Use OpenRouter
            - "regex": No LLM, regex only
            - "auto": Try LLM providers, fallback to regex (default)

    Example:
        >>> parser = NLParser()
        >>> request = parser.parse("Sentinel-2 images of Paris from last month with less than 20% clouds")
        >>> print(request.product, request.location_name, request.cloud_cover_max)
        S2_MSI_L2A Paris 20.0
    """

    def __init__(self, llm_provider: str = "auto"):
        """Initialize parser with specified LLM provider"""
        self.llm_provider = llm_provider
        self.geocoder = Geocoder()
        self.llm_client = None
        self._init_llm()

    def _init_llm(self):
        """Initialize LLM client if not using regex-only mode"""
        if self.llm_provider != "regex":
            self.llm_client = get_llm_client(self.llm_provider)

    def parse(self, query: str) -> DataRequest:
        """
        Parse natural language query to structured DataRequest.

        Args:
            query: Natural language query string

        Returns:
            DataRequest object with extracted parameters

        Example:
            >>> parser = NLParser()
            >>> request = parser.parse("Get Landsat 8 data for New York from January 2024")
        """

        # Try LLM first if available
        if self.llm_client:
            try:
                return self._parse_with_llm(query)
            except Exception as e:
                print(f"LLM parsing failed: {e}, falling back to regex")

        # Fallback to regex
        return self._parse_with_regex(query)

    def _parse_with_llm(self, query: str) -> DataRequest:
        """Use LLM to extract structured data from query"""

        prompt = self._build_prompt(query)
        response = self.llm_client.complete(prompt)

        # Extract JSON from response (handle cases where LLM adds explanation)
        json_str = self._extract_json(response)
        parsed = json.loads(json_str)

        return self._dict_to_request(parsed, query)

    def _build_prompt(self, query: str) -> str:
        """Build LLM prompt for parameter extraction"""
        return f'''Extract geospatial data request parameters from this query.

Query: "{query}"

Return a JSON object with these fields (use null if not mentioned):
{{
    "product": "product code like S2_MSI_L2A, LANDSAT_C2L2, COP-DEM_GLO-30",
    "data_type": "optical|sar|dem|land_cover|climate|air_quality",
    "location": "location name mentioned",
    "bbox": [minx, miny, maxx, maxy] or null,
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD",
    "cloud_cover_max": number 0-100 or null,
    "provider": "preferred provider or null"
}}

Product mappings:
- sentinel-2, sentinel 2, s2 → S2_MSI_L2A (optical)
- sentinel-1, sentinel 1, s1, sar → S1_SAR_GRD (sar)
- landsat 8, landsat-8, l8 → LANDSAT_C2L2 (optical)
- landsat 9, landsat-9, l9 → LANDSAT_C2L2 (optical)
- dem, elevation, srtm, height → COP-DEM_GLO-30 (dem)
- land cover, landcover, lulc → ESA_WORLDCOVER (land_cover)
- modis → MODIS_MOD09GA (optical)

Time mappings:
- "last week" → past 7 days from today
- "last month" → past 30 days from today
- "last N days" → past N days from today
- "yesterday" → yesterday's date
- "January 2024" → 2024-01-01 to 2024-01-31
- "2024" → 2024-01-01 to 2024-12-31

Cloud cover:
- "less than 20% clouds" → 20
- "clear skies" → 10
- "mostly clear" → 20

Return ONLY valid JSON, no explanation.'''

    def _extract_json(self, text: str) -> str:
        """Extract JSON object from LLM response"""
        # Try to find JSON object in response
        match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', text, re.DOTALL)
        if match:
            return match.group(0)

        # If no JSON found, assume entire response is JSON
        return text.strip()

    def _dict_to_request(self, parsed: dict, original_query: str) -> DataRequest:
        """Convert parsed dictionary to DataRequest object"""

        # Extract location and geocode if needed
        location = parsed.get('location')
        geometry = None
        bbox = parsed.get('bbox')

        if bbox and isinstance(bbox, list) and len(bbox) == 4:
            bbox = tuple(bbox)
        elif location:
            geo_result = self.geocoder.geocode(location)
            if geo_result:
                bbox = geo_result.get('bbox')
                geometry = geo_result.get('geometry')

        # Parse data type
        data_type_str = parsed.get('data_type')
        data_type = None
        if data_type_str:
            try:
                data_type = DataType(data_type_str.lower())
            except ValueError:
                pass

        return DataRequest(
            product=parsed.get('product'),
            data_type=data_type,
            provider=parsed.get('provider'),
            location_name=location,
            geometry=geometry,
            bbox=bbox,
            start_date=parsed.get('start_date'),
            end_date=parsed.get('end_date'),
            cloud_cover_max=parsed.get('cloud_cover_max')
        )

    def _parse_with_regex(self, query: str) -> DataRequest:
        """Fallback regex-based parsing"""
        query_lower = query.lower()

        # Extract product and data type
        product, data_type = self._extract_product_regex(query_lower)

        # Extract location
        location = self._extract_location_regex(query)

        # Extract dates
        start_date, end_date = self._extract_dates_regex(query_lower)

        # Extract cloud cover
        cloud_cover = self._extract_cloud_cover_regex(query_lower)

        # Geocode location if found
        geometry = None
        bbox = None
        if location:
            geo_result = self.geocoder.geocode(location)
            if geo_result:
                bbox = geo_result.get('bbox')
                geometry = geo_result.get('geometry')

        return DataRequest(
            product=product,
            data_type=data_type,
            location_name=location,
            geometry=geometry,
            bbox=bbox,
            start_date=start_date,
            end_date=end_date,
            cloud_cover_max=cloud_cover
        )

    def _extract_product_regex(self, query: str) -> Tuple[Optional[str], Optional[DataType]]:
        """Extract product type using regex patterns"""
        patterns = {
            r'sentinel[-\s]?2|s2\b': ('S2_MSI_L2A', DataType.OPTICAL),
            r'sentinel[-\s]?1|s1\b|sar\b': ('S1_SAR_GRD', DataType.SAR),
            r'landsat[-\s]?8|l8\b': ('LANDSAT_C2L2', DataType.OPTICAL),
            r'landsat[-\s]?9|l9\b': ('LANDSAT_C2L2', DataType.OPTICAL),
            r'landsat': ('LANDSAT_C2L2', DataType.OPTICAL),
            r'dem\b|elevation|srtm|height': ('COP-DEM_GLO-30', DataType.DEM),
            r'land\s?cover|lulc': ('ESA_WORLDCOVER', DataType.LAND_COVER),
            r'modis': ('MODIS_MOD09GA', DataType.OPTICAL),
        }

        for pattern, (product, dtype) in patterns.items():
            if re.search(pattern, query):
                return product, dtype

        # Default to Sentinel-2 if no match
        return 'S2_MSI_L2A', DataType.OPTICAL

    def _extract_dates_regex(self, query: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract date range from query"""
        now = datetime.now()

        # Relative patterns
        if 'last week' in query or 'past week' in query:
            return (now - timedelta(days=7)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')

        if 'last month' in query or 'past month' in query:
            return (now - timedelta(days=30)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')

        if 'yesterday' in query:
            yesterday = now - timedelta(days=1)
            return yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d')

        # "last N days"
        match = re.search(r'(?:last|past)\s+(\d+)\s+days?', query)
        if match:
            days = int(match.group(1))
            return (now - timedelta(days=days)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')

        # Month Year pattern: "January 2024"
        months = {
            'january': 1, 'february': 2, 'march': 3, 'april': 4,
            'may': 5, 'june': 6, 'july': 7, 'august': 8,
            'september': 9, 'october': 10, 'november': 11, 'december': 12
        }
        for month_name, month_num in months.items():
            match = re.search(rf'{month_name}\s+(\d{{4}})', query)
            if match:
                year = int(match.group(1))
                start = datetime(year, month_num, 1)
                if month_num == 12:
                    end = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end = datetime(year, month_num + 1, 1) - timedelta(days=1)
                return start.strftime('%Y-%m-%d'), end.strftime('%Y-%m-%d')

        # Year only: "2024"
        match = re.search(r'\b(20\d{2})\b', query)
        if match:
            year = int(match.group(1))
            return f"{year}-01-01", f"{year}-12-31"

        # Explicit date range: "from YYYY-MM-DD to YYYY-MM-DD"
        match = re.search(r'from\s+(\d{4}-\d{2}-\d{2})\s+to\s+(\d{4}-\d{2}-\d{2})', query)
        if match:
            return match.group(1), match.group(2)

        # Single date: "on YYYY-MM-DD"
        match = re.search(r'(?:on|date)\s+(\d{4}-\d{2}-\d{2})', query)
        if match:
            return match.group(1), match.group(1)

        # Default: last 30 days
        return (now - timedelta(days=30)).strftime('%Y-%m-%d'), now.strftime('%Y-%m-%d')

    def _extract_cloud_cover_regex(self, query: str) -> Optional[float]:
        """Extract cloud cover threshold"""
        # "less than 20% clouds"
        match = re.search(r'(?:less\s+than|under|below|max|maximum)\s+(\d+)\s*%?\s*cloud', query)
        if match:
            return float(match.group(1))

        # "20% cloud cover"
        match = re.search(r'(\d+)\s*%\s*cloud', query)
        if match:
            return float(match.group(1))

        # "clear skies" or "clear"
        if re.search(r'\bclear\s+sk(?:y|ies)\b', query):
            return 10.0

        # "mostly clear"
        if re.search(r'mostly\s+clear', query):
            return 20.0

        return None

    def _extract_location_regex(self, query: str) -> Optional[str]:
        """Extract location from query"""
        # Look for "for <location>" or "of <location>" or "in <location>"
        patterns = [
            r'(?:for|of|in|over|around|near)\s+([A-Z][a-zA-Z\s,]+?)(?:\s+(?:from|last|with|during|between|in\s+\d{4})|$)',
            r'(?:for|of|in|over|around|near)\s+([A-Z][a-zA-Z\s,]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                location = match.group(1).strip()

                # Remove trailing punctuation
                location = location.rstrip('.,;:')

                # Filter out common non-location words
                stopwords = [
                    'the', 'last', 'month', 'week', 'year',
                    'january', 'february', 'march', 'april', 'may', 'june',
                    'july', 'august', 'september', 'october', 'november', 'december',
                    'sentinel', 'landsat', 'modis', 'images', 'data'
                ]
                location_lower = location.lower()

                # Check if location is not just a stopword
                if location_lower not in stopwords and len(location) > 2:
                    return location

        return None
