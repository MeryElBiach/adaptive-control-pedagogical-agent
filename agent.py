"""Les trois actions de l'agent. Chaque fonction fait UN appel à l'API Cloudflare Workers AI.

Test rapide (identifiants dans .env) : python agent.py
"""

import os
import time

import requests
from dotenv import load_dotenv

from config import MAX_TENTATIVES, MAX_TOKENS, MODELE, PAUSE_ENTRE_APPELS, SEED, TEMPERATURE

load_dotenv()

# --- Consignes (en anglais, comme les exercices) ---

CONSIGNE_RESOUDRE = """Solve the following math problem step by step.
At the end, write the final answer on its own line, in exactly this format:
Final answer: <number>

Problem:
{question}"""

CONSIGNE_VERIFIER = """You are checking a solution to a math problem.
Check every step carefully, including each calculation.
Reply in exactly this format:
VERDICT: CORRECT or WRONG
REASON: <one or two sentences>

Problem:
{question}

Solution to check:
{reponse}"""

CONSIGNE_CORRIGER = """Your previous solution to this math problem may contain an error.
Using the reviewer's remark, write a corrected solution step by step.
At the end, write the final answer on its own line, in exactly this format:
Final answer: <number>

Problem:
{question}

Your previous solution:
{reponse}

Reviewer's remark:
{remarque}"""

REMARQUE_PAR_DEFAUT = "No remark was given. Re-check every step and every calculation."


# --- Appel à l'API ---

def _url_et_entetes():
    """Construit l'adresse de l'API et l'en-tête d'authentification à partir du .env."""
    compte = os.getenv("CLOUDFLARE_ACCOUNT_ID")
    token = os.getenv("CLOUDFLARE_API_TOKEN")
    if not compte or not token:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID ou CLOUDFLARE_API_TOKEN introuvable : complète le fichier .env.")
    url = f"https://api.cloudflare.com/client/v4/accounts/{compte}/ai/run/{MODELE}"
    return url, {"Authorization": f"Bearer {token}"}


def _texte_de_la_reponse(donnees):
    """Récupère le texte du modèle dans la réponse JSON de Cloudflare."""
    resultat = donnees.get("result") or {}
    if isinstance(resultat, dict) and "response" in resultat:
        return resultat["response"] or ""
    if isinstance(resultat, dict) and "choices" in resultat:       # format de type OpenAI
        return resultat["choices"][0]["message"]["content"] or ""
    raise RuntimeError(f"Réponse inattendue de l'API : {str(donnees)[:300]}")


def appeler_llm(consigne):
    """Envoie une consigne au modèle et renvoie son texte.

    Erreur passagère (429 ou serveur) : on attend de plus en plus longtemps puis on réessaie.
    Quota quotidien épuisé : on s'arrête avec un message clair (inutile de réessayer).
    """
    url, entetes = _url_et_entetes()
    corps = {
        "messages": [{"role": "user", "content": consigne}],
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
        "seed": SEED,
    }
    for tentative in range(1, MAX_TENTATIVES + 1):
        try:
            reponse = requests.post(url, headers=entetes, json=corps, timeout=120)
        except requests.RequestException as erreur:
            statut, detail = None, str(erreur)
        else:
            if reponse.status_code == 200:
                if PAUSE_ENTRE_APPELS:
                    time.sleep(PAUSE_ENTRE_APPELS)
                return _texte_de_la_reponse(reponse.json())
            statut, detail = reponse.status_code, reponse.text[:300]
            if statut in (401, 403):
                raise RuntimeError(f"Accès refusé ({statut}) : vérifie l'Account ID et le token dans .env.\n{detail}")
            if "neuron" in detail.lower() or "daily" in detail.lower():
                raise RuntimeError(f"Quota gratuit du jour épuisé : reprendre demain (00:00 UTC).\n{detail}")
            if statut not in (429, 500, 502, 503, 504):
                raise RuntimeError(f"Erreur de l'API ({statut}) : {detail}")
        attente = 2 ** tentative
        print(f"  [tentative {tentative}/{MAX_TENTATIVES}] erreur {statut or 'réseau'}, nouvel essai dans {attente} s")
        time.sleep(attente)
    raise RuntimeError(f"Échec de l'appel au modèle après {MAX_TENTATIVES} tentatives.")


# --- Les trois actions ---

def resoudre(question):
    """Première réponse à l'exercice. Renvoie le texte du modèle."""
    return appeler_llm(CONSIGNE_RESOUDRE.format(question=question))


def verifier(question, reponse):
    """Vérifie une réponse. Renvoie le texte du modèle (VERDICT + REASON)."""
    return appeler_llm(CONSIGNE_VERIFIER.format(question=question, reponse=reponse))


def corriger(question, reponse, remarque=None):
    """Corrige une réponse, avec la remarque du vérificateur si elle existe.

    remarque=None permet de corriger sans vérification préalable (utile pour le RL).
    """
    return appeler_llm(CONSIGNE_CORRIGER.format(
        question=question,
        reponse=reponse,
        remarque=remarque or REMARQUE_PAR_DEFAUT,
    ))


if __name__ == "__main__":
    from extraction import extraire_nombre, extraire_verdict

    question = "Tom has 3 boxes of 12 pencils and gives away 5. How many pencils does he have left?"

    texte = resoudre(question)
    print("=== RÉSOUDRE ===\n" + texte)
    print("-> nombre extrait :", extraire_nombre(texte))

    texte_verif = verifier(question, texte)
    print("\n=== VÉRIFIER ===\n" + texte_verif)
    print("-> verdict extrait :", extraire_verdict(texte_verif))

    texte_corr = corriger(question, texte, texte_verif)
    print("\n=== CORRIGER ===\n" + texte_corr)
    print("-> nombre extrait :", extraire_nombre(texte_corr))