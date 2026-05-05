"""
Long-term Memory Store using ChromaDB
Stores and retrieves important conversation facts for each user
"""

import chromadb
from chromadb.utils import embedding_functions
import os
from datetime import datetime


class MemoryStore:
    """
    Long-term memory storage using ChromaDB with vector embeddings.
    Stores important facts from conversations and retrieves them when relevant.
    """
    
    def __init__(self, persist_directory: str = None):
        """
        Initialize the memory store.
        
        Args:
            persist_directory: Directory to persist ChromaDB data (optional)
        """
        # Use default embedding model (same as policy embeddings)
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        # Initialize Chroma client
        if persist_directory:
            self.client = chromadb.PersistentClient(path=persist_directory)
        else:
            self.client = chromadb.Client()
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="novahr_long_term_memory",
            embedding_function=self.embedding_function,
            metadata={"description": "Long-term memory for NovaHR conversations"}
        )
    
    def add_memory(self, user_id: str, text: str, metadata: dict = None):
        """
        Store a memory for a user.
        
        Args:
            user_id: User's ID (employee_id)
            text: The text to remember
            metadata: Optional additional metadata (e.g., intent, timestamp)
        """
        # Create unique ID using user_id, timestamp, and hash
        timestamp = datetime.now().isoformat()
        memory_id = f"{user_id}_{timestamp}_{hash(text)}"
        
        # Prepare metadata
        meta = {
            "user_id": str(user_id),
            "timestamp": timestamp
        }
        if metadata:
            meta.update(metadata)
        
        # Store in ChromaDB
        self.collection.add(
            documents=[text],
            metadatas=[meta],
            ids=[memory_id]
        )
        
        print(f"[MEMORY] Stored for user {user_id}: {text[:50]}...")
    
    def search_memory(self, user_id: str, query: str, n_results: int = 3, recency_boost: bool = True):
        """
        Retrieve relevant memories for a user based on query.
        Now includes recency boosting - recent memories ranked higher.
        
        Args:
            user_id: User's ID
            query: The query to search for
            n_results: Number of results to return
            recency_boost: Whether to boost recent memories (default: True)
            
        Returns:
            List of relevant memory texts
        """
        try:
            # Query ChromaDB (get more results for ranking)
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results * 3,  # Get 3x more for ranking
                where={"user_id": str(user_id)}
            )
            
            # Extract documents and metadata
            if results and results["documents"] and len(results["documents"]) > 0:
                documents = results["documents"][0]
                metadatas = results["metadatas"][0] if results["metadatas"] else []
                distances = results["distances"][0] if results["distances"] else []
                
                if not documents:
                    return []
                
                # Apply recency boosting
                if recency_boost and metadatas:
                    ranked_memories = self._rank_by_recency(
                        documents, metadatas, distances, n_results
                    )
                else:
                    ranked_memories = documents[:n_results]
                
                if ranked_memories:
                    print(f"[MEMORY] Retrieved {len(ranked_memories)} memories for user {user_id}")
                    return ranked_memories
            
            return []
            
        except Exception as e:
            print(f"[MEMORY] Search failed: {str(e)}")
            return []
    
    def _rank_by_recency(self, documents: list, metadatas: list, distances: list, n_results: int):
        """
        Rank memories by combining similarity score and recency.
        Recent memories get a boost in ranking.
        
        Formula: final_score = similarity_score * recency_multiplier
        
        Args:
            documents: List of memory texts
            metadatas: List of metadata dicts
            distances: List of similarity distances (lower = more similar)
            n_results: Number of results to return
            
        Returns:
            List of top N ranked memory texts
        """
        from datetime import datetime
        
        scored_memories = []
        
        for doc, meta, dist in zip(documents, metadatas, distances):
            # Convert distance to similarity (0-1, higher = more similar)
            similarity = 1 / (1 + dist)
            
            # Calculate recency multiplier
            timestamp_str = meta.get("timestamp", "")
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str)
                    age_days = (datetime.now() - timestamp).days
                    
                    # Recency multiplier: 1.0 for today, decays over time
                    # After 30 days: 0.5x, After 90 days: 0.25x
                    if age_days <= 7:
                        recency_multiplier = 1.0  # Last week: full weight
                    elif age_days <= 30:
                        recency_multiplier = 0.8  # Last month: 80%
                    elif age_days <= 90:
                        recency_multiplier = 0.5  # Last 3 months: 50%
                    else:
                        recency_multiplier = 0.3  # Older: 30%
                except Exception:
                    recency_multiplier = 0.5  # Default if timestamp parsing fails
            else:
                recency_multiplier = 0.5  # Default if no timestamp
            
            # Calculate final score
            final_score = similarity * recency_multiplier
            
            scored_memories.append({
                "document": doc,
                "score": final_score,
                "similarity": similarity,
                "recency_multiplier": recency_multiplier,
                "age_days": age_days if timestamp_str else None
            })
        
        # Sort by final score (descending)
        scored_memories.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top N documents
        return [mem["document"] for mem in scored_memories[:n_results]]
    
    def get_all_memories(self, user_id: str, limit: int = 10):
        """
        Get all memories for a user (most recent first).
        
        Args:
            user_id: User's ID
            limit: Maximum number of memories to return
            
        Returns:
            List of memory texts
        """
        try:
            results = self.collection.get(
                where={"user_id": str(user_id)},
                limit=limit
            )
            
            if results and results["documents"]:
                return results["documents"]
            
            return []
            
        except Exception as e:
            print(f"[MEMORY] Get all failed: {str(e)}")
            return []
    
    def clear_user_memories(self, user_id: str):
        """
        Clear all memories for a specific user.
        
        Args:
            user_id: User's ID
        """
        try:
            # Get all IDs for this user
            results = self.collection.get(
                where={"user_id": str(user_id)}
            )
            
            if results and results["ids"]:
                self.collection.delete(ids=results["ids"])
                print(f"[MEMORY] Cleared {len(results['ids'])} memories for user {user_id}")
        
        except Exception as e:
            print(f"[MEMORY] Clear failed: {str(e)}")
    
    def cleanup_old_memories(self, days: int = 30):
        """
        Delete memories older than specified days (TTL cleanup).
        Should be run periodically (e.g., daily cron job).
        
        Args:
            days: Delete memories older than this many days (default: 30)
        """
        from datetime import datetime, timedelta
        
        try:
            # Get all memories
            all_results = self.collection.get(
                include=["metadatas"]
            )
            
            if not all_results or not all_results["ids"]:
                print("[MEMORY CLEANUP] No memories to check")
                return
            
            cutoff_date = datetime.now() - timedelta(days=days)
            ids_to_delete = []
            
            # Check each memory's timestamp
            for memory_id, metadata in zip(all_results["ids"], all_results["metadatas"]):
                timestamp_str = metadata.get("timestamp", "")
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if timestamp < cutoff_date:
                            ids_to_delete.append(memory_id)
                    except Exception:
                        # If timestamp parsing fails, keep the memory
                        pass
            
            # Delete old memories
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                print(f"[MEMORY CLEANUP] Deleted {len(ids_to_delete)} memories older than {days} days")
            else:
                print(f"[MEMORY CLEANUP] No memories older than {days} days found")
        
        except Exception as e:
            print(f"[MEMORY CLEANUP] Failed: {str(e)}")
    
    def cleanup_by_user(self, user_id: str, days: int = 30):
        """
        Delete old memories for a specific user.
        
        Args:
            user_id: User's ID
            days: Delete memories older than this many days
        """
        from datetime import datetime, timedelta
        
        try:
            # Get user's memories
            results = self.collection.get(
                where={"user_id": str(user_id)},
                include=["metadatas"]
            )
            
            if not results or not results["ids"]:
                return
            
            cutoff_date = datetime.now() - timedelta(days=days)
            ids_to_delete = []
            
            for memory_id, metadata in zip(results["ids"], results["metadatas"]):
                timestamp_str = metadata.get("timestamp", "")
                if timestamp_str:
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if timestamp < cutoff_date:
                            ids_to_delete.append(memory_id)
                    except Exception:
                        pass
            
            if ids_to_delete:
                self.collection.delete(ids=ids_to_delete)
                print(f"[MEMORY CLEANUP] Deleted {len(ids_to_delete)} old memories for user {user_id}")
        
        except Exception as e:
            print(f"[MEMORY CLEANUP] Failed for user {user_id}: {str(e)}")
    
    def get_stats(self):
        """Get statistics about stored memories."""
        try:
            count = self.collection.count()
            return {
                "total_memories": count,
                "collection_name": self.collection.name
            }
        except Exception as e:
            print(f"[MEMORY] Stats failed: {str(e)}")
            return {"total_memories": 0, "error": str(e)}


# Global instance (lazy initialization)
_memory_store = None


def get_memory_store(persist_directory: str = None) -> MemoryStore:
    """
    Get the global memory store instance (singleton pattern).
    
    Args:
        persist_directory: Directory to persist data (optional)
        
    Returns:
        MemoryStore instance
    """
    global _memory_store
    if _memory_store is None:
        # Use data/long_term_memory by default
        if persist_directory is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            persist_directory = os.path.join(base_dir, "data", "long_term_memory")
        
        _memory_store = MemoryStore(persist_directory=persist_directory)
    
    return _memory_store
