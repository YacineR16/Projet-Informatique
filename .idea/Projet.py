import Donnees_osm as d
import os

class Tuile :
    def __init__(self,lat,lon,zoom,path):
        self.lat=lat
        self.lon=lon
        self.zoom=zoom
        self.path=path


    def telecharger(self,lat,lon,zoom,path):
        x_tile, y_tile = latlon_to_tile(lat, lon, zoom)

        # Téléchargement de la tuile
        file_path = os.path.join("tiles/" + path)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        tile_path = d.download_osm_tile(zoom, x_tile, y_tile, file_path)
        print(f"Tile downloaded and saved to: {tile_path}")

class Carte:
    def __init__(self):
        self.tuiles={}

    def ajouter_tuile(self, tuile):
        self.tuiles[(tuile.x, tuile.y)] = tuile

class Drone:
    def __init__(self,x,y,h,vitesse):
        self.position=(x,y)
        self.altitude=h
        self.vitesse=vitesse

    def voler (self):



class AnalyseTuile:
    def __init__(self):


