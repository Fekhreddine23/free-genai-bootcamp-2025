import re
import unicodedata
from typing import Dict

def generate_song_id(artist: str, title: str) -> str:
    """
    Generate a URL-safe song ID from artist and title.
    
    Args:
        artist (str): The artist name
        title (str): The song title
        
    Returns:
        return f"{normalize_string(artist)}-{normalize_string(title)}"
    """
    def clean_string(s: str) -> str:
        if not s:
            return "unknown"
            
        # Normalisation des caractères Unicode
        s = unicodedata.normalize('NFKD', s)
        # Suppression des caractères spéciaux
        s = re.sub(r'[^\w\s-]', '', s.lower())
        # Remplacement des espaces/tirets multiples
        s = re.sub(r'[\s-]+', '-', s)
        # Suppression des tirets en début/fin
        s = s.strip('-')
        # Limite de longueur pour les URLs
        s = s[:100]
        
        return s or "unknown"  # Double sécurité
    
    artist_clean = clean_string(artist)
    title_clean = clean_string(title)
    
    return f"{artist_clean}-{title_clean}"  # Retourne "yoasobi-idol"
