# GeoDataHub QGIS Plugin

AI-powered satellite data search and download with natural language queries and smart dataset recommendations.

## Features

- **Natural Language Search**: Search for satellite data using plain English
  - "Sentinel-2 images of Paris from January 2024 with less than 20% cloud cover"
  - "Landsat 8 data for London from last month"

- **AI Dataset Recommendations**: Describe your analysis and get intelligent suggestions
  - Recommends best datasets for your use case
  - Suggests relevant spectral indices
  - Provides processing tips

- **Direct Download & Layer Loading**: Download data and add directly to QGIS

- **Multiple Data Sources**:
  - Copernicus (Sentinel-1, Sentinel-2)
  - USGS (Landsat)
  - AWS Earth Search
  - Planetary Computer

## Installation

### Method 1: Run Install Script

1. Double-click `install.bat` (Windows)
2. Open QGIS
3. Go to Plugins > Manage and Install Plugins
4. Enable "GeoDataHub"

### Method 2: Manual Installation

1. Copy the `geodatahub_qgis` folder to your QGIS plugins directory:
   - Windows: `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`
   - Linux: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`
   - Mac: `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

2. Also copy the `geodatahub` core package to the same location

3. Enable the plugin in QGIS Plugin Manager

### Dependencies

Install these in QGIS Python (OSGeo4W Shell on Windows):

```bash
pip install eodag requests
```

## Configuration

1. Create EODAG config file at `~/.config/eodag/eodag.yml`:

```yaml
cop_dataspace:
  priority: 1
  auth:
    credentials:
      username: YOUR_COPERNICUS_USERNAME
      password: YOUR_COPERNICUS_PASSWORD
```

2. Register at https://dataspace.copernicus.eu/ (free)

3. (Optional) Set `GROQ_API_KEY` environment variable for better NL parsing

## Usage

### Natural Language Search

1. Click the GeoDataHub icon in the toolbar
2. Enter a search query like: "Sentinel-2 images of New York from December 2024"
3. Click Search
4. Select results and click "Download & Add to Map"

### AI Recommendations

1. Click "AI Dataset Recommendations" in the GeoDataHub menu
2. Describe your analysis: "I want to monitor crop health"
3. Click "Get AI Recommendations"
4. Review suggestions and click "Search for This Data"

## Supported Datasets

| Code | Dataset | Resolution | Use Cases |
|------|---------|------------|-----------|
| S2_MSI_L2A | Sentinel-2 L2A | 10m | Vegetation, agriculture, land cover |
| S1_SAR_GRD | Sentinel-1 SAR | 10m | Flood mapping, all-weather monitoring |
| LANDSAT_C2L2 | Landsat 8/9 | 30m | Long-term monitoring, change detection |
| COP-DEM_GLO-30 | Copernicus DEM | 30m | Terrain analysis, elevation |

## Troubleshooting

**Plugin not appearing:**
- Make sure both `geodatahub_qgis` and `geodatahub` folders are in the plugins directory
- Check QGIS Python console for import errors

**Search fails:**
- Verify EODAG configuration and credentials
- Check internet connection
- Try with a smaller search area

**Download fails:**
- Ensure Copernicus credentials are correct
- Check disk space in output directory

## License

MIT License
