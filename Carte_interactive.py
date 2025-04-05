import folium

#Zoom correspondant à la vue totale du département du Finistère avec un centrage sur le centre de Brest
carte_finistere=folium.Map(location=[48.418962,-4.470674], zoom_start=9)

#Création des points d'interêt ENSTA-La Gua
ENSTA=folium.Marker(location=[48.419365,-4.471680],popup='ENSTA',icon=folium.Icon(color='blue')).add_to(carte_finistere)
La_Gua=folium.Marker(location=[48.385148,-4.493561],popup='LA GUA',icon=folium.Icon(color='green')).add_to(carte_finistere)

#Création de l'icone de drone
Drone=folium.CustomIcon(icon_image='avion.png',icon_size=[20,20], icon_anchor=[25,25])

#Placement du drone à l'ENSTA
Placement_Drone=folium.Marker(location=[48.418875,-4.471403],popup='Drone',icon=Drone).add_to(carte_finistere)

#Création du fichier Html permettant l'affichage intéractif de la carte OpenStreetMap
carte_finistere.save('carte_finistere.html')