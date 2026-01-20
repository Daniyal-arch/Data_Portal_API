"""
GeoDataHub REST API

A FastAPI service providing RESTful access to geospatial data search and download.

Run with:
    uvicorn geodatahub_api.main:app --reload
"""

from fastapi import FastAPI, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

try:
    from geodatahub import GeoDataHub, NLParser, DataRequest
    from geodatahub.models.request import DataType, OutputFormat
    from geodatahub.models.result import SearchResult
    from geodatahub.data_sources import (
        DATA_SOURCES, DataCategory,
        get_sources_for_analysis, get_sources_by_category, get_sources_by_keyword
    )
except ImportError:
    raise ImportError(
        "geodatahub package not found. Please install it first:\n"
        "  pip install -e ."
    )


# FastAPI app
app = FastAPI(
    title="GeoData Hub API",
    description="Unified API for searching and downloading geospatial data using natural language",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize GeoDataHub and parser
hub = GeoDataHub()
parser = NLParser()

# Store search results for download reference
_last_search_results: Dict[str, Any] = {}


# Pydantic models for request/response

class SearchRequest(BaseModel):
    """Search request model"""
    query: Optional[str] = Field(None, description="Natural language query")
    product: Optional[str] = Field(None, description="Product type (e.g., S2_MSI_L2A)")
    data_type: Optional[str] = Field(None, description="Data type (optical, sar, dem, etc.)")
    bbox: Optional[List[float]] = Field(None, description="Bounding box [minx, miny, maxx, maxy]")
    location: Optional[str] = Field(None, description="Location name to geocode")
    start_date: Optional[str] = Field(None, description="Start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="End date (YYYY-MM-DD)")
    cloud_cover_max: Optional[float] = Field(None, description="Maximum cloud cover (0-100)")
    provider: Optional[str] = Field(None, description="Preferred provider")
    limit: int = Field(10, description="Maximum number of results", ge=1, le=100)

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Sentinel-2 images of Paris from January 2024 with less than 20% cloud cover",
                "limit": 10
            }
        }


class SearchResultResponse(BaseModel):
    """Individual search result"""
    id: str
    title: str
    provider: str
    product_type: str
    data_type: str
    datetime: str
    cloud_cover: Optional[float]
    bbox: Optional[List[float]]
    thumbnail_url: Optional[str]
    size_mb: Optional[float]


class SearchResponse(BaseModel):
    """Search response model"""
    count: int
    query: Optional[str]
    parsed_request: Dict[str, Any]
    results: List[SearchResultResponse]


class ProductInfo(BaseModel):
    """Product information model"""
    id: str
    title: Optional[str]
    provider: Optional[str]
    description: Optional[str]


# API Routes

@app.get("/", tags=["General"])
def root():
    """API root endpoint"""
    return {
        "message": "GeoData Hub API",
        "version": "0.1.0",
        "docs": "/docs",
        "endpoints": {
            "search": "/search",
            "search_nl": "/search/nl",
            "products": "/products",
            "providers": "/providers",
            "download": "/download",
            "datasources": "/datasources",
            "datasources_recommend": "/datasources/recommend",
            "datasources_categories": "/datasources/categories/list"
        }
    }


@app.get("/health", tags=["General"])
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "geodatahub-api"
    }


@app.post("/search", response_model=SearchResponse, tags=["Search"])
def search(request: SearchRequest):
    """
    Search for geospatial data.

    Supports both natural language queries and explicit parameters.
    Natural language query takes precedence if provided.

    Example:
        ```json
        {
            "query": "Sentinel-2 images of Paris from last month",
            "limit": 5
        }
        ```
    """
    try:
        # Build DataRequest from either natural language or explicit params
        if request.query:
            data_request = parser.parse(request.query)

            # Override with explicit parameters if provided
            if request.product:
                data_request.product = request.product
            if request.bbox:
                data_request.bbox = tuple(request.bbox)
            if request.location:
                data_request.location_name = request.location
            if request.start_date:
                data_request.start_date = request.start_date
            if request.end_date:
                data_request.end_date = request.end_date
            if request.cloud_cover_max is not None:
                data_request.cloud_cover_max = request.cloud_cover_max
            if request.provider:
                data_request.provider = request.provider
            data_request.limit = request.limit

        else:
            # Build from explicit parameters only
            data_request = DataRequest(
                product=request.product,
                bbox=tuple(request.bbox) if request.bbox else None,
                location_name=request.location,
                start_date=request.start_date,
                end_date=request.end_date,
                cloud_cover_max=request.cloud_cover_max,
                provider=request.provider,
                limit=request.limit
            )

        # Execute search
        results = hub.search(data_request)

        # Format response
        return SearchResponse(
            count=len(results),
            query=request.query,
            parsed_request={
                "product": data_request.product,
                "data_type": data_request.data_type.value if data_request.data_type else None,
                "location": data_request.location_name,
                "bbox": data_request.bbox,
                "start_date": data_request.start_date,
                "end_date": data_request.end_date,
                "cloud_cover_max": data_request.cloud_cover_max,
                "provider": data_request.provider
            },
            results=[
                SearchResultResponse(
                    id=r.id,
                    title=r.title,
                    provider=r.provider,
                    product_type=r.product_type,
                    data_type=r.data_type.value if isinstance(r.data_type, DataType) else r.data_type,
                    datetime=r.datetime,
                    cloud_cover=r.cloud_cover,
                    bbox=list(r.bbox) if r.bbox else None,
                    thumbnail_url=r.thumbnail_url,
                    size_mb=r.size_mb
                )
                for r in results
            ]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/search/nl", tags=["Search"])
def search_natural_language(
    q: str = Query(..., description="Natural language query"),
    limit: int = Query(10, description="Maximum number of results", ge=1, le=100)
):
    """
    Search using natural language query (GET endpoint).

    Example:
        GET /search/nl?q=Sentinel-2 images of London from last week&limit=5
    """
    try:
        # Parse query
        data_request = parser.parse(q)
        data_request.limit = limit

        # Execute search
        results = hub.search(data_request)

        # Cache results for download
        for r in results:
            _last_search_results[r.id] = r

        # Format response
        return {
            "query": q,
            "parsed": {
                "product": data_request.product,
                "data_type": data_request.data_type.value if data_request.data_type else None,
                "location": data_request.location_name,
                "bbox": data_request.bbox,
                "start_date": data_request.start_date,
                "end_date": data_request.end_date,
                "cloud_cover_max": data_request.cloud_cover_max
            },
            "count": len(results),
            "results": [r.to_dict() for r in results],
            "download_hint": "Use POST /download with product_id to download any result"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/products", tags=["Metadata"])
def list_products(
    provider: Optional[str] = Query(None, description="Filter by provider")
):
    """
    List available product types.

    Example:
        GET /products
        GET /products?provider=cop_dataspace
    """
    try:
        products = hub.list_products(provider=provider)

        return {
            "count": len(products),
            "provider": provider,
            "products": [
                {
                    "id": p.get('ID', p.get('id', 'Unknown')),
                    "title": p.get('title', p.get('productType', '')),
                    "provider": p.get('provider', ''),
                    "description": p.get('description', '')
                }
                for p in products
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list products: {str(e)}")


@app.get("/products/{product_id}", tags=["Metadata"])
def get_product_info(
    product_id: str,
    provider: Optional[str] = Query(None, description="Provider name")
):
    """
    Get detailed information about a specific product type.

    Example:
        GET /products/S2_MSI_L2A
    """
    try:
        info = hub.get_product_info(product_id, provider=provider)

        if not info:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")

        return info

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get product info: {str(e)}")


@app.get("/providers", tags=["Metadata"])
def list_providers():
    """
    List available data providers.

    Example:
        GET /providers
    """
    try:
        providers = hub.list_providers()

        return {
            "count": len(providers),
            "providers": providers
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list providers: {str(e)}")


@app.get("/data-types", tags=["Metadata"])
def list_data_types():
    """List available data types"""
    return {
        "data_types": [dt.value for dt in DataType]
    }


# Download functionality

class DownloadRequest(BaseModel):
    """Download request model"""
    product_id: str = Field(..., description="Product ID from search results")
    output_dir: Optional[str] = Field(None, description="Output directory (default: ./downloads)")

    class Config:
        json_schema_extra = {
            "example": {
                "product_id": "S2A_MSIL2A_20240115T103321_N0510_R108_T31UDQ_20240115T144655",
                "output_dir": "f:/Automating_data_portal/downloads"
            }
        }


class DownloadResponse(BaseModel):
    """Download response model"""
    status: str
    product_id: str
    message: str
    file_path: Optional[str] = None


@app.post("/download", response_model=DownloadResponse, tags=["Download"])
def download_product(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Download a satellite product by ID.

    First search for products, then use the product ID from results to download.
    Downloads run in the background.

    Example:
        ```json
        {
            "product_id": "S2A_MSIL2A_20240115...",
            "output_dir": "f:/Automating_data_portal/downloads"
        }
        ```
    """
    try:
        # Check if product is in cache
        if request.product_id not in _last_search_results:
            raise HTTPException(
                status_code=404,
                detail=f"Product {request.product_id} not found in recent search results. Please search first."
            )

        result = _last_search_results[request.product_id]
        output_dir = request.output_dir or "f:/Automating_data_portal/downloads"

        # Download synchronously (for small files) or use background for large
        try:
            file_path = hub.download(result, output_dir)
            return DownloadResponse(
                status="completed",
                product_id=request.product_id,
                message="Download completed successfully",
                file_path=str(file_path)
            )
        except Exception as e:
            return DownloadResponse(
                status="failed",
                product_id=request.product_id,
                message=f"Download failed: {str(e)}",
                file_path=None
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download failed: {str(e)}")


@app.post("/search-and-download", tags=["Download"])
def search_and_download(
    query: str = Query(..., description="Natural language search query"),
    output_dir: Optional[str] = Query(None, description="Output directory"),
    limit: int = Query(1, description="Number of products to download", ge=1, le=5)
):
    """
    Search and download in one step.

    Searches for products and downloads the top results.

    Example:
        POST /search-and-download?query=Sentinel-2 Monaco January 2024&limit=1
    """
    try:
        # Parse and search
        data_request = parser.parse(query)
        data_request.limit = limit
        results = hub.search(data_request)

        if not results:
            return {
                "status": "no_results",
                "query": query,
                "message": "No products found matching your query"
            }

        # Cache results
        for r in results:
            _last_search_results[r.id] = r

        output_dir = output_dir or "f:/Automating_data_portal/downloads"
        downloaded = []
        failed = []

        for result in results:
            try:
                file_path = hub.download(result, output_dir)
                downloaded.append({
                    "product_id": result.id,
                    "file_path": str(file_path),
                    "cloud_cover": result.cloud_cover,
                    "datetime": result.datetime
                })
            except Exception as e:
                failed.append({
                    "product_id": result.id,
                    "error": str(e)
                })

        return {
            "status": "completed",
            "query": query,
            "searched": len(results),
            "downloaded": len(downloaded),
            "failed": len(failed),
            "results": downloaded,
            "errors": failed if failed else None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search and download failed: {str(e)}")


# Data Sources Catalog Endpoints

class DataSourceResponse(BaseModel):
    """Data source information model"""
    id: str
    name: str
    description: str
    provider: str
    category: str
    resolution_m: Optional[float]
    revisit_days: Optional[int]
    bands: List[str]
    use_cases: List[str]
    suitable_indices: List[str]
    keywords: List[str]
    pros: List[str]
    cons: List[str]


class RecommendationRequest(BaseModel):
    """AI recommendation request"""
    analysis_description: str = Field(..., description="Description of the analysis you want to perform")

    class Config:
        json_schema_extra = {
            "example": {
                "analysis_description": "I want to monitor crop health and detect drought stress in agricultural fields"
            }
        }


@app.get("/datasources", tags=["Data Sources"])
def list_data_sources(
    category: Optional[str] = Query(None, description="Filter by category (optical, sar, dem, climate, etc.)"),
    keyword: Optional[str] = Query(None, description="Filter by keyword")
):
    """
    List all available data sources in the catalog.

    Optionally filter by category or keyword.

    Categories: optical, sar, dem, land_cover, climate, ocean, atmosphere, vegetation, nighttime

    Example:
        GET /datasources
        GET /datasources?category=optical
        GET /datasources?keyword=agriculture
    """
    try:
        if category:
            try:
                cat = DataCategory(category.lower())
                sources = get_sources_by_category(cat)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid category '{category}'. Valid categories: {[c.value for c in DataCategory]}"
                )
        elif keyword:
            sources = get_sources_by_keyword(keyword)
        else:
            sources = list(DATA_SOURCES.values())

        return {
            "count": len(sources),
            "filter": {"category": category, "keyword": keyword},
            "datasources": [
                {
                    "id": s.id,
                    "name": s.name,
                    "description": s.description,
                    "provider": s.provider,
                    "category": s.category.value,
                    "resolution_m": s.resolution_m,
                    "revisit_days": s.revisit_days,
                    "bands": s.bands,
                    "use_cases": s.use_cases,
                    "suitable_indices": s.suitable_indices,
                    "keywords": s.keywords,
                    "pros": s.pros,
                    "cons": s.cons
                }
                for s in sources
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list data sources: {str(e)}")


@app.get("/datasources/{source_id}", tags=["Data Sources"])
def get_data_source(source_id: str):
    """
    Get detailed information about a specific data source.

    Example:
        GET /datasources/S2_MSI_L2A
    """
    if source_id not in DATA_SOURCES:
        raise HTTPException(
            status_code=404,
            detail=f"Data source '{source_id}' not found. Use GET /datasources to see available sources."
        )

    source = DATA_SOURCES[source_id]
    return {
        "id": source.id,
        "name": source.name,
        "description": source.description,
        "provider": source.provider,
        "category": source.category.value,
        "resolution_m": source.resolution_m,
        "revisit_days": source.revisit_days,
        "bands": source.bands,
        "use_cases": source.use_cases,
        "suitable_indices": source.suitable_indices,
        "keywords": source.keywords,
        "pros": source.pros,
        "cons": source.cons
    }


@app.get("/datasources/categories/list", tags=["Data Sources"])
def list_categories():
    """
    List all available data source categories.

    Example:
        GET /datasources/categories/list
    """
    return {
        "categories": [
            {"id": c.value, "name": c.value.replace("_", " ").title()}
            for c in DataCategory
        ]
    }


@app.post("/datasources/recommend", tags=["Data Sources"])
def recommend_data_sources(request: RecommendationRequest):
    """
    Get AI-powered data source recommendations based on your analysis description.

    Describe what you want to analyze and get intelligent suggestions for:
    - Best datasets for your use case
    - Relevant spectral indices
    - Processing tips

    Example:
        ```json
        {
            "analysis_description": "I want to monitor crop health and detect drought stress"
        }
        ```
    """
    try:
        analysis = request.analysis_description.lower()

        # Get matching sources from catalog
        matching_sources = get_sources_for_analysis(analysis)

        if not matching_sources:
            # Fallback to keyword search
            keywords = analysis.split()
            for word in keywords:
                if len(word) > 3:
                    matching_sources.extend(get_sources_by_keyword(word))
            matching_sources = list({s.id: s for s in matching_sources}.values())

        # Build recommendations with reasoning
        recommendations = []
        for source in matching_sources[:5]:  # Top 5 recommendations
            match_reasons = []
            for use_case in source.use_cases:
                if any(keyword in analysis for keyword in use_case.lower().split()):
                    match_reasons.append(use_case)

            recommendations.append({
                "id": source.id,
                "name": source.name,
                "description": source.description,
                "category": source.category.value,
                "resolution_m": source.resolution_m,
                "why_recommended": match_reasons[:3] if match_reasons else source.use_cases[:2],
                "suggested_indices": source.suitable_indices[:4],
                "pros": source.pros[:3],
                "cons": source.cons[:2],
                "provider": source.provider
            })

        # Add workflow suggestions based on analysis type
        workflow_tips = []
        if any(word in analysis for word in ['vegetation', 'crop', 'agriculture', 'plant', 'forest']):
            workflow_tips.append("Use NDVI for vegetation health assessment")
            workflow_tips.append("Consider time series analysis for phenology monitoring")
        if any(word in analysis for word in ['water', 'flood', 'lake', 'river', 'moisture']):
            workflow_tips.append("Use NDWI or MNDWI for water body detection")
            workflow_tips.append("Consider SAR data for all-weather monitoring")
        if any(word in analysis for word in ['urban', 'city', 'building', 'settlement']):
            workflow_tips.append("Use NDBI for built-up area mapping")
            workflow_tips.append("Consider nighttime lights for urbanization analysis")
        if any(word in analysis for word in ['fire', 'burn', 'thermal']):
            workflow_tips.append("Use NBR for burn severity assessment")
            workflow_tips.append("Consider MODIS or VIIRS for active fire detection")

        return {
            "analysis": request.analysis_description,
            "recommendation_count": len(recommendations),
            "recommendations": recommendations,
            "workflow_tips": workflow_tips if workflow_tips else ["Explore the recommended datasets based on your specific use case"],
            "note": "Use GET /datasources/{id} for full details on any dataset"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation failed: {str(e)}")


# Error handlers

@app.exception_handler(404)
def not_found_handler(request, exc):
    return JSONResponse(
        status_code=404,
        content={"detail": "Endpoint not found"}
    )


@app.exception_handler(500)
def internal_error_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
