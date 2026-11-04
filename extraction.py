"""Récupération du nombre et du verdict dans les textes écrits par le modèle.

Test rapide : python extraction.py
"""

import re

from donnees import normaliser_nombre

# "Final answer: 31", "**Final Answer:** $1,250", "Final answer is 31", "Final answer: \boxed{31}"
MOTIF_REPONSE = re.compile(
    r"final\s+answer\s*\**\s*(?:is)?\s*[:：]?\s*\**\s*(?:\\boxed\{)?\s*\$?\s*(-?\d[\d,]*(?:\.\d+)?)",
    re.IGNORECASE,
)

# "VERDICT: CORRECT" ou "VERDICT: WRONG" (format demandé au vérificateur)
MOTIF_VERDICT = re.compile(r"verdict\s*\**\s*[:：]?\s*\**\s*(CORRECT|WRONG|INCORRECT)", re.IGNORECASE)


def extraire_nombre(texte):
    """Renvoie le nombre après 'Final answer', normalisé ('31'), ou None s'il est absent.

    Si le modèle écrit plusieurs 'Final answer', on garde la dernière.
    """
    if not texte:
        return None
    trouves = MOTIF_REPONSE.findall(texte)
    if not trouves:
        return None
    return normaliser_nombre(trouves[-1])


def extraire_verdict(texte):
    """Renvoie 'CORRECT', 'WRONG' ou None si le verdict est introuvable."""
    if not texte:
        return None
    trouve = MOTIF_VERDICT.search(texte)
    if trouve:
        mot = trouve.group(1).upper()
    else:
        # Le modèle n'a pas respecté le format : on cherche les mots en majuscules.
        mots = re.findall(r"\b(CORRECT|WRONG|INCORRECT)\b", texte)
        if not mots:
            return None
        mot = mots[0]
    return "WRONG" if mot in ("WRONG", "INCORRECT") else "CORRECT"


def est_juste(reponse, corrige):
    """Compare une réponse normalisée au corrigé. Une réponse absente (None) est fausse."""
    if reponse is None or corrige is None:
        return False
    try:
        return abs(float(reponse) - float(corrige)) < 1e-6
    except ValueError:
        return False


if __name__ == "__main__":
    cas_nombre = [
        ("3 x 12 = 36, 36 - 5 = 31.\nFinal answer: 31", "31"),
        ("**Final Answer:** $1,250.", "1250"),
        ("The final answer is 18.0", "18"),
        ("Final answer: \\boxed{42}", "42"),
        ("Final answer: 3.50 dollars", "3.5"),
        ("Final answer: -7", "-7"),
        ("Final answer: 10\n...\nFinal answer: 12", "12"),
        ("I think the result is 31.", None),
        ("", None),
    ]
    cas_verdict = [
        ("VERDICT: CORRECT\nREASON: all steps are right.", "CORRECT"),
        ("**Verdict:** WRONG\nReason: the pens are missing.", "WRONG"),
        ("VERDICT: INCORRECT", "WRONG"),
        ("The solution is WRONG because...", "WRONG"),
        ("Looks fine to me.", None),
    ]

    erreurs = 0
    for texte, attendu in cas_nombre:
        obtenu = extraire_nombre(texte)
        statut = "OK " if obtenu == attendu else "ERREUR"
        erreurs += obtenu != attendu
        print(f"[{statut}] extraire_nombre -> {obtenu!r} (attendu {attendu!r})")
    for texte, attendu in cas_verdict:
        obtenu = extraire_verdict(texte)
        statut = "OK " if obtenu == attendu else "ERREUR"
        erreurs += obtenu != attendu
        print(f"[{statut}] extraire_verdict -> {obtenu!r} (attendu {attendu!r})")

    print("\nTous les tests passent." if erreurs == 0 else f"\n{erreurs} test(s) en échec.")