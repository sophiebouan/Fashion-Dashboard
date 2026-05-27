"""
dashboard.py — Projet Final Algo & BDD | Performance Mode H&M
==============================================================
Dashboard interactif Streamlit avec :
  - 3 KPIs (CA total, nb clients actifs, panier moyen)
  - 2+ graphiques Plotly
  - Filtres interactifs (saison, canal, segment RFM)
  - Callbacks réactifs via st.session_state / widgets Streamlit

Lancement : streamlit run dashboard.py
"""

import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─── Configuration de la page ─────────────────────────────────────────────────
st.set_page_config(
    page_title="H&M Fashion Analytics",
    page_icon="🛍️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── CSS personnalisé ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fond général */
    .stApp { background-color: #0f0f14; color: #f0f0f0; }
    /* Sidebar */
    [data-testid="stSidebar"] { background-color: #1a1a24; }
    /* Cartes KPI */
    .kpi-card {
        background: linear-gradient(135deg, #1e1e2e, #2a2a3e);
        border-radius: 16px;
        padding: 20px 24px;
        border: 1px solid #3a3a5c;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .kpi-label { font-size: 0.85rem; color: #9999cc; letter-spacing: 0.08em; text-transform: uppercase; }
    .kpi-value { font-size: 2.2rem; font-weight: 700; color: #c084fc; margin: 6px 0; }
    .kpi-sub   { font-size: 0.8rem; color: #6666aa; }
    /* Titre */
    .main-title { font-size: 2rem; font-weight: 800; color: #e2d9f3; }
    .sub-title  { color: #9999cc; font-size: 1rem; }
</style>
""", unsafe_allow_html=True)


# =============================================================================
# CONNEXION BASE DE DONNÉES
# =============================================================================
@st.cache_resource
def get_connection():
    """Retourne une connexion SQLite mise en cache."""
    conn = sqlite3.connect("hm_fashion.db", check_same_thread=False)
    return conn


@st.cache_data
def charger_transactions():
    conn = get_connection()
    return pd.read_sql_query("""
        SELECT t.id_transaction, t.id_client, t.date_achat,
               t.prix_total, t.quantite, t.canal,
               a.nom AS article, a.saison, a.couleur, a.prix AS prix_unitaire,
               pg.nom_group AS categorie,
               c.pays, c.statut_membre, c.age
        FROM transactions t
        JOIN articles a ON t.id_article = a.id_article
        JOIN customers c ON t.id_client = c.id_client
        LEFT JOIN article_product_groups apg ON a.id_article = apg.id_article
        LEFT JOIN product_groups pg ON apg.id_group = pg.id_group
    """, conn)


@st.cache_data
def charger_rfm():
    conn = get_connection()
    return pd.read_sql_query("SELECT * FROM rfm_scores", conn)


# =============================================================================
# CHARGEMENT DES DONNÉES
# =============================================================================
try:
    df = charger_transactions()
    df_rfm = charger_rfm()
    df["date_achat"] = pd.to_datetime(df["date_achat"])
    db_ok = True
except Exception as e:
    st.error(f"⚠️ Impossible de charger la base. Lance d'abord `pipeline.py`.\nErreur : {e}")
    st.stop()
    db_ok = False


# =============================================================================
# SIDEBAR — FILTRES INTERACTIFS
# =============================================================================
with st.sidebar:
    st.markdown("## 🎛️ Filtres")
    st.divider()

    # Filtre Saison (DROPDOWN)
    saisons_dispo = ["Toutes"] + sorted(df["saison"].dropna().unique().tolist())
    saison_sel = st.selectbox("🌸 Saison", saisons_dispo, key="filtre_saison")

    # Filtre Canal (MULTISELECT)
    canaux_dispo = sorted(df["canal"].dropna().unique().tolist())
    canaux_sel = st.multiselect("🛒 Canal de vente", canaux_dispo, default=canaux_dispo, key="filtre_canal")

    # Filtre Segment RFM (MULTISELECT)
    segments_dispo = sorted(df_rfm["segment"].dropna().unique().tolist()) if not df_rfm.empty else []
    segments_sel = st.multiselect("👤 Segment RFM", segments_dispo, default=segments_dispo, key="filtre_segment")

    # Filtre Pays (DROPDOWN)
    pays_dispo = ["Tous"] + sorted(df["pays"].dropna().unique().tolist())
    pays_sel = st.selectbox("🌍 Pays", pays_dispo, key="filtre_pays")

    st.divider()
    st.caption("Données : Synthétique H&M | API : Open-Meteo")


# =============================================================================
# APPLICATION DES FILTRES (CALLBACK RÉACTIF)
# =============================================================================
df_filtre = df.copy()

if saison_sel != "Toutes":
    df_filtre = df_filtre[df_filtre["saison"] == saison_sel]

if canaux_sel:
    df_filtre = df_filtre[df_filtre["canal"].isin(canaux_sel)]

if pays_sel != "Tous":
    df_filtre = df_filtre[df_filtre["pays"] == pays_sel]

# Filtrage par segment RFM (jointure avec rfm_scores)
if segments_sel and not df_rfm.empty:
    clients_segments = df_rfm[df_rfm["segment"].isin(segments_sel)]["id_client"].tolist()
    df_filtre = df_filtre[df_filtre["id_client"].isin(clients_segments)]


# =============================================================================
# EN-TÊTE PRINCIPAL
# =============================================================================
st.markdown('<div class="main-title">🛍️ H&M Fashion Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Dashboard de performance produits & segmentation clients</div>', unsafe_allow_html=True)
st.markdown("---")


# =============================================================================
# KPIs — 3 INDICATEURS CLÉS
# =============================================================================
col1, col2, col3, col4 = st.columns(4)

ca_total    = df_filtre["prix_total"].sum()
nb_clients  = df_filtre["id_client"].nunique()
panier_moy  = df_filtre["prix_total"].mean() if len(df_filtre) > 0 else 0
nb_articles = df_filtre["id_transaction"].nunique()

with col1:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">💰 Chiffre d'Affaires</div>
        <div class="kpi-value">{ca_total:,.0f} €</div>
        <div class="kpi-sub">{len(df_filtre):,} transactions</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">👥 Clients Actifs</div>
        <div class="kpi-value">{nb_clients:,}</div>
        <div class="kpi-sub">clients uniques</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🧺 Panier Moyen</div>
        <div class="kpi-value">{panier_moy:,.2f} €</div>
        <div class="kpi-sub">par transaction</div>
    </div>""", unsafe_allow_html=True)

with col4:
    note_moy = df_filtre["prix_unitaire"].mean() if len(df_filtre) > 0 else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-label">🏷️ Prix Unitaire Moyen</div>
        <div class="kpi-value">{note_moy:,.2f} €</div>
        <div class="kpi-sub">articles filtrés</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# =============================================================================
# GRAPHIQUE 1 : CA par Saison (Bar Chart)
# GRAPHIQUE 2 : Répartition par Canal (Donut)
# =============================================================================
col_g1, col_g2 = st.columns([3, 2])

with col_g1:
    st.markdown("#### 📊 Chiffre d'Affaires par Saison & Catégorie")
    if df_filtre.empty:
        st.info("Aucune donnée pour cette sélection.")
    else:
        df_saison_cat = (
            df_filtre.groupby(["saison", "categorie"])["prix_total"]
            .sum().reset_index()
            .sort_values("prix_total", ascending=False)
        )
        couleurs_saison = {
            "Printemps": "#a78bfa", "Été": "#f59e0b",
            "Automne": "#f97316",   "Hiver": "#60a5fa"
        }
        fig1 = px.bar(
            df_saison_cat, x="saison", y="prix_total", color="categorie",
            labels={"prix_total": "CA (€)", "saison": "Saison", "categorie": "Catégorie"},
            template="plotly_dark",
            color_discrete_sequence=px.colors.qualitative.Vivid,
        )
        fig1.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            legend=dict(orientation="h", y=-0.2),
            margin=dict(t=20, b=60),
            yaxis_tickformat=",.0f",
        )
        st.plotly_chart(fig1, use_container_width=True)

with col_g2:
    st.markdown("#### 🛒 Ventes par Canal")
    if df_filtre.empty:
        st.info("Aucune donnée.")
    else:
        df_canal = df_filtre.groupby("canal")["prix_total"].sum().reset_index()
        fig2 = px.pie(
            df_canal, values="prix_total", names="canal",
            hole=0.5, template="plotly_dark",
            color_discrete_sequence=["#c084fc", "#60a5fa", "#34d399"],
        )
        fig2.update_traces(textposition="inside", textinfo="percent+label")
        fig2.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            showlegend=True,
            legend=dict(orientation="h", y=-0.1),
            margin=dict(t=20, b=40),
        )
        st.plotly_chart(fig2, use_container_width=True)


# =============================================================================
# GRAPHIQUE 3 : Évolution mensuelle du CA (Line chart)
# GRAPHIQUE 4 : Segments RFM (Bar horizontal)
# =============================================================================
col_g3, col_g4 = st.columns([3, 2])

with col_g3:
    st.markdown("#### 📈 Évolution Mensuelle du Chiffre d'Affaires")
    if df_filtre.empty:
        st.info("Aucune donnée.")
    else:
        df_filtre["mois"] = df_filtre["date_achat"].dt.to_period("M").astype(str)
        df_mensuel = df_filtre.groupby("mois")["prix_total"].sum().reset_index()
        df_mensuel = df_mensuel.sort_values("mois")

        fig3 = px.area(
            df_mensuel, x="mois", y="prix_total",
            labels={"prix_total": "CA (€)", "mois": "Mois"},
            template="plotly_dark",
            color_discrete_sequence=["#c084fc"],
        )
        fig3.update_traces(fill="tozeroy", line_color="#c084fc", fillcolor="rgba(192,132,252,0.15)")
        fig3.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(tickangle=45, tickfont=dict(size=10)),
            yaxis_tickformat=",.0f",
            margin=dict(t=20, b=80),
        )
        st.plotly_chart(fig3, use_container_width=True)

with col_g4:
    st.markdown("#### 👤 Segmentation Clients RFM")
    if df_rfm.empty:
        st.info("Lance pipeline.py pour générer les scores RFM.")
    else:
        df_rfm_filtre = df_rfm.copy()
        if segments_sel:
            df_rfm_filtre = df_rfm_filtre[df_rfm_filtre["segment"].isin(segments_sel)]

        df_seg = df_rfm_filtre.groupby("segment")["id_client"].count().reset_index()
        df_seg.columns = ["segment", "nb_clients"]
        df_seg = df_seg.sort_values("nb_clients", ascending=True)

        couleurs_seg = {
            "Champion": "#a78bfa", "Fidèle": "#60a5fa",
            "Potentiel": "#34d399", "À risque": "#f59e0b", "Inactif": "#f87171"
        }
        df_seg["couleur"] = df_seg["segment"].map(couleurs_seg).fillna("#9999cc")

        fig4 = px.bar(
            df_seg, x="nb_clients", y="segment", orientation="h",
            labels={"nb_clients": "Nb clients", "segment": "Segment"},
            template="plotly_dark",
            color="segment",
            color_discrete_map=couleurs_seg,
        )
        fig4.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
            showlegend=False,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig4, use_container_width=True)


# =============================================================================
# GRAPHIQUE 5 : Top 10 Catégories par CA
# =============================================================================
st.markdown("#### 🏆 Top 10 Catégories par Chiffre d'Affaires")
if not df_filtre.empty:
    df_cat = (
        df_filtre.groupby("categorie")["prix_total"]
        .sum().reset_index()
        .sort_values("prix_total", ascending=False)
        .head(10)
    )
    fig5 = px.bar(
        df_cat, x="categorie", y="prix_total",
        labels={"prix_total": "CA (€)", "categorie": "Catégorie"},
        template="plotly_dark",
        color="prix_total",
        color_continuous_scale="Purples",
    )
    fig5.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        coloraxis_showscale=False,
        margin=dict(t=20),
        yaxis_tickformat=",.0f",
    )
    st.plotly_chart(fig5, use_container_width=True)

st.divider()
st.caption("🛍️ H&M Fashion Analytics · Projet Algo & BDD · Données synthétiques · API Open-Meteo")
