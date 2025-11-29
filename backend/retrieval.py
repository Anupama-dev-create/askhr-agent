from typing import List, Dict, Tuple
import numpy as np
import json
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Data directory and JSON file
DATA_DIR = Path("data")
DATA_PATH = DATA_DIR / "hr_knowledge.json"


class HRRetrievalIndex:
    def __init__(self):
        self.vectorizer = None
        self.doc_matrix = None
        self.documents: List[Dict] = []

        # Load saved KB if it exists
        self.load_index()

    # ---------------------------
    # Save KB
    # ---------------------------
    def save_index(self):
        DATA_DIR.mkdir(exist_ok=True)

        if not self.documents:
            # If empty → delete file
            if DATA_PATH.exists():
                DATA_PATH.unlink()
            return

        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump({"documents": self.documents}, f, ensure_ascii=False, indent=2)

    # ---------------------------
    # Load KB
    # ---------------------------
    def load_index(self):
        if not DATA_PATH.exists():
            return

        try:
            with open(DATA_PATH, "r", encoding="utf-8") as f:
                stored = json.load(f)
        except Exception:
            # corrupted file → remove it
            DATA_PATH.unlink(missing_ok=True)
            return

        self.documents = stored.get("documents", [])
        if not self.documents:
            return

        texts = [d["text"] for d in self.documents]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_matrix = self.vectorizer.fit_transform(texts)

    # ---------------------------
    # Clear KB
    # ---------------------------
    def clear_index(self):
        self.documents = []
        self.vectorizer = None
        self.doc_matrix = None
        if DATA_PATH.exists():
            DATA_PATH.unlink()

    # ---------------------------
    # Build new KB
    # ---------------------------
    def build_index(self, documents: List[Dict]) -> Tuple[np.ndarray, List[Dict]]:
        self.documents = documents

        if not documents:
            self.doc_matrix = None
            self.vectorizer = None
            self.save_index()
            return np.zeros((0, 1)), []

        texts = [d["text"] for d in documents]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.doc_matrix = self.vectorizer.fit_transform(texts)

        # Save permanently
        self.save_index()

        return self.doc_matrix, self.documents

    # ---------------------------
    # Query
    # ---------------------------
    def retrieve_top_k(self, query: str, k=4) -> List[Dict]:
        if not self.documents or self.vectorizer is None:
            return []

        query_vec = self.vectorizer.transform([query])
        scores = cosine_similarity(query_vec, self.doc_matrix)[0]

        top_idx = np.argsort(scores)[::-1][:k]
        results = []

        for idx in top_idx:
            doc = self.documents[int(idx)].copy()
            doc["score"] = float(scores[idx])
            results.append(doc)

        return results


# Global instance
_index = HRRetrievalIndex()


# Wrappers used in app.py
def build_index(documents: List[Dict]):
    return _index.build_index(documents)


def retrieve_top_k(query, emb_unused, docs_unused, k=4):
    return _index.retrieve_top_k(query, k)


def load_existing_index():
    return _index.documents


def clear_index():
    _index.clear_index()
