
# Architecting GenAI -  Language Learning Platform

This diagram represents an interactive language learning platform designed to help students master a language by combining educational resources, immersive activities, and advanced technologies. The system is divided into several interconnected components, each playing a crucial role in the user experience and progress tracking.

## Conceptual Structure

### 1. **Lang Portal**

- **Description**: Main interface used by students and teachers.
- **Contains**:
  - **Word Group**: Grouping of key words for learning.
  - **User Profile**: Management of personal information and progress tracking.
- **Connected** to a **Progress Tracking** system to monitor skill development.

### 2. **Database**

- **Description**: Contains essential linguistic resources.
- **Contains**:
  - A corpus of **2000 essential words**.
  - **Grammatical rules** necessary for sentence construction.
- **Used** to fuel learning activities.

### 3. **Learning Activities**

- **Description**: Interactive modules to reinforce language skills.
- **Includes**:
  - **Writing Practice App**: Writing exercises.
  - **Text Adventure Immersion**: Immersion in narrative scenarios.
  - **Sentence Constructor**: Sentence construction based on grammatical rules.
  - **Speak to Learn**: Oral practice.
  - **Visual Flashcard Vocabulary**: Visual vocabulary learning.

## Technical Workflow (Sentence Constructor)

### 1. **Query**

- The user submits a query via the **Sentence Constructor** module.

### 2. **RAG (Retrieval-Augmented Generation)**

- Searches the vector database to retrieve relevant information (words and grammatical rules).
- Uses an internet connection to enrich responses.

### 3. **Prompt Cache**

- Optimizes performance by storing frequently used prompts.

### 4. **AI Pipeline**

- Integrates an API-based model using a **LLM (Large Language Model)** such as GPT.
- Ensures response quality through:
  - **Input Guardian**: Verification of incoming data.
  - **Output Guardian**: Validation of generated responses.

## Progress Tracking

The tracking system allows users to visualize their improvements over time, based on their interactions with the various learning modules.

## Objectives

- Provide a personalized and immersive learning experience.
- Facilitate language mastery through advanced technological tools.
- Enable teachers to effectively monitor and guide their students.

## Technologies Used

- **Vector database** for fast search.
- **LLM model** (e.g., GPT) for intelligent language generation.
- Interactive modules to maximize user engagement.
