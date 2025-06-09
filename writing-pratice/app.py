import yaml
import streamlit as st
import random
import logging
import json
from enum import Enum
from typing import Dict
from PIL import Image
import numpy as np
import io
import os
import requests
from datetime import datetime
import fitz  # PyMuPDF
from Levenshtein import ratio

try:
    from manga_ocr import MangaOcr
    from streamlit_drawable_canvas import st_canvas
    from groq import Groq
except ImportError as e:
    logger.error(
        f"Erreur d'importation: {str(e)}. Assurez-vous que toutes les dépendances sont installées."
    )
    st.error(f"Erreur: {str(e)}. Veuillez installer les dépendances nécessaires.")
    raise

# Configuration du logger
logger = logging.getLogger("japanese_app")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    file_handler = logging.FileHandler("app.log")
    file_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"


class JapaneseLearningApp:
    def __init__(self):
        if "app_initialized" not in st.session_state:
            logger.debug("Initialisation de l'application...")
            self.load_prompt_yaml()
            self.initialize_session_state()
            self.load_vocabulary()
            self.mocr = MangaOcr()
            api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
            if api_key:
                self.groq_client = Groq(api_key=api_key)
                logger.debug("Groq configuré.")
            else:
                logger.warning("Aucune clé API Groq trouvée.")
                self.groq_client = None
            self.pre_generated_sentences = self.pre_generate_sentences()
            st.session_state.app_initialized = True
            logger.debug("Application initialisée")

    def load_prompt_yaml(self):
        try:
            yaml_file_path = os.path.join(os.path.dirname(__file__), "prompt.yaml")
            with open(yaml_file_path, "r", encoding="utf-8") as file:
                self.prompt_config = yaml.safe_load(file) or {}
                logger.info("Fichier prompt.yaml chargé avec succès.")
        except FileNotFoundError:
            logger.error("Fichier prompt.yaml introuvable.")
            st.error("Erreur : Fichier prompt.yaml introuvable.")
            self.prompt_config = {}
        except Exception as e:
            logger.error(f"Erreur YAML: {str(e)}")
            st.error(f"Erreur lors du chargement du YAML: {str(e)}")
            self.prompt_config = {}

    def initialize_session_state(self):
        defaults = {
            "app_state": AppState.SETUP,
            "current_sentence": None,
            "review_data": None,
            "vocabulary_loaded": False,
            "practice_history": [],
            "current_level": "N5",
            "drawing_data": None,
            "recognized_text": "",
            "exercise_started": False,
            "alternative_sentences": {},
        }
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def load_vocabulary(self):
        if not st.session_state.vocabulary_loaded:
            st.session_state.vocabulary = {
                "words": [
                    {
                        "kanji": "本",
                        "french": "livre",
                        "reading": "ほん",
                        "level": "N5",
                        "contexts": ["lire", "acheter", "emporter"],
                    },
                    {
                        "kanji": "食べる",
                        "french": "manger",
                        "reading": "たべる",
                        "level": "N5",
                        "contexts": ["repas", "nourriture", "restaurant"],
                    },
                    {
                        "kanji": "水",
                        "french": "eau",
                        "reading": "みず",
                        "level": "N5",
                        "contexts": ["boire", "verser", "bouteille"],
                    },
                    {
                        "kanji": "旅行",
                        "french": "voyage",
                        "reading": "りょこう",
                        "level": "N4",
                        "contexts": ["partir", "vacances", "bagages"],
                    },
                    {
                        "kanji": "経済",
                        "french": "économie",
                        "reading": "けいざい",
                        "level": "N3",
                        "contexts": ["étudier", "nouvelle", "système"],
                    },
                    {
                        "kanji": "学校",
                        "french": "école",
                        "reading": "がっこう",
                        "level": "N5",
                        "contexts": ["étudier", "aller", "élève"],
                    },
                ]
            }
            st.session_state.vocabulary_loaded = True
            logger.info(
                f"Vocabulaire chargé ({len(st.session_state.vocabulary['words'])} mots)"
            )

    def validate_semantics(self, response: dict, word: dict) -> bool:
        if not response.get("japanese") or not response.get("hint"):
            return False
        hint_lower = response["hint"].lower()
        word_french_lower = word["french"].lower()
        return word_french_lower in hint_lower

    def generate_sentence_with_groq(self, word: dict, attempts=3) -> dict:
        if not self.groq_client:
            logger.warning("Groq non configuré. Utilisation de phrases de secours.")
            return self.generate_fallback_sentence(word)

        if attempts <= 0:
            logger.warning(f"Maximum d'essais atteint pour {word['kanji']}")
            return self.generate_fallback_sentence(word)

        try:
            prompt = self.prompt_config["sentence_generation"]["user"].format(
                word=word["kanji"]
            )
            chat_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.prompt_config["sentence_generation"]["system"],
                    },
                    {"role": "user", "content": prompt},
                ],
                model="llama3-70b-8192",
                temperature=0.7,
                max_tokens=300,
            )
            japanese_sentence = chat_completion.choices[0].message.content.strip()

            translation_prompt = self.prompt_config["translation"]["user"].format(
                text=japanese_sentence
            )
            translation_completion = self.groq_client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": self.prompt_config["translation"]["system"],
                    },
                    {"role": "user", "content": translation_prompt},
                ],
                model="llama3-70b-8192",
                temperature=0.2,
                max_tokens=150,
            )
            hint = translation_completion.choices[0].message.content.strip()

            return {
                "japanese": japanese_sentence,
                "hint": hint,
                "word_used": word["kanji"],
                "word_reading": word["reading"],
                "word_meaning": word["french"],
                "grammar_points": ["auto-généré"],
                "difficulty": word["level"],
                "context": random.choice(word["contexts"]),
            }
        except Exception as e:
            logger.error(f"Erreur Groq: {str(e)}")
            return self.generate_fallback_sentence(word)

    def pre_generate_sentences(self):
        sentences = {}
        for word in st.session_state.vocabulary["words"]:
            alternatives = []
            for _ in range(3):
                sentence = self.generate_sentence_with_groq(
                    word
                ) or self.generate_fallback_sentence(word)
                alternatives.append(sentence)
            sentences[word["kanji"]] = alternatives
        return sentences

    def generate_fallback_sentence(self, word: dict) -> dict:
        templates = {
            "lire": [
                ("{}を読みます", "Je lis [quelque chose]"),
                ("{}が面白い", "[Quelque chose] est intéressant"),
                ("{}を買った", "J'ai acheté [quelque chose]"),
            ],
            "manger": [
                ("{}を食べたい", "Je veux manger [quelque chose]"),
                ("{}を作る", "Je cuisine [quelque chose]"),
                ("{}が美味しい", "[Quelque chose] est délicieux"),
            ],
            "boire": [
                ("{}を飲む", "Je bois [quelque chose]"),
                ("{}が欲しい", "Je veux [quelque chose]"),
                ("{}をください", "Donnez-moi [quelque chose]"),
            ],
        }
        used_context = word["contexts"][0]
        template, hint = random.choice(
            templates.get(used_context, [("{}を使う", "J'utilise [quelque chose]")])
        )
        return {
            "japanese": template.format(word["kanji"]),
            "hint": hint,
            "word_used": word["kanji"],
            "word_reading": word["reading"],
            "word_meaning": word["french"],
            "grammar_points": ["phrase simple"],
            "difficulty": word["level"],
            "context": used_context,
        }

    def generate_sentence(self) -> dict:
        level_words = [
            w
            for w in st.session_state.vocabulary["words"]
            if w["level"] == st.session_state.current_level
        ]

        if not level_words:
            st.error(f"Aucun mot pour le niveau {st.session_state.current_level}")
            return None

        word = random.choice(level_words)

        if word["kanji"] in self.pre_generated_sentences:
            return random.choice(self.pre_generated_sentences[word["kanji"]])

        return self.generate_sentence_with_groq(
            word
        ) or self.generate_fallback_sentence(word)

    def render_setup_state(self):
        st.markdown(
            """
        ### Assistant d'Écriture Japonaise
        **Fonctionnalités:**
        - Phrases adaptées à votre niveau JLPT
        - Reconnaissance d'écriture manuscrite
        - Feedback immédiat
        - Exemples variés
        """
        )

        st.session_state.current_level = st.selectbox(
            "Choisissez votre niveau JLPT", ["N5", "N4", "N3", "N2", "N1"], index=0
        )

        if st.button("Commencer la Pratique"):
            self.pre_generated_sentences = self.pre_generate_sentences()
            st.session_state.app_state = AppState.PRACTICE
            st.session_state.current_sentence = self.generate_sentence()
            st.session_state.exercise_started = True
            st.rerun()

    def render_practice_state(self):
        if not st.session_state.current_sentence:
            st.session_state.current_sentence = self.generate_sentence()

        sentence = st.session_state.current_sentence
        st.subheader("Exercice d'Écriture")

        with st.expander("📝 Phrase Modèle", expanded=True):
            st.markdown(f"**Japonais:** `{sentence['japanese']}`")
            st.caption(f"**Indice:** {sentence['hint']}")
            st.caption(f"**Contexte:** {sentence['context']}")

        st.markdown(
            f"""
        **Mot Clé:**  
        `{sentence['word_used']}` ({sentence['word_reading']})  
        *Signification: {sentence['word_meaning']}*
        """
        )

        st.subheader("Soumettre votre réponse en téléchargeant un fichier")
        uploaded_file = st.file_uploader(
            "Téléchargez votre fichier de réponse", type=["jpg", "png", "pdf", "txt"]
        )

        if uploaded_file is not None:
            st.write(f"Fichier téléchargé: {uploaded_file.name}")

            if uploaded_file.type in ["image/jpeg", "image/png"]:
                image = Image.open(uploaded_file)
                st.image(image, caption="Image téléchargée", use_column_width=True)

                try:
                    recognized_text = self.mocr(image)
                    st.session_state.recognized_text = recognized_text
                    st.success(f"Reconnaissance: {recognized_text}")
                except Exception as e:
                    st.error(f"Erreur lors de la reconnaissance: {str(e)}")

            elif uploaded_file.type == "application/pdf":
                text = self.extract_text_from_pdf(uploaded_file)
                st.text_area("Texte extrait du PDF", value=text, height=100)

            elif uploaded_file.type == "text/plain":
                text = uploaded_file.getvalue().decode("utf-8")
                st.text_area("Texte téléchargé", value=text, height=100)

        canvas_result = st_canvas(
            stroke_width=3,
            stroke_color="#000000",
            background_color="#FFFFFF",
            height=200,
            drawing_mode="freedraw",
            key="canvas",
        )

        if canvas_result.image_data is not None and st.button("Analyser le Dessin"):
            img = Image.fromarray(
                (canvas_result.image_data[:, :, :3] * 255).astype(np.uint8)
            )
            st.session_state.drawing_data = img

            try:
                recognized_text = self.mocr(img)
                st.session_state.recognized_text = recognized_text
                st.success(f"Reconnaissance: {recognized_text}")
            except Exception as e:
                st.error(f"Erreur: {str(e)}")

        user_input = st.text_area(
            "Ou écrivez directement:",
            value=getattr(st.session_state, "recognized_text", ""),
            height=100,
            key="user_input",
        )

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Vérifier", type="primary"):
                self.check_answer(user_input)
        with col2:
            if st.button("🔄 Nouveau Mot"):
                self.reset_exercise()
        with col3:
            if st.button("🔀 Autre Exemple"):
                self.show_alternative()

    def check_answer(self, user_input: str = None):
        """Évalue la réponse de l'utilisateur et enregistre le résultat"""
        if user_input is None:
            user_input = st.session_state.get("recognized_text", "").strip()

        if not user_input:
            st.warning("Veuillez écrire ou dessiner votre réponse")
            return

        # Évaluation locale
        review = self.grade_submission(
            user_input, st.session_state.current_sentence["japanese"]
        )
        current_word_kanji = st.session_state.current_sentence["word_used"]
        current_word = next(
            (
                w
                for w in st.session_state.vocabulary["words"]
                if w["kanji"] == current_word_kanji
            ),
            None,
        )

        if not current_word:
            st.error("Mot courant non trouvé dans le vocabulaire")
            return

        # Préparation des données pour le backend
        submission_data = {
            "session": {"group_id": 1, "study_activity_id": 1},
            "answers": [
                {
                    "word_id": self.get_word_id(current_word_kanji),
                    "correct": review["grade"] in ["A+", "A"],
                }
            ],
        }

        logger.debug(f"Données soumises: {json.dumps(submission_data, indent=2)}")

        try:
            # Création de la session
            session_response = requests.post(
                "http://localhost:5000/study_sessions",
                json=submission_data["session"],
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            session_response.raise_for_status()
            session_data = session_response.json()
            logger.debug(f"Réponse de création de session: {session_data}")
            session_id = session_data.get("session_id")

            if not session_id:
                st.error("Erreur: session_id non retourné par le serveur")
                return

            # Enregistrement des réponses
            review_response = requests.post(
                f"http://localhost:5000/study_sessions/{session_id}/review",
                json={
                    "answers": submission_data["answers"]
                },  # Envelopper dans {"answers": ...}
                headers={"Content-Type": "application/json"},
                timeout=5,
            )
            review_response.raise_for_status()
            logger.debug(
                f"Réponse de l'enregistrement des réponses: {review_response.json()}"
            )

            # Récupération des résultats
            results_response = requests.get(
                f"http://localhost:5000/api/study-sessions/{session_id}", timeout=5
            )
            results_response.raise_for_status()
            results = results_response.json()

            st.session_state.review_data = {
                "user_input": user_input,
                "correct_sentence": st.session_state.current_sentence["japanese"],
                "review": review,
                "drawing": st.session_state.drawing_data,
                "backend_data": results.get("session", {}),
            }
            st.session_state.app_state = AppState.REVIEW
            st.rerun()

        except requests.exceptions.HTTPError as e:
            logger.error(f"Erreur HTTP: {str(e)} - Détails: {e.response.text}")
            st.error(f"Erreur lors de la soumission: {e.response.text}")
            # Fallback local
            st.session_state.review_data = {
                "user_input": user_input,
                "correct_sentence": st.session_state.current_sentence["japanese"],
                "review": review,
                "drawing": st.session_state.drawing_data,
                "backend_data": None,
            }
            st.session_state.app_state = AppState.REVIEW
            st.rerun()
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion au backend: {str(e)}")
            st.error(f"Erreur de connexion au serveur: {str(e)}")
            st.session_state.review_data = {
                "user_input": user_input,
                "correct_sentence": st.session_state.current_sentence["japanese"],
                "review": review,
                "drawing": st.session_state.drawing_data,
                "backend_data": None,
            }
            st.session_state.app_state = AppState.REVIEW
            st.rerun()

    def get_word_id(self, kanji: str) -> int:
        for idx, word in enumerate(st.session_state.vocabulary["words"]):
            if word["kanji"] == kanji:
                return idx + 1
        return 1

    def reset_exercise(self):
        st.session_state.current_sentence = self.generate_sentence()
        st.session_state.drawing_data = None
        st.session_state.recognized_text = ""

    def show_alternative(self):
        current_word = st.session_state.current_sentence["word_used"]
        if current_word in self.pre_generated_sentences:
            alternatives = [
                s
                for s in self.pre_generated_sentences[current_word]
                if s["japanese"] != st.session_state.current_sentence["japanese"]
            ]
            if alternatives:
                st.session_state.current_sentence = random.choice(alternatives)
                st.rerun()

    def render_review_state(self):
        if not st.session_state.review_data:
            st.error("Aucune donnée disponible")
            st.session_state.app_state = AppState.SETUP
            st.rerun()
            return

        data = st.session_state.review_data
        backend_data = data.get("backend_data", {})

        st.subheader("Résultats")

        if data.get("drawing"):
            buf = io.BytesIO()
            data["drawing"].save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Votre écriture", width=200)

        if backend_data:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Note", backend_data.get("grade", "N/A"))
            with col2:
                st.metric("Précision", f"{backend_data.get('accuracy', 0)}%")
            with col3:
                st.metric("Feedback", backend_data.get("feedback", ""))
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Note", data["review"]["grade"])
            with col2:
                st.metric("Précision", "80%")

        st.markdown(
            f"""
        **Votre Réponse:**  
        `{data['user_input']}`  
        
        **Correction:**  
        `{data['correct_sentence']}`  
        
        **Feedback:**  
        {data['review']['feedback']}
        """
        )

        if st.button("↩️ Nouvel Exercice"):
            self.reset_exercise()
            st.session_state.app_state = AppState.PRACTICE
            st.rerun()

    def grade_submission(self, user_input: str, correct_sentence: str) -> Dict:
        user_clean = user_input.strip()
        correct_clean = correct_sentence.strip()

        if user_clean == correct_clean:
            return {"grade": "A+", "feedback": "Parfait ! Votre phrase est exacte."}
        elif self.is_almost_correct(user_clean, correct_clean):
            return {
                "grade": "A",
                "feedback": "Presque parfait ! Vérifiez les petits détails.",
            }
        else:
            return {
                "grade": "B",
                "feedback": "Quelques erreurs. Analysez la correction.",
            }

    def is_almost_correct(self, user: str, correct: str) -> bool:
        user_clean = user.strip().replace(" ", "").replace("。", ".")
        correct_clean = correct.strip().replace(" ", "").replace("。", ".")
        return ratio(user_clean, correct_clean) > 0.9

    def extract_text_from_pdf(self, uploaded_file):
        try:
            pdf_document = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page in pdf_document:
                text += page.get_text()
            pdf_document.close()
            return text.strip()
        except Exception as e:
            logger.error(f"Erreur PDF: {str(e)}")
            st.error(f"Erreur lors de l'extraction du texte: {str(e)}")
            return ""

    def render_ui(self):
        if st.session_state.app_state == AppState.SETUP:
            self.render_setup_state()
        elif st.session_state.app_state == AppState.PRACTICE:
            self.render_practice_state()
        elif st.session_state.app_state == AppState.REVIEW:
            self.render_review_state()
        else:
            st.error("État inconnu")
            st.session_state.app_state = AppState.SETUP
            self.render_setup_state()


def main():
    st.set_page_config(page_title="Pratique Japonaise", page_icon="🇯🇵")
    if "app" not in st.session_state:
        st.session_state.app = JapaneseLearningApp()
    st.session_state.app.render_ui()


if __name__ == "__main__":
    main()
