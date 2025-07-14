"""
This module contains the core Retrieval-Augmented Generation (RAG) engine.
"""
import os
import json
from typing import List, Dict
from .document_parser import parse_document

from langchain.tools import tool
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.agents import AgentExecutor, create_openai_tools_agent
import shutil

# --- STORAGE CONFIGURATION ---
STORAGE_DIR = "persistent_storage"
FAISS_INDEX_PATH = os.path.join(STORAGE_DIR, "vector_store")
METADATA_PATH = os.path.join(STORAGE_DIR, "metadata.json")


# --- AGENT SYSTEM PROMPT ---
AGENT_SYSTEM_PROMPT = """
You are an expert financial and legal assistant. You are working with a knowledge base of documents provided by the user.
Your primary goal is to answer questions based on the content of these documents.
You have access to a set of tools to help you.

- Use the `knowledge_base_qa` tool to answer any questions about the content of the documents.
- Use the `summarize_document` tool ONLY when the user explicitly asks for a summary of a specific file. You can also specify the summary's language (e.g., "summarize file.pdf in Chinese").
- For general conversation or questions not related to the documents, you can answer directly.

When providing answers, be professional, concise, and cite the source document if possible.
The user has uploaded the following files to the knowledge base: {file_list}
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
        
        # Define tools using instance methods
        @tool
        def knowledge_base_qa(query: str) -> str:
            """
            Use this tool to answer any questions about the content of the uploaded documents.
            The input should be a user's full question.
            This is your primary tool for information retrieval.
            """
            if not self.rag_chain:
                return "Error: The knowledge base is not initialized. Please load documents first."
            response = self.rag_chain.invoke({"input": query})
            return response.get("answer", "I could not find an answer in the documents.")

        @tool
        def summarize_document(file_name: str, language: str = "English") -> str:
            """
            Use this tool to generate a detailed summary of a SINGLE, SPECIFIC document in a specified language.
            The first input MUST be the exact file name.
            The second, optional input is the language for the summary (defaults to English).
            """
            if file_name not in self.raw_texts:
                return f"Error: The file '{file_name}' was not found in the knowledge base. Please use one of the available files: {', '.join(self.file_names)}"
            
            text_to_summarize = self.raw_texts[file_name]
            system_prompt = f"You are a highly skilled summarization assistant. Your sole task is to generate a concise and comprehensive summary of the provided document text. The summary MUST be written in the following language: {language}."
            human_prompt = f"Please summarize the following document, '{file_name}', in {language}:\n\nDocument content:\n{text_to_summarize[:16000]}"
            
            response = self.llm.invoke([
                SystemMessage(content=system_prompt),
                HumanMessage(content=human_prompt)
            ])
            return response.content
        
        self.tools = [knowledge_base_qa, summarize_document]
        # Expose summary tool for direct calls from UI
        self.summarize_document = summarize_document

    def _build_agent(self):
        """Builds or rebuilds the agent executor with the current file list."""
        print("Rebuilding agent with updated file list...")
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", AGENT_SYSTEM_PROMPT.format(file_list=", ".join(self.file_names))),
            AIMessage(content="Hello! I am your AI assistant. How can I help you with your documents today?"),
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

    def load_from_disk(self) -> bool:
        """
        Loads an existing vector store and metadata from disk.
        Returns True if successful, False otherwise.
        """
        if os.path.exists(FAISS_INDEX_PATH) and os.path.exists(METADATA_PATH):
            print("Found existing knowledge base. Loading from disk...")
            self.vectorstore = FAISS.load_local(FAISS_INDEX_PATH, self.embeddings, allow_dangerous_deserialization=True)
            with open(METADATA_PATH, 'r') as f:
                metadata = json.load(f)
                self.file_names = metadata["file_names"]
                self.raw_texts = metadata["raw_texts"]
            
            self._build_rag_chain()
            self._build_agent()
            print("Successfully loaded knowledge base.")
            return True
        return False

    def _save_to_disk(self):
        """Saves the current vector store and metadata to disk."""
        print("Saving knowledge base to disk...")
        self.vectorstore.save_local(FAISS_INDEX_PATH)
        metadata = {
            "file_names": self.file_names,
            "raw_texts": self.raw_texts
        }
        with open(METADATA_PATH, 'w') as f:
            json.dump(metadata, f)
        print("Save complete.")

    def create_and_save(self, file_paths: List[str]):
        """
        Creates a new knowledge base from files and saves it to disk.
        """
        print("Creating new knowledge base...")
        docs_for_rag = []
        for file_path in file_paths:
            file_name = os.path.basename(file_path)
            print(f"  - Processing: {file_name}")
            parsed_data = parse_document(file_path)
            if "error" in parsed_data:
                raise ValueError(f"Failed to parse {file_name}: {parsed_data['error']}")
            
            text = parsed_data.get("text", "")
            self.raw_texts[file_name] = text
            docs_for_rag.append((text, {"source": file_name}))
        
        self.file_names = [os.path.basename(p) for p in file_paths]
        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.create_documents(
            [doc[0] for doc in docs_for_rag],
            metadatas=[doc[1] for doc in docs_for_rag]
        )
        
        self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        self._build_rag_chain()
        self._build_agent()
        self._save_to_disk()

    def delete_document(self, file_name_to_delete: str):
        """
        Deletes a document from the knowledge base and rebuilds the index.
        """
        if file_name_to_delete not in self.file_names:
            print(f"Error: Cannot delete '{file_name_to_delete}', as it's not in the knowledge base.")
            return

        print(f"Deleting '{file_name_to_delete}' from the knowledge base...")
        
        # Remove the file from our tracked lists
        self.file_names.remove(file_name_to_delete)
        self.raw_texts.pop(file_name_to_delete, None)
        
        if not self.file_names:
            # If no files are left, just clear the storage
            print("No files left in the knowledge base. Deleting storage...")
            if os.path.exists(FAISS_INDEX_PATH):
                shutil.rmtree(FAISS_INDEX_PATH)
            if os.path.exists(METADATA_PATH):
                os.remove(METADATA_PATH)
            self.vectorstore = None
            self.rag_chain = None
            self.agent_executor = None
            return

        # Rebuild the entire knowledge base from the remaining files
        print("Rebuilding knowledge base from remaining files...")
        docs_for_rag = []
        for file_name in self.file_names:
            text = self.raw_texts.get(file_name, "")
            if text:
                docs_for_rag.append((text, {"source": file_name}))

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.create_documents(
            [doc[0] for doc in docs_for_rag],
            metadatas=[doc[1] for doc in docs_for_rag]
        )
        
        self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)
        self._build_rag_chain()
        self._build_agent()
        self._save_to_disk()
        print(f"Successfully deleted '{file_name_to_delete}' and rebuilt the knowledge base.")

    def add_documents(self, new_file_paths: List[str]):
        """
        Adds new documents to the existing knowledge base.
        """
        if not self.vectorstore:
            raise ValueError("Cannot add documents to a non-existent knowledge base. Call create_and_save first.")
            
        print("Adding new documents to the knowledge base...")
        docs_for_rag = []
        for file_path in new_file_paths:
            file_name = os.path.basename(file_path)
            if file_name in self.file_names:
                print(f"  - Skipping already existing file: {file_name}")
                continue
                
            print(f"  - Processing: {file_name}")
            parsed_data = parse_document(file_path)
            if "error" in parsed_data:
                raise ValueError(f"Failed to parse {file_name}: {parsed_data['error']}")
            
            text = parsed_data.get("text", "")
            self.raw_texts[file_name] = text
            self.file_names.append(file_name)
            docs_for_rag.append((text, {"source": file_name}))

        if not docs_for_rag:
            print("No new documents to add.")
            return

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        split_docs = text_splitter.create_documents(
            [doc[0] for doc in docs_for_rag],
            metadatas=[doc[1] for doc in docs_for_rag]
        )
        
        # Add new documents to the existing vector store
        self.vectorstore.add_documents(split_docs)
        
        # Rebuild agent with updated file list and save everything
        self._build_rag_chain()
        self._build_agent()
        self._save_to_disk()
        
    def invoke(self, question: str, chat_history: List = None):
        """
        Invokes the agent to get a response.
        """
        if not self.agent_executor:
            return "The AI agent is not ready. Please create or load a knowledge base first."
            
        chat_history = chat_history or []
        response = self.agent_executor.invoke({
            "input": question,
            "chat_history": chat_history
        })
        return response.get("output", "Sorry, I encountered an error.")

# Example usage for testing
if __name__ == '__main__':
    # This section would need to be updated to test the new persistent workflow.
    # e.g., create, then load, then add.
    pass 