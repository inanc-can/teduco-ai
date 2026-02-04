"""
RAG Chatbot Pipeline Module

Main orchestrator that combines document loading, retrieval, and LLM generation
into a complete RAG pipeline.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict
from langchain_core.documents import Document
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

from rag.chatbot.config import GROQ_MODEL
from rag.chatbot.loader import DocumentLoader
from rag.chatbot.retriever import RetrievalPipeline
from rag.chatbot.db_ops import retrieve_chunks

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
        data_dir: str = "backend/rag_data",
        vector_store_dir: Optional[str] = None,
        model_name: Optional[str] = None,
        program_slugs: Optional[List[str]] = None,
        use_cache: bool = True,
        embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        k: int = 15,
        similarity_threshold: float = 0.30,
        semantic_weight: float = 0.6,
        keyword_weight: float = 0.4
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
            similarity_threshold: Minimum hybrid score (0-1) to use a document.
                                 Lowered from 0.40 to 0.25 for multilingual embeddings.
            semantic_weight: Weight for semantic similarity in hybrid search (0-1, default: 0.5)
            keyword_weight: Weight for keyword matching in hybrid search (0-1, default: 0.5)
        """
        self.data_dir = data_dir
        self.vector_store_dir = vector_store_dir or f"{data_dir}/vector_store"
        self.model_name = model_name if model_name is not None else GROQ_MODEL
        self.program_slugs = program_slugs
        self.use_cache = use_cache
        self.similarity_threshold = similarity_threshold  # Minimum similarity to use document
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        
        # Check for API key
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables!")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] \n" + "="*70)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] INITIALIZING RAG CHATBOT PIPELINE")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] " + "="*70)
        
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
        print(f"[{datetime.now().strftime('%H:%M:%S')}] \n[PIPELINE] Initializing components...")
        
        # Step 1: Verify Supabase connection (skip local document loading)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] \n[1/2] Verifying Supabase connection...")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [PIPELINE] Using Supabase for vector storage and retrieval")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [PIPELINE] [OK] Supabase configuration loaded")
        
        # Step 2: Setup LLM chain
        print(f"[{datetime.now().strftime('%H:%M:%S')}] \n[2/2] Setting up LLM chain...")
        self._setup_llm_chain()
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] \n" + "="*70)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [OK] RAG PIPELINE READY")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] " + "="*70 + "\n")
    
    def _setup_llm_chain(self):
        """Setup the LLM chain for answer generation."""
        # Initialize Groq LLM
        self.llm = ChatGroq(
            model=self.model_name,
            temperature=0,
            max_tokens=1000,  # Reduced for more concise responses
            groq_api_key=os.getenv("GROQ_API_KEY")
        )
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   [PIPELINE] [OK] LLM initialized (model: {self.model_name})")
        
        # Create prompt template with chat history support
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a friendly but professional education consultant at Teduco, specializing in TUM admissions. Be approachable; keep a professional, precise tone.

ABSOLUTE RULE: Only answer based on the CONTEXT below (TUM program information from the information center). If information is NOT in the context, say: "I don't have that information. Contact study@tum.de."

WHEN YOU HAVE THE INFORMATION: State it directly and confidently. Do NOT say "I recommend contacting study@tum.de" or "you can start by checking TUMonline" when the answer (e.g. application dates, requirements) is in the context — give the answer. Only redirect when the information is genuinely not in the context.

FOLLOW-UP QUESTIONS: If the question is ambiguous or you need one or two specific details (e.g. which program, intake, or whether they are international), ask one or two short follow-up questions. Once they answer, give a complete, straight-to-the-point answer using the conversation history.

MISSING DOCUMENTS/PROFILE: If they ask about their eligibility or required documents and relevant profile or document info is missing, briefly state what is missing, suggest they upload documents or complete their profile, then answer as well as you can.

WHEN UNCERTAIN: Do not guess. Redirect to study@tum.de only (never suggest the TUM website or tum.de).

REDIRECTS: Only direct users to study@tum.de or TUMonline. NEVER suggest "the TUM website", "tum.de", "check the TUM website", or similar.

NEVER: Guess, assume, or infer; use "typically"/"usually"; make up facts; mention "information center", "context", "database", or "documents" in your reply.

ALWAYS: State only facts from the context; be concise (3-5 sentences, bullets for lists); after you have enough info, give a complete, straight-to-the-point answer. Do NOT use sign-offs (Best regards, Sincerely, [Your Name], etc.); end with the answer only.

=== PROGRAM INFORMATION ===
{context}"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}")
        ])
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   [PIPELINE] [OK] Prompt template configured")
        
        # Custom retriever function that prints debug info
        def retrieve_with_debug(question: str):
            """Retrieve documents with hybrid search and print debug info using Supabase."""
            print(f"[{datetime.now().strftime('%H:%M:%S')}] \n{'='*70}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] Query: {question}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] Hybrid search weights - Semantic: {self.semantic_weight}, Keyword: {self.keyword_weight}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {'='*70}")
            
            try:
                # 1. Embed query (using existing embeddings module)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] Embedding query...")
                query_embedding = self.retriever_pipeline.embeddings.embed_query(question)
                
                # 2. Retrieve from Supabase using hybrid search
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] Querying Supabase with hybrid search...")
                results = retrieve_chunks(
                    query=question,
                    query_embedding=query_embedding,
                    top_k=self.retriever_pipeline.k,
                    semantic_weight=self.semantic_weight,
                    keyword_weight=self.keyword_weight
                )
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] Retrieved {len(results)} chunks from Supabase")
                
                if not results:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] WARNING: No documents retrieved from Supabase!")
                    return []
                
                # 3. Process results
                filtered_docs = []
                for idx, res in enumerate(results, 1):
                    hybrid_score = res.get("hybrid_score", 0.0)
                    similarity = res.get("similarity_score", 0.0)
                    keyword_rank = res.get("keyword_rank", 0.0)
                    content = res.get("content", "")
                    metadata = res.get("metadata") or {}
                    
                    # Create Document object
                    doc = Document(page_content=content, metadata=metadata)
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   [{idx}] Hybrid Score: {hybrid_score:.4f} (Semantic: {similarity:.4f}, Keyword: {keyword_rank:.4f})", end="")
                    
                    # Check if document meets threshold (using hybrid_score)
                    if hybrid_score >= self.similarity_threshold:
                        print(f" [OK] (Above threshold: {self.similarity_threshold})")
                        filtered_docs.append(doc)
                    else:
                        print(f" [FAIL] (Below threshold: {self.similarity_threshold}) - FILTERED OUT")
                    
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]       Source: {doc.metadata.get('source', 'unknown')}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]       Section: {doc.metadata.get('section', 'N/A')}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]       Type: {doc.metadata.get('type', 'N/A')}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]       Key: {doc.metadata.get('key', 'N/A')}")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]       Content Preview: {doc.page_content[:200]}...")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] ")

                print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] After filtering: {len(filtered_docs)}/{len(results)} documents meet threshold ({self.similarity_threshold})")
                
                if len(filtered_docs) == 0:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] WARNING: No documents meet hybrid score threshold!")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] This means the retrieved documents are not relevant enough.")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] Consider:")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   - Lowering threshold (current: {self.similarity_threshold})")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   - Adjusting semantic/keyword weights (current: {self.semantic_weight}/{self.keyword_weight})")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   - Improving document quality")
                    print(f"[{datetime.now().strftime('%H:%M:%S')}]   - Rephrasing the question")
                
                print(f"[{datetime.now().strftime('%H:%M:%S')}] {'='*70}\n")
                
                # Return filtered documents (only those above threshold)
                return filtered_docs

            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER DEBUG] ERROR during retrieval: {e}")
                import traceback
                traceback.print_exc()
                return []

        # Initialize agentic assistant that can use user profile and docs if available
        from rag.chatbot.agent import Agent

        # Create the Agent with the existing llm, retriever pipeline, embeddings, and hybrid search weights
        self.agent = Agent(
            llm=self.llm,
            retriever_pipeline=self.retriever_pipeline,
            embeddings=self.retriever_pipeline.embeddings,
            k=self.retriever_pipeline.k,
            similarity_threshold=self.similarity_threshold,
            semantic_weight=self.semantic_weight,
            keyword_weight=self.keyword_weight,
        )
        
        # Format documents helper with debug output
        def format_docs(docs):
            formatted = "\n\n".join([doc.page_content for doc in docs])
            
            # Debug: Print the full context being sent to LLM
            print(f"[{datetime.now().strftime('%H:%M:%S')}] \n{'='*70}")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [CONTEXT DEBUG] Full context being sent to LLM ({len(docs)} documents):")
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {'='*70}")
            print(formatted)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {'='*70}\n")
            
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
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}]   [PIPELINE] [OK] RAG chain configured with chat history support!")
    
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
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [PIPELINE] [FAIL] {error_msg}")
            return error_msg
    
    @property
    def split_docs(self):
        """Get the split documents."""
        return self.retriever_pipeline.split_docs


def initialize_rag_pipeline(
    data_dir: str = "backend/rag_data",
    vector_store_dir: Optional[str] = None,
    use_cache: bool = True,
    program_slugs: Optional[List[str]] = None,
    similarity_threshold: float = 0.30,
    semantic_weight: float = 0.6,
    keyword_weight: float = 0.4,
    model_name: Optional[str] = None
) -> RAGChatbotPipeline:
    """
    Initialize the RAG pipeline (convenience function).
    Uses GROQ_MODEL from rag.chatbot.config unless model_name is passed.

    Args:
        data_dir: Directory for crawled data
        vector_store_dir: Directory for vector store
        use_cache: Use cached data if available
        program_slugs: List of program slugs to load
        similarity_threshold: Minimum hybrid score (0-1) to use a document. Default: 0.35
        semantic_weight: Weight for semantic similarity in hybrid search (0-1, default: 0.6)
        keyword_weight: Weight for keyword matching in hybrid search (0-1, default: 0.4)
        model_name: Groq model name (default: from rag.chatbot.config.GROQ_MODEL)
        
    Returns:
        Initialized RAGChatbotPipeline instance
    """
    return RAGChatbotPipeline(
        data_dir=data_dir,
        vector_store_dir=vector_store_dir,
        use_cache=use_cache,
        program_slugs=program_slugs,
        similarity_threshold=similarity_threshold,
        semantic_weight=semantic_weight,
        keyword_weight=keyword_weight,
        model_name=model_name
    )

