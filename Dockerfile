# Uses a lightweight Python image
FROM python:3.12-slim

# Defines the working directory inside the container
WORKDIR /app

# Installs system dependencies:
#   libpq-dev/gcc: psycopg2
#   libgdal-dev: geopandas/fiona (HU-31 shapefile parsing)
#   libproj-dev: pyproj (reprojection to SRID 4674)
#   libgeos-dev: shapely
RUN apt-get update && apt-get install -y \
        libpq-dev gcc \
        libgdal-dev libproj-dev libgeos-dev \
    && rm -rf /var/lib/apt/lists/*

# Copies only the requirements first (optimizes Docker cache)
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copies the backend source code
COPY backend/src ./src

# Ensures Python can find the src package
ENV PYTHONPATH=/app/src

# Exposes the port used by FastAPI
EXPOSE 8000

# Command to run the application
CMD ["python", "-m", "uvicorn", "geoavia_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]