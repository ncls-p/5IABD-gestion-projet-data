# 🗓️ Calendar Planning Assistant

Un assistant de planification de calendrier intelligent qui utilise GPT d'OpenAI pour gérer et planifier les événements. Construit avec FastAPI, Streamlit et PostgreSQL, suivant les principes de Clean Architecture.

## 📋 Fonctionnalités

- 💬 Interface en langage naturel pour la gestion du calendrier
- ➕ Création, suppression et visualisation d'événements
- 🤖 Suggestions de planification intelligentes
- 📅 Export du calendrier au format ICS
- 📊 Planification basée sur la semaine
- 🔄 Gestion flexible des événements
- 🌍 Support multilingue (français/anglais)

## 🏗️ Architecture du Projet
```
src/
├── core/ # Configuration et utilitaires
│ ├── config.py # Configuration de l'application
│ └── logger.py # Configuration des logs
├── domain/ # Logique métier et entités
│ ├── entities/ # Modèles de domaine
│ │ ├── event.py # Entité événement
│ │ └── message.py # Entité message
│ └── interfaces/ # Interfaces abstraites
│ └── repositories.py # Interfaces des repositories
├── infrastructure/ # Implémentation des services externes
│ ├── database/ # Implémentation base de données
│ │ └── postgres.py # Repository PostgreSQL
│ └── llm/ # Implémentation service LLM
│ └── openai.py # Repository OpenAI
├── application/ # Services applicatifs
│ └── services/ # Services métier
│ ├── calendar_service.py
│ └── chat_service.py
└── interfaces/ # Adaptateurs d'interface
├── api/ # Routes et schémas FastAPI
│ ├── routes/ # Points d'entrée API
│ └── schemas/ # Modèles Pydantic
└── ui/ # Interface utilisateur Streamlit
└── streamlit_app.py
```

## 🛠️ Prérequis

- Python 3.8+
- PostgreSQL
- Clé API OpenAI

## ⚙️ Installation

1. Cloner le repository:

```bash
git clone https://github.com/yourusername/calendar-planning-assistant.git
```

2. Créer et activer un environnement virtuel:

```bash
python -m venv .venv
source .venv/bin/activate # Sur Windows: .venv\Scripts\activate
```

3. Installer les dépendances:

```bash
pip install -r requirements.txt
```

4. Configurer les variables d'environnement:

```bash
cp .env.example .env
```

### Éditer .env avec votre configuration

```bash
docker compose up -d
```


## 🚀 Lancement de l'Application

1. Démarrer le serveur backend:

```bash
python run.py
```


2. Démarrer l'application frontend:

```bash
bash
python -m streamlit run src/interfaces/ui/streamlit_app.py
```


L'application sera accessible à:
- Frontend: http://localhost:8501
- API Backend: http://localhost:8000
- Documentation API: http://localhost:8000/docs

## 💡 Utilisation

### Interface Utilisateur
1. Ouvrir l'interface Streamlit dans votre navigateur
2. Utiliser la barre latérale pour sélectionner la semaine à planifier
3. Vous pouvez:
   - Demander à l'assistant de planifier votre semaine
   - Ajouter des événements spécifiques
   - Voir les événements existants
   - Supprimer des événements
   - Exporter votre calendrier au format ICS

### Exemples de Commandes
En français:
- "Planifie ma semaine de travail"
- "Ajoute une réunion demain à 14h"
- "Montre-moi mes événements"
- "Supprime la réunion de demain"

En anglais:
- "Plan my work week"
- "Add a meeting tomorrow at 2pm"
- "Show me my events"
- "Delete tomorrow's meeting"

## 🔑 Variables d'Environnement

Configuration dans le fichier `.env`:
```bash
env
Configuration Base de données
POSTGRES_HOST=localhost
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=mysecretpassword
POSTGRES_PORT=5432
Configuration OpenAI
LLM_API_URL=https://api.openai.com/v1/chat/completions
MODEL_ID=gpt-3.5-turbo
LLM_API_KEY=your-openai-api-key
```


## 🏗️ Architecture

Ce projet suit les principes de Clean Architecture:

- **Domain Layer**: Logique métier et entités
  - Définit les entités et les interfaces des repositories
  - Indépendant des frameworks et des services externes

- **Application Layer**: Cas d'utilisation et services
  - Implémente la logique métier
  - Orchestre les interactions entre les entités

- **Infrastructure Layer**: Implémentation des services externes
  - Gère la persistance des données
  - Intègre les services externes (OpenAI)

- **Interface Layer**: Adaptateurs d'interface
  - API REST avec FastAPI
  - Interface utilisateur avec Streamlit

## 🔍 Dépannage

### Problèmes Courants

1. **Erreur de connexion à PostgreSQL**
   - Vérifier que PostgreSQL est en cours d'exécution
   - Vérifier les informations de connexion dans `.env`

2. **Erreur d'API OpenAI**
   - Vérifier que la clé API est valide
   - Vérifier le modèle spécifié dans `.env`

3. **Erreur de démarrage de l'application**
   - Vérifier que tous les packages sont installés
   - Vérifier que les ports 8000 et 8501 sont disponibles

## 📚 Documentation API

La documentation complète de l'API est disponible à `http://localhost:8000/docs` une fois l'application lancée.

Endpoints principaux:
- `POST /chat` - Interaction avec l'assistant
- `GET /events` - Liste des événements
- `POST /events` - Création d'événement
- `DELETE /events/{id}` - Suppression d'événement
- `POST /export-ics` - Export du calendrier

## 🤝 Contribution

1. Forker le repository
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Créer une Pull Request

## 📝 Licence

Ce projet est sous licence MIT - voir le fichier LICENSE pour plus de détails.

