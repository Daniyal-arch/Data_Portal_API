"""
Tests for data models
"""

import pytest
from geodatahub.models.request import DataRequest, DataType, OutputFormat
from geodatahub.models.result import SearchResult


class TestDataRequest:
    """Test DataRequest model"""

    def test_create_basic_request(self):
        """Test creating a basic request"""
        request = DataRequest(
            product="S2_MSI_L2A",
            location_name="Paris",
            start_date="2024-01-01",
            end_date="2024-01-31"
        )

        assert request.product == "S2_MSI_L2A"
        assert request.location_name == "Paris"
        assert request.start_date == "2024-01-01"
        assert request.end_date == "2024-01-31"

    def test_bbox_validation(self):
        """Test bounding box validation"""
        # Valid bbox
        request = DataRequest(bbox=(2.25, 48.81, 2.42, 48.90))
        assert len(request.bbox) == 4

        # Invalid bbox should raise ValueError
        with pytest.raises(ValueError):
            DataRequest(bbox=(2.25, 48.81))  # Only 2 values

    def test_cloud_cover_validation(self):
        """Test cloud cover validation"""
        # Valid cloud cover
        request = DataRequest(cloud_cover_max=20.0)
        assert request.cloud_cover_max == 20.0

        # Invalid cloud cover
        with pytest.raises(ValueError):
            DataRequest(cloud_cover_max=150.0)  # > 100

        with pytest.raises(ValueError):
            DataRequest(cloud_cover_max=-10.0)  # < 0

    def test_data_type_conversion(self):
        """Test DataType enum conversion"""
        request = DataRequest(data_type="optical")
        assert request.data_type == DataType.OPTICAL

    def test_repr(self):
        """Test string representation"""
        request = DataRequest(
            product="S2_MSI_L2A",
            location_name="Paris"
        )
        repr_str = repr(request)
        assert "S2_MSI_L2A" in repr_str
        assert "Paris" in repr_str


class TestSearchResult:
    """Test SearchResult model"""

    def test_create_result(self):
        """Test creating a search result"""
        result = SearchResult(
            id="test_id",
            title="Test Product",
            provider="test_provider",
            product_type="S2_MSI_L2A",
            data_type=DataType.OPTICAL,
            geometry={"type": "Point", "coordinates": [0, 0]},
            bbox=(2.25, 48.81, 2.42, 48.90),
            datetime="2024-01-15T10:00:00Z",
            cloud_cover=15.5
        )

        assert result.id == "test_id"
        assert result.cloud_cover == 15.5
        assert result.data_type == DataType.OPTICAL

    def test_to_dict(self):
        """Test converting to dictionary"""
        result = SearchResult(
            id="test_id",
            title="Test Product",
            provider="test_provider",
            product_type="S2_MSI_L2A",
            data_type=DataType.OPTICAL,
            geometry={"type": "Point", "coordinates": [0, 0]},
            datetime="2024-01-15T10:00:00Z"
        )

        result_dict = result.to_dict()
        assert result_dict["id"] == "test_id"
        assert result_dict["data_type"] == "optical"
        assert "_eodag_product" not in result_dict  # Internal field excluded

    def test_date_property(self):
        """Test date extraction"""
        result = SearchResult(
            id="test_id",
            title="Test Product",
            provider="test_provider",
            product_type="S2_MSI_L2A",
            data_type=DataType.OPTICAL,
            geometry={},
            datetime="2024-01-15T10:00:00Z"
        )

        assert result.date == "2024-01-15"

    def test_year_property(self):
        """Test year extraction"""
        result = SearchResult(
            id="test_id",
            title="Test Product",
            provider="test_provider",
            product_type="S2_MSI_L2A",
            data_type=DataType.OPTICAL,
            geometry={},
            datetime="2024-01-15T10:00:00Z"
        )

        assert result.year == 2024


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
