// ========================================
// VARIABLES GLOBALES
// ========================================

let maCarte = null;
let marqueurs = null;
let anneeSelectionnee = 2024;
let continentSelectionne = "tous";
let themeSombre = false;

// Données chargées depuis les fichiers JSON
let PAYS_DATA = [];
let EVENEMENTS_DATA = [];

// ========================================
// CLASSE GESTIONNAIRE DE CARTE (VERSION CORRIGÉE)
// ========================================

class GestionnaireCarte {
    constructor() {
        console.log("🗺️ Initialisation du gestionnaire de carte");
        this.initialiserCarte();
        this.initialiserControles();
        this.chargerDonneesJSON();
    }

    // Créer la carte Leaflet
    initialiserCarte() {
        console.log("📍 Création de la carte");
        
        // Vérifier que l'élément carte existe
        const elementCarte = document.getElementById('carte');
        if (!elementCarte) {
            console.error("❌ Élément #carte introuvable dans le HTML");
            return;
        }
        
        // Créer la carte
        maCarte = L.map('carte').setView([20, 0], 2);
        
        // Ajouter les tuiles
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
            maxZoom: 18
        }).addTo(maCarte);
        
        // Créer le groupe de marqueurs
        marqueurs = L.layerGroup().addTo(maCarte);
        
        console.log("✅ Carte créée avec succès");
    }

    // Charger les données JSON
    async chargerDonneesJSON() {
        console.log("📦 Chargement des données JSON...");
        
        try {
            // Charger les événements
            const reponseEvenements = await fetch('data/evenements.json');
            if (reponseEvenements.ok) {
                EVENEMENTS_DATA = await reponseEvenements.json();
                console.log(`✅ ${EVENEMENTS_DATA.length} événements chargés`);
                console.log("📋 Événements:", EVENEMENTS_DATA);
            } else {
                console.log("⚠️ Pas de fichier evenements.json, utilisation des données de test");
                EVENEMENTS_DATA = this.donneesTestEvenements();
            }
            
            // Charger les pays
            const reponsePays = await fetch('data/pays.json');
            if (reponsePays.ok) {
                PAYS_DATA = await reponsePays.json();
                console.log(`✅ ${PAYS_DATA.length} pays chargés`);
                console.log("📋 Pays:", PAYS_DATA);
            } else {
                console.log("⚠️ Pas de fichier pays.json, utilisation des données de test");
                PAYS_DATA = this.donneesTestPays();
            }
            
            // Afficher les marqueurs
            this.mettreAJourMarqueurs();
            this.mettreAJourStatistiques();
            
        } catch (erreur) {
            console.error("❌ Erreur lors du chargement:", erreur);
            console.log("📄 Utilisation des données de test");
            PAYS_DATA = this.donneesTestPays();
            EVENEMENTS_DATA = this.donneesTestEvenements();
            this.mettreAJourMarqueurs();
            this.mettreAJourStatistiques();
        }
    }

    // Données de test pour les pays
    donneesTestPays() {
        return [
            { pays: "France", continent: "europe", coordonnees: [46.603354, 1.888334] },
            { pays: "Allemagne", continent: "europe", coordonnees: [51.165691, 10.451526] },
            { pays: "États-Unis", continent: "amerique", coordonnees: [37.09024, -95.712891] },
            { pays: "Chine", continent: "asie", coordonnees: [35.86166, 104.195397] },
            { pays: "Égypte", continent: "afrique", coordonnees: [26.820553, 30.802498] }
        ];
    }

    // Données de test pour les événements
    donneesTestEvenements() {
        return [
            {
                pays: "France",
                date: "1789-07-14",
                titre: "Prise de la Bastille",
                description: "Début de la Révolution française",
                categorie: "politique",
                lien: "fiches/france/prise-bastille.html"
            },
            {
                pays: "France",
                date: "1804-12-02",
                titre: "Sacre de Napoléon",
                description: "Napoléon devient empereur",
                categorie: "politique",
                lien: "#"
            },
            {
                pays: "États-Unis",
                date: "1776-07-04",
                titre: "Déclaration d'indépendance",
                description: "Naissance des États-Unis",
                categorie: "politique",
                lien: "#"
            }
        ];
    }

    // Configurer les contrôles
    initialiserControles() {
        console.log("🎮 Configuration des contrôles");
        
        // Bouton thème
        const boutonTheme = document.getElementById('theme-btn');
        if (boutonTheme) {
            boutonTheme.addEventListener('click', () => {
                this.changerTheme();
            });
        }

        // Slider année
        const sliderAnnee = document.getElementById('slider-annee');
        const affichageAnnee = document.getElementById('annee-affichee');
        
        if (sliderAnnee && affichageAnnee) {
            sliderAnnee.addEventListener('input', (event) => {
                anneeSelectionnee = parseInt(event.target.value);
                affichageAnnee.textContent = anneeSelectionnee;
                this.mettreAJourMarqueurs();
                this.mettreAJourStatistiques();
            });
        }

        // Boutons continents
        const boutonsContinent = document.querySelectorAll('.btn-continent');
        boutonsContinent.forEach(bouton => {
            bouton.addEventListener('click', () => {
                // Retirer actif de tous
                boutonsContinent.forEach(b => b.classList.remove('actif'));
                // Ajouter actif au cliqué
                bouton.classList.add('actif');
                // Changer le continent
                continentSelectionne = bouton.dataset.continent;
                this.mettreAJourMarqueurs();
                this.mettreAJourStatistiques();
            });
        });
        
        console.log("✅ Contrôles configurés");
    }

    // ⭐ FONCTION CORRIGÉE - Mettre à jour les marqueurs
    mettreAJourMarqueurs() {
        if (!maCarte || !marqueurs) {
            console.log("⏳ Carte pas encore prête");
            return;
        }
        
        console.log("\n" + "=".repeat(50));
        console.log("🔄 MISE À JOUR DES MARQUEURS");
        console.log("=".repeat(50));
        console.log(`📅 Année sélectionnée : ${anneeSelectionnee}`);
        console.log(`🌍 Continent : ${continentSelectionne}`);
        
        marqueurs.clearLayers();
        
        // Filtrer les pays
        let paysFiltres = PAYS_DATA;
        if (continentSelectionne !== "tous") {
            paysFiltres = PAYS_DATA.filter(pays => pays.continent === continentSelectionne);
            console.log(`📊 ${paysFiltres.length} pays après filtre continent`);
        }
        
        let totalMarqueurs = 0;
        
        // Pour chaque pays
        paysFiltres.forEach(pays => {
            // ⭐ CORRECTION : Filtrage avec gestion de date_fin et perpetuel
            const evenementsPays = EVENEMENTS_DATA.filter(event => {
                // Vérifier que c'est le bon pays
                if (event.pays.toLowerCase() !== pays.pays.toLowerCase()) {
                    return false;
                }
                
                // Sécurité : vérifier que date existe
                if (!event.date) {
                    console.warn(`⚠️ Événement sans date: ${event.titre}`);
                    return false;
                }
                
                // Extraire l'année de début
                const anneEvent = parseInt(event.date.toString().split('-')[0]);
                
                // Si l'événement n'a pas encore commencé
                if (anneEvent > anneeSelectionnee) {
                    return false;
                }
                
                // ⭐ Si l'événement est perpétuel, toujours afficher après le début
                if (event.perpetuel === true) {
                    console.log(`  ♾️ ${event.titre} (perpétuel depuis ${anneEvent}) → VISIBLE`);
                    return true;
                }
                
                // ⭐ Si l'événement a une date de fin
                if (event.date_fin) {
                    const anneeFin = parseInt(event.date_fin.toString().split('-')[0]);
                    const visible = anneeSelectionnee >= anneEvent && anneeSelectionnee <= anneeFin;
                    console.log(`  📅 ${event.titre} (${anneEvent}-${anneeFin}) → ${visible ? 'VISIBLE' : 'CACHÉ'}`);
                    return visible;
                }
                
                // Événement ponctuel : afficher seulement pour l'année exacte
                const visible = anneEvent === anneeSelectionnee;
                console.log(`  📌 ${event.titre} (${anneEvent}) → ${visible ? 'VISIBLE' : 'CACHÉ'}`);
                return visible;
            });
            
            // Créer marqueur si événements
            if (evenementsPays.length > 0) {
                console.log(`\n✅ ${pays.pays} : ${evenementsPays.length} événement(s) visible(s)`);
                this.creerMarqueur(pays, evenementsPays);
                totalMarqueurs++;
            }
        });
        
        console.log("\n" + "=".repeat(50));
        console.log(`✅ ${totalMarqueurs} marqueurs affichés sur la carte`);
        console.log("=".repeat(50) + "\n");
    }

    // Créer un marqueur
    creerMarqueur(pays, evenements) {
        if (!pays.coordonnees || 
            !Array.isArray(pays.coordonnees) || 
            pays.coordonnees.length !== 2 ||
            isNaN(pays.coordonnees[0]) || 
            isNaN(pays.coordonnees[1])) {
            console.error(`❌ Coordonnées invalides pour ${pays.pays}:`, pays.coordonnees);
            return;
        }

        let contenuPopup = `<h3>${pays.pays}</h3>`;
        contenuPopup += `<p><strong>${evenements.length} événement(s)</strong></p>`;
        
        // Ajouter les événements avec liens
        evenements.slice(0, 3).forEach(event => {
            contenuPopup += `
                <div style="margin: 8px 0; padding: 8px; background: #f0f0f0; border-radius: 4px;">
                    <strong style="color: #3b82f6;">${event.date}</strong><br>
                    <a href="${event.lien}" target="_blank" style="color: #1e40af; text-decoration: none; font-weight: 500;">
                        ${event.titre}
                    </a>
                </div>
            `;
        });
        
        if (evenements.length > 3) {
            contenuPopup += `<p><em>... et ${evenements.length - 3} autre(s)</em></p>`;
        }
        
        // Créer le marqueur
        const marqueur = L.marker(pays.coordonnees)
            .bindPopup(contenuPopup, { maxWidth: 300 })
            .addTo(marqueurs);
        
        // Clic pour timeline
        marqueur.on('click', () => {
            this.afficherTimeline(pays.pays, evenements);
        });
    }

    // Afficher la timeline
    afficherTimeline(nomPays, evenements) {
        const contenuTimeline = document.getElementById('contenu-timeline');
        if (!contenuTimeline) return;
        
        let html = `<h3>Timeline - ${nomPays}</h3>`;
        
        if (evenements.length === 0) {
            html += `<p>Aucun événement trouvé pour ${nomPays} avant ${anneeSelectionnee}.</p>`;
        } else {
            evenements.forEach(event => {
                html += `
                    <div style="margin: 12px 0; padding: 12px; background: var(--couleur-fond); border-left: 4px solid var(--couleur-accent); border-radius: 4px;">
                        <strong style="color: var(--couleur-accent);">${event.date}</strong><br>
                        <a href="${event.lien}" target="_blank" style="color: var(--couleur-accent); text-decoration: none; font-weight: 600;">
                            ${event.titre}
                        </a><br>
                        <em>${event.description}</em>
                    </div>
                `;
            });
        }
        
        contenuTimeline.innerHTML = html;
    }

    // ⭐ FONCTION CORRIGÉE - Mettre à jour les statistiques
    mettreAJourStatistiques() {
        const nbPaysElement = document.getElementById('nb-pays');
        const nbEvenementsElement = document.getElementById('nb-evenements');
        
        if (!nbPaysElement || !nbEvenementsElement) return;
        
        let paysAvecEvenements = 0;
        let totalEvenements = 0;
        
        PAYS_DATA.forEach(pays => {
            // ⭐ CORRECTION : Même logique de filtrage que mettreAJourMarqueurs
            const evenementsPays = EVENEMENTS_DATA.filter(event => {
                // Vérifier que c'est le bon pays
                if (event.pays.toLowerCase() !== pays.pays.toLowerCase()) {
                    return false;
                }
                
                // Sécurité : vérifier que date existe
                if (!event.date) {
                    return false;
                }
                
                const anneEvent = parseInt(event.date.split('-')[0]);
                
                // Si pas encore commencé
                if (anneEvent > anneeSelectionnee) {
                    return false;
                }
                
                // ⭐ Si perpétuel
                if (event.perpetuel === true) {
                    return true;
                }
                
                // ⭐ Si date de fin
                if (event.date_fin) {
                    const anneeFin = parseInt(event.date_fin.split('-')[0]);
                    return anneeSelectionnee >= anneEvent && anneeSelectionnee <= anneeFin;
                }
                
                // Ponctuel
                return anneEvent === anneeSelectionnee;
            });
            
            if (evenementsPays.length > 0) {
                paysAvecEvenements++;
                totalEvenements += evenementsPays.length;
            }
        });
        
        nbPaysElement.textContent = paysAvecEvenements;
        nbEvenementsElement.textContent = totalEvenements;
    }

    // Changer le thème
    changerTheme() {
        themeSombre = !themeSombre;
        
        if (themeSombre) {
            document.body.classList.add('theme-sombre');
        } else {
            document.body.classList.remove('theme-sombre');
        }
        
        localStorage.setItem('theme-sombre', themeSombre);
    }
}

// ========================================
// FONCTIONS UTILITAIRES
// ========================================

function ajouterPays(nom, continent, latitude, longitude) {
    PAYS_DATA.push({
        nom: nom,
        continent: continent,
        coordonnees: [latitude, longitude]
    });
    console.log(`✅ Pays ajouté : ${nom}`);
    
    if (window.gestionnaire) {
        window.gestionnaire.mettreAJourMarqueurs();
        window.gestionnaire.mettreAJourStatistiques();
    }
}

function ajouterEvenement(pays, date, titre, description, lien = "#") {
    EVENEMENTS_DATA.push({
        pays: pays,
        date: date,
        titre: titre,
        description: description,
        lien: lien
    });
    console.log(`✅ Événement ajouté : ${titre}`);
    
    if (window.gestionnaire) {
        window.gestionnaire.mettreAJourMarqueurs();
        window.gestionnaire.mettreAJourStatistiques();
    }
}

function sauvegarderPays() {
    const dataStr = JSON.stringify(PAYS_DATA, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'pays.json';
    link.click();
    URL.revokeObjectURL(url);
    console.log("💾 Fichier pays.json téléchargé !");
}

function sauvegarderEvenements() {
    const dataStr = JSON.stringify(EVENEMENTS_DATA, null, 2);
    const dataBlob = new Blob([dataStr], {type: 'application/json'});
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'evenements.json';
    link.click();
    URL.revokeObjectURL(url);
    console.log("💾 Fichier evenements.json téléchargé !");
}

// ========================================
// INITIALISATION
// ========================================

document.addEventListener('DOMContentLoaded', function() {
    console.log("🚀 Page chargée, initialisation...");
    
    // Charger le thème sauvegardé
    const themeSauvegarde = localStorage.getItem('theme-sombre');
    if (themeSauvegarde === 'true') {
        themeSombre = true;
        document.body.classList.add('theme-sombre');
    }
    
    // Créer le gestionnaire
    window.gestionnaire = new GestionnaireCarte();
    
    console.log("✅ Application initialisée !");
    console.log("💡 Commandes disponibles :");
    console.log("- ajouterPays(nom, continent, lat, lng)");
    console.log("- ajouterEvenement(pays, date, titre, description, lien)");
    console.log("- sauvegarderPays() / sauvegarderEvenements()");
});
