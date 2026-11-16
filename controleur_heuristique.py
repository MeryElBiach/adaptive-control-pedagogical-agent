"""Contrôleur heuristique : vérifier seulement si l'énoncé est long.

Règle (écrite à la main) :
- énoncé court (<= seuil de mots) : résoudre -> arrêter                       (1 appel)
- énoncé long  (>  seuil de mots) : résoudre -> vérifier -> corriger si WRONG (2 ou 3 appels)

Aucun appel au modèle : tout est calculé à partir de resultats/fixe.csv,
qui contient déjà la réponse initiale ET la réponse après vérification.

Utilisation : python controleur_heuristique.py
"""

import os

from config import RESULTATS_DIR
from donnees import charger_seuil
from resultats import charger_resultats, tableau_resultats

CHEMIN_FIXE = os.path.join(RESULTATS_DIR, "fixe.csv")
CHEMIN_HEURISTIQUE = os.path.join(RESULTATS_DIR, "heuristique.csv")


def appliquer_regle(ligne):
    """Applique la règle heuristique à une ligne du fixe et renvoie la ligne de l'heuristique."""
    long = ligne["longueur"] == "long"
    return {
        "id": ligne["id"],
        "longueur": ligne["longueur"],
        "verifie": long,
        "reponse_initiale": ligne["reponse_initiale"],
        "reponse_finale": ligne["reponse_finale"] if long else ligne["reponse_initiale"],
        "corrige": ligne["corrige"],
        "juste_initiale": ligne["juste_initiale"],
        "juste_finale": ligne["juste_finale"] if long else ligne["juste_initiale"],
        "nb_appels": ligne["nb_appels"] if long else 1,
    }


def lancer():
    if not os.path.exists(CHEMIN_FIXE):
        raise FileNotFoundError("resultats/fixe.csv introuvable : fais d'abord « git pull ».")

    fixe = charger_resultats(CHEMIN_FIXE)
    heuristique = fixe.apply(appliquer_regle, axis=1, result_type="expand")
    heuristique.to_csv(CHEMIN_HEURISTIQUE, index=False)

    print(f"Règle : vérifier seulement si l'énoncé dépasse {charger_seuil():.0f} mots.")
    print(f"{len(heuristique)} exercices, dont {int(heuristique['verifie'].sum())} vérifiés (longs).")
    print(f"Résultats enregistrés dans {CHEMIN_HEURISTIQUE}\n")

    print("=== Résultats du contrôleur heuristique ===")
    print(tableau_resultats(heuristique).to_string())

    print("\n=== Comparaison sur les mêmes exercices ===")
    print(f"Sans vérification : {100 * fixe['juste_initiale'].mean():.1f} % juste, 1.00 appel")
    print(f"Fixe              : {100 * fixe['juste_finale'].mean():.1f} % juste, {fixe['nb_appels'].mean():.2f} appels")
    print(f"Heuristique       : {100 * heuristique['juste_finale'].mean():.1f} % juste, {heuristique['nb_appels'].mean():.2f} appels")


if __name__ == "__main__":
    lancer()