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
load_dotenv(dotenv_path="writing-pratice/.env")
import os

# Setup Custom Logging
logger = logging.getLogger('japanese_app')
logger.setLevel(logging.DEBUG)

if logger.hasHandlers():
    logger.handlers.clear()

fh = logging.FileHandler('app.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - JAPANESE_APP - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.propagate = False

# State Management
class AppState(Enum):
    SETUP = "setup"
    PRACTICE = "practice"
    REVIEW = "review"

class JapaneseLearningApp:
    def __init__(self):
        logger.debug("Initializing Japanese Learning App...")
        self.initialize_session_state()
        self.load_vocabulary()
        self.init_groq_client()
        
    def initialize_session_state(self):
        """Initialize or get session state variables"""
        defaults = {
            'app_state': AppState.SETUP,
            'current_sentence': None,
            'review_data': None,
            'vocabulary_loaded': False,
            'last_error': None
        }
        
        for key, value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    def init_groq_client(self):
        """Initialize Groq client with error handling"""
        try:
            api_key = (
                st.secrets.get("GROQ_API_KEY")
                if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets
                else os.getenv("GROQ_API_KEY")
            )
            self.groq_client = Groq(api_key=api_key)
            logger.info("Groq client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {e}")
            st.session_state.last_error = f"API initialization failed: {str(e)}"
            self.groq_client = None

    def load_vocabulary(self):
        """Fetch vocabulary from API"""
        try:
            group_id = st.query_params.get('group_id', 'default')
            
            if not group_id or group_id == 'default':
                st.warning("Using default vocabulary set")
                self.vocabulary = {
                    'words': [
                        {'kanji': '本', 'english': 'book', 'reading': 'ほん'},
                        {'kanji': '食べる', 'english': 'to eat', 'reading': 'たべる'},
                        {'kanji': '水', 'english': 'water', 'reading': 'みず'}
                    ]
                }
                st.session_state.vocabulary_loaded = True
                return
                
            url = f'http://localhost:5000/api/groups/{group_id}/words/raw'
            logger.debug(f"Fetching vocabulary from: {url}")
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            self.vocabulary = response.json()
            st.session_state.vocabulary_loaded = True
            logger.info(f"Loaded vocabulary with {len(self.vocabulary.get('words', []))} words")
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Vocabulary API error: {e}")
            st.session_state.last_error = f"Failed to load vocabulary: {str(e)}"
            self.vocabulary = None
        except Exception as e:
            logger.error(f"Unexpected error loading vocabulary: {e}")
            st.session_state.last_error = f"Unexpected error: {str(e)}"
            self.vocabulary = None

    def generate_sentence(self) -> Optional[Dict[str, str]]:
        """Generate a sentence using Groq API"""
        if not self.groq_client or not st.session_state.vocabulary_loaded:
            return None
            
        try:
            word = random.choice(self.vocabulary['words'])
            logger.debug(f"Selected word: {word['kanji']} ({word['english']})")
            
            prompt = f"""
            Generate a simple Japanese sentence using the word: {word['kanji']} ({word['reading']})
            Requirements:
            - JLPT N5 level grammar only
            - Use simple vocabulary (book, eat, drink, today, etc.)
            - Maximum 10 words
            
            Response format (JSON):
            {{
                "japanese": "Japanese sentence",
                "english": "English translation",
                "word_used": "{word['kanji']}",
                "word_meaning": "{word['english']}"
            }}
            """
            
            start_time = time.time()
            response = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150,
                response_format={"type": "json_object"}
            )
            
            processing_time = time.time() - start_time
            logger.debug(f"Sentence generated in {processing_time:.2f}s")
            
            content = response.choices[0].message.content
            try:
                result = json.loads(content)
                result['source_word'] = word
                return result
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON response: {content}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating sentence: {e}")
            st.session_state.last_error = f"Generation failed: {str(e)}"
            return None

    def grade_submission(self, image) -> Dict:
        """Process image submission and grade it"""
        # TODO: Implement actual MangaOCR integration
        mock_response = {
            "transcription": "今日は本を読みます",
            "translation": "Today I will read a book",
            "grade": "B",
            "feedback": "Good attempt! Minor grammar improvement needed.",
            "corrected": "今日は本を読みます"
        }
        
        if random.random() < 0.3:  # 30% chance to simulate variation
            mock_response.update({
                "grade": "A",
                "feedback": "Excellent! Perfect sentence construction."
            })
        
        return mock_response

    def render_setup_state(self):
        """Render the setup state UI"""
        st.title("🇯🇵 Japanese Writing Practice")
        st.markdown("### Practice writing simple Japanese sentences")
        
        if st.session_state.last_error:
            st.error(st.session_state.last_error)
            st.session_state.last_error = None
            
        if not st.session_state.vocabulary_loaded:
            st.warning("Vocabulary not loaded yet...")
            return