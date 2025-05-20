import streamlit as st
import sys
import os
import json
from datetime import datetime
import asyncio
import platform

# Configuration de compatibilité asyncio pour Windows
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Initialisation de l'event loop
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Ajout du chemin du backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.question_generator import QuestionGenerator
from backend.audio_generator import AudioGenerator

# Configuration de la page
st.set_page_config(
    page_title="JLPT Listening Practice",
    page_icon="🎧",
    layout="wide"
)

def inject_custom_css():
    """Injecte du CSS personnalisé pour améliorer l'interface"""
    st.markdown("""
    <style>
        .question-container {
            background-color: #f9f9f9;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .conversation-bubble {
            background-color: #e6f7ff;
            border-radius: 15px;
            padding: 10px 15px;
            margin: 5px 0;
            border-left: 3px solid #1890ff;
        }
        .correct-answer {
            background-color: #e6ffed;
            border-left: 3px solid #52c41a;
        }
        .incorrect-answer {
            background-color: #fff2f0;
            border-left: 3px solid #ff4d4f;
        }
        .stRadio > div {
            gap: 10px;
        }
        .stRadio label {
            border: 1px solid #d9d9d9;
            border-radius: 4px;
            padding: 8px 12px;
            margin: 2px 0;
        }
    </style>
    """, unsafe_allow_html=True)

def load_stored_questions():
    """Charge les questions sauvegardées depuis le fichier JSON"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend/data/stored_questions.json"
    )
    if os.path.exists(questions_file):
        with open(questions_file, 'r', encoding='utf-8') as f:
            try:
                stored_questions = json.load(f)
                return {
                    qid: qdata for qid, qdata in stored_questions.items()
                    if all(key in qdata for key in ['question', 'practice_type', 'topic'])
                }
            except json.JSONDecodeError:
                return {}
    return {}

def save_question(question, practice_type, topic, audio_file=None):
    """Sauvegarde une question dans le fichier JSON"""
    questions_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "backend/data/stored_questions.json"
    )
    stored_questions = load_stored_questions()
    question_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    question_data = {
        "question": question,
        "practice_type": practice_type,
        "topic": topic,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "audio_file": audio_file
    }
    
    os.makedirs(os.path.dirname(questions_file), exist_ok=True)
    with open(questions_file, 'w', encoding='utf-8') as f:
        json.dump({**stored_questions, question_id: question_data}, f, ensure_ascii=False, indent=2)
    
    return question_id

def normalize_question(question_data):
    """Normalise la structure de la question"""
    if not question_data:
        return None
        
    # Conversion des clés et gestion des formats différents
    normalized = {
        "introduction": question_data.get("introduction") or question_data.get("Introduction") or "",
        "conversation": [],
        "question": question_data.get("question") or question_data.get("Question") or "",
        "options": question_data.get("options") or question_data.get("Options") or [],
        "answer_index": question_data.get("answer_index") or question_data.get("AnswerIndex") or 0
    }
    
    # Normalisation de la conversation
    conversation = question_data.get("conversation") or question_data.get("Conversation") or []
    if isinstance(conversation, list):
        for i, item in enumerate(conversation):
            if isinstance(item, dict):
                speaker = item.get("speaker", f"Personne {i%2+1}")
                text = item.get("text", "")
            else:
                speaker = f"Personne {i%2+1}"
                text = str(item)
            
            normalized["conversation"].append({
                "speaker": speaker,
                "text": text
            })
    
    return normalized

def render_question(question):
    """
    Affiche une question normalisée avec un format clair et lisible
    Args:
        question (dict): Dictionnaire contenant les éléments de la question
    """
    if not question:
        st.warning("Aucune question à afficher")
        return

    # Injection CSS pour un affichage optimal
    st.markdown("""
    <style>
        .question-section {
            margin-bottom: 1.5rem;
        }
        .conversation-line {
            margin: 0.5rem 0;
            padding: 0.8rem;
            background-color: white;
            color: black;
            border-radius: 4px;
            border-left: 3px solid #4e8cff;
        }
        .speaker-label {
            font-weight: bold;
            color: #2c3e50;
        }
        .options-container {
            margin-top: 1rem;
        }
        .correct-feedback {
            color: #28a745;
            font-weight: bold;
        }
        .incorrect-feedback {
            color: #dc3545;
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        # Section Introduction
        with st.markdown("<div class='question-section'>", unsafe_allow_html=True):
            st.subheader("📘 Introduction")
            st.write(question.get("introduction", "Pas d'introduction disponible."))

        # Section Conversation - Version robuste
        with st.markdown("<div class='question-section'>", unsafe_allow_html=True):
            st.subheader("🗣️ Conversation")
            
            if not question.get("conversation"):
                st.warning("Aucun contenu de conversation disponible")
            else:
                for i, line in enumerate(question["conversation"]):
                    # Gestion des différents formats de ligne
                    speaker = "Personne A" if i % 2 == 0 else "Personne B"
                    text = ""
                    
                    if isinstance(line, dict):
                        speaker = line.get('speaker', speaker)
                        text = line.get('text', '')
                    elif isinstance(line, str):
                        text = line
                    
                    st.markdown(
                        f"""
                        <div class='conversation-line'>
                            <span class='speaker-label'>{speaker}:</span>
                            <span>{text}</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        # Section Question
        with st.markdown("<div class='question-section'>", unsafe_allow_html=True):
            st.subheader("❓ Question")
            st.write(question.get("question", "Pas de question disponible."))

        # Section Options de réponse
        options = question.get("options", [])
        if options:
            with st.markdown("<div class='options-container'>", unsafe_allow_html=True):
                selected = st.radio(
                    "Choisissez votre réponse:",
                    options,
                    index=None,
                    key=f"options_{hash(str(question))}"
                )

                if selected is not None:
                    answer_index = question.get("answer_index", 0)
                    is_correct = options.index(selected) == answer_index
                    
                    if is_correct:
                        st.markdown(
                            "<div class='correct-feedback'>✅ Correct! Bonne réponse.</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"""
                            <div class='incorrect-feedback'>
                                ❌ Incorrect. La réponse correcte est: 
                                <strong>{options[answer_index]}</strong>
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

def main():
    inject_custom_css()
    
    # Initialisation de l'état de session
    if 'question_generator' not in st.session_state:
        st.session_state.question_generator = QuestionGenerator()
    if 'audio_generator' not in st.session_state:
        st.session_state.audio_generator = AudioGenerator()
    if 'current_question' not in st.session_state:
        st.session_state.current_question = None
    if 'current_audio' not in st.session_state:
        st.session_state.current_audio = None
    
    st.title("JLPT Listening Practice")
    
    # Barre latérale avec historique
    with st.sidebar:
        st.header("Questions Sauvegardées")
        stored_questions = load_stored_questions()
        
        if stored_questions:
            for qid, qdata in stored_questions.items():
                btn_label = f"{qdata['practice_type']} - {qdata['topic']} ({qdata['created_at']})"
                if st.button(btn_label, key=qid):
                    st.session_state.current_question = qdata['question']
                    st.session_state.current_audio = qdata.get('audio_file')
                    st.rerun()
        else:
            st.info("Aucune question sauvegardée")
    
    # Contenu principal
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Sélection du type d'exercice
        practice_type = st.selectbox(
            "Type d'exercice",
            ["Dialogue Practice", "Phrase Matching"]
        )
        
        # Sélection du thème
        topics = {
            "Dialogue Practice": ["Daily Conversation", "Shopping", "Restaurant", "Travel"],
            "Phrase Matching": ["Announcements", "Instructions", "News"]
        }
        topic = st.selectbox("Thème", topics.get(practice_type, []))
        
        # Bouton de génération
        if st.button("Générer une nouvelle question"):
            with st.spinner("Génération en cours..."):
                try:
                    new_question = st.session_state.question_generator.generate_question(topic)
                    if new_question:
                        st.session_state.current_question = new_question
                        st.session_state.current_audio = None
                        save_question(new_question, practice_type, topic)
                        st.rerun()
                    else:
                        st.error("Échec de la génération de la question")
                except Exception as e:
                    st.error(f"Erreur: {str(e)}")
        
        # Affichage de la question actuelle
        if st.session_state.current_question:
            normalized_question = normalize_question(st.session_state.current_question)
            render_question(normalized_question)
        else:
            st.info("Cliquez sur 'Générer une nouvelle question' pour commencer")
    
    with col2:
        # Section Audio
        if st.session_state.current_question:
            st.subheader("Audio")
            
            if st.session_state.current_audio and os.path.exists(st.session_state.current_audio):
                st.audio(st.session_state.current_audio)
            else:
                if st.button("Générer Audio"):
                    with st.spinner("Génération audio..."):
                        try:
                            normalized_question = normalize_question(st.session_state.current_question)
                            parts = []
                            if normalized_question["introduction"]:
                                parts.append(("Announcer", normalized_question["introduction"]))
                            for line in normalized_question["conversation"]:
                                parts.append((line["speaker"], line["text"]))
                            if normalized_question["question"]:
                                parts.append(("Announcer", normalized_question["question"]))

                            audio_path = st.session_state.audio_generator.generate_audio({"parts": parts})
                            if audio_path and os.path.exists(audio_path):
                                st.session_state.current_audio = audio_path
                                save_question(
                                    st.session_state.current_question,
                                    practice_type,
                                    topic,
                                    audio_path
                                )
                                st.rerun()
                            else:
                                st.error("Échec de la génération audio")
                        except Exception as e:
                            st.error(f"Erreur audio: {str(e)}")

if __name__ == "__main__":
    main()