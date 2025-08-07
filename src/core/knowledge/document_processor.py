"""
Document Processor - Document Processing and Text Splitting

Responsible for:
- Document parsing using DocumentParser
- Text splitting with intelligent chunk sizing
- Content validation and filtering
- Metadata management
"""

from typing import List, Tuple, Dict, Any
from ..parser import DocumentParser
from langchain.text_splitter import RecursiveCharacterTextSplitter


class DocumentProcessor:
    """
    Handles all document processing operations for the knowledge base.
    
    This class encapsulates document parsing, text splitting, and validation
    logic, providing a clean interface for knowledge base management.
    """
    
    def __init__(self):
        """Initialize the document processor."""
        self.min_chunk_length = 10  # Minimum viable chunk length
    
    def process_uploaded_files(self, uploaded_files: List) -> Tuple[List[Tuple[str, Dict]], List[str]]:
        """
        Process a list of uploaded files and extract their content.
        
        Args:
            uploaded_files: List of Streamlit UploadedFile objects
            
        Returns:
            Tuple of (docs_for_rag, failed_files) where:
            - docs_for_rag: List of (text_content, metadata) tuples
            - failed_files: List of filenames that couldn't be processed
        """
        docs_for_rag = []
        failed_files = []
        
        for file in uploaded_files:
            print(f"📄 Processing: {file.name}")
            
            # Save the uploaded file to a temporary location
            try:
                with open(file.name, "wb") as f:
                    f.write(file.getvalue())
                
                # Parse the document
                parsed_result = DocumentParser.parse_document(file.name)
                
                if "error" in parsed_result:
                    print(f"  ❌ Failed to parse {file.name}: {parsed_result['error']}")
                    failed_files.append(file.name)
                    continue
                
                text = parsed_result["content"]
                
                # Validate content
                if not self._is_valid_content(text):
                    print(f"  - {file.name} contains no readable text (may be image-only or OCR failed)")
                    failed_files.append(file.name)
                    continue
                
                print(f"  ✅ Extracted {len(text)} characters")
                docs_for_rag.append((text, {"source": file.name}))
                
            except Exception as e:
                print(f"  ❌ Error processing {file.name}: {str(e)}")
                failed_files.append(file.name)
            
            finally:
                # Clean up temporary file
                try:
                    import os
                    if os.path.exists(file.name):
                        os.remove(file.name)
                except:
                    pass  # Ignore cleanup errors
        
        return docs_for_rag, failed_files
    
    def _is_valid_content(self, text: str) -> bool:
        """
        Validate if the extracted text is meaningful.
        
        Args:
            text: Text content to validate
            
        Returns:
            True if content is valid, False otherwise
        """
        if not text:
            return False
        
        if text.startswith("=== Document contains only images with no readable text ==="):
            return False
        
        # Check for minimum meaningful content
        if len(text.strip()) < self.min_chunk_length:
            return False
        
        return True
    
    def get_text_splitter(self, docs_for_rag: List = None) -> RecursiveCharacterTextSplitter:
        """
        Create an intelligent text splitter based on document characteristics.
        
        Args:
            docs_for_rag: Optional list of documents to analyze for optimal splitting
            
        Returns:
            Configured RecursiveCharacterTextSplitter
        """
        # Default configuration
        chunk_size = 1500
        overlap = 300
        
        # Analyze documents to optimize chunk size if provided
        if docs_for_rag:
            total_length = sum(len(doc[0]) for doc in docs_for_rag)
            avg_doc_length = total_length / len(docs_for_rag) if docs_for_rag else 0
            
            print(f"📊 Document analysis: {len(docs_for_rag)} docs, avg length: {avg_doc_length:.0f} chars")
            
            # Adjust chunk size based on document characteristics
            if avg_doc_length < 2000:
                # Short documents - smaller chunks
                chunk_size = 800
                overlap = 200
                print("🔧 Using smaller chunks for short documents")
            elif avg_doc_length > 10000:
                # Long documents - larger chunks  
                chunk_size = 2000
                overlap = 400
                print("🔧 Using larger chunks for long documents")
            
        print(f"📏 Text splitting: chunk_size={chunk_size}, overlap={overlap}")
        
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size, 
            chunk_overlap=overlap
        )
    
    def create_valid_chunks(self, text_splitter: RecursiveCharacterTextSplitter, 
                          docs_for_rag: List) -> List:
        """
        Create and validate document chunks, filtering out empty or meaningless ones.
        
        Args:
            text_splitter: Configured text splitter
            docs_for_rag: List of (text, metadata) tuples
            
        Returns:
            List of valid LangChain Document objects
        """
        split_docs = text_splitter.create_documents(
            [doc[0] for doc in docs_for_rag],
            metadatas=[doc[1] for doc in docs_for_rag]
        )
        
        # Filter out invalid chunks
        valid_chunks = [
            doc for doc in split_docs 
            if len(doc.page_content.strip()) > self.min_chunk_length
        ]
        
        if not valid_chunks:
            raise ValueError("No meaningful content chunks could be created from the documents.")
        
        if len(valid_chunks) < len(split_docs):
            filtered_count = len(split_docs) - len(valid_chunks)
            print(f"🧹 Filtered out {filtered_count} empty or very small chunks")
        
        print(f"📝 Created {len(valid_chunks)} valid chunks")
        return valid_chunks
    
    def extract_raw_texts(self, uploaded_files: List, docs_for_rag: List) -> Dict[str, str]:
        """
        Extract raw text mapping for files that were successfully processed.
        
        Args:
            uploaded_files: Original list of uploaded files
            docs_for_rag: Successfully processed documents
            
        Returns:
            Dictionary mapping filename to raw text content
        """
        raw_texts = {}
        processed_sources = {doc[1]["source"] for doc in docs_for_rag}
        
        for file in uploaded_files:
            if file.name in processed_sources:
                # Find the corresponding document content
                for text, metadata in docs_for_rag:
                    if metadata["source"] == file.name:
                        raw_texts[file.name] = text
                        break
        
        return raw_texts
