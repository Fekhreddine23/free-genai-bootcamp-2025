import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, Optional, Tuple
import re
import logging
import unicodedata

# Configure logging
logger = logging.getLogger(__name__)

# Common lyric container selectors (prioritized)
LYRIC_SELECTORS = [
    {"name": "lyrics", "classes": ["lyrics", "lyric", "lyric-body"]},
    {"name": "songtext", "classes": ["songtext", "song-text"]},
    {"name": "romaji", "classes": ["romaji", "romaaji"]},
    {"name": "japanese", "classes": ["japanese", "kanji", "original"]},
    {"name": "content", "classes": ["content", "text", "main", "entry-content"]},
]


async def get_page_content(url: str) -> Dict[str, Optional[str]]:
    """
    Extract lyrics content from a webpage with improved accuracy

    Args:
        url (str): URL of the webpage

    Returns:
        Dict[str, Optional[str]]: Contains japanese_lyrics, romaji_lyrics, metadata
    """
    logger.info(f"Fetching content from URL: {url}")
    try:
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=20),  # Augmenter le timeout
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            },
        ) as session:
            logger.debug("Making HTTP request...")
            async with session.get(url) as response:
                # Handle HTTP errors
                if response.status != 200:
                    error_msg = f"HTTP Error {response.status}"
                    logger.error(error_msg)
                    return error_response(error_msg)

                # Détecter l'encodage
                content_type = response.headers.get("Content-Type", "")
                charset_match = re.search(r"charset=([\w-]+)", content_type)
                encoding = charset_match.group(1) if charset_match else None

                # Essayer plusieurs encodages si nécessaire
                encodings_to_try = (
                    [encoding, "utf-8", "shift_jis", "euc-jp"]
                    if encoding
                    else ["utf-8", "shift_jis", "euc-jp"]
                )
                html = None

                for enc in encodings_to_try:
                    if not enc:
                        continue
                    try:
                        html = await response.text(encoding=enc, errors="strict")
                        break
                    except UnicodeDecodeError:
                        logger.debug(f"Encoding {enc} failed, trying next")

                if html is None:
                    # Dernier recours
                    html = await response.text(errors="replace")

                soup = BeautifulSoup(html, "html.parser")

                # Extraire les paroles
                japanese, romaji = extract_lyrics(soup)

                # Ajouter l'URL aux métadonnées
                metadata = f"From: {url}"
                if soup.title and soup.title.string:
                    metadata = f"{soup.title.string} | {metadata}"

                return {
                    "japanese_lyrics": japanese,
                    "romaji_lyrics": romaji,
                    "metadata": metadata,
                }

    except Exception as e:
        error_msg = f"Error fetching URL: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return error_response(error_msg)


def extract_lyrics(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract Japanese and Romaji lyrics using prioritized strategies

    Returns:
        Tuple: (japanese_text, romaji_text)
    """
    # Strategy 1: Targeted class detection
    for selector in LYRIC_SELECTORS:
        for class_name in selector["classes"]:
            elements = soup.find_all(class_=class_name)
            if not elements:
                continue

            logger.debug(f"Found {len(elements)} elements with class: {class_name}")
            japanese, romaji = process_elements(elements)
            if japanese or romaji:
                return japanese, romaji

    # Strategy 2: Structural analysis
    japanese, romaji = find_lyrics_by_structure(soup)
    if japanese or romaji:
        return japanese, romaji

    # Strategy 3: Content-based scanning
    return find_lyrics_by_content(soup)


def process_elements(elements) -> Tuple[Optional[str], Optional[str]]:
    """Process found elements to identify lyrics"""
    japanese_text = None
    romaji_text = None

    for element in elements:
        text = element.get_text()
        if not text:
            continue

        cleaned = clean_text(text)
        if len(cleaned) < 50:  # Minimum lyric length
            continue

        # Classify content
        jp_ratio = japanese_ratio(cleaned)
        rm_ratio = romaji_ratio(cleaned)

        logger.debug(
            f"Content analysis - JP: {jp_ratio:.2f}, RM: {rm_ratio:.2f}, Len: {len(cleaned)}"
        )

        # Prioritize based on language dominance
        if not japanese_text and jp_ratio > 0.4:
            japanese_text = cleaned
        if not romaji_text and rm_ratio > 0.6:
            romaji_text = cleaned

        # Early termination if both found
        if japanese_text and romaji_text:
            break

    return japanese_text, romaji_text


def find_lyrics_by_structure(
    soup: BeautifulSoup,
) -> Tuple[Optional[str], Optional[str]]:
    """Find lyrics by analyzing page structure"""
    # Look for common containers
    containers = soup.select(
        "div#lyrics, div#lyric, div#romaji, div#japanese,"
        "section.lyrics, article.lyrics, pre.lyrics"
    )

    if containers:
        return process_elements(containers)

    # Look for adjacent headings
    for heading in soup.find_all(["h1", "h2", "h3", "h4"]):
        if "lyrics" in heading.get_text().lower():
            container = find_next_container(heading)
            if container:
                return process_elements([container])

    return None, None


def find_lyrics_by_content(soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
    """Fallback: Scan all text blocks for lyric-like content"""
    candidates = []
    for element in soup.find_all(["div", "p", "section", "article", "pre"]):
        text = element.get_text()
        if not text:
            continue

        cleaned = clean_text(text)
        if len(cleaned) < 100:  # Minimum length for lyrics
            continue

        # Score by language characteristics
        jp_score = japanese_ratio(cleaned)
        rm_score = romaji_ratio(cleaned)
        line_count = len(cleaned.splitlines())

        # Lyrics typically have multiple lines
        if line_count < 3:
            continue

        candidates.append(
            {
                "text": cleaned,
                "score": max(jp_score, rm_score),
                "type": "japanese" if jp_score > rm_score else "romaji",
            }
        )

    # Select best candidates
    japanese = next(
        (
            c["text"]
            for c in sorted(
                [c for c in candidates if c["type"] == "japanese"],
                key=lambda x: x["score"],
                reverse=True,
            )[:1]
        ),
        None,
    )

    romaji = next(
        (
            c["text"]
            for c in sorted(
                [c for c in candidates if c["type"] == "romaji"],
                key=lambda x: x["score"],
                reverse=True,
            )[:1]
        ),
        None,
    )

    return japanese, romaji


def clean_text(text: str) -> str:
    """
    Clean text while preserving lyric structure
    - Normalizes whitespace
    - Preserves line breaks
    - Removes unwanted characters
    """
    # Normalize Unicode
    text = unicodedata.normalize("NFKC", text)

    # Preserve line breaks while cleaning
    lines = []
    for line in text.splitlines():
        # Remove unwanted characters
        line = re.sub(r'[^\w\s.,!?\'"\-\[\]()\u3000-\u30FF\u4E00-\u9FFF]', "", line)
        # Normalize whitespace
        line = re.sub(r"\s+", " ", line).strip()
        if line:
            lines.append(line)

    # Rebuild with cleaned lines
    return "\n".join(lines)


def japanese_ratio(text: str) -> float:
    """Calculate ratio of Japanese characters in text"""
    jp_chars = re.findall(
        r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\uFF65-\uFF9F]", text
    )
    total_chars = max(len(re.sub(r"\s", "", text)), 1)  # Ignore whitespace
    return len(jp_chars) / total_chars


def romaji_ratio(text: str) -> float:
    """Calculate ratio of Romaji-friendly characters"""
    # Count Latin characters (excluding digits and punctuation)
    roma_chars = re.findall(r"[a-zA-Z]", text)
    total_chars = max(len(re.sub(r"[^a-zA-Z]", "", text)), 1)
    return len(roma_chars) / total_chars


def find_next_container(element) -> Optional[BeautifulSoup]:
    """Find next structural container after heading"""
    for sibling in element.next_siblings:
        if sibling.name in ["div", "section", "article"]:
            return sibling
        if sibling.name == "pre":
            return sibling
    return None


def error_response(message: str) -> Dict[str, Optional[str]]:
    """Standard error response"""
    return {"japanese_lyrics": None, "romaji_lyrics": None, "metadata": message}