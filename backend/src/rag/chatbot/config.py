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
RETRIEVAL_K = 10  # Number of documents to retrieve

# Retrieval quality threshold
SIMILARITY_THRESHOLD = 0.25  # Minimum hybrid score (0-1) to use a document
# Lowered from 0.40 because multilingual MiniLM produces lower cosine similarities
# and the normalized hybrid score combines semantic + keyword proportionally

# Hybrid search weights
SEMANTIC_WEIGHT = 0.5
KEYWORD_WEIGHT = 0.5

# Crawler configuration
TUM_BASE_URL = "https://www.tum.de"
TUM_DETAIL_SUFFIX = "/en/studies/degree-programs/detail/"

# Pipeline settings
USE_CACHE = True  # Use cached data if available
FORCE_RECRAWL = False  # Force fresh crawl even if cache exists

