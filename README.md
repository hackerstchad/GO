# BOOK-DOWN

<img width="1024" height="576" alt="49ee0c5c-726e-4284-8497-f6b49514d2c6" src="https://github.com/user-attachments/assets/de677014-b1c9-41e5-b0a6-e22c72cd18ee" />


Auteur : Hackers_tchad


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
python book_down.py --url https://example.com<img width="1024" height="576" alt="49ee0c5c-726e-4284-8497-f6b49514d2c6" src="https://github.com/user-attachments/assets/002ee6a0-c298-4409-a588-800873f6aada" />
/books --ext pdf,epub --output ./downloads --depth 2
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
