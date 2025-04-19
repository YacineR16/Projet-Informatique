import math
import os
import requests
from PIL import Image
"""tqdm permet d’afficher une barre de progression élégante et pratique dans la console"""
from tqdm import tqdm

# Coordonnées de référence (le centre du référentiel)
lat_ref = 48.385143
lon_ref = -4.493569

def metric_to_latlon(x_metric, y_metric, lat_ref, lon_ref):
    meters_per_deg_lat = 111320
    meters_per_deg_lon = 111320 * math.cos(math.radians(lat_ref))
    delta_lat = y_metric / meters_per_deg_lat
    delta_lon = x_metric / meters_per_deg_lon
    return lat_ref + delta_lat, lon_ref + delta_lon

def latlon_to_tile(lat, lon, zoom):
    x_tile = int((lon + 180.0) / 360.0 * (2 ** zoom))
    y_tile = int((1.0 - math.log(math.tan(math.radians(lat)) + 1.0 / math.cos(math.radians(lat))) / math.pi) / 2.0 * (2 ** zoom))
    return x_tile, y_tile

def tile_to_latlon(x_tile, y_tile, zoom):
    n = 2.0 ** zoom
    lon_deg = x_tile / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y_tile / n)))
    lat_deg = math.degrees(lat_rad)
    return lat_deg, lon_deg

def download_osm_tile(zoom, x, y, output_folder="tiles", retries=3):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
    headers = {
        'User-Agent': 'Mozilla/5.0 (compatible; OpenStreetMapDownloader/1.0; +https://yourwebsite.com)'
    }

    tile_path = os.path.join(output_folder, f"{zoom}_{x}_{y}.png")

    if os.path.exists(tile_path):
        return tile_path

    for attempt in range(retries):
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            with open(tile_path, 'wb') as file:
                file.write(response.content)
            return tile_path
        else:
            print(f"Failed to download tile: {url} (Attempt {attempt + 1} of {retries}) - Status code: {response.status_code}")

    raise Exception(f"Failed to download tile after {retries} attempts: {url}")

def telecharger_zone(lat_min, lat_max, lon_min, lon_max, zoom, dossier="tiles_zone"):
    x_min, y_max = latlon_to_tile(lat_min, lon_min, zoom)
    x_max, y_min = latlon_to_tile(lat_max, lon_max, zoom)

    dossier_complet = os.path.join(dossier, f"zoom_{zoom}")
    os.makedirs(dossier_complet, exist_ok=True)

    tuiles = [(x, y) for x in range(x_min, x_max + 1) for y in range(y_min, y_max + 1)]

    print(f"Tuiles à télécharger : {len(tuiles)}")
    for x, y in tqdm(tuiles, desc="Téléchargement"):
        try:
            download_osm_tile(zoom, x, y, dossier_complet)
        except Exception as e:
            print(f"Erreur pour la tuile {x}, {y} : {e}")

    return x_min, x_max, y_min, y_max, dossier_complet

def assembler_image(x_min, x_max, y_min, y_max, zoom, dossier):
    largeur = (x_max - x_min + 1) * 256
    hauteur = (y_max - y_min + 1) * 256
    image_finale = Image.new("RGB", (largeur, hauteur))

    for x in range(x_min, x_max + 1):
        for y in range(y_min, y_max + 1):
            try:
                nom_fichier = f"{zoom}_{x}_{y}.png"
                chemin = os.path.join(dossier, nom_fichier)
                tuile = Image.open(chemin)
                dx = (x - x_min) * 256
                dy = (y - y_min) * 256
                image_finale.paste(tuile, (dx, dy))
            except Exception as e:
                print(f"Erreur collage {x},{y} : {e}")

    image_finale.save(os.path.join(dossier, f"carte_assemblee_zoom{zoom}.png"))
    print(f"Image assemblée enregistrée : carte_assemblee_zoom{zoom}.png")

if __name__ == "__main__":
    # Zone test autour de Brest (5x5 tuiles environ)
    lat_min = 48.378
    lat_max = 48.388
    lon_min = -4.51
    lon_max = -4.49
    zoom = 17

    x_min, x_max, y_min, y_max, dossier = telecharger_zone(lat_min, lat_max, lon_min, lon_max, zoom, dossier="tiles_brest")
    assembler_image(x_min, x_max, y_min, y_max, zoom, dossier)

