from pathlib import Path  # Ajoutez cette ligne
import logging
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import json
from agent import SongLyricsAgent
from Tools.search_web_serp import SerpApiSearcher  # Corrected class name


import re

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("song_vocab")
logger.setLevel(logging.DEBUG)

app = FastAPI()


@app.get("/")
async def root():
    return {
        "message": "Welcome to Song Vocab API",
        "endpoints": {
            "/api/agent": "POST - Find lyrics and generate vocabulary (format: 'Find lyrics for [title] by [artist]')"
        },
    }


class LyricsRequest(BaseModel):
    message_request: str


def extract_song_info(message: str) -> tuple[str, str]:
    # Pattern pour extraire le titre et l'artiste
    pattern = r"Find lyrics for (.+?)\s+(.+?)( from|$)"
    match = re.search(pattern, message, re.IGNORECASE)
    if match:
        artist_name = match.group(1).strip()
        song_title = match.group(2).strip()
        logger.debug(f"Pattern matched: artist='{artist_name}', title='{song_title}'")
        return artist_name, song_title

    # Pattern pour "Find lyrics for [title] by [artist]"
    pattern2 = r"Find lyrics for (.+?) by (.+?)( from|$)"
    match2 = re.search(pattern2, message, re.IGNORECASE)
    if match2:
        artist_name = match2.group(2).strip()
        song_title = match2.group(1).strip()
        logger.debug(f"Pattern2 matched: artist='{artist_name}', title='{song_title}'")
        return artist_name, song_title

    logger.debug(f"No pattern matched for: {message}")
    return "", ""


@app.post("/api/agent")
async def get_lyrics(request: LyricsRequest) -> JSONResponse:
    try:
        logger.info(f"Received request: {request.message_request}")

        # Extraire l'artiste et le titre
        artist_name, song_title = extract_song_info(request.message_request)
        logger.info(f"Extracted: artist='{artist_name}', title='{song_title}'")

        if not song_title:
            raise HTTPException(status_code=400, detail="Song title not found")

        # Initialize agent
        agent = SongLyricsAgent()

        # Process the request
        song_id = await agent.process_request(artist_name, song_title)
        logger.info(f"Got song_id: {song_id}")

        # Corrected song_id handling
        if isinstance(song_id, dict):
            clean_song_id = song_id.get("song_id", "").replace("_FINISHED", "")
        else:
            clean_song_id = song_id.replace("_FINISHED", "")

        # Retrieve stored files
        lyrics_file = Path(agent.lyrics_path) / f"{clean_song_id}.txt"
        vocab_file = Path(agent.vocabulary_path) / f"{clean_song_id}.json"

        if not lyrics_file.exists():
            lyrics = "Lyrics not found"
        else:
            lyrics = lyrics_file.read_text()

        if not vocab_file.exists():
            vocabulary = [
                {"word": "Error", "reading": "えらー", "meaning": "File not found"}
            ]
        else:
            vocabulary = json.loads(vocab_file.read_text())

        return JSONResponse(
            content={
                "song_id": clean_song_id,
                "lyrics": lyrics,
                "vocabulary": vocabulary,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.on_event("startup")
async def startup_event():
    logger.info("Testing lyrics search on startup...")
    test_message = "Find lyrics for Gurenge by LiSA from Demon Slayer"
    try:
        artist_name, song_title = extract_song_info(test_message)
        logger.info(f"Test extraction: artist='{artist_name}', title='{song_title}'")

        if not song_title:
            logger.error("Failed to extract song title from test message")
            return

        agent = SongLyricsAgent()
        result = await agent.execute_sequence(artist_name, song_title)
        logger.info(f"Test search completed successfully: {result}")

    except Exception as e:
        logger.error(f"Error in startup: {str(e)}")
        raise


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
