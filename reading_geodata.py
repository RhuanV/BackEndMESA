"""
Script to read and inspect a Shapefile using GeoPandas.
This helps in understanding the attributes and coordinate system before loading into the database.
"""
import geopandas as gpd

def main() -> None:
    # Path to the .shp file (adjust to the actual name of the downloaded file)
    file_path = "data/BR_UF_2025/BR_UF_2025.shp"

    # GeoPandas reads the .shp and automatically pulls the .dbf and .prj files alongside it
    gdf = gpd.read_file(file_path)

    # View the first 5 rows of the table (the .dbf content)
    print("--- Attribute Table ---")
    print(gdf.head())

    # View available column names
    print("\n--- Available Columns ---")
    print(gdf.columns)

    # View the Coordinate Reference System (CRS) from the .prj file
    print("\n--- Coordinate Reference System (CRS) ---")
    print(gdf.crs)

if __name__ == "__main__":
    main()
