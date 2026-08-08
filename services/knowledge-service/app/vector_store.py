from __future__ import annotations

import json
import pickle
from pathlib import Path
from typing import Any

import numpy as np

from app.config import get_settings

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover
    faiss = None

try:
    import chromadb  # type: ignore
except ImportError:  # pragma: no cover
    chromadb = None  # optional; default stack uses FAISS only



class VectorStore:
    """FAISS (default) or Chroma-backed chunk store for hybrid RAG."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.backend = (self.settings.vector_backend or "faiss").lower()
        self._meta: list[dict[str, Any]] = []
        self._index = None
        self._chroma = None
        self._dim: int | None = None
        Path(self.settings.faiss_index_dir).mkdir(parents=True, exist_ok=True)
        Path(self.settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)
        self._load()

    def _faiss_paths(self) -> tuple[Path, Path]:
        root = Path(self.settings.faiss_index_dir)
        return root / "index.faiss", root / "meta.pkl"

    def _load(self) -> None:
        if self.backend == "chroma" and chromadb is not None:
            client = chromadb.PersistentClient(path=self.settings.chroma_persist_dir)
            self._chroma = client.get_or_create_collection(
                name="knowledge_chunks",
                metadata={"hnsw:space": "cosine"},
            )
            return

        # FAISS path (also used if chroma package missing)
        self.backend = "faiss"
        index_path, meta_path = self._faiss_paths()
        if index_path.exists() and meta_path.exists() and faiss is not None:
            self._index = faiss.read_index(str(index_path))
            with meta_path.open("rb") as f:
                self._meta = pickle.load(f)
            self._dim = self._index.d if self._index.ntotal else None

    def _save_faiss(self) -> None:
        if self._index is None or faiss is None:
            return
        index_path, meta_path = self._faiss_paths()
        faiss.write_index(self._index, str(index_path))
        with meta_path.open("wb") as f:
            pickle.dump(self._meta, f)
        # human-readable sidecar for debugging
        (Path(self.settings.faiss_index_dir) / "meta.json").write_text(
            json.dumps([{"id": m.get("id"), "title": m.get("title"), "url": m.get("url")} for m in self._meta], indent=2),
            encoding="utf-8",
        )

    def add(self, vectors: np.ndarray, metadatas: list[dict[str, Any]]) -> int:
        if vectors.size == 0:
            return 0
        if vectors.ndim == 1:
            vectors = vectors.reshape(1, -1)

        if self.backend == "chroma" and self._chroma is not None:
            ids = [m["id"] for m in metadatas]
            self._chroma.upsert(
                ids=ids,
                embeddings=vectors.tolist(),
                documents=[m.get("text", "") for m in metadatas],
                metadatas=[
                    {
                        "title": m.get("title", ""),
                        "url": m.get("url", ""),
                        "doc_id": m.get("doc_id", ""),
                    }
                    for m in metadatas
                ],
            )
            return len(metadatas)

        if faiss is None:
            # Pure numpy fallback store
            self._meta.extend(metadatas)
            store = Path(self.settings.faiss_index_dir) / "vectors.npy"
            if store.exists():
                old = np.load(store)
                np.save(store, np.vstack([old, vectors]))
            else:
                np.save(store, vectors)
            with (Path(self.settings.faiss_index_dir) / "meta.pkl").open("wb") as f:
                pickle.dump(self._meta, f)
            return len(metadatas)

        dim = vectors.shape[1]
        if self._index is None:
            self._index = faiss.IndexFlatIP(dim)
            self._dim = dim
        self._index.add(vectors.astype(np.float32))
        self._meta.extend(metadatas)
        self._save_faiss()
        return len(metadatas)

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> list[dict[str, Any]]:
        if query_vec.ndim == 1:
            query_vec = query_vec.reshape(1, -1)
        query_vec = query_vec.astype(np.float32)

        if self.backend == "chroma" and self._chroma is not None:
            res = self._chroma.query(query_embeddings=query_vec.tolist(), n_results=top_k)
            out: list[dict[str, Any]] = []
            docs = (res.get("documents") or [[]])[0]
            metas = (res.get("metadatas") or [[]])[0]
            dists = (res.get("distances") or [[]])[0]
            for doc, meta, dist in zip(docs, metas, dists):
                score = 1.0 - float(dist) if dist is not None else 0.0
                out.append(
                    {
                        "type": "rag",
                        "title": (meta or {}).get("title", ""),
                        "url": (meta or {}).get("url", ""),
                        "snippet": (doc or "")[:400],
                        "score": score,
                    }
                )
            return out

        if faiss is not None and self._index is not None and self._index.ntotal > 0:
            scores, idxs = self._index.search(query_vec, min(top_k, self._index.ntotal))
            results: list[dict[str, Any]] = []
            for score, idx in zip(scores[0], idxs[0]):
                if idx < 0 or idx >= len(self._meta):
                    continue
                m = self._meta[idx]
                results.append(
                    {
                        "type": "rag",
                        "title": m.get("title", ""),
                        "url": m.get("url", ""),
                        "snippet": m.get("text", "")[:400],
                        "score": float(score),
                    }
                )
            return results

        # numpy cosine fallback
        store = Path(self.settings.faiss_index_dir) / "vectors.npy"
        meta_path = Path(self.settings.faiss_index_dir) / "meta.pkl"
        if not store.exists() or not meta_path.exists():
            return []
        mat = np.load(store)
        with meta_path.open("rb") as f:
            meta = pickle.load(f)
        sims = (mat @ query_vec.T).reshape(-1)
        order = np.argsort(-sims)[:top_k]
        return [
            {
                "type": "rag",
                "title": meta[i].get("title", ""),
                "url": meta[i].get("url", ""),
                "snippet": meta[i].get("text", "")[:400],
                "score": float(sims[i]),
            }
            for i in order
        ]

    def list_sources(self) -> list[dict[str, str]]:
        seen: dict[str, dict[str, str]] = {}
        for m in self._meta:
            doc_id = m.get("doc_id") or m.get("url") or m.get("id")
            if doc_id and doc_id not in seen:
                seen[str(doc_id)] = {
                    "id": str(doc_id),
                    "url": m.get("url", ""),
                    "title": m.get("title", ""),
                }
        if self.backend == "chroma" and self._chroma is not None:
            # Best-effort listing
            try:
                raw = self._chroma.get(include=["metadatas"])
                for meta in raw.get("metadatas") or []:
                    if not meta:
                        continue
                    key = meta.get("doc_id") or meta.get("url")
                    if key and key not in seen:
                        seen[str(key)] = {
                            "id": str(key),
                            "url": meta.get("url", ""),
                            "title": meta.get("title", ""),
                        }
            except Exception:  # noqa: BLE001
                pass
        return list(seen.values())


_STORE: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _STORE
    if _STORE is None:
        _STORE = VectorStore()
    return _STORE
