"""
Configuration file for RAG Chatbot Pipeline

Centralized configuration for easy customization.
"""

from pathlib import Path
from typing import List, Optional

# Data directories
BACKEND_DIR = Path(__file__).parent.parent.parent
RAG_DIR = BACKEND_DIR / "rag"
DATA_DIR = RAG_DIR / "data"
VECTOR_STORE_DIR = DATA_DIR / "vector_store"

# Default program slugs to crawl
DEFAULT_PROGRAM_SLUGS = [
    "informatics-master-of-science-msc",
    "mathematics-master-of-science-msc",
    "mathematics-in-data-science-master-of-science-msc",
    "mathematics-in-science-and-engineering-master-of-science-msc",
    "mathematical-finance-and-actuarial-science-master-of-science-msc",
    "informatics-games-engineering-master-of-science-msc",
    "informatics-bachelor-of-science-bsc"
]

# Model configuration
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # 750 tps - 34% faster than llama-3.1
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Chunking configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
RETRIEVAL_K = 15  # Number of documents to retrieve

# Retrieval quality threshold
SIMILARITY_THRESHOLD = 0.30  # Minimum hybrid score (0-1) to use a document
# With semantic_weight=0.6, a doc with 0.55 semantic sim gets 0.33 hybrid score
# So 0.30 keeps relevant results while filtering noise

# Hybrid search weights
SEMANTIC_WEIGHT = 0.6  # Favor semantic similarity slightly
KEYWORD_WEIGHT = 0.4   # Keywords still important for exact term matching

# Crawler configuration
TUM_BASE_URL = "https://www.tum.de"
TUM_DETAIL_SUFFIX = "/en/studies/degree-programs/detail/"

# Pipeline settings
USE_CACHE = True  # Use cached data if available
FORCE_RECRAWL = False  # Force fresh crawl even if cache exists

