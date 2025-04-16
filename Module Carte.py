"""permet de voir le coloriage en direct de la carte en fonction du déplacement du drone"""
import pygame
import numpy as np
import matplotlib.pyplot as plt
import osmnx as ox

import Donnees_osm
from Donnees_osm import latlon_to_tile

"""PIL = bibliothèque Python pour ouvrir, modifier, afficher et enregistrer des images"""
from PIL import Image
import SQL
import Donnees_osm

taille_tuile=256 #pixels

"""class qui délimite la zone à cartographiée en récupérant l'image sur OSM qui retourne une image.png 
= représente la mission complète du drone
peut être à renommer en Mission"""
class Environnement:
    def __init__(self, lat_min, lon_min, lat_max, lon_max, zoom,altitude,mode_vol):
        self.lat_min = lat_min
        self.lon_min = lon_min
        self.lat_max = lat_max
        self.lon_max = lon_max
        self.altitude = altitude
        self.mode_vol=mode_vol
        self.zoom = zoom  # même si non utilisé directement ici
        self.image_path = "zone_osm.png"

    def OSM(self):
        # Créer un polygone (boîte englobante)
        north = self.lat_max
        south = self.lat_min
        east = self.lon_max
        west = self.lon_min

        # Télécharger la carte comme graphe
        G = ox.graph_from_bbox(north, south, east, west, network_type='all')

        # Obtenir l’image avec le fond de carte
        fig, ax = ox.plot_graph(ox.project_graph(G), show=False, close=True)

        # Sauvegarder l'image
        fig.savefig(self.image_path, dpi=300, bbox_inches='tight')
        plt.close(fig)

        return self.image_path


    """donne le numéro de toutes les tuiles de la zone à cartographier
    utile pour retrouver le nom de l'image enregistre et pour le tableau SQL"""
    def tuiles_zone(self,lat_min, lat_max, lon_min, lon_max, zoom):
        x_min, y_max = Donnees_osm.latlon_to_tile(lat_min, lon_min, zoom)
        x_max, y_min = Donnees_osm.latlon_to_tile(lat_max, lon_max, zoom)

        tuiles = []
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                tuiles.append((x, y, zoom))  # ou f"{zoom}_{x}_{y}" pour un ID unique
        return tuiles

    """création du tableau SQL"""
    def enregistrer_mission(self):
        SQL.tableau_SQL()
        tiles_included= self.tuiles_zone(self.lat_min,self.lat_max,self.lon_min,self.lon_max,self.zoom)
        nb_tuile = len(tiles_included)
        SQL.inserer_donnees_carte(self.lat_min, self.lat_max, self.lon_min, self.lon_max, self.zoom, self.altitude, self.mode_vol, nb_tuile, tiles_included)


class Carte:
    def __init__(self, nom_image):
        """nom_image est une chaîne de caractères"""
        self.nom_image = nom_image
        self.image = self.image_np(nom_image)
        self.carte_blanche = self.initialisation_carte()

    def image_np(self, nom_image):
        """Retourne un tableau de pixels RGB à partir de l'image"""
        img = Image.open(nom_image).convert("RGB")
        return np.array(img)

    def initialisation_carte(self):
        """Crée une carte blanche de même taille que l'image de référence"""
        size = self.image.shape
        return np.ones((size[0], size[1], 3), dtype=np.uint8) * 255

    def color_carte(self, x, y, altitude):
        """mise à jour de la carte blanche"""
        analyseur = Analyseur(x, y, altitude)
        taille = analyseur.taille_patch(altitude)
        demi = taille // 2
        couleur = analyseur.moyenne_RGB(altitude, x, y, self.image)
        self.carte_blanche[y - demi:y + demi + 1, x - demi:x + demi + 1] = couleur




"""Seul 3 altitudes pourront être choisi : basse, moyenne,  qui définiront les tailles des patch analysés"""
""" basse : 5x5 ; moyenne : 15x15 ; haute : 30x30 pixel"""
"""ici x et y sont les coordonnées dans la matrice avec en haut à gauche le point (x=0,y=0)"""
class Drone:
    def __init__(self,x,y,altitude,carte):
        self.x = x
        self.y = y
        self.altitude = altitude
        self.carte = carte

#Cela n'a pas fonctionné, car fait tout direct au lieu de faire une apparition dynamique de la carte
    """def vol_automatique(self):
        traite toute la carte par déplacement avec balayage, ici forcément en commençant en (0,0) (voir le main)
        analyseur = Analyseur(self.x, self.y, self.altitude)
        step = analyseur.taille_patch(self.altitude)
        while self.x < self.carte.image.shape[1]:
            self.y=0
            while self.y < self.carte.image.shape[0] :
                self.carte.color_carte(self.x,self.y,self.altitude)
                self.y+=step
            self.x+=step"""

    def voler_un_pas(self):
        """Fait une seule étape de coloration et avance"""
        analyseur = Analyseur(self.x, self.y, self.altitude)
        step = analyseur.taille_patch(self.altitude)
        if self.x >= self.carte.image.shape[1]:
            return False  # Fin

        if self.y >= self.carte.image.shape[0]:
            self.y = 0
            self.x += step

        if self.x <  self.carte.image.shape[1] and self.y < self.carte.image.shape[0]:
            self.carte.color_carte(self.x, self.y, self.altitude)
            self.y += step
            return True

        return False

    def bouger_selon_la_cote(self):
        analyseur = Analyseur(self.x, self.y, self.altitude)
        reponse = analyseur.next_direction(self.altitude, self.x, self.y, self.carte.image)
        if reponse == "La côte est vertical, il faut aller vers le haut":
            self.y += 1
        elif reponse == "La côte est horizontal, il faut aller vers la droite":
            self.x += 1
        elif reponse == "La côte est en bas à gauche du pixel, il faut aller vers la diagonale haut/droite de manière descendante":
            self.y -= 1
            self.x -= 1
        elif reponse == "La côte est en haut à gauche du pixel, il faut aller vers la diagonale haut/gauche de manière ascendante":
            self.y += 1
            self.x -= 1
        elif reponse == "La côte est en bas à droite du pixel, il faut aller vers la diagonale haut/gauche de manière descendante":
            self.y -= 1
            self.x += 1
        elif reponse == "La côte est en haut à droite du pixel, il faut aller vers la diagonale haut/droite de manière ascendante":
            self.y += 1
            self.x += 1
        elif reponse == "On est sur la terre ferme, il faut repartir au patch précédent" or reponse == "On est en plein dans l'océan, il faut repartir au patch précédent":
            pass
    # Je ne vois pas trop comment le coder, mais je voudrais faire déplacer les coordonnées aux valeurs précédentes (ce serait presque un appel récursif en quelque sorte ou dans le même délire que les parcours de graphe).


class Analyseur:
    def __init__(self,x,y,altitude):
        self.x = x
        self.y = y
        self.altitude = altitude

    def taille_patch(self,altitude):
        if altitude == "basse":
            return 5

        if altitude == "moyenne":
            return 15

        if altitude == "haute":
            return 30

    def moyenne_RGB(self,altitude,x,y,image):
        taille= self.taille_patch(altitude)
        demi = taille // 2
        patch = image[max(y - demi,0):min(y + demi+1,image.shape[0]), max(x - demi,0):min(x + demi+1,image.shape[1])]
        moyenne = patch.mean(axis=(0, 1))  # moyenne des 25 pixels
        couleur = tuple(moyenne.astype(int))  # arrondi en entier RGB
        return couleur

    def couleur_dominante(self, altitude, x, y,
                          image):  # Correction du code avec chatGPT parce que problème d'analyse de patch
        maritime, terrestre = 0, 0
        taille = self.taille_patch(altitude)
        demi = taille // 2

        # extrait le patch centré autour de (x, y)
        patch = image[max(y - demi, 0):min(y + demi + 1, image.shape[0]),
                max(x - demi, 0):min(x + demi + 1, image.shape[1])]

        # parcours de chaque pixel du patch
        for i in range(patch.shape[0]):
            for j in range(patch.shape[1]):
                r, g, b = patch[i, j]
                if r < 100 and g < 100 and b > 200:
                    maritime += 1
                else:
                    terrestre += 1

        if maritime > terrestre:
            return 1
        else:
            return 0

    def quatre_cadrans(self, patch, taille):
        long_mid, large_mid = taille // 2, taille // 2
        cadran1 = patch[0:long_mid, 0:large_mid]
        cadran2 = patch[0:long_mid, large_mid:taille]
        cadran3 = patch[long_mid:taille, 0:large_mid]
        cadran4 = patch[long_mid:taille, large_mid:taille]
        return cadran1, cadran2, cadran3, cadran4

    def next_direction(self, altitude, x, y, image):
        taille = self.taille_patch(altitude)
        demi = taille // 2
        patch = image[max(y - demi, 0):min(y + demi + 1, image.shape[0]),
                max(x - demi, 0):min(x + demi + 1, image.shape[1])]
        cadran1, cadran2, cadran3, cadran4 = self.quatre_cadrans(patch, taille)
        cas1 = self.couleur_dominante(altitude, x, y, cadran1)
        cas2 = self.couleur_dominante(altitude, x, y, cadran2)
        cas3 = self.couleur_dominante(altitude, x, y, cadran3)
        cas4 = self.couleur_dominante(altitude, x, y, cadran4)
        if cas1 == 1 and cas2 == 1 and cas3 == 0 and cas4 == 0:
            return "La côte est vertical, il faut aller vers le haut"
        elif cas1 == 1 and cas2 == 0 and cas3 == 1 and cas4 == 0:
            return "La côte est horizontal, il faut aller vers la droite"
        elif cas1 == 0 and cas2 == 1 and cas3 == 1 and cas4 == 1:
            return "La côte est en bas à gauche du pixel, il faut aller vers la diagonale haut/droite de manière descendante"
        elif cas1 == 1 and cas2 == 0 and cas3 == 1 and cas4 == 1:
            return "La côte est en haut à gauche du pixel, il faut aller vers la diagonale haut/gauche de manière ascendante"
        elif cas1 == 1 and cas2 == 1 and cas3 == 0 and cas4 == 1:
            return "La côte est en bas à droite du pixel, il faut aller vers la diagonale haut/gauche de manière descendante"
        elif cas1 == 1 and cas2 == 1 and cas3 == 1 and cas4 == 0:
            return "La côte est en haut à droite du pixel, il faut aller vers la diagonale haut/droite de manière ascendante"
        elif cas1 == 0 and cas2 == 0 and cas3 == 0 and cas4 == 0:
            return "On est sur la terre ferme, il faut repartir au patch précédent"
        elif cas1 == 1 and cas2 == 1 and cas3 == 1 and cas4 == 1:
            return "On est en plein dans l'océan, il faut repartir au patch précédent"


# === Fonction d’animation Pygame === réalise avec chatgpt
def animation(drone):
    def numpy_to_surface(array):
        return pygame.surfarray.make_surface(np.transpose(array, (1, 0, 2)))

    pygame.init()
    carte = drone.carte
    surface = numpy_to_surface(carte.carte_blanche)
    largeur, hauteur = surface.get_size()
    fenetre = pygame.display.set_mode((largeur, hauteur))
    pygame.display.set_caption("Drone Cartographe")
    clock = pygame.time.Clock()

    running = True
    while running:
        continuer = drone.voler_un_pas()  # un seul pas par frame
        surface = numpy_to_surface(carte.carte_blanche)
        fenetre.blit(surface, (0, 0))
        pygame.display.flip()
        clock.tick(10)  # vitesse d’animation

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not continuer:
            running = False  # Stop si la carte est finie

    pygame.quit()

# -------- Simulation minimal --------
if __name__ == "__main__":
    # Charge une image existante
    image_path = "14_7982_5669.png"  # Ton image OSM
    carte = Carte(image_path)

    # Crée un drone qui va se déplacer automatiquement
    drone = Drone(x=0, y=0, altitude="moyenne", carte=carte)

    # Lance l'animation avec Pygame
    animation(drone)
