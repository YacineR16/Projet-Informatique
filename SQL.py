import sqlite3

def tableau_SQL():
    conn = sqlite3.connect('mes_donnes.db')  # Crée ou ouvre un fichier de base de données
    cursor = conn.cursor() #permet d’exécuter des commandes SQL

    #méthode utilisée pour envoyer une requête SQL à la base
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS donnees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zoom REAL,
        x_tuile REAL,
        y_tuile REAL,
        rouge_moyenne REAL
        vert_moyenne REAL,
        bleu_moyenne REAL,
        ref_point_interet REAL
    )
    """)
    conn.commit()

def inserer_donnees(z,x,y,r,g,b,ref_pi):
    conn = sqlite3.connect('mes_donnes.db')  # Crée ou ouvre un fichier de base de données
    cursor = conn.cursor()  # permet d’exécuter des commandes SQL

    cursor.execute("""
    INSERT INTO donnees (zoom,x_tuile,y_tuile,rouge_moyenne,vert_moyenne,bleu_moyenne,ref_point_interet) VALUES (?, ?, ?,?,?,?,?)
    """, (z, x, y,r,g,b,ref_pi))
    conn.commit()


# demande est un type text qui correspond à "select * from donnees..."
def lire_donnees(demande):
    conn = sqlite3.connect('mes_donnes.db')  # Crée ou ouvre un fichier de base de données
    cursor = conn.cursor()  # permet d’exécuter des commandes SQL

    cursor.execute(demande)
    resultats = cursor.fetchall()

    for ligne in resultats:
        print(ligne)



#conn.close() pour fermer la connexion

