from flask import Flask, g
from flask_cors import CORS
from urllib.parse import urlparse

from lib.db import Db
import routes.words
import routes.groups
import routes.study_sessions
import routes.dashboard
import routes.study_activities


def get_allowed_origins(app):
    try:
        cursor = app.db.cursor()
        cursor.execute("SELECT url FROM study_activities")
        urls = cursor.fetchall()
        # Convert URLs to origins (e.g., https://example.com/app -> https://example.com)
        origins = set()
        for url in urls:
            try:
                parsed = urlparse(url["url"])
                origin = f"{parsed.scheme}://{parsed.netloc}"
                origins.add(origin)
            except Exception as e:
                print(f"Erreur lors de l'extraction de l'origine: {e}")
                continue
        return list(origins) if origins else ["*"]
    except Exception as e:
        print(f"Erreur lors de l'accès à la base de données: {e}")
        return ["*"]  # Fallback to allow all origins if there's an error


def create_app(test_config=None):
    app = Flask(__name__)

    if test_config is None:
        app.config.from_mapping(DATABASE="words.db")
    else:
        app.config.update(test_config)

    # Initialize database first since we need it for CORS configuration
    app.db = Db(database=app.config["DATABASE"])

    # Get allowed origins from study_activities table
    allowed_origins = get_allowed_origins(app)

    # In development, add localhost to allowed origins
    if app.debug:
        allowed_origins.extend(["http://localhost:8080", "http://127.0.0.1:8080"])

    # Configure CORS with combined origins
    CORS(
        app,
        resources={
            r"/*": {
                "origins": allowed_origins,
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
            }
        },
    )

    # Route pour la racine ("/")
    @app.route("/")
    def home():
        return "Bienvenue sur la page d'accueil!"

    # Close database connection
    @app.teardown_appcontext
    def close_db(exception):
        app.db.close()

    # load routes
    routes.words.load(app)
    routes.groups.load(app)
    routes.study_sessions.load(app)
    routes.dashboard.load(app)
    routes.study_activities.load(app)

    return app


# Création de l'application
app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
