# CLAUDE.md

## Geospatial Stack Preferences

- Prefer Python-based approaches
- Use existing packages instead of building solutions from scratch
- My preference for geospatial packages are below
  - Pandas for tabular data
  - GeoPandas for vector geospatial data
  - XArray ecosystem (rioxarray, xarray-spatial etc) for raster geospatial data
  - Scikit-learn for Machine Learning
  - GeoAI (geoai-py) for Deep Learning
- Web Apps
  - Streamlit for data driven apps
  - Leaflet for interactive mapping apps
  - Self contained HTML for small apps

## Other Preferences

- Write code that is simple to understand and explain
- Always install python packages in a conda environment. Never install anything in the base environment. Ask the user for confirmation on their preferred conda environment before installing anything.
- Do not use emojis