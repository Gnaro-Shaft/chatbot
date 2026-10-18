# AGENTS.md — Règles du projet chatbot

> Ce fichier est le **contrat de règles** entre l'humain et l'agent LLM qui code ce projet.
> Toute la suite du code est dérivée de ce contrat.
> Le LLM doit lire et respecter ce fichier avant de coder quoi que ce soit.

---

## 1. Vue d'ensemble

Projet : **chatbot** — un chatbot conversationnel en ligne de commande (CLI),
en langage Python, qui utilise l'API Tavily comme moteur de recherche web
et un LLM pour générer des réponses conversationnelles.

Interface : terminal interactif.
Persistance : **aucune** (mémoire en session uniquement).
Dépendance LLM : Tavily API (`TAVILY_API_KEY`).

---

## 2. Architecture — une responsabilité par fichier

- Un fichier Python = **une responsabilité unitaire** (une fonction ou une classe principale)
- Chaque fichier dans `src/` a un miroir obligatoire dans `tests/`
- Les imports croisés entre modules sont **explicites et nommés** (`from .consent import get_consent`)
- Pas de fichier `models.py`, `utils.py` ou `helpers.py` fourre-tout : tout doit être atomique
- Si un fichier dépasse **120 lignes** → il est trop large, il faut le découper

### Structure attendue

```
chatbot/
├── AGENTS.md
├── pyproject.toml
├── ruff.toml
├── .env.example
├── .env                # gitignored, ne jamais committer
├── README.md
├── src/
│   └── chatbot/
│       ├── __init__.py
│       ├── main.py           # point d'entrée CLI
│       ├── config.py          # chargement des variables d'environnement
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── client.py      # appel à l'API Tavily
│       │   └── types.py       # types de données (dataclasses)
│       ├── core/
│       │   ├── __init__.py
│       │   ├── engine.py      # boucle de conversation
│       │   ├── prompt.py      # construction du prompt système
│       │   └── history.py     # mémoire de session (in-memory)
│       ├── ai_act/
│       │   ├── __init__.py
│       │   ├── transparency.py   # bannière "vous parlez à une IA"
│       │   ├── oversight.py      # intervention utilisateur (annuler / corriger)
│       │   └── logging.py        # journalisation des échanges
│       ├── rgpd/
│       │   ├── __init__.py
│       │   ├── consent.py        # consentement explicite
│       │   ├── minimization.py   # filtre les PII dans les logs
│       │   └── erasure.py        # purge à la fin de session
│       └── data_act/
│           ├── __init__.py
│           └── interop.py        # export JSON standardisé
└── tests/
    ├── conftest.py
    ├── test_consent.py
    ├── test_prompt.py
    ├── test_history.py
    ├── test_transparency.py
    └── test_interop.py
```

---

## 3. RGPD — conformité

| Article | Implémentation | Fichier |
|---|---|---|
| Art. 6 — Base légale | Consentement explicite au 1er lancement, texte clair, pas d'opt-out par défaut | `rgpd/consent.py` |
| Art. 5(1)(c) — Minimité | Ne stocker que le contexte conversationnel minimal ; ne loger aucune donnée personnelle | `rgpd/minimization.py` |
| Art. 17 — Droit à l'oubli | À la fin de la session, la mémoire est effacée ; pas de fichier persistant | `rgpd/erasure.py` |
| Art. 15 — Droit d'accès | Commande `/export` qui écrit un JSON lisible dans le dossier courant | `data_act/interop.py` |

Règle pratique : **aucune donnée ne peut quitter la session sans explicitation du consentement préalable**.

---

## 4. AI Act — conformité

| Article | Implémentation | Fichier |
|---|---|---|
| Art. 50 — Transparence | Bannière affichée au 1er message : « Vous parlez à un assistant IA. Les réponses peuvent contenir des inexactitudes. » | `ai_act/transparency.py` |
| Art. 14 — Supervision humaine | L'utilisateur peut : annuler une réponse (`/undo`), corriger la dernière réponse (`/correct <text>`) | `ai_act/oversight.py` |
| Art. 10 — Qualité des données | Chaque échange (input, output, timestamp, source URLs) est journalisé en mémoire | `ai_act/logging.py` |

Règle pratique : **l'utilisateur doit toujours pouvoir intervenir et contrôler la conversation**.

---

## 5. Data Act — conformité

| Article | Implémentation | Fichier |
|---|---|---|
| Art. 2 — Partage ouvert | Le format d'export est JSON standard (RFC 8259), schéma documenté, pas de clé chiffrée | `data_act/interop.py` |
| Art. 11 — Interopérabilité | L'export est réutilisable par tout lecteur JSON standard | `data_act/interop.py` |
| Licence des données exportées | CC0 (domaine public) sauf données personnelles | `data_act/interop.py` |

Schéma d'export minimal :
```json
{
  "session_id": "uuid",
  "timestamp": "ISO 8601",
  "exchanges": [
    {
      "id": "uuid",
      "timestamp": "ISO 8601",
      "input": "...",
      "output": "...",
      "sources": ["url1", "url2"],
      "model": "tavily-research"
    }
  ],
  "version": "1.0"
}
```

---

## 6. Bonnes pratiques Python

| Règle | Détail |
|---|---|
| Typage | Type annotations obligatoires sur toutes les signatures (`def f(x: int) -> str:`) |
| Docstrings | Chaque module et chaque fonction publique a un docstring (style NumPy) |
| Tests | Un test par fonction, couverture > 80 % minimum |
| Lint | `ruff check` sans erreur |
| Format | `black --line-length=88` |
| Noms | `snake_case` pour fonctions/variables, `PascalCase` pour classes |
| Fichiers | Nom du fichier = nom de la principale fonction/ classe |
| Imports | `from .module import NomExacte`, pas `import *` |
| Logs | Le module standard `logging`, pas `print()` |
| Exceptions | Ne pas catcher `except:`, être spécifique (`except ValueError:`) |
| Pas de globals | État uniquement via classes et paramètres de fonction |
| Configuration | Via `os.environ` et `config.py`, pas de dur-codié |

---

## 7. Outils de développement

```bash
# Installer
pip install -e .
pip install -r requirements-dev.txt    # ou: pip install pytest ruff black

# Lint
ruff check src/

# Format
black --line-length=88 src/

# Tests
pytest tests/ -v --cov=src/chatbot --cov-report=term-missing
```

---

## 8. Contraintes de code

- Pas de dépendance non nécessaire : Tavily + requests uniquement (pas de framework web)
- Pas de base de données, pas de fichier de log persistant
- La clé API est lue depuis l'environ, ne jamais logguer ni afficher
- Les tests ne doivent pas appeler l'API Tavily (mock obligé avec `unittest.mock`)
- Chaque fichier de test correspond à un fichier source (mirroir `tests/test_X.py ↔ src/.../X.py`)

---

*Contrat version 1.0 — 2026-10-18*
*Toute modification doit être validée par l'humain et faire l'objet d'une nouvelle version*
