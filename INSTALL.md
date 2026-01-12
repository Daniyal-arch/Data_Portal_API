# Installation Guide

This guide will help you install and configure GeoDataHub.

## Prerequisites

- Python 3.8 or higher
- pip package manager
- Git (optional, for cloning the repository)

## Installation Methods

### Method 1: Install from Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/yourusername/geodatahub.git
cd geodatahub

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Linux/Mac:
source venv/bin/activate

# Install in development mode
pip install -e .

# Install API dependencies (optional)
pip install -e .[api]
```

### Method 2: Install from PyPI (when published)

```bash
# Basic installation
pip install geodatahub

# With API support
pip install geodatahub[api]

# Full installation with all extras
pip install geodatahub[api,cli,dev]
```

## Configuration

### 1. Configure Data Providers (EODAG)

EODAG is the backend that connects to various data providers. You need to configure at least one provider.

```bash
# Create config directory
mkdir -p ~/.config/eodag

# Copy example configuration
cp config/eodag.yml.example ~/.config/eodag/eodag.yml

# Edit the configuration file
nano ~/.config/eodag/eodag.yml
```

**Required: Add your credentials for at least one provider**

#### Recommended Provider: Copernicus Data Space

1. Register at: https://dataspace.copernicus.eu/
2. Add credentials to `~/.config/eodag/eodag.yml`:

```yaml
cop_dataspace:
  priority: 1
  credentials:
    username: your_username
    password: your_password
```

#### Alternative: USGS (for Landsat)

1. Register at: https://ers.cr.usgs.gov/register
2. Add credentials to `~/.config/eodag/eodag.yml`:

```yaml
usgs:
  priority: 2
  credentials:
    username: your_username
    password: your_password
```

### 2. Configure Natural Language Processing (Optional but Recommended)

GeoDataHub works without an LLM provider (using regex fallback), but works much better with one.

Choose one option:

#### Option A: Groq (Recommended - Cloud, Free Tier)

1. Get API key from: https://console.groq.com/
2. Set environment variable:

```bash
export GROQ_API_KEY="your_api_key_here"
```

Or add to `.env` file:
```bash
cp .env.example .env
# Edit .env and add your GROQ_API_KEY
```

#### Option B: Ollama (Recommended - Local, Private)

1. Install Ollama from: https://ollama.ai/
2. Download a model:

```bash
ollama pull llama3
# or
ollama pull mistral
```

3. Ollama will be automatically detected when running

#### Option C: OpenRouter (Alternative - Cloud)

1. Get API key from: https://openrouter.ai/
2. Set environment variable:

```bash
export OPENROUTER_API_KEY="your_api_key_here"
```

#### Option D: No LLM (Regex Only)

No configuration needed. The parser will use regex-based extraction (less accurate but works offline).

## Verification

### Test the Installation

```bash
# Test CLI
geodatahub --help

# Test Python import
python -c "from geodatahub import GeoDataHub; print('Success!')"

# Test with example
python examples/basic_usage.py
```

### Test the API (if installed with [api])

```bash
# Start the API server
uvicorn geodatahub_api.main:app --reload

# In another terminal, test the API
curl http://localhost:8000/
curl "http://localhost:8000/search/nl?q=Sentinel-2%20images%20of%20Paris"

# Or run the API client example
python examples/api_client.py
```

## Troubleshooting

### Problem: "eodag not found"

```bash
pip install eodag>=2.9.0
```

### Problem: "No providers configured"

Make sure you have:
1. Created `~/.config/eodag/eodag.yml`
2. Added credentials for at least one provider
3. Registered an account with that provider

### Problem: "Search returns no results"

Check:
1. Provider credentials are correct
2. The product type is available from your configured provider
3. Your search area and date range have available data
4. Cloud cover threshold isn't too restrictive

### Problem: "LLM parsing failed"

This is normal if you haven't configured an LLM provider. The parser will automatically fall back to regex-based parsing. To improve accuracy:
1. Configure Groq (fastest, free)
2. Or install Ollama (local, private)
3. Or use explicit parameters instead of natural language

### Problem: "Download fails"

Common issues:
1. Provider authentication expired - re-enter credentials
2. Product is offline - try a different result or provider
3. Network issues - check your connection
4. Disk space - ensure you have enough storage

## Next Steps

- Read [README.md](README.md) for usage examples
- Check [examples/](examples/) directory for sample code
- Configure additional providers in EODAG config
- Set up LLM provider for better natural language understanding

## Getting Help

- Check the [EODAG documentation](https://eodag.readthedocs.io/)
- Open an issue on GitHub
- Check provider-specific documentation for authentication issues

## Uninstallation

```bash
# If installed with pip
pip uninstall geodatahub

# Remove configuration files (optional)
rm -rf ~/.config/eodag/
rm -rf ~/.eodag/
```
