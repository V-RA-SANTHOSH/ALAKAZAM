from transformers import pipeline
from typing import List
import logging

logger = logging.getLogger(__name__)

class NLIVerifier:
    def __init__(self):
        """
        Initialize NLI pipeline
        """
        try:
            self.nli = pipeline(
                "zero-shot-classification",
                model="facebook/bart-large-mnli"
            )
        except Exception as e:
            logger.error(f"Failed to load NLI model: {e}")
            raise RuntimeError("NLI model initialization failed")

    def verify_claim(self, claim: str, evidence_list: List[str]) -> dict:
        """
        Verify a claim against multiple evidence texts
        Returns verdict + confidence
        """
        if not evidence_list:
            return {
                "label": "UNVERIFIABLE",
                "confidence": 0.0
            }

        scores = []

        for evidence in evidence_list:
            try:
                result = self.nli(
                    sequences=claim,
                    candidate_labels=["entailment", "contradiction", "neutral"],
                    hypothesis_template="This evidence {} the claim. " 

                )

                label = result["labels"][0]
                score = result["scores"][0]

                scores.append((label, score))

            except Exception as e:
                logger.warning(f"NLI inference failed: {e}")
                continue

        return self._aggregate_results(scores)

    def _aggregate_results(self, scores: list) -> dict:
          """
           Conservative aggregation of NLI results
          """
          if not scores:
              return {"label": "UNVERIFIABLE", "confidence": 0.0}

          mapped = []
          label_map = {
                "entailment": "ENTAILED",
                "contradiction": "CONTRADICTED",
                "neutral": "UNVERIFIABLE"
           }
          for label, score in scores:
              mapped.append((label_map[label], score))

    # Priority rules (important)
          contradictions = [s for la, s in mapped if la == "CONTRADICTED"]
          entailments = [s for la, s in mapped if la == "ENTAILED"]
          if contradictions and max(contradictions) > 0.5:
               return {
                    "label": "CONTRADICTED",
                    "confidence": round(max(contradictions), 3)
               }
          if entailments and max(entailments) > 0.5:
              return {
                 "label": "ENTAILED",
                 "confidence": round(max(entailments), 3)
             }

          return {
             "label": "UNVERIFIABLE",
            "confidence": round(max(score for _, score in mapped), 3)
           }
               
          
        