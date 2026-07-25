from typing import List, Optional
import logging
from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)


class BM25Index:
    """In-memory BM25 index per repository."""

    _instances: dict = {}

    @classmethod
    def get_instance(cls, repository_id: str) -> "BM25Index":
        if repository_id not in cls._instances:
            cls._instances[repository_id] = cls()
        return cls._instances[repository_id]

    def __init__(self):
        self.documents: List[dict] = []
        self.tokenized: List[List[str]] = []
        self.bm25 = None

    def build(self, documents: List[dict]) -> None:
        self.documents = documents
        self.tokenized = [doc.get("content", "").lower().split() for doc in documents]
        if self.tokenized:
            self.bm25 = BM25Okapi(self.tokenized)

    def search(self, query: str, repository_id: str, top_k: int = 10) -> List[dict]:
        if not self.bm25 or not self.documents:
            return []

        tokenized_query = query.lower().split()
        scores = self.bm25.get_scores(tokenized_query)

        ranked = sorted(
            zip(self.documents, scores),
            key=lambda x: x[1],
            reverse=True,
        )[:top_k]

        return [
            {**doc, "bm25_score": float(score), "score": float(score)}
            for doc, score in ranked if score > 0
        ]


class RetrievalEngine:
    """Retrieval engine for semantic search."""
    
    def __init__(self, vector_db, bm25_index=None):
        """Initialize retrieval engine."""
        self.vector_db = vector_db
        self.bm25_index = bm25_index
    
    async def dense_search(
        self,
        query_embedding: List[float],
        repository_id: str,
        top_k: int = 10
    ) -> List[dict]:
        """Perform dense retrieval using embeddings."""
        try:
            results = await self.vector_db.search(
                query_vector=query_embedding,
                repository_id=repository_id,
                top_k=top_k,
            )
            
            logger.debug(f"Dense search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Dense search error: {str(e)}")
            return []
    
    async def sparse_search(
        self,
        query_text: str,
        repository_id: str,
        top_k: int = 10
    ) -> List[dict]:
        """Perform sparse retrieval using BM25."""
        try:
            if not self.bm25_index:
                logger.warning("BM25 index not available")
                return []
            
            results = self.bm25_index.search(
                query=query_text,
                repository_id=repository_id,
                top_k=top_k,
            )
            
            logger.debug(f"Sparse search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Sparse search error: {str(e)}")
            return []
    
    async def hybrid_search(
        self,
        query_text: str,
        query_embedding: List[float],
        repository_id: str,
        top_k: int = 10,
        alpha: float = 0.5
    ) -> List[dict]:
        """Perform hybrid retrieval combining dense and sparse search."""
        try:
            # Get results from both retrievers
            dense_results = await self.dense_search(
                query_embedding,
                repository_id,
                top_k=top_k * 2
            )
            sparse_results = await self.sparse_search(
                query_text,
                repository_id,
                top_k=top_k * 2
            )
            
            # Merge and rerank results
            merged_results = self._merge_search_results(
                dense_results,
                sparse_results,
                alpha=alpha
            )
            
            # Return top-k
            return merged_results[:top_k]
        except Exception as e:
            logger.error(f"Hybrid search error: {str(e)}")
            return []
    
    @staticmethod
    def _merge_search_results(
        dense_results: List[dict],
        sparse_results: List[dict],
        alpha: float = 0.5
    ) -> List[dict]:
        """Merge and rank results from dense and sparse retrieval."""
        # Create result map
        result_map = {}
        
        # Add dense results
        for i, result in enumerate(dense_results):
            doc_id = result.get("id") or result.get("chunk_id")
            score = result.get("similarity_score", 0) or result.get("score", 0)
            
            # Normalize score to 0-1
            normalized_score = min(max(score, 0), 1)
            
            result_map[doc_id] = {
                **result,
                "dense_score": normalized_score,
                "dense_rank": i + 1,
                "sparse_score": 0,
                "sparse_rank": float('inf'),
            }
        
        # Add/update with sparse results
        for i, result in enumerate(sparse_results):
            doc_id = result.get("id") or result.get("chunk_id")
            score = result.get("bm25_score", 0) or result.get("score", 0)
            
            # Normalize BM25 score
            normalized_score = min(max(score / 10, 0), 1)  # BM25 scores can exceed 1
            
            if doc_id in result_map:
                result_map[doc_id]["sparse_score"] = normalized_score
                result_map[doc_id]["sparse_rank"] = i + 1
            else:
                result_map[doc_id] = {
                    **result,
                    "dense_score": 0,
                    "dense_rank": float('inf'),
                    "sparse_score": normalized_score,
                    "sparse_rank": i + 1,
                }
        
        # Calculate combined score
        for doc_id, result in result_map.items():
            # Normalize ranks
            dense_rank_norm = min(result["dense_rank"], 100) / 100
            sparse_rank_norm = min(result["sparse_rank"], 100) / 100
            
            # Combined score: weighted sum of score components
            combined_score = (
                alpha * (1 - dense_rank_norm) +
                (1 - alpha) * (1 - sparse_rank_norm)
            )
            
            result_map[doc_id]["combined_score"] = combined_score
        
        # Sort by combined score
        merged = sorted(
            result_map.values(),
            key=lambda x: x["combined_score"],
            reverse=True
        )
        
        return merged


class QueryExpander:
    """Expand queries for better retrieval."""
    
    @staticmethod
    def expand_query(query: str) -> List[str]:
        """Expand query with synonyms and variations."""
        expanded = [query]
        
        # Add common synonyms
        synonyms = {
            "authenticate": ["auth", "login", "signin", "access control"],
            "database": ["db", "storage", "data store", "persistence"],
            "function": ["method", "procedure", "routine"],
            "class": ["object", "type", "interface"],
            "error": ["exception", "fault", "failure"],
            "validate": ["verify", "check", "sanitize"],
        }
        
        # Check for keywords and add synonyms
        query_lower = query.lower()
        for keyword, syns in synonyms.items():
            if keyword in query_lower:
                for syn in syns:
                    expanded.append(query.replace(keyword, syn))
        
        return expanded


class ResultReranker:
    """Rerank retrieval results using cross-encoders."""
    
    def __init__(self, model=None):
        """Initialize reranker."""
        self.model = model
    
    async def rerank(
        self,
        query: str,
        candidates: List[dict],
        top_k: int = 3
    ) -> List[dict]:
        """Rerank candidates using cross-encoder."""
        if not self.model:
            # If no cross-encoder, return candidates as-is sorted by score
            return sorted(
                candidates,
                key=lambda x: x.get("combined_score", 0),
                reverse=True
            )[:top_k]
        
        try:
            # Prepare query-candidate pairs
            pairs = [
                [query, c.get("snippet", "")]
                for c in candidates
            ]
            
            # Score pairs
            scores = self.model.predict(pairs)
            
            # Update scores
            for i, candidate in enumerate(candidates):
                candidate["rerank_score"] = float(scores[i])
            
            # Sort and return top-k
            reranked = sorted(
                candidates,
                key=lambda x: x.get("rerank_score", 0),
                reverse=True
            )
            
            return reranked[:top_k]
        except Exception as e:
            logger.error(f"Reranking error: {str(e)}")
            # Fall back to original ranking
            return candidates[:top_k]
