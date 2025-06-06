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
from manga_ocr import MangaOcr
from streamlit_drawable_canvas import st_canvas
from groq import Groq
import os

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
        """Initialisation de l'application"""
        if "app_initialized" not in st.session_state:
            logger.debug("Initialisation de l'application...")
            self.load_prompt_yaml()  # Charger le YAML ici
            self.initialize_session_state()
            self.load_vocabulary()
            self.mocr = MangaOcr()

            # Extraire la clé API
            api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")

            # Assurez-vous que la clé API est disponible
            if api_key:
                logger.debug(f"Configuration Groq: {api_key[:5]}...")
            else:
                logger.warning(
                    "Aucune clé API Groq trouvée. Vérifiez la configuration."
                )

            # Créer l'instance de Groq avec la clé API
            self.groq_client = Groq(api_key=api_key)

            self.pre_generated_sentences = self.pre_generate_sentences()
            st.session_state.app_initialized = True
            logger.debug("Application initialisée")

    def load_prompt_yaml(self):
        """Charge le fichier YAML pour la génération de phrases"""
        try:
            # Charger le fichier YAML depuis son chemin absolu
            yaml_file_path = "/mnt/c/Users/far23/Bureau/free-genai-bootcamp-2025-main/writing-pratice/prompt.yaml"
            with open(yaml_file_path, "r") as file:
                self.prompt_config = yaml.safe_load(file)
                logger.info("Fichier prompt.yaml chargé avec succès.")
                # Afficher le contenu du YAML pour débogage
                logger.debug(f"Contenu du YAML: {self.prompt_config}")

                # Vérification de la présence de la clé 'sentence_generation'
                if "sentence_generation" not in self.prompt_config:
                    logger.error(
                        "Clé 'sentence_generation' manquante dans le fichier YAML."
                    )
                    raise KeyError(
                        "Clé 'sentence_generation' manquante dans le fichier YAML."
                    )
        except Exception as e:
            logger.error(f"Erreur lors du chargement du fichier prompt.yaml: {str(e)}")
            self.prompt_config = {}

    def initialize_session_state(self):
        """Initialise l'état de la session"""
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
        """Charge le vocabulaire avec plus d'exemples"""
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
        """Validation basique de la sémantique"""
        if not response.get("japanese") or not response.get("hint"):
            return False

        hint_lower = response["hint"].lower()
        word_french_lower = word["french"].lower()

        # Vérification simple que le mot français apparaît dans l'indice
        return word_french_lower in hint_lower

    def generate_sentence_with_groq(self, word: dict, attempts=3) -> dict:
        """Génère une phrase avec Groq avec gestion des réessais"""
        if attempts <= 0:
            logger.warning(f"Maximum d'essais atteint pour {word['kanji']}")
            return self.generate_fallback_sentence(word)

        try:
            # Utilisation du prompt tel qu'il est dans votre YAML
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

            # La réponse est juste la phrase en japonais
            japanese_sentence = chat_completion.choices[0].message.content.strip()

            # Génération de la traduction
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
                temperature=0.2,  # Plus bas pour des traductions précises
                max_tokens=150,
            )

            hint = translation_completion.choices[0].message.content.strip()

            # Création de la structure de réponse attendue
            return {
                "japanese": japanese_sentence,
                "hint": hint,
                "word_used": word["kanji"],
                "word_reading": word["reading"],
                "word_meaning": word["french"],
                "grammar_points": [
                    "auto-généré"
                ],  # Vous pourriez ajouter une analyse ici
                "difficulty": word["level"],
                "context": random.choice(word["contexts"]),
            }

        except Exception as e:
            logger.error(f"Erreur Groq: {str(e)}")
            return self.generate_fallback_sentence(word)

    def pre_generate_sentences(self):
        """Pré-génère 3 phrases alternatives pour chaque mot"""
        sentences = {}
        for word in st.session_state.vocabulary["words"]:
            alternatives = []
            for _ in range(3):  # 3 phrases alternatives
                sentence = self.generate_sentence_with_groq(
                    word
                ) or self.generate_fallback_sentence(word)
                alternatives.append(sentence)
            sentences[word["kanji"]] = alternatives
        return sentences

    def generate_fallback_sentence(self, word: dict) -> dict:
        """Génère des phrases de secours variées"""
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
            "voyage": [
                ("{}の計画", "Plan de [activité]"),
                ("{}が楽しい", "[Activité] est amusante"),
                ("{}に行く", "Aller en [quelque part]"),
            ],
            "étudier": [
                ("{}を学ぶ", "J'apprends [quelque chose]"),
                ("{}の先生", "Professeur de [quelque chose]"),
                ("{}が難しい", "[Quelque chose] est difficile"),
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
        """Génère une phrase aléatoire ou utilise le cache"""
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
        """Affiche l'écran d'accueil"""
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

        test_word = st.session_state.vocabulary["words"][0]
        test_result = self.generate_sentence_with_groq(test_word)
        st.json(test_result)

        if st.button("Commencer la Pratique"):
            st.session_state.app_state = AppState.PRACTICE
            st.session_state.current_sentence = self.generate_sentence()
            st.session_state.exercise_started = True
            st.rerun()

    def render_practice_state(self):
        """Affiche l'interface de pratique"""
        if (
            "current_sentence" not in st.session_state
            or st.session_state.current_sentence is None
        ):
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

        # Zone de téléchargement de fichier
        st.subheader("Soumettre votre réponse en téléchargeant un fichier")
        uploaded_file = st.file_uploader(
            "Téléchargez votre fichier de réponse", type=["jpg", "png", "pdf", "txt"]
        )

        if uploaded_file is not None:
            st.write(f"Fichier téléchargé: {uploaded_file.name}")

            # Traitement du fichier selon son type
            if uploaded_file.type in ["image/jpeg", "image/png"]:
                # Si le fichier est une image, utilisez Tesseract pour l'OCR
                image = Image.open(uploaded_file)
                st.image(image, caption="Image téléchargée", use_column_width=True)

                try:
                    recognized_text = self.mocr(image)
                    st.session_state.recognized_text = recognized_text
                    st.success(f"Reconnaissance: {recognized_text}")
                except Exception as e:
                    st.error(f"Erreur lors de la reconnaissance: {str(e)}")

            elif uploaded_file.type == "application/pdf":
                # Si le fichier est un PDF, utilisez PyMuPDF ou PyPDF2 pour extraire le texte
                text = self.extract_text_from_pdf(uploaded_file)
                st.text_area("Texte extrait du PDF", value=text, height=100)

            elif uploaded_file.type == "text/plain":
                # Si le fichier est un fichier texte, lisez directement le contenu
                text = uploaded_file.getvalue().decode("utf-8")
                st.text_area("Texte téléchargé", value=text, height=100)

        # Zone de dessin pour permettre à l'utilisateur de dessiner sa réponse
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

        # Entrée texte alternative si l'utilisateur préfère écrire directement
        user_input = st.text_area(
            "Ou écrivez directement:",
            value=getattr(st.session_state, "recognized_text", ""),
            height=100,
            key="user_input",
        )

        # Boutons pour vérifier la réponse
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

    def check_answer(self, user_input: str):
        """Évalue la réponse de l'utilisateur"""
        if not user_input.strip():
            st.warning("Veuillez écrire ou dessiner votre réponse")
            return

        review = self.grade_submission(
            user_input, st.session_state.current_sentence["japanese"]
        )
        st.session_state.review_data = {
            "user_input": user_input,
            "correct_sentence": st.session_state.current_sentence["japanese"],
            "review": review,
            "drawing": st.session_state.drawing_data,
        }
        st.session_state.app_state = AppState.REVIEW
        st.rerun()

    def reset_exercise(self):
        """Réinitialise l'exercice avec un nouveau mot"""
        st.session_state.current_sentence = self.generate_sentence()
        st.session_state.drawing_data = None
        st.session_state.recognized_text = ""
        st.rerun()

    def show_alternative(self):
        """Affiche une phrase alternative pour le même mot"""
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
        """Affiche les résultats"""
        if not st.session_state.review_data:
            st.error("Aucune donnée disponible")
            st.session_state.app_state = AppState.SETUP
            st.rerun()
            return

        data = st.session_state.review_data
        st.subheader("Résultats")

        if data.get("drawing"):
            buf = io.BytesIO()
            data["drawing"].save(buf, format="PNG")
            st.image(buf.getvalue(), caption="Votre écriture", width=200)

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
        """Évalue la réponse avec plus de nuances"""
        user_clean = user_input.strip()
        correct_clean = correct_sentence.strip()

        if user_clean == correct_clean:
            return {
                "grade": "A+",
                "feedback": "Parfait ! Votre phrase est exacte.",
            }
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
        """Détecte les réponses presque correctes"""
        return (
            user.replace(" ", "") == correct.replace(" ", "")
            or user.replace("。", ".") == correct.replace("。", ".")
            or user in correct
            or correct in user
        )

    def render_ui(self):
        """Gère l'affichage principal"""
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


# Point d'entrée de l'application
def main():
    st.set_page_config(page_title="Pratique Japonaise", page_icon="🇯🇵")
    if "app" not in st.session_state:
        st.session_state.app = JapaneseLearningApp()
    st.session_state.app.render_ui()


if __name__ == "__main__":
    main()
