"""Chargement de GSM8K, tirage de l'échantillon et calcul du seuil court / long.

À lancer UNE SEULE FOIS : python donnees.py
Les fichiers produits (data/exercices.csv et data/seuil.json) sont versionnés
sur GitHub pour que le binôme travaille sur exactement les mêmes exercices.
"""

import json
import os

import pandas as pd

from config import DATA_DIR, N_TOTAL, SEED, SPLIT

CHEMIN_EXERCICES = os.path.join(DATA_DIR, "exercices.csv")
CHEMIN_SEUIL = os.path.join(DATA_DIR, "seuil.json")


def normaliser_nombre(texte):
    """'1,250' -> '1250' ; '18.0' -> '18' ; '$3.50' -> '3.5'. Renvoie None si illisible."""
    if texte is None:
        return None
    nettoye = str(texte).replace(",", "").replace("$", "").strip().rstrip(".")
    try:
        valeur = float(nettoye)
    except ValueError:
        return None
    return str(int(valeur)) if valeur == int(valeur) else str(valeur)


def extraire_corrige(solution):
    """Récupère le nombre écrit après '####' dans la solution de GSM8K."""
    return normaliser_nombre(solution.split("####")[-1])


def construire_exercices():
    """Télécharge GSM8K, tire l'échantillon, calcule le seuil et sauvegarde le tout."""
    from datasets import load_dataset  # import ici : inutile pour charger_exercices()

    brut = load_dataset("openai/gsm8k", "main", split=SPLIT)
    echantillon = brut.shuffle(seed=SEED).select(range(N_TOTAL))

    df = pd.DataFrame({
        "id": range(N_TOTAL),
        "question": echantillon["question"],
        "corrige": [extraire_corrige(s) for s in echantillon["answer"]],
    })
    df["nb_mots"] = df["question"].str.split().str.len()

    seuil = float(df["nb_mots"].median())
    df["longueur"] = df["nb_mots"].apply(lambda n: "long" if n > seuil else "court")

    os.makedirs(DATA_DIR, exist_ok=True)
    df.to_csv(CHEMIN_EXERCICES, index=False)
    with open(CHEMIN_SEUIL, "w", encoding="utf-8") as f:
        json.dump({"seuil_mots": seuil}, f)
    return df


def charger_exercices(n=None):
    """Renvoie les exercices (DataFrame : id, question, corrige, nb_mots, longueur).

    n : nombre d'exercices à garder (les n premiers). None = tous.
    """
    df = pd.read_csv(CHEMIN_EXERCICES, dtype={"corrige": str})
    return df if n is None else df.head(n)


def charger_seuil():
    """Renvoie le seuil de mots qui sépare les énoncés courts des longs."""
    with open(CHEMIN_SEUIL, encoding="utf-8") as f:
        return json.load(f)["seuil_mots"]


if __name__ == "__main__":
    df = construire_exercices()
    print(df.head(3).to_string())
    print("\nCorrigés manquants :", df["corrige"].isna().sum())
    print("Seuil (mots) :", charger_seuil())
    print(df["longueur"].value_counts().to_string())