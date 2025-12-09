# AVOID MODIFYING THIS FILE EXCEPT YOU KNOW WHAT YOU ARE DOING 

"""
ChromaDB RAG system for Pixella.

This module provides a Retrieval-Augmented Generation (RAG) system
using ChromaDB for document storage and retrieval, integrated with
Google Generative AI for generating document embeddings.

"""

import os
import logging
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any, TypedDict, cast
import json
import chromadb
from chromadb.api.types import Embedding
from pydantic import SecretStr
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from config import ENV_PATH, get_config, set_config


logger = logging.getLogger(__name__)

class DocumentInput(TypedDict):
    content: str
    source: Optional[str]
    metadata: Optional[Dict[str, Any]]


class ChromaDBRAG:
    """
    Retrieval-Augmented Generation using ChromaDB for document storage and retrieval
    """

    def __init__(self, db_path: str = "./db/chroma", collection_name: str = "pixella"):
        """
        Initialize ChromaDB RAG system
        
        Args:
            db_path: Path to store ChromaDB data
            collection_name: Name of the collection to use
        """
        self.db_path = db_path
        self.collection_name = collection_name

        # Create db directory if it doesn't exist
        Path(db_path).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client
        try:
            self.client = chromadb.PersistentClient(path=self.db_path)
            logger.debug("ChromaDB client initialized at %s", self.db_path)
        except Exception as exc: # Catching specific exception
            logger.error("Failed to initialize ChromaDB: %s", exc)
            raise

        # Initialize embeddings model (using Google Generative AI)
        try:
            config = get_config()
            google_api_key = config.get("GOOGLE_API_KEY")
            current_embedding_model = get_current_embedding_model()
            
            if not google_api_key:
                raise ValueError("GOOGLE_API_KEY not found in config.")

            self.embeddings = GoogleGenerativeAIEmbeddings(
                model=current_embedding_model,
                google_api_key=SecretStr(google_api_key)
            )
            logger.debug("Google Generative AI embeddings model: %s", current_embedding_model)
        except Exception as exc: # Catching specific exception
            logger.warning("Failed to initialize embeddings: %s", exc)
            self.embeddings = None

        # Get or create collection
        try:
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            logger.debug("Collection '%s' initialized", collection_name)
        except Exception as exc: # Catching specific exception
            logger.error("Failed to get/create collection: %s", exc)
            raise

        # Text splitter for chunking documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            separators=["\n\n", "\n", " ", ""]
        )

    def add_documents(self, documents: List[DocumentInput]) -> int:
        """
        Add documents to the collection.
        Uses batching for efficiency and falls back to individual adds on error.
        
        Args:
            documents: List of dicts with 'content' and optional 'metadata' keys
        
        Returns:
            Number of document chunks added
        """
        if not documents:
            logger.warning("No documents provided to add.")
            return 0

        if not self.embeddings:
            logger.error("Embeddings model not initialized. Please ensure GOOGLE_API_KEY is set in your .env file and a valid EMBEDDING_MODEL is selected.")
            return 0

        chunks_to_add = []
        for idx, doc in enumerate(documents):
            content = doc.get("content", "")
            if not content:
                logger.warning("Document %d has no content, skipping.", idx)
                continue

            chunks = self.text_splitter.split_text(content)
            for chunk_idx, chunk in enumerate(chunks):
                chunk_hash = hashlib.sha256(chunk.encode('utf-8')).hexdigest()
                doc_id = f"doc_{chunk_hash}"

                chunks_to_add.append({
                    "id": doc_id,
                    "document": chunk,
                    "metadata": {
                        **(doc.get("metadata") or {}),
                        "source": doc.get("source", "unknown"),
                        "chunk_index": chunk_idx,
                    }
                })

        if not chunks_to_add:
            return 0

        try:
            ids = [c["id"] for c in chunks_to_add]
            docs = [c["document"] for c in chunks_to_add]
            metadatas = [c["metadata"] for c in chunks_to_add]

            # Embed and add in a single batch
            embeddings = cast(List[Embedding], self.embeddings.embed_documents(docs))
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=docs,
                metadatas=metadatas
            )

            added_count = len(ids)
            logger.info("Successfully added %d document chunks to collection.", added_count)
            return added_count

        except Exception as exc: # Catching specific exception
            logger.error(
                "Batch add failed: %s. Falling back to individual additions.", exc
            )
            # Fallback to adding one by one for resilience
            added_count = 0
            for chunk_data in chunks_to_add:
                try:
                    embedding = self.embeddings.embed_query(chunk_data["document"])
                    self.collection.add(
                        ids=[chunk_data["id"]],
                        embeddings=[embedding],
                        documents=[chunk_data["document"]],
                        metadatas=[chunk_data["metadata"]]
                    )
                    added_count += 1
                except Exception as inner_exc: # Catching specific exception
                    # Log error for the specific chunk and continue
                    logger.error(
                        "Failed to add individual chunk %s: %s", chunk_data['id'],
                          inner_exc)

            logger.info("Individually added %d chunks after batch failure.", added_count)
            return added_count

    def add_text(self, text: str, source: str = "user_input") -> int:
        """
        Add raw text to the collection
        
        Args:
            text: Text content to add
            source: Source/label for the text
        
        Returns:
            Number of chunks added
        """
        return self.add_documents([{
            "content": text,
            "source": source,
            "metadata": {"type": "user_text"}
        }])

    def add_file(self, file_path: str) -> int:
        """
        Add contents of a file to the collection
        
        Args:
            file_path: Path to the file
        
        Returns:
            Number of chunks added
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return self.add_documents([{
                "content": content,
                "source": os.path.basename(file_path),
                "metadata": {"type": "file", "path": file_path}
            }])
        except FileNotFoundError:
            logger.error(f"Error adding file {file_path}: File not found.")
            return 0
        except Exception as exc: # Catching specific exception
            logger.error(f"Error reading file {file_path}: {exc}")
            return 0

    def query(
        self,
        query_text: str,
        top_k: int = 3,
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Query the collection for similar documents
        
        Args:
            query_text: Text to query
            top_k: Number of top results to return
            threshold: Similarity threshold (0-1)
        
        Returns:
            List of similar documents with metadata and distance
        """
        if not self.embeddings:
            logger.error("Embeddings model not initialized. Please ensure GOOGLE_API_KEY is set in your .env file and a valid EMBEDDING_MODEL is selected.")
            return []

        try:
            # Generate query embedding
            query_embedding = self.embeddings.embed_query(query_text)

            # Query the collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                include=["distances", "documents", "metadatas"]
            )

            # Safely extract documents, distances, and metadatas
            documents = results.get("documents")
            distances = results.get("distances")
            metadatas = results.get("metadatas")

            if not documents or not documents[0]:
                logger.debug("No results found for query or documents are empty.")
                return []

            # Format results
            formatted_results = []
            for i, doc in enumerate(documents[0]):
                # Safely get distance
                distance = (
                    distances[0][i]
                    if distances and distances[0] and len(distances[0]) > i
                    else 0.0
                )
                similarity = 1 - distance  # Convert distance to similarity

                # Skip if below threshold
                if similarity < threshold:
                    logger.debug("Skipping result with similarity %f", similarity)
                    continue

                # Safely get metadata
                metadata = (
                    metadatas[0][i]
                    if metadatas and metadatas[0] and len(metadatas[0]) > i
                    else {}
                )

                formatted_results.append({
                    "content": doc,
                    "similarity": similarity,
                    "distance": distance,
                    "metadata": metadata
                })

            logger.debug("Found %d results for query", len(formatted_results))
            return formatted_results

        except Exception as exc: # Catching specific exception
            logger.error("Error querying collection: %s", exc)
            return []

    def query_with_context(self, query_text: str, top_k: int = 3) -> str:
        """
        Query and return formatted context for LLM
        
        Args:
            query_text: Text to query
            top_k: Number of top results
        
        Returns:
            Formatted context string for use with LLM
        """
        results = self.query(query_text, top_k)

        if not results:
            return ""

        context = "## Retrieved Context:\n\n"
        for i, result in enumerate(results, 1):
            source = result.get("metadata", {}).get("source", "unknown")
            similarity = result.get("similarity", 0)
            context += f"### Source {i}: {source} (Relevance: {similarity:.2%})\n"
            context += f"{result['content']}\n\n"

        return context

    def get_collection_info(self) -> Dict:
        """
        Get information about the current collection
        
        Returns:
            Dictionary with collection statistics
        """
        try:
            count = self.collection.count()
            metadata = self.collection.metadata

            return {
                "name": self.collection_name,
                "count": count,
                "metadata": metadata,
                "db_path": self.db_path
            }
        except Exception as exc: # Catching specific exception
            logger.error("Error getting collection info: %s", exc)
            return {}

    def delete_collection(self) -> bool:
        """
        Delete the current collection
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.delete_collection(name=self.collection_name)
            logger.info("Deleted collection '%s'", self.collection_name)

            # Re-create empty collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            return True
        except Exception as exc: # Catching specific exception
            logger.error("Error deleting collection: %s", exc)
            return False

    def clear_all(self) -> bool:
        """
        Clear all data from the database
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Delete and recreate collection
            return self.delete_collection()
        except Exception as exc: # Catching specific exception
            logger.error("Error clearing database: %s", exc)
            return False

    def export_collection(self, output_path: str) -> bool:
        """
        Export collection data to a file
        
        Args:
            output_path: Path to export to
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Get all documents in collection
            all_docs = self.collection.get()

            export_data = {
                "collection": self.collection_name,
                "count": len(all_docs.get("ids", [])),
                "documents": {
                    "ids": all_docs.get("ids", []),
                    "documents": all_docs.get("documents", []),
                    "metadatas": all_docs.get("metadatas", [])
                }
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2)

            logger.info("Exported collection to %s", output_path)
            return True
        except Exception as exc: # Catching specific exception
            logger.error("Error exporting collection: %s", exc)
            return False


# Global RAG instance
_RAG_INSTANCE = None # Renamed to conform to UPPER_CASE naming style


def get_rag() -> Optional[ChromaDBRAG]:
    """
    Get or create the global RAG instance
    
    Returns:
        ChromaDBRAG instance or None if initialization fails
    """
    global _RAG_INSTANCE # Use the renamed global variable

    try:
        if _RAG_INSTANCE is None:
            config = get_config()
            google_api_key = config.get("GOOGLE_API_KEY")
            if not google_api_key:
                logger.error("GOOGLE_API_KEY not found in config. RAG cannot be initialized without an API key.")
                return None
            db_path = config.get("DB_PATH", "./db/chroma")
            _RAG_INSTANCE = ChromaDBRAG(db_path)
        return _RAG_INSTANCE
    except Exception as exc: # Catching specific exception
        logger.error("Failed to initialize RAG: %s", exc)
        return None


def reset_rag():
    """Reset the global RAG instance"""

    global _RAG_INSTANCE # Use the renamed global variable
    _RAG_INSTANCE = None


def list_available_embedding_models() -> dict[str, str]:
    """
    List available embedding models.
    
    Returns:
        Dictionary of available models with descriptions
    """
    return {
        "models/embedding-001": "Google's default embedding model.",
        "models/text-embedding-004": "Google's latest, optimized embedding model.",
    }


def get_current_embedding_model() -> str:
    """
    Get the current embedding model from config.
    
    Returns:
        The current embedding model name
    """
    config = get_config()
    return config.get("EMBEDDING_MODEL", "models/embedding-001")


def set_embedding_model(model_name: str) -> None:
    """
    Set the embedding model in the config.
    
    Args:
        model_name: The name of the model to set
    """
    set_config("EMBEDDING_MODEL", model_name)
    if _RAG_INSTANCE: # Use the renamed global variable
        config = get_config()
        google_api_key = config.get("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in config.")

        _RAG_INSTANCE.embeddings = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=SecretStr(google_api_key)
        )
        logger.info("RAG embedding model changed to: %s", model_name)

