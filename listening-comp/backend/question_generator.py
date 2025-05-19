import os
from openai import OpenAI
import json
import logging
from typing import Optional, Dict

logging.basicConfig(level=logging.ERROR)

class QuestionGenerator:
    def __init__(self):
        """Initialise l'API Groq avec la clé API et le modèle"""
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        self.model = "llama3-8b-8192"

    def _invoke_groq(self, prompt: str) -> Optional[str]:
        """Envoie un prompt à l'API Groq et retourne la réponse brute"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that generates JSON output."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error invoking Groq: {str(e)}")
            return None

    def _parse_question(self, response: str) -> Optional[Dict]:
        """Analyse la réponse brute de l'API et retourne un dictionnaire"""
        if not response:
            logging.error("Empty response received")
            return None

        try:
            # Nettoyer la réponse si nécessaire
            response = response.strip()
            if not response.startswith('{'):
                response = '{' + response.split('{', 1)[-1]
            if not response.endswith('}'):
                response = response.split('}', 1)[0] + '}'

            question = json.loads(response)
            return {
                "Introduction": question.get("introduction", ""),
                "Conversation": question.get("conversation", []),
                "Question": question.get("question", ""),
                "Options": question.get("options", []),
                "AnswerIndex": question.get("answer_index", None)
            }
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing question. Response was: {response}")
            return None
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            return None

    def _create_prompt(self, topic: str) -> str:
        """Crée un prompt optimisé pour générer des questions JLPT avec un JSON fiable"""
        return f"""# Instruction
Générez une question de compréhension orale pour le JLPT N4/N3 sur le thème : {topic}

## Exigences strictes
1. Format de sortie : UNIQUEMENT un JSON valide
2. Langue : Exclusivement en japonais
3. Structure obligatoire :
   - Introduction contextuelle (1 phrase)
   - Dialogue (3 répliques minimum)
   - Question directe
   - 4 options de réponse numérotées
   - Index de la bonne réponse (0-3)

## Format JSON exigé :
```json
{{
  "introduction": "導入文（1文で）",
  "conversation": [
    "会話1",
    "会話2", 
    "会話3"
  ],
  "question": "質問文？",
  "options": [
    "回答1",
    "回答2",
    "回答3",
    "回答4"
  ],
  "answer_index": 0
}}
"""
    
    def generate_question(self, topic: str) -> Optional[Dict]:
        """Génère une nouvelle question sur un sujet donné"""
        prompt = self._create_prompt(topic)
        response = self._invoke_groq(prompt)
        if not response:
            logging.error("No response from API")
            return None
        return self._parse_question(response)

    def generate_similar_question(self, section_num: int, topic: str) -> Optional[Dict]:
        """Génère une nouvelle question similaire sur un sujet donné"""
        return self.generate_question(topic)