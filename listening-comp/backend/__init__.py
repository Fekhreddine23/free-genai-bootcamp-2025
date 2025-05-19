import os
from dotenv import load_dotenv

# Charger les variables d'environnement depuis le fichier .env
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
load_dotenv(dotenv_path)