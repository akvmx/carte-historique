#!/usr/bin/env python3
"""
Surveillance simple des fichiers Obsidian
Version corrigée sans erreurs de syntaxe
"""

import time
import subprocess
import os
import sys
from pathlib import Path
from datetime import datetime

# Configuration globale
WATCH_FOLDER = "wiki-export"
DEBOUNCE_DELAY = 2  # secondes

def install_watchdog():
    """Installer watchdog si nécessaire"""
    try:
        import watchdog
        return True
    except ImportError:
        print("📦 Installation de watchdog...")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'watchdog'])
            print("✅ Watchdog installé")
            return True
        except:
            print("❌ Impossible d'installer watchdog")
            return False

class SimpleWatcher:
    """Gestionnaire simple de surveillance"""
    
    def __init__(self, watch_folder):
        self.watch_folder = watch_folder
        self.last_trigger = 0
        self.pending_files = set()
        self.stats = {
            'events': 0,
            'generations': 0,
            'start_time': datetime.now()
        }
        
    def should_process_file(self, file_path):
        """Vérifier si le fichier doit être traité"""
        path = Path(file_path)
        
        # Ignorer les fichiers cachés
        if path.name.startswith('.') or path.name.startswith('~'):
            return False
            
        # Traiter uniquement les .md
        if path.suffix.lower() != '.md':
            return False
            
        return True
    
    def trigger_generation(self):
        """Déclencher la génération"""
        current_time = time.time()
        
        # Debouncing
        if current_time - self.last_trigger < DEBOUNCE_DELAY:
            print("⏱️ Attente (debouncing)...")
            return
            
        self.last_trigger = current_time
        
        if not self.pending_files:
            return
        
        files_list = list(self.pending_files)
        self.pending_files.clear()
        
        print(f"🔄 Génération pour {len(files_list)} fichier(s)")
        for file_path in files_list[:3]:  # Afficher max 3
            print(f"   📄 {Path(file_path).name}")
        
        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, "generate_json_optimise.py"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                self.stats['generations'] += 1
                print(f"✅ Génération réussie en {duration:.2f}s")
                
                # Afficher les dernières lignes de sortie
                if result.stdout:
                    lines = result.stdout.strip().split('\n')
                    for line in lines[-2:]:
                        if line.strip() and ('événements' in line or 'pays' in line):
                            print(f"   {line.strip()}")
            else:
                print(f"❌ Erreur génération (code {result.returncode})")
                if result.stderr:
                    print(f"   {result.stderr.strip()}")
                    
        except subprocess.TimeoutExpired:
            print("⏰ Timeout génération (>60s)")
        except Exception as e:
            print(f"💥 Erreur: {e}")
    
    def on_file_change(self, file_path, event_type):
        """Gérer un changement de fichier"""
        if not self.should_process_file(file_path):
            return
            
        self.stats['events'] += 1
        self.pending_files.add(file_path)
        
        filename = Path(file_path).name
        print(f"📝 {event_type}: {filename}")
        
        # Programmer la génération
        self.schedule_generation()
    
    def schedule_generation(self):
        """Programmer une génération avec délai"""
        import threading
        
        def delayed_trigger():
            time.sleep(DEBOUNCE_DELAY)
            self.trigger_generation()
        
        threading.Thread(target=delayed_trigger, daemon=True).start()
    
    def print_stats(self):
        """Afficher les statistiques"""
        uptime = datetime.now() - self.stats['start_time']
        print("\n📊 STATISTIQUES")
        print(f"   Temps d'activité: {uptime}")
        print(f"   Événements détectés: {self.stats['events']}")
        print(f"   Générations: {self.stats['generations']}")

def watch_with_watchdog(watch_folder):
    """Surveillance avec la bibliothèque watchdog"""
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    
    watcher = SimpleWatcher(watch_folder)
    
    class ChangeHandler(FileSystemEventHandler):
        def on_modified(self, event):
            if not event.is_directory:
                watcher.on_file_change(event.src_path, "Modifié")
        
        def on_created(self, event):
            if not event.is_directory:
                watcher.on_file_change(event.src_path, "Créé")
        
        def on_deleted(self, event):
            if not event.is_directory:
                watcher.on_file_change(event.src_path, "Supprimé")
    
    observer = Observer()
    observer.schedule(ChangeHandler(), watch_folder, recursive=True)
    
    try:
        observer.start()
        print(f"👀 Surveillance active: {Path(watch_folder).absolute()}")
        print("🛑 Appuyez sur Ctrl+C pour arrêter")
        
        # Génération initiale
        print("🔄 Génération initiale...")
        watcher.trigger_generation()
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé...")
        observer.stop()
        watcher.print_stats()
    
    observer.join()
    print("✅ Surveillance arrêtée")

def watch_simple_polling(watch_folder):
    """Surveillance simple par polling (sans watchdog)"""
    print("📝 Mode polling simple (sans watchdog)")
    
    watcher = SimpleWatcher(watch_folder)
    last_check = {}
    
    def scan_folder():
        """Scanner le dossier pour détecter les changements"""
        current_files = {}
        
        for file_path in Path(watch_folder).rglob("*.md"):
            try:
                stat = file_path.stat()
                current_files[str(file_path)] = stat.st_mtime
            except:
                continue
        
        # Détecter les changements
        for file_path, mtime in current_files.items():
            if file_path not in last_check:
                watcher.on_file_change(file_path, "Nouveau")
            elif last_check[file_path] != mtime:
                watcher.on_file_change(file_path, "Modifié")
        
        # Détecter les suppressions
        for file_path in list(last_check.keys()):
            if file_path not in current_files:
                watcher.on_file_change(file_path, "Supprimé")
        
        last_check.clear()
        last_check.update(current_files)
    
    try:
        print(f"👀 Surveillance polling: {Path(watch_folder).absolute()}")
        print("🛑 Appuyez sur Ctrl+C pour arrêter")
        
        # Génération initiale
        print("🔄 Génération initiale...")
        watcher.trigger_generation()
        
        while True:
            scan_folder()
            time.sleep(3)  # Vérifier toutes les 3 secondes
            
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé...")
        watcher.print_stats()
    
    print("✅ Surveillance arrêtée")

def main():
    """Fonction principale"""
    print("🚀 Démarrage de la surveillance Obsidian")
    print("="*50)
    
    # Vérifier le dossier
    if not os.path.exists(WATCH_FOLDER):
        print(f"❌ Dossier {WATCH_FOLDER} introuvable")
        print(f"💡 Créez le dossier {WATCH_FOLDER} et ajoutez vos fichiers .md")
        return 1
    
    # Vérifier le générateur
    if not os.path.exists("generate_json_optimise.py"):
        print("❌ Fichier generate_json_optimise.py introuvable")
        print("💡 Assurez-vous d'avoir le générateur dans le même dossier")
        return 1
    
    # Choisir la méthode de surveillance
    if install_watchdog():
        print("✅ Utilisation de watchdog (recommandé)")
        try:
            watch_with_watchdog(WATCH_FOLDER)
        except Exception as e:
            print(f"❌ Erreur watchdog: {e}")
            print("🔄 Passage en mode polling...")
            watch_simple_polling(WATCH_FOLDER)
    else:
        print("⚠️ Watchdog non disponible, utilisation du polling")
        watch_simple_polling(WATCH_FOLDER)
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"💥 Erreur fatale: {e}")
        sys.exit(1)