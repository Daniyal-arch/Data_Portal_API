# Usage Guide

Comprehensive guide to using GeoDataHub.

## Table of Contents

1. [Python API](#python-api)
2. [Command Line Interface](#command-line-interface)
3. [REST API](#rest-api)
4. [Natural Language Queries](#natural-language-queries)
5. [Advanced Usage](#advanced-usage)

---

## Python API

### Basic Search

```python
from geodatahub import GeoDataHub, DataRequest

hub = GeoDataHub()

# Create a request
request = DataRequest(
    product="S2_MSI_L2A",
    bbox=(2.25, 48.81, 2.42, 48.90),  # Paris
    start_date="2024-01-01",
    end_date="2024-01-31",
    cloud_cover_max=20,
    limit=10
)

# Search
results = hub.search(request)

# Display results
for result in results:
    print(f"{result.title} - {result.datetime[:10]} - {result.cloud_cover}% clouds")
```

### Natural Language Search

```python
from geodatahub import search_natural_language

# Simple one-liner
results = search_natural_language(
    "Sentinel-2 images of Paris from January 2024 with less than 20% cloud cover"
)

# With additional parameters
results = search_natural_language(
    "Sentinel-2 images of London from last month",
    limit=5,
    cloud_cover_max=10  # Override parsed value
)
```

### Using the Parser Directly

```python
from geodatahub import NLParser, GeoDataHub

parser = NLParser()
hub = GeoDataHub()

# Parse query
request = parser.parse("Sentinel-2 images of Paris from January 2024")

# Inspect parsed parameters
print(f"Product: {request.product}")
print(f"Location: {request.location_name}")
print(f"BBox: {request.bbox}")
print(f"Dates: {request.start_date} to {request.end_date}")

# Search with parsed request
results = hub.search(request)
```

### Downloading Data

```python
from geodatahub import GeoDataHub

hub = GeoDataHub()

# Search first
results = hub.search(request)

# Download single result
if results:
    path = hub.download(results[0], "./data")
    print(f"Downloaded to: {path}")

# Download multiple results
paths = hub.download_all(results[:5], "./data")
print(f"Downloaded {len(paths)} files")
```

### Different Data Types

```python
from geodatahub import DataRequest, DataType

# Sentinel-1 SAR
request = DataRequest(
    product="S1_SAR_GRD",
    data_type=DataType.SAR,
    location_name="Tokyo",
    start_date="2024-01-01",
    end_date="2024-01-31"
)

# DEM
request = DataRequest(
    product="COP-DEM_GLO-30",
    data_type=DataType.DEM,
    bbox=(86.9, 27.9, 87.0, 28.0)  # Mount Everest
)

# Land Cover
request = DataRequest(
    product="ESA_WORLDCOVER",
    data_type=DataType.LAND_COVER,
    location_name="Amazon rainforest"
)
```

### Listing Resources

```python
from geodatahub import GeoDataHub

hub = GeoDataHub()

# List all providers
providers = hub.list_providers()
print(providers)

# List all products
products = hub.list_products()
for product in products:
    print(f"{product['ID']}: {product.get('title', 'N/A')}")

# List products from specific provider
products = hub.list_products(provider="cop_dataspace")
```

---

## Command Line Interface

### Search

```bash
# Natural language
geodatahub search "Sentinel-2 images of Paris from January 2024"

# With explicit parameters
geodatahub search --product S2_MSI_L2A --location "London" \
    --start 2024-01-01 --end 2024-01-31 --cloud 20

# Using bounding box
geodatahub search --product S2_MSI_L2A \
    --bbox 2.25 48.81 2.42 48.90 \
    --start 2024-01-01 --end 2024-01-31

# Save results to file
geodatahub search "Sentinel-2 images of Paris" --output results.json

# Limit results
geodatahub search "Sentinel-2 images of London" --limit 5
```

### Download

```bash
# Download from natural language query
geodatahub download "Sentinel-2 images of Paris from last week" -o ./data

# With limit
geodatahub download "Sentinel-2 images of London" -o ./data --limit 3

# Skip confirmation
geodatahub download "Sentinel-2 images of Paris" -o ./data --yes
```

### List Resources

```bash
# List all providers
geodatahub list providers

# List all products
geodatahub list products

# List products from specific provider
geodatahub list products --provider cop_dataspace
```

---

## REST API

### Starting the Server

```bash
# Development mode
uvicorn geodatahub_api.main:app --reload

# Production mode
uvicorn geodatahub_api.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Endpoints

#### GET /

API information

```bash
curl http://localhost:8000/
```

#### GET /health

Health check

```bash
curl http://localhost:8000/health
```

#### POST /search

Search with JSON body

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Sentinel-2 images of Paris from January 2024",
    "limit": 5
  }'
```

Or with explicit parameters:

```bash
curl -X POST http://localhost:8000/search \
  -H "Content-Type: application/json" \
  -d '{
    "product": "S2_MSI_L2A",
    "location": "London",
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "cloud_cover_max": 20,
    "limit": 10
  }'
```

#### GET /search/nl

Search with natural language (GET request)

```bash
curl "http://localhost:8000/search/nl?q=Sentinel-2%20images%20of%20Paris&limit=5"
```

#### GET /products

List products

```bash
# All products
curl http://localhost:8000/products

# Filter by provider
curl "http://localhost:8000/products?provider=cop_dataspace"
```

#### GET /products/{product_id}

Get product information

```bash
curl http://localhost:8000/products/S2_MSI_L2A
```

#### GET /providers

List providers

```bash
curl http://localhost:8000/providers
```

#### GET /data-types

List available data types

```bash
curl http://localhost:8000/data-types
```

### Interactive Documentation

Open in browser: http://localhost:8000/docs

---

## Natural Language Queries

### Supported Patterns

#### Product Types

- "Sentinel-2", "Sentinel 2", "S2" → Sentinel-2
- "Sentinel-1", "Sentinel 1", "S1", "SAR" → Sentinel-1 SAR
- "Landsat 8", "Landsat-8", "L8" → Landsat 8
- "Landsat 9", "Landsat-9", "L9" → Landsat 9
- "DEM", "elevation", "SRTM" → Digital Elevation Model
- "land cover", "LULC" → Land Cover

#### Locations

- "of Paris", "for London", "in New York"
- "over Tokyo", "around Berlin", "near Rome"

#### Dates

- "from January 2024" → Month and year
- "from last week" → Past 7 days
- "from last month" → Past 30 days
- "from last 15 days" → Past 15 days
- "yesterday" → Yesterday's date
- "from 2024-01-01 to 2024-01-31" → Explicit date range

#### Cloud Cover

- "with less than 20% cloud cover" → Max 20%
- "with clear skies" → Max 10%
- "mostly clear" → Max 20%

### Example Queries

```
"Sentinel-2 images of Paris from January 2024 with less than 20% cloud cover"
"Landsat 8 data for New York from last month"
"Sentinel-1 SAR data for Tokyo from last week"
"DEM data for Mount Everest"
"Land cover data for Amazon rainforest"
"Sentinel-2 images of London with clear skies from 2024-01-01 to 2024-01-31"
"Get Sentinel-2 data for California from January 2024"
"Show me SAR images of Tokyo from last month"
```

---

## Advanced Usage

### Custom LLM Provider

```python
from geodatahub.nlp.parser import NLParser

# Use specific LLM provider
parser = NLParser(llm_provider="groq")  # or "ollama", "openrouter"

# Use regex only (no LLM)
parser = NLParser(llm_provider="regex")
```

### Custom Geocoder

```python
from geodatahub.nlp.geocoder import Geocoder

geocoder = Geocoder()

# Geocode location
result = geocoder.geocode("Paris, France")
print(result['bbox'])  # Bounding box
print(result['geometry'])  # GeoJSON geometry

# Reverse geocode
result = geocoder.reverse_geocode(48.8566, 2.3522)
print(result['display_name'])  # Address
```

### Working with Results

```python
# Access result properties
for result in results:
    print(f"ID: {result.id}")
    print(f"Title: {result.title}")
    print(f"Provider: {result.provider}")
    print(f"Product Type: {result.product_type}")
    print(f"Date: {result.date}")
    print(f"Year: {result.year}")
    print(f"Cloud Cover: {result.cloud_cover}%")
    print(f"BBox: {result.bbox}")
    print(f"Thumbnail: {result.thumbnail_url}")
    print(f"Size: {result.size_mb} MB")

# Convert to dictionary
result_dict = result.to_dict()

# Access metadata
print(result.metadata)
```

### Custom EODAG Configuration

```python
from geodatahub import GeoDataHub

# Use custom config file
hub = GeoDataHub(config_path="./my_eodag_config.yml")
```

### Filtering Results

```python
# Filter by cloud cover
low_cloud_results = [r for r in results if r.cloud_cover < 10]

# Filter by date
from datetime import datetime
recent_results = [r for r in results if r.year >= 2024]

# Sort by cloud cover
sorted_results = sorted(results, key=lambda r: r.cloud_cover or 100)
```

### Error Handling

```python
from geodatahub import GeoDataHub, NLParser

try:
    hub = GeoDataHub()
    parser = NLParser()

    request = parser.parse("Sentinel-2 images of Paris")
    results = hub.search(request)

    if not results:
        print("No results found")
    else:
        paths = hub.download_all(results[:1], "./data")

except Exception as e:
    print(f"Error: {e}")
```

### Integration with Other Tools

#### Pandas

```python
import pandas as pd

# Convert results to DataFrame
data = [r.to_dict() for r in results]
df = pd.DataFrame(data)
df.to_csv("search_results.csv", index=False)
```

#### GeoPandas

```python
import geopandas as gpd
from shapely.geometry import shape

# Create GeoDataFrame
geometries = [shape(r.geometry) for r in results]
gdf = gpd.GeoDataFrame(
    [r.to_dict() for r in results],
    geometry=geometries,
    crs="EPSG:4326"
)
gdf.to_file("search_results.geojson", driver="GeoJSON")
```

---

## Tips and Best Practices

1. **Start Broad**: Use relaxed parameters initially, then refine
2. **Check Cloud Cover**: For optical data, cloud cover is crucial
3. **Provider Authentication**: Ensure providers are properly configured
4. **Disk Space**: Check available space before downloading
5. **Rate Limiting**: Respect provider rate limits
6. **Error Handling**: Always handle potential errors
7. **Test First**: Search before downloading to verify results
8. **Use Limits**: Start with small limits when testing

## Troubleshooting

See [INSTALL.md](INSTALL.md#troubleshooting) for common issues and solutions.
