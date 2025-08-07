"""
This module contains the core Retrieval-Augmented Generation (RAG) engine.
"""
import os
import json
from typing import List, Dict
from .parser import DocumentParser
from .tools import create_all_tools

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain.agents import AgentExecutor, create_openai_tools_agent
import shutil

# --- STORAGE CONFIGURATION ---
STORAGE_DIR = "persistent_storage"
FAISS_INDEX_PATH = os.path.join(STORAGE_DIR, "vector_store")
METADATA_PATH = os.path.join(STORAGE_DIR, "metadata.json")


# --- AGENT SYSTEM PROMPT ---
AGENT_SYSTEM_PROMPT = """
You are an expert AI assistant specializing in Communication Engineering.
Your primary goal is to assist users by analyzing technical documents and performing relevant calculations.
You have access to a specialized set of tools to help you. The user has uploaded the following files: {file_list}

Here is your operational guide:

1.  **For General Questions**: Use the `knowledge_base_qa` tool to answer questions about the contents of the documents. This is your primary tool for information retrieval.

2.  **For Summarization**: Use the `summarize_document` tool ONLY when the user explicitly asks for a summary of a specific file.

3.  **For Calculations (e.g., Link Budget)**: This is a multi-step process.
    *   **Step A: Identify Parameters**: First, understand what parameters are needed for the calculation (e.g., for a link budget, you need distance, power, gain, loss, frequency).
    *   **Step B: Gather Data**: If the user has not provided all parameters, use the `extract_technical_specifications` tool to find the missing information from the uploaded documents. You may need to call this tool multiple times for different documents.
    *   **Step C: Execute Calculation**: Once you have all the necessary parameters, use the `calculate_link_budget` tool to perform the calculation.
    *   **Step D: Present Results**: Clearly present the final calculated results to the user and, if helpful, list the parameters used to get there.

Always be professional, concise, and when possible, cite the source document for any data you extract.
"""


class AgentEngine:
    """
    An AI Agent that can use tools to interact with a knowledge base of documents.
    This engine supports persistence, allowing it to load, save, and update the knowledge base.
    """
    def __init__(self, api_key: str):
        if not api_key:
            raise ValueError("OpenAI API key is required.")
        os.environ["OPENAI_API_KEY"] = api_key
        
        # Core components
        self.llm = ChatOpenAI(model="gpt-4o-mini")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        
        # State variables
        self.vectorstore: FAISS = None
        self.rag_chain = None
        self.agent_executor: AgentExecutor = None
        self.file_names: List[str] = []
        self.raw_texts: Dict[str, str] = {}
        
        # Ensure storage directory exists
        os.makedirs(STORAGE_DIR, exist_ok=True)
        
        # --- Initialize Tools ---
        self.tools = create_all_tools(self)
        
        # Expose summary tool for direct calls from UI
        self.summarize_document = self.tools[1]  # summarize_document is the second tool

    def _get_text_splitter(self, docs_for_rag: List = None):
        """
        Creates an optimal text splitter based on document characteristics.
        """
        if not docs_for_rag:
            # Default configuration for unknown content
            return RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            
        # Smart text splitting based on content size
        # For OCR content, extract the actual text without the prefix
        actual_texts = []
        for i, doc in enumerate(docs_for_rag):
            text = doc[0] if isinstance(doc, tuple) else doc
            
            print(f"  - Document {i+1}: Total length = {len(text)} chars")
            
            # Remove OCR prefix for length calculation
            if text.startswith("=== Text extracted from images using OCR ===\n"):
                actual_text = text.replace("=== Text extracted from images using OCR ===\n", "")
                actual_texts.append(actual_text)
                print(f"    OCR document: Prefix removed, actual length = {len(actual_text)} chars")
            else:
                actual_texts.append(text)
                print(f"    Regular document: Using full length = {len(text)} chars")
        
        total_text_length = sum(len(text) for text in actual_texts)
        avg_text_length = total_text_length / len(actual_texts) if actual_texts else 0
        
        print(f"  - Total actual text length: {total_text_length}")
        print(f"  - Average text length: {int(avg_text_length)}")
        
        # Adjust chunk size based on document size
        if avg_text_length < 200:
            # Very tiny documents - don't chunk, use as single piece
            chunk_size = max(avg_text_length, 50)  # Minimum 50 chars for FAISS
            overlap = 0
            print(f"  - Strategy: TINY documents (< 200 chars) - minimal chunking")
        elif avg_text_length < 500:
            # Small documents - use smaller chunks
            chunk_size = max(200, int(avg_text_length * 0.8))
            overlap = min(50, chunk_size // 4)
            print(f"  - Strategy: SMALL documents (200-500 chars)")
        elif avg_text_length < 2000:
            # Medium documents
            chunk_size = 500
            overlap = 100
            print(f"  - Strategy: MEDIUM documents (500-2000 chars)")
        else:
            # Large documents - use default settings
            chunk_size = 1000
            overlap = 200
            print(f"  - Strategy: LARGE documents (> 2000 chars)")
            
        print(f"Using chunk_size={chunk_size}, overlap={overlap} for {len(docs_for_rag)} document(s) (avg_length={int(avg_text_length)})")
        return RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=overlap)
        
    def _create_valid_chunks(self, text_splitter, docs_for_rag):
        """
        Creates and validates document chunks, filtering out empty or meaningless ones.
        """
        split_docs = text_splitter.create_documents(
            [doc[0] for doc in docs_for_rag],
            metadatas=[doc[1] for doc in docs_for_rag]
        )
        
        # Ensure we have meaningful chunks
        valid_chunks = [doc for doc in split_docs if len(doc.page_content.strip()) > 10]
        
        if not valid_chunks:
            raise ValueError("No meaningful content chunks could be created from the documents.")
        
        if len(valid_chunks) < len(split_docs):
            print(f"Filtered out {len(split_docs) - len(valid_chunks)} empty or very small chunks")
            
        return valid_chunks

    def _build_agent(self):
        """Builds or rebuilds the agent executor with the current file list."""
        print("Rebuilding agent with updated file list...")
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", AGENT_SYSTEM_PROMPT.format(file_list=", ".join(self.file_names))),
            ("placeholder", "{chat_history}"),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        agent = create_openai_tools_agent(self.llm, self.tools, agent_prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=self.tools, verbose=True)
        print("Agent is ready.")

    def _build_rag_chain(self):
        """Builds the RAG chain from the current vectorstore."""
        retriever = self.vectorstore.as_retriever(search_kwargs={"k": 8})
        qa_prompt = ChatPromptTemplate.from_template("""
Answer the user's question based only on the following context:
{context}

Question: {input}
""")
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        self.rag_chain = create_retrieval_chain(retriever, question_answer_chain)

    def create_and_save(self, uploaded_files: List) -> List[str]:
        """Create knowledge base from uploaded files and save persistently."""
        print("🔧 Creating knowledge base...")
        
        docs_for_rag = []
        failed_files = []
        
        for file in uploaded_files:
            print(f"📄 Processing: {file.name}")
            
            # Save the uploaded file to a temporary location
            with open(file.name, "wb") as f:
                f.write(file.getvalue())
            
            # Parse the document
            parsed_result = DocumentParser.parse_document(file.name)
            
            if "error" in parsed_result:
                print(f"  ❌ Failed to parse {file.name}: {parsed_result['error']}")
                failed_files.append(file.name)
                os.remove(file.name)  # Clean up
                continue
            
            text = parsed_result["content"]
            
            # Check if the text is actually valid content or OCR failure
            if not text or text.startswith("=== Document contains only images with no readable text ==="):
                print(f"  - {file.name} contains no readable text (may be image-only or OCR failed)")
                failed_files.append(file.name)
                os.remove(file.name)  # Clean up
                continue
            
            print(f"  ✅ Extracted {len(text)} characters")
            docs_for_rag.append((text, {"source": file.name}))
            self.raw_texts[file.name] = text
            os.remove(file.name)  # Clean up
        
        if not docs_for_rag:
            raise ValueError("❌ No files could be processed successfully. Please check your file formats and content.")
        
        # Smart text splitting
        text_splitter = self._get_text_splitter(docs_for_rag)
        
        # Create valid chunks with filtering
        split_docs = self._create_valid_chunks(text_splitter, docs_for_rag)
        
        # Create vector store
        print("🔤 Creating embeddings...")
        self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        self.file_names = [file.name for file in uploaded_files if file.name not in failed_files]
        
        # Build chains and agents
        self._build_rag_chain()
        self._build_agent()
        
        # Save everything
        self.save()
        
        print(f"✅ Knowledge base created with {len(self.file_names)} documents!")
        return failed_files

    def add_documents(self, uploaded_files: List) -> List[str]:
        """Add new documents to existing knowledge base."""
        print("🔧 Adding documents to existing knowledge base...")
        
        if not self.vectorstore:
            raise ValueError("No existing knowledge base found. Please create one first.")
        
        docs_for_rag = []
        failed_files = []
        new_file_names = []
        
        for file in uploaded_files:
            if file.name in self.file_names:
                print(f"  ⚠️ {file.name} already exists, skipping...")
                continue
                
            print(f"📄 Processing: {file.name}")
            
            # Save the uploaded file to a temporary location
            with open(file.name, "wb") as f:
                f.write(file.getvalue())
            
            # Parse the document
            parsed_result = DocumentParser.parse_document(file.name)
            
            if "error" in parsed_result:
                print(f"  ❌ Failed to parse {file.name}: {parsed_result['error']}")
                failed_files.append(file.name)
                os.remove(file.name)  # Clean up
                continue
            
            text = parsed_result["content"]
            
            # Check if the text is actually valid content or OCR failure  
            if not text or text.startswith("=== Document contains only images with no readable text ==="):
                print(f"  - {file.name} contains no readable text (may be image-only or OCR failed)")
                failed_files.append(file.name)
                os.remove(file.name)  # Clean up
                continue
            
            print(f"  ✅ Extracted {len(text)} characters")
            docs_for_rag.append((text, {"source": file.name}))
            self.raw_texts[file.name] = text
            new_file_names.append(file.name)
            os.remove(file.name)  # Clean up
        
        if not docs_for_rag:
            print("No new documents were processed.")
            return failed_files
        
        # Smart text splitting for new documents
        text_splitter = self._get_text_splitter(docs_for_rag)
        
        # Create valid chunks for new documents
        split_docs = self._create_valid_chunks(text_splitter, docs_for_rag)
        
        # Add to existing vector store
        print("🔤 Adding new embeddings...")
        self.vectorstore.add_documents(split_docs)
        self.file_names.extend(new_file_names)
        
        # Rebuild chains and agents with updated file list
        self._build_rag_chain()
        self._build_agent()
        
        # Save everything
        self.save()
        
        print(f"✅ Added {len(new_file_names)} new documents!")
        return failed_files

    def delete_document(self, file_name_to_delete: str):
        """Delete a specific document from the knowledge base."""
        if file_name_to_delete not in self.file_names:
            raise ValueError(f"Document '{file_name_to_delete}' not found in knowledge base.")
        
        print(f"🗑️ Deleting document: {file_name_to_delete}")
        
        # Remove from file list and raw texts
        self.file_names.remove(file_name_to_delete)
        if file_name_to_delete in self.raw_texts:
            del self.raw_texts[file_name_to_delete]
        
        # Check if any documents remain
        if not self.file_names:
            print("No documents remain. Clearing knowledge base...")
            self.vectorstore = None
            self.rag_chain = None
            self.agent_executor = None
            self.save()
            return
        
        # Rebuild vector store without the deleted document
        print("Rebuilding vector store without deleted document...")
        docs_for_rag = [(self.raw_texts[name], {"source": name}) for name in self.file_names]
        
        # Smart text splitting
        text_splitter = self._get_text_splitter(docs_for_rag)
        
        # Create valid chunks
        split_docs = self._create_valid_chunks(text_splitter, docs_for_rag)
        
        # Recreate vector store
        print("🔤 Recreating embeddings...")
        self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        
        # Rebuild chains and agents
        self._build_rag_chain()
        self._build_agent()
        
        # Save everything
        self.save()
        print(f"✅ Document '{file_name_to_delete}' deleted successfully!")

    def save(self):
        """Save the current state to persistent storage."""
        if self.vectorstore:
            self.vectorstore.save_local(FAISS_INDEX_PATH)
        
        # Save metadata
        metadata = {
            "file_names": self.file_names,
            "raw_texts": self.raw_texts
        }
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved to {STORAGE_DIR}")

    def load(self) -> bool:
        """Load existing state from persistent storage. Returns True if successful."""
        try:
            if not os.path.exists(FAISS_INDEX_PATH) or not os.path.exists(METADATA_PATH):
                return False
            
            # Load metadata
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                metadata = json.load(f)
            
            self.file_names = metadata.get("file_names", [])
            self.raw_texts = metadata.get("raw_texts", {})
            
            if not self.file_names:
                return False
            
            # Load vector store
            self.vectorstore = FAISS.load_local(
                FAISS_INDEX_PATH, 
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            
            # Rebuild chains and agents
            self._build_rag_chain()
            self._build_agent()
            
            print(f"📂 Loaded existing knowledge base with {len(self.file_names)} documents")
            return True
            
        except Exception as e:
            print(f"❌ Failed to load existing knowledge base: {e}")
            return False

    def invoke(self, query: str, chat_history: List = None) -> str:
        """Process a user query through the agent."""
        if not self.agent_executor:
            return "❌ Knowledge base not initialized. Please upload documents first."
        
        try:
            response = self.agent_executor.invoke({
                "input": query,
                "chat_history": chat_history or []
            })
            return response["output"]
        except Exception as e:
            return f"❌ Error processing query: {str(e)}"

    def reset_storage(self):
        """Delete all persistent storage."""
        if os.path.exists(STORAGE_DIR):
            shutil.rmtree(STORAGE_DIR)
            print(f"🗑️ Cleared storage directory: {STORAGE_DIR}")
        
        # Reset instance state
        self.vectorstore = None
        self.rag_chain = None
        self.agent_executor = None
        self.file_names = []
        self.raw_texts = {}
        
        # Recreate storage directory
        os.makedirs(STORAGE_DIR, exist_ok=True)
