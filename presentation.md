# 🎤 Script de Soutenance — H&M Fashion Analytics

> **Durée estimée** : 5 à 7 minutes  
> **Format** : Distanciel — partage d'écran recommandé

---

## 1️⃣ La Problématique Métier *(~1 min)*

> *"Bonjour, mon projet s'intitule **H&M Fashion Analytics**. Il s'agit d'une analyse de performance produits et de segmentation clients dans le secteur de la mode, inspirée du dataset réel d'H&M."*

> *"La problématique métier est la suivante : **quels types d'articles performent le mieux selon les profils clients et les saisons ?** Et comment identifier les clients à fort potentiel commercial grâce à des algorithmes de scoring ?"*

> *"Pour répondre à cette question, j'ai construit un pipeline complet : de la modélisation de la base de données jusqu'à un dashboard interactif, en passant par un algorithme de segmentation client appelé **RFM**."*

---

## 2️⃣ Schéma de la Base & Choix de Modélisation *(~2 min)*

> *"Voici le schéma de ma base de données — je vous invite à regarder le diagramme sur dbdiagram.io."*

**Expliquer les 6 tables :**

- **`customers`** : contient les profils clients — age, pays, statut membre. C'est la table centrale côté client.
- **`articles`** : le catalogue produits — nom, couleur, prix, saison. C'est la table centrale côté produit.
- **`transactions`** : c'est le cœur du système. Elle relie chaque client à chaque article acheté, avec la date, la quantité, le montant et le canal (online, magasin, application).
- **`product_groups`** : les catégories de produits (Tops, Bottoms, Outerwear…)
- **`article_product_groups`** : c'est ma **table de jointure many-to-many**. Un article peut appartenir à plusieurs catégories, et une catégorie contient de nombreux articles. C'est un cas classique de relation plusieurs-à-plusieurs.
- **`rfm_scores`** : générée par mon pipeline Python. Elle stocke le résultat de l'algorithme RFM pour chaque client.

> *"J'ai respecté toutes les contraintes : clés étrangères, contraintes NOT NULL et UNIQUE sur les noms de catégories, et j'ai créé deux vues SQL pour faciliter les requêtes métier."*

---

## 3️⃣ Démo du Dashboard *(~2 min)*

> *"Je vais maintenant vous montrer le dashboard interactif. Pour le lancer, j'utilise la commande `streamlit run dashboard.py`."*

**Guide étape par étape :**

1. **Montrer les KPIs en haut** :
   > *"En haut de la page, vous voyez 4 indicateurs clés : le chiffre d'affaires total, le nombre de clients actifs, le panier moyen et le prix unitaire moyen."*

2. **Utiliser le filtre Saison** (sidebar gauche) :
   > *"Je vais filtrer sur la saison **Été**. Observez comment tous les graphiques se mettent à jour instantanément — c'est le mécanisme réactif de Streamlit."*

3. **Montrer le graphique CA par saison/catégorie** :
   > *"Ce graphique empilé montre le chiffre d'affaires par saison, décomposé par catégorie de produit. On voit que certaines catégories comme Outerwear dominent en Hiver."*

4. **Montrer le donut canal** :
   > *"Le donut montre la répartition des ventes par canal. On constate que le canal online représente environ un tiers des ventes."*

5. **Montrer la courbe d'évolution mensuelle** :
   > *"Cette courbe montre l'évolution mensuelle du CA — on peut identifier des pics saisonniers."*

6. **Montrer la segmentation RFM** :
   > *"Enfin, ce graphique représente la distribution des segments clients. Les **Champions** sont nos meilleurs clients — ils achètent souvent, beaucoup, et récemment."*

---

## 4️⃣ Code Intéressant *(~1.5 min)*

### Requête SQL — CTE multi-étapes (queries.sql, Requête 7)

> *"Voici la requête SQL dont je suis le plus fier. Elle utilise deux CTEs enchaînées."*

```sql
-- Étape 1 : on agrège les ventes par groupe de produit ET par saison
WITH ventes_groupe_saison AS (
    SELECT a.saison, pg.nom_group,
           SUM(t.prix_total) AS ca,
           COUNT(t.id_transaction) AS nb_ventes
    FROM transactions t
    JOIN articles a ON t.id_article = a.id_article
    JOIN article_product_groups apg ON a.id_article = apg.id_article
    JOIN product_groups pg ON apg.id_group = pg.id_group
    GROUP BY a.saison, pg.nom_group
),
-- Étape 2 : on classe les groupes au sein de chaque saison
rang_par_saison AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY saison ORDER BY ca DESC) AS rang
    FROM ventes_groupe_saison
)
-- Résultat : seulement le top 1 par saison
SELECT saison, nom_group, ca, nb_ventes
FROM rang_par_saison WHERE rang = 1;
```

> *"Cette requête joint **4 tables**, utilise un **CTE en deux étapes** et une **fonction de fenêtrage ROW_NUMBER** pour isoler le meilleur groupe par saison — sans sous-requête corrélée."*

---

### Algorithme Python — Score RFM (pipeline.py)

> *"Du côté Python, le cœur de mon pipeline est l'algorithme RFM. Voici comment il fonctionne en 3 étapes :"*

```python
# 1. Agrégation par client
rfm = df_transactions.groupby("id_client").agg(
    recence   = ("date_achat", lambda x: (date_ref - x.max()).days),
    frequence = ("id_transaction", "count"),
    montant   = ("prix_total", "sum")
)

# 2. Scoring en quintiles (1 à 5 pour chaque dimension)
rfm["score_r"] = pd.qcut(rfm["recence"], q=5, labels=[5,4,3,2,1])
rfm["score_f"] = pd.qcut(rfm["frequence"].rank(), q=5, labels=[1,2,3,4,5])
rfm["score_m"] = pd.qcut(rfm["montant"].rank(),   q=5, labels=[1,2,3,4,5])
rfm["score_rfm"] = rfm["score_r"] + rfm["score_f"] + rfm["score_m"]

# 3. Segmentation métier selon le score total (3 à 15)
# Champion (≥13), Fidèle (≥10), Potentiel (≥7), À risque (≥5), Inactif
```

> *"L'enrichissement API est aussi notable : j'appelle l'API Open-Meteo pour récupérer les températures mensuelles à Paris, et je les associe à chaque transaction selon son mois d'achat — sans aucune clé API requise."*

---

## ✅ Conclusion

> *"Pour résumer : j'ai modélisé une base de données relationnelle en 6 tables avec des relations many-to-many, j'ai écrit 8 requêtes SQL avancées, développé un pipeline Python qui intègre une API externe et un algorithme de segmentation, et construit un dashboard interactif. Merci de votre attention, je suis disponible pour vos questions."*
