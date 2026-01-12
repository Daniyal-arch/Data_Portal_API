"""
Tests for NLP parser
"""

import pytest
from geodatahub.nlp.parser import NLParser
from geodatahub.models.request import DataType


class TestNLParser:
    """Test the natural language parser"""

    def setup_method(self):
        """Setup for each test"""
        # Use regex-only mode for testing (no LLM required)
        self.parser = NLParser(llm_provider="regex")

    def test_parse_sentinel2_query(self):
        """Test parsing Sentinel-2 query"""
        query = "Sentinel-2 images of Paris from January 2024"
        request = self.parser.parse(query)

        assert request.product == "S2_MSI_L2A"
        assert request.data_type == DataType.OPTICAL
        assert request.location_name == "Paris"
        assert request.start_date is not None
        assert request.end_date is not None

    def test_parse_landsat_query(self):
        """Test parsing Landsat query"""
        query = "Landsat 8 data for New York"
        request = self.parser.parse(query)

        assert request.product == "LANDSAT_C2L2"
        assert request.data_type == DataType.OPTICAL
        assert request.location_name == "New York"

    def test_parse_sar_query(self):
        """Test parsing SAR query"""
        query = "Sentinel-1 SAR data for Tokyo"
        request = self.parser.parse(query)

        assert request.product == "S1_SAR_GRD"
        assert request.data_type == DataType.SAR
        assert request.location_name == "Tokyo"

    def test_parse_dem_query(self):
        """Test parsing DEM query"""
        query = "DEM data for Mount Everest"
        request = self.parser.parse(query)

        assert request.product == "COP-DEM_GLO-30"
        assert request.data_type == DataType.DEM

    def test_parse_cloud_cover(self):
        """Test parsing cloud cover"""
        query = "Sentinel-2 with less than 20% cloud cover"
        request = self.parser.parse(query)

        assert request.cloud_cover_max == 20.0

    def test_parse_relative_dates(self):
        """Test parsing relative dates"""
        query = "Sentinel-2 from last week"
        request = self.parser.parse(query)

        assert request.start_date is not None
        assert request.end_date is not None

    def test_parse_month_year(self):
        """Test parsing month and year"""
        query = "Sentinel-2 from January 2024"
        request = self.parser.parse(query)

        assert request.start_date == "2024-01-01"
        assert request.end_date == "2024-01-31"

    def test_parse_location_extraction(self):
        """Test location name extraction"""
        queries_locations = [
            ("images of Paris", "Paris"),
            ("data for London", "London"),
            ("images in New York", "New York"),
            ("over Tokyo", "Tokyo"),
        ]

        for query, expected_location in queries_locations:
            request = self.parser.parse(query)
            assert request.location_name == expected_location


class TestDateParsing:
    """Test date parsing functionality"""

    def setup_method(self):
        """Setup for each test"""
        self.parser = NLParser(llm_provider="regex")

    def test_last_week(self):
        """Test 'last week' parsing"""
        request = self.parser.parse("data from last week")
        assert request.start_date is not None
        assert request.end_date is not None

    def test_last_month(self):
        """Test 'last month' parsing"""
        request = self.parser.parse("data from last month")
        assert request.start_date is not None
        assert request.end_date is not None

    def test_specific_month(self):
        """Test specific month parsing"""
        months = [
            ("January 2024", "2024-01-01", "2024-01-31"),
            ("February 2024", "2024-02-01", "2024-02-29"),  # Leap year
            ("December 2024", "2024-12-01", "2024-12-31"),
        ]

        for query, expected_start, expected_end in months:
            request = self.parser.parse(query)
            assert request.start_date == expected_start
            assert request.end_date == expected_end


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
