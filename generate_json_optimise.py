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
                
                # Normaliser les dates
                elif key in ('date', 'date_fin'):
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    
                    normalized = normalize_date(value)
                    if normalized:
                        metadata[key] = normalized

                # Champs pouvant contenir plusieurs valeurs sur une ligne (séparées par des virgules)
                elif key in ('pays', 'personnages'):
                    if '#' in value:
                        value = value.split('#')[0].strip()
                    # ex : "France, Russie, Pologne"
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
    """Générer le fichier HTML de manière plus sûre"""
    
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
    
    coords = metadata.get('coords', [])
    coords_str = str(coords[0]) + ", " + str(coords[1]) if coords else "Non spécifiées"
    
    # Template HTML simplifié sans f-strings problématiques
    pays_meta = metadata.get('pays', 'Pays inconnu')
    if isinstance(pays_meta, list):
        pays_str = ", ".join(pays_meta)
    else:
        pays_str = pays_meta
    html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>""" + metadata.get('titre', 'Sans titre') + """</title>
    <style>
        body {
            font-family: system-ui, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            background: #f8fafc;
            line-height: 1.6;
        }
        .container {
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        .btn-retour {
            display: inline-block;
            padding: 0.75rem 1.5rem;
            background: #3b82f6;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            margin-bottom: 2rem;
        }
        h1 { color: #3b82f6; }
        h2, h3 { color: #1e40af; margin-top: 2rem; }
        .meta { background: #f8fafc; padding: 1rem; border-radius: 8px; margin: 1rem 0; }
    </style>
</head>
<body>
    <div class="container">
        <a href="../index.html" class="btn-retour">← Retour à la carte</a>
        
        <h1>""" + metadata.get('titre', 'Sans titre') + """</h1>
        
        <div class="meta">
            <p><strong>📅 Date :</strong> """ + metadata.get('date', 'Date inconnue') + """</p>
            <p><strong>🌍 Pays :</strong> """ + pays_str + """</p>
            <p><strong>📍 Coordonnées :</strong> """ + coords_str + """</p>
            <p><strong>🏷️ Catégorie :</strong> """ + metadata.get('categorie', 'General').title() + """</p>
        </div>
        
        <div class="content">
            """ + html_content + """
        </div>
        
        <footer style="margin-top: 3rem; padding-top: 2rem; border-top: 1px solid #e2e8f0; color: #64748b; font-size: 0.9rem;">
        </footer>
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
        print("ERREUR génération HTML:", str(e))
        return False

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
    
    coords = metadata.get('coords', [])
    coords_str = f"{coords[0]:.4f}, {coords[1]:.4f}" if coords else "Non spécifiées"
    
    html = html_template.format(
        titre=metadata.get('titre', 'Sans titre'),
        date=metadata.get('date', 'Date inconnue'),
        pays=metadata.get('pays', 'Pays inconnu'),
        coords_str=coords_str,
        categorie=metadata.get('categorie', 'General').title(),
        content_html=html_content,
        timestamp=datetime.now().strftime("%d/%m/%Y à %H:%M")
    )
    
    html_filename = filename.replace('.md', '.html')
    html_path = os.path.join(OUTPUT_HTML_FOLDER, html_filename)
    
    try:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        return True
    except Exception as e:
        print(f"Erreur génération HTML: {e}")
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
    stats = {'processed': 0, 'events': 0, 'countries': 0, 'errors': 0}
    
    # Traiter tous les fichiers .md
    for filename in os.listdir(EXPORT_FOLDER):
        if not filename.endswith('.md'):
            continue
            
        filepath = os.path.join(EXPORT_FOLDER, filename)
        stats['processed'] += 1
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            metadata, markdown_content = parse_frontmatter(content)
            
            if not metadata or metadata.get('type') != 'évènement':
                print(f"⏭️ Ignoré: {filename} (pas un événement)")
                continue
            
            # Validation des champs requis
            required = ['titre', 'date', 'pays', 'coords']
            missing = [field for field in required if field not in metadata]
            if missing:
                print(f"Champs manquants dans {filename}: {missing}")
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
                "date_fin": metadata.get('date_fin', False),      # ← Optionnel
                "perpetuel": metadata.get('perpetuel', False),  # ← Optionnel
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
                print(f"✅ Traité: {filename}")
            else:
                print(f"⚠️ HTML non généré pour: {filename}")
                
        except Exception as e:
            print(f"Erreur avec {filename}: {e}")
            stats['errors'] += 1
    
    # Sauvegarder les JSON
    try:
        with open(OUTPUT_EVENTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(evenements, f, ensure_ascii=False, indent=2)
        
        pays_list = list(pays_dict.values())
        with open(OUTPUT_PAYS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pays_list, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*50)
        print("GÉNÉRATION TERMINÉE")
        print(f"Fichiers traités: {stats['processed']}")
        print(f"Événements créés: {stats['events']}")
        print(f"Pays créés: {stats['countries']}")
        print(f"Fichiers HTML: {stats['events']}")
        print(f"Erreurs: {stats['errors']}")
        print(f"JSON sauvés: {OUTPUT_EVENTS_FILE}, {OUTPUT_PAYS_FILE}")
        print("="*50)
        
        if stats['events'] > 0:
            print("🎉 Actualisez votre carte pour voir les changements !")
        
    except Exception as e:
        print(f"Erreur sauvegarde JSON: {e}")

if __name__ == "__main__":
    main()