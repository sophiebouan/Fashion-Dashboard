-- =============================================================================
-- init_db.sql  —  Projet Final Algo & BDD  |  Performance Mode H&M
-- Base de données SQLite
-- =============================================================================

-- Activation des clés étrangères (SQLite)
PRAGMA foreign_keys = ON;

-- =============================================================================
-- SUPPRESSION DES TABLES (si re-exécution)
-- =============================================================================
DROP TABLE IF EXISTS rfm_scores;
DROP TABLE IF EXISTS article_product_groups;
DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS articles;
DROP TABLE IF EXISTS product_groups;
DROP TABLE IF EXISTS customers;

-- =============================================================================
-- TABLE 1 : customers — Profils clients
-- =============================================================================
CREATE TABLE customers (
    id_client       INTEGER PRIMARY KEY AUTOINCREMENT,
    age             INTEGER NOT NULL CHECK(age >= 0 AND age <= 120),
    statut_membre   VARCHAR(20) NOT NULL DEFAULT 'Active',
    pays            VARCHAR(50) NOT NULL,
    date_inscription DATE NOT NULL
);

-- =============================================================================
-- TABLE 2 : product_groups — Groupes de produits (catégories)
-- =============================================================================
CREATE TABLE product_groups (
    id_group    INTEGER PRIMARY KEY AUTOINCREMENT,
    nom_group   VARCHAR(50) NOT NULL UNIQUE,   -- contrainte UNIQUE
    description TEXT
);

-- =============================================================================
-- TABLE 3 : articles — Catalogue produits H&M
-- =============================================================================
CREATE TABLE articles (
    id_article      INTEGER PRIMARY KEY AUTOINCREMENT,
    nom             VARCHAR(100) NOT NULL,
    couleur         VARCHAR(30),
    prix            DECIMAL(8,2) NOT NULL CHECK(prix > 0),
    saison          VARCHAR(20),
    note_moyenne    DECIMAL(3,1)
);

-- =============================================================================
-- TABLE 4 : article_product_groups — TABLE DE JOINTURE many-to-many
--           Un article peut appartenir à plusieurs groupes
--           Un groupe peut contenir plusieurs articles
-- =============================================================================
CREATE TABLE article_product_groups (
    id_article  INTEGER NOT NULL,
    id_group    INTEGER NOT NULL,
    PRIMARY KEY (id_article, id_group),
    FOREIGN KEY (id_article) REFERENCES articles(id_article) ON DELETE CASCADE,
    FOREIGN KEY (id_group)   REFERENCES product_groups(id_group) ON DELETE CASCADE
);

-- =============================================================================
-- TABLE 5 : transactions — Historique des achats
-- =============================================================================
CREATE TABLE transactions (
    id_transaction  INTEGER PRIMARY KEY AUTOINCREMENT,
    id_client       INTEGER NOT NULL,
    id_article      INTEGER NOT NULL,
    date_achat      DATE NOT NULL,
    quantite        INTEGER NOT NULL CHECK(quantite > 0),
    prix_total      DECIMAL(10,2) NOT NULL,
    canal           VARCHAR(20) NOT NULL DEFAULT 'online',
    FOREIGN KEY (id_client)  REFERENCES customers(id_client),
    FOREIGN KEY (id_article) REFERENCES articles(id_article)
);

-- =============================================================================
-- TABLE 6 : rfm_scores — Résultats de l'analyse RFM (générés par pipeline.py)
-- =============================================================================
CREATE TABLE rfm_scores (
    id_client   INTEGER PRIMARY KEY,
    recence     INTEGER,       -- nb jours depuis dernier achat
    frequence   INTEGER,       -- nb de transactions
    montant     DECIMAL(10,2), -- CA total du client
    score_rfm   INTEGER,       -- score global 3-15
    segment     VARCHAR(30),   -- Champion, Fidèle, À risque…
    FOREIGN KEY (id_client) REFERENCES customers(id_client)
);

-- =============================================================================
-- VUE : vue_ventes_par_saison
-- Permet de consulter le CA et les ventes par saison facilement
-- =============================================================================
CREATE VIEW vue_ventes_par_saison AS
SELECT
    a.saison,
    COUNT(t.id_transaction) AS nb_ventes,
    SUM(t.prix_total)       AS chiffre_affaires,
    ROUND(AVG(t.prix_total), 2) AS panier_moyen
FROM transactions t
JOIN articles a ON t.id_article = a.id_article
GROUP BY a.saison;

-- =============================================================================
-- VUE : vue_top_articles
-- Top articles par chiffre d'affaires avec leur groupe principal
-- =============================================================================
CREATE VIEW vue_top_articles AS
SELECT
    a.id_article,
    a.nom,
    a.saison,
    pg.nom_group,
    COUNT(t.id_transaction) AS nb_ventes,
    ROUND(SUM(t.prix_total), 2) AS ca_total
FROM transactions t
JOIN articles a  ON t.id_article = a.id_article
LEFT JOIN article_product_groups apg ON a.id_article = apg.id_article
LEFT JOIN product_groups pg ON apg.id_group = pg.id_group
GROUP BY a.id_article, a.nom, a.saison, pg.nom_group
ORDER BY ca_total DESC;
