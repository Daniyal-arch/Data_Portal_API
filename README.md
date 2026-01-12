# GeoDataHub

A unified Python interface for searching and downloading geospatial data from multiple providers using natural language queries.

## Features

- **Natural Language Search**: Query geospatial data using plain English
- **Multiple Data Sources**: Sentinel-2, Sentinel-1, Landsat, DEM, Land Cover, and more
- **Flexible Interfaces**: CLI, Python API, REST API, and QGIS plugin
- **Smart Parsing**: LLM-powered query understanding with regex fallback
- **Unified Output**: Consistent data model across all providers

## Installation

```bash
pip install geodatahub
```

For API service:
```bash
pip install geodatahub[api]
```

## Quick Start

### Python API

```python
from geodatahub import search_natural_language

# Natural language search
results = search_natural_language(
    "Sentinel-2 images of Paris from last month with less than 20% cloud cover"
)

# Download results
from geodatahub import GeoDataHub
hub = GeoDataHub()
hub.download_all(results, output_dir="./data")
```

### CLI

```bash
# Search using natural language
geodatahub search "Sentinel-2 images of London from January 2024"

# Download data
geodatahub download "Sentinel-2 images of London from January 2024" -o ./data

# List available products
geodatahub list products

# List available providers
geodatahub list providers
```

### REST API

```bash
# Start the API server
uvicorn geodatahub_api.main:app --reload

# Query the API
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "Sentinel-2 images of Paris from last week"}'
```

## Natural Language Examples

The parser understands various natural language patterns:

- "Sentinel-2 images of Paris from last month with less than 20% cloud cover"
- "Get DEM data for Mount Everest"
- "Landsat 8 images of California from January 2024"
- "SAR data for Tokyo from last week"
- "Land cover data for Amazon rainforest"

## Configuration

### LLM Providers

GeoDataHub supports multiple LLM providers for natural language parsing:

1. **Groq** (recommended for cloud): Fast and free tier available
   ```bash
   export GROQ_API_KEY="your_api_key"
   ```

2. **Ollama** (recommended for local): Privacy-focused local processing
   ```bash
   # Install and run Ollama with llama3 or mistral
   ollama run llama3
   ```

3. **OpenRouter**: Access to various models including free options
   ```bash
   export OPENROUTER_API_KEY="your_api_key"
   ```

4. **Regex Fallback**: No API key required, works offline

### Data Providers

Configure EODAG providers in `~/.config/eodag/eodag.yml`:

```yaml
providers:
  cop_dataspace:
    priority: 1
    credentials:
      username: your_username
      password: your_password

  usgs:
    priority: 2
    credentials:
      username: your_username
      password: your_password
```

## Supported Data Types

- **Optical**: Sentinel-2, Landsat 8/9, MODIS
- **SAR**: Sentinel-1
- **DEM**: Copernicus DEM, SRTM
- **Land Cover**: ESA WorldCover, CORINE
- **Climate**: ERA5, MODIS
- **Population**: GHS-POP
- **Air Quality**: Sentinel-5P

## Architecture

```
geodatahub/
├── models/          # Core data models (DataRequest, SearchResult)
├── nlp/            # Natural language processing (parser, geocoder, LLM clients)
├── core/           # EODAG integration and download logic
└── __init__.py     # Main API

geodatahub_api/     # FastAPI REST service
cli.py              # Command-line interface
```

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/geodatahub.git
cd geodatahub

# Install in development mode
pip install -e .[dev]

# Run tests
pytest

# Format code
black geodatahub/
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Citation

If you use GeoDataHub in your research, please cite:

```bibtex
@software{geodatahub,
  title = {GeoDataHub: Unified Geospatial Data Access},
  author = {GeoDataHub Team},
  year = {2024},
  url = {https://github.com/yourusername/geodatahub}
}
```
