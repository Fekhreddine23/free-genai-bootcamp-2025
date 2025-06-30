# Utilise une image Python officielle plus légère
FROM python:3.9-slim-bullseye

# Définit le répertoire de travail dans le conteneur
WORKDIR /app

# Définit les variables d'environnement
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Installe d'abord les dépendances système nécessaires
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc build-essential && \
    rm -rf /var/lib/apt/lists/*

# Copie uniquement le fichier de dépendances d'abord (optimisation de cache Docker)
COPY requirements.txt .

# Installe les dépendances Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copie le reste de l'application
COPY . .

# Expose le port 8000
EXPOSE 8000

# Commande à exécuter au démarrage du conteneur
CMD ["python", "app.py"]