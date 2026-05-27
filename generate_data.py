"""
generate_data.py
Script de génération de données synthétiques H&M
Génère les fichiers CSV dans le dossier data/
"""

import csv
import random
from datetime import date, timedelta

random.seed(42)

# ─── Paramètres ──────────────────────────────────────────────────────────────
NB_CLIENTS     = 800
NB_ARTICLES    = 300
NB_TRANSACTIONS = 5000

PAYS = ["France", "Allemagne", "Espagne", "Italie", "Suède", "Pays-Bas"]
STATUTS = ["Active", "Pre-Active", "Left Club"]
CANAUX = ["online", "magasin", "application"]
SAISONS = ["Printemps", "Été", "Automne", "Hiver"]
COULEURS = ["Noir", "Blanc", "Bleu", "Rouge", "Vert", "Beige", "Gris", "Rose", "Jaune", "Marron"]

GROUPES = [
    ("Tops", "Hauts et t-shirts"),
    ("Bottoms", "Pantalons et jupes"),
    ("Robes", "Robes et combinaisons"),
    ("Outerwear", "Vestes et manteaux"),
    ("Accessories", "Accessoires divers"),
    ("Footwear", "Chaussures"),
    ("Underwear", "Sous-vêtements et lingerie"),
    ("Sportswear", "Vêtements de sport"),
    ("Nightwear", "Pyjamas et vêtements de nuit"),
    ("Kids", "Vêtements enfants"),
]

NOMS_ARTICLES = [
    "T-shirt basique", "Jean slim", "Robe fleurie", "Veste en cuir",
    "Pull en laine", "Short en jean", "Chemise à carreaux", "Cardigan",
    "Manteau long", "Legging sport", "Blouse légère", "Blazer structuré",
    "Jupe midi", "Parka imperméable", "Sweatshirt capuche", "Top bandeau",
    "Pantalon chino", "Robe portefeuille", "Gilet sans manches", "Trench-coat",
    "Body", "Salopette", "Combinaison", "Débardeur", "Polo",
    "Jogging", "Anorak", "Kimono", "Tunique", "Mini-jupe",
]


def date_aleatoire(debut: date, fin: date) -> date:
    """Retourne une date aléatoire entre debut et fin."""
    delta = (fin - debut).days
    return debut + timedelta(days=random.randint(0, delta))


# ─── Génération des clients ───────────────────────────────────────────────────
clients = []
for i in range(1, NB_CLIENTS + 1):
    clients.append({
        "id_client": i,
        "age": random.randint(18, 75),
        "statut_membre": random.choice(STATUTS),
        "pays": random.choice(PAYS),
        "date_inscription": date_aleatoire(date(2018, 1, 1), date(2022, 12, 31)).isoformat(),
    })

with open("data/customers.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=clients[0].keys())
    writer.writeheader()
    writer.writerows(clients)

print(f"✅ {NB_CLIENTS} clients générés → data/customers.csv")


# ─── Génération des articles ──────────────────────────────────────────────────
articles = []
for i in range(1, NB_ARTICLES + 1):
    nom_base = random.choice(NOMS_ARTICLES)
    couleur   = random.choice(COULEURS)
    saison    = random.choice(SAISONS)
    prix      = round(random.uniform(9.99, 149.99), 2)
    note      = round(random.uniform(2.5, 5.0), 1)
    articles.append({
        "id_article": i,
        "nom": f"{nom_base} {couleur}",
        "couleur": couleur,
        "prix": prix,
        "saison": saison,
        "note_moyenne": note,
    })

with open("data/articles.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=articles[0].keys())
    writer.writeheader()
    writer.writerows(articles)

print(f"✅ {NB_ARTICLES} articles générés → data/articles.csv")


# ─── Génération des transactions ──────────────────────────────────────────────
transactions = []
for i in range(1, NB_TRANSACTIONS + 1):
    client  = random.choice(clients)
    article = random.choice(articles)
    qte     = random.randint(1, 4)
    transactions.append({
        "id_transaction": i,
        "id_client": client["id_client"],
        "id_article": article["id_article"],
        "date_achat": date_aleatoire(date(2020, 1, 1), date(2023, 12, 31)).isoformat(),
        "quantite": qte,
        "prix_total": round(article["prix"] * qte, 2),
        "canal": random.choice(CANAUX),
    })

with open("data/transactions.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
    writer.writeheader()
    writer.writerows(transactions)

print(f"✅ {NB_TRANSACTIONS} transactions générées → data/transactions.csv")

# ─── Génération des groupes de produits ──────────────────────────────────────
with open("data/product_groups.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id_group", "nom_group", "description"])
    writer.writeheader()
    for idx, (nom, desc) in enumerate(GROUPES, start=1):
        writer.writerow({"id_group": idx, "nom_group": nom, "description": desc})

print(f"✅ {len(GROUPES)} groupes de produits → data/product_groups.csv")

# ─── Génération des liaisons article ↔ groupe (many-to-many) ─────────────────
liens = set()
for article in articles:
    # Chaque article appartient à 1 ou 2 groupes
    groupes_choisis = random.sample(range(1, len(GROUPES) + 1), k=random.randint(1, 2))
    for g in groupes_choisis:
        liens.add((article["id_article"], g))

with open("data/article_product_groups.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["id_article", "id_group"])
    writer.writeheader()
    for (art, grp) in sorted(liens):
        writer.writerow({"id_article": art, "id_group": grp})

print(f"✅ {len(liens)} liaisons article-groupe → data/article_product_groups.csv")
print("\n🎉 Génération des données terminée !")
