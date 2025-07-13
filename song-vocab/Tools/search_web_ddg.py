from duckduckgo_search import AsyncDDGS
import logging
import random
import asyncio
from typing import List, Dict

logger = logging.getLogger(__name__)


class DuckDuckGoSearcher:
    """DuckDuckGo-based search engine for Japanese song lyrics with enhanced filtering."""

    PREFERRED_DOMAINS = [
        "petitlyrics.com",
        "j-lyric.net",
        "uta-net.com",
        "kashinavi.com",
        "jtw.xyz",
        "animelyrics.com",
        "jpopasia.com",
        "musixmatch.com",
    ]

    def __init__(self, max_results: int = 5, region: str = "jp-jp"):
        self.max_results = max_results
        self.region = region
        self.ddgs = AsyncDDGS()

        self.max_retries = 5  # Maximum number of retries before failing
        self.base_delay = 2  # Initial delay in seconds

    async def search_web_ddg(self, query: str) -> List[Dict[str, str]]:
        logger.info(f"Searching DuckDuckGo for: {query}")

        try:
            enhanced_query = f"{query} 歌詞 lyrics 日本語"
            logger.debug(f"Enhanced query: {enhanced_query}")

            # Random delay to avoid rate limiting
            delay = random.uniform(1.0, 3.0)
            await asyncio.sleep(delay)

            max_attempts = 5
            backoff_time = 5  # Start with 5 seconds
            for attempt in range(max_attempts):
                try:
                    results = []
                    async for result in self.ddgs.text(
                        enhanced_query,
                        region=self.region,
                        safesearch="off",
                        timelimit="y",
                        max_results=self.max_results * 3,
                    ):
                        results.append(result)
                        if len(results) >= self.max_results * 3:
                            break

                    if not results:
                        logger.warning("No search results found")
                        return [{"error": "No results found"}]

                    processed_results = self._process_results(results)
                    final_results = processed_results[: self.max_results]

                    logger.info(f"Returning {len(final_results)} filtered results")
                    return final_results
                except Exception as e:
                    logger.warning(f"Attempt {attempt+1} failed: {str(e)}")
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(backoff_time)
                    backoff_time *= 2  # Exponential backoff

        except Exception as e:
            logger.error(f"DuckDuckGo search failed: {str(e)}", exc_info=True)
            return [
                {
                    "title": "Fallback Result",
                    "url": "https://www.lyrical-nonsense.com/global/lyrics/yoasobi/idol/",
                    "snippet": "Fallback result due to search error",
                }
            ]

    def _process_results(self, results: List[Dict]) -> List[Dict[str, str]]:
        """Filtre et classe les résultats par pertinence"""
        processed = []

        for result in results:
            title = result.get("title", "")
            url = result.get("href", "")
            snippet = result.get("body", "")
            domain = self._extract_domain(url)

            is_priority = any(
                pref_domain in domain for pref_domain in self.PREFERRED_DOMAINS
            )

            score = 0
            if "歌詞" in title or "lyrics" in title.lower():
                score += 2
            if "japanese" in title.lower() or "日本語" in title:
                score += 1
            if "romaji" in title.lower():
                score += 1
            if is_priority:
                score += 3
            if "youtube.com" in domain or "spotify.com" in domain:
                score -= 2

            processed.append(
                {
                    "title": title,
                    "url": url,
                    "snippet": snippet,
                    "domain": domain,
                    "priority": is_priority,
                    "score": score,
                }
            )

        processed.sort(key=lambda x: (-x["score"], -x["priority"]))
        return [
            {"title": r["title"], "url": r["url"], "snippet": r["snippet"]}
            for r in processed
        ]

    def _extract_domain(self, url: str) -> str:
        """Extrait le domaine principal d'une URL"""
        if not url:
            return ""
        domain = url.split("//")[-1].split("/")[0]
        if domain.startswith("www."):
            domain = domain[4:]
        if domain.startswith("m."):
            domain = domain[2:]
        return domain


# Exemple d'utilisation
async def main():
    logging.basicConfig(level=logging.INFO)

    searcher = DuckDuckGoSearcher(max_results=3)
    results = await searcher.search_web("YOASOBI Idol 歌詞")

    for i, result in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Title: {result['title']}")
        print(f"URL: {result['url']}")
        print(f"Snippet: {result['snippet'][:100]}...\n")


if __name__ == "__main__":
    asyncio.run(main())
