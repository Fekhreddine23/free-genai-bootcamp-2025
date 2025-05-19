from typing import Optional, Dict
from dotenv import load_dotenv
from openai import OpenAI
from pathlib import Path

import os

# Charger les variables d'environnement depuis le .env
load_dotenv(dotenv_path=Path("../.env"))

# Créer le client Groq avec le bon endpoint
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MODEL_ID = "llama3-8b-8192"
print("✅ Clé trouvée :", os.getenv("GROQ_API_KEY")[:6], "..." if os.getenv("GROQ_API_KEY") else "❌ Clé non trouvée")

class TranscriptStructurer:
    def __init__(self, model_id: str = MODEL_ID):
        self.model_id = model_id
        self.prompts = {
            1: """...""",  # Tu peux remettre ton prompt complet ici si tu veux
            2: """Extract questions from section 問題2 of this JLPT transcript where the answer can be determined solely from the conversation without needing visual aids.
            
            ONLY include questions that meet these criteria:
            - The answer can be determined purely from the spoken dialogue
            - No spatial/visual information is needed (like locations, layouts, or physical appearances)
            - No physical objects or visual choices need to be compared

            Format each question exactly like this:

            <question>
            Introduction:
            [the situation setup in japanese]
            
            Conversation:
            [the dialogue in japanese]
            
            Question:
            [the question being asked in japanese]
            </question>

            Rules:
            - Only extract questions from the 問題2 section
            - Only include questions where answers can be determined from dialogue alone
            - Ignore any practice examples (marked with 例)
            - Do not translate any Japanese text
            - Do not include any section descriptions or other text
            - Output questions one after another with no extra text between them
            """,
            3: """Extract all questions from section 問題3 of this JLPT transcript.
            Format each question exactly like this:

            <question>
            Situation:
            [the situation in japanese where a phrase is needed]
            
            Question:
            何と言いますか
            </question>

            Rules:
            - Only extract questions from the 問題3 section
            - Ignore any practice examples (marked with 例)
            - Do not translate any Japanese text
            - Do not include any section descriptions or other text
            - Output questions one after another with no extra text between them
            """
        }

    def _invoke_model(self, prompt: str, transcript: str) -> Optional[str]:
        """Appelle Groq avec LLaMA 3"""
        full_prompt = f"{prompt}\n\nHere's the transcript:\n{transcript}"
        try:
            response = client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": full_prompt}
                ],
                temperature=0,
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error invoking Groq: {str(e)}")
            return None

    def structure_transcript(self, transcript: str) -> Dict[int, str]:
        """Structure the transcript into three sections using separate prompts"""
        results = {}
        # Skipping section 1 for now
        for section_num in range(2, 4):
            result = self._invoke_model(self.prompts[section_num], transcript)
            if result:
                results[section_num] = result
        return results

    def save_questions(self, structured_sections: Dict[int, str], base_filename: str) -> bool:
        """Save each section to a separate file"""
        try:
            # Create questions directory if it doesn't exist
            os.makedirs(os.path.dirname(base_filename), exist_ok=True)
            
            # Save each section
            for section_num, content in structured_sections.items():
                filename = f"{os.path.splitext(base_filename)[0]}_section{section_num}.txt"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
            return True
        except Exception as e:
            print(f"Error saving questions: {str(e)}")
            return False

    def load_transcript(self, filename: str) -> Optional[str]:
        """Load transcript from a file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading transcript: {str(e)}")
            return None


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.abspath(__file__))  # Répertoire du script
    transcript_path = os.path.join(base_dir, "data/transcripts/sY7L5cfCWno.txt")

    if not os.path.exists(transcript_path):
        print(f"Error: Transcript file not found at {transcript_path}")
    else:
        with open(transcript_path, 'r') as f:
            transcript = f.read()
            print("Transcript loaded successfully")
            structurer = TranscriptStructurer()
            structured_sections = structurer.structure_transcript(transcript)
            structurer.save_questions(structured_sections, os.path.join(base_dir, "data/questions/sY7L5cfCWno.txt"))