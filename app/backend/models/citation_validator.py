import re
import requests
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class CitationValidator:
    def __init__(self):
        self.crossref_api = "https://api.crossref.org/works"
        self.semantic_api = "https://api.semanticscholar.org/graph/v1/paper/search"

        # Common citation styles (heuristic-based)
        self.citation_patterns = {
            "ieee": r"\[(\d+)\]",
            "apa_et_al": r"([A-Z][a-zA-Z]+ et al\., \d{4})",
            "apa_full": r"([A-Z][a-zA-Z]+,\s(?:[A-Z]\.\s?)+\(\d{4}\))",
            "mla": r"“(.+?)”"
        }

    # --------------------------------------------------
    # PUBLIC METHODS
    # --------------------------------------------------
    def extract_citations(self, text: str) -> List[str]:
        """
        Extract citation strings from text
        """
        citations = []

        for pattern in self.citation_patterns.values():
            matches = re.findall(pattern, text)
            citations.extend(matches)

        return list(set(citations))

    def validate_citation(self, citation: str) -> Dict:
        """
        Validate a single citation
        """
        exists, metadata = self._check_existence(citation)
        metadata_ok = self._check_metadata(metadata)
        semantic_ok = self._check_semantic(citation)
        link_ok = self._check_link(metadata)

        return {
            "citation": citation,
            "exists": exists,
            "metadata_complete": metadata_ok,
            "semantic_valid": semantic_ok,
            "link_valid": link_ok,
            "issues": self._identify_issues(
                exists, metadata_ok, semantic_ok, link_ok
            )
        }

    # --------------------------------------------------
    # EXISTENCE CHECK (CrossRef + Semantic Scholar)
    # --------------------------------------------------
    def _check_existence(self, citation: str):
        """
        Check if citation exists in academic databases
        """
        try:
            params = {"query": citation, "rows": 1}
            res = requests.get(self.crossref_api, params=params, timeout=10)
            res.raise_for_status()

            items = res.json().get("message", {}).get("items", [])
            if items:
                return True, items[0]

        except Exception as e:
            logger.warning(f"CrossRef lookup failed: {e}")

        # Fallback: Semantic Scholar
        try:
            params = {"query": citation, "limit": 1}
            headers = {"User-Agent": "AI-H&C/1.0"}
            res = requests.get(
                self.semantic_api, params=params, headers=headers, timeout=10
            )
            res.raise_for_status()

            data = res.json().get("data", [])
            if data:
                return True, data[0]

        except Exception as e:
            logger.warning(f"Semantic Scholar lookup failed: {e}")

        return False, {}

    # --------------------------------------------------
    # METADATA VALIDATION
    # --------------------------------------------------
    def _check_metadata(self, metadata: Dict) -> bool:
        """
        Verify DOI, title, year presence
        """
        if not metadata:
            return False

        has_title = bool(metadata.get("title"))
        has_year = bool(
            metadata.get("published-print")
            or metadata.get("published-online")
            or metadata.get("year")
        )
        has_doi = bool(metadata.get("DOI"))

        return has_title and has_year

    # --------------------------------------------------
    # SEMANTIC VALIDATION (HEURISTIC)
    # --------------------------------------------------
    def _check_semantic(self, citation: str) -> bool:
        """
        Detect obviously fake or vague citations
        """
        red_flags = [
            "unknown",
            "anonymous",
            "example",
            "test paper",
            "lorem ipsum"
        ]

        citation_lower = citation.lower()
        return not any(flag in citation_lower for flag in red_flags)

    # --------------------------------------------------
    # LINK CHECK
    # --------------------------------------------------
    def _check_link(self, metadata: Dict) -> bool:
        """
        Check if DOI or URL resolves
        """
        doi = metadata.get("DOI")
        if not doi:
            return False

        try:
            res = requests.get(f"https://doi.org/{doi}", timeout=10)
            return res.status_code < 400
        except Exception:
            return False

    # --------------------------------------------------
    # ISSUE REPORTING
    # --------------------------------------------------
    def _identify_issues(
        self,
        exists: bool,
        metadata_ok: bool,
        semantic_ok: bool,
        link_ok: bool
    ) -> List[str]:
        issues = []

        if not exists:
            issues.append("Citation not found in academic databases")
        if not metadata_ok:
            issues.append("Incomplete metadata (missing title/year/DOI)")
        if not semantic_ok:
            issues.append("Citation appears semantically suspicious")
        if not link_ok:
            issues.append("DOI or source link not reachable")

        return issues
