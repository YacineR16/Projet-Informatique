import sqlite3

def tableau_SQL():

    # Connexion à la base de données SQLite (ici dans un fichier local 'cartographie.db')
    conn = sqlite3.connect('mes_donnes.db')
    cursor = conn.cursor()

    # Création des tables selon la structure définie
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Cartes (
        id_carte       INTEGER PRIMARY KEY,
        lat_min        REAL,
        lat_max        REAL,
        lon_min        REAL,
        lon_max        REAL,
        zoom           INTEGER,
        altitude       REAL,
        mode_vol       TEXT,
        nb_tuile     INTEGER,
        tiles_included TEXT
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Pixels (
        id_pixel    INTEGER PRIMARY KEY,
        x           INTEGER,
        y           INTEGER,
        R       INTEGER,
        G       INTEGER,
        B       INTEGER,
        tile_number INTEGER,
        id_carte    INTEGER,
        FOREIGN KEY(id_carte) REFERENCES Cartes(id_carte)
    )
    """)

    conn.commit()
    conn.close()

def carte_existe_deja(lat_min, lat_max, lon_min, lon_max, zoom, altitude, mode_vol):
    conn = sqlite3.connect('mes_donnes.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id_carte FROM Cartes
        WHERE lat_min=? AND lat_max=? AND lon_min=? AND lon_max=?
          AND zoom=? AND altitude=? AND mode_vol=?
    """, (lat_min, lat_max, lon_min, lon_max, zoom, altitude, mode_vol))
    result = cursor.fetchone()
    conn.close()
    return result is not None


def inserer_donnees_carte(lat_min,lat_max,lon_min,lon_max,zoom,altitude,mode_vol,nb_tuile,tiles_included):
    conn = sqlite3.connect('mes_donnes.db')  # Crée ou ouvre un fichier de base de données
    cursor = conn.cursor()  # permet d’exécuter des commandes SQL
    carte_data=(lat_min,lat_max,lon_min,lon_max,zoom,altitude,mode_vol,nb_tuile,tiles_included)
    cursor.execute("""
    INSERT INTO Cartes(lat_min, lat_max, lon_min, lon_max, zoom, altitude, mode_vol, nb_tuile, tiles_included)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, carte_data)
    id_carte = cursor.lastrowid  # Récupérer l'ID auto-généré de la carte insérée
    conn.commit()
    conn.close()

    return id_carte


def inserer_données_pixel(x, y, R, G, B, altitude, mode_vol, tile_number, id_carte):
    conn = sqlite3.connect('mes_donnes.db')  # Crée ou ouvre un fichier de base de données
    cursor = conn.cursor()  # permet d’exécuter des commandes SQL
    cursor.execute("""
    INSERT INTO Pixels(x, y, R, G, B, tile_number, id_carte)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (x, y, R, G, B, tile_number, id_carte) )

    conn.commit()
    conn.close()


def trouver_id_carte(lat_min, lat_max, lon_min, lon_max, zoom, altitude, mode_vol):
    conn = sqlite3.connect('mes_donnes.db')
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id_carte FROM Cartes
    WHERE lat_min=? AND lat_max=? AND lon_min=? AND lon_max=?
      AND zoom=? AND altitude=? AND mode_vol=?
    ORDER BY id_carte DESC LIMIT 1
    """, (lat_min, lat_max, lon_min, lon_max, zoom, altitude, mode_vol))

    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# demande est un type text qui correspond à "select * from donnees..."
def lire_donnees(demande):
    conn = sqlite3.connect('mes_donnes.db')  # Crée ou ouvre un fichier de base de données
    cursor = conn.cursor()  # permet d’exécuter des commandes SQL

    cursor.execute(demande)
    resultats = cursor.fetchall()

    for ligne in resultats:
        print(ligne)
    conn.close() #pour fermer la connexion
