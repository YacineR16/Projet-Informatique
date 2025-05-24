# -*- coding: utf-8 -*-

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox
import sys
import numpy as np
from PIL import Image
import donnees_osm
import SQL
import pygame
from pygame.locals import *
from Drone_color_carte_dynamiquement import Environnement, Carte, DroneFactory, MissionDrone


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.ui = Ui_Interface()
        self.ui.setupUi(self)

        # Variables pour stocker les paramètres
        self.mission = None
        self.current_drone = None

        # Connecter les signaux
        self.ui.Depart.clicked.connect(self.lancer_mission)
        self.ui.boutonQuitter.clicked.connect(self.close)

        # Initialiser les combobox avec les valeurs par défaut
        self.ui.comboBox.setCurrentText("automatique")
        self.ui.comboBox_2.setCurrentText("moyenne")
        self.ui.comboBox_3.setCurrentText("1")

        # Configurer la zone d'affichage
        self.scene = QtWidgets.QGraphicsScene()
        self.ui.widget.setLayout(QtWidgets.QVBoxLayout())
        self.graphics_view = QtWidgets.QGraphicsView(self.scene)
        self.ui.widget.layout().addWidget(self.graphics_view)

    def lancer_mission(self):
        try:
            # Récupérer les paramètres de l'interface
            mode_vol = self.ui.comboBox.currentText()
            altitude = self.ui.comboBox_2.currentText()
            nb_drones = int(self.ui.comboBox_3.currentText())

            # Récupérer les coordonnées géographiques
            try:
                lat_max = float(self.ui.textEdit_4.toPlainText())
                lat_min = float(self.ui.textEdit_5.toPlainText())
                lon_max = float(self.ui.textEdit_6.toPlainText())
                lon_min = float(self.ui.textEdit_7.toPlainText())
            except ValueError:
                QMessageBox.warning(self, "Erreur", "Veuillez entrer des coordonnées valides")
                return

            # Vérifier que les coordonnées sont cohérentes
            if lat_min >= lat_max or lon_min >= lon_max:
                QMessageBox.warning(self, "Erreur", "Les coordonnées min doivent être inférieures aux coordonnées max")
                return

            zoom = 17  # Valeur fixe pour le zoom, peut être modifiée si besoin

            # Créer et préparer la mission
            self.mission = MissionDrone() \
                .set_mode(mode_vol) \
                .set_altitude(altitude) \
                .set_zone((lat_min, lon_min, lat_max, lon_max)) \
                .set_zoom(zoom) \
                .preparer()

            # Exécuter la mission dans un thread séparé pour ne pas bloquer l'interface
            if mode_vol == "manuel":
                self.executer_mission_manuel()
            else:
                self.executer_mission_automatique()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {str(e)}")

    def executer_mission_manuel(self):
        # Pour le mode manuel, nous utilisons directement pygame
        # Il faut fermer l'interface PyQt temporairement
        self.hide()

        try:
            self.mission.executer()

            # Sauvegarder la carte après exécution
            if hasattr(self.mission, 'carte'):
                self.mission.carte.sauvegarder_image_finale("carte_coloree_manuel.png")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur pendant l'exécution: {str(e)}")
        finally:
            self.show()

    def executer_mission_automatique(self):
        # Pour le mode automatique, nous pouvons afficher la progression dans l'interface
        try:
            # Créer un thread pour exécuter la mission sans bloquer l'interface
            from PyQt5.QtCore import QThread, pyqtSignal

            class MissionThread(QThread):
                update_signal = pyqtSignal(np.ndarray)
                finished_signal = pyqtSignal()

                def __init__(self, mission):
                    super().__init__()
                    self.mission = mission

                def run(self):
                    drone = self.mission.drone
                    while drone.voler_un_pas():
                        self.update_signal.emit(drone.carte.carte_blanche)
                        QThread.msleep(100)  # Pause pour visualisation
                    self.finished_signal.emit()

            self.thread = MissionThread(self.mission)
            self.thread.update_signal.connect(self.afficher_carte)
            self.thread.finished_signal.connect(self.mission_terminee)
            self.thread.start()

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur pendant l'exécution: {str(e)}")

    def afficher_carte(self, carte_np):
        # Convertir le numpy array en QImage puis en QPixmap pour affichage
        height, width, channel = carte_np.shape
        bytes_per_line = 3 * width
        qimage = QtGui.QImage(carte_np.data, width, height, bytes_per_line, QtGui.QImage.Format_RGB888)
        pixmap = QtGui.QPixmap.fromImage(qimage)

        # Mettre à jour l'affichage
        self.scene.clear()
        self.scene.addPixmap(pixmap)
        self.graphics_view.fitInView(self.scene.itemsBoundingRect(), QtCore.Qt.KeepAspectRatio)

    def mission_terminee(self):
        QMessageBox.information(self, "Mission terminée", "La cartographie est terminée!")

        # Sauvegarder la carte
        if hasattr(self.mission, 'carte'):
            self.mission.carte.sauvegarder_image_finale("carte_coloree_automatique.png")

        # Afficher les données SQL
        try:
            SQL.lire_donnees("SELECT * FROM Cartes")
            SQL.lire_donnees("SELECT * FROM Pixels")
        except Exception as e:
            QMessageBox.warning(self, "Base de données", f"Erreur lors de la lecture de la base de données: {str(e)}")


class Ui_Interface(object):
    def setupUi(self, Interface):
        Interface.setObjectName("Interface")
        Interface.resize(1116, 722)
        Interface.setProperty("74", "")
        self.centralwidget = QtWidgets.QWidget(Interface)
        self.centralwidget.setObjectName("centralwidget")
        self.widget = QtWidgets.QWidget(self.centralwidget)
        self.widget.setGeometry(QtCore.QRect(80, 60, 931, 431))
        self.widget.setObjectName("widget")
        self.Depart = QtWidgets.QPushButton(self.centralwidget)
        self.Depart.setGeometry(QtCore.QRect(920, 550, 93, 28))
        self.Depart.setObjectName("Depart")
        self.boutonQuitter = QtWidgets.QPushButton(self.centralwidget)
        self.boutonQuitter.setGeometry(QtCore.QRect(920, 600, 93, 28))
        self.boutonQuitter.setObjectName("boutonQuitter")
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setGeometry(QtCore.QRect(140, 550, 110, 30))
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox_2 = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox_2.setGeometry(QtCore.QRect(140, 610, 110, 30))
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_3 = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox_3.setGeometry(QtCore.QRect(440, 550, 140, 30))
        self.comboBox_3.setObjectName("comboBox_3")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.textEdit_4 = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_4.setGeometry(QtCore.QRect(750, 520, 91, 31))
        self.textEdit_4.setObjectName("textEdit_4")
        self.textEdit_5 = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_5.setGeometry(QtCore.QRect(750, 560, 91, 31))
        self.textEdit_5.setObjectName("textEdit_5")
        self.textEdit_6 = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_6.setGeometry(QtCore.QRect(750, 600, 91, 31))
        self.textEdit_6.setObjectName("textEdit_6")
        self.textEdit_7 = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_7.setGeometry(QtCore.QRect(750, 640, 91, 31))
        self.textEdit_7.setObjectName("textEdit_7")
        self.label = QtWidgets.QLabel(self.centralwidget)
        self.label.setGeometry(QtCore.QRect(300, 560, 111, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(self.centralwidget)
        self.label_2.setGeometry(QtCore.QRect(40, 560, 91, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.centralwidget)
        self.label_3.setGeometry(QtCore.QRect(50, 610, 61, 31))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.centralwidget)
        self.label_4.setGeometry(QtCore.QRect(630, 530, 111, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(self.centralwidget)
        self.label_5.setGeometry(QtCore.QRect(630, 570, 111, 16))
        self.label_5.setObjectName("label_5")
        self.label_6 = QtWidgets.QLabel(self.centralwidget)
        self.label_6.setGeometry(QtCore.QRect(630, 610, 111, 16))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(self.centralwidget)
        self.label_7.setGeometry(QtCore.QRect(630, 650, 111, 16))
        self.label_7.setObjectName("label_7")
        Interface.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(Interface)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 1116, 26))
        self.menubar.setObjectName("menubar")
        Interface.setMenuBar(self.menubar)
        self.action = QtWidgets.QAction(Interface)
        self.action.setObjectName("action")
        self.actionautomatique = QtWidgets.QAction(Interface)
        self.actionautomatique.setObjectName("actionautomatique")
        self.actionmanuel = QtWidgets.QAction(Interface)
        self.actionmanuel.setObjectName("actionmanuel")
        self.actionsuivie_cote = QtWidgets.QAction(Interface)
        self.actionsuivie_cote.setObjectName("actionsuivie_cote")

        self.retranslateUi(Interface)
        self.boutonQuitter.clicked.connect(Interface.close)  # type: ignore
        QtCore.QMetaObject.connectSlotsByName(Interface)

    def retranslateUi(self, Interface):
        _translate = QtCore.QCoreApplication.translate
        Interface.setWindowTitle(_translate("Interface", "Cartographie par drones"))
        self.Depart.setText(_translate("Interface", "GO !"))
        self.boutonQuitter.setText(_translate("Interface", "Quitter"))
        self.comboBox.setCurrentText(_translate("Interface", "automatique"))
        self.comboBox.setItemText(0, _translate("Interface", "automatique"))
        self.comboBox.setItemText(1, _translate("Interface", "manuel"))
        self.comboBox.setItemText(2, _translate("Interface", "suivie de cote"))
        self.comboBox_2.setItemText(0, _translate("Interface", "basse"))
        self.comboBox_2.setItemText(1, _translate("Interface", "moyenne"))
        self.comboBox_2.setItemText(2, _translate("Interface", "haute"))
        self.comboBox_3.setItemText(0, _translate("Interface", "1"))
        self.comboBox_3.setItemText(1, _translate("Interface", "4"))
        self.comboBox_3.setItemText(2, _translate("Interface", "9"))
        self.comboBox_3.setItemText(3, _translate("Interface", "16"))
        self.textEdit_4.setHtml(_translate("Interface",
                                           "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                           "<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
                                           "p, li { white-space: pre-wrap; }\n"
                                           "</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:7.8pt; font-weight:400; font-style:normal;\">\n"
                                           "<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.label.setText(_translate("Interface", "Nombre de drones"))
        self.label_2.setText(_translate("Interface", "Mode de Vol"))
        self.label_3.setText(_translate("Interface", "Altitude"))
        self.label_4.setText(_translate("Interface", "Latitude max"))
        self.label_5.setText(_translate("Interface", "Latitude min"))
        self.label_6.setText(_translate("Interface", "Longitude max"))
        self.label_7.setText(_translate("Interface", "Longitude min"))
        self.action.setText(_translate("Interface", "Quitter"))
        self.actionautomatique.setText(_translate("Interface", "automatique"))
        self.actionmanuel.setText(_translate("Interface", "manuel"))
        self.actionsuivie_cote.setText(_translate("Interface", "suivie de cote"))


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())