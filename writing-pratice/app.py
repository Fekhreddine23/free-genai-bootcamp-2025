import streamlit as st
import requests
from enum import Enum
import json
from typing import Dict, Optional
import logging
import random
from groq import Groq
import time
from dotenv import load_dotenv
import os

# Configuration
load_dotenv(dotenv_path="writing-pratice/.env")
MODEL_NAME = "llama3-70b-8192"  # Modèle plus puissant et versatile
TEMPERATURE = 0.7
MAX_TOKENS = 1024

# Logging
logger = logging.getLogger("japanese_app")
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

fh = logging.FileHandler("app.log")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - JAPANESE_APP - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.propagate = False


# États de l'application
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"


class JapaneseLearningApp:
    def __init__(self):
        logger.debug("Initialisation de l'application...")
        self.initialize_session_state()
        self.load_vocabulary()
        self.init_groq_client()

    def initialize_session_state(self):
        """Initialise l'état de la session"""
        defaults = {
            "app_state": AppState.SETUP,
            "current_sentence": None,
            "review_data": None,
            "vocabulary_loaded": False,
            "last_error": None,
            "practice_history": [],
            "current_level": "N5",
        }

        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def init_groq_client(self):
        """Initialise le client Groq"""
        try:
            api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY", "")
            self.groq_client = Groq(api_key=api_key)
            logger.info("Client Groq initialisé")
        except Exception as e:
            logger.error(f"Erreur Groq: {e}")
            st.session_state.last_error = f"Erreur API: {str(e)}"
            self.groq_client = None

    def load_vocabulary(self):
        """Charge le vocabulaire"""
        try:
            # Version simplifiée avec vocabulaire intégré
            self.vocabulary = {
                "words": [
                    {
                        "kanji": "本",
                        "french": "livre",
                        "reading": "ほん",
                        "level": "N5",
                    },
                    {
                        "kanji": "食べる",
                        "french": "manger",
                        "reading": "たべる",
                        "level": "N5",
                    },
                    {"kanji": "水", "french": "eau", "reading": "みず", "level": "N5"},
                    {
                        "kanji": "旅行",
                        "french": "voyage",
                        "reading": "りょこう",
                        "level": "N4",
                    },
                    {
                        "kanji": "経済",
                        "french": "économie",
                        "reading": "けいざい",
                        "level": "N3",
                    },
                ]
            }
            st.session_state.vocabulary_loaded = True
            logger.info(f"Vocabulaire chargé ({len(self.vocabulary['words'])} mots)")

        except Exception as e:
            logger.error(f"Erreur vocabulaire: {e}")
            st.session_state.last_error = f"Erreur: {str(e)}"
            self.vocabulary = None

    def generate_sentence(self) -> Optional[Dict[str, str]]:
        """Génère une phrase avec Groq"""
        if not self.groq_client or not self.vocabulary:
            return None

        try:
            # Filtre par niveau JLPT
            level_words = [
                w
                for w in self.vocabulary["words"]
                if w["level"] == st.session_state.current_level
            ]
            if not level_words:
                level_words = self.vocabulary["words"]

            word = random.choice(level_words)

            prompt = f"""
            Tu es un professeur de japonais. Génère une phrase d'exemple en japonais utilisant le mot: {word['kanji']} ({word['reading']})
            
            Exigences:
            - Niveau JLPT {st.session_state.current_level}
            - Maximum 12 mots
            - Grammaire appropriée au niveau
            - Utilisation naturelle du mot
            
            Format de sortie JSON:
            {{
                "japanese": "phrase en japonais",
                "french": "traduction en français",
                "word_used": "{word['kanji']}",
                "word_reading": "{word['reading']}",
                "word_meaning": "{word['french']}",
                "grammar_points": ["point de grammaire 1", "point de grammaire 2"],
                "difficulty": "facile/moyen/difficile"
            }}
            """

            response = self.groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            result["source_word"] = word
            result["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

            # Enregistre dans l'historique
            st.session_state.practice_history.append(result)
            return result

        except Exception as e:
            logger.error(f"Erreur génération: {e}")
            st.session_state.last_error = f"Erreur: {str(e)}"
            return None

    def grade_submission(self, user_input: str, correct_sentence: str) -> Dict:
        """Évalue la soumission de l'utilisateur"""
        prompt = f"""
        Tu es un professeur de japonais. Évalue cette réponse d'étudiant:
        
        Phrase correcte: {correct_sentence}
        Réponse étudiante: {user_input}
        
        Analyse:
        - Exactitude (orthographe, grammaire)
        - Suggestions d'amélioration
        - Note globale (A-F)
        
        Format de sortie JSON:
        {{
            "grade": "note A-F",
            "accuracy": "score 0-100",
            "feedback": "retour détaillé en français",
            "corrected": "phrase corrigée si nécessaire",
            "common_mistakes": ["erreur1", "erreur2"]
        }}
        """

        try:
            response = self.groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Plus strict pour l'évaluation
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Erreur évaluation: {e}")
            return {
                "grade": "E",
                "accuracy": 0,
                "feedback": f"Erreur d'évaluation: {str(e)}",
                "corrected": correct_sentence,
                "common_mistakes": [],
            }

    def render_ui(self):
        """Affiche l'interface utilisateur"""
        st.title("🇯🇵 Pratique d'Écriture Japonaise")

        # Sidebar avec configuration
        with st.sidebar:
            st.header("Configuration")
            st.session_state.current_level = st.selectbox(
                "Niveau JLPT", ["N5", "N4", "N3", "N2", "N1"], index=0
            )

            if st.button("Nouvelle phrase"):
                sentence = self.generate_sentence()
                if sentence:
                    st.session_state.current_sentence = sentence
                    st.session_state.app_state = AppState.PRACTICE
                else:
                    st.error("Erreur de génération")

            if st.session_state.practice_history:
                st.header("Historique")
                for i, item in enumerate(st.session_state.practice_history[-5:]):
                    st.caption(f"{i+1}. {item['japanese']} ({item['word_used']})")

        # État principal
        if st.session_state.last_error:
            st.error(st.session_state.last_error)
            st.session_state.last_error = None

        if st.session_state.app_state == AppState.SETUP:
            self.render_setup_state()
        elif st.session_state.app_state == AppState.PRACTICE:
            self.render_practice_state()
        elif st.session_state.app_state == AppState.REVIEW:
            self.render_review_state()

    def render_setup_state(self):
        """Affiche l'état initial"""
        st.markdown(
            """
        ### Bienvenue dans votre assistant d'écriture japonaise
            
        **Fonctionnalités:**
        - Génération de phrases adaptées à votre niveau
        - Évaluation automatique de vos réponses
        - Historique de pratique
            
        Commencez par sélectionner votre niveau JLPT dans la sidebar et cliquez sur "Nouvelle phrase".
        """
        )

        if not st.session_state.vocabulary_loaded:
            st.warning("Chargement du vocabulaire...")

    def render_practice_state(self):
        """Affiche l'état de pratique"""
        if not st.session_state.current_sentence:
            st.warning("Aucune phrase générée")
            return

        sentence = st.session_state.current_sentence
        st.subheader("Phrase à écrire")
        st.markdown(
            f"""
        **Mot clé:** {sentence['word_used']} ({sentence['word_reading']})  
        **Signification:** {sentence['word_meaning']}  
        **Traduction:** {sentence['french']}
        """
        )

        user_input = st.text_area("Écrivez la phrase en japonais:", height=100)

        if st.button("Soumettre"):
            if user_input.strip():
                review = self.grade_submission(user_input, sentence["japanese"])
                st.session_state.review_data = {
                    "user_input": user_input,
                    "correct_sentence": sentence["japanese"],
                    "review": review,
                }
                st.session_state.app_state = AppState.REVIEW
                st.rerun()
            else:
                st.warning("Veuillez entrer votre réponse")

    def render_review_state(self):
        """Affiche les résultats"""
        if not st.session_state.review_data:
            st.error("Aucune donnée d'évaluation")
            return

        data = st.session_state.review_data
        review = data["review"]

        st.subheader("Résultats")
        col1, col2 = st.columns(2)
        col1.metric("Note", review["grade"])
        col2.metric("Précision", f"{review.get('accuracy', 0)}%")

        st.markdown(
            f"""
        **Votre réponse:**  
        {data['user_input']}
            
        **Correction:**  
        {review['corrected']}
            
        **Feedback:**  
        {review['feedback']}
        """
        )

        if st.button("Nouvel exercice"):
            st.session_state.app_state = AppState.SETUP
            st.rerun()


# Lancement de l'app
if __name__ == "__main__":
    app = JapaneseLearningApp()
    app.render_ui()
