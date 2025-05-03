import unittest
import Drone_color_carte_dynamiquement as dccd
import numpy as np
from PIL import Image



class testAnalyseur (unittest.TestCase):
    def test_analyseur_types(self):
        a = dccd.Analyseur(10, 10, "moyenne")
        self.assertIsInstance(a.x, int)
        self.assertIsInstance(a.altitude, str)

    def test_taille_patch(self):
        analyseur = dccd.Analyseur(0, 0, "moyenne")
        self.assertEqual(analyseur.taille_patch("moyenne"), 15)

    def test_moyenne_RGB(self):
        # image de 5x5 pixels, rouges (255, 0, 0)
        image = np.zeros((5, 5, 3), dtype=np.uint8)
        image[:, :, 0] = 255 # image[x,y,(1, 2 ou 3 avec 1 rouge, 2 vert, et 3 bleu)

        # analyseur au centre (2,2) avec altitude "basse" => patch 5x5
        analyseur = dccd.Analyseur(x=2, y=2, altitude="basse")

        moyenne = analyseur.moyenne_RGB("basse", 2, 2, image)

        # La moyenne doit être exactement (255, 0, 0)
        self.assertEqual(moyenne, (255, 0, 0))

    def test_couleur_dominante_M(self):
        patch=np.full((3,3,3),[0,0,255], dtype=np.uint8)
        result=dccd.Analyseur.couleur_dominante(self,"basse",0,0,patch)
        self.assertEqual(result,1)

    def test_couleur_dominante_T(self):
        patch=np.full((3,3,3),[255,0,0], dtype=np.uint8)
        result=dccd.Analyseur.couleur_dominante(self,"basse",0,0,patch)
        self.assertEqual(result,0)

    def test_quatre_cadrans(self):
        patch=np.arange(4*4*3).reshape((4,4,3))
        cadran1,cadran2,cadran3,cadran4=dccd.Analyseur.quatre_cadrans(self,patch)
        self.assertEqual(cadran1.shape,(2,2,3))
        self.assertEqual(cadran2.shape,(2,2,3))
        self.assertEqual(cadran3.shape,(2,2,3))
        self.assertEqual(cadran4.shape,(2,2,3))

    def test_next_direction(self):
        image = np.zeros((5, 5, 3), dtype=np.uint8)
        image[:2, :2] = [0, 0, 255]  # Bleu en haut à gauche
        image[2:, 2:] = [0, 255, 0]  # Rouge en bas à droite
        image[2:, :2] = [0, 0, 255]  # Bleu en bas à gauche
        image[:2, 2:] = [255, 0, 0]  # Rouge en haut à droite
        analyseur = dccd.Analyseur(2, 2, "basse")
        direction = analyseur.next_direction("basse", 2, 2, image)
        # Vérifier que la direction est valide
        directions_valides = ["haut", "bas", "gauche", "droite","haut/gauche","bas/gauche","haut/droite","bas/droite"]
        self.assertIn(direction, directions_valides)
        # Si vous êtes sûr que la direction doit être "droite"
        self.assertEqual(direction, "droite")

    # Tests unitaires dans le cas d'un drone qui analyse
    def test_next_direction_unique_drone_maritime(self):
        image = np.full((1, 1, 3), [0, 0, 255], dtype=np.uint8)  # patch 1x1 bleu
        analyseur = dccd.Analyseur(1, 1, "basse")
        direction = analyseur.next_direction("basse", 0, 0, image)
        self.assertEqual(direction, "gauche")

    def test_next_direction_unique_drone_terrestre(self):
        image = np.full((1, 1, 3), [0, 255, 0], dtype=np.uint8)  # patch 1x1 vert
        analyseur = dccd.Analyseur(1, 1, "basse")
        direction = analyseur.next_direction("basse", 0, 0, image)
        self.assertEqual(direction, "droite")

class testCarte(unittest.TestCase) :

    def test_carte_types(self):
        img = np.ones((50, 50, 3), dtype=np.uint8) * 128
        test_path = "test_image_temporaire.png"
        Image.fromarray(img).save(test_path)

        carte = dccd.Carte(nom_image=test_path, lat_min=0, lat_max=1, lon_min=0, lon_max=1, zoom=17, altitude="moyenne",
                           mode_vol="manuel")
        self.assertIsInstance(carte.image, np.ndarray)
        self.assertIsInstance(carte.carte_blanche, np.ndarray)

    def test_initialisation_carte(self):
        # création d'une image pour le test
        img = np.ones((50, 100, 3), dtype=np.uint8) * 128
        test_path = "test_image.png"
        Image.fromarray(img).save(test_path)

        carte = dccd.Carte(
            nom_image=test_path,
            lat_min=0, lat_max=1,
            lon_min=0, lon_max=1,
            zoom=17, altitude="moyenne", mode_vol="manuel"
        )

        self.assertEqual(carte.carte_blanche.shape, carte.image.shape)



class testDrone (unittest.TestCase):
    def test_drone_init_types(self):
        img = np.ones((50, 50, 3), dtype=np.uint8) * 128
        test_path = "test_image_temp.png"
        Image.fromarray(img).save(test_path)

        carte = dccd.Carte(nom_image=test_path, lat_min=0, lat_max=1, lon_min=0, lon_max=1, zoom=17, altitude="moyenne",
                           mode_vol="manuel")

        drone = dccd.Drone(10, 20, "moyenne", carte, "manuel")
        self.assertIsInstance(drone.x, int)
        self.assertIsInstance(drone.y, int)
        self.assertIsInstance(drone.altitude, str)
        self.assertIsInstance(drone.carte, dccd.Carte)

    def test_deplacement_manuel(self):
        # avec une fausse carte
        img = np.ones((50, 100, 3), dtype=np.uint8) * 128
        path = "test.png"
        Image.fromarray(img).save(path)

        carte = dccd.Carte(path, 0, 1, 0, 1, 17, "basse", "manuel")
        drone = dccd.Drone(0, 0, "basse", carte, "manuel")

        x_avant = drone.x
        drone.deplacement_manuel("droite")
        self.assertGreaterEqual(drone.x, x_avant)

    def test_suivie_cote(self):
        # Création d'une image test de 10x10 pixels
        image_test = np.zeros((10, 10, 3), dtype=np.uint8)
        image_test[:5, :5] = [0, 0, 255]  # Zone bleue (mer)
        image_test[5:, 5:] = [255, 0, 0]  # Zone rouge (terre)
        test_path = "test_image.png"
        Image.fromarray(image_test).save(test_path)
        carte_test = dccd.Carte(test_path, 0, 1, 0, 1, 17, "basse", "suivie_cote")
        # Création du drone test
        drone_test = dccd.Drone(x=5, y=5, altitude="basse", carte=carte_test, mode_vol="suivie_cote")
        x_initial = drone_test.x
        y_initial = drone_test.y
        drone_test.suivie_cote()
        # Vérification que le drone s'est déplacé
        self.assertTrue((drone_test.x != x_initial) or (drone_test.y != y_initial),"Le drone ne s'est pas déplacé")
        # Vérification que le déplacement est d'une seule unité
        self.assertTrue(abs(drone_test.x - x_initial) <= 1 and abs(drone_test.y - y_initial) <= 1,"Le déplacement est supérieur à une unité")
        # Vérification que le drone reste dans les limites de l'image
        self.assertTrue(0 <= drone_test.x < carte_test.image.shape[1] and 0 <= drone_test.y < carte_test.image.shape[0],"Le drone est sorti des limites de l'image")


class testMissionDrone(unittest.TestCase) :
    def test_set_mode_type(self):
        mission = dccd.MissionDrone()
        mission.set_mode("manuel")
        self.assertIsInstance(mission.mode, str)

    def test_set_zone_type(self):
        mission = dccd.MissionDrone()
        zone = (48.85, 2.35, 48.86, 2.36)
        mission.set_zone(zone)
        self.assertIsInstance(mission.zone, tuple)
        self.assertEqual(len(mission.zone), 4)

    def test_preparer(self):
        def test_set_mode(self):
            mission = dccd.MissionDrone()
            mission.set_mode("manuel")
            self.assertEqual(mission.mode, "manuel")



if __name__ == "__main__":
    unittest.main()