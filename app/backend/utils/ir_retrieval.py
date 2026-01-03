import requests
from typing import List
import logging
from time import sleep
import time

logger = logging.getLogger(__name__)

class IRRetrieval:
    def __init__(self):
        self.crossref_api = "https://api.crossref.org/works"
        self.semantic_api = "https://api.semanticscholar.org/graph/v1/paper/search"

    # -----------------------------
    # PUBLIC METHOD
    # -----------------------------
    def search_evidence(self, claim: str) -> List[str]:
        """
        Search for evidence texts relevant to the claim
        Returns a list of textual evidence snippets
        """
        evidence = []

        try:
            evidence += self._search_crossref(claim)
        except Exception as e:
            logger.warning(f"CrossRef search failed: {e}")

        try:
            evidence += self._search_semantic_scholar(claim)
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed: {e}")

        return self._rank_results(evidence, claim)

    # -----------------------------
    # CROSSREF SEARCH
    # -----------------------------
    
    def _search_crossref(self, query: str) -> List[str]:
        params = {
            "query": query,
            "rows": 5,
            "mailto": "aihc.project@example.com"
        }

        response = requests.get(self.crossref_api, params=params, timeout=10)
        response.raise_for_status()

        items = response.json().get("message", {}).get("items", [])

        results = []
        for item in items:
            title = " ".join(item.get("title", []))
            abstract = item.get("abstract")

            if abstract:
                results.append(self._clean_text(abstract))
            elif title:
                results.append(title)

        return results

    # -----------------------------
    # SEMANTIC SCHOLAR SEARCH
    # -----------------------------
    def _search_semantic_scholar(self, query: str) -> List[str]:
        headers = {
            "User-Agent": "AI-Hallucination-Checker/1.0 (academic-project)"
        }
        params = {
            "query": query,
            "limit": 5,
            "fields": "title,abstract"
        }

        for attempt in range(3):
            response = requests.get(
                self.semantic_api,
                params=params,
                headers=headers,
                timeout=10
        )

            if response.status_code == 429:
                time.sleep(2 * (attempt + 1))  # exponential backoff
                continue

            response.raise_for_status()
            break
        else:
            raise RuntimeError("Semantic Scholar rate limit exceeded")

        data = response.json().get("data", [])

        results = []
        for paper in data:
            if paper.get("abstract"):
                results.append(self._clean_text(paper["abstract"]))
            elif paper.get("title"):
                results.append(paper["title"])

        return results

    # -----------------------------
    # RANKING (SIMPLE & EFFECTIVE)
    # -----------------------------
    def _rank_results(self, evidence_list: List[str], claim: str) -> List[str]:
        """
        Rank evidence by keyword overlap with claim
        """
        claim_words = set(claim.lower().split())

        scored = []
        for ev in evidence_list:
            ev_words = set(ev.lower().split())
            score = len(claim_words.intersection(ev_words))
            scored.append((ev, score))

        scored.sort(key=lambda x: x[1], reverse=True)

        # Return top 5 evidence snippets
        return [ev for ev, _ in scored[:5]]

    # -----------------------------
    # TEXT CLEANING
    # -----------------------------
    def _clean_text(self, text: str) -> str:
        """
        Remove HTML tags & trim text
        """
        return (
            text.replace("<jats:p>", "")
                .replace("</jats:p>", "")
                .strip()
        )
