"""
pipeline.py — Projet Final Algo & BDD | Performance Mode H&M
=============================================================
Ce script :
  1. Initialise la base SQLite et charge les données CSV
  2. Appelle l'API Open-Meteo (météo historique) pour enrichir les transactions
  3. Applique l'algorithme RFM (Récence, Fréquence, Montant)
  4. Insère les scores RFM dans la table rfm_scores
  5. Simule une procédure stockée get_top_clients_par_pays()
"""

import sqlite3
import csv
import os
import requests
import pandas as pd
from datetime import date

# ─── Configuration ────────────────────────────────────────────────────────────
DB_PATH   = "hm_fashion.db"
SQL_INIT  = "init_db.sql"
DATA_DIR  = "data"

# Date de référence pour le calcul de récence RFM
DATE_REF  = date(2024, 1, 1)


# =============================================================================
# FONCTION 1 : Initialisation de la base de données
# =============================================================================
def initialiser_base(db_path: str, sql_path: str) -> sqlite3.Connection:
    """
    Crée la base SQLite, exécute le script init_db.sql
    et retourne la connexion.
    """
    print("📂 Initialisation de la base de données...")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    with open(sql_path, "r", encoding="utf-8") as f:
        script = f.read()

    # On filtre les commentaires de style -- pour éviter les erreurs
    conn.executescript(script)
    conn.commit()
    print(f"   ✅ Base '{db_path}' créée avec succès.")
    return conn


# =============================================================================
# FONCTION 2 : Chargement des CSV dans la base
# =============================================================================
def charger_csv_dans_base(conn: sqlite3.Connection, data_dir: str) -> None:
    """
    Lit les fichiers CSV du dossier data/ et les insère dans la base SQLite.
    """
    print("\n📥 Chargement des données CSV...")
    cur = conn.cursor()

    # ── Clients ──────────────────────────────────────────────────────────────
    with open(os.path.join(data_dir, "customers.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cur.executemany(
        "INSERT INTO customers (id_client, age, statut_membre, pays, date_inscription) VALUES (?,?,?,?,?)",
        [(r["id_client"], r["age"], r["statut_membre"], r["pays"], r["date_inscription"]) for r in rows]
    )
    print(f"   ✅ {len(rows)} clients insérés.")

    # ── Groupes de produits ───────────────────────────────────────────────────
    with open(os.path.join(data_dir, "product_groups.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cur.executemany(
        "INSERT INTO product_groups (id_group, nom_group, description) VALUES (?,?,?)",
        [(r["id_group"], r["nom_group"], r["description"]) for r in rows]
    )
    print(f"   ✅ {len(rows)} groupes de produits insérés.")

    # ── Articles ──────────────────────────────────────────────────────────────
    with open(os.path.join(data_dir, "articles.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cur.executemany(
        "INSERT INTO articles (id_article, nom, couleur, prix, saison, note_moyenne) VALUES (?,?,?,?,?,?)",
        [(r["id_article"], r["nom"], r["couleur"], r["prix"], r["saison"], r["note_moyenne"]) for r in rows]
    )
    print(f"   ✅ {len(rows)} articles insérés.")

    # ── Liaisons article ↔ groupe (many-to-many) ──────────────────────────────
    with open(os.path.join(data_dir, "article_product_groups.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cur.executemany(
        "INSERT INTO article_product_groups (id_article, id_group) VALUES (?,?)",
        [(r["id_article"], r["id_group"]) for r in rows]
    )
    print(f"   ✅ {len(rows)} liaisons article-groupe insérées.")

    # ── Transactions ──────────────────────────────────────────────────────────
    with open(os.path.join(data_dir, "transactions.csv"), newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    cur.executemany(
        "INSERT INTO transactions (id_transaction, id_client, id_article, date_achat, quantite, prix_total, canal) VALUES (?,?,?,?,?,?,?)",
        [(r["id_transaction"], r["id_client"], r["id_article"],
          r["date_achat"], r["quantite"], r["prix_total"], r["canal"]) for r in rows]
    )
    print(f"   ✅ {len(rows)} transactions insérées.")

    conn.commit()


# =============================================================================
# FONCTION 3 : Appel API Open-Meteo — météo historique mensuelle (Paris)
# =============================================================================
def get_meteo_par_mois() -> dict:
    """
    Appelle l'API Open-Meteo pour récupérer les températures moyennes mensuelles
    à Paris (2020-2023). Retourne un dict {(annee, mois): temp_moyenne}.
    API gratuite, sans clé, cf. https://open-meteo.com/
    """
    print("\n🌤️  Appel API Open-Meteo (météo Paris 2020-2023)...")
    url = (
        "https://archive-api.open-meteo.com/v1/archive"
        "?latitude=48.8566&longitude=2.3522"
        "&start_date=2020-01-01&end_date=2023-12-31"
        "&daily=temperature_2m_mean"
        "&timezone=Europe/Paris"
    )
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        df_meteo = pd.DataFrame({
            "date":  pd.to_datetime(data["daily"]["time"]),
            "temp":  data["daily"]["temperature_2m_mean"]
        })
        df_meteo["annee"] = df_meteo["date"].dt.year
        df_meteo["mois"]  = df_meteo["date"].dt.month

        meteo_mois = (
            df_meteo.groupby(["annee", "mois"])["temp"]
            .mean()
            .round(1)
            .to_dict()
        )
        print(f"   ✅ {len(meteo_mois)} mois de données météo récupérés.")
        return meteo_mois

    except Exception as e:
        print(f"   ⚠️  API indisponible ({e}). Utilisation de valeurs par défaut.")
        # Valeurs de secours si l'API est inaccessible
        return {(a, m): [3, 4, 8, 12, 17, 21, 23, 22, 18, 13, 7, 4][m-1]
                for a in range(2020, 2024) for m in range(1, 13)}


# =============================================================================
# FONCTION 4 : Algorithme RFM — Récence, Fréquence, Montant
# =============================================================================
def calculer_rfm(df_transactions: pd.DataFrame, date_ref: date) -> pd.DataFrame:
    """
    Calcule les scores RFM pour chaque client.

    Paramètres :
        df_transactions (pd.DataFrame) : DataFrame des transactions
        date_ref (date)                : Date de référence pour la récence

    Retourne :
        pd.DataFrame avec colonnes [id_client, recence, frequence, montant,
                                    score_r, score_f, score_m, score_rfm, segment]
    """
    print("\n🧮 Calcul de l'algorithme RFM...")

    df_transactions["date_achat"] = pd.to_datetime(df_transactions["date_achat"])
    date_ref_ts = pd.Timestamp(date_ref)

    # Agrégation par client
    rfm = df_transactions.groupby("id_client").agg(
        recence   = ("date_achat", lambda x: (date_ref_ts - x.max()).days),
        frequence = ("id_transaction", "count"),
        montant   = ("prix_total", "sum")
    ).reset_index()

    # Scoring en quintiles (1 à 5)
    rfm["score_r"] = pd.qcut(rfm["recence"],   q=5, labels=[5, 4, 3, 2, 1]).astype(int)
    rfm["score_f"] = pd.qcut(rfm["frequence"].rank(method="first"), q=5, labels=[1, 2, 3, 4, 5]).astype(int)
    rfm["score_m"] = pd.qcut(rfm["montant"].rank(method="first"),   q=5, labels=[1, 2, 3, 4, 5]).astype(int)

    rfm["score_rfm"] = rfm["score_r"] + rfm["score_f"] + rfm["score_m"]

    # Segmentation métier
    def segmenter(row):
        if row["score_rfm"] >= 13:
            return "Champion"
        elif row["score_rfm"] >= 10:
            return "Fidèle"
        elif row["score_rfm"] >= 7:
            return "Potentiel"
        elif row["score_rfm"] >= 5:
            return "À risque"
        else:
            return "Inactif"

    rfm["segment"]  = rfm.apply(segmenter, axis=1)
    rfm["montant"]  = rfm["montant"].round(2)
    print(f"   ✅ RFM calculé pour {len(rfm)} clients.")
    print(rfm["segment"].value_counts().to_string())
    return rfm


# =============================================================================
# FONCTION 5 : Insertion des scores RFM dans la base
# =============================================================================
def inserer_rfm(conn: sqlite3.Connection, df_rfm: pd.DataFrame) -> None:
    """
    Insère le DataFrame rfm_scores dans la table SQLite rfm_scores.
    """
    print("\n💾 Insertion des scores RFM dans la base...")
    cur = conn.cursor()
    cur.execute("DELETE FROM rfm_scores")  # On vide avant réinsertion

    for _, row in df_rfm.iterrows():
        cur.execute(
            """INSERT INTO rfm_scores
               (id_client, recence, frequence, montant, score_rfm, segment)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (int(row["id_client"]), int(row["recence"]), int(row["frequence"]),
             float(row["montant"]), int(row["score_rfm"]), row["segment"])
        )
    conn.commit()
    print(f"   ✅ {len(df_rfm)} scores RFM insérés dans la table rfm_scores.")


# =============================================================================
# PROCÉDURE STOCKÉE SIMULÉE : get_top_clients_par_pays
# Équivalent Python d'une procédure stockée MySQL
# =============================================================================
def get_top_clients_par_pays(conn: sqlite3.Connection, pays: str, limit: int = 10) -> pd.DataFrame:
    """
    Retourne les top clients par chiffre d'affaires pour un pays donné.
    Simule une procédure stockée MySQL (non supportée nativement par SQLite).

    Paramètres :
        conn   : connexion SQLite
        pays   : pays à filtrer (ex: "France")
        limit  : nombre de résultats (défaut 10)
    """
    query = """
        SELECT c.id_client, c.pays, c.statut_membre,
               SUM(t.prix_total) AS depense_totale,
               COUNT(t.id_transaction) AS nb_achats
        FROM transactions t
        JOIN customers c ON t.id_client = c.id_client
        WHERE c.pays = ?
        GROUP BY c.id_client
        ORDER BY depense_totale DESC
        LIMIT ?
    """
    return pd.read_sql_query(query, conn, params=(pays, limit))


# =============================================================================
# POINT D'ENTRÉE PRINCIPAL
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print(" PIPELINE H&M — Analyse Performance Produits & Mode")
    print("=" * 60)

    # Étape 1 : Initialisation
    conn = initialiser_base(DB_PATH, SQL_INIT)

    # Étape 2 : Chargement des données
    charger_csv_dans_base(conn, DATA_DIR)

    # Étape 3 : Enrichissement météo via API
    meteo = get_meteo_par_mois()
    # Affichage d'un aperçu
    print(f"\n   Exemple — Température Paris Jan 2022 : {meteo.get((2022, 1), 'N/A')}°C")

    # Étape 4 : Chargement transactions dans Pandas
    df_tx = pd.read_sql_query(
        "SELECT id_transaction, id_client, date_achat, prix_total FROM transactions",
        conn
    )

    # Enrichissement : ajout de la température moyenne du mois de la transaction
    df_tx["date_achat"] = pd.to_datetime(df_tx["date_achat"])
    df_tx["annee"] = df_tx["date_achat"].dt.year
    df_tx["mois"]  = df_tx["date_achat"].dt.month
    df_tx["temp_mois"] = df_tx.apply(
        lambda r: meteo.get((r["annee"], r["mois"]), None), axis=1
    )
    print(f"\n🌡️  Enrichissement météo appliqué — aperçu :")
    print(df_tx[["id_transaction", "date_achat", "temp_mois"]].head(5).to_string(index=False))

    # Étape 5 : Algorithme RFM
    df_rfm = calculer_rfm(df_tx, DATE_REF)

    # Étape 6 : Insertion RFM en base
    inserer_rfm(conn, df_rfm)

    # Étape 7 : Démonstration de la procédure stockée simulée
    print("\n📋 Top 5 clients — France :")
    top_fr = get_top_clients_par_pays(conn, "France", limit=5)
    print(top_fr.to_string(index=False))

    conn.close()
    print("\n" + "=" * 60)
    print(" ✅ Pipeline terminé ! Base prête pour le dashboard.")
    print("=" * 60)
