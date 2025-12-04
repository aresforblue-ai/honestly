import faiss
import numpy as np
import pickle
import os
from typing import List, Dict, Optional

class FaissIndex:
    def __init__(self, dim: int = 384,
                 index_path: str = 'faiss.index',
                 meta_path: str = 'faiss_meta.pkl'):
        self.dim = dim
        self.index_path = index_path
        self.meta_path = meta_path

        # meta structure:
        # {
        #   'next_id': int,
        #   'id_to_faiss': { external_id (str): faiss_id (int) },
        #   'faiss_to_id': { faiss_id (int): external_id (str) },
        #   'meta_store': { str(faiss_id): {'external_id': str, 'metadata': dict} }
        # }
        if os.path.exists(self.index_path) and os.path.exists(self.meta_path):
            try:
                self.index = faiss.read_index(self.index_path)
                with open(self.meta_path, 'rb') as f:
                    self.meta = pickle.load(f)
                # Ensure index is an IndexIDMap wrapper for id-aware operations
                if not isinstance(self.index, faiss.IndexIDMap):
                    self.index = faiss.IndexIDMap(self.index)
            except Exception as e:
                print(f"Warning: failed to read index/meta, creating new index ({e})")
                self._create_empty()
        else:
            self._create_empty()

    def _create_empty(self):
        base_index = faiss.IndexFlatL2(self.dim)
        self.index = faiss.IndexIDMap(base_index)
        self.meta = {'next_id': 1, 'id_to_faiss': {}, 'faiss_to_id': {}, 'meta_store': {}}
        self._save()

    def _save(self):
        # write faiss index
        faiss.write_index(self.index, self.index_path)
        # write meta mapping
        with open(self.meta_path, 'wb') as f:
            pickle.dump(self.meta, f)

    def add(self, id: str, vector: List[float], metadata: Optional[dict] = None) -> int:
        """
        Add a vector for external string id. Returns the faiss integer id used.
        If the external id already exists, this will reuse the same faiss id and
        append an additional vector (IndexFlatL2 via IndexIDMap won't replace in-place).
        For small scale, duplicates are acceptable; for production, implement delete+reindex.
        """
        if id in self.meta['id_to_faiss']:
            faiss_id = self.meta['id_to_faiss'][id]
        else:
            faiss_id = self.meta['next_id']
            self.meta['next_id'] += 1
            self.meta['id_to_faiss'][id] = faiss_id
            self.meta['faiss_to_id'][faiss_id] = id

        vec = np.array([vector], dtype='float32')
        ids = np.array([faiss_id], dtype='int64')
        try:
            self.index.add_with_ids(vec, ids)
        except Exception as e:
            raise RuntimeError(f"Failed to add vector to FAISS index: {e}")

        # store metadata per faiss id in meta (optional)
        self.meta['meta_store'][str(faiss_id)] = {'external_id': id, 'metadata': metadata}
        self._save()
        return faiss_id

    def search(self, vector: List[float], top_k: int = 5) -> List[Dict]:
        vec = np.array([vector], dtype='float32')
        D, I = self.index.search(vec, top_k)
        results = []
        for dist, faiss_id in zip(D[0], I[0]):
            if faiss_id == -1:
                continue
            external_id = self.meta['faiss_to_id'].get(int(faiss_id))
            md = self.meta.get('meta_store', {}).get(str(int(faiss_id)))
            results.append({
                'id': external_id,
                'score': float(dist),
                'metadata': md.get('metadata') if md else None
            })
        return results

    def delete(self, external_id: str):
        """
        FAISS deletion support is index-dependent. IndexFlatL2 doesn't support deletion.
        For real deletion: rebuild index from scratch excluding this id.
        Here we simply remove mapping and mark it; reindexing is left to the caller.
        """
        faiss_id = self.meta['id_to_faiss'].pop(external_id, None)
        if faiss_id:
            self.meta['faiss_to_id'].pop(faiss_id, None)
            self.meta.get('meta_store', {}).pop(str(faiss_id), None)
            self._save()
            # Note: vectors remain in index until re-built.

    def count(self) -> int:
        return int(self.index.ntotal)