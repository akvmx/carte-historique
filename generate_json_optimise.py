#!/usr/bin/env python3
"""
Générateur JSON simplifié pour carte historique
Version autonome sans dépendances complexes
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

# Configuration
EXPORT_FOLDER = "wiki-export"
OUTPUT_EVENTS_FILE = "data/evenements.json"
OUTPUT_PAYS_FILE = "data/pays.json"
OUTPUT_PERSONNES_FILE = "data/personnes.json"  # 🔸 NOUVEAU
OUTPUT_HTML_FOLDER = "fiches"


def normalize_date(date_str):
    """
    Normaliser les dates au format ISO (YYYY-MM-DD)
    Accepte: "1805", "1805-12", "1805-12-02"
    """
    if not date_str:
        return None

    # Nettoyer la chaîne (enlever guillemets et espaces)
    date_str = str(date_str).strip().strip('"').strip("'")

    # Si déjà au format complet YYYY-MM-DD
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str

    # Si format année-mois YYYY-MM
    if re.match(r'^\d{4}-\d{2}$', date_str):
        return f"{date_str}-01"

    # Si format année seule (1 à 4 chiffres)
    if re.match(r'^\d{1,4}$', date_str):
        # Pad l'année à 4 chiffres (990 → 0990)
        year = date_str.zfill(4)
        return f"{year}-01-01"

    print(f"⚠️ Format de date non reconnu: {date_str}")
    return date_str


def create_directories():
    """Créer les dossiers nécessaires"""
    for folder in ['data', OUTPUT_HTML_FOLDER]:
        Path(folder).mkdir(exist_ok=True)


def parse_frontmatter(content):
    """Extraire le front matter YAML simple"""
    if not content.startswith('---'):
        return None, content

    try:
        # Trouver la fin du front matter
        end_marker = content.find('---', 3)
        if end_marker == -1:
            return None, content

        frontmatter = content[3:end_marker].strip()
        markdown_content = content[end_marker + 3:].strip()

        # Parser YAML simple
        metadata = {}
        for line in frontmatter.split('\n'):
            line = line.strip()
            if ':' in line and not line.startswith('#'):
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()

                # Nettoyer les guillemets
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]

                # Parser les coordonnées
                if key == 'coords':

                    # Retirer les commentaires après #
                    if '#' in value:
                        value = value.split('#')[0].strip()

                    # Parser le tableau
                    if value.startswith('[') and value.endswith(']'):
                        coords_str = value[1:-1]
                        try:
                            coords = [float(x.strip()) for x in coords_str.split(',')]
                            if len(coords) == 2:
                                metadata[key] = coords
                            else:
                                print(f"⚠️ Coordonnées invalides (pas 2 valeurs): {value}")
                        except Exception as e:
                            print(f"⚠️ Coordonnées invalides: {value} - Erreur: {e}")
                    else:
                        print(f"⚠️ Format coordonnées invalide: {value}")

                # Parser les booléens
                elif key == 'perpetuel':
                    metadata[key] = value.lower() in ('true', 'yes', '1')

                # Normaliser les dates (événements + personnes)
                elif key in ('date', 'date_fin', 'naissance', 'mort'):
                    if '#' in value:
                        value = value.split('#')[0].strip()

                    normalized = normalize_date(value)
                    if normalized:
                        metadata[key] = normalized

                # Champs pouvant contenir plusieurs valeurs sur une ligne
                # (séparées par des virgules)
                elif key in ('pays', 'personnages', 'pays_principaux'):
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    if ',' in value:
                        items = [v.strip() for v in value.split(',') if v.strip()]
                        metadata[key] = items
                    else:
                        metadata[key] = value

                else:
                    # Retirer les commentaires pour les autres champs aussi
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    metadata[key] = value

        return metadata, markdown_content

    except Exception as e:
        print(f"❌ Erreur parsing front matter: {e}")
        return None, content


def determine_continent(coords):
    """Déterminer le continent à partir des coordonnées"""
    if not coords or len(coords) != 2:
        return "inconnu"

    lat, lng = coords

    # Zones approximatives
    if -35 <= lat <= 37 and -20 <= lng <= 55:
        return "afrique"
    elif 35 <= lat <= 70 and -10 <= lng <= 40:
        return "europe"
    elif 5 <= lat <= 55 and 40 <= lng <= 150:
        return "asie"
    elif -55 <= lat <= 70 and -130 <= lng <= -30:
        return "amerique"
    elif -50 <= lat <= -10 and 110 <= lng <= 180:
        return "oceanie"
    else:
        return "autre"


def generate_html(metadata, content, filename):
    """Générer le fichier HTML pour une fiche évènement (style épuré)"""

    # Conversion markdown basique
    html_content = content
    # Titres
    html_content = re.sub(r'^### (.*)', r'<h3>\1</h3>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^## (.*)', r'<h2>\1</h2>', html_content, flags=re.MULTILINE)
    html_content = re.sub(r'^# (.*)', r'<h1>\1</h1>', html_content, flags=re.MULTILINE)
    # Gras et italique
    html_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html_content)
    html_content = re.sub(r'\*(.*?)\*', r'<em>\1</em>', html_content)
    # Paragraphes
    html_content = re.sub(r'\n\n', '</p><p>', html_content)
    html_content = '<p>' + html_content + '</p>'
    html_content = re.sub(r'<p></p>', '', html_content)

    # Coordonnées formatées
    coords = metadata.get('coords', [])
    coords_str = f"{coords[0]}, {coords[1]}" if coords else "Non spécifiées"

    # Pays (string OU liste)
    pays_meta = metadata.get('pays', 'Pays inconnu')
    if isinstance(pays_meta, list):
        pays_str = ", ".join(pays_meta)
    else:
        pays_str = pays_meta

    titre = metadata.get('titre', 'Sans titre')
    date = metadata.get('date', 'Date inconnue')
    categorie = metadata.get('categorie', 'Général').title()

    # Template HTML avec style modernisé
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + titre + """</title>
    <style>
        :root {
            --accent: #FFC5D3;
            --accent-soft: rgba(255, 197, 211, 0.18);
            --bg-page: #f9fafb;
            --bg-card: #ffffff;
            --border-subtle: #e5e7eb;
            --text-main: #111827;
            --text-muted: #6b7280;
            --radius-lg: 18px;
            --shadow-card: 0 18px 40px rgba(15, 23, 42, 0.08);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: radial-gradient(circle at top left, #fee2e2 0, #f9fafb 40%, #eef2ff 100%);
            color: var(--text-main);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            padding: 32px 16px;
        }

        .page {
            width: 100%;
            max-width: 960px;
        }

        .back-link {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-size: 0.85rem;
            color: var(--text-muted);
            text-decoration: none;
            padding: 6px 10px;
            border-radius: 999px;
            border: 1px solid rgba(148, 163, 184, 0.4);
            margin-bottom: 16px;
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(10px);
        }

        .back-link:hover {
            border-color: var(--accent);
            color: var(--accent);
        }

        .event-card {
            background: var(--bg-card);
            border-radius: var(--radius-lg);
            padding: 24px 22px 26px;
            box-shadow: var(--shadow-card);
            border: 1px solid var(--border-subtle);
        }

        .event-header {
            display: flex;
            justify-content: space-between;
            gap: 12px;
            align-items: flex-start;
            margin-bottom: 20px;
        }

        .event-title-block {
            max-width: 75%;
        }

        .event-kicker {
            font-size: 0.78rem;
            letter-spacing: 0.16em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 6px;
        }

        .event-title {
            font-size: clamp(1.6rem, 3vw, 2.1rem);
            font-weight: 650;
            line-height: 1.2;
        }

        .event-subtitle {
            font-size: 0.9rem;
            color: var(--text-muted);
            margin-top: 6px;
        }

        .event-badge-stack {
            display: flex;
            flex-direction: column;
            align-items: flex-end;
            gap: 6px;
            text-align: right;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 10px;
            border-radius: 999px;
            font-size: 0.8rem;
            background: var(--accent-soft);
            color: var(--accent);
            border: 1px solid rgba(248, 250, 252, 0.9);
        }

        .badge-ghost {
            background: transparent;
            border-color: rgba(148, 163, 184, 0.5);
            color: var(--text-muted);
        }

        .meta-grid {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 10px 16px;
            padding: 14px 14px 16px;
            margin-bottom: 16px;
            border-radius: 14px;
            background: #f9fafb;
            border: 1px solid #e5e7eb;
        }

        .meta-item-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--text-muted);
            margin-bottom: 2px;
        }

        .meta-item-value {
            font-size: 0.9rem;
        }

        .content {
            margin-top: 4px;
            font-size: 0.97rem;
            color: #1f2933;
        }

        .content p {
            margin-bottom: 0.9rem;
        }

        .content h1,
        .content h2,
        .content h3 {
            margin-top: 1.8rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }

        .content h1 { font-size: 1.35rem; }
        .content h2 { font-size: 1.2rem; }
        .content h3 { font-size: 1.05rem; }

        .content ul,
        .content ol {
            margin: 0.8rem 0 0.8rem 1.4rem;
        }

        .content li {
            margin-bottom: 0.25rem;
        }

        .footnote {
            margin-top: 22px;
            font-size: 0.8rem;
            color: var(--text-muted);
            border-top: 1px dashed rgba(148, 163, 184, 0.8);
            padding-top: 10px;
        }

        @media (max-width: 720px) {
            body {
                padding: 18px 10px 22px;
            }
            .event-card {
                padding: 18px 16px 20px;
            }
            .event-header {
                flex-direction: column;
                gap: 8px;
            }
            .event-title-block {
                max-width: 100%;
            }
            .event-badge-stack {
                align-items: flex-start;
            }
            .meta-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="page">
        <a href="../index.html" class="back-link">← Retour à la carte</a>

        <article class="event-card">
            <header class="event-header">
                <div class="event-title-block">
                    <div class="event-kicker">évènement historique</div>
                    <h1 class="event-title">""" + titre + """</h1>
                </div>
                <div class="event-badge-stack">
                    <span class="badge">🏷️ """ + categorie + """</span>
                    <span class="badge badge-ghost">📅 """ + date + """</span>
                </div>
            </header>

            <section class="meta-grid">
                <div>
                    <div class="meta-item-label">pays</div>
                    <div class="meta-item-value">""" + pays_str + """</div>
                </div>
                <div>
                    <div class="meta-item-label">période</div>
                    <div class="meta-item-value">""" + date + """</div>
                </div>
                <div>
                    <div class="meta-item-label">catégorie</div>
                    <div class="meta-item-value">""" + categorie + """</div>
                </div>
            </section>

            <section class="content">
            """ + html_content + """
            </section>
        </article>
    </div>
</body>
</html>"""

    html_filename = filename.replace('.md', '.html')
    html_path = os.path.join(OUTPUT_HTML_FOLDER, html_filename)

    try:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True
    except Exception as e:
        print(f"❌ Erreur lors de l'écriture du HTML {html_path}: {e}")
        return False


def main():
    """Fonction principale"""
    print("Génération des fichiers JSON...")

    # Créer les dossiers
    create_directories()

    if not os.path.exists(EXPORT_FOLDER):
        print(f"Dossier {EXPORT_FOLDER} introuvable")
        print(f"Créez le dossier {EXPORT_FOLDER} et ajoutez vos fichiers .md")
        return

    evenements = []
    pays_dict = {}
    personnes = []  # 🔸 NOUVEAU

    stats = {'processed': 0, 'events': 0, 'countries': 0, 'persons': 0, 'errors': 0}

    # Traiter tous les fichiers .md (y compris dans les sous-dossiers)
    for root, dirs, files in os.walk(EXPORT_FOLDER):
        for filename in files:
            if not filename.endswith('.md'):
                continue

            filepath = os.path.join(root, filename)
            stats['processed'] += 1

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                metadata, markdown_content = parse_frontmatter(content)

                if not metadata:
                    print(f"⏭️ Ignoré: {os.path.relpath(filepath, EXPORT_FOLDER)} (pas de front matter)")
                    continue

                doc_type = metadata.get('type')

                # -----------------------------------
                # 1) TRAITEMENT DES ÉVÉNEMENTS
                # -----------------------------------
                if doc_type == 'évènement':
                    # Validation des champs requis
                    required = ['titre', 'date', 'pays', 'coords']
                    missing = [field for field in required if field not in metadata]
                    if missing:
                        print(f"Champs manquants dans {os.path.relpath(filepath, EXPORT_FOLDER)}: {missing}")
                        stats['errors'] += 1
                        continue

                    # Créer l'événement
                    html_filename = filename.replace('.md', '.html')

                    # Nettoyer la catégorie (enlever guillemets superflus)
                    categorie = metadata.get('categorie', 'general')
                    categorie = categorie.strip('"').strip("'")

                    evenement = {
                        "titre": metadata['titre'],
                        "date": metadata['date'],
                        "date_fin": metadata.get('date_fin', False),
                        "perpetuel": metadata.get('perpetuel', False),
                        "pays": metadata['pays'],
                        "coords": metadata['coords'],
                        "description": metadata.get('description', ''),
                        "categorie": categorie,
                        "personnages": metadata.get('personnages'),
                        "lien": f"fiches/{html_filename}"
                    }
                    evenements.append(evenement)
                    stats['events'] += 1

                    # Gérer les pays (un événement peut concerner plusieurs pays)
                    pays_field = metadata['pays']  # str ou liste
                    continent = determine_continent(metadata['coords'])

                    if isinstance(pays_field, list):
                        pays_list = pays_field
                    else:
                        pays_list = [pays_field]

                    for pays_name in pays_list:
                        if not pays_name:
                            continue
                        pays_key = pays_name.lower().strip()
                        if pays_key not in pays_dict:
                            pays_dict[pays_key] = {
                                "pays": pays_name,
                                "continent": continent,
                                "coordonnees": metadata['coords']
                            }
                            stats['countries'] += 1

                    # Générer HTML
                    if generate_html(metadata, markdown_content, filename):
                        print(f"✅ Traité (événement): {os.path.relpath(filepath, EXPORT_FOLDER)}")
                    else:
                        print(f"⚠️ HTML non généré pour: {os.path.relpath(filepath, EXPORT_FOLDER)}")

                # -----------------------------------
                # 2) TRAITEMENT DES PERSONNES
                # -----------------------------------
                elif doc_type in ('personne', 'person', 'personnage'):
                    # nom par défaut = 'nom' ou 'titre' ou nom de fichier
                    nom = metadata.get('nom') or metadata.get('titre') or filename.replace('.md', '')

                    # pays_principaux → tableau
                    pays_principaux = metadata.get('pays_principaux') or []
                    if isinstance(pays_principaux, str):
                        pays_principaux = [p.strip() for p in pays_principaux.split(',') if p.strip()]

                    # bio courte : YAML > sinon 1er paragraphe du contenu
                    bio_courte = metadata.get('bio_courte')
                    if not bio_courte:
                        blocs = [p.strip() for p in markdown_content.split('\n\n') if p.strip()]
                        bio_courte = blocs[0] if blocs else ""
                    
                    # 🟣 bio longue : YAML "bio_longue" > sinon tout le contenu Obsidian
                    bio_longue = metadata.get('bio_longue') or markdown_content.strip()

                    personne = {
                        "nom": nom,
                        "titre": metadata.get('titre', nom),
                        "naissance": metadata.get('naissance'),
                        "mort": metadata.get('mort'),
                        "lieu_naissance": metadata.get('lieu_naissance'),
                        "lieu_mort": metadata.get('lieu_mort'),
                        "fonction": metadata.get('fonction'),
                        "pays_principaux": pays_principaux,
                        "image": metadata.get('image'),
                        "bio_courte": bio_courte,
                        "bio_longue": bio_longue,
                        "sources": metadata.get('sources')
                    }

                    personnes.append(personne)
                    stats['persons'] += 1
                    print(f"✅ Traité (personne): {os.path.relpath(filepath, EXPORT_FOLDER)}")

                else:
                    print(f"⏭️ Ignoré: {os.path.relpath(filepath, EXPORT_FOLDER)} (type inconnu ou non géré: {doc_type})")
                    continue

            except Exception as e:
                print(f"Erreur avec {os.path.relpath(filepath, EXPORT_FOLDER)}: {e}")
                stats['errors'] += 1

    # Sauvegarder les JSON
    try:
        # Événements
        with open(OUTPUT_EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(evenements, f, ensure_ascii=False, indent=2)

        # Pays
        pays_list = list(pays_dict.values())
        with open(OUTPUT_PAYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pays_list, f, ensure_ascii=False, indent=2)

        # Personnes 🔸 NOUVEAU
        if personnes:
            with open(OUTPUT_PERSONNES_FILE, 'w', encoding='utf-8') as f:
                json.dump(personnes, f, ensure_ascii=False, indent=2)

        print("\n" + "="*50)
        print("GÉNÉRATION TERMINÉE")
        print(f"Fichiers traités: {stats['processed']}")
        print(f"Événements créés: {stats['events']}")
        print(f"Pays créés: {stats['countries']}")
        print(f"Personnes créées: {stats['persons']}")
        print(f"Fichiers HTML (événements): {stats['events']}")
        print(f"Erreurs: {stats['errors']}")
        print(f"JSON sauvés: {OUTPUT_EVENTS_FILE}, {OUTPUT_PAYS_FILE}", end='')
        if personnes:
            print(f", {OUTPUT_PERSONNES_FILE}")
        else:
            print("")
        print("="*50)

        if stats['events'] > 0 or stats['persons'] > 0:
            print("🎉 Actualisez votre carte pour voir les changements !")

    except Exception as e:
        print(f"Erreur sauvegarde JSON: {e}")


if __name__ == "__main__":
    main()
