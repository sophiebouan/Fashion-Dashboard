-- =============================================================================
-- queries.sql  —  Projet Final Algo & BDD  |  Performance Mode H&M
-- Recueil de requêtes SQL avancées
-- =============================================================================

PRAGMA foreign_keys = ON;

-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTE 1 : WHERE + ORDER BY + LIMIT
-- Les 10 articles les plus chers de la saison Été
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    id_article,
    nom,
    couleur,
    prix
FROM articles
WHERE saison = 'Été'
ORDER BY prix DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTE 2 : GROUP BY + HAVING + ORDER BY
-- Clients ayant dépensé plus de 500€ au total, triés par dépense décroissante
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    id_client,
    COUNT(id_transaction) AS nb_achats,
    ROUND(SUM(prix_total), 2) AS depense_totale
FROM transactions
GROUP BY id_client
HAVING SUM(prix_total) > 500
ORDER BY depense_totale DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTE 3 : JOINTURE SUR 3 TABLES
-- Détail des ventes : client + article + groupe de produit
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    c.id_client,
    c.pays,
    a.nom         AS article,
    a.saison,
    pg.nom_group  AS categorie,
    t.date_achat,
    t.prix_total,
    t.canal
FROM transactions t
JOIN customers c         ON t.id_client  = c.id_client
JOIN articles a          ON t.id_article = a.id_article
JOIN article_product_groups apg ON a.id_article = apg.id_article
JOIN product_groups pg   ON apg.id_group = pg.id_group
ORDER BY t.date_achat DESC
LIMIT 50;


-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTE 4 : CTE (Common Table Expression)
-- Calcul du CA par pays avec classement (RANK simulé par ORDER BY)
-- ─────────────────────────────────────────────────────────────────────────────
WITH ca_par_pays AS (
    SELECT
        c.pays,
        COUNT(t.id_transaction) AS nb_transactions,
        ROUND(SUM(t.prix_total), 2) AS ca_total,
        COUNT(DISTINCT c.id_client) AS nb_clients
    FROM transactions t
    JOIN customers c ON t.id_client = c.id_client
    GROUP BY c.pays
)
SELECT
    pays,
    nb_transactions,
    ca_total,
    nb_clients,
    ROUND(ca_total / nb_clients, 2) AS ca_par_client
FROM ca_par_pays
ORDER BY ca_total DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTE 5 : SOUS-REQUÊTE
-- Articles dont le prix est supérieur au prix moyen de leur saison
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    a.id_article,
    a.nom,
    a.saison,
    a.prix,
    (SELECT ROUND(AVG(a2.prix), 2)
     FROM articles a2
     WHERE a2.saison = a.saison) AS prix_moyen_saison
FROM articles a
WHERE a.prix > (
    SELECT AVG(a2.prix)
    FROM articles a2
    WHERE a2.saison = a.saison
)
ORDER BY a.saison, a.prix DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTE 6 : GROUP BY + canal de vente
-- Répartition du chiffre d'affaires par canal de vente
-- ─────────────────────────────────────────────────────────────────────────────
SELECT
    canal,
    COUNT(id_transaction)     AS nb_commandes,
    ROUND(SUM(prix_total), 2) AS ca_total,
    ROUND(AVG(prix_total), 2) AS panier_moyen
FROM transactions
GROUP BY canal
ORDER BY ca_total DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTE 7 : CTE multi-étapes + analyse saisonnière avancée
-- Top groupe de produit par saison (avec CTE)
-- ─────────────────────────────────────────────────────────────────────────────
WITH ventes_groupe_saison AS (
    SELECT
        a.saison,
        pg.nom_group,
        SUM(t.prix_total)       AS ca,
        COUNT(t.id_transaction) AS nb_ventes
    FROM transactions t
    JOIN articles a ON t.id_article = a.id_article
    JOIN article_product_groups apg ON a.id_article = apg.id_article
    JOIN product_groups pg ON apg.id_group = pg.id_group
    GROUP BY a.saison, pg.nom_group
),
rang_par_saison AS (
    SELECT
        saison,
        nom_group,
        ca,
        nb_ventes,
        ROW_NUMBER() OVER (PARTITION BY saison ORDER BY ca DESC) AS rang
    FROM ventes_groupe_saison
)
SELECT saison, nom_group, ROUND(ca, 2) AS ca_total, nb_ventes
FROM rang_par_saison
WHERE rang = 1
ORDER BY saison;


-- ─────────────────────────────────────────────────────────────────────────────
-- REQUÊTE 8 : Utilisation de la VUE vue_ventes_par_saison
-- ─────────────────────────────────────────────────────────────────────────────
SELECT *
FROM vue_ventes_par_saison
ORDER BY chiffre_affaires DESC;


-- ─────────────────────────────────────────────────────────────────────────────
-- PROCÉDURE STOCKÉE (syntaxe MySQL équivalente — incluse pour documentation)
-- En SQLite, cette logique est implémentée comme fonction Python dans pipeline.py
-- ─────────────────────────────────────────────────────────────────────────────
-- DELIMITER $$
-- CREATE PROCEDURE get_top_clients_par_pays(IN p_pays VARCHAR(50), IN p_limit INT)
-- BEGIN
--     SELECT c.id_client, c.pays, SUM(t.prix_total) AS depense
--     FROM transactions t
--     JOIN customers c ON t.id_client = c.id_client
--     WHERE c.pays = p_pays
--     GROUP BY c.id_client
--     ORDER BY depense DESC
--     LIMIT p_limit;
-- END $$
-- DELIMITER ;

-- Version SQLite (vue paramétrée simulée) :
-- Appel depuis pipeline.py : get_top_clients_par_pays("France", 10)
