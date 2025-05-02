"""permet de voir le coloriage en direct de la carte en fonction du déplacement du drone"""
import pygame
import numpy as np
import os
import donnees_osm
"""PIL = bibliothèque Python pour ouvrir, modifier, afficher et enregistrer des images"""
from PIL import Image
import SQL


taille_tuile=256 #pixels

"""class qui délimite la zone à cartographiée en récupérant l'image sur OSM qui retourne une image.png 
= représente la mission complète du drone
peut etre à renommer en Mission"""
class Environnement:
    def __init__(self, lat_min, lon_min, lat_max, lon_max, zoom,altitude,mode_vol):
        self.lat_min = lat_min
        self.lon_min = lon_min
        self.lat_max = lat_max
        self.lon_max = lon_max
        self.altitude = altitude
        self.mode_vol=mode_vol
        self.zoom = zoom  # même si non utilisé directement ici
        self.image_path = f"carte_assemblee_zoom{zoom}.png"
        self.tuile = []


    def adapter_zone(self,lat_min, lat_max, lon_min, lon_max, zoom):
        largeur_max = 1024
        hauteur_max = 768
        x_min, y_max = donnees_osm.latlon_to_tile(lat_min, lon_min, zoom)
        x_max, y_min = donnees_osm.latlon_to_tile(lat_max, lon_max, zoom)

        nb_tiles_x = x_max - x_min + 1
        nb_tiles_y = y_max - y_min + 1

        if nb_tiles_x * 256 <= largeur_max and nb_tiles_y * 256 <= hauteur_max:
            return lat_min, lat_max, lon_min, lon_max  # OK

        print("Taille de carte demandée trop grande : recadrage de la carte automatique")
        # Sinon on recentre : prend le milieu et limite à un nombre max de tuiles
        max_tiles_x = largeur_max // 256
        max_tiles_y = hauteur_max // 256

        x_centre = (x_min + x_max) // 2
        y_centre = (y_min + y_max) // 2

        new_x_min = x_centre - max_tiles_x // 2
        new_x_max = x_centre + max_tiles_x // 2 - 1
        new_y_min = y_centre - max_tiles_y // 2
        new_y_max = y_centre + max_tiles_y // 2 - 1

        # Reconversion en lat/lon
        lat_max_new, lon_min_new = donnees_osm.tile_to_latlon(new_x_min, new_y_min, zoom)
        lat_min_new, lon_max_new = donnees_osm.tile_to_latlon(new_x_max, new_y_max, zoom)

        return lat_min_new, lat_max_new, lon_min_new, lon_max_new


    def OSM(self):
        print("\n--- Téléchargement et assemblage des tuiles OSM ---")
        lat_min, lat_max, lon_min, lon_max = self.adapter_zone(self.lat_min, self.lat_max, self.lon_min, self.lon_max,
                                                               self.zoom)
        self.lat_min, self.lat_max, self.lon_min, self.lon_max = lat_min, lat_max, lon_min, lon_max

        x_min, x_max, y_min, y_max, dossier = donnees_osm.telecharger_zone(
            self.lat_min, self.lat_max, self.lon_min, self.lon_max, self.zoom, dossier="tuiles_environnement")
        donnees_osm.assembler_image(x_min, x_max, y_min, y_max, self.zoom, dossier)
        self.image_path = os.path.join(dossier, f"carte_assemblee_zoom{self.zoom}.png")
        print(f"Image assemblée disponible : {self.image_path}")
        return self.image_path


    """donne le numéro de toutes les tuiles de la zone à cartographier
    utile pour retrouver le nom de l'image enregistre et pour le tableau SQL"""
    def tuiles_zone(self,lat_min, lat_max, lon_min, lon_max, zoom):
        x_min, y_max = donnees_osm.latlon_to_tile(lat_min, lon_min, zoom)
        x_max, y_min = donnees_osm.latlon_to_tile(lat_max, lon_max, zoom)

        self.tuiles = []
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                self.tuiles.append((x, y, zoom))  # ou f"{zoom}_{x}_{y}" pour un ID unique
        return self.tuiles

    """création du tableau SQL"""
    def enregistrer_mission(self):
        SQL.tableau_SQL()
        tiles_included= self.tuiles_zone(self.lat_min,self.lat_max,self.lon_min,self.lon_max,self.zoom)
        nb_tuile = len(tiles_included)
        if not SQL.carte_existe_deja(self.lat_min, self.lat_max, self.lon_min, self.lon_max,
                                     self.zoom, self.altitude, self.mode_vol):
            SQL.inserer_donnees_carte(self.lat_min, self.lat_max, self.lon_min, self.lon_max, self.zoom,
                                  self.altitude, self.mode_vol, nb_tuile, str(tiles_included))


class Carte:
    def __init__(self, nom_image, lat_min, lat_max, lon_min, lon_max, zoom, altitude, mode_vol):
        """nom_image est une chaîne de caractères"""
        self.nom_image = nom_image
        self.image = self.image_np(nom_image)
        self.carte_blanche = self.initialisation_carte()
        self.id_carte = SQL.trouver_id_carte(lat_min, lat_max, lon_min, lon_max, zoom, altitude, mode_vol)

    def image_np(self, nom_image):
        """Retourne un tableau de pixels RGB à partir de l'image"""
        img = Image.open(nom_image).convert("RGB")
        return np.array(img)

    def initialisation_carte(self):
        """Crée une carte blanche de même taille que l'image de référence"""
        size = self.image.shape
        return np.ones((size[0], size[1], 3), dtype=np.uint8) * 255

    def color_carte(self, x, y, altitude,mode_vol):
        analyseur = Analyseur(x, y, altitude)
        taille = analyseur.taille_patch(altitude)
        demi = taille // 2
        couleur = analyseur.moyenne_RGB(altitude, x, y, self.image)
        self.carte_blanche[y - demi:y + demi + 1, x - demi:x + demi + 1] = couleur

        R, G, B = couleur
        tile_x = x // taille_tuile
        tile_y = y // taille_tuile
        tile_number = tile_y * (self.image.shape[1] // taille_tuile) + tile_x  # simple numéro local

        if self.id_carte is not None:
            SQL.inserer_données_pixel(x, y, R, G, B,altitude,mode_vol,
                                      tile_number=tile_number, id_carte=self.id_carte)

    def sauvegarder_image_finale(self, chemin="carte_coloree_par_drone.png"):
        image_pil = Image.fromarray(self.carte_blanche)
        image_pil.save(chemin)
        print(f"Carte coloriée enregistrée sous : {chemin}")


"""Seul 3 altitudes pourront être choisi : basse, moyenne,  qui définiront les tailles des patch analysés"""
""" basse : 5x5 ; moyenne : 15x15 ; haute : 30x30 pixel"""
"""ici x et y sont les coordonnées dans la matrice avec en haut à gauche le point (x=0,y=0)"""
class Drone:
    def __init__(self,x,y,altitude,carte,mode_vol):
        self.x = x
        self.y = y
        self.altitude = altitude
        self.carte = carte
        self.mode_vol=mode_vol

    def voler(self):
        self.mode_vol.voler(self)


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
            self.carte.color_carte(self.x, self.y, self.altitude,self.mode_vol)
            self.y += step
            return True

        return False

    def deplacement_manuel(self,direction):
        analyseur = Analyseur(self.x, self.y, self.altitude)
        step = analyseur.taille_patch(self.altitude)

        if direction == "droite":
            self.x=min(self.x + step, self.carte.image.shape[1] - 1)
            """min entre le nombre de pixel qu'avance le drone (en fonction altitude) et le dernier pixel de la largeur de la carte"""

        if direction == "gauche":
            self.x = max(self.x - step, 0)

        if direction == "haut":
            self.y = max(self.y - step, 0)

        if direction == "bas":
            self.y = min(self.y + step, self.carte.image.shape[0] - 1)

    """déplacer le drone manuellement (flèches), visualiser ce qu'il voit sur la carte OSM, 
    colorier une carte blanche avec ce qu'il perçoit, afficher tout ça en temps réel."""
    def vol_manuel(self):
        pygame.init()

        """Crée deux surfaces Pygame à partir de l'image OSM et la carte blanche"""
        surface_osm = pygame.surfarray.make_surface(np.transpose(self.carte.image, (1, 0, 2)))
        surface_blanche = pygame.surfarray.make_surface(np.transpose(self.carte.carte_blanche, (1, 0, 2)))

        """Crée une fenêtre graphique : deux fois la largeur de la carte (OSM à gauche, carte blanche à droite) 
        et même hauteur que l’image."""
        largeur, hauteur = surface_osm.get_size()
        fenetre = pygame.display.set_mode((largeur * 2, hauteur))
        """permet de réguler le nombre d'image afficher à la seconde"""
        clock = pygame.time.Clock()

        running = True
        while running: #tourne jusqu'à fermeture de la carte
            fenetre.fill((0, 0, 0)) # pour effacer la position du drone précédente
            for event in pygame.event.get(): #  la base du contrôle des événements dans Pygame : permet la fermeture du programme
                if event.type == pygame.QUIT:
                    running = False

            keys = pygame.key.get_pressed() # modélise les touches enfoncées

            if keys[pygame.K_RIGHT]: # valeur de la touche enfoncée et lance le programme déplacer correspondant
                self.deplacement_manuel("droite")
            if keys[pygame.K_LEFT]:
                self.deplacement_manuel("gauche")
            if keys[pygame.K_DOWN]:
                self.deplacement_manuel("bas")
            if keys[pygame.K_UP]:
                self.deplacement_manuel("haut")

            """ Observer ce que voit le drone et colorier"""
            self.carte.color_carte(self.x, self.y, self.altitude, self.mode_vol)

            """Mise à jour des surfaces"""
            surface_osm =pygame.surfarray.make_surface(np.transpose(self.carte.image, (1, 0, 2)))
            surface_blanche = pygame.surfarray.make_surface(np.transpose(self.carte.carte_blanche, (1, 0, 2)))

            """ Affiche les 2 surfaces créées avant sur la fenêtre"""
            fenetre.blit(surface_osm, (0, 0))
            fenetre.blit(surface_blanche, (largeur, 0))

            """Afficher rectangle autour du drone (zone de vision)"""
            analyseur = Analyseur(self.x, self.y, self.altitude)
            step = analyseur.taille_patch(self.altitude)
            pygame.draw.rect(fenetre, (255, 0, 0), (self.x, self.y, step, step), 2) #pour la vision du drone

            pygame.display.flip() # met à jour l'écran
            clock.tick(10)

        pygame.quit()

    def suivie_cote(self):
        """""
        Fonction permettant le suivi du littoral
        """
        analyseur = Analyseur(self.x, self.y, self.altitude)
        reponse = analyseur.next_direction(self.altitude, self.x, self.y, self.carte.image)
        if reponse == "bas":
            self.y += 1
        elif reponse == "haut":
            self.y -= 1
        elif reponse == "gauche":
            self.x -= 1
        elif reponse == "droite":
            self.x += 1
        elif reponse == "haut/gauche":
            self.y -= 1
            self.x -= 1
        elif reponse == "bas/gauche":
            self.y += 1
            self.x -= 1
        elif reponse == "haut/droite":
            self.y -= 1
            self.x += 1
        elif reponse == "bas/droite":
            self.y += 1
            self.x += 1
        else:
            print(f"Direction inconnue : {reponse}")

class Analyseur:
    def __init__(self, x, y, altitude):
        self.x = x
        self.y = y
        self.altitude = altitude

    def taille_patch(self, altitude):
        if altitude == "basse":
            return 5
        if altitude == "moyenne":
            return 15
        if altitude == "haute":
            return 30

    def moyenne_RGB(self, altitude, x, y, image):
        taille = self.taille_patch(altitude)
        demi = taille // 2
        patch = image[max(y - demi, 0):min(y + demi + 1, image.shape[0]),
                      max(x - demi, 0):min(x + demi + 1, image.shape[1])]
        moyenne = patch.mean(axis=(0, 1))  # moyenne des pixels
        couleur = tuple(moyenne.astype(int))  # arrondi en entier RGB
        return couleur

    def couleur_dominante(self, altitude, x, y, patch):
        maritime, terrestre = 0, 0
        for i in range(patch.shape[0]):
            for j in range(patch.shape[1]):
                r, g, b = patch[i, j]
                if r < 50 and g < 50 and b > 200:
                    maritime += 1
                else:
                    terrestre += 1
        if maritime > terrestre:
            return 1
        else:
            return 0

    def quatre_cadrans(self, patch):
        long_mid, large_mid = patch.shape[0] // 2, patch.shape[1] // 2
        cadran1 = patch[0:long_mid, 0:large_mid]
        cadran2 = patch[long_mid:, 0:large_mid]
        cadran3 = patch[0:long_mid, large_mid:]
        cadran4 = patch[long_mid:, large_mid:]
        return cadran1, cadran2, cadran3, cadran4

    def next_direction(self, altitude, x, y, image):
        taille = self.taille_patch(altitude)
        demi = taille // 2
        patch = image[max(y - demi, 0):min(y + demi + 1, image.shape[0]),
                      max(x - demi, 0):min(x + demi + 1, image.shape[1])]

        # Vérifier si le patch est suffisamment grand pour appliquer les cadrans
        if patch.shape[0] >= 2 and patch.shape[1] >= 2:
            cadran1, cadran2, cadran3, cadran4 = self.quatre_cadrans(patch)
            cas1 = self.couleur_dominante(altitude, x, y, cadran1)
            cas2 = self.couleur_dominante(altitude, x, y, cadran2)
            cas3 = self.couleur_dominante(altitude, x, y, cadran3)
            cas4 = self.couleur_dominante(altitude, x, y, cadran4)

            if cas1 == 1 and cas2 == 1 and cas3 == 0 and cas4 == 0:
                return "droite"
            elif cas1 == 1 and cas2 == 0 and cas3 == 1 and cas4 == 0:
                return "bas"
            elif cas1 == 0 and cas2 == 1 and cas3 == 1 and cas4 == 1:
                return "haut/gauche"
            elif cas1 == 1 and cas2 == 0 and cas3 == 1 and cas4 == 1:
                return "bas/gauche"
            elif cas1 == 1 and cas2 == 1 and cas3 == 0 and cas4 == 1:
                return "haut/droite"
            elif cas1 == 1 and cas2 == 1 and cas3 == 1 and cas4 == 0:
                return "bas/droite"
            elif cas1 == 0 and cas2 == 1 and cas3 == 0 and cas4 == 1:
                return "haut"
            else:
                return "bas"
        else:
            # Cas unique drone : on se base uniquement sur la moyenne RGB
            couleur = self.moyenne_RGB(altitude, x, y, image)
            r, g, b = couleur
            if r < 100 and g < 100 and b > 200:
                return "gauche"
            else:
                return "droite"


## DESIGN PATTERN

class DroneFactory: #Creation du drone avec son mode de vol associé
    @staticmethod
    def creer_drone(type, x, y, altitude, carte, mode_vol):
        if type == "manuel":
            return Drone(x, y, altitude, carte, "manuel") #Normalement ce sera la class de Drone qui sera controlable manuellement
        elif type == "automatique":
            return Drone(x, y, altitude, carte, "automatique")
        elif type == "suivie_cote":
            return Drone(x, y, altitude, carte, "suivie_cote")

class Mode_de_vol:
    def voler(self, drone):
        raise NotImplementedError

class manuel(Mode_de_vol):
    def voler(self, drone):
        drone.vol_manuel()

class Suivi_Cote(Mode_de_vol):
    def voler(self, drone):
        drone.bouger_selon_la_cote()

# mise en place du DSL
class MissionDrone:
    def __init__(self):
        self.mode = None  # "manuel" ou "automatique"
        self.altitude = None  # "petite" , "moyenne" ou "haute"
        self.zone = (None, None, None, None)  # pour automatique
        self.zoom = None  # à choisir mais le mieux 17
        self.drone = None  # contient le drone actif, qui se déplace, colorie, et enregistre
        self.carte = None #Contient la carte blanche et l’image source à analyser
        self.env = None # Contient les données de l'environnement OSM (carte, zone, SQL...)

    # méthodes setter permettant d'affecter une valeur à un attribut interne
    def set_mode(self, mode):
        self.mode = mode
        return self

    def set_altitude(self, altitude):
        self.altitude = altitude
        return self

    def set_zone(self, zone):
        self.zone = zone
        return self

    def set_zoom(self, zoom):
        self.zoom = zoom
        return self

    def set_drone(self, drone):
        self.drone = drone
        return self

    def set_carte(self, carte):
        self.carte = carte
        return self

    def set_env(self, env):
        self.env = env
        return self


    def preparer(self):
        """Configure l'environnement de vol selon le mode choisi."""

        if self.mode == "automatique" and self.zone is not None:
            # enrionnement créé
            lat_min, lon_min, lat_max, lon_max = self.zone
            self.env = Environnement(
                lat_min=lat_min, lon_min=lon_min,
                lat_max=lat_max, lon_max=lon_max,
                zoom=self.zoom,
                altitude=self.altitude,
                mode_vol="automatique"
            )

            # telechargement de la carte OSM
            self.env.OSM()

            # mission enregistrée dans la table mission
            self.env.enregistrer_mission()

            # créer la carte
            self.carte = Carte(
                self.env.image_path,
                self.env.lat_min, self.env.lat_max,
                self.env.lon_min, self.env.lon_max,
                self.env.zoom,
                self.env.altitude,
                "automatique"
            )

            # créer le drone
            self.drone = Drone(0, 0, self.altitude, self.carte, "automatique")


        elif self.mode == "manuel":
            # environnement créé
            lat_min, lon_min, lat_max, lon_max = self.zone
            self.env = Environnement(
                lat_min=lat_min, lon_min=lon_min,
                lat_max=lat_max, lon_max=lon_max,
                zoom=self.zoom,
                altitude=self.altitude,
                mode_vol="manuel"
            )

            # telechargement de la carte OSM
            self.env.OSM()

            # mission enregistrée dans la table mission
            self.env.enregistrer_mission()

            # créer la carte
            self.carte = Carte(
                self.env.image_path,
                self.env.lat_min, self.env.lat_max,
                self.env.lon_min, self.env.lon_max,
                self.env.zoom,
                self.env.altitude,
                "manuel"
            )

            # créer le drone
            self.drone = Drone(0, 0, self.altitude, self.carte, "manuel")

        elif self.mode == "suivie_cote":
            # enrionnement créé
            lat_min, lon_min, lat_max, lon_max = self.zone
            self.env = Environnement(
                lat_min=lat_min, lon_min=lon_min,
                lat_max=lat_max, lon_max=lon_max,
                zoom=self.zoom,
                altitude=self.altitude,
                mode_vol="suivie_cote"
            )

            # telechargement de la carte OSM
            self.env.OSM()

            # mission enregistrée dans la table mission
            self.env.enregistrer_mission()

            # créer la carte
            self.carte = Carte(
                self.env.image_path,
                self.env.lat_min, self.env.lat_max,
                self.env.lon_min, self.env.lon_max,
                self.env.zoom,
                self.env.altitude,
                "suivie_cote"
            )

            # créer le drone
            self.drone = Drone(0, 0, self.altitude, self.carte, "manuel")

        else:
            raise ValueError("Mode inconnu ou informations incomplètes.")

        return self

    def executer(self):
        if (self.mode == "manuel"):
            self.drone.vol_manuel()
        elif self.mode == "automatique":
            animation(self.drone)
        elif self.mode == "suivie_cote":
            #animation_suivie_cote(self.drone)
            raise ValueError("Mode de vol non existant.")
        else:
            raise ValueError("Mode de vol non reconnu.")


# animation pygame pour l'automatique
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

#Mode suivie de la côte
'''def animation_suivie_cote(drone):
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
        continuer = drone.suivie_cote()  # suivre la côte
        surface = numpy_to_surface(carte.carte_blanche)
        fenetre.blit(surface, (0, 0))
        pygame.display.flip()
        clock.tick(10)  # vitesse d’animation

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if not continuer:
            running = False  # Stop si la carte est finie

    pygame.quit()'''

# Simulation
if __name__ == "__main__":
    # Zone élargie autour de Brest
    lat_min = 48.8560
    lat_max = 48.8570
    lon_min = 2.3510
    lon_max = 2.3520
    zoom = 17
    zone = (lat_min, lon_min, lat_max, lon_max)

    mission = MissionDrone() \
        .set_mode("manuel") \
        .set_altitude("moyenne") \
        .set_zone(zone) \
        .set_zoom(zoom) \
        .preparer() \

    mission.executer()

    # Sauvegarde carte finale
    mission.carte.sauvegarder_image_finale("carte_coloree_manuel.png")

    # Lecture BDD
    SQL.lire_donnees("SELECT * FROM Cartes")
    SQL.lire_donnees("SELECT * FROM Pixels")
