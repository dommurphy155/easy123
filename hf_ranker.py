import os
import pickle
import logging
import torch
import torch.nn.functional as F
from transformers import AutoTokenizer, AutoModel

CACHE_FILE = "hf_cache.pkl"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

class HFMatcher:
    def __init__(self, model_name=MODEL_NAME):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModel.from_pretrained(model_name).to(self.device)
            self.model.eval()
        except Exception as e:
            logging.error(f"[HFMatcher] Model load failed: {e}")
            raise RuntimeError("Transformer model failed to load.")

        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, "rb") as f:
                    return pickle.load(f)
            except Exception as e:
                logging.warning(f"[HFMatcher] Failed loading cache: {e}")
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, "wb") as f:
                pickle.dump(self.cache, f)
        except Exception as e:
            logging.warning(f"[HFMatcher] Failed saving cache: {e}")

    def embed(self, text: str):
        if text in self.cache:
            return self.cache[text]

        try:
            encoded = self.tokenizer(text, return_tensors="pt", truncation=True, padding=True).to(self.device)
            with torch.no_grad():
                output = self.model(**encoded)
                cls_embedding = output.last_hidden_state[:, 0, :]
                norm_embedding = F.normalize(cls_embedding, p=2, dim=1).cpu().numpy()[0]
        except Exception as e:
            logging.error(f"[HFMatcher] Embedding failed: {e}")
            raise RuntimeError("Embedding generation failed.")

        self.cache[text] = norm_embedding
        self._save_cache()
        return norm_embedding

    def score(self, cv_text: str, job_text: str) -> float:
        try:
            cv_vec = self.embed(cv_text)
            job_vec = self.embed(job_text)
            score = float(F.cosine_similarity(torch.tensor(cv_vec), torch.tensor(job_vec), dim=0).item())
            return round(score, 4)
        except Exception as e:
            logging.error(f"[HFMatcher] Scoring failed: {e}")
            return 0.0
