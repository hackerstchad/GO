# BOOK-DOWN

Script Python avancé créé par **Hackers-Tchad** pour télécharger des livres depuis un site web via son URL.

## Avertissement légal

Ce script est destiné à un usage **légal et éthique uniquement** :
- Télécharger des livres que vous possédez légalement
- Télécharger des livres sous licence libre (Creative Commons, domaine public, etc.)
- Télécharger des livres avec autorisation explicite de l'auteur ou de l'éditeur

**Ne l'utilisez jamais** pour pirater des œuvres protégées par le droit d'auteur.

## Fonctionnalités

- Découverte automatique des liens de livres (PDF, EPUB, MOBI, etc.)
- Téléchargement récursif ou limité en profondeur
- Filtrage par extension de fichier
- Filtrage par taille minimale/maximale
- Renommage automatique des fichiers
- Sauvegarde des métadonnées (URL source, date de téléchargement)
- Journal de téléchargement
- Interface terminal stylisée black/green
- Barre de progression
- Option de reprise en cas d'interruption

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

### Mode interactif

```bash
python book_down.py
```

### Mode ligne de commande

```bash
python book_down.py --url https://example.com/books --ext pdf,epub --output ./downloads --depth 2
```

## Options

| Option | Description |
|--------|-------------|
| `--url` | URL du site à scanner |
| `--output` | Dossier de destination |
| `--ext` | Extensions de fichiers à télécharger (pdf,epub,mobi) |
| `--depth` | Profondeur de crawl (0 = page uniquement) |
| `--min-size` | Taille minimale en Mo |
| `--max-size` | Taille maximale en Mo |
| `--no-recursion` | Désactiver le crawl récursif |
| `--delay` | Délai entre les requêtes en secondes |

## Exemple

```bash
python book_down.py --url https://example.com/library --ext pdf,epub --output ./mes_livres --depth 1 --delay 1
```

## Structure

- `book_down.py` — Script principal
- `requirements.txt` — Dépendances
- `README.md` — Documentation
