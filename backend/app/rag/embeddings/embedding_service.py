from typing import List, Optional
from abc import ABC, abstractmethod
import logging
import numpy as np

logger = logging.getLogger(__name__)


class EmbeddingModel(ABC):
    """Abstract base class for embedding models."""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text."""
        pass
    
    @abstractmethod
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts."""
        pass


class GeminiEmbeddingModel(EmbeddingModel):
    """Google Gemini Embedding Model wrapper."""
    
    def __init__(self, api_key: str, model: str = "models/gemini-embedding-2"):
        """Initialize Gemini embedding model."""
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        self.genai = genai
        self.model = model
        self.model_name = model
        
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text using Gemini."""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.genai.embed_content(
                    model=self.model,
                    content=text,
                    task_type="retrieval_document",
                )
            )
            return result["embedding"]
        except Exception as e:
            logger.error(f"Gemini embedding error: {str(e)}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts using Gemini."""
        try:
            embeddings = []
            for text in texts:
                emb = await self.embed_text(text)
                embeddings.append(emb)
            return embeddings
        except Exception as e:
            logger.error(f"Gemini batch embedding error: {str(e)}")
            raise


class OpenAIEmbeddingModel(EmbeddingModel):
    """OpenAI Embedding Model wrapper (fallback)."""
    
    def __init__(self, api_key: str, model: str = "text-embedding-3-large"):
        """Initialize OpenAI embedding model."""
        from openai import AsyncOpenAI
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.model_name = model
        
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text using OpenAI."""
        try:
            response = await self.client.embeddings.create(
                input=text,
                model=self.model,
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"OpenAI embedding error: {str(e)}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts using OpenAI."""
        try:
            response = await self.client.embeddings.create(
                input=texts,
                model=self.model,
            )
            embeddings = sorted(response.data, key=lambda x: x.index)
            return [e.embedding for e in embeddings]
        except Exception as e:
            logger.error(f"OpenAI batch embedding error: {str(e)}")
            raise


class LocalEmbeddingModel(EmbeddingModel):
    """Local embedding model using sentence-transformers."""
    
    def __init__(self, model_name: str = "BAAI/bge-large-en-v1.5"):
        """Initialize local embedding model."""
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text locally."""
        try:
            embedding = self.model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Local embedding error: {str(e)}")
            raise
    
    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed multiple texts locally."""
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Local batch embedding error: {str(e)}")
            raise


class EmbeddingProcessor:
    """Process texts into embeddings."""
    
    def __init__(self, model: EmbeddingModel):
        """Initialize embedding processor."""
        self.model = model
    
    async def embed_code_chunk(self, code: str, metadata: Optional[dict] = None) -> dict:
        """Embed a code chunk with metadata."""
        try:
            if metadata and metadata.get("entity_name"):
                text_input = f"{metadata['entity_name']}: {code}"
            else:
                text_input = code
            
            embedding = await self.model.embed_text(text_input)
            
            return {
                "embedding": embedding,
                "model": self.model.model_name if hasattr(self.model, 'model_name') else "gemini",
                "dimension": len(embedding),
                "metadata": metadata or {},
            }
        except Exception as e:
            logger.error(f"Embedding processor error: {str(e)}")
            raise
    
    async def embed_chunks(self, chunks: List[dict]) -> List[dict]:
        """Embed multiple code chunks."""
        try:
            texts = [c.get("content", "") for c in chunks]
            embeddings = await self.model.embed_texts(texts)
            
            results = []
            for i, embedding in enumerate(embeddings):
                results.append({
                    "chunk_index": i,
                    "embedding": embedding,
                    "model": self.model.model_name if hasattr(self.model, 'model_name') else "gemini",
                    "dimension": len(embedding),
                    "metadata": chunks[i].get("metadata", {}),
                })
            
            return results
        except Exception as e:
            logger.error(f"Batch embedding error: {str(e)}")
            raise


class SemanticSimilarity:
    """Calculate semantic similarity between embeddings."""
    
    @staticmethod
    def cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
        """Calculate cosine similarity between two embeddings."""
        try:
            v1 = np.array(embedding1)
            v2 = np.array(embedding2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"Similarity calculation error: {str(e)}")
            return 0.0
    
    @staticmethod
    def batch_cosine_similarity(
        query_embedding: List[float],
        embeddings: List[List[float]]
    ) -> List[float]:
        """Calculate cosine similarity between query and multiple embeddings."""
        try:
            similarities = []
            for embedding in embeddings:
                sim = SemanticSimilarity.cosine_similarity(
                    query_embedding,
                    embedding
                )
                similarities.append(sim)
            
            return similarities
        except Exception as e:
            logger.error(f"Batch similarity error: {str(e)}")
            return [0.0] * len(embeddings)
    
    @staticmethod
    def top_k_similar(
        query_embedding: List[float],
        embeddings: List[dict],
        k: int = 5
    ) -> List[dict]:
        """Get top-k most similar embeddings."""
        try:
            similarities = SemanticSimilarity.batch_cosine_similarity(
                query_embedding,
                [e.get("vector", []) for e in embeddings]
            )
            
            ranked = []
            for i, (embedding, similarity) in enumerate(zip(embeddings, similarities)):
                ranked.append({
                    **embedding,
                    "similarity_score": similarity,
                    "rank": i + 1,
                })
            
            ranked.sort(key=lambda x: x["similarity_score"], reverse=True)
            
            return ranked[:k]
        except Exception as e:
            logger.error(f"Top-k retrieval error: {str(e)}")
            return []
