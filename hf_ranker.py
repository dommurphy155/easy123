from sentence_transformers import SentenceTransformer, util
import os

class HFMatcher:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Uses a SentenceTransformer model to embed CV and job text,
        then ranks job relevance by cosine similarity.
        Model all‑MiniLM‑L6‑v2 is fast (384-d vectors, ~14K sentences/sec on CPU) while providing good semantic similarity quality.  [oai_citation:0‡huggingface.co](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2?utm_source=chatgpt.com)
        """
        self.model = SentenceTransformer(model_name)
        # Warm-up to pre-load
        _ = self.model.encode("initializing model", convert_to_tensor=True)

    def score(self, cv_text: str, job_text: str) -> float:
        """
        Return a similarity score [0.0–1.0] between CV and job description.
        """
        embeddings = self.model.encode([cv_text, job_text], convert_to_tensor=True)
        sim = util.pytorch_cos_sim(embeddings[0], embeddings[1])
        return float(sim.item())

    @staticmethod
    def example_usage():
        """
        Example:
        > matcher = HFMatcher()
        > score = matcher.score(cv_text, "Software engineer at Acme UK")
        > print(score)
        """
        pass
