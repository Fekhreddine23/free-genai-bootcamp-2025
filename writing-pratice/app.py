import streamlit as st
import json
import logging
import random
from groq import Groq
import time
from dotenv import load_dotenv
import os
from enum import Enum
from typing import Dict, Optional

# Configuration
load_dotenv(dotenv_path="writing-pratice/.env")
MODEL_NAME = "llama3-70b-8192"  # Modèle plus puissant et versatile
TEMPERATURE = 0.7
MAX_TOKENS = 1024

# Logging
logger = logging.getLogger("japanese_app")
logger.setLevel(logging.DEBUG)

# Configuration du log
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

        # Initialisation des états de session
        if "app_state" not in st.session_state:
            st.session_state.app_state = AppState.SETUP
        if "current_sentence" not in st.session_state:
            st.session_state.current_sentence = None

        self.initialize_session_state()  # Initialisation des états de session
        self.load_vocabulary()  # Chargement du vocabulaire
        self.init_groq_client()  # Initialisation du client Groq

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
        if not self.groq_client:
            st.error("Erreur: Client Groq non initialisé.")
            return None
        if not self.vocabulary:
            st.error("Erreur: Vocabulaire non chargé.")
            return None

        try:
            level_words = [
                w
                for w in self.vocabulary["words"]
                if w["level"] == st.session_state.current_level
            ]
            if not level_words:
                level_words = self.vocabulary["words"]

            word = random.choice(level_words)
            logger.debug(f"Mot sélectionné: {word['kanji']}")

            prompt = f"""
            Tu es un professeur de japonais expérimenté. Génère une phrase d'exemple en japonais utilisant le mot: {word['kanji']} ({word['reading']})

            Exigences STRICTES:
            - Niveau JLPT {st.session_state.current_level}
            - Maximum 12 mots
            - Uniquement la phrase en japonais et sa traduction
            - Format JSON valide et bien formé

            Format de réponse STRICT:
            {{
                "japanese": "phrase en japonais",
                "french": "traduction en français",
                "word_used": "{word['kanji']}",
                "word_reading": "{word['reading']}",
                "word_meaning": "{word['french']}",
                "grammar_points": ["point1", "point2"],
                "difficulty": "facile/moyen/difficile"
            }}
            Exemple VALIDE:
            {{
                "japanese": "私は本を読みます",
                "french": "Je lis un livre",
                "word_used": "本",
                "word_reading": "ほん",
                "word_meaning": "livre",
                "grammar_points": ["particule を", "verbe en -ます"],
                "difficulty": "facile"
            }}
            """

            response = self.groq_client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Réduit pour plus de cohérence
                max_tokens=MAX_TOKENS,
                response_format={"type": "json_object"},
            )

            result = json.loads(response.choices[0].message.content)
            logger.debug(f"Réponse reçue: {result}")

            # Validation des champs obligatoires
            required_fields = [
                "japanese",
                "french",
                "word_used",
                "word_reading",
                "word_meaning",
            ]
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Champ manquant: {field}")

            result["source_word"] = word
            result["generated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")

            if "practice_history" not in st.session_state:
                st.session_state.practice_history = []
            st.session_state.practice_history.append(result)

            return result

        except Exception as e:
            logger.error(f"Erreur génération: {str(e)}")
            st.error(f"Erreur lors de la génération: {str(e)}")
            return None

    def render_setup_state(self):
        """Affiche l'état initial de l'application"""
        st.write("Débogage : L'état SETUP est en cours d'affichage")

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

    def render_ui(self):
        """Affiche l'interface utilisateur"""
        st.title("🇯🇵 Pratique d'Écriture Japonaise")

        # Débogage : afficher un message pour confirmer que la fonction s'exécute
        st.write("Débogage : L'interface utilisateur a démarré")

        # Initialisation critique des états
        if "app_state" not in st.session_state:
            st.session_state.app_state = AppState.SETUP
            st.write("Débogage : Passage à l'état SETUP")

        # Vérification de l'état actuel
        st.write(f"État actuel de l'application : {st.session_state.app_state}")
        st.write(f"Vocabulaire chargé : {st.session_state.vocabulary_loaded}")

        # Sidebar - Doit persister entre les reruns
        with st.sidebar:
            st.header("Configuration")
            level = st.selectbox(
                "Niveau JLPT",
                ["N5", "N4", "N3", "N2", "N1"],
                index=["N5", "N4", "N3", "N2", "N1"].index(
                    st.session_state.get("current_level", "N5")
                ),
            )

            st.write(f"Niveau JLPT sélectionné : {level}")

            if level != st.session_state.get("current_level"):
                st.session_state.current_level = level
                st.write(f"Débogage : Niveau changé en {level}")
                st.rerun()

            if st.button("✨ Nouvelle phrase", type="primary", key="new_sentence"):
                st.session_state.app_state = AppState.PRACTICE
                with st.spinner("Création d'un nouvel exercice..."):
                    sentence = self.generate_sentence()
                    if sentence:
                        st.session_state.current_sentence = sentence
                        st.session_state.practice_started = True
                    else:
                        st.error("Échec de la génération")
                        st.session_state.app_state = AppState.SETUP

            if st.session_state.get("practice_history"):
                st.header("Derniers exercices")
                for i, item in enumerate(
                    reversed(st.session_state.practice_history[-3:])
                ):
                    st.caption(
                        f"{len(st.session_state.practice_history)-i}. {item['japanese']}"
                    )

        # Contenu principal - Gestion des états
        if st.session_state.app_state == AppState.SETUP:
            self.render_setup_state()
        elif st.session_state.app_state == AppState.PRACTICE:
            if (
                "current_sentence" in st.session_state
                and st.session_state.current_sentence
            ):
                self.render_practice_state()
            else:
                st.warning("Génération en cours...")
                st.session_state.app_state = AppState.SETUP
        elif st.session_state.app_state == AppState.REVIEW:
            self.render_review_state()

    def render_practice_state(self):
        """Affiche l'état de pratique"""
        if (
            "current_sentence" not in st.session_state
            or st.session_state.current_sentence is None
        ):
            st.warning("Veuillez générer une nouvelle phrase")
            return

        sentence = st.session_state.current_sentence
        st.subheader("Phrase à écrire")

        # Affichage de la phrase générée
        st.markdown(
            f"**Mot à utiliser :** `{sentence['word_used']}` ({sentence['word_reading']})"
        )
        st.caption(f"Signification : {sentence['word_meaning']}")

        # Zone de réponse
        st.markdown("### Votre réponse")
        user_input = st.text_area(
            "Tapez la phrase en japonais:",
            value="",
            height=100,
            key=f"input_{sentence['generated_at']}",  # Clé unique par exercice
        )
        st.write(f"Réponse utilisateur : {user_input}")  # Debug

        # Boutons de contrôle
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔍 Vérifier", type="primary"):
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
                    st.warning("Veuillez écrire votre réponse")

        with col2:
            if st.button("🔄 Nouvel exercice"):
                st.session_state.app_state = AppState.SETUP
                st.session_state.current_sentence = None
                st.rerun()

        # Aide contextuelle
        with st.expander("💡 Indice"):
            st.markdown(f"**Traduction :** {sentence['french']}")
            st.caption(f"Points de grammaire : {', '.join(sentence['grammar_points'])}")

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
            st.session_state.current_sentence = None  # Réinitialiser la phrase actuelle
            st.session_state.review_data = None  # Réinitialiser les données de révision
            st.rerun()

    def grade_submission(self, user_input: str, correct_sentence: str) -> Dict:
        """Évalue la soumission de l'utilisateur"""
        return {
            "grade": "B",
            "accuracy": 80,
            "corrected": correct_sentence,
            "feedback": "Votre réponse est presque correcte, vérifiez l'ordre des particules.",
        }


# Lancement de l'app
if __name__ == "__main__":
    app = JapaneseLearningApp()
    app.render_ui()
