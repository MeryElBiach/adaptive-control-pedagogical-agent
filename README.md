# Contrôle adaptatif d'un agent pédagogique

Projet de fin de semestre (S5, ENSIAS) — Binôme : Hind et Meryem — Encadrant : M. Rachad.

Un agent résout des exercices de mathématiques (GSM8K) avec un LLM, puis décide s'il doit vérifier sa réponse, la corriger ou s'arrêter. Le projet compare trois façons de prendre cette décision : contrôle fixe, heuristique et appris (Q-learning), selon deux mesures : le taux de bonnes réponses et le nombre d'appels au modèle.

## Installation

```bash
python -m venv venv
# Windows : venv\Scripts\activate    |    macOS / Linux : source venv/bin/activate
pip install -r requirements.txt
```

Copier `.env.example` sous le nom `.env`, puis y mettre son propre Account ID et son API Token Cloudflare (dash.cloudflare.com, token de type « Workers AI »).

## Modèle

`@cf/meta/llama-3.2-3b-instruct` via l'API Cloudflare Workers AI : environ 1 000 appels gratuits par jour, et un modèle assez petit pour se tromper sur une partie des exercices (environ 78 % de réussite sur GSM8K selon Meta).

## Structure

| Fichier | Rôle |
|---|---|
| `config.py` | Paramètres communs : graine, échantillons, modèle, température |
| `donnees.py` | Tirage des 1 000 exercices GSM8K et calcul du seuil court / long |
| `agent.py` | Les trois actions de l'agent : `resoudre`, `verifier`, `corriger` |
| `extraction.py` | Récupération du nombre (`Final answer:`) et du verdict (`CORRECT` / `WRONG`) |
| `resultats.py` | Calcul du % de bonnes réponses et des appels moyens à partir d'un CSV |
| `data/` | `exercices.csv` et `seuil.json`, partagés par le binôme |
| `resultats/` | CSV produits par les contrôleurs |

## Règles de travail

- Faire `git pull` avant de commencer à travailler.
- Ne pas modifier le même fichier en même temps.
- Ne pas modifier `config.py` ni les consignes de `agent.py` sans accord du binôme.
- Ne pas relancer `donnees.py` : utiliser `data/exercices.csv`.
- Ne jamais pousser le fichier `.env`.