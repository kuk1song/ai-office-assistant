"""
Persistence Manager - Knowledge Base State Persistence

Responsible for:
- FAISS index saving and loading
- Metadata persistence (file names, raw texts)
- Storage directory management
- State validation and recovery
"""

import os
import json
import shutil
from typing import Dict, List, Optional, Tuple
from langchain_community.vectorstores import FAISS


class PersistenceManager:
    """
    Manages persistence operations for the knowledge base.
    
    This class handles saving and loading of vector stores, metadata,
    and other knowledge base state to ensure data persistence across sessions.
    """
    
    def __init__(self, storage_dir: str = "persistent_storage"):
        """
        Initialize the persistence manager.
        
        Args:
            storage_dir: Directory for storing persistent data
        """
        self.storage_dir = storage_dir
        self.faiss_index_path = os.path.join(storage_dir, "vector_store")
        self.metadata_path = os.path.join(storage_dir, "metadata.json")
        
        # Ensure storage directory exists
        os.makedirs(storage_dir, exist_ok=True)
    
    def save_knowledge_base(self, vector_store: FAISS, file_names: List[str], 
                          raw_texts: Dict[str, str]) -> None:
        """
        Save the complete knowledge base state to disk.
        
        Args:
            vector_store: FAISS vector store to save
            file_names: List of processed file names
            raw_texts: Dictionary mapping file names to raw content
        """
        print("💾 Saving knowledge base to disk...")
        
        try:
            # Save FAISS vector store
            if vector_store:
                vector_store.save_local(self.faiss_index_path)
                print(f"  📚 Vector store saved to {self.faiss_index_path}")
            
            # Save metadata
            metadata = {
                "file_names": file_names,
                "raw_texts": raw_texts,
                "vector_store_exists": vector_store is not None,
                "document_count": len(file_names)
            }
            
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            print(f"  📋 Metadata saved to {self.metadata_path}")
            print(f"✅ Knowledge base saved successfully ({len(file_names)} documents)")
            
        except Exception as e:
            print(f"❌ Error saving knowledge base: {str(e)}")
            raise
    
    def load_knowledge_base(self, embedding_provider) -> Tuple[Optional[FAISS], List[str], Dict[str, str]]:
        """
        Load the complete knowledge base state from disk.
        
        Args:
            embedding_provider: Embedding provider for loading vector store
            
        Returns:
            Tuple of (vector_store, file_names, raw_texts)
        """
        print("📂 Loading knowledge base from disk...")
        
        # Check if metadata exists
        if not os.path.exists(self.metadata_path):
            print("No existing knowledge base found")
            return None, [], {}
        
        try:
            # Load metadata
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            file_names = metadata.get("file_names", [])
            raw_texts = metadata.get("raw_texts", {})
            vector_store_exists = metadata.get("vector_store_exists", False)
            
            # Load vector store if it exists
            vector_store = None
            if vector_store_exists and os.path.exists(self.faiss_index_path):
                embeddings_model = embedding_provider.get_embeddings()
                vector_store = FAISS.load_local(
                    self.faiss_index_path, 
                    embeddings_model,
                    allow_dangerous_deserialization=True
                )
                print(f"  📚 Vector store loaded from {self.faiss_index_path}")
            
            print(f"  📋 Metadata loaded: {len(file_names)} documents")
            print(f"✅ Knowledge base loaded successfully")
            
            return vector_store, file_names, raw_texts
            
        except Exception as e:
            print(f"❌ Error loading knowledge base: {str(e)}")
            print("Knowledge base may be corrupted, starting fresh")
            return None, [], {}
    
    def knowledge_base_exists(self) -> bool:
        """
        Check if a knowledge base exists on disk.
        
        Returns:
            True if knowledge base exists, False otherwise
        """
        return (os.path.exists(self.metadata_path) and 
                os.path.exists(self.faiss_index_path))
    
    def get_knowledge_base_info(self) -> Dict:
        """
        Get information about the stored knowledge base.
        
        Returns:
            Dictionary with knowledge base information
        """
        if not os.path.exists(self.metadata_path):
            return {"exists": False}
        
        try:
            with open(self.metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            return {
                "exists": True,
                "document_count": len(metadata.get("file_names", [])),
                "file_names": metadata.get("file_names", []),
                "vector_store_exists": metadata.get("vector_store_exists", False),
                "storage_size": self._get_storage_size()
            }
            
        except Exception as e:
            return {"exists": False, "error": str(e)}
    
    def clear_knowledge_base(self) -> None:
        """
        Delete all persistent knowledge base data.
        """
        print("🗑️ Clearing knowledge base storage...")
        
        try:
            if os.path.exists(self.storage_dir):
                shutil.rmtree(self.storage_dir)
                print("✅ Knowledge base storage cleared")
            
            # Recreate empty storage directory
            os.makedirs(self.storage_dir, exist_ok=True)
            
        except Exception as e:
            print(f"❌ Error clearing storage: {str(e)}")
            raise
    
    def _get_storage_size(self) -> str:
        """
        Calculate the total size of stored knowledge base files.
        
        Returns:
            Human-readable storage size string
        """
        total_size = 0
        
        try:
            for root, dirs, files in os.walk(self.storage_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    if os.path.exists(file_path):
                        total_size += os.path.getsize(file_path)
            
            # Convert to human-readable format
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            elif total_size < 1024 * 1024 * 1024:
                return f"{total_size / (1024 * 1024):.1f} MB"
            else:
                return f"{total_size / (1024 * 1024 * 1024):.1f} GB"
                
        except Exception:
            return "Unknown"
    
    def backup_knowledge_base(self, backup_name: str) -> bool:
        """
        Create a backup of the current knowledge base.
        
        Args:
            backup_name: Name for the backup
            
        Returns:
            True if backup was successful, False otherwise
        """
        if not self.knowledge_base_exists():
            print("No knowledge base to backup")
            return False
        
        backup_dir = f"{self.storage_dir}_backup_{backup_name}"
        
        try:
            if os.path.exists(backup_dir):
                shutil.rmtree(backup_dir)
            
            shutil.copytree(self.storage_dir, backup_dir)
            print(f"✅ Knowledge base backed up to {backup_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Error creating backup: {str(e)}")
            return False
