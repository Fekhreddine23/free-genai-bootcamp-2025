# groq_chat.py
import os
from openai import OpenAI
import streamlit as st
from typing import Optional, Dict, Any

# Initialise la clé API Groq depuis une variable d’environnement



class GroqChat:
    def __init__(self, model_id: str = MODEL_ID):
        """Initialize Groq chat client"""
        self.model_id = model_id
        self.client = OpenAI(
            api_key=os.getenv("GROQ_API_KEY"),
            base_url="https://api.groq.com/openai/v1"
        )
        if not os.getenv("GROQ_API_KEY"):
            raise ValueError("La clé API GROQ n'est pas définie. Utilisez la variable d'environnement GROQ_API_KEY.")

        if not openai.api_key:
            raise ValueError("La clé API GROQ n'est pas définie. Utilisez la variable d'environnement GROQ_API_KEY.")

    def generate_response(self, message: str, inference_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Génère une réponse avec le modèle Groq (via API OpenAI).
        :param message: Message utilisateur à envoyer au modèle.
        :param inference_config: Configuration optionnelle pour l'inférence (par exemple, température).
        :return: Réponse générée par le modèle ou None en cas d'erreur.
        """
        if inference_config is None:
            inference_config = {"temperature": 0.7}

        try:
            # Appel à l'API OpenAI pour générer une réponse
            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "user", "content": message}
                ],
                temperature=inference_config.get("temperature", 0.7)
            )
            # Retourne le contenu du premier choix
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            st.error(f"Erreur lors de la génération : {str(e)}")
            return None


# Initialisation du client GroqChat
chat = GroqChat()

st.title("Chat avec Groq")
user_input = st.text_input("Vous :", placeholder="Tapez votre message ici...")

if user_input:
    response = chat.generate_response(user_input)
    if response:
        st.write(f"**Bot**: {response}")
    else:
        st.error("Une erreur est survenue lors de la génération de la réponse.")