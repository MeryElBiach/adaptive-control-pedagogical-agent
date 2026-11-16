# Contrôle adaptatif d'un agent pédagogique

Projet de fin de semestre (S5, ENSIAS) — Binôme : Hind et Meryem — Encadrant : M. Rachad.

Un agent résout des exercices de mathématiques (GSM8K) à l'aide d'un LLM, puis décide s'il doit vérifier sa réponse, la corriger ou s'arrêter. Vérifier et corriger peuvent améliorer la réponse, mais chaque étape coûte un appel supplémentaire au modèle. Le projet compare trois façons de prendre cette décision — **contrôle fixe**, **contrôle heuristique** et **contrôle appris** (Q-learning) — selon deux mesures : le **taux de bonnes réponses** et le **nombre moyen d'appels au modèle** par exercice.

**État d'avancement :** contrôle fixe ✅ · contrôle heuristique ✅ · contrôle appris ⏳

## Installation

```bash
python -m venv venv
# Windows : venv\Scripts\activate    |    macOS / Linux : source venv/bin/activate
pip install -r requirements.txt
```

Copier `.env.example` sous le nom `.env`, puis y mettre son propre Account ID et son API Token Cloudflare (dash.cloudflare.com, token de type « Workers AI »). Le contrôle heuristique n'en a pas besoin : il n'appelle pas le modèle.

## Données et modèle

- **Données :** GSM8K (subset `main`, split `test`). 1 000 exercices tirés avec la graine 42 ; les 100 premiers servent aux contrôles fixe et heuristique. Chaque énoncé est classé **court** ou **long** selon la médiane de son nombre de mots (**43 mots**).
- **Modèle :** `@cf/meta/llama-3.2-3b-instruct` via l'API Cloudflare Workers AI (température 0). Ce petit modèle a été choisi volontairement : il se trompe sur une partie des exercices (environ 20 %), ce qui laisse à la vérification des erreurs à corriger.
- **Évaluation :** la réponse finale est comparée au corrigé de GSM8K. L'agent ne voit jamais le corrigé.

## Les trois actions de l'agent

Chaque action est un appel au modèle avec une consigne différente (`agent.py`) :

| Action | Ce que reçoit le modèle | Ce qu'il renvoie |
|---|---|---|
| Résoudre | L'énoncé | Une solution terminée par `Final answer: <nombre>` |
| Vérifier | L'énoncé et la solution | `VERDICT: CORRECT` ou `VERDICT: WRONG`, avec une raison |
| Corriger | L'énoncé, la solution et la remarque du vérificateur | Une nouvelle solution terminée par `Final answer: <nombre>` |

Le vérificateur est le même modèle : il ne connaît pas le corrigé et peut donc se tromper (fausse alerte sur une bonne réponse, ou erreur non détectée).

## Contrôle fixe (`controleur_fixe.py`)

**Règle :** la même séquence pour tous les exercices.

1. Résoudre (appel 1)
2. Vérifier (appel 2)
3. Corriger seulement si le verdict est WRONG (appel 3), puis s'arrêter

Chaque exercice coûte donc 2 ou 3 appels. Pour chaque exercice, `resultats/fixe.csv` enregistre la **réponse initiale** (avant vérification) et la **réponse finale** (après vérification et correction éventuelle), ce qui permet aussi de mesurer le résultat « sans vérification » sur la même exécution.

```bash
python controleur_fixe.py        # 100 exercices (environ 220 appels)
```

## Contrôle heuristique (`controleur_heuristique.py`)

**Règle, écrite à la main :** vérifier **seulement si l'énoncé est long** (plus de 43 mots).

- Énoncé court : résoudre, puis s'arrêter (1 appel). Le modèle y réussit déjà 90 % des exercices : une vérification coûte un appel et risque de casser une bonne réponse.
- Énoncé long : même séquence que le contrôle fixe (2 ou 3 appels).

Ses étapes étant incluses dans celles du contrôle fixe, il est calculé **à partir de `resultats/fixe.csv`, sans nouvel appel au modèle** : réponse initiale pour un énoncé court, réponse finale du fixe pour un énoncé long. Les deux contrôles sont ainsi comparés sur exactement les mêmes réponses du modèle ; seule la règle de décision change.

```bash
python controleur_heuristique.py
```

## Résultats (100 exercices)

| Contrôle | % de bonnes réponses | Appels moyens |
|---|---|---|
| Sans vérification (référence) | 79 % | 1,00 |
| Fixe | 75 % | 2,20 |
| Heuristique | **78 %** | **1,58** |

Détail par longueur d'énoncé :

| Groupe | Sans vérification | Fixe | Heuristique |
|---|---|---|---|
| Courts (51) | 90,2 % · 1 appel | 84,3 % · 2,22 appels | 90,2 % · 1 appel |
| Longs (49) | 67,3 % · 1 appel | 65,3 % · 2,18 appels | 65,3 % · 2,18 appels |

**Ce que montre la vérification systématique (contrôle fixe) :**

| Cas | Nombre |
|---|---|
| Réponses justes cassées par la correction | 6 |
| Réponses fausses réparées par la correction | 2 |
| Fausses alertes (réponse juste, verdict WRONG) | 11 |
| Erreurs non détectées (réponse fausse, verdict CORRECT) | 12 |

**Conclusions :**

1. Avec ce modèle, la vérification systématique fait baisser l'exactitude (79 % → 75 %) tout en multipliant le coût par 2,2 : elle casse plus de bonnes réponses qu'elle n'en répare.
2. La perte se concentre sur les énoncés courts (−5,9 points), où le modèle avait déjà presque toujours raison.
3. Le contrôle heuristique, qui ne vérifie que les énoncés longs, fait mieux que le contrôle fixe sur les deux mesures (78 % contre 75 %, 1,58 appel contre 2,20).
4. Il reste légèrement en dessous de la référence sans vérification (79 %), car sur les énoncés longs la vérification fait encore perdre un peu (67,3 % → 65,3 %). Le contrôle appris devra montrer s'il trouve une meilleure règle.

Remarque : même à température 0, l'API ne renvoie pas exactement les mêmes réponses d'une exécution à l'autre (écart observé d'environ 3 points). Les résultats de référence sont donc ceux enregistrés dans `resultats/`.

## Structure du dépôt

| Fichier | Rôle |
|---|---|
| `config.py` | Paramètres communs : graine, échantillons, modèle, température |
| `donnees.py` | Tirage des 1 000 exercices GSM8K et calcul du seuil court / long (lancé une seule fois) |
| `agent.py` | Les trois actions de l'agent : `resoudre`, `verifier`, `corriger` |
| `extraction.py` | Récupération du nombre (`Final answer:`) et du verdict (`CORRECT` / `WRONG`), comparaison au corrigé |
| `resultats.py` | Calcul du % de bonnes réponses et des appels moyens à partir d'un CSV |
| `controleur_fixe.py` | Contrôle fixe : résoudre → vérifier → corriger si WRONG |
| `controleur_heuristique.py` | Contrôle heuristique : vérifier seulement les énoncés longs |
| `data/` | `exercices.csv` et `seuil.json`, partagés par le binôme |
| `resultats/` | `fixe.csv` et `heuristique.csv` : une ligne par exercice |

Pour recalculer les mesures d'un fichier de résultats : `python resultats.py resultats/heuristique.csv`

## Règles de travail

- Faire `git pull` avant de commencer à travailler.
- Ne pas modifier le même fichier en même temps.
- Ne pas modifier `config.py` ni les consignes de `agent.py` sans accord du binôme.
- Ne pas relancer `donnees.py` : utiliser `data/exercices.csv`.
- Versionner les fichiers de `resultats/` : ils sont la référence des chiffres du rapport.
- Ne jamais pousser le fichier `.env`.