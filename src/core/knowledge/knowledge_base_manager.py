"""
Knowledge Base Manager - Unified Knowledge Base Lifecycle Management

Responsible for:
- Orchestrating document processing, vector storage, and persistence
- Providing unified API for all knowledge base operations
- Managing knowledge base state and metadata
- Coordinating between different knowledge base components
"""

from typing import List, Dict, Optional, Tuple
from .document_processor import DocumentProcessor
from .vector_store_manager import VectorStoreManager
from .persistence_manager import PersistenceManager


class KnowledgeBaseManager:
    """
    Unified manager for all knowledge base operations.
    
    This class provides a single point of access for all knowledge base
    functionality and coordinates between document processing, vector storage,
    and persistence components.
    """
    
    def __init__(self, ai_model_manager, storage_dir: str = "persistent_storage"):
        """
        Initialize the knowledge base manager.
        
        Args:
            ai_model_manager: AI model manager for embedding operations
            storage_dir: Directory for persistent storage
        """
        self.ai_model_manager = ai_model_manager
        
        # Initialize component managers
        self.document_processor = DocumentProcessor()
        self.vector_store_manager = VectorStoreManager(
            ai_model_manager.get_embedding_provider()
        )
        self.persistence_manager = PersistenceManager(storage_dir)
        
        # State management
        self.file_names: List[str] = []
        self.raw_texts: Dict[str, str] = {}
        self._is_initialized = False
    
    def create_knowledge_base(self, uploaded_files: List) -> List[str]:
        """
        Create a new knowledge base from uploaded files.
        
        Args:
            uploaded_files: List of Streamlit UploadedFile objects
            
        Returns:
            List of file names that failed to process
        """
        print("🔧 Creating knowledge base...")
        
        if not uploaded_files:
            raise ValueError("No files provided for knowledge base creation")
        
        # Step 1: Process documents
        docs_for_rag, failed_files = self.document_processor.process_uploaded_files(uploaded_files)
        
        if not docs_for_rag:
            raise ValueError("❌ No files could be processed successfully. Please check your file formats and content.")
        
        # Step 2: Create text chunks
        text_splitter = self.document_processor.get_text_splitter(docs_for_rag)
        split_docs = self.document_processor.create_valid_chunks(text_splitter, docs_for_rag)
        
        # Step 3: Create vector store
        vector_store = self.vector_store_manager.create_vector_store(split_docs)
        
        # Step 4: Update state
        self.file_names = [file.name for file in uploaded_files if file.name not in failed_files]
        self.raw_texts = self.document_processor.extract_raw_texts(uploaded_files, docs_for_rag)
        self._is_initialized = True
        
        # Step 5: Save to disk
        self.save_knowledge_base()
        
        print(f"✅ Knowledge base created with {len(self.file_names)} documents!")
        return failed_files
    
    def add_documents(self, uploaded_files: List) -> List[str]:
        """
        Add new documents to existing knowledge base.
        
        Args:
            uploaded_files: List of new files to add
            
        Returns:
            List of file names that failed to process
        """
        print("🔧 Adding documents to existing knowledge base...")
        
        if not self._is_initialized:
            raise ValueError("No existing knowledge base found. Please create one first.")
        
        # Step 1: Process new documents
        docs_for_rag, failed_files = self.document_processor.process_uploaded_files(uploaded_files)
        
        if not docs_for_rag:
            print("No valid documents to add")
            return [file.name for file in uploaded_files]
        
        # Step 2: Create chunks for new documents
        text_splitter = self.document_processor.get_text_splitter(docs_for_rag)
        split_docs = self.document_processor.create_valid_chunks(text_splitter, docs_for_rag)
        
        # Step 3: Add to vector store
        self.vector_store_manager.add_documents_to_store(split_docs)
        
        # Step 4: Update state
        new_file_names = [file.name for file in uploaded_files if file.name not in failed_files]
        self.file_names.extend(new_file_names)
        
        new_raw_texts = self.document_processor.extract_raw_texts(uploaded_files, docs_for_rag)
        self.raw_texts.update(new_raw_texts)
        
        # Step 5: Save updated state
        self.save_knowledge_base()
        
        print(f"✅ Added {len(new_file_names)} documents to knowledge base!")
        return failed_files
    
    def delete_document(self, file_name: str) -> bool:
        """
        Delete a document from the knowledge base.
        
        Args:
            file_name: Name of the file to delete
            
        Returns:
            True if document was found and deleted, False otherwise
        """
        if not self._is_initialized:
            print("No knowledge base available")
            return False
        
        if file_name not in self.file_names:
            print(f"Document '{file_name}' not found in knowledge base")
            return False
        
        # Remove from vector store
        success = self.vector_store_manager.delete_documents_by_source(file_name)
        
        if success:
            # Update state
            self.file_names.remove(file_name)
            if file_name in self.raw_texts:
                del self.raw_texts[file_name]
            
            # Save updated state
            self.save_knowledge_base()
            
            print(f"✅ Document '{file_name}' deleted from knowledge base")
            return True
        
        return False
    
    def load_knowledge_base(self) -> bool:
        """
        Load existing knowledge base from disk.
        
        Returns:
            True if knowledge base was loaded successfully, False otherwise
        """
        vector_store, file_names, raw_texts = self.persistence_manager.load_knowledge_base(
            self.ai_model_manager.get_embedding_provider()
        )
        
        if vector_store is not None:
            self.vector_store_manager.set_vector_store(vector_store)
            self.file_names = file_names
            self.raw_texts = raw_texts
            self._is_initialized = True
            
            print(f"✅ Knowledge base loaded: {len(file_names)} documents")
            return True
        
        return False
    
    def save_knowledge_base(self) -> None:
        """Save current knowledge base state to disk."""
        if not self._is_initialized:
            print("No knowledge base to save")
            return
        
        vector_store = self.vector_store_manager.get_vector_store()
        self.persistence_manager.save_knowledge_base(
            vector_store, self.file_names, self.raw_texts
        )
    
    def clear_knowledge_base(self) -> None:
        """Clear all knowledge base data."""
        self.persistence_manager.clear_knowledge_base()
        self.file_names = []
        self.raw_texts = {}
        self.vector_store_manager.set_vector_store(None)
        self._is_initialized = False
        
        print("✅ Knowledge base cleared")
    
    def get_vector_store_retriever(self, search_kwargs: Dict = None):
        """
        Get a retriever for the vector store.
        
        Args:
            search_kwargs: Optional search configuration
            
        Returns:
            Vector store retriever for RAG operations
        """
        return self.vector_store_manager.get_retriever(search_kwargs)
    
    def search_documents(self, query: str, k: int = 8):
        """
        Search for relevant documents.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of relevant documents
        """
        return self.vector_store_manager.search_similar_documents(query, k)
    
    def get_file_names(self) -> List[str]:
        """Get list of all file names in the knowledge base."""
        return self.file_names.copy()
    
    def get_raw_text(self, file_name: str) -> Optional[str]:
        """
        Get raw text content for a specific file.
        
        Args:
            file_name: Name of the file
            
        Returns:
            Raw text content or None if not found
        """
        return self.raw_texts.get(file_name)
    
    def get_all_raw_texts(self) -> Dict[str, str]:
        """Get all raw text contents."""
        return self.raw_texts.copy()
    
    def is_initialized(self) -> bool:
        """Check if knowledge base is initialized and ready."""
        return self._is_initialized
    
    def get_knowledge_base_info(self) -> Dict:
        """
        Get comprehensive information about the knowledge base.
        
        Returns:
            Dictionary with knowledge base statistics and information
        """
        base_info = self.persistence_manager.get_knowledge_base_info()
        
        if self._is_initialized:
            base_info.update({
                "initialized": True,
                "current_file_count": len(self.file_names),
                "current_files": self.file_names,
                "vector_store_document_count": self.vector_store_manager.get_document_count(),
                "raw_text_size": sum(len(text) for text in self.raw_texts.values())
            })
        else:
            base_info.update({
                "initialized": False,
                "current_file_count": 0,
                "current_files": []
            })
        
        return base_info
