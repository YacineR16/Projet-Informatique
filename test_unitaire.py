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
