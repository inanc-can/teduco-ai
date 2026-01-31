"""
Retrieval Pipeline Module

Handles document chunking, embedding, and vector store creation for retrieval.
Uses the chunker components to process documents before embedding.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

# Add parent directories to path for imports
CURRENT_DIR = Path(__file__).parent  # backend/rag/chatbot
RAG_DIR = CURRENT_DIR.parent          # backend/rag
BACKEND_DIR = RAG_DIR.parent          # backend
CHUNKER_DIR = RAG_DIR / "chunker"     # backend/rag/chunker

# Add paths similar to how crawler.py does it
sys.path.insert(0, str(BACKEND_DIR))  # Add backend to path
sys.path.insert(0, str(RAG_DIR))      # Add rag to path
sys.path.insert(0, str(CHUNKER_DIR))  # Add chunker to path

# Import using the same pattern as crawler.py
from chunker.langchain_splitters import (
    MarkdownHeaderSplitter,
    RecursiveTextSplitter
)


class RetrievalPipeline:
    """
    Handles document chunking, embedding, and vector store creation.
    
    This class:
    1. Chunks documents using appropriate strategies (recursive or markdown-based)
    2. Creates embeddings using HuggingFace models
    3. Builds a FAISS vector store for fast similarity search
    4. Provides a retriever interface for the RAG pipeline
    """
    
    def __init__(
        self,
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        k: int = 10
    ):
        """
        Initialize the retrieval pipeline.
        
        Args:
            embedding_model: HuggingFace model name for embeddings
            chunk_size: Size of text chunks
            chunk_overlap: Overlap between chunks
            k: Number of documents to retrieve
        """
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.k = k
        
        # Initialize components
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER] Loading embedding model: {embedding_model}")
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER] This may take 30-120 seconds on first run (downloading model)...")
        start_time = datetime.now()
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model,
            cache_folder="/app/.hf_cache",
            encode_kwargs={
                "normalize_embeddings": True  # VERY IMPORTANT for cosine similarity
            },
            model_kwargs={'device': 'cpu'}
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [RETRIEVER] [OK] Embedding model loaded in {elapsed:.2f}s")
        # self.text_splitter = RecursiveTextSplitter()
        self.text_splitter = RecursiveTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        
        self.md_splitter = MarkdownHeaderSplitter()
        
        self.vector_store: Optional[FAISS] = None
        self.split_docs: List[Document] = []
        
    def build_vector_store(self, documents: List[Document]) -> FAISS:
        """
        Build vector store from documents.
        
        This method:
        1. Chunks documents appropriately based on their type
        2. Creates embeddings for all chunks
        3. Builds FAISS vector store
        
        Args:
            documents: List of Document objects to process
            
        Returns:
            FAISS vector store instance
        """
        print(f"\n[RETRIEVER] Building vector store from {len(documents)} documents...")
        
        # Process documents - use markdown splitter for markdown content,
        # recursive splitter for other content
        all_chunks = []
        
        for doc in documents:
            # If document is already from markdown chunks, use as-is
            if doc.metadata.get("type") == "aptitude_assessment":
                # Already chunked by markdown splitter, just add to chunks
                chunks = self.text_splitter.split_documents([doc])
                all_chunks.extend(chunks)
            else:
                # For metadata/JSON content, only split if document is very long
                # Most metadata documents are complete units and shouldn't be split
                doc_length = len(doc.page_content)
                doc_key = doc.metadata.get("key", "unknown")
                
                # Only split if document is significantly longer than chunk_size
                # This preserves complete information for metadata documents
                if doc_length > self.chunk_size * 2:  # Only split if > 2x chunk_size (1000+ chars)
                    # Document is long enough to warrant splitting
                    chunks = self.text_splitter.split_documents([doc])
                    all_chunks.extend(chunks)
                    if doc_key == "Application deadlines":
                        print(f"      [RETRIEVER DEBUG] Split 'Application deadlines' into {len(chunks)} chunks")
                        for i, chunk in enumerate(chunks):
                            print(f"        Chunk {i+1}: {len(chunk.page_content)} chars - {chunk.page_content[:100]}...")
                else:
                    # Keep document as a single chunk to preserve complete information
                    all_chunks.append(doc)
                    if doc_key == "Application deadlines":
                        print(f"      [RETRIEVER DEBUG] Kept 'Application deadlines' as single chunk ({doc_length} chars)")
                        print(f"        Preview: {doc.page_content[:200]}...")
        
        self.split_docs = all_chunks
        print(f"  [RETRIEVER] [OK] Split into {len(all_chunks)} chunks")
        
        # Create embeddings and vector store
        print(f"  [RETRIEVER] ⏳ Generating embeddings (this may take a moment)...")
        self.vector_store = FAISS.from_documents(
            documents=all_chunks,
            embedding=self.embeddings
        )
        
        print(f"  [RETRIEVER] [OK] Vector store created with {len(all_chunks)} vectors")
        return self.vector_store
    
    def get_retriever(self, search_type: str = "similarity"):
        """
        Get a retriever from the vector store.
        
        Args:
            search_type: Type of search ("similarity" or "mmr")
            
        Returns:
            Retriever instance
        """
        if self.vector_store is None:
            raise ValueError("Vector store not built. Call build_vector_store() first.")
        
        retriever = self.vector_store.as_retriever(
            search_type=search_type,
            search_kwargs={"k": self.k}
        )
        
        print(f"  [RETRIEVER] [OK] Retriever configured (k={self.k})")
        return retriever
    
    def save_vector_store(self, path: str) -> None:
        """
        Save vector store to disk.
        
        Args:
            path: Directory path to save the vector store
        """
        if self.vector_store is None:
            raise ValueError("Vector store not built. Call build_vector_store() first.")
        
        save_path = Path(path)
        save_path.mkdir(parents=True, exist_ok=True)
        
        self.vector_store.save_local(str(save_path))
        print(f"  [RETRIEVER] [OK] Vector store saved to {save_path}")
    
    def load_vector_store(self, path: str) -> None:
        """
        Load vector store from disk.
        
        Args:
            path: Directory path to load the vector store from
        """
        load_path = Path(path)
        
        if not load_path.exists():
            raise FileNotFoundError(f"Vector store not found at {load_path}")
        
        self.vector_store = FAISS.load_local(
            str(load_path),
            self.embeddings,
            allow_dangerous_deserialization=True
        )
        
        print(f"  [RETRIEVER] [OK] Vector store loaded from {load_path}")

