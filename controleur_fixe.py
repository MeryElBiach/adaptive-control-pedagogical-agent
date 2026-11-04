"""Contrôleur fixe : résoudre -> vérifier -> corriger seulement si WRONG -> arrêter.

Utilisation :
    python controleur_fixe.py 5      # test rapide sur les 5 premiers exercices
    python controleur_fixe.py        # les N_FIXE (100) premiers exercices

Chaque exercice est enregistré dans resultats/fixe.csv dès qu'il est terminé.
Si le programme s'arrête (quota du jour, coupure réseau...), relancer la même
commande reprend là où il s'était arrêté. Pour tout recommencer, supprimer le fichier.
"""

import os
import sys

import pandas as pd

from agent import corriger, resoudre, verifier
from config import N_FIXE, RESULTATS_DIR
from donnees import charger_exercices
from extraction import est_juste, extraire_nombre, extraire_verdict
from resultats import charger_resultats, tableau_resultats

CHEMIN_FIXE = os.path.join(RESULTATS_DIR, "fixe.csv")


def controleur_fixe(question):
    """Applique la séquence fixe à un exercice et renvoie toutes les étapes.

    Si le verdict est introuvable (None), on le traite comme CORRECT : on s'arrête.
    """
    texte_initial = resoudre(question)                      # appel 1
    texte_verification = verifier(question, texte_initial)  # appel 2
    verdict = extraire_verdict(texte_verification)

    texte_correction = ""
    texte_final = texte_initial
    nb_appels = 2
    if verdict == "WRONG":
        texte_correction = corriger(question, texte_initial, texte_verification)  # appel 3
        texte_final = texte_correction
        nb_appels = 3

    return {
        "texte_initial": texte_initial,
        "reponse_initiale": extraire_nombre(texte_initial),
        "texte_verification": texte_verification,
        "verdict": verdict,
        "texte_correction": texte_correction,
        "reponse_finale": extraire_nombre(texte_final),
        "nb_appels": nb_appels,
    }


def ids_deja_faits():
    """Renvoie les id des exercices déjà enregistrés (pour reprendre après un arrêt)."""
    if not os.path.exists(CHEMIN_FIXE):
        return set()
    return set(pd.read_csv(CHEMIN_FIXE, usecols=["id"])["id"])


def enregistrer_ligne(ligne):
    """Ajoute une ligne au CSV (crée le fichier et l'en-tête au premier exercice)."""
    os.makedirs(RESULTATS_DIR, exist_ok=True)
    nouveau = not os.path.exists(CHEMIN_FIXE)
    pd.DataFrame([ligne]).to_csv(CHEMIN_FIXE, mode="a", header=nouveau, index=False)


def lancer(n):
    exercices = charger_exercices(n)
    faits = ids_deja_faits()
    a_faire = exercices[~exercices["id"].isin(faits)]
    print(f"{len(exercices)} exercices demandés, {len(faits & set(exercices['id']))} déjà faits, {len(a_faire)} à faire.\n")

    for numero, ex in enumerate(a_faire.itertuples(index=False), start=1):
        etapes = controleur_fixe(ex.question)
        ligne = {
            "id": ex.id,
            "longueur": ex.longueur,
            **etapes,
            "corrige": ex.corrige,
            "juste_initiale": est_juste(etapes["reponse_initiale"], ex.corrige),
            "juste_finale": est_juste(etapes["reponse_finale"], ex.corrige),
        }
        enregistrer_ligne(ligne)
        print(
            f"[{numero}/{len(a_faire)}] id={ex.id:<4} {ex.longueur:<5} "
            f"initiale={'juste' if ligne['juste_initiale'] else 'faux '} "
            f"verdict={str(etapes['verdict']):<7} "
            f"finale={'juste' if ligne['juste_finale'] else 'faux '} "
            f"appels={etapes['nb_appels']}"
        )

    # Résultats sur les n exercices demandés
    df = charger_resultats(CHEMIN_FIXE)
    df = df[df["id"].isin(exercices["id"])]
    print("\n=== Résultats du contrôleur fixe ===")
    print(tableau_resultats(df).to_string())
    print("\nRéponses initiales sans nombre lisible :", df["reponse_initiale"].isna().sum())
    print("Verdicts illisibles :", df["verdict"].isna().sum())


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_FIXE
    lancer(n)