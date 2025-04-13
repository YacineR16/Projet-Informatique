import xmltodict
from mpl_toolkits.axes_grid1.inset_locator import zoomed_inset_axes
import Donnees_osm as d
import os
import Code Eleanore

class Tuile :
    def __init__(self,lat,lon,zoom,path):
        self.lat=lat
        self.lon=lon
        self.zoom=zoom
        self.path=path

    def telecharger(self,lat,lon,zoom,path):
        x_tile, y_tile = d.latlon_to_tile(lat, lon, zoom)

        # Téléchargement de la tuile
        file_path = os.path.join("tiles/" + path)
        if not os.path.exists(file_path):
            os.makedirs(file_path)
        tile_path = d.download_osm_tile(zoom, x_tile, y_tile, file_path)
        print(f"Tile downloaded and saved to: {tile_path}")

class Carte:
    def __init__(self,zoom):
        self.couleur=[0,0,0]
        self.zoom=zoom

    def ajouter_tuile(self, tuile):
        self.tuile[(tuile.x, tuile.y)] = tuile

    #def quadrillage(self,zoom,path):


class Drone:
    def __init__(self,x,y,h,vitesse):
        self.position=(x,y)
        self.altitude=h
        self.vit=vitesse

    def VG(self,x,y):
        self.new_position=(x+1,y)

    def VD(self,x,y):
        self.new_position=(x-1,y)

    def VH(self,x,y):
        self.new_position=(x,y+1)

    def VB(self,x,y):
        self.new_position=(x,y-1)

class AnalyseTuile:
    def __init__(self):
        self.tuiles=None

    def couleur_moyenne(self,tuile):
        self.Rmoy,self.Gmoy,self.Bmoy=0,0,0
        self.pixel=tuile.pixel
        for i in range(len(tuile)):
            for j in range(len(tuile)):
                self.Rmoy+=tuile.pixel[0]
                self.Gmoy+=tuile.pixel[1]
                self.Bmoy+=tuile.pixel[2]
        self.couleur_moy=[self.Rmoy/len(tuile),self.Gmoy/len(tuile),self.Bmoy/len(tuile)]

    def couleur_dominante(self,tuile):
        maritime,terrestre=0,0
        for i in range(len(tuile)):
            for j in range(len(tuile)):
                if tuile.pixel[0]<100 and tuile.pixel[1]<100 and tuile.pixel[2]>200:
                    maritime+=1
                else:
                    terrestre+=1
        if maritime>terrestre:
            return "L'eau est dominante sur la tuile"
        else:
            return "La terre est dominante sur la tuile"

    def point_dinteret(self,tuile,doc_OSM):
        dico=xmltodict.parse(doc_OSM)
        Ref=dico[ref]
        if Ref not in tuile:
            return None
        else:
            print(f"Il y a un point d'interêt qui correspond à {Ref}")
            