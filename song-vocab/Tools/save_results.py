from pathlib import Path  # AJOUT CRITIQUE
from typing import List, Dict, Any
import json
import logging


logger = logging.getLogger("song_vocab")


def save_results(
    song_id: str,
    lyrics: str,
    vocabulary: List[Dict[str, Any]],
    lyrics_path: Path,
    vocabulary_path: Path,
) -> str:
    """
    Save lyrics and vocabulary to their respective files.
    """
    try:
        # Début: Ajout des logs pour le débogage
        logger.info(f"Attempting to save results for song_id: {song_id}")
        logger.info(
            f"Lyrics: {lyrics[:200]}..."
        )  # Print a preview of lyrics to check if it's valid
        logger.info(
            f"Vocabulary: {vocabulary[:5]}..."
        )  # Print a preview of the vocabulary
        # Fin des logs ajoutés

        # Ensure the directories exist
        logger.debug(f"Checking directory: {lyrics_path}")
        lyrics_path.mkdir(parents=True, exist_ok=True)
        vocabulary_path.mkdir(parents=True, exist_ok=True)

        # Ensure the lyrics are properly encoded
        if isinstance(lyrics, bytes):
            lyrics = lyrics.decode("utf-8", errors="replace")
        elif isinstance(lyrics, str):
            # Normalize to UTF-8
            lyrics = lyrics.encode("utf-8", errors="replace").decode("utf-8")

        # Vérifiez le type de song_id
        if not isinstance(song_id, str):
            logger.error(f"Invalid song_id type: {type(song_id)}, expected string")
        song_id = str(song_id)  # Conversion de secours

        # Save lyrics with UTF-8 encoding
        lyrics_file = lyrics_path / f"{song_id}.txt"
        logger.debug(f"Attempting to save lyrics to: {lyrics_file}")
        with lyrics_file.open("w", encoding="utf-8") as f:
            f.write(lyrics)
        logger.info(f"Saved lyrics to {lyrics_file}")

        # Save vocabulary with UTF-8 encoding
        vocab_file = vocabulary_path / f"{song_id}.json"
        logger.debug(f"Attempting to save vocabulary to: {vocab_file}")
        with vocab_file.open("w", encoding="utf-8") as f:
            json.dump(vocabulary, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved vocabulary to {vocab_file}")

        return song_id

    except Exception as e:
        logger.error(f"Error saving results: {str(e)}")
        raise
