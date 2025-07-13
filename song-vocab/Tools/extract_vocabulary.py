import logging
from typing import List, Dict
import ollama
import instructor
from pathlib import Path
import asyncio
import re

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


async def extract_vocabulary(lyrics: str) -> List[Dict]:
    """
    Extract Japanese vocabulary from lyrics text using LLM
    """
    logger.info("Starting vocabulary extraction")

    # Validate input
    if not isinstance(lyrics, str) or not lyrics.strip():
        logger.error("Invalid or empty lyrics provided")
        return []

    try:
        # Load prompt template
        prompt_path = Path(__file__).parent.parent / "prompts" / "Extract_Vocabulary.md"
        if not prompt_path.exists():
            logger.error(f"Prompt file not found: {prompt_path}")
            return []

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Limit text to avoid context overflow
        MAX_TEXT_LENGTH = 6000
        truncated_text = lyrics[:MAX_TEXT_LENGTH]

        # Prepare the prompt with clear instructions
        prompt = (
            f"{prompt_template}\n\n"
            "Text to analyze:\n"
            "===== BEGIN TEXT =====\n"
            f"{truncated_text}\n"
            "===== END TEXT =====\n\n"
            "Instructions:\n"
            "- List ONLY vocabulary items in format: KANJI - ROMAJI - FRENCH\n"
            "- Example: 言葉 - kotoba - mot\n"
            "- DO NOT include any explanations or additional text\n"
        )

        # New: Manual parsing fallback
        def parse_fallback_response(text: str) -> List[Dict]:
            """Parse fallback for LLM responses that don't match the expected format"""
            items = []
            # Pattern to detect: kanji - romaji - french
            pattern = r"([\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]+)\s*-\s*([a-zA-Z\s]+)\s*-\s*([^\n]+)"
            for match in re.finditer(pattern, text):
                kanji, romaji, french = match.groups()
                items.append(
                    {
                        "kanji": kanji.strip(),
                        "romaji": romaji.strip(),
                        "french": french.strip(),
                        "parts": [],  # Simplified parts
                    }
                )
            return items

        # Try multiple models for better compatibility
        models_to_try = ["llama3", "mistral", "gemma:7b"]
        all_items = []

        for model_name in models_to_try:
            try:
                logger.info(f"Trying extraction with model: {model_name}")
                client = ollama.AsyncClient()
                response = await client.chat(
                    model=model_name,
                    messages=[{"role": "user", "content": prompt}],
                    options={"temperature": 0.1, "num_ctx": 8192},
                )

                llm_output = response["message"]["content"]
                logger.debug(f"LLM output: {llm_output[:200]}...")

                # Try to parse the response
                parsed_items = parse_fallback_response(llm_output)
                if parsed_items:
                    logger.info(
                        f"Extracted {len(parsed_items)} items with {model_name}"
                    )
                    all_items.extend(parsed_items)
                    break
                else:
                    logger.warning(
                        f"No items extracted with {model_name}, trying next model"
                    )

            except Exception as e:
                logger.error(f"Error with model {model_name}: {str(e)}")

        # If we have items, remove duplicates
        if all_items:
            seen = set()
            unique_items = []
            for item in all_items:
                identifier = (item["kanji"], item["romaji"], item["french"])
                if identifier not in seen:
                    seen.add(identifier)
                    unique_items.append(item)
            logger.info(f"Returning {len(unique_items)} unique vocabulary items")
            return unique_items
        else:
            logger.error("All extraction attempts failed, returning empty list")
            return []

    except Exception as e:
        logger.exception(f"Vocabulary extraction failed: {str(e)}")
        return []
