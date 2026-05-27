# 🛍️ H&M Fashion Analytics — Projet Final Algo & BDD

> **Problématique métier** : Quels types d'articles performent le mieux selon les profils clients et les saisons ? Comment identifier les clients à fort potentiel grâce à l'analyse RFM ?

![Schéma BDD](schema_dbdiagram.png)
*(Remplace cette ligne par une capture d'écran de ton schéma sur dbdiagram.io)*

---

## 📋 Sommaire

1. [Contexte & Données](#contexte)
2. [Architecture du projet](#architecture)
3. [Installation](#installation)
4. [Lancement](#lancement)
5. [Schéma de la base de données](#schema)
6. [Pipeline Python](#pipeline)
7. [Dashboard](#dashboard)

---

## 📦 Contexte & Données <a name="contexte"></a>

Ce projet analyse les **performances produits et la segmentation clients** d'un retailer de mode inspiré du dataset H&M (Kaggle).

Les données sont **synthétiques** mais réalistes, générées avec `generate_data.py` :

| Fichier | Description | Volume |
|---|---|---|
| `customers.csv` | Profils clients (age, pays, statut) | 800 clients |
| `articles.csv` | Catalogue produits (couleur, prix, saison) | 300 articles |
| `transactions.csv` | Historique d'achats | 5 000 transactions |
| `product_groups.csv` | Catégories de produits | 10 groupes |

---

## 🗂️ Architecture du projet <a name="architecture"></a>

```
hm_project/
├── data/                      ← Données CSV générées
├── generate_data.py           ← Génération des données synthétiques
├── init_db.sql                ← Schéma BDD (6 tables, 2 vues)
├── queries.sql                ← 8 requêtes SQL avancées
├── pipeline.py                ← ETL + API météo + algorithme RFM
├── dashboard.py               ← Dashboard Streamlit interactif
├── requirements.txt           ← Dépendances Python
├── .gitignore
└── README.md
```

---

## ⚙️ Installation <a name="installation"></a>

```bash
# Cloner le projet
git clone <url-du-repo>
cd hm_project

# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Mac/Linux

# Installer les dépendances
pip install -r requirements.txt
```

---

## 🚀 Lancement <a name="lancement"></a>

**Étape 1 — Générer les données :**
```bash
python3 generate_data.py
```

**Étape 2 — Lancer le pipeline (création BDD + RFM + API) :**
```bash
python3 pipeline.py
```

**Étape 3 — Lancer le dashboard :**
```bash
streamlit run dashboard.py
```

Ouvre ensuite http://localhost:8501 dans ton navigateur.

---

## 🗄️ Schéma de la base de données <a name="schema"></a>

La base contient **6 tables** :

```
customers ──────────┐
                    ↓
                transactions ←── articles ──────────────────┐
                                    ↑                       │
                              article_product_groups        │
                                    ↓                       │
                              product_groups                │
                                                            │
rfm_scores ←── (calculé par pipeline.py depuis customers)  │
```

### Relations clés
- **many-to-many** : `articles` ↔ `product_groups` via `article_product_groups`
- **one-to-many** : `customers` → `transactions`
- **one-to-many** : `articles` → `transactions`

### Code DBML (à coller sur [dbdiagram.io](https://dbdiagram.io/d))

```dbml
Table customers {
  id_client       integer [pk, increment]
  age             integer [not null]
  statut_membre   varchar [not null]
  pays            varchar [not null]
  date_inscription date [not null]
}

Table product_groups {
  id_group    integer [pk, increment]
  nom_group   varchar [not null, unique]
  description text
}

Table articles {
  id_article   integer [pk, increment]
  nom          varchar [not null]
  couleur      varchar
  prix         decimal [not null]
  saison       varchar
  note_moyenne decimal
}

Table article_product_groups {
  id_article integer [ref: > articles.id_article]
  id_group   integer [ref: > product_groups.id_group]
  indexes { (id_article, id_group) [pk] }
}

Table transactions {
  id_transaction integer [pk, increment]
  id_client      integer [ref: > customers.id_client]
  id_article     integer [ref: > articles.id_article]
  date_achat     date [not null]
  quantite       integer [not null]
  prix_total     decimal [not null]
  canal          varchar [not null]
}

Table rfm_scores {
  id_client  integer [pk, ref: > customers.id_client]
  recence    integer
  frequence  integer
  montant    decimal
  score_rfm  integer
  segment    varchar
}
```

---

## 🐍 Pipeline Python <a name="pipeline"></a>

Le script `pipeline.py` réalise 4 opérations :

1. **Initialisation BDD** — Exécute `init_db.sql` via SQLite
2. **Chargement des CSV** — Insère les données dans les tables
3. **Appel API Open-Meteo** — Récupère les températures moyennes mensuelles à Paris (2020-2023) pour enrichir les transactions
4. **Algorithme RFM** — Segmente les clients en 5 catégories :

| Segment | Description | Score RFM |
|---|---|---|
| 🏆 Champion | Achète souvent, récemment, gros panier | 13-15 |
| 💚 Fidèle | Client régulier à fort potentiel | 10-12 |
| 🔵 Potentiel | Bon comportement, à fidéliser | 7-9 |
| ⚠️ À risque | N'a plus acheté depuis longtemps | 5-6 |
| 😴 Inactif | Inactif, difficile à réactiver | 3-4 |

---

## 📊 Dashboard <a name="dashboard"></a>

Le dashboard Streamlit propose :

- **4 KPIs** : CA total, clients actifs, panier moyen, prix unitaire moyen
- **5 graphiques** : CA par saison/catégorie, répartition canal, évolution mensuelle, segments RFM, top catégories
- **4 filtres interactifs** : saison, canal de vente, segment RFM, pays

---

## 👥 Auteur

Projet réalisé dans le cadre du cours **Algorithmes & Bases de Données**.
