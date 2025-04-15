import math
import os
import requests
import argparse
from PIL import Image

# Coordonnées de référence (le centre du référentiel)
lat_ref = 48.385143
lon_ref = -4.493569


def metric_to_latlon(x_metric, y_metric, lat_ref, lon_ref):
    """Convertit des coordonnées métriques (x, y) en latitude et longitude, centrées sur un point de référence."""
    # Facteurs de conversion métrique vers degrés de latitude et longitude
    meters_per_deg_lat = 111320  # Distance approximative en mètres pour 1° de latitude
    meters_per_deg_lon = 111320 * math.cos(
        math.radians(lat_ref))  # Distance en mètres pour 1° de longitude à cette latitude

    # Calcul des décalages
    delta_lat = y_metric / meters_per_deg_lat  # Déplacement en latitude
    delta_lon = x_metric / meters_per_deg_lon  # Déplacement en longitude

    # Nouvelles coordonnées
    return lat_ref + delta_lat, lon_ref + delta_lon


def latlon_to_tile(lat, lon, zoom):
    """Convertit des coordonnées géographiques en coordonnées de tuiles."""
    x_tile = int((lon + 180.0) / 360.0 * (2 ** zoom))
    y_tile = int(
        (1.0 - math.log(math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))) / math.pi) / 2.0 * (2 ** zoom))
    return x_tile, y_tile


def download_osm_tile(zoom, x, y, output_folder="tiles", retries=3):
    """Télécharge une tuile OSM pour un niveau de zoom et des coordonnées X et Y donnés."""
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; OpenStreetMapDownloader/1.0; +https://yourwebsite.com)'
    }

    for attempt in range(retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            tile_path = os.path.join(output_folder, f"{zoom}_{x}_{y}.png")
            with open(tile_path, 'wb') as file:
                file.write(response.content)
            print(f"Tile downloaded successfully: {tile_path}")
            return tile_path
        else:
            print(
                f"Failed to download tile: {url} (Attempt {attempt + 1} of {retries}) - Status code: {response.status_code}")

    raise Exception(f"Failed to download tile after {retries} attempts: {url}")


if __name__ == "__main__":
    """parser = argparse.ArgumentParser(description="Download OSM tile based on x, y, and zoom parameters.")
    parser.add_argument("x", type=int, help="The x coordinate")
    parser.add_argument("y", type=int, help="The y coordinate")
    parser.add_argument("zoom", type=int, help="The zoom level")
    parser.add_argument("path", type=str, help="The path to save the tile")

    args = parser.parse_args()

    x_metric = args.x
    y_metric = args.y
    zoom = args.zoom
    path = args.path"""

    # Exemple de test direct dans le code
    lat,lon = 48.378947,-4.501734
    zoom = 17
    path = "brest"

    try:

        # Conversion des coordonnées géographiques en coordonnées de tuiles
        x_tile, y_tile = latlon_to_tile(lat, lon, zoom)

        # Téléchargement de la tuile
        file_path = os.path.join("tiles/" + path)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        tile_path = download_osm_tile(zoom, x_tile, y_tile, file_path)
        print(f"Tile downloaded and saved to: {tile_path}")
    except Exception as e:
        print(f"An error occurred: {e}")
