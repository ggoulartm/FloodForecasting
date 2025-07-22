# 🌊 FloodForecastingMVP

**MVP de Prévision des Inondations pour les Alpes du Nord**

Ce projet fournit une interface web permettant de consulter les données hydrométriques historiques et en temps réel, et de générer des prévisions de débit avec différents algorithmes (tendance simple, moyenne mobile, régression linéaire).

## 🚀 Fonctionnalités

- Recherche et sélection de sites hydrométriques (Isère & Savoie)
- Affichage des données horaires (24 h) et journalières (30 jours)
- Prévisions sur 24 h avec bornes min/max d'incertitude
- Sélection d'algorithmes de prévision en temps réel
- Interface responsive (desktop/mobile)

## 🛠 Tech Stack

- Backend : Python 3.11, Flask, Flask-CORS, Flask-SQLAlchemy, SQLite
- Frontend : React 18, Vite, Recharts, Tailwind CSS
- Environnement : Conda (Python, Node.js), pip, npm

## Prérequis

- Git
- [Conda](https://docs.conda.io/) (ou Anaconda/Miniconda)
- Node.js & npm (installés via Conda ou depuis nodejs.org)

## Installation

1. Cloner le dépôt :
   ```cmd
   git clone https://github.com/your-org/FloodForecastingMVP.git
   cd FloodForecastingMVP
   ```

2. Créer l'environnement Conda :
   ```cmd
   conda env create -f environment.yml
   conda activate FloodForecastingMVP
   ```

3. Installer les dépendances Python :
   ```cmd
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. Préparer la base de données :
   ```cmd
   python src\main.py  # création automatique de database/app.db
   ```

5. Installer et lancer le frontend en mode développement :
   ```cmd
   cd src\static
   npm install
   npm run dev
   ```

6. Lancer le backend :
   ```cmd
   conda activate FloodForecastingMVP
   python src\main.py
   ```

7. Ouvrir l'application à : http://localhost:5173 (frontend) et http://localhost:5002 (API)

## Production (Build + Serve)

1. Générer le build React :
   ```cmd
   cd src\static
   npm run build
   ```

2. Configurer Flask pour servir le dossier `dist/` (voir commentaires dans `src/main.py`).
3. Lancer le serveur Flask :
   ```cmd
   python src\main.py
   ```
4. Accéder à l'interface sur http://localhost:5002

## Endpoints API

- GET `/api/flood/sites` : liste des sites hydrométriques
- GET `/api/flood/real-time-data/<code_site>` : observations en temps réel
- GET `/api/flood/historical-data/<code_site>` : données historiques 30 jours
- GET `/api/flood/forecast/<code_site>?algorithm=<key>` : prévisions 24 h

## 📄 Licence

Ce projet est sous licence MIT. Voir `LICENSE` pour plus de détails.
