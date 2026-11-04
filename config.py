"""Paramètres communs du projet.

Ne modifier ces valeurs qu'en accord avec le binôme : les deux contrôleurs
doivent tourner avec exactement les mêmes réglages pour que la comparaison
soit valable.
"""

# --- Données (GSM8K) ---
SEED = 42              # graine du tirage de l'échantillon (et des réponses du modèle)
SPLIT = "test"         # split utilisé (1 319 exercices)
N_TOTAL = 1000         # taille de l'échantillon (servira au RL)
N_FIXE = 100           # exercices utilisés pour le contrôleur fixe
DATA_DIR = "data"
RESULTATS_DIR = "resultats"

# --- LLM (API Cloudflare Workers AI) ---
MODELE = "@cf/meta/llama-3.2-3b-instruct"   # petit modèle (~78 % sur GSM8K) : il fait assez d'erreurs
TEMPERATURE = 0            # réponses les plus stables possible
MAX_TOKENS = 600           # longueur maximale d'une réponse (256 par défaut chez Cloudflare : trop court)
PAUSE_ENTRE_APPELS = 1.0   # secondes entre deux appels
MAX_TENTATIVES = 5         # nouvelles tentatives en cas d'erreur passagère

# --- Agent ---
MAX_TOURS = 3          # vérifications + corrections maximum par exercice