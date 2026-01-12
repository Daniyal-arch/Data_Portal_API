import requests
from typing import Optional, Dict
import time


class Geocoder:
    """
    Geocode location names to coordinates using Nominatim (OpenStreetMap).

    This class provides geocoding functionality to convert place names into
    geographic coordinates and bounding boxes.

    Attributes:
        base_url: Nominatim API endpoint
        headers: HTTP headers including User-Agent

    Example:
        >>> geocoder = Geocoder()
        >>> result = geocoder.geocode("Paris, France")
        >>> print(result['bbox'])
        (2.224122, 48.815573, 2.469920, 48.902156)
    """

    def __init__(self):
        self.base_url = "https://nominatim.openstreetmap.org/search"
        self.headers = {"User-Agent": "GeoDataHub/1.0"}
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Nominatim requires max 1 request per second

    def _rate_limit(self):
        """Ensure we don't exceed Nominatim's rate limit"""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last_request)

        self._last_request_time = time.time()

    def geocode(self, location: str) -> Optional[Dict]:
        """
        Convert location name to geometry.

        Args:
            location: Location name (e.g., "Paris", "New York, USA", "Mount Everest")

        Returns:
            Dictionary with keys:
                - bbox: (minx, miny, maxx, maxy) tuple
                - geometry: GeoJSON geometry object
                - display_name: Full formatted address
                - lat: Latitude of centroid
                - lon: Longitude of centroid

            Returns None if geocoding fails.

        Example:
            >>> geocoder = Geocoder()
            >>> result = geocoder.geocode("London")
            >>> print(result['display_name'])
            'London, Greater London, England, United Kingdom'
        """
        try:
            # Rate limiting
            self._rate_limit()

            params = {
                "q": location,
                "format": "json",
                "limit": 1,
                "polygon_geojson": 1
            }

            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            results = response.json()
            if not results:
                print(f"No results found for location: '{location}'")
                return None

            result = results[0]

            # Extract bounding box
            bbox = result.get('boundingbox')
            if bbox:
                # Nominatim returns [south, north, west, east]
                # Convert to (minx, miny, maxx, maxy) = (west, south, east, north)
                bbox = (
                    float(bbox[2]),  # west (minx)
                    float(bbox[0]),  # south (miny)
                    float(bbox[3]),  # east (maxx)
                    float(bbox[1])   # north (maxy)
                )

            # Build GeoJSON geometry
            geometry = result.get('geojson')
            if not geometry:
                # Fallback: create point geometry from lat/lon
                geometry = {
                    "type": "Point",
                    "coordinates": [float(result.get('lon')), float(result.get('lat'))]
                }

            return {
                "bbox": bbox,
                "geometry": geometry,
                "display_name": result.get('display_name'),
                "lat": float(result.get('lat')),
                "lon": float(result.get('lon'))
            }

        except requests.exceptions.RequestException as e:
            print(f"Geocoding network error for '{location}': {e}")
            return None
        except (KeyError, ValueError, IndexError) as e:
            print(f"Geocoding parsing error for '{location}': {e}")
            return None
        except Exception as e:
            print(f"Geocoding failed for '{location}': {e}")
            return None

    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Convert coordinates to location name.

        Args:
            lat: Latitude
            lon: Longitude

        Returns:
            Dictionary with location information, or None if failed

        Example:
            >>> geocoder = Geocoder()
            >>> result = geocoder.reverse_geocode(48.8566, 2.3522)
            >>> print(result['display_name'])
            'Paris, Île-de-France, France'
        """
        try:
            self._rate_limit()

            params = {
                "lat": lat,
                "lon": lon,
                "format": "json"
            }

            response = requests.get(
                "https://nominatim.openstreetmap.org/reverse",
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()

            result = response.json()

            return {
                "display_name": result.get('display_name'),
                "address": result.get('address', {}),
                "lat": float(result.get('lat')),
                "lon": float(result.get('lon'))
            }

        except Exception as e:
            print(f"Reverse geocoding failed for ({lat}, {lon}): {e}")
            return None
