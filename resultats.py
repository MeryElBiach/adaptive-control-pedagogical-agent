"""Calcul des mesures à partir du CSV produit par un contrôleur.

Colonnes attendues dans le CSV :
- juste_finale (True/False) : la réponse finale est-elle juste ?
- nb_appels (entier)        : nombre d'appels au modèle pour l'exercice
- longueur ("court"/"long") : facultatif, pour séparer les résultats
- juste_initiale (True/False) : facultatif, pour la référence « sans vérification »

Utilisation : python resultats.py resultats/fixe.csv
Sans argument, le script tourne sur un petit exemple inventé.
"""

import sys

import pandas as pd


def mesures(df):
    """Renvoie les mesures principales pour un groupe d'exercices."""
    resultat = {
        "exercices": len(df),
        "% juste (contrôleur)": round(100 * df["juste_finale"].mean(), 1),
        "appels moyens": round(df["nb_appels"].mean(), 2),
    }
    if "juste_initiale" in df.columns:
        resultat["% juste (sans vérification)"] = round(100 * df["juste_initiale"].mean(), 1)
    return resultat


def tableau_resultats(df):
    """Mesures pour tous les exercices, puis séparées en courts et longs."""
    lignes = {"tous": mesures(df)}
    if "longueur" in df.columns:
        for groupe in ("court", "long"):
            partie = df[df["longueur"] == groupe]
            if len(partie) > 0:
                lignes[groupe] = mesures(partie)
    return pd.DataFrame(lignes).T


def charger_resultats(chemin):
    df = pd.read_csv(chemin)
    for colonne in ("juste_finale", "juste_initiale"):
        if colonne in df.columns:
            df[colonne] = df[colonne].astype(str).str.lower().isin(["true", "1", "oui"])
    return df


if __name__ == "__main__":
    if len(sys.argv) > 1:
        df = charger_resultats(sys.argv[1])
    else:
        print("Aucun fichier donné : exemple inventé à 4 exercices.\n")
        df = pd.DataFrame({
            "longueur": ["court", "long", "court", "long"],
            "juste_initiale": [True, False, False, True],
            "juste_finale": [True, True, False, True],
            "nb_appels": [2, 3, 2, 2],
        })
    print(tableau_resultats(df).to_string())