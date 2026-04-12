User Story: As a Geographic Data Analyst, I want the state and municipal boundaries of Brazil to be automatically loaded into a geospatial database via Airflow, so that I can perform spatial queries and cross-reference these boundaries with other information layers (such as preservation areas or rivers).



1. Database Structure

At least two tables must be created: state_boundaries and municipal_boundaries.

The tables must contain a column of type GEOMETRY (or GEOGRAPHY) to store the polygons.

Basic attribute columns from the .dbf must be included (e.g., ibge_code, municipality_name, state_abbr).

The table must have a spatial index (GIST) to ensure performance in geographic searches.

2. Orchestration with Apache Airflow

The DAG must download the .zip file directly from the IBGE FTP.

The DAG must be able to unzip the file and read the Shapefile dataset.

The load must be idempotent (if run twice, it must not duplicate data; it should clear the table or perform an upsert).

Database and FTP credentials must be managed via Airflow Connections.

3. Integration and Docker

The environment must be spun up via docker-compose, containing the services: postgres (with PostGIS), airflow-webserver, and airflow-scheduler.

There must be a mapped volume to persist the database data, even if the container is restarted.



I think it's worth changing the name of airflow to something that reminds us it's a geographic database (bdg)
I think the ports should be configured in the .env
It might be better to change the name of some keys in the .env to avoid confusion

Tip for opening the maps
https://mapshaper.org/



```bash
docker-compose down -v
docker-compose up --build
docker-compose up --build -d
docker-compose logs -f  # show logs

docker exec -it geoavia_airflow bash # open a bash terminal inside docker container
```