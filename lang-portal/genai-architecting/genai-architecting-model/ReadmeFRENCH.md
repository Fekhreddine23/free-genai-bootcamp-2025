# Architecting GenAI - Plateforme d'Apprentissage Linguistique

Ce schéma représente une plateforme interactive d'apprentissage des langues conçue pour aider les étudiants à maîtriser une langue en combinant des ressources pédagogiques, des activités immersives et des technologies avancées. Le système est divisé en plusieurs composants interconnectés, chacun jouant un rôle essentiel dans l'expérience utilisateur et le suivi des progrès.

## Structure Conceptuelle

### 1. **Lang Portal**

- **Description** : Interface principale utilisée par les étudiants et les enseignants.
- **Contient** :
  - **Word Group** : Regroupement de mots clés pour l'apprentissage.
  - **Profil utilisateur** : Gestion des informations personnelles et du suivi des progrès.
- **Connecté** à un système de **Progress Tracking** pour surveiller l'évolution des compétences.

### 2. **Base de données**

- **Description** : Contient les ressources linguistiques essentielles.
- **Contient** :
  - Un corpus de **2000 mots essentiels**.
  - Les **règles grammaticales** nécessaires à la construction de phrases.
- **Utilisée** pour alimenter les activités d'apprentissage.

### 3. **Activités d'apprentissage**

- **Description** : Modules interactifs pour renforcer les compétences linguistiques.
- **Inclut** :
  - **Writing Practice App** : Exercices d'écriture.
  - **Text Adventure Immersion** : Immersion dans des scénarios narratifs.
  - **Sentence Constructor** : Construction de phrases basées sur les règles grammaticales.
  - **Speak to Learn** : Pratique orale.
  - **Visual Flashcard Vocabulary** : Apprentissage visuel du vocabulaire.

## Fonctionnement Technique (Sentence Constructor)

### 1. **Requête (Query)**

- L'utilisateur soumet une requête via le module **Sentence Constructor**.

### 2. **RAG (Retrieval-Augmented Generation)**

- Recherche dans la base de données vectorielle pour récupérer les informations pertinentes (mots et règles grammaticales).
- Utilise une connexion Internet pour enrichir les réponses.

### 3. **Prompt Cache**

- Optimise les performances en stockant les prompts fréquemment utilisés.

### 4. **Pipeline IA**

- Intègre un modèle basé sur une **API LLM (Large Language Model)** comme GPT.
- Garantit la qualité des réponses grâce à :
  - **Input Guardian** : Vérification des données entrantes.
  - **Output Guardian** : Validation des réponses générées.

## Suivi des Progrès

Le système de suivi permet aux utilisateurs de visualiser leurs améliorations au fil du temps, en se basant sur leurs interactions avec les différents modules d'apprentissage.

## Objectifs

- Offrir une expérience d'apprentissage personnalisée et immersive.
- Faciliter la maîtrise d'une langue grâce à des outils technologiques avancés.
- Permettre aux enseignants de suivre et guider leurs étudiants efficacement.

## Technologies Utilisées

- **Base de données vectorielle** pour une recherche rapide.
- **Modèle LLM** (par exemple, GPT) pour la génération linguistique intelligente.
- Modules interactifs pour maximiser l'engagement utilisateur.
