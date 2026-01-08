"""
RAG Chatbot Pipeline Module

Main orchestrator that combines document loading, retrieval, and LLM generation
into a complete RAG pipeline.
"""

import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Add parent directories to path
CURRENT_DIR = Path(__file__).parent
RAG_DIR = CURRENT_DIR.parent
BACKEND_DIR = RAG_DIR.parent

# Add paths in correct order
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(RAG_DIR))

from rag.chatbot.loader import DocumentLoader
from rag.chatbot.retriever import RetrievalPipeline

# Load environment variables
load_dotenv()


class RAGChatbotPipeline:
    """
    Complete RAG pipeline for university chatbot.
    
    This class orchestrates:
    1. Document loading (from crawler or cache)
    2. Document chunking and embedding
    3. Vector store creation
    4. Retrieval and LLM-based answer generation
    """
    
    def __init__(
        self,
        data_dir: str = "backend/rag/data",
        vector_store_dir: Optional[str] = None,
        model_name: str = "llama-3.1-8b-instant",
        program_slugs: Optional[List[str]] = None,
        use_cache: bool = True,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        k: int = 3,
        similarity_threshold: float = 0.55
    ):
        """
        Initialize the RAG chatbot pipeline.
        
        Args:
            data_dir: Directory for crawled data
            vector_store_dir: Directory to save/load vector store (optional)
            model_name: Groq model name
            program_slugs: List of program slugs to load (None = default list)
            use_cache: If True, load from cache instead of crawling
            embedding_model: HuggingFace embedding model
            chunk_size: Text chunk size
            chunk_overlap: Chunk overlap
            k: Number of documents to retrieve
            similarity_threshold: Minimum similarity score (0-1) to use a document.
                                 Documents below this threshold are filtered out.
                                 Default: 0.55 (balanced). 
                                 Recommended: 0.50-0.60 for most cases.
        """
        self.data_dir = data_dir
        self.vector_store_dir = vector_store_dir or f"{data_dir}/vector_store"
        self.model_name = model_name
        self.program_slugs = program_slugs
        self.use_cache = use_cache
        self.similarity_threshold = similarity_threshold  # Minimum similarity to use document
        
        # Check for API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables!")
        
        print("\n" + "="*70)
        print("INITIALIZING RAG CHATBOT PIPELINE")
        print("="*70)
        
        # Initialize components
        self.loader = DocumentLoader(data_dir=data_dir)
        self.retriever_pipeline = RetrievalPipeline(
            embedding_model=embedding_model,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            k=k
        )
        
        # Initialize pipeline
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Initialize the complete RAG pipeline."""
        print("\n[PIPELINE] Initializing components...")
        
        # Step 1: Load documents
        print("\n[1/3] Loading documents...")
        documents = self.loader.load_from_crawler(
            program_slugs=self.program_slugs,
            use_cache=self.use_cache
        )
        
        if not documents:
            raise ValueError("No documents loaded! Check data directory or run crawler.")
        
        # Step 2: Build vector store
        print("\n[2/3] Building vector store...")
        vector_store_path = Path(self.vector_store_dir)
        
        # Debug: Print document summary
        print(f"\n[DEBUG] Document Summary:")
        print(f"  Total documents loaded: {len(documents)}")
        sources = {}
        for doc in documents:
            source = doc.metadata.get('source', 'unknown')
            doc_type = doc.metadata.get('type', 'unknown')
            sources[source] = sources.get(source, {})
            sources[source][doc_type] = sources[source].get(doc_type, 0) + 1
        
        for source, types in sources.items():
            print(f"  {source}:")
            for doc_type, count in types.items():
                print(f"    - {doc_type}: {count} documents")
        print()
        
        # Try to load existing vector store
        if vector_store_path.exists() and self.use_cache:
            try:
                print(f"  [PIPELINE] Attempting to load existing vector store...")
                self.retriever_pipeline.load_vector_store(str(vector_store_path))
                print(f"  [PIPELINE] ✓ Loaded existing vector store")
                print(f"  [PIPELINE] NOTE: If retrieval isn't working, delete vector_store and rebuild")
            except Exception as e:
                print(f"  [PIPELINE] Could not load existing store: {e}")
                print(f"  [PIPELINE] Building new vector store...")
                self.retriever_pipeline.build_vector_store(documents)
                self.retriever_pipeline.save_vector_store(str(vector_store_path))
        else:
            # Build new vector store
            self.retriever_pipeline.build_vector_store(documents)
            self.retriever_pipeline.save_vector_store(str(vector_store_path))
        
        # Step 3: Setup LLM chain
        print("\n[3/3] Setting up LLM chain...")
        self._setup_llm_chain()
        
        print("\n" + "="*70)
        print("✓ RAG PIPELINE READY")
        print("="*70 + "\n")
    
    def _setup_llm_chain(self):
        """Setup the LLM chain for answer generation."""
        # Initialize Groq LLM
        self.llm = ChatGroq(
            model=self.model_name,
            temperature=0,
            max_tokens=512,  # Reduced for faster, shorter responses
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        print(f"  [PIPELINE] ✓ LLM initialized (model: {self.model_name})")
        
        # Create prompt template with chat history support
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful university admissions advisor for the Technical University of Munich (TUM).

Answer questions about degree programs, admission requirements, and application processes using the context below.

INSTRUCTIONS:
- Keep answers SHORT and CONCISE (2-3 sentences when possible)
- Extract only the most relevant information from the context
- Include key details (dates, deadlines, requirements) but be brief
- Use bullet points for lists to save space
- Only say "I don't have that information" if the context is empty
- Use the conversation history to understand the user's context and refer back to previous topics when relevant
- If the user asks a follow-up question, use the chat history to understand what they're referring to

=== CONTEXT FROM DOCUMENTS ===
{context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        print("  [PIPELINE] ✓ Prompt template configured")
        
        # Get retriever and vector store for debugging
        retriever = self.retriever_pipeline.get_retriever()
        vector_store = self.retriever_pipeline.vector_store
        
        # Custom retriever function that prints debug info
        def retrieve_with_debug(question: str):
            """Retrieve documents with similarity scores and print debug info."""
            print(f"\n{'='*70}")
            print(f"[RETRIEVER DEBUG] Query: {question}")
            print(f"{'='*70}")
            
            # Check if vector store is available
            if vector_store is None:
                print("[RETRIEVER DEBUG] ERROR: Vector store is None!")
                return []
            
            # Use similarity_search_with_score to get scores
            # Note: Lower score = more similar (L2 distance)
            try:
                results_with_scores = vector_store.similarity_search_with_score(
                    question, 
                    k=self.retriever_pipeline.k
                )
            except Exception as e:
                print(f"[RETRIEVER DEBUG] ERROR during retrieval: {e}")
                import traceback
                traceback.print_exc()
                return []
            
            print(f"[RETRIEVER DEBUG] Retrieved {len(results_with_scores)} documents:\n")
            
            if len(results_with_scores) == 0:
                print("[RETRIEVER DEBUG] WARNING: No documents retrieved!")
                print("[RETRIEVER DEBUG] This might mean:")
                print("  - Vector store is empty")
                print("  - Documents weren't loaded correctly")
                print("  - Need to rebuild vector store")
                return []
            
            # Filter documents by similarity threshold
            filtered_docs = []
            for idx, (doc, score) in enumerate(results_with_scores, 1):
                # Convert L2 distance to similarity (lower distance = higher similarity)
                similarity = 1 / (1 + score)  # Convert distance to similarity score (0-1)
                
                print(f"  [{idx}] Similarity Score: {similarity:.4f} (Distance: {score:.4f})", end="")
                
                # Check if document meets threshold
                if similarity >= self.similarity_threshold:
                    print(f" ✓ (Above threshold: {self.similarity_threshold})")
                    filtered_docs.append(doc)
                else:
                    print(f" ✗ (Below threshold: {self.similarity_threshold}) - FILTERED OUT")
                
                print(f"      Source: {doc.metadata.get('source', 'unknown')}")
                print(f"      Section: {doc.metadata.get('section', 'N/A')}")
                print(f"      Type: {doc.metadata.get('type', 'N/A')}")
                print(f"      Key: {doc.metadata.get('key', 'N/A')}")
                print(f"      Content Preview: {doc.page_content[:200]}...")
                print()
            
            print(f"[RETRIEVER DEBUG] After filtering: {len(filtered_docs)}/{len(results_with_scores)} documents meet threshold ({self.similarity_threshold})")
            
            if len(filtered_docs) == 0:
                print("[RETRIEVER DEBUG] WARNING: No documents meet similarity threshold!")
                print("[RETRIEVER DEBUG] This means the retrieved documents are not relevant enough.")
                print("[RETRIEVER DEBUG] Consider:")
                print(f"  - Lowering threshold (current: {self.similarity_threshold})")
                print("  - Improving document quality")
                print("  - Rephrasing the question")
            
            print(f"{'='*70}\n")
            
            # Return filtered documents (only those above threshold)
            return filtered_docs

        # Initialize agentic assistant that can use user profile and docs if available
        from rag.chatbot.agent import Agent

        # Create the Agent with the existing llm, retriever pipeline and embeddings
        self.agent = Agent(
            llm=self.llm,
            retriever_pipeline=self.retriever_pipeline,
            embeddings=self.retriever_pipeline.embeddings,
            k=self.retriever_pipeline.k,
            similarity_threshold=self.similarity_threshold,
        )
        
        # Format documents helper with debug output
        def format_docs(docs):
            formatted = "\n\n".join([doc.page_content for doc in docs])
            
            # Debug: Print the full context being sent to LLM
            print(f"\n{'='*70}")
            print(f"[CONTEXT DEBUG] Full context being sent to LLM ({len(docs)} documents):")
            print(f"{'='*70}")
            print(formatted)
            print(f"{'='*70}\n")
            
            return formatted
        
        # Build RAG chain with debug retriever and chat history support
        # Use RunnableLambda to wrap both functions for the chain
        def get_question(x):
            """Extract question from input dict or use input directly."""
            if isinstance(x, dict):
                return x.get("question", x)
            return x
        
        def get_chat_history(x):
            """Extract chat history from input dict or return empty list."""
            if isinstance(x, dict):
                return x.get("chat_history", [])
            return []
        
        self.chain = (
            {
                "context": RunnableLambda(lambda x: get_question(x)) | RunnableLambda(retrieve_with_debug) | RunnableLambda(format_docs), 
                "question": RunnableLambda(lambda x: get_question(x)),
                "chat_history": RunnableLambda(lambda x: get_chat_history(x))
            }
            | self.prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("  [PIPELINE] ✓ RAG chain configured with chat history support!")
    
    def answer_question(self, question: str, chat_history: Optional[List[Dict[str, str]]] = None) -> str:
        """
        Answer a user's question using the RAG pipeline.
        
        Args:
            question: User's question
            chat_history: Optional list of previous messages in the format:
                          [{"role": "user", "content": "..."}, {"role": "assistant", "content": "..."}]
            
        Returns:
            Answer string
        """
        try:
            # Convert chat history to LangChain message format
            messages = []
            if chat_history:
                for msg in chat_history:
                    if msg.get("role") == "user":
                        messages.append(HumanMessage(content=msg.get("content", "")))
                    elif msg.get("role") == "assistant":
                        messages.append(AIMessage(content=msg.get("content", "")))
            
            # Build the input with chat history
            chain_input = {
                "question": question,
                "chat_history": messages
            }
            
            answer = self.chain.invoke(chain_input)
            return answer
        except Exception as e:
            error_msg = f"Error generating response: {str(e)}"
            print(f"[PIPELINE] ✗ {error_msg}")
            return error_msg
    
    @property
    def split_docs(self):
        """Get the split documents."""
        return self.retriever_pipeline.split_docs


def initialize_rag_pipeline(
    data_dir: str = "backend/rag/data",
    vector_store_dir: Optional[str] = None,
    use_cache: bool = True,
    program_slugs: Optional[List[str]] = None,
    similarity_threshold: float = 0.55
) -> RAGChatbotPipeline:
    """
    Initialize the RAG pipeline (convenience function).
    
    Args:
        data_dir: Directory for crawled data
        vector_store_dir: Directory for vector store
        use_cache: Use cached data if available
        program_slugs: List of program slugs to load
        similarity_threshold: Minimum similarity score (0-1) to use a document.
                             Documents below this are filtered out. Default: 0.55
        
    Returns:
        Initialized RAGChatbotPipeline instance
    """
    return RAGChatbotPipeline(
        data_dir=data_dir,
        vector_store_dir=vector_store_dir,
        use_cache=use_cache,
        program_slugs=program_slugs,
        similarity_threshold=similarity_threshold
    )

