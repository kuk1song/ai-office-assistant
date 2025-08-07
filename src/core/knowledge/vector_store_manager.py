"""
Vector Store Manager - FAISS Vector Storage Management

Responsible for:
- FAISS vector store creation and management
- Document embedding and indexing
- Vector search and retrieval operations
- Vector store serialization and loading
"""

from typing import List, Optional, Dict, Any
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document


class VectorStoreManager:
    """
    Manages FAISS vector store operations for the knowledge base.
    
    This class handles all vector storage operations including creation,
    updates, search, and persistence of the vector index.
    """
    
    def __init__(self, embedding_provider):
        """
        Initialize the vector store manager.
        
        Args:
            embedding_provider: Embedding provider for vectorization
        """
        self.embedding_provider = embedding_provider
        self.vector_store: Optional[FAISS] = None
    
    def create_vector_store(self, documents: List[Document]) -> FAISS:
        """
        Create a new FAISS vector store from documents.
        
        Args:
            documents: List of LangChain Document objects
            
        Returns:
            Created FAISS vector store
        """
        if not documents:
            raise ValueError("Cannot create vector store with empty document list")
        
        print("🔤 Creating embeddings...")
        embeddings_model = self.embedding_provider.get_embeddings()
        
        self.vector_store = FAISS.from_documents(documents, embeddings_model)
        
        print(f"✅ Vector store created with {len(documents)} document chunks")
        return self.vector_store
    
    def add_documents_to_store(self, documents: List[Document]) -> None:
        """
        Add new documents to an existing vector store.
        
        Args:
            documents: List of new documents to add
            
        Raises:
            ValueError: If no existing vector store is found
        """
        if not self.vector_store:
            raise ValueError("No existing vector store found. Create one first.")
        
        if not documents:
            print("No valid documents to add")
            return
        
        print(f"📝 Adding {len(documents)} new document chunks to vector store...")
        self.vector_store.add_documents(documents)
        
        print("✅ Documents added to vector store successfully")
    
    def delete_documents_by_source(self, source_filename: str) -> bool:
        """
        Delete all document chunks from a specific source file.
        
        Args:
            source_filename: Name of the source file to remove
            
        Returns:
            True if documents were found and deleted, False otherwise
        """
        if not self.vector_store:
            print("No vector store available")
            return False
        
        try:
            # Get all document IDs that match the source
            all_docs = self.vector_store.docstore._dict
            ids_to_delete = []
            
            for doc_id, doc in all_docs.items():
                if hasattr(doc, 'metadata') and doc.metadata.get('source') == source_filename:
                    ids_to_delete.append(doc_id)
            
            if not ids_to_delete:
                print(f"No documents found for source: {source_filename}")
                return False
            
            # Delete the documents
            self.vector_store.delete(ids_to_delete)
            print(f"🗑️ Deleted {len(ids_to_delete)} chunks from {source_filename}")
            return True
            
        except Exception as e:
            print(f"Error deleting documents from {source_filename}: {str(e)}")
            return False
    
    def search_similar_documents(self, query: str, k: int = 8) -> List[Document]:
        """
        Search for similar documents in the vector store.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of similar documents
        """
        if not self.vector_store:
            raise ValueError("No vector store available for search")
        
        return self.vector_store.similarity_search(query, k=k)
    
    def get_retriever(self, search_kwargs: Dict[str, Any] = None):
        """
        Get a retriever for the vector store.
        
        Args:
            search_kwargs: Optional search configuration
            
        Returns:
            Vector store retriever
        """
        if not self.vector_store:
            raise ValueError("No vector store available")
        
        if search_kwargs is None:
            search_kwargs = {"k": 8}
        
        return self.vector_store.as_retriever(search_kwargs=search_kwargs)
    
    def get_vector_store(self) -> Optional[FAISS]:
        """
        Get the current vector store instance.
        
        Returns:
            Current FAISS vector store or None
        """
        return self.vector_store
    
    def set_vector_store(self, vector_store: FAISS) -> None:
        """
        Set the vector store instance (used when loading from disk).
        
        Args:
            vector_store: FAISS vector store to set
        """
        self.vector_store = vector_store
    
    def get_document_count(self) -> int:
        """
        Get the total number of document chunks in the vector store.
        
        Returns:
            Number of documents in the store
        """
        if not self.vector_store:
            return 0
        
        return len(self.vector_store.docstore._dict)
    
    def get_all_sources(self) -> List[str]:
        """
        Get a list of all unique source files in the vector store.
        
        Returns:
            List of unique source filenames
        """
        if not self.vector_store:
            return []
        
        sources = set()
        for doc in self.vector_store.docstore._dict.values():
            if hasattr(doc, 'metadata') and 'source' in doc.metadata:
                sources.add(doc.metadata['source'])
        
        return sorted(list(sources))
