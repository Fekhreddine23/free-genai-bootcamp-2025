import ollama
import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from functools import partial
import asyncio
import re

# Importer les outils spécifiés
from Tools.search_web_serp import SerpApiSearcher
from Tools.get_page_content import get_page_content
from Tools.extract_vocabulary import extract_vocabulary
from Tools.generate_song_id import generate_song_id
from Tools.save_results import save_results

logger = logging.getLogger("song_vocab")


def normalize_string(s: str) -> str:
    """Normaliser la chaîne pour l'utilisation dans un nom de fichier."""
    s = re.sub(r"[^\w\s]", "", s)  # Supprimer les caractères spéciaux
    return s.lower().strip().replace(" ", "_")


class SongLyricsAgent:
    """Agent optimisé pour TinyLlama et machines avec 16Go RAM"""

    def __init__(self, model: str = "tinyllama"):
        # Initialisation des chemins
        self.base_path = Path(__file__).parent
        self.lyrics_path = self.base_path / "outputs" / "lyrics"
        self.vocabulary_path = self.base_path / "outputs" / "vocabulary"

        # Création des répertoires de sortie
        self.lyrics_path.mkdir(parents=True, exist_ok=True)
        self.vocabulary_path.mkdir(parents=True, exist_ok=True)

        # Initialisation d'ollama et du modèle
        self.model = model
        self.client = ollama.Client()
        self.max_turns = 8  # Réduit pour éviter les boucles infinies

        # Configuration des outils avec validation
        self.tools = {
            "search_web": self.validate_tool(SerpApiSearcher().search_web, ["query"]),
            "get_page_content": self.validate_tool(get_page_content, ["url"]),
            "extract_vocabulary": self.validate_tool(extract_vocabulary, ["lyrics"]),
            "generate_song_id": self.validate_tool(
                generate_song_id, ["artist", "title"]
            ),
            "save_results": self.validate_tool(
                partial(
                    save_results,
                    lyrics_path=self.lyrics_path,
                    vocabulary_path=self.vocabulary_path,
                ),
                ["song_id", "lyrics", "vocabulary"],
            ),
        }

        # Vérification de la clé API (après initialisation des outils)
        try:
            api_key = (
                SerpApiSearcher().api_key
            )  # Supposant que SerpApiSearcher a un attribut api_key
            if api_key:
                logger.info(f"SerpAPI key loaded: {api_key[:4]}...")
            else:
                logger.warning("SerpAPI key not loaded")
        except Exception as e:
            logger.error(f"Error checking API key: {str(e)}")

    def validate_tool(self, tool, required_args):
        """Crée un wrapper pour valider les arguments avant l'exécution"""

        async def wrapper(**kwargs):
            missing = [arg for arg in required_args if arg not in kwargs]
            if missing:
                raise ValueError(f"Arguments manquants: {', '.join(missing)}")
            return (
                await tool(**kwargs)
                if asyncio.iscoroutinefunction(tool)
                else tool(**kwargs)
            )

        return wrapper

    async def execute_sequence(self, artist_name: str, song_title: str) -> str:
        """
        Exécute la séquence d'outils de manière déterministe sans dépendre du LLM
        pour les étapes critiques de la recherche et de l'extraction.
        """
        try:
            # 1. Recherche web
            logger.info("Executing search_web")
            search_results = await self.tools["search_web"](
                query=f"{artist_name} {song_title} 歌詞"
            )
            if not search_results or not search_results[0].get("url"):
                raise ValueError("Aucun résultat valide trouvé")

            first_url = search_results[0]["url"]

            # 2. Obtenir le contenu de la page
            logger.info("Executing get_page_content")
            page_result = await self.tools["get_page_content"](url=first_url)

            # Extraire le contenu textuel du résultat
            if isinstance(page_result, dict):
                # Essayer plusieurs clés possibles pour les lyrics
                lyrics_content = (
                    page_result.get("japanese_lyrics")
                    or page_result.get("romaji_lyrics")
                    or page_result.get("lyrics")
                    or ""
                )
                metadata = page_result.get("metadata", "")
            else:
                # Si c'est une string, l'utiliser directement
                lyrics_content = str(page_result)
                metadata = ""

            if not lyrics_content:
                raise ValueError("Aucun contenu de paroles trouvé")

            # 3. Extraire le vocabulaire
            logger.info("Executing extract_vocabulary")
            vocabulary = await self.tools["extract_vocabulary"](
                lyrics=lyrics_content[:5000]
            )  # Limite à 5000 caractères

            # 4. Générer l'ID de la chanson
            logger.info("Executing generate_song_id")
            song_id = await self.tools["generate_song_id"](
                artist=artist_name, title=song_title
            )

            # 5. Sauvegarder les résultats
            logger.info("Executing save_results")
            await self.tools["save_results"](
                song_id=song_id, lyrics=lyrics_content, vocabulary=vocabulary
            )

            return song_id
        except Exception as e:
            logger.error(f"Erreur dans la séquence: {str(e)}")
            return f"{normalize_string(artist_name)}_{normalize_string(song_title)}"

    async def process_request(self, artist_name: str, song_title: str) -> str:
        """Traitement de la requête avec approche hybride"""
        # Tentative d'exécution séquentielle directe (plus fiable)
        try:
            return await self.execute_sequence(artist_name, song_title)
        except Exception as e:
            logger.warning(f"Approche séquentielle échouée: {str(e)}, utilisant le LLM")
            return await self.process_with_llm(artist_name, song_title)

    async def process_with_llm(self, artist_name: str, song_title: str) -> str:
        """Traitement de la requête avec le LLM comme solution de repli"""
        artist_norm = normalize_string(artist_name)
        title_norm = normalize_string(song_title)
        logger.info(f"Utilisation du LLM pour: {artist_name} - {song_title}")

        # Préparation de la conversation
        conversation = [
            {
                "role": "system",
                "content": (
                    "RÈGLES ABSOLUES:\n"
                    "1. Répondez UNIQUEMENT avec: Tool: NOM_DE_L_OUTIL(args) ou FINISHED ID\n"
                    "2. Pas de texte supplémentaire\n"
                    "3. SÉQUENCE OBLIGATOIRE:\n"
                    "   a. search_web(query='ARTISTE TITRE 歌詞')\n"
                    "   b. get_page_content(url=RESULTAT[0].url)\n"
                    "   c. extract_vocabulary(lyrics=CONTENU_PAGE)\n"
                    "   d. generate_song_id(artist='ARTISTE', title='TITRE')\n"
                    "   e. save_results(song_id=ID, lyrics=CONTENU, vocabulary=VOCAB)\n"
                    "EXEMPLE:\n"
                    "Tool: search_web(query='YOASOBI Idol 歌詞')\n"
                    "Tool: get_page_content(url='https://utaten.com/lyric/yoasobi/idol')\n"
                    "Tool: extract_vocabulary(lyrics='...')\n"
                    "Tool: generate_song_id(artist='YOASOBI', title='Idol')\n"
                    "Tool: save_results(song_id='yoasobi_idol', lyrics='...', vocabulary='...')\n"
                    "FINISHED yoasobi_idol"
                ),
            },
            {
                "role": "user",
                "content": f"Trouver paroles pour: {artist_name} {song_title}",
            },
        ]

        for turn in range(self.max_turns):
            try:
                # Appel LLM
                response = self.client.chat(
                    model=self.model,
                    messages=conversation,
                    options={"num_ctx": 1024},
                )
                llm_content = response["message"]["content"]
                logger.info(f"LLM Turn {turn+1}:\n{llm_content}")

                # Vérifier la fin du processus
                if "FINISHED" in llm_content:
                    if match := re.search(r"FINISHED\s+(\w+)", llm_content):
                        return match.group(1)
                    return f"{artist_norm}_{title_norm}"

                # Exécuter l'outil
                if tool_call := self.parse_llm_action(llm_content):
                    tool_name, args = tool_call
                    result = await self.execute_tool(tool_name, args)

                    # Formatage du résultat pour la conversation
                    result_str = str(result)
                    if len(result_str) > 300:
                        result_str = result_str[:300] + "..."

                    conversation.append(
                        {
                            "role": "system",
                            "content": f"{tool_name} result: {result_str}",
                        }
                    )
                    conversation.append({"role": "assistant", "content": llm_content})
                else:
                    # Réponse d'erreur formatée
                    conversation.append(
                        {
                            "role": "assistant",
                            "content": "Erreur dans la réponse LLM.",
                        }
                    )

            except Exception as e:
                logger.error(f"Erreur lors de l'appel LLM: {str(e)}")
                break

        return f"{artist_norm}_{title_norm}"

    async def execute_tool(self, tool_name: str, args: List[str]) -> Any:
        """Exécution d'un outil à partir du nom et des arguments."""
        try:
            tool = self.tools.get(tool_name)
            if not tool:
                raise ValueError(f"Outil {tool_name} non trouvé")
            return await tool(*args)
        except Exception as e:
            logger.error(f"Erreur d'exécution de l'outil {tool_name}: {str(e)}")
            return None
