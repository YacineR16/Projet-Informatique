"""permet de voir le coloriage en direct de la carte en fonction du déplacement du drone"""
import pygame
import numpy as np
import matplotlib.pyplot as plt
import osmnx as ox
"""PIL = bibliothèque Python pour ouvrir, modifier, afficher et enregistrer des images"""
from PIL import Image

taille_tuile=256 #pixels

"""class qui délimite la zone à cartographiée en récupérant l'image sur OSM qui retourne une image.png"""
class Environnement:
    def __init__(self, lat_min, lon_min, lat_max, lon_max, zoom=16):
        self.lat_min = lat_min
        self.lon_min = lon_min
        self.lat_max = lat_max
        self.lon_max = lon_max
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

#n'a pas fonctionné car fait tout direct au lieu de faire une apparition dynamique de la carte
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