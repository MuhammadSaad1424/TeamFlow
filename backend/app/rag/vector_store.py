from typing import List, Optional, Dict
from abc import ABC, abstractmethod
import logging
import json

logger = logging.getLogger(__name__)


class VectorStore(ABC):
    """Abstract base class for vector stores."""
    
    @abstractmethod
    async def add_vectors(self, vectors: List[Dict]) -> List[str]:
        """Add vectors to store."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_vector: List[float],
        repository_id: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict]:
        """Search for similar vectors."""
        pass
    
    @abstractmethod
    async def delete(self, vector_id: str) -> bool:
        """Delete vector from store."""
        pass


class ChromaDBStore(VectorStore):
    """ChromaDB vector store wrapper."""
    
    def __init__(self, path: str = "./data/chromadb"):
        """Initialize ChromaDB store."""
        import chromadb
        self.client = chromadb.PersistentClient(path=path)
        self.collections = {}
    
    def _get_collection(self, repository_id: str):
        """Get or create collection for repository."""
        collection_name = f"repo_{repository_id}".replace("-", "_")
        
        if collection_name not in self.collections:
            self.collections[collection_name] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"},
            )
        
        return self.collections[collection_name]
    
    async def add_vectors(
        self,
        vectors: List[Dict],
        repository_id: str,
    ) -> List[str]:
        """Add vectors to ChromaDB."""
        try:
            collection = self._get_collection(repository_id)
            
            ids = []
            embeddings = []
            metadatas = []
            documents = []
            
            for vector_data in vectors:
                vector_id = vector_data.get("id") or vector_data.get("vector_id")
                ids.append(str(vector_id))
                embeddings.append(vector_data.get("embedding"))
                metadatas.append(vector_data.get("metadata", {}))
                documents.append(vector_data.get("content", ""))
            
            collection.add(
                ids=ids,
                embeddings=embeddings,
                metadatas=metadatas,
                documents=documents,
            )
            
            logger.info(f"Added {len(ids)} vectors to ChromaDB")
            return ids
        except Exception as e:
            logger.error(f"ChromaDB add error: {str(e)}")
            raise
    
    async def search(
        self,
        query_vector: List[float],
        repository_id: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict]:
        """Search ChromaDB."""
        try:
            collection = self._get_collection(repository_id)
            
            results = collection.query(
                query_embeddings=[query_vector],
                n_results=top_k,
            )
            
            # Format results
            formatted = []
            if results and results["ids"]:
                for i, (doc_id, distance, document, metadata) in enumerate(zip(
                    results["ids"][0],
                    results["distances"][0],
                    results["documents"][0],
                    results["metadatas"][0],
                )):
                    # Convert distance to similarity (cosine distance to similarity)
                    similarity = 1 - distance
                    
                    formatted.append({
                        "id": doc_id,
                        "chunk_id": doc_id,
                        "content": document,
                        "snippet": document[:500] if len(document) > 500 else document,
                        "similarity_score": similarity,
                        "metadata": metadata,
                        "rank": i + 1,
                    })
            
            return formatted
        except Exception as e:
            logger.error(f"ChromaDB search error: {str(e)}")
            return []
    
    async def delete(self, vector_id: str, repository_id: str) -> bool:
        """Delete vector from ChromaDB."""
        try:
            collection = self._get_collection(repository_id)
            collection.delete(ids=[str(vector_id)])
            logger.info(f"Deleted vector {vector_id} from ChromaDB")
            return True
        except Exception as e:
            logger.error(f"ChromaDB delete error: {str(e)}")
            return False


class PineconeStore(VectorStore):
    """Pinecone vector store wrapper."""
    
    def __init__(self, api_key: str, environment: str, index_name: str):
        """Initialize Pinecone store."""
        import pinecone
        self.index_name = index_name
        
        pinecone.init(api_key=api_key, environment=environment)
        self.index = pinecone.Index(index_name)
    
    async def add_vectors(
        self,
        vectors: List[Dict],
        repository_id: str,
    ) -> List[str]:
        """Add vectors to Pinecone."""
        try:
            vectors_to_upsert = []
            ids = []
            
            for vector_data in vectors:
                vector_id = f"{repository_id}#{vector_data.get('id', '')}"
                ids.append(vector_id)
                
                vectors_to_upsert.append((
                    vector_id,
                    vector_data.get("embedding"),
                    vector_data.get("metadata", {}),
                ))
            
            self.index.upsert(
                vectors=vectors_to_upsert,
                namespace=repository_id,
            )
            
            logger.info(f"Added {len(ids)} vectors to Pinecone")
            return ids
        except Exception as e:
            logger.error(f"Pinecone add error: {str(e)}")
            raise
    
    async def search(
        self,
        query_vector: List[float],
        repository_id: str,
        top_k: int = 5,
        **kwargs
    ) -> List[Dict]:
        """Search Pinecone."""
        try:
            results = self.index.query(
                query_vector,
                top_k=top_k,
                namespace=repository_id,
                include_metadata=True,
            )
            
            # Format results
            formatted = []
            for i, match in enumerate(results["matches"]):
                formatted.append({
                    "id": match["id"],
                    "chunk_id": match["id"].split("#")[1],
                    "similarity_score": match["score"],
                    "metadata": match.get("metadata", {}),
                    "rank": i + 1,
                })
            
            return formatted
        except Exception as e:
            logger.error(f"Pinecone search error: {str(e)}")
            return []
    
    async def delete(self, vector_id: str, repository_id: str) -> bool:
        """Delete vector from Pinecone."""
        try:
            full_id = f"{repository_id}#{vector_id}"
            self.index.delete(ids=[full_id], namespace=repository_id)
            logger.info(f"Deleted vector {vector_id} from Pinecone")
            return True
        except Exception as e:
            logger.error(f"Pinecone delete error: {str(e)}")
            return False
