# Chatbot — Chatbot conversationnel CLI

Un chatbot conversationnel en ligne de commande, conforme aux cadres
**RGPD**, **AI Act** et **Data Act**.

## Principe

- Interface **CLI** (terminal), pas d'interface web
- Moteur de recherche : [Tavily](https://tavily.com/)
- Mémoire de conversation en session, **aucune donnée persistante**
- Une **responsabilité par fichier** dans `src/chatbot/`

## Conformité réglementaire

| Cadre | Ce qu'on fait |
|---|---|
| **RGPD** | Consentement explicite, minimisation des données, purge en fin de session |
| **AI Act** | Bannière transparence IA, supervision humaine (`/undo`, `/correct`), journalisation |
| **Data Act** | Export JSON standardisé, format ouvert, licence CC0 |

Voir [`AGENTS.md`](AGENTS.md) — le contrat complet de règles du projet.

## Installation

```bash
# Python ≥ 3.10
cp .env.example .env
# Éditer .env et mettre TAVILY_API_KEY
pip install -e .
```

## Lancer

```bash
chatbot
# ou
python -m chatbot.main
```

## Utiliser le chatbot

```
$ chatbot
[Consentement RGPD] ...
[Transparence AI Act] Vous parlez à un assistant IA...

Vous: bonjour, peux-tu me résumer l'actualité de l'IA ?
Chatbot: D'après les sources : ...
Vous: /export
```

## Commandes

| Commande | Action |
|---|---|
| `/export` | Exécute l'export JSON de la session (Data Act) |
| `/undo` | Annule la dernière réponse (AI Act — supervision) |
| `/correct <texte>` | Corrige la dernière réponse |
| `/quit` | Termine et purge la session |

## Architecture

Voir [`AGENTS.md`](AGENTS.md) — section 2 pour l'arborescence complète.

## Tests

```bash
pytest tests/ -v
```

## Licence

MIT
