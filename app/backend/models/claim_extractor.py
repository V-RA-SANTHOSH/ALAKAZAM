from transformers import pipeline
import spacy

class ClaimExtractor:
    def __init__(self):
        """
        Initialize NLP models:
        - spaCy for sentence segmentation
        - Zero-shot classifier for future extensibility
        """
        self.nlp = spacy.load("en_core_web_sm")

        # Zero-shot model (used later if needed)
        self.zero_shot = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli"
        )

    def extract_claims(self, text: str) -> list:
        """
        Decompose input text into atomic factual claims
        """
        doc = self.nlp(text)

        # Sentence tokenization
        sentences = [sent.text.strip() for sent in doc.sents]

        # Filter only factual claims
        claims = self._filter_factual_claims(sentences)

        return claims

    def _filter_factual_claims(self, sentences: list) -> list:
        """
        Remove questions, imperatives, and very short sentences
        """
        claims = []

        for sent in sentences:
            # Skip questions
            if sent.endswith("?"):
                continue

            # Skip very short sentences
            if len(sent.split()) < 5:
                continue

            # Skip imperatives (basic heuristic)
            if sent.lower().startswith(("please", "do ", "try ", "consider ")):
                continue

            claims.append(sent)

        return claims
