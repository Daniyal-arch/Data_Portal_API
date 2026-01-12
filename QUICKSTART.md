# Quick Start Guide

Get started with GeoDataHub in 5 minutes!

## 1. Install

```bash
# Clone and install
git clone https://github.com/yourusername/geodatahub.git
cd geodatahub
pip install -e .
```

## 2. Configure a Data Provider

You need credentials from at least one data provider. We recommend Copernicus Data Space (free):

1. Register at: https://dataspace.copernicus.eu/
2. Create config directory and file:

```bash
mkdir -p ~/.config/eodag
cat > ~/.config/eodag/eodag.yml << EOF
cop_dataspace:
  priority: 1
  credentials:
    username: YOUR_USERNAME
    password: YOUR_PASSWORD
EOF
```

Replace `YOUR_USERNAME` and `YOUR_PASSWORD` with your actual credentials.

## 3. (Optional) Configure LLM for Better Parsing

For better natural language understanding, set up Groq (free):

1. Get API key from: https://console.groq.com/
2. Set environment variable:

```bash
export GROQ_API_KEY="your_api_key_here"
```

**Or** use local Ollama (more private):

```bash
# Install Ollama from https://ollama.ai/
ollama pull llama3
```

**Note:** GeoDataHub works without an LLM (using regex), but works better with one.

## 4. Try It Out!

### Python API

```python
from geodatahub import search_natural_language, GeoDataHub

# Natural language search
results = search_natural_language(
    "Sentinel-2 images of Paris from last month with less than 20% cloud cover"
)

print(f"Found {len(results)} images")
for result in results[:3]:
    print(f"- {result.title} ({result.datetime[:10]}) - {result.cloud_cover}% clouds")

# Download
hub = GeoDataHub()
paths = hub.download_all(results[:1], "./data")  # Download first result
print(f"Downloaded to: {paths}")
```

### Command Line

```bash
# Search
geodatahub search "Sentinel-2 images of London from January 2024"

# Download
geodatahub download "Sentinel-2 images of London from last week" -o ./data

# List available products
geodatahub list products

# List providers
geodatahub list providers
```

### REST API

Start the server:

```bash
pip install -e .[api]
uvicorn geodatahub_api.main:app --reload
```

Query the API:

```bash
# Natural language search
curl "http://localhost:8000/search/nl?q=Sentinel-2%20images%20of%20Paris"

# Or use the web interface
# Open http://localhost:8000/docs in your browser
```

## Examples of Natural Language Queries

- "Sentinel-2 images of Paris from January 2024 with less than 20% cloud cover"
- "Landsat 8 data for New York from last month"
- "SAR data for Tokyo from last week"
- "DEM data for Mount Everest"
- "Land cover data for Amazon rainforest"
- "Sentinel-2 images of London with clear skies"

## Next Steps

- Check out [examples/basic_usage.py](examples/basic_usage.py) for more examples
- Read the full [README.md](README.md) for detailed documentation
- See [INSTALL.md](INSTALL.md) for advanced configuration
- Configure additional providers in `~/.config/eodag/eodag.yml`

## Troubleshooting

**Problem:** "Search returns no results"
- Check your provider credentials
- Verify the location and date range have available data
- Try a broader search (higher cloud cover, wider date range)

**Problem:** "Authentication failed"
- Verify your credentials in `~/.config/eodag/eodag.yml`
- Make sure you registered with the provider
- Some providers require email verification

**Problem:** "Download fails"
- Some products may be offline temporarily
- Check your network connection
- Ensure you have enough disk space

## Support

- GitHub Issues: https://github.com/yourusername/geodatahub/issues
- EODAG Docs: https://eodag.readthedocs.io/
- Provider-specific help: Check your provider's documentation

Happy data hunting! 🛰️
