"""
This module contains the core Retrieval-Augmented Generation (RAG) engine.
"""
import os
from .document_parser import parse_document

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

class ChatEngine:
    """
    The core RAG engine for the AI Office Assistant.
    It takes a file, processes it into a vector store, and can answer questions
    based on the document's content.
    """
    def __init__(self, file_paths: list[str], api_key: str):
        """
        Initializes the RAG engine for multiple documents.
        1. Loads and parses all documents.
        2. Splits them into chunks with metadata.
        3. Creates a single vector store (FAISS).
        4. Sets up a conversation retrieval chain.
        """
        if not api_key:
            raise ValueError("OpenAI API key is required to initialize the ChatEngine.")

        os.environ["OPENAI_API_KEY"] = api_key
        
        # Initialize LLM and Embeddings
        self.llm = ChatOpenAI(model="gpt-4o-mini")
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

        # 1. Load and parse all documents
        print(f"Parsing {len(file_paths)} documents...")
        all_docs = []
        for file_path in file_paths:
            print(f"  - Parsing: {os.path.basename(file_path)}")
            parsed_data = parse_document(file_path)
            if "error" in parsed_data:
                raise ValueError(f"Failed to parse document: {parsed_data['error']}")
            
            # Create a document object with metadata
            doc_content = parsed_data.get("text", "")
            doc_metadata = {"source": os.path.basename(file_path)}
            all_docs.append((doc_content, doc_metadata))

        # 2. Split documents into chunks
        print("Splitting documents into chunks...")
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, 
            chunk_overlap=200
        )
        
        doc_contents = [doc[0] for doc in all_docs]
        doc_metadatas = [doc[1] for doc in all_docs]
        split_docs = text_splitter.create_documents(doc_contents, metadatas=doc_metadatas)

        # 3. Create a vector store
        print(f"Creating vector store from {len(split_docs)} chunks...")
        self.vectorstore = FAISS.from_documents(split_docs, self.embeddings)

        # 4. Create a history-aware retriever
        print("Setting up conversational chain...")
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 8}) # Increased k for more context
        self._setup_conversation_chain()
        print("Engine is ready.")

    def _setup_conversation_chain(self):
        """
        Builds the conversational chain that can use chat history
        to answer questions.
        """
        # Prompt for contextualizing question based on history
        contextualize_q_system_prompt = (
            "Given a chat history and the latest user question "
            "which might reference context in the chat history, "
            "formulate a standalone question which can be understood "
            "without the chat history. Do NOT answer the question, "
            "just reformulate it if needed and otherwise return it as is."
        )
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        self.history_aware_retriever = create_history_aware_retriever(
            self.llm, self.retriever, contextualize_q_prompt
        )

        # Prompt for answering the question based on retrieved context
        qa_system_prompt = (
            "You are an expert assistant for question-answering tasks over a collection of documents. "
            "Use the following pieces of retrieved context to answer the question. "
            "The context provided has a `source` in its metadata, pointing to the origin document. "
            "If you don't know the answer, just say that you don't know. "
            "Be concise and professional. When possible, cite the source document for your answer. "
            "Example: 'According to the document `annual_report.pdf`, the revenue was $10 million.' "
            "\n\n"
            "{context}"
        )
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        
        # Chain for combining documents and answering
        question_answer_chain = create_stuff_documents_chain(self.llm, qa_prompt)
        
        # The final full chain
        self.rag_chain = create_retrieval_chain(self.history_aware_retriever, question_answer_chain)

    def ask(self, question: str, chat_history: list = None):
        """
        Asks a question to the RAG chain.
        
        Args:
            question (str): The user's question.
            chat_history (list): A list of previous HumanMessage and AIMessage objects.
        
        Returns:
            str: The AI's answer.
        """
        if chat_history is None:
            chat_history = []
            
        response = self.rag_chain.invoke({
            "input": question,
            "chat_history": chat_history
        })
        return response.get("answer", "Sorry, I could not find an answer.")

# Example usage (for testing)
if __name__ == '__main__':
    # This is a placeholder for a file. Create a dummy file for testing.
    dummy_files_data = {
        "report_2022.txt": "In 2022, the project Alpha was launched. The manager was Sarah Smith.",
        "report_2023.txt": "In 2023, the project Beta was launched, and the revenue was $10 million. The manager for this project was John Doe."
    }
    
    dummy_file_paths = []
    for name, content in dummy_files_data.items():
        with open(name, "w") as f:
            f.write(content)
        dummy_file_paths.append(name)

    # Make sure to set your OPENAI_API_KEY as an environment variable
    # from dotenv import load_dotenv
    # load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if api_key:
        print("--- Testing ChatEngine ---")
        engine = ChatEngine(file_paths=dummy_file_paths, api_key=api_key)
        
        history = []
        
        # First question
        q1 = "Who was the project manager in 2022?"
        print(f"\nUser: {q1}")
        answer1 = engine.ask(q1, history)
        print(f"AI: {answer1}")
        history.extend([HumanMessage(content=q1), AIMessage(content=answer1)])

        # Follow-up question that requires info from the other doc
        q2 = "And what was the revenue in the following year?"
        print(f"\nUser: {q2}")
        answer2 = engine.ask(q2, history)
        print(f"AI: {answer2}")

        # Clean up the dummy files
        for path in dummy_file_paths:
            os.remove(path)
    else:
        print("Skipping test: OPENAI_API_KEY not found.") 