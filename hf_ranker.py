import os
import numpy as np
from sentence_transformers import SentenceTransformer, util
import pickle
import logging

CACHE_FILE = "hf_cache.pkl"

class HFMatcher:
    def __init__(self, model_name="all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logging.warning(f"Failed loading cache: {e}")
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            logging.warning(f"Failed saving cache: {e}")

    def embed(self, text):
        if text in self.cache:
            return self.cache[text]
        embedding = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        self.cache[text] = embedding
        self._save_cache()
        return embedding

    def score(self, cv_text, job_text):
        """
        Returns cosine similarity score (0 to 1) between CV and job desc
        """
        cv_emb = self.embed(cv_text)
        job_emb = self.embed(job_text)
        score = util.cos_sim(cv_emb, job_emb).item()
        return score
