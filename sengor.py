# -*- coding: utf-8 -*-
"""
==============================================================================
 SiteLab - Collecte, analyse et gestion des données d'un chantier de BÂTIMENT
           avec SOUS-SOL (terrassement, soutènement, nappe, béton, planning)
==============================================================================
 Installation :   pip install streamlit pandas numpy plotly
 Lancement    :   streamlit run main.py

 Modules :
   1. Tableau de bord        (KPI, courbe en S, points d'attention)
   2. Projet & sous-sol      (paramètres, poussée des terres, soulèvement
                              hydraulique, volumes de terrassement, coupe)
   3. Collecte des données   (auscultation, béton, terrassement, avancement)
   4. Auscultation           (séries, seuils, anomalies, corrélations)
   5. Contrôle du béton      (conformité EN 206 simplifiée, prévision à 28 j)
   6. Avancement & coûts     (valeur acquise SPI/CPI, Gantt, courbe en S)
   7. Qualité & sécurité     (registre des non-conformités)
   8. Rapport & export

 NB : outil d'aide au suivi et de pré-vérification. Toute décision de chantier
 doit être validée par un ingénieur qualifié, selon les normes en vigueur.
==============================================================================
"""
import math
import re
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import streamlit as st

# Import de plotly tolérant au déploiement : si le serveur n'a pas installé
# plotly (requirements.txt ignoré, mal placé ou mal encodé), on l'installe
# automatiquement au premier lancement puis on réessaie.
try:
    import plotly.graph_objects as go
except ModuleNotFoundError:
    import subprocess
    import sys

    import plotly.graph_objects as go

st.set_page_config(
    page_title="SiteLab - Suivi de chantier",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =============================================================================
# 1. STYLE PROFESSIONNEL (clair, sobre, interactif)
# =============================================================================
NAVY, BLUE, TEAL, AMBER, RED, GREEN, GREY = (
    "#0f2a43", "#1f4e79", "#2a9d8f", "#e9a23b", "#c0392b", "#2e7d32", "#6c7a89")
PALETTE = [BLUE, TEAL, AMBER, "#8e6c8a", "#3d85c6", "#7a9e3b", RED, GREY]

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

@keyframes fadeUp { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes heroShift { 0% { background-position: 0% 50%; } 100% { background-position: 100% 50%; } }
@keyframes growBar { from { width: 0; } to { width: var(--w); } }
@keyframes pulseDot { 0%,100% { box-shadow: 0 0 0 0 rgba(192,57,43,.45); } 50% { box-shadow: 0 0 0 6px rgba(192,57,43,0); } }

.stApp { background: #f3f5f8; color: #1f2937; }
.block-container { padding-top: 1.6rem; animation: fadeUp .5s ease both; }
header[data-testid="stHeader"] { background: transparent; }
h1, h2, h3, h4, h5 { color: #0f2a43 !important; font-weight: 600 !important; letter-spacing: -.01em; }
[data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li { color: #1f2937; }
[data-testid="stWidgetLabel"] p { color: #334155 !important; font-weight: 500; }
[data-testid="stCaptionContainer"] { color: #64748b !important; }

/* Barre latérale */
[data-testid="stSidebar"] { background: linear-gradient(185deg, #0f2a43 0%, #14395a 100%); }
[data-testid="stSidebar"] * { color: #e8eef5; }
[data-testid="stSidebar"] [data-testid="stWidgetLabel"] p { color: #aebfd0 !important; }
[data-testid="stSidebar"] .stTextInput input { background: rgba(255,255,255,.08) !important; color: #fff !important;
  border: 1px solid rgba(255,255,255,.18) !important; }
[data-testid="stSidebar"] [role="radiogroup"] label {
  padding: 8px 12px; border-radius: 10px; margin-bottom: 2px; transition: all .2s ease; cursor: pointer; }
[data-testid="stSidebar"] [role="radiogroup"] label:hover { background: rgba(255,255,255,.10); transform: translateX(4px); }
[data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) {
  background: rgba(42,157,143,.28); border-left: 3px solid #2a9d8f; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,.15); }
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] { color: #aebfd0 !important; }
.brand { font-size: 1.45rem; font-weight: 700; letter-spacing: -.02em; margin: 0; }
.brand span { color: #2a9d8f; }

/* Bandeau */
.hero {
  padding: 24px 30px; margin-bottom: 18px; border-radius: 16px; color: #fff;
  background: linear-gradient(115deg, #0f2a43, #1f4e79 55%, #2a9d8f 100%); background-size: 200% 200%;
  animation: heroShift 14s ease-in-out infinite alternate, fadeUp .5s ease both;
  box-shadow: 0 8px 24px rgba(15,42,67,.18);
}
.hero h1 { margin: 0; font-size: 1.9rem; font-weight: 700; color: #fff !important; }
.hero p { margin: 6px 0 0 0; color: #d6e4f0 !important; font-weight: 300; }

/* Cartes métriques et graphiques */
[data-testid="stMetric"] {
  background: #ffffff; border: 1px solid #e3e8ef; border-left: 4px solid #1f4e79; border-radius: 12px;
  padding: 14px 16px; box-shadow: 0 1px 3px rgba(15,42,67,.06); transition: all .25s ease;
}
[data-testid="stMetric"]:hover { transform: translateY(-3px); box-shadow: 0 10px 22px rgba(15,42,67,.12); border-left-color: #2a9d8f; }
[data-testid="stMetricValue"] { color: #0f2a43 !important; font-weight: 700; }
[data-testid="stMetricLabel"] p { color: #64748b !important; font-weight: 500; }
[data-testid="stPlotlyChart"] {
  background: #fff; border: 1px solid #e3e8ef; border-radius: 14px; padding: 6px;
  box-shadow: 0 1px 3px rgba(15,42,67,.05); transition: box-shadow .25s ease;
}
[data-testid="stPlotlyChart"]:hover { box-shadow: 0 8px 22px rgba(15,42,67,.10); }

/* Boutons */
.stButton > button, .stDownloadButton > button {
  background: #1f4e79; color: #fff; border: none; border-radius: 10px; font-weight: 500;
  padding: .5rem 1.1rem; transition: all .2s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  background: #2a9d8f; color: #fff; transform: translateY(-2px); box-shadow: 0 6px 16px rgba(42,157,143,.35); }
.stButton > button:active { transform: translateY(0); }

/* Onglets */
button[data-baseweb="tab"] { transition: all .2s ease; border-radius: 8px 8px 0 0; }
button[data-baseweb="tab"] p { color: #475569 !important; font-weight: 500; }
button[data-baseweb="tab"]:hover { background: rgba(31,78,121,.07); }
button[data-baseweb="tab"][aria-selected="true"] p { color: #1f4e79 !important; font-weight: 600; }
div[data-baseweb="tab-highlight"] { background: #2a9d8f !important; height: 3px; }

/* Champs */
.stNumberInput input, .stTextInput input, .stDateInput input, .stTimeInput input, textarea {
  background: #fff !important; color: #1f2937 !important; border-radius: 8px !important; border: 1px solid #cbd5e1 !important; }
div[data-baseweb="select"] > div { background: #fff !important; border-radius: 8px !important; border: 1px solid #cbd5e1 !important; }
div[data-baseweb="select"] span { color: #1f2937 !important; }
[data-testid="stExpander"] { background: #fff; border: 1px solid #e3e8ef; border-radius: 12px; }
[data-testid="stExpander"] summary p { color: #0f2a43 !important; font-weight: 600; }
[data-testid="stSidebar"] div[data-baseweb="select"] span { color: #1f2937 !important; }

/* Badges, tableaux, alertes, barres */
.badge { padding: 3px 11px; border-radius: 999px; font-size: .76rem; font-weight: 600; display: inline-block; }
.badge.ok   { background: #e6f4ea; color: #1e7e34; }
.badge.warn { background: #fff4e0; color: #b26a00; }
.badge.ko   { background: #fdeaea; color: #c0392b; }
.badge.info { background: #e8f0f8; color: #1f4e79; }
.tbl-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid #e3e8ef; background: #fff; margin: 6px 0 14px 0; }
.tbl { width: 100%; border-collapse: collapse; font-size: .88rem; color: #1f2937; }
.tbl th { background: #eef2f7; color: #0f2a43; padding: 10px 12px; text-align: left; font-weight: 600; white-space: nowrap; }
.tbl td { padding: 8px 12px; border-top: 1px solid #eef2f7; }
.tbl tr { transition: background .15s; }
.tbl tr:hover td { background: #f6f9fc; }
.alert-card { background: #fff; border: 1px solid #e3e8ef; border-left: 5px solid #1f4e79; border-radius: 10px;
  padding: 10px 14px; margin-bottom: 8px; color: #1f2937; transition: transform .2s ease, box-shadow .2s ease; }
.alert-card:hover { transform: translateX(4px); box-shadow: 0 4px 14px rgba(15,42,67,.10); }
.alert-card.ko { border-left-color: #c0392b; }
.alert-card.warn { border-left-color: #e9a23b; }
.alert-card.ok { border-left-color: #2e7d32; }
.pbar { background: #e6ecf3; border-radius: 999px; height: 10px; overflow: hidden; margin: 4px 0 12px 0; }
.pbar > div { height: 100%; border-radius: 999px; width: var(--w); animation: growBar 1.1s ease both;
  background: linear-gradient(90deg, #1f4e79, #2a9d8f); }
.pl { display: flex; justify-content: space-between; font-size: .85rem; color: #334155; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def hero(title, subtitle):
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def style_fig(fig, height=400, title=None):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#fbfcfe",
        font=dict(family="Inter, sans-serif", color="#1f2937"),
        height=height,
        margin=dict(l=20, r=20, t=55 if title else 20, b=20),
        title=dict(text=title, font=dict(size=15, color=NAVY)) if title else None,
        legend=dict(bgcolor="rgba(255,255,255,0.85)", bordercolor="#e3e8ef", borderwidth=1),
        hoverlabel=dict(bgcolor="white", font_size=12),
    )
    return fig


def badge(ok, txt_ok="CONFORME", txt_ko="NON CONFORME"):
    return f"<span class='badge {'ok' if ok else 'ko'}'>{txt_ok if ok else txt_ko}</span>"


def status_badge(s):
    cls = {"Normal": "ok", "ALERTE": "warn", "ALARME": "ko"}.get(s, "info")
    return f"<span class='badge {cls}'>{s}</span>"


def html_table(headers, rows):
    th = "".join(f"<th>{h}</th>" for h in headers)
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    st.markdown(
        f"<div class='tbl-wrap'><table class='tbl'><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def progress_bar(label, pct, right=None):
    pct = float(max(0, min(100, pct)))
    right = f"{pct:.0f} %" if right is None else right
    st.markdown(
        f"<div class='pl'><span>{label}</span><b>{right}</b></div>"
        f"<div class='pbar'><div style='--w:{pct}%'></div></div>",
        unsafe_allow_html=True,
    )


def alert_card(level, text):
    st.markdown(f"<div class='alert-card {level}'>{text}</div>", unsafe_allow_html=True)


def fmt_int(x):
    return f"{x:,.0f}".replace(",", " ")


def today():
    return pd.Timestamp.now().normalize()


# =============================================================================
# 2. DONNÉES : PARAMÈTRES, SEUILS, DONNÉES DE DÉMONSTRATION
# =============================================================================
def make_default_proj():
    return dict(
        nom="Résidence Les Terrasses - R+5 sur 2 sous-sols",
        client="Maître d'ouvrage",
        date_debut=(today() - pd.Timedelta(days=140)).date(),
        n_etages=5, n_ss=2, emprise=1800.0, h_ss=2.9, h_etage=3.0, e_radier=0.90, charge_niv=12.0,
        gamma=19.0, phi=30.0, coh=5.0, z_nappe=3.0, q=20.0,
        foison=1.25, cap_camion=12.0, fs_uplift=1.10, pompage=True,
    )


SEUILS_DEF = pd.DataFrame(
    [
        ["Piézomètre", "m", "Min", 1.0, 0.3],
        ["Inclinomètre", "mm", "Max", 15.0, 25.0],
        ["Tassement", "mm", "Max", 5.0, 10.0],
        ["Fissuromètre", "mm", "Max", 0.30, 0.50],
        ["Débit de pompage", "m³/h", "Max", 60.0, 80.0],
        ["Vibration", "mm/s", "Max", 5.0, 8.0],
    ],
    columns=["Type", "Unité", "Sens", "Seuil d'alerte", "Seuil d'alarme"],
)
UNITS = dict(zip(SEUILS_DEF["Type"], SEUILS_DEF["Unité"]))
TYPE_HELP = {"Piézomètre": "marge entre la nappe et le fond de fouille (m, + = nappe sous le fond de fouille)",
             "Inclinomètre": "déplacement horizontal de la paroi (mm)",
             "Tassement": "tassement des avoisinants (mm)", "Fissuromètre": "ouverture de fissure (mm)",
             "Débit de pompage": "débit de rabattement (m³/h)", "Vibration": "vitesse particulaire de pointe (mm/s)"}

MES_COLS = ["Date", "Capteur", "Type", "Valeur", "Unité", "Opérateur", "Observation"]
BET_COLS = ["Date", "Élément", "Classe", "Âge (j)", "Résistance (MPa)", "Affaissement (mm)", "T° béton (°C)"]
TER_COLS = ["Date", "Phase", "Volume (m³)", "Camions"]
TASK_COLS = ["Tâche", "Lot", "Début prévu", "Fin prévue", "Avancement (%)", "Coût prévu (k€)", "Coût réel (k€)"]
NC_COLS = ["Date", "Type", "Description", "Zone", "Gravité", "Responsable", "Statut", "Échéance"]
CLASSES = ["C16/20", "C20/25", "C25/30", "C30/37", "C35/45", "C40/50"]
NC_TYPES = ["Non-conformité", "Sécurité", "Qualité", "Environnement", "Document"]
GRAVITES = ["Mineure", "Moyenne", "Majeure", "Critique"]
STATUTS = ["Ouverte", "En cours", "Clôturée"]
PHASES = ["Décapage", "Excavation SS-1", "Excavation SS-2", "Excavation SS-3", "Fond de fouille & radier", "Autre"]


def _smooth(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def make_demo_mesures(p, seed=11):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp(p["date_debut"])
    days = max((today() - start).days, 30) + 1
    t = np.arange(days)
    dates = start + pd.to_timedelta(t, unit="D") + pd.Timedelta(hours=8)
    s = _smooth((t - 40) / 50.0)                          # avancement de l'excavation
    ser = {}
    ser[("PZ-1", "Piézomètre")] = 2.3 + 0.25 * np.sin(t / 18) + rng.normal(0, 0.05, days)
    ser[("PZ-2", "Piézomètre")] = 2.5 - 0.02 * np.clip(t - 60, 0, None) + rng.normal(0, 0.05, days)
    ser[("INC-1", "Inclinomètre")] = 11.5 * s + rng.normal(0, 0.15, days)
    ser[("INC-2", "Inclinomètre")] = 14 * s + 0.12 * np.clip(t - 100, 0, None) + rng.normal(0, 0.15, days)
    ser[("TAS-1", "Tassement")] = 3.0 * s + rng.normal(0, 0.08, days)
    ser[("TAS-2", "Tassement")] = 2.1 * s + rng.normal(0, 0.08, days)
    ser[("TAS-3", "Tassement")] = 5.8 * s + rng.normal(0, 0.10, days)
    ser[("FIS-1", "Fissuromètre")] = 0.10 + 0.22 * s + rng.normal(0, 0.008, days)
    ser[("FIS-2", "Fissuromètre")] = 0.05 + 0.08 * s + rng.normal(0, 0.006, days)
    pump = np.where(t >= 25, 35 + 10 * np.sin(t / 9) + rng.normal(0, 1.5, days), 0.0)
    ser[("POM-1", "Débit de pompage")] = np.clip(pump, 0, None)
    vib = 0.8 + rng.exponential(0.5, days) + np.where((t > 40) & (t < 90), rng.exponential(1.1, days), 0.0)
    vib[np.argmax(t == min(60, days - 1))] = 6.1
    ser[("VIB-1", "Vibration")] = vib
    frames = [pd.DataFrame({"Date": dates, "Capteur": c, "Type": ty, "Valeur": np.round(v, 3),
                            "Unité": UNITS[ty], "Opérateur": "Auto", "Observation": ""})
              for (c, ty), v in ser.items()]
    return clean_mesures(pd.concat(frames, ignore_index=True))


def make_demo_beton(p, seed=5):
    rng = np.random.default_rng(seed)
    start = pd.Timestamp(p["date_debut"])
    now = today()
    pours = [("Béton de propreté", "C16/20", 60, 0), ("Radier B1", "C30/37", 70, 0), ("Radier B2", "C30/37", 77, 0),
             ("Radier B3", "C30/37", 84, 0), ("Voiles SS-2 A", "C30/37", 100, 0), ("Voiles SS-2 B", "C30/37", 108, 0),
             ("Dalle SS-2", "C30/37", 106, -9.5), ("Poteaux fond. P1", "C25/30", 78, 0),
             ("Poteaux fond. P2", "C25/30", 90, 0), ("Poteaux fond. P3", "C25/30", 96, 0),
             ("Voiles SS-1", "C30/37", 126, 0), ("Dalle SS-1", "C30/37", 131, 0)]
    rows = []
    for name, cl, d0, bias in pours:
        fck = int(re.search(r"C(\d+)/", cl).group(1))
        f28 = fck + rng.normal(8, 1.5) + bias
        for age in (7, 28):
            when = start + pd.Timedelta(days=d0 + age) + pd.Timedelta(hours=10)
            if when > now:
                continue
            f = f28 * (0.66 if age == 7 else 1.0) + rng.normal(0, 0.6)
            rows.append([when, name, cl, age, round(f, 1), int(rng.integers(150, 205)), round(float(rng.normal(19, 3)), 1)])
    return clean_beton(pd.DataFrame(rows, columns=BET_COLS))


def make_demo_terr(p, seed=3):
    start = pd.Timestamp(p["date_debut"])
    vb = p["emprise"] * (p["n_ss"] * p["h_ss"] + p["e_radier"])
    fr = [0.04, 0.10, 0.16, 0.20, 0.20, 0.18, 0.12]
    ph = ["Décapage", "Excavation SS-1", "Excavation SS-1", "Excavation SS-1", "Excavation SS-2", "Excavation SS-2",
          "Fond de fouille & radier"]
    rows = []
    for i, (f, pn) in enumerate(zip(fr, ph)):
        d = start + pd.Timedelta(days=40 + 7 * i, hours=17)
        if d <= today() + pd.Timedelta(days=1):
            v = round(vb * f, 0)
            rows.append([d, pn, v, int(round(v * p["foison"] / p["cap_camion"]))])
    return clean_terr(pd.DataFrame(rows, columns=TER_COLS))


def make_demo_tasks(p):
    start = pd.Timestamp(p["date_debut"])
    elapsed = (today() - start).days
    spec = [("Installation de chantier", "Préparation", 0, 15, 120), ("Soutènement (paroi berlinoise)", "Soutènement", 10, 45, 980),
            ("Rabattement de nappe", "Terrassement", 25, 120, 210), ("Terrassement en masse", "Terrassement", 40, 50, 620),
            ("Radier et fondations", "Gros œuvre", 85, 30, 540), ("Voiles et dalles sous-sol -2", "Gros œuvre", 110, 30, 480),
            ("Voiles et dalles sous-sol -1", "Gros œuvre", 135, 30, 460), ("Étanchéité et cuvelage", "Étanchéité", 120, 50, 310),
            ("Structure RDC à R+2", "Gros œuvre", 165, 70, 1250), ("Structure R+3 à R+5", "Gros œuvre", 235, 70, 1100),
            ("Façades et étanchéité toiture", "Second œuvre", 290, 80, 900), ("Lots techniques (CVC, élec., plomberie)", "Lots techniques", 300, 120, 1700),
            ("Finitions et aménagements", "Second œuvre", 380, 90, 1300), ("Réception et levée des réserves", "Réception", 470, 20, 150)]
    rows = []
    for name, lot, off, dur, cost in spec:
        planned = float(np.clip((elapsed - off) / dur, 0, 1))
        av = 100.0 if planned >= 1 else round(planned * 92 / 5) * 5.0
        real = round(cost * av / 100 * 1.035, 0)
        rows.append([name, lot, start + pd.Timedelta(days=off), start + pd.Timedelta(days=off + dur), av, float(cost), real])
    return clean_tasks(pd.DataFrame(rows, columns=TASK_COLS))


def make_demo_nc():
    n = today()
    d = lambda k: n + pd.Timedelta(days=k)
    rows = [
        [d(-95), "Non-conformité", "Ferraillage radier : enrobage insuffisant", "Radier B3", "Moyenne", "Entreprise GO", "Clôturée", d(-88)],
        [d(-70), "Sécurité", "Absence de garde-corps en rive d'excavation Nord", "Excavation Nord", "Critique", "Chef de chantier", "Clôturée", d(-69)],
        [d(-48), "Environnement", "Fuite d'hydrocarbures d'un engin - dépollution", "Zone engins", "Moyenne", "Entreprise TP", "Clôturée", d(-40)],
        [d(-30), "Non-conformité", "Fissures et infiltrations voile SS-2 axe 4", "Voile SS-2 A4", "Majeure", "Bureau de contrôle", "En cours", d(-5)],
        [d(-21), "Sécurité", "Étaiement dalle SS-2 non conforme au plan d'exécution", "Dalle SS-2", "Critique", "Chef de chantier", "En cours", d(3)],
        [d(-12), "Qualité", "Écart de planéité de la dalle SS-1", "Dalle SS-1", "Mineure", "Entreprise GO", "Ouverte", d(10)],
        [d(-6), "Document", "Plan d'exécution armatures voiles SS-1 indice B manquant", "Bureau d'études", "Moyenne", "Bureau d'études", "Ouverte", d(4)],
        [d(-2), "Sécurité", "Vérification périodique de la nacelle non à jour", "Façade Sud", "Majeure", "HSE", "Ouverte", d(2)],
    ]
    return clean_nc(pd.DataFrame(rows, columns=NC_COLS))


# --- Nettoyage / validation des tableaux ------------------------------------
def _ensure(df, cols):
    df = df.copy()
    for c in cols:
        if c not in df.columns:
            df[c] = np.nan
    return df


def clean_mesures(df):
    df = _ensure(df, MES_COLS)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Valeur"] = pd.to_numeric(df["Valeur"], errors="coerce")
    df["Capteur"] = df["Capteur"].astype(str).str.strip()
    df = df.dropna(subset=["Date", "Valeur"])
    df = df[(df["Capteur"].str.len() > 0) & (df["Capteur"].str.lower() != "nan")]
    reg = df.dropna(subset=["Type"]).groupby("Capteur")["Type"].last().to_dict() if len(df) else {}
    df["Type"] = [t if isinstance(t, str) and t.strip() else reg.get(c, "Autre") for t, c in zip(df["Type"], df["Capteur"])]
    df["Unité"] = [u if isinstance(u, str) and u.strip() else UNITS.get(t, "") for u, t in zip(df["Unité"], df["Type"])]
    df["Opérateur"] = df["Opérateur"].fillna("").astype(str)
    df["Observation"] = df["Observation"].fillna("").astype(str)
    return df[MES_COLS].sort_values("Date").reset_index(drop=True)


def clean_beton(df):
    df = _ensure(df, BET_COLS)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    for c in ["Âge (j)", "Résistance (MPa)", "Affaissement (mm)", "T° béton (°C)"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["Élément"] = df["Élément"].fillna("").astype(str)
    df["Classe"] = df["Classe"].fillna("").astype(str).str.strip()
    df = df.dropna(subset=["Date", "Résistance (MPa)", "Âge (j)"])
    df = df[df["Classe"].str.len() > 0]
    return df[BET_COLS].sort_values("Date").reset_index(drop=True)


def clean_terr(df):
    df = _ensure(df, TER_COLS)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Volume (m³)"] = pd.to_numeric(df["Volume (m³)"], errors="coerce")
    df["Camions"] = pd.to_numeric(df["Camions"], errors="coerce").fillna(0)
    df["Phase"] = df["Phase"].fillna("Autre").astype(str)
    df = df.dropna(subset=["Date", "Volume (m³)"])
    return df[TER_COLS].sort_values("Date").reset_index(drop=True)


def clean_tasks(df):
    df = _ensure(df, TASK_COLS)
    df["Début prévu"] = pd.to_datetime(df["Début prévu"], errors="coerce")
    df["Fin prévue"] = pd.to_datetime(df["Fin prévue"], errors="coerce")
    for c in ["Avancement (%)", "Coût prévu (k€)", "Coût réel (k€)"]:
        df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0.0)
    df["Tâche"] = df["Tâche"].fillna("").astype(str).str.strip()
    df["Lot"] = df["Lot"].fillna("Divers").astype(str)
    df = df.dropna(subset=["Début prévu", "Fin prévue"])
    df = df[df["Tâche"].str.len() > 0].copy()
    df["Fin prévue"] = df[["Début prévu", "Fin prévue"]].max(axis=1)
    df["Avancement (%)"] = df["Avancement (%)"].clip(0, 100)
    return df[TASK_COLS].sort_values("Début prévu").reset_index(drop=True)


def clean_nc(df):
    df = _ensure(df, NC_COLS)
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Échéance"] = pd.to_datetime(df["Échéance"], errors="coerce")
    for c, default in [("Type", "Non-conformité"), ("Gravité", "Moyenne"), ("Statut", "Ouverte")]:
        df[c] = df[c].fillna(default).astype(str)
    for c in ["Description", "Zone", "Responsable"]:
        df[c] = df[c].fillna("").astype(str)
    df = df.dropna(subset=["Date"])
    df = df[df["Description"].str.len() > 0]
    return df[NC_COLS].sort_values("Date").reset_index(drop=True)


def init_state():
    ss = st.session_state
    if "proj" not in ss:
        ss.proj = make_default_proj()
    p = ss.proj
    if "mesures" not in ss:
        ss.mesures = make_demo_mesures(p)
    if "beton" not in ss:
        ss.beton = make_demo_beton(p)
    if "terr" not in ss:
        ss.terr = make_demo_terr(p)
    if "tasks" not in ss:
        ss.tasks = make_demo_tasks(p)
    if "nc" not in ss:
        ss.nc = make_demo_nc()
    if "seuils" not in ss:
        ss.seuils = SEUILS_DEF.copy()


def num(label, key, mn, mx, step, fmt="%.2f", help=None, container=st):
    p = st.session_state.proj
    v = container.number_input(label, min_value=float(mn), max_value=float(mx), value=float(p[key]),
                               step=float(step), format=fmt, key=f"w_{key}", help=help)
    p[key] = int(round(v)) if key in INT_KEYS else float(v)
    return p[key]


def csv_importer(label, cleaner, state_key, key):
    up = st.file_uploader(label, type=["csv"], key=f"up_{key}")
    if up is not None and st.button("📥 Fusionner avec les données", key=f"btn_up_{key}"):
        try:
            new = cleaner(pd.read_csv(up, sep=None, engine="python"))
            st.session_state[state_key] = cleaner(pd.concat([st.session_state[state_key], new], ignore_index=True))
            st.toast(f"{len(new)} lignes importées ✅")
            st.rerun()
        except Exception as exc:
            st.error(f"Import impossible : {exc}")


# =============================================================================
# 3. CALCULS : SOUS-SOL, MESURES, BÉTON, AVANCEMENT
# =============================================================================
GW = 9.81
INT_KEYS = {"n_etages", "n_ss"}


def excavation_depth(p):
    return p["n_ss"] * p["h_ss"] + p["e_radier"]


def earth_pressure(p, pompage):
    """Poussée active (Rankine) sur la paroi, avec surcharge et nappe. Résultats par mètre linéaire."""
    Hx = excavation_depth(p)
    z = np.linspace(0.0, Hx, 241)
    ka = math.tan(math.radians(45 - p["phi"] / 2)) ** 2
    zw = 1e6 if pompage else p["z_nappe"]
    sv = p["q"] + p["gamma"] * np.minimum(z, zw) + (p["gamma"] + 1.0 - GW) * np.maximum(z - zw, 0)
    sa = np.maximum(ka * sv - 2 * p["coh"] * math.sqrt(ka), 0.0)
    u = GW * np.maximum(z - zw, 0)
    sig = sa + u
    dz = z[1] - z[0]
    mid = (sig[:-1] + sig[1:]) / 2
    zmid = (z[:-1] + z[1:]) / 2
    P = float(np.sum(mid) * dz)
    zbar = float(np.sum(mid * zmid) * dz / P) if P > 1e-9 else Hx / 2
    n_props = max(1, int(p["n_ss"]))
    return dict(Hx=Hx, z=z, sig=sig, u=u, ka=ka, P=P, zbar=zbar, M=P * (Hx - zbar), n_props=n_props, react=P / n_props)


def uplift_check(p):
    Hx, S = excavation_depth(p), p["emprise"]
    hw = max(Hx - p["z_nappe"], 0.0)
    U = GW * hw * S
    g_rad = p["e_radier"] * 25.0
    G_cons = S * (g_rad + p["n_ss"] * p["charge_niv"])
    G_fin = S * (g_rad + (p["n_ss"] + 1 + p["n_etages"]) * p["charge_niv"])
    fs_c = G_cons / U if U > 0 else 99.0
    fs_f = G_fin / U if U > 0 else 99.0
    deficit = max(p["fs_uplift"] * U - G_cons, 0.0)
    return dict(hw=hw, U=U, G_cons=G_cons, G_fin=G_fin, fs_c=fs_c, fs_f=fs_f, ok_c=fs_c >= p["fs_uplift"],
                ok_f=fs_f >= p["fs_uplift"], extra_h=deficit / (S * 25.0) if S > 0 else 0.0)


def terr_stats(p, terr):
    Vb = p["emprise"] * excavation_depth(p)
    done = float(terr["Volume (m³)"].sum()) if len(terr) else 0.0
    trucks = float(terr["Camions"].sum()) if len(terr) else 0.0
    rate, eta = 0.0, None
    if len(terr) >= 2:
        last = terr[terr["Date"] >= terr["Date"].max() - pd.Timedelta(days=14)]
        span = max((last["Date"].max() - last["Date"].min()).days + 7, 1)
        rate = float(last["Volume (m³)"].sum()) / span
        if rate > 0 and Vb - done > 0:
            eta = terr["Date"].max() + pd.Timedelta(days=(Vb - done) / rate)
    return dict(Vb=Vb, done=done, pct=100 * done / Vb if Vb > 0 else 0.0, trucks=trucks, rate=rate, eta=eta,
                haul=Vb * p["foison"], n_trucks=Vb * p["foison"] / p["cap_camion"])


def get_status(val, typ, seuils):
    row = seuils[seuils["Type"] == typ]
    if row.empty:
        return "Normal"
    r = row.iloc[0]
    a, b = float(r["Seuil d'alerte"]), float(r["Seuil d'alarme"])
    if str(r.get("Sens", "Max")) == "Min":
        return "ALARME" if val <= b else ("ALERTE" if val <= a else "Normal")
    return "ALARME" if val >= b else ("ALERTE" if val >= a else "Normal")


def sensor_summary(df, seuils):
    rows = []
    for cap, g in df.groupby("Capteur"):
        g = g.sort_values("Date")
        v = g["Valeur"].to_numpy(float)
        days = (g["Date"] - g["Date"].iloc[0]).dt.total_seconds().to_numpy() / 86400
        slope = float(np.polyfit(days, v, 1)[0]) if len(g) >= 3 and days.max() > 0 else 0.0
        typ = g["Type"].iloc[-1]
        rows.append(dict(Capteur=cap, Type=typ, Unité=g["Unité"].iloc[-1], N=len(g), Min=float(v.min()),
                         Moyenne=float(v.mean()), Max=float(v.max()), Ecart=float(v.std(ddof=1)) if len(v) > 1 else 0.0,
                         Dernière=float(v[-1]), Date=g["Date"].iloc[-1].strftime("%d/%m/%Y"), Tendance=slope,
                         Statut=get_status(float(v[-1]), typ, seuils)))
    return pd.DataFrame(rows)


def robust_outliers(y, thr=3.5):
    y = np.asarray(y, float)
    med = np.median(y)
    mad = np.median(np.abs(y - med))
    if mad < 1e-9:
        return np.zeros(len(y), dtype=bool)
    return np.abs(0.6745 * (y - med) / mad) > thr


def parse_fck(cl):
    m = re.search(r"C(\d+)\s*/", str(cl))
    return float(m.group(1)) if m else None


def beton_stats(dfb):
    """Conformité simplifiée type EN 206 sur les résultats à 28 jours, par classe."""
    rows = []
    d28 = dfb[dfb["Âge (j)"] == 28]
    for cl, g in d28.groupby("Classe"):
        fck = parse_fck(cl)
        v = g["Résistance (MPa)"].to_numpy(float)
        n = len(v)
        fcm, fmin = float(v.mean()), float(v.min())
        sig = float(v.std(ddof=1)) if n > 1 else 0.0
        if fck is None or n < 3:
            rows.append(dict(Classe=cl, n=n, fck=fck, fcm=fcm, fmin=fmin, sigma=sig, lim1=None, lim2=None,
                             c1=None, c2=None, statut="Insuffisant (n<3)"))
            continue
        lim1 = fck + 4.0 if n < 15 else fck + 1.48 * max(sig, 3.0)
        lim2 = fck - 4.0
        c1, c2 = fcm >= lim1, fmin >= lim2
        rows.append(dict(Classe=cl, n=n, fck=fck, fcm=fcm, fmin=fmin, sigma=sig, lim1=lim1, lim2=lim2, c1=c1, c2=c2,
                         statut="Conforme" if (c1 and c2) else "Non conforme"))
    return pd.DataFrame(rows)


def beton_forecast(dfb):
    """Prévision de la résistance à 28 j à partir des essais à 7 j (f28 ≈ f7 / 0,65)."""
    d7 = dfb[dfb["Âge (j)"] == 7].copy()
    d28 = dfb[dfb["Âge (j)"] == 28]
    done = set(zip(d28["Élément"], d28["Classe"]))
    d7["fck"] = d7["Classe"].map(parse_fck)
    d7["f28_est"] = d7["Résistance (MPa)"] / 0.65
    d7["Déjà testé à 28 j"] = [(e, c) in done for e, c in zip(d7["Élément"], d7["Classe"])]
    d7["OK"] = d7["f28_est"] >= d7["fck"] + 4
    return d7


def evm(tasks, t):
    t = pd.Timestamp(t)
    cost = tasks["Coût prévu (k€)"]
    dur = (tasks["Fin prévue"] - tasks["Début prévu"]).dt.days.clip(lower=1)
    frac = ((t - tasks["Début prévu"]).dt.days / dur).clip(0, 1)
    bac = float(cost.sum())
    pv = float((cost * frac).sum())
    ev = float((cost * tasks["Avancement (%)"] / 100).sum())
    ac = float(tasks["Coût réel (k€)"].sum())
    spi = ev / pv if pv > 0 else 1.0
    cpi = ev / ac if ac > 0 else 1.0
    return dict(bac=bac, pv=pv, ev=ev, ac=ac, spi=spi, cpi=cpi, eac=bac / cpi if cpi > 0 else bac,
                pct=100 * ev / bac if bac > 0 else 0.0)


def scurve(tasks):
    dates = pd.date_range(tasks["Début prévu"].min(), tasks["Fin prévue"].max(), freq="D")
    pv = np.zeros(len(dates))
    for _, r in tasks.iterrows():
        dur = max((r["Fin prévue"] - r["Début prévu"]).days, 1)
        frac = np.clip(np.asarray((dates - r["Début prévu"]).days, dtype=float) / dur, 0, 1)
        pv += r["Coût prévu (k€)"] * frac
    return dates, pv


def delay_days(tasks, ev):
    dates, pv = scurve(tasks)
    idx = int(np.searchsorted(pv, ev))
    idx = min(idx, len(dates) - 1)
    return int((today() - dates[idx]).days)


# =============================================================================
# 4. FIGURES
# =============================================================================
def fig_coupe(p):
    Hx, zw = excavation_depth(p), p["z_nappe"]
    W = 30.0
    hb = p["h_etage"] * (p["n_etages"] + 1)
    deep = Hx + 4.0
    fig = go.Figure()
    fig.add_shape(type="rect", x0=-12, x1=W + 12, y0=-deep, y1=0, fillcolor="#d8c3a5", line=dict(width=0), layer="below")
    if zw < deep:
        fig.add_shape(type="rect", x0=-12, x1=W + 12, y0=-deep, y1=-zw, fillcolor="rgba(61,133,198,0.30)",
                      line=dict(width=0), layer="below")
        fig.add_shape(type="line", x0=-12, x1=W + 12, y0=-zw, y1=-zw, line=dict(color="#3d85c6", width=2, dash="dash"))
    fig.add_shape(type="rect", x0=0, x1=W, y0=-Hx, y1=0, fillcolor="#f3f5f8", line=dict(width=0))
    for x0, x1 in [(-0.7, 0), (W, W + 0.7)]:
        fig.add_shape(type="rect", x0=x0, x1=x1, y0=-(Hx + 3), y1=0, fillcolor=GREY, line=dict(color=NAVY, width=1))
    fig.add_shape(type="rect", x0=0, x1=W, y0=-Hx, y1=-Hx + p["e_radier"], fillcolor=NAVY, line=dict(color=NAVY))
    for k in range(1, p["n_ss"] + 1):
        y = -Hx + p["e_radier"] + k * p["h_ss"]
        fig.add_shape(type="rect", x0=0, x1=W, y0=y - 0.25, y1=y, fillcolor="#8a97a6", line=dict(color=NAVY, width=1))
    fig.add_shape(type="rect", x0=0, x1=W, y0=0, y1=hb, fillcolor="rgba(31,78,121,0.10)", line=dict(color=BLUE, width=2))
    for k in range(1, p["n_etages"] + 1):
        fig.add_shape(type="line", x0=0, x1=W, y0=k * p["h_etage"], y1=k * p["h_etage"], line=dict(color=BLUE, width=1))
    fig.add_shape(type="line", x0=-12, x1=W + 12, y0=0, y1=0, line=dict(color="#7a5c3a", width=2))
    U = uplift_check(p)
    if U["hw"] > 0:
        for x in np.linspace(3, W - 3, 6):
            fig.add_annotation(x=x, y=-Hx + p["e_radier"] + 0.1, ax=x, ay=-Hx - 1.8, xref="x", yref="y", axref="x", ayref="y",
                               showarrow=True, arrowhead=2, arrowwidth=2, arrowcolor=RED)
    fig.add_annotation(x=W / 2, y=-Hx / 2, text=f"{p['n_ss']} sous-sol(s) - H fouille = {Hx:.1f} m", showarrow=False, font=dict(color=NAVY))
    fig.add_annotation(x=W / 2, y=hb / 2, text=f"R+{p['n_etages']}", showarrow=False, font=dict(color=BLUE, size=16))
    fig.add_annotation(x=W + 11.5, y=-zw, text=f"Nappe -{zw:.1f} m", showarrow=False, xanchor="right", yshift=10, font=dict(color="#2d6aa0"))
    fig.add_annotation(x=-0.35, y=-(Hx + 3), text="Paroi", showarrow=False, yshift=-12, font=dict(color=NAVY))
    if U["hw"] > 0:
        fig.add_annotation(x=W / 2, y=-Hx - 2.2, text="Sous-pression sur le radier", showarrow=False, font=dict(color=RED))
    fig.update_xaxes(range=[-12, W + 12], visible=False)
    fig.update_yaxes(range=[-deep - 0.5, hb + 2], title="Niveau / TN (m)", zeroline=False, gridcolor="#e8edf3")
    return style_fig(fig, 520, "Coupe schématique du bâtiment et du sous-sol")


def fig_pressure(ep, ep_off, p):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ep["sig"], y=-ep["z"], name="Poussée totale (sol + eau)", fill="tozerox",
                             line=dict(color=BLUE, width=3), fillcolor="rgba(31,78,121,0.18)"))
    fig.add_trace(go.Scatter(x=ep["u"], y=-ep["z"], name="Pression d'eau", line=dict(color="#3d85c6", dash="dash", width=2)))
    if ep_off is not None:
        fig.add_trace(go.Scatter(x=ep_off["sig"], y=-ep_off["z"], name="Variante : pompage hors service",
                                 line=dict(color=RED, dash="dot", width=2)))
    fig.add_hline(y=-ep["zbar"], line=dict(color=AMBER, dash="dash"),
                  annotation_text=f"Résultante P = {ep['P']:.0f} kN/ml", annotation_font_color=AMBER)
    fig.update_xaxes(title="Pression horizontale (kPa)")
    fig.update_yaxes(title="Profondeur (m, négatif vers le bas)")
    return style_fig(fig, 430, "Diagramme des pressions sur la paroi")


def fig_scurve(tasks, ev_info):
    dates, pv = scurve(tasks)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=pv, name="Prévu (PV)", mode="lines", fill="tozeroy",
                             line=dict(color=BLUE, width=3), fillcolor="rgba(31,78,121,0.10)"))
    t = today()
    fig.add_trace(go.Scatter(x=[t], y=[ev_info["ev"]], mode="markers", name="Valeur acquise (EV)",
                             marker=dict(size=14, color=TEAL, line=dict(color="white", width=2))))
    fig.add_trace(go.Scatter(x=[t], y=[ev_info["ac"]], mode="markers", name="Coût réel (AC)",
                             marker=dict(size=14, symbol="diamond", color=AMBER, line=dict(color="white", width=2))))
    fig.add_shape(type="line", x0=t, x1=t, y0=0, y1=1, yref="paper", line=dict(color=GREY, dash="dot"))
    fig.add_annotation(x=t, y=1, yref="paper", text="Aujourd'hui", showarrow=False, yshift=8, font=dict(color=GREY))
    fig.update_yaxes(title="Coût cumulé (k€)")
    return style_fig(fig, 400, "Courbe en S : prévu, acquis et réel")


# =============================================================================
# 5. PAGES
# =============================================================================
def page_dashboard():
    p = st.session_state.proj
    ss = st.session_state
    hero(p["nom"], f"{p['client']} · R+{p['n_etages']} sur {p['n_ss']} sous-sol(s) · Tableau de bord de suivi de chantier")
    ev = evm(ss.tasks, today()) if len(ss.tasks) else None
    summ = sensor_summary(ss.mesures, ss.seuils) if len(ss.mesures) else pd.DataFrame()
    bs = beton_stats(ss.beton) if len(ss.beton) else pd.DataFrame()
    ts = terr_stats(p, ss.terr)
    up = uplift_check(p)
    nc = ss.nc
    nc_open = nc[nc["Statut"] != "Clôturée"]
    nc_late = nc_open[nc_open["Échéance"] < today()]
    n_alert = int((summ["Statut"] == "ALERTE").sum()) if len(summ) else 0
    n_alarm = int((summ["Statut"] == "ALARME").sum()) if len(summ) else 0

    c = st.columns(5)
    if ev:
        c[0].metric("Avancement global", f"{ev['pct']:.1f} %")
        c[1].metric("SPI (délais)", f"{ev['spi']:.2f}", "en retard" if ev["spi"] < 0.95 else "conforme", delta_color="inverse" if ev["spi"] < 0.95 else "normal")
        c[2].metric("CPI (coûts)", f"{ev['cpi']:.2f}", "dérive" if ev["cpi"] < 0.95 else "maîtrisé", delta_color="inverse" if ev["cpi"] < 0.95 else "normal")
        c[3].metric("Budget consommé", f"{100 * ev['ac'] / ev['bac']:.1f} %" if ev["bac"] else "-")
        c[4].metric("Retard estimé", f"{max(delay_days(ss.tasks, ev['ev']), 0)} j")
    c = st.columns(5)
    c[0].metric("Terrassement réalisé", f"{ts['pct']:.0f} %")
    c[1].metric("Capteurs en alerte", n_alert)
    c[2].metric("Capteurs en alarme", n_alarm)
    ok_b = int((bs["statut"] == "Conforme").sum()) if len(bs) else 0
    c[3].metric("Classes béton conformes", f"{ok_b} / {len(bs)}")
    c[4].metric("NC ouvertes", len(nc_open), f"{len(nc_late)} en retard" if len(nc_late) else "dans les délais",
                delta_color="inverse" if len(nc_late) else "off")

    left, right = st.columns([3, 2])
    with left:
        if ev:
            st.plotly_chart(fig_scurve(ss.tasks, ev), key="dash_s")
    with right:
        st.markdown("#### Avancement par lot")
        if len(ss.tasks):
            g = ss.tasks.assign(ev=ss.tasks["Coût prévu (k€)"] * ss.tasks["Avancement (%)"] / 100).groupby("Lot")[["ev", "Coût prévu (k€)"]].sum()
            for lot, r in g.iterrows():
                progress_bar(lot, 100 * r["ev"] / r["Coût prévu (k€)"] if r["Coût prévu (k€)"] else 0)

    st.markdown("#### Points d'attention")
    shown = 0
    for _, r in summ.iterrows():
        if r["Statut"] != "Normal":
            alert_card("ko" if r["Statut"] == "ALARME" else "warn",
                       f"<b>{r['Capteur']}</b> ({r['Type']}) : {r['Dernière']:.2f} {r['Unité']} - {status_badge(r['Statut'])}")
            shown += 1
    for _, r in bs.iterrows() if len(bs) else []:
        if r["statut"] == "Non conforme":
            alert_card("ko", f"Béton <b>{r['Classe']}</b> non conforme : fcm = {r['fcm']:.1f} MPa (min. requis {r['lim1']:.1f}), "
                             f"fmin = {r['fmin']:.1f} MPa (min. requis {r['lim2']:.1f})")
            shown += 1
    for _, r in nc_open[nc_open["Gravité"].isin(["Critique", "Majeure"])].iterrows():
        late = pd.notna(r["Échéance"]) and r["Échéance"] < today()
        alert_card("ko" if r["Gravité"] == "Critique" or late else "warn",
                   f"{r['Type']} <b>{r['Gravité']}</b> : {r['Description']} ({r['Zone']}){' - <b>en retard</b>' if late else ''}")
        shown += 1
    if ev and ev["spi"] < 0.95:
        alert_card("warn", f"Retard de planning : SPI = {ev['spi']:.2f}")
        shown += 1
    if ev and ev["cpi"] < 0.95:
        alert_card("warn", f"Dérive des coûts : CPI = {ev['cpi']:.2f}, coût final estimé {fmt_int(ev['eac'])} k€ pour un budget de {fmt_int(ev['bac'])} k€")
        shown += 1
    if not up["ok_c"] or not up["ok_f"]:
        alert_card("ko", f"Risque de soulèvement hydraulique : FS chantier = {up['fs_c']:.2f}, FS final = {up['fs_f']:.2f} (min. {p['fs_uplift']:.2f})")
        shown += 1
    if shown == 0:
        alert_card("ok", "Aucun point d'attention : tout est conforme.")


def page_projet():
    p = st.session_state.proj
    hero("🏗️ Projet & sous-sol", "Paramètres, volumes de terrassement, poussée des terres sur la paroi et soulèvement hydraulique")
    with st.expander("⚙️ Paramètres du projet", expanded=True):
        t1, t2, t3 = st.tabs(["🏢 Bâtiment", "🌍 Sol et nappe", "🚚 Terrassement"])
        with t1:
            c1, c2, c3 = st.columns(3)
            p["client"] = c1.text_input("Maître d'ouvrage", p["client"], key="w_client")
            p["date_debut"] = c2.date_input("Début du chantier", p["date_debut"], key="w_date_debut")
            num("Emprise du sous-sol (m²)", "emprise", 100, 50000, 50, "%.0f", container=c3)
            num("Étages hors sol (R+N)", "n_etages", 0, 40, 1, "%.0f", container=c1)
            num("Nombre de sous-sols", "n_ss", 1, 6, 1, "%.0f", container=c2)
            num("Hauteur d'un sous-sol (m)", "h_ss", 2.2, 5.0, 0.1, container=c3)
            num("Hauteur d'un étage (m)", "h_etage", 2.6, 5.0, 0.1, container=c1)
            num("Épaisseur du radier (m)", "e_radier", 0.3, 3.0, 0.05, container=c2)
            num("Charge permanente par niveau (kN/m²)", "charge_niv", 5, 30, 0.5, container=c3,
                help="Poids propre de la structure et des superstructures par niveau (dalle + voiles + finitions)")
        with t2:
            c1, c2, c3 = st.columns(3)
            num("Poids volumique du sol γ (kN/m³)", "gamma", 14, 23, 0.5, container=c1)
            num("Angle de frottement φ (°)", "phi", 15, 45, 1, "%.0f", container=c2)
            num("Cohésion c (kPa)", "coh", 0, 100, 1, "%.0f", container=c3)
            num("Profondeur de la nappe sous TN (m)", "z_nappe", 0, 30, 0.5, container=c1)
            num("Surcharge en tête q (kPa)", "q", 0, 100, 5, "%.0f", container=c2, help="Engins, stockage, bâtiments voisins")
            num("Coef. de sécurité mini au soulèvement", "fs_uplift", 1.0, 1.5, 0.01, container=c3)
            p["pompage"] = st.checkbox("Rabattement de nappe en service (la nappe est sous le fond de fouille)", value=p["pompage"], key="w_pompage")
        with t3:
            c1, c2 = st.columns(2)
            num("Coefficient de foisonnement", "foison", 1.0, 1.6, 0.01, container=c1)
            num("Capacité d'un camion (m³)", "cap_camion", 5, 30, 1, "%.0f", container=c2)

    Hx = excavation_depth(p)
    ts = terr_stats(p, st.session_state.terr)
    ep = earth_pressure(p, p["pompage"])
    ep_off = earth_pressure(p, False) if p["pompage"] else None
    up = uplift_check(p)

    c = st.columns(5)
    c[0].metric("Profondeur de fouille", f"{Hx:.1f} m")
    c[1].metric("Volume en place", f"{fmt_int(ts['Vb'])} m³")
    c[2].metric("Volume à évacuer", f"{fmt_int(ts['haul'])} m³", f"foisonné ×{p['foison']:.2f}", delta_color="off")
    c[3].metric("Rotations de camions", fmt_int(ts["n_trucks"]))
    c[4].metric("Niveaux d'étais/ancrages", ep["n_props"])

    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(fig_coupe(p), key="coupe")
    with right:
        st.markdown("#### Soulèvement hydraulique (sous-pression)")
        rows = [
            ["Charge d'eau sous radier", f"{up['hw']:.2f} m", "-", status_badge("Normal") if up["hw"] == 0 else "<span class='badge info'>nappe haute</span>"],
            ["Sous-pression totale U", f"{fmt_int(up['U'] / 1000)} MN", "-", "-"],
            ["Stade gros œuvre sous-sol : FS", f"{up['fs_c']:.2f}", f"≥ {p['fs_uplift']:.2f}", badge(up["ok_c"], "OK", "NON")],
            ["Bâtiment terminé : FS", f"{up['fs_f']:.2f}", f"≥ {p['fs_uplift']:.2f}", badge(up["ok_f"], "OK", "NON")],
        ]
        html_table(["Vérification", "Valeur", "Critère", "Statut"], rows)
        if not up["ok_c"]:
            st.error(f"Lestage insuffisant au stade chantier : épaissir le radier d'environ {up['extra_h']:.2f} m, ou maintenir le pompage jusqu'à la mise en charge.")
        else:
            st.success("Le poids du bâtiment équilibre la sous-pression, y compris au stade gros œuvre du sous-sol.")
        st.markdown("#### Poussée sur la paroi")
        k = st.columns(2)
        k[0].metric("Ka (Rankine)", f"{ep['ka']:.3f}")
        k[1].metric("Poussée P", f"{ep['P']:.0f} kN/ml")
        k[0].metric("Moment en pied", f"{ep['M']:.0f} kN·m/ml")
        k[1].metric("Réaction par niveau d'étais", f"{ep['react']:.0f} kN/ml")
        st.caption("Répartition simplifiée de la poussée sur les niveaux d'étais : à justifier par un calcul de paroi complet (logiciel d'interaction sol-structure).")
    st.plotly_chart(fig_pressure(ep, ep_off, p), key="press")

    st.markdown("#### Terrassement")
    terr = st.session_state.terr
    t1, t2 = st.columns([2, 1])
    with t1:
        if len(terr):
            cum = terr["Volume (m³)"].cumsum()
            f = go.Figure()
            f.add_trace(go.Bar(x=terr["Date"], y=terr["Volume (m³)"], name="Volume par relevé", marker_color="#9bb7d4"))
            f.add_trace(go.Scatter(x=terr["Date"], y=cum, name="Cumul", mode="lines+markers", line=dict(color=BLUE, width=3)))
            f.add_hline(y=ts["Vb"], line=dict(color=RED, dash="dash"), annotation_text="Volume total à excaver",
                        annotation_font_color=RED)
            f.update_yaxes(title="m³ en place")
            st.plotly_chart(style_fig(f, 360, "Avancement des terrassements"), key="terr_chart")
        else:
            st.info("Aucun relevé de terrassement : saisissez-en dans « Collecte des données ».")
    with t2:
        progress_bar("Terrassement réalisé", ts["pct"])
        st.metric("Cadence récente", f"{ts['rate']:.0f} m³/j")
        st.metric("Fin estimée", ts["eta"].strftime("%d/%m/%Y") if ts["eta"] is not None else "-")
        st.metric("Camions déjà évacués", fmt_int(ts["trucks"]))


def page_collecte():
    ss = st.session_state
    p = ss.proj
    hero("📡 Collecte des données", "Saisie manuelle, import CSV et tableaux éditables pour chaque famille de données")
    t1, t2, t3, t4 = st.tabs(["📈 Auscultation", "🧪 Béton", "🚚 Terrassement", "📅 Avancement & coûts"])

    with t1:
        df = ss.mesures
        c = st.columns(4)
        c[0].metric("Mesures", fmt_int(len(df)))
        c[1].metric("Capteurs", df["Capteur"].nunique() if len(df) else 0)
        c[2].metric("Types", df["Type"].nunique() if len(df) else 0)
        c[3].metric("Dernière mesure", df["Date"].max().strftime("%d/%m/%Y") if len(df) else "-")
        a, b, c3 = st.columns(3)
        types = list(UNITS.keys()) + ["Autre"]
        with a:
            d = st.date_input("Date", date.today(), key="m_date")
            tm = st.time_input("Heure", datetime.now().time().replace(second=0, microsecond=0), key="m_time")
        with b:
            typ = st.selectbox("Type de mesure", types, key="m_type")
            existing = sorted(df.loc[df["Type"] == typ, "Capteur"].unique()) if len(df) else []
            choice = st.selectbox("Capteur", existing + ["➕ Nouveau capteur"], key="m_cap")
            cap = st.text_input("Nom du nouveau capteur", key="m_newcap") if choice.startswith("➕") else choice
        with c3:
            val = st.number_input("Valeur", value=0.0, format="%.3f", key="m_val")
            st.caption(f"Unité : {UNITS.get(typ, '')} - {TYPE_HELP.get(typ, '')}")
            oper = st.text_input("Opérateur", key="m_oper")
        obs = st.text_input("Observation", key="m_obs")
        if st.button("➕ Enregistrer la mesure", key="m_save"):
            if not cap or not cap.strip():
                st.error("Indiquez le nom du capteur.")
            else:
                new = pd.DataFrame([{"Date": datetime.combine(d, tm), "Capteur": cap.strip(), "Type": typ, "Valeur": val,
                                     "Unité": UNITS.get(typ, ""), "Opérateur": oper, "Observation": obs}])
                ss.mesures = clean_mesures(pd.concat([ss.mesures, new], ignore_index=True))
                st.toast("Mesure enregistrée ✅")
                st.rerun()
        with st.expander("📂 Import / export / tableau éditable"):
            csv_importer("CSV (Date, Capteur, Type, Valeur, ...)", clean_mesures, "mesures", "mes")
            st.download_button("⬇️ Télécharger les mesures", ss.mesures.to_csv(index=False).encode("utf-8"), "mesures.csv", "text/csv", key="dl_mes")
            cc = st.columns(2)
            if cc[0].button("🎲 Recharger la démo", key="m_demo"):
                ss.mesures = make_demo_mesures(p)
                st.rerun()
            if cc[1].button("🗑️ Vider", key="m_clear"):
                ss.mesures = clean_mesures(pd.DataFrame(columns=MES_COLS))
                st.rerun()
            ed = st.data_editor(ss.mesures.sort_values("Date", ascending=False).reset_index(drop=True), num_rows="dynamic",
                                hide_index=True, height=360, key="ed_mes",
                                column_config={"Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                                               "Type": st.column_config.SelectboxColumn(options=types)})
            if st.button("💾 Enregistrer les modifications", key="m_sv"):
                ss.mesures = clean_mesures(ed)
                st.session_state.pop("ed_mes", None)
                st.rerun()

    with t2:
        c = st.columns(4)
        c[0].metric("Essais", len(ss.beton))
        c[1].metric("Dont à 28 jours", int((ss.beton["Âge (j)"] == 28).sum()) if len(ss.beton) else 0)
        c[2].metric("Classes", ss.beton["Classe"].nunique() if len(ss.beton) else 0)
        c[3].metric("Dernier essai", ss.beton["Date"].max().strftime("%d/%m/%Y") if len(ss.beton) else "-")
        a, b, c3 = st.columns(3)
        d = a.date_input("Date de l'essai", date.today(), key="b_date")
        elem = a.text_input("Élément coulé", "Dalle SS-1", key="b_elem")
        cl = b.selectbox("Classe de béton", CLASSES, index=3, key="b_cl")
        age = b.selectbox("Âge à l'essai (jours)", [3, 7, 14, 28, 56], index=3, key="b_age")
        fc = c3.number_input("Résistance (MPa)", 0.0, 120.0, 38.0, 0.5, key="b_fc")
        sl = c3.number_input("Affaissement (mm)", 0, 300, 180, 5, key="b_sl")
        tb = c3.number_input("Température du béton (°C)", -5.0, 45.0, 18.0, 0.5, key="b_t")
        if st.button("➕ Enregistrer l'essai", key="b_save"):
            new = pd.DataFrame([[datetime.combine(d, datetime.now().time()), elem, cl, age, fc, sl, tb]], columns=BET_COLS)
            ss.beton = clean_beton(pd.concat([ss.beton, new], ignore_index=True))
            st.toast("Essai enregistré ✅")
            st.rerun()
        with st.expander("📂 Import / export / tableau éditable"):
            csv_importer("CSV béton", clean_beton, "beton", "bet")
            st.download_button("⬇️ Télécharger les essais", ss.beton.to_csv(index=False).encode("utf-8"), "essais_beton.csv", "text/csv", key="dl_bet")
            ed = st.data_editor(ss.beton.sort_values("Date", ascending=False).reset_index(drop=True), num_rows="dynamic",
                                hide_index=True, height=340, key="ed_bet",
                                column_config={"Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                                               "Classe": st.column_config.SelectboxColumn(options=CLASSES)})
            if st.button("💾 Enregistrer les modifications", key="b_sv"):
                ss.beton = clean_beton(ed)
                st.session_state.pop("ed_bet", None)
                st.rerun()

    with t3:
        ts = terr_stats(p, ss.terr)
        c = st.columns(4)
        c[0].metric("Volume excavé", f"{fmt_int(ts['done'])} m³")
        c[1].metric("Volume total à excaver", f"{fmt_int(ts['Vb'])} m³")
        c[2].metric("Avancement", f"{ts['pct']:.0f} %")
        c[3].metric("Camions", fmt_int(ts["trucks"]))
        a, b, c3 = st.columns(3)
        d = a.date_input("Date du relevé", date.today(), key="t_date")
        ph = b.selectbox("Phase", PHASES, index=1, key="t_ph")
        v = c3.number_input("Volume excavé (m³ en place)", 0.0, 100000.0, 800.0, 50.0, key="t_v")
        st.caption(f"Camions estimés : {int(round(v * p['foison'] / p['cap_camion']))} (foisonnement {p['foison']:.2f}, camion {p['cap_camion']:.0f} m³)")
        if st.button("➕ Enregistrer le relevé", key="t_save"):
            new = pd.DataFrame([[datetime.combine(d, datetime.now().time()), ph, v, round(v * p["foison"] / p["cap_camion"])]], columns=TER_COLS)
            ss.terr = clean_terr(pd.concat([ss.terr, new], ignore_index=True))
            st.toast("Relevé enregistré ✅")
            st.rerun()
        with st.expander("📂 Import / export / tableau éditable"):
            csv_importer("CSV terrassement", clean_terr, "terr", "ter")
            st.download_button("⬇️ Télécharger", ss.terr.to_csv(index=False).encode("utf-8"), "terrassement.csv", "text/csv", key="dl_ter")
            ed = st.data_editor(ss.terr, num_rows="dynamic", hide_index=True, key="ed_ter",
                                column_config={"Date": st.column_config.DatetimeColumn(format="DD/MM/YYYY HH:mm"),
                                               "Phase": st.column_config.SelectboxColumn(options=PHASES)})
            if st.button("💾 Enregistrer les modifications", key="t_sv"):
                ss.terr = clean_terr(ed)
                st.session_state.pop("ed_ter", None)
                st.rerun()

    with t4:
        tasks = ss.tasks
        if len(tasks):
            st.markdown("##### Mise à jour rapide")
            a, b, c3, d4 = st.columns([2.2, 1.6, 1.2, 1])
            name = a.selectbox("Tâche", tasks["Tâche"].tolist(), key="q_task")
            row = tasks[tasks["Tâche"] == name].iloc[0]
            av = b.slider("Avancement (%)", 0, 100, int(row["Avancement (%)"]), 5, key=f"q_av_{name}")
            cr = c3.number_input("Coût réel (k€)", 0.0, 1e7, float(row["Coût réel (k€)"]), 10.0, key=f"q_cr_{name}")
            d4.write("")
            if d4.button("✅ Mettre à jour", key="q_save"):
                i = tasks.index[tasks["Tâche"] == name][0]
                ss.tasks.loc[i, "Avancement (%)"] = float(av)
                ss.tasks.loc[i, "Coût réel (k€)"] = float(cr)
                st.toast("Tâche mise à jour ✅")
                st.rerun()
        st.markdown("##### Planning et budget (tableau éditable)")
        ed = st.data_editor(
            ss.tasks, num_rows="dynamic", hide_index=True, key="ed_tasks",
            column_config={"Début prévu": st.column_config.DateColumn(format="DD/MM/YYYY"),
                           "Fin prévue": st.column_config.DateColumn(format="DD/MM/YYYY"),
                           "Avancement (%)": st.column_config.NumberColumn(min_value=0, max_value=100, format="%.0f"),
                           "Coût prévu (k€)": st.column_config.NumberColumn(format="%.0f", min_value=0),
                           "Coût réel (k€)": st.column_config.NumberColumn(format="%.0f", min_value=0)})
        cc = st.columns(3)
        if cc[0].button("💾 Enregistrer le planning", key="tk_sv"):
            ss.tasks = clean_tasks(ed)
            st.session_state.pop("ed_tasks", None)
            st.rerun()
        if cc[1].button("🎲 Recharger la démo", key="tk_demo"):
            ss.tasks = make_demo_tasks(p)
            st.session_state.pop("ed_tasks", None)
            st.rerun()
        cc[2].download_button("⬇️ Télécharger", ss.tasks.to_csv(index=False).encode("utf-8"), "planning.csv", "text/csv", key="dl_tk")
        csv_importer("CSV planning", clean_tasks, "tasks", "tk")


def page_ausc():
    ss = st.session_state
    hero("📈 Auscultation", "Piézomètres, inclinomètres, tassements, fissures, pompage et vibrations : tendances, seuils et anomalies")
    df = ss.mesures
    if df.empty:
        st.info("Aucune mesure : ajoutez-en dans « Collecte des données ».")
        return
    with st.expander("⚙️ Seuils d'alerte et d'alarme (modifiables)"):
        ss.seuils = st.data_editor(ss.seuils, hide_index=True, key="ed_seuils", disabled=["Type", "Unité", "Sens"],
                                   column_config={"Seuil d'alerte": st.column_config.NumberColumn(format="%.2f"),
                                                  "Seuil d'alarme": st.column_config.NumberColumn(format="%.2f")})
        st.caption("Sens « Max » : alerte quand la valeur dépasse le seuil. Sens « Min » : alerte quand elle passe sous le seuil (ex. marge nappe).")
    seuils = ss.seuils

    f1, f2, f3 = st.columns([1.2, 1.6, 1.4])
    all_types = sorted(df["Type"].unique())
    sel_types = f1.multiselect("Types", all_types, default=all_types[:1], key="f_types")
    caps = sorted(df.loc[df["Type"].isin(sel_types), "Capteur"].unique())
    sel_caps = f2.multiselect("Capteurs", caps, default=caps, key="f_caps")
    dmin, dmax = df["Date"].min().date(), df["Date"].max().date()
    rng = f3.date_input("Période", (dmin, dmax), min_value=dmin, max_value=dmax, key="f_range")
    d0, d1 = (rng[0], rng[1]) if isinstance(rng, (list, tuple)) and len(rng) == 2 else (dmin, dmax)
    dff = df[df["Capteur"].isin(sel_caps) & (df["Date"].dt.date >= d0) & (df["Date"].dt.date <= d1)]
    if dff.empty:
        st.warning("Aucune mesure pour cette sélection.")
        return
    o1, o2 = st.columns(2)
    win = o1.slider("Moyenne mobile (jours, 0 = désactivée)", 0, 30, 7, key="f_win")
    show_out = o2.checkbox("Détecter les anomalies (méthode MAD)", value=True, key="f_out")

    fig = go.Figure()
    n_out = 0
    for i, (cap, g) in enumerate(dff.groupby("Capteur")):
        g = g.sort_values("Date")
        col = PALETTE[i % len(PALETTE)]
        fig.add_trace(go.Scatter(x=g["Date"], y=g["Valeur"], mode="lines", name=cap, line=dict(color=col, width=1.8),
                                 opacity=0.9 if win == 0 else 0.4))
        if win > 0:
            ma = g.set_index("Date")["Valeur"].rolling(f"{win}D", min_periods=1).mean()
            fig.add_trace(go.Scatter(x=ma.index, y=ma.values, mode="lines", name=f"{cap} (moy. {win} j)", line=dict(color=col, width=3.2)))
        if show_out and len(g) >= 10:
            mask = robust_outliers(g["Valeur"].values)
            n_out += int(mask.sum())
            if mask.any():
                fig.add_trace(go.Scatter(x=g["Date"][mask], y=g["Valeur"][mask], mode="markers", name=f"Anomalies {cap}",
                                         marker=dict(symbol="x", size=10, color=RED, line=dict(width=2, color="white"))))
    types_in = dff["Type"].unique()
    if len(types_in) == 1:
        row = seuils[seuils["Type"] == types_in[0]]
        if not row.empty:
            fig.add_hline(y=float(row.iloc[0]["Seuil d'alerte"]), line=dict(color=AMBER, dash="dash"), annotation_text="Alerte", annotation_font_color=AMBER)
            fig.add_hline(y=float(row.iloc[0]["Seuil d'alarme"]), line=dict(color=RED, dash="dash"), annotation_text="Alarme", annotation_font_color=RED)
    fig.update_yaxes(title=" / ".join(sorted({UNITS.get(t, "") for t in types_in})))
    st.plotly_chart(style_fig(fig, 460, "Évolution temporelle"), key="an_ts")

    summ = sensor_summary(dff, seuils)
    c = st.columns(4)
    c[0].metric("Mesures filtrées", fmt_int(len(dff)))
    c[1].metric("Capteurs", len(summ))
    c[2].metric("Anomalies détectées", n_out)
    c[3].metric("Capteurs hors seuil", int((summ["Statut"] != "Normal").sum()))

    st.markdown("#### Synthèse par capteur")
    rows = []
    for _, r in summ.iterrows():
        arrow = "↗" if r["Tendance"] > 1e-4 else ("↘" if r["Tendance"] < -1e-4 else "→")
        rows.append([r["Capteur"], r["Type"], r["N"], f"{r['Min']:.2f}", f"{r['Moyenne']:.2f}", f"{r['Max']:.2f}",
                     f"{r['Dernière']:.2f} {r['Unité']}", r["Date"], f"{arrow} {r['Tendance']:+.4f} {r['Unité']}/j", status_badge(r["Statut"])])
    html_table(["Capteur", "Type", "N", "Min", "Moy.", "Max", "Dernière valeur", "Date", "Tendance", "Statut"], rows)

    tb1, tb2, tb3 = st.tabs(["🔗 Corrélations", "🎯 Relation entre 2 capteurs", "📊 Distributions"])
    daily = df.assign(day=df["Date"].dt.floor("D")).pivot_table(index="day", columns="Capteur", values="Valeur", aggfunc="mean")
    with tb1:
        cols = [c for c in daily.columns if c in sel_caps] if len(sel_caps) >= 2 else list(daily.columns)
        if len(cols) >= 2:
            corr = daily[cols].corr()
            hm = go.Figure(go.Heatmap(z=corr.values, x=corr.columns, y=corr.index, zmin=-1, zmax=1,
                                      colorscale=[[0, RED], [0.5, "#f8fafc"], [1, BLUE]], text=np.round(corr.values, 2),
                                      texttemplate="%{text}", colorbar=dict(title="r")))
            st.plotly_chart(style_fig(hm, 480, "Matrice de corrélation (moyennes journalières)"), key="an_corr")
        else:
            st.info("Sélectionnez au moins 2 capteurs.")
    with tb2:
        if daily.shape[1] >= 2:
            ca, cb = st.columns(2)
            xs_ = ca.selectbox("Capteur X (cause)", list(daily.columns), index=0, key="rel_x")
            ys_ = cb.selectbox("Capteur Y (réponse)", list(daily.columns), index=min(1, daily.shape[1] - 1), key="rel_y")
            pair = daily[[xs_, ys_]].dropna() if xs_ != ys_ else pd.DataFrame()
            if len(pair) >= 5:
                k, b0 = np.polyfit(pair[xs_], pair[ys_], 1)
                r2 = float(np.corrcoef(pair[xs_], pair[ys_])[0, 1] ** 2)
                xx = np.linspace(pair[xs_].min(), pair[xs_].max(), 50)
                sc = go.Figure()
                sc.add_trace(go.Scatter(x=pair[xs_], y=pair[ys_], mode="markers", name="Jours",
                                        marker=dict(size=7, color=np.arange(len(pair)), colorscale="Blues", showscale=True,
                                                    colorbar=dict(title="Temps"), opacity=0.9)))
                sc.add_trace(go.Scatter(x=xx, y=k * xx + b0, mode="lines", name=f"y = {k:.3f}x + {b0:.2f} (R² = {r2:.2f})",
                                        line=dict(color=AMBER, width=3)))
                sc.update_xaxes(title=xs_)
                sc.update_yaxes(title=ys_)
                st.plotly_chart(style_fig(sc, 430, f"{ys_} en fonction de {xs_}"), key="an_sc")
            else:
                st.info("Choisissez deux capteurs différents avec assez de jours en commun.")
    with tb3:
        bx = go.Figure()
        for i, (cap, g) in enumerate(dff.groupby("Capteur")):
            bx.add_trace(go.Violin(y=g["Valeur"], name=cap, box_visible=True, meanline_visible=True,
                                   line_color=PALETTE[i % len(PALETTE)], opacity=0.75))
        st.plotly_chart(style_fig(bx, 420, "Distribution des mesures"), key="an_dist")


def page_beton():
    ss = st.session_state
    hero("🧪 Contrôle du béton", "Conformité des résistances à 28 jours (EN 206 simplifiée), prévision à partir des essais à 7 jours")
    dfb = ss.beton
    if dfb.empty:
        st.info("Aucun essai : saisissez-en dans « Collecte des données ».")
        return
    bs = beton_stats(dfb)
    d28 = dfb[dfb["Âge (j)"] == 28]
    c = st.columns(4)
    c[0].metric("Essais enregistrés", len(dfb))
    c[1].metric("Résistance moyenne à 28 j", f"{d28['Résistance (MPa)'].mean():.1f} MPa" if len(d28) else "-")
    c[2].metric("Résultat minimal à 28 j", f"{d28['Résistance (MPa)'].min():.1f} MPa" if len(d28) else "-")
    c[3].metric("Classes conformes", f"{int((bs['statut'] == 'Conforme').sum()) if len(bs) else 0} / {len(bs)}")

    st.markdown("#### Conformité par classe (essais à 28 jours)")
    if len(bs):
        rows = []
        for _, r in bs.iterrows():
            if pd.isna(r["c1"]):
                rows.append([r["Classe"], r["n"], "-", f"{r['fcm']:.1f}", f"{r['fmin']:.1f}", "-", "-", "<span class='badge info'>Insuffisant (n&lt;3)</span>"])
            else:
                rows.append([r["Classe"], r["n"], f"{r['fck']:.0f}", f"{r['fcm']:.1f}", f"{r['fmin']:.1f}",
                             f"≥ {r['lim1']:.1f} {badge(r['c1'], 'OK', 'NON')}", f"≥ {r['lim2']:.1f} {badge(r['c2'], 'OK', 'NON')}",
                             badge(r["statut"] == "Conforme")])
        html_table(["Classe", "n", "fck", "fcm", "fmin", "Critère moyenne", "Critère individuel", "Verdict"], rows)
        st.caption("n < 15 : fcm ≥ fck + 4 MPa ; n ≥ 15 : fcm ≥ fck + 1,48 σ. Individuel : chaque résultat ≥ fck - 4 MPa. Résistances sur éprouvettes cylindriques.")
    else:
        st.info("Pas encore de résultat à 28 jours.")

    f1, f2 = st.columns([1, 3])
    classes = sorted(dfb["Classe"].unique())
    sel = f1.multiselect("Classes affichées", classes, default=classes, key="bet_cl")
    dsel = dfb[dfb["Classe"].isin(sel)]
    fig = go.Figure()
    for i, (cl, g) in enumerate(dsel.groupby("Classe")):
        for age, sym in [(7, "circle-open"), (28, "circle")]:
            gg = g[g["Âge (j)"] == age]
            if len(gg):
                fig.add_trace(go.Scatter(x=gg["Date"], y=gg["Résistance (MPa)"], mode="markers", name=f"{cl} - {age} j",
                                         text=gg["Élément"], marker=dict(size=11, symbol=sym, color=PALETTE[i % len(PALETTE)],
                                                                         line=dict(width=2, color=PALETTE[i % len(PALETTE)])),
                                         hovertemplate="%{text}<br>%{y:.1f} MPa<extra></extra>"))
        fck = parse_fck(cl)
        if fck:
            fig.add_hline(y=fck, line=dict(color=PALETTE[i % len(PALETTE)], dash="dash", width=1),
                          annotation_text=f"fck {cl}", annotation_font_color=PALETTE[i % len(PALETTE)])
    fig.update_yaxes(title="Résistance (MPa)")
    with f2:
        st.plotly_chart(style_fig(fig, 420, "Carte de contrôle des résistances"), key="bet_ctrl")

    t1, t2 = st.columns(2)
    fc = beton_forecast(dsel)
    with t1:
        st.markdown("#### Prévision à 28 jours")
        pend = fc[~fc["Déjà testé à 28 j"]]
        if len(pend):
            rows = [[r["Élément"], r["Classe"], f"{r['Résistance (MPa)']:.1f}", f"{r['f28_est']:.1f}", f"≥ {r['fck'] + 4:.0f}",
                     badge(bool(r["OK"]), "OK", "À SURVEILLER")] for _, r in pend.iterrows()]
            html_table(["Élément", "Classe", "f7 (MPa)", "f28 estimée", "Cible", "Statut"], rows)
            st.caption("Estimation indicative : f28 ≈ f7 / 0,65 (ciment courant). À remplacer par la courbe de durcissement du fournisseur.")
        else:
            st.info("Tous les éléments testés à 7 jours ont déjà leur résultat à 28 jours.")
    with t2:
        st.markdown("#### Ouvrabilité et température")
        sl = go.Figure()
        sl.add_trace(go.Scatter(x=dsel["Date"], y=dsel["Affaissement (mm)"], mode="markers", name="Affaissement (mm)",
                                marker=dict(color=BLUE, size=9)))
        sl.add_trace(go.Scatter(x=dsel["Date"], y=dsel["T° béton (°C)"], mode="markers", name="Température (°C)", yaxis="y2",
                                marker=dict(color=AMBER, size=9, symbol="diamond")))
        sl.update_layout(yaxis=dict(title="Affaissement (mm)"), yaxis2=dict(title="°C", overlaying="y", side="right", showgrid=False))
        st.plotly_chart(style_fig(sl, 340), key="bet_slump")


def page_avancement():
    ss = st.session_state
    hero("📅 Avancement & coûts", "Méthode de la valeur acquise : délais (SPI), coûts (CPI), planning et courbe en S")
    tasks = ss.tasks
    if tasks.empty:
        st.info("Aucune tâche : renseignez le planning dans « Collecte des données ».")
        return
    ev = evm(tasks, today())
    delay = delay_days(tasks, ev["ev"])
    c = st.columns(5)
    c[0].metric("Budget (BAC)", f"{fmt_int(ev['bac'])} k€")
    c[1].metric("Valeur acquise (EV)", f"{fmt_int(ev['ev'])} k€")
    c[2].metric("Coût réel (AC)", f"{fmt_int(ev['ac'])} k€")
    c[3].metric("Coût final estimé", f"{fmt_int(ev['eac'])} k€", f"{fmt_int(ev['eac'] - ev['bac'])} k€",
                delta_color="inverse" if ev["eac"] > ev["bac"] else "normal")
    c[4].metric("Retard estimé", f"{max(delay, 0)} j")
    c = st.columns(4)
    c[0].metric("SPI", f"{ev['spi']:.2f}", "retard" if ev["spi"] < 0.95 else "conforme", delta_color="inverse" if ev["spi"] < 0.95 else "normal")
    c[1].metric("CPI", f"{ev['cpi']:.2f}", "dérive" if ev["cpi"] < 0.95 else "maîtrisé", delta_color="inverse" if ev["cpi"] < 0.95 else "normal")
    c[2].metric("Écart délais (EV - PV)", f"{fmt_int(ev['ev'] - ev['pv'])} k€")
    c[3].metric("Écart coûts (EV - AC)", f"{fmt_int(ev['ev'] - ev['ac'])} k€")

    st.plotly_chart(fig_scurve(tasks, ev), key="av_s")

    t = tasks.sort_values("Début prévu")
    dur_ms = (t["Fin prévue"] - t["Début prévu"]).dt.total_seconds() * 1000
    g = go.Figure()
    g.add_trace(go.Bar(y=t["Tâche"], x=dur_ms, base=t["Début prévu"], orientation="h", name="Prévu", marker_color="#c9d8e8",
                       customdata=t["Avancement (%)"], hovertemplate="%{y}<br>Avancement : %{customdata:.0f} %<extra></extra>"))
    g.add_trace(go.Bar(y=t["Tâche"], x=dur_ms * t["Avancement (%)"] / 100, base=t["Début prévu"], orientation="h",
                       name="Réalisé", marker_color=BLUE, hoverinfo="skip"))
    g.update_layout(barmode="overlay")
    g.update_yaxes(autorange="reversed")
    g.update_xaxes(type="date")
    g.add_shape(type="line", x0=today(), x1=today(), y0=0, y1=1, yref="paper", line=dict(color=RED, dash="dot", width=2))
    g.add_annotation(x=today(), y=1, yref="paper", text="Aujourd'hui", showarrow=False, yshift=8, font=dict(color=RED))
    st.plotly_chart(style_fig(g, 120 + 34 * len(t), "Planning (Gantt)"), key="av_gantt")

    lots = tasks.assign(EV=tasks["Coût prévu (k€)"] * tasks["Avancement (%)"] / 100).groupby("Lot").agg(
        Prévu=("Coût prévu (k€)", "sum"), Acquis=("EV", "sum"), Réel=("Coût réel (k€)", "sum")).reset_index()
    b = go.Figure()
    b.add_trace(go.Bar(x=lots["Lot"], y=lots["Prévu"], name="Budget prévu", marker_color="#c9d8e8"))
    b.add_trace(go.Bar(x=lots["Lot"], y=lots["Acquis"], name="Valeur acquise", marker_color=TEAL))
    b.add_trace(go.Bar(x=lots["Lot"], y=lots["Réel"], name="Coût réel", marker_color=AMBER))
    b.update_layout(barmode="group")
    b.update_yaxes(title="k€")
    st.plotly_chart(style_fig(b, 380, "Budget, valeur acquise et coût réel par lot"), key="av_lots")


def page_qualite():
    ss = st.session_state
    hero("⚠️ Qualité & sécurité", "Registre des non-conformités, incidents et réserves, avec suivi des échéances")
    with st.expander("➕ Déclarer une non-conformité / un incident", expanded=False):
        a, b, c3 = st.columns(3)
        typ = a.selectbox("Type", NC_TYPES, key="nc_type")
        zone = a.text_input("Zone", key="nc_zone")
        grav = b.selectbox("Gravité", GRAVITES, index=1, key="nc_grav")
        resp = b.text_input("Responsable", key="nc_resp")
        ech = c3.date_input("Échéance", date.today() + timedelta(days=7), key="nc_ech")
        desc = st.text_area("Description", key="nc_desc")
        if st.button("Enregistrer", key="nc_save"):
            if not desc.strip():
                st.error("Décrivez la non-conformité.")
            else:
                new = pd.DataFrame([[pd.Timestamp.now(), typ, desc, zone, grav, resp, "Ouverte", pd.Timestamp(ech)]], columns=NC_COLS)
                ss.nc = clean_nc(pd.concat([ss.nc, new], ignore_index=True))
                st.toast("Enregistré ✅")
                st.rerun()
    nc = ss.nc
    open_ = nc[nc["Statut"] != "Clôturée"]
    late = open_[open_["Échéance"] < today()]
    c = st.columns(4)
    c[0].metric("Total déclarées", len(nc))
    c[1].metric("Ouvertes / en cours", len(open_))
    c[2].metric("Critiques ouvertes", int((open_["Gravité"] == "Critique").sum()))
    c[3].metric("En retard", len(late), delta_color="off")
    if len(nc):
        l, r = st.columns(2)
        with l:
            g = nc.groupby("Type").size().reset_index(name="n")
            f = go.Figure(go.Bar(x=g["Type"], y=g["n"], marker_color=BLUE))
            st.plotly_chart(style_fig(f, 320, "Par type"), key="nc_type_ch")
        with r:
            g = nc.groupby("Statut").size().reset_index(name="n")
            colmap = {"Ouverte": RED, "En cours": AMBER, "Clôturée": GREEN}
            f = go.Figure(go.Pie(labels=g["Statut"], values=g["n"], hole=0.55, marker=dict(colors=[colmap.get(s, GREY) for s in g["Statut"]])))
            st.plotly_chart(style_fig(f, 320, "Par statut"), key="nc_stat_ch")
    st.markdown("#### Registre (modifiable)")
    ed = st.data_editor(
        nc.sort_values("Date", ascending=False).reset_index(drop=True), num_rows="dynamic", hide_index=True, key="ed_nc",
        column_config={"Date": st.column_config.DateColumn(format="DD/MM/YYYY"),
                       "Échéance": st.column_config.DateColumn(format="DD/MM/YYYY"),
                       "Type": st.column_config.SelectboxColumn(options=NC_TYPES),
                       "Gravité": st.column_config.SelectboxColumn(options=GRAVITES),
                       "Statut": st.column_config.SelectboxColumn(options=STATUTS)})
    if st.button("💾 Enregistrer le registre", key="nc_sv"):
        ss.nc = clean_nc(ed)
        st.session_state.pop("ed_nc", None)
        st.rerun()


def build_report(p):
    ss = st.session_state
    L = [f"# Rapport de suivi de chantier - {p['nom']}", f"_Généré le {datetime.now().strftime('%d/%m/%Y %H:%M')}_", "",
         "## 1. Projet", f"- Bâtiment R+{p['n_etages']} sur {p['n_ss']} sous-sol(s), emprise {p['emprise']:.0f} m²",
         f"- Profondeur de fouille : {excavation_depth(p):.1f} m ; nappe à {p['z_nappe']:.1f} m sous TN"]
    ts = terr_stats(p, ss.terr)
    ep = earth_pressure(p, p["pompage"])
    up = uplift_check(p)
    L += ["", "## 2. Sous-sol",
          f"- Terrassement : {ts['done']:.0f} / {ts['Vb']:.0f} m³ ({ts['pct']:.0f} %), {ts['trucks']:.0f} camions",
          f"- Poussée sur paroi : {ep['P']:.0f} kN/ml (Ka = {ep['ka']:.3f}), réaction par niveau d'étais {ep['react']:.0f} kN/ml",
          f"- Soulèvement hydraulique : FS chantier {up['fs_c']:.2f} ({'OK' if up['ok_c'] else 'NON'}), FS final {up['fs_f']:.2f} ({'OK' if up['ok_f'] else 'NON'})"]
    if len(ss.tasks):
        ev = evm(ss.tasks, today())
        L += ["", "## 3. Avancement et coûts", f"- Avancement global : {ev['pct']:.1f} % ; SPI = {ev['spi']:.2f} ; CPI = {ev['cpi']:.2f}",
              f"- Budget {fmt_int(ev['bac'])} k€ ; coût réel {fmt_int(ev['ac'])} k€ ; coût final estimé {fmt_int(ev['eac'])} k€"]
    if len(ss.mesures):
        s = sensor_summary(ss.mesures, ss.seuils)
        L += ["", "## 4. Auscultation", "| Capteur | Type | Dernière valeur | Tendance/j | Statut |", "|---|---|---|---|---|"]
        for _, r in s.iterrows():
            L.append(f"| {r['Capteur']} | {r['Type']} | {r['Dernière']:.2f} {r['Unité']} | {r['Tendance']:+.4f} | {r['Statut']} |")
    bs = beton_stats(ss.beton) if len(ss.beton) else pd.DataFrame()
    if len(bs):
        L += ["", "## 5. Béton (28 jours)", "| Classe | n | fck | fcm | fmin | Verdict |", "|---|---|---|---|---|---|"]
        for _, r in bs.iterrows():
            fck = "-" if r["fck"] is None else f"{r['fck']:.0f}"
            L.append(f"| {r['Classe']} | {r['n']} | {fck} | {r['fcm']:.1f} | {r['fmin']:.1f} | {r['statut']} |")
    nc = ss.nc[ss.nc["Statut"] != "Clôturée"]
    L += ["", "## 6. Non-conformités ouvertes", f"- {len(nc)} ouverte(s), dont {int((nc['Gravité'] == 'Critique').sum())} critique(s)"]
    for _, r in nc.iterrows():
        L.append(f"  - [{r['Gravité']}] {r['Description']} ({r['Zone']}) - échéance {r['Échéance'].strftime('%d/%m/%Y') if pd.notna(r['Échéance']) else '-'}")
    L += ["", "> Document d'aide au suivi : à valider par les intervenants qualifiés."]
    return "\n".join(L)


def page_rapport():
    ss = st.session_state
    hero("📄 Rapport & export", "Synthèse téléchargeable et export de toutes les données")
    md = build_report(ss.proj)
    c = st.columns(5)
    c[0].download_button("⬇️ Rapport (.md)", md.encode("utf-8"), "rapport_chantier.md", "text/markdown", key="dl_rap")
    c[1].download_button("⬇️ Mesures", ss.mesures.to_csv(index=False).encode("utf-8"), "mesures.csv", "text/csv", key="dl_r1")
    c[2].download_button("⬇️ Béton", ss.beton.to_csv(index=False).encode("utf-8"), "beton.csv", "text/csv", key="dl_r2")
    c[3].download_button("⬇️ Planning", ss.tasks.to_csv(index=False).encode("utf-8"), "planning.csv", "text/csv", key="dl_r3")
    c[4].download_button("⬇️ Non-conformités", ss.nc.to_csv(index=False).encode("utf-8"), "non_conformites.csv", "text/csv", key="dl_r4")
    st.markdown(md)


# =============================================================================
# 6. NAVIGATION
# =============================================================================
PAGES = {
    "🏠 Tableau de bord": page_dashboard,
    "🏗️ Projet & sous-sol": page_projet,
    "📡 Collecte des données": page_collecte,
    "📈 Auscultation": page_ausc,
    "🧪 Contrôle du béton": page_beton,
    "📅 Avancement & coûts": page_avancement,
    "⚠️ Qualité & sécurité": page_qualite,
    "📄 Rapport & export": page_rapport,
}


def main():
    init_state()
    with st.sidebar:
        st.markdown("<p class='brand'>Site<span>Lab</span></p>", unsafe_allow_html=True)
        st.caption("Suivi de chantier · Bâtiment avec sous-sol")
        st.session_state.proj["nom"] = st.text_input("Nom du projet", st.session_state.proj["nom"], key="w_nom")
        page = st.radio("Navigation", list(PAGES.keys()), label_visibility="collapsed")
        st.divider()
        st.caption("Outil d'aide au suivi : à valider par un ingénieur qualifié.")
    PAGES[page]()


main()
