"""
Document Loader Module

Loads documents from crawled data using the parser/crawler components.
This module bridges the gap between the crawler and the RAG pipeline.
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import traceback
from langchain_core.documents import Document

# Add parent directories to path for imports
CURRENT_DIR = Path(__file__).parent  # backend/rag/chatbot
RAG_DIR = CURRENT_DIR.parent          # backend/rag
BACKEND_DIR = RAG_DIR.parent          # backend
PARSER_DIR = RAG_DIR / "parser"       # backend/rag/parser
CHUNKER_DIR = RAG_DIR / "chunker"     # backend/rag/chunker

# Add paths similar to how crawler.py does it
sys.path.insert(0, str(BACKEND_DIR))  # Add backend to path
sys.path.insert(0, str(RAG_DIR))      # Add rag to path
sys.path.insert(0, str(PARSER_DIR))   # Add parser to path
sys.path.insert(0, str(CHUNKER_DIR))  # Add chunker to path

# Import using the same pattern as crawler.py
# The crawler imports like: from chunker.langchain_splitters import MarkdownSplitter
# So we need to be in a context where 'chunker' and 'parser' are importable

# from parser.crawler import TumDegreeParser
from chunker.langchain_splitters import (
    MarkdownHeaderSplitter,
    RecursiveTextSplitter
)


class DocumentLoader:
    """
    Loads and processes documents from crawled TUM degree program data.
    
    This class:
    1. Uses the crawler to fetch data from web (or loads from cache)
    2. Processes JSON and markdown files from crawled data
    3. Converts them into LangChain Document objects for the RAG pipeline
    """
    
    def __init__(self, data_dir: str = "backend/rag_data"):
        """
        Initialize the document loader.
        
        Args:
            data_dir: Directory where crawled data is stored
        """
        self.data_dir = Path(data_dir)
        # self.data_dir.mkdir(parents=True, exist_ok=True)
        # self.crawler = TumDegreeParser(data_dir=str(self.data_dir))
        self.university = "TUM"
        self.md_splitter = MarkdownHeaderSplitter()
    
    def load_from_local_dir(
        self, 
        program_slugs: Optional[List[str]] = None,
    ):
        """
        Load documents from local directory.
        
        Args:
            program_slugs: List of program slugs to load. If None, uses default list.
        
        Returns:
            List of Document objects ready for chunking and embedding
        """
        documents = []
        
        # Default program slugs if none provided
        if program_slugs is None:
            program_slugs = [
                "informatics-master-of-science-msc",
                "mathematics-master-of-science-msc",
                "mathematics-in-data-science-master-of-science-msc",
                "mathematics-in-science-and-engineering-master-of-science-msc",
                "mathematical-finance-and-actuarial-science-master-of-science-msc",
                "informatics-games-engineering-master-of-science-msc",
                "informatics-bachelor-of-science-bsc"
            ]
        
        print(f"\n[LOADER] Loading documents for {len(program_slugs)} programs...")
        for slug in program_slugs:
            program_dir = self.data_dir / slug
            docs = self._load_from_cache(program_dir, slug)
            documents.extend(docs)
        
        print(f"  [LOADER] [OK] Loaded {len(documents)} total document from local cache.")
        return documents
        
    # def load_from_crawler(
    #     self, 
    #     program_slugs: Optional[List[str]] = None,
    #     use_cache: bool = True
    # ) -> List[Document]:
    #     """
    #     Load documents by running the crawler or loading from cache.
        
    #     Args:
    #         program_slugs: List of program slugs to crawl. If None, uses default list.
    #         use_cache: If True, loads from existing files instead of crawling
        
    #     Returns:
    #         List of Document objects ready for chunking and embedding
    #     """
    #     documents = []
        
    #     # Default program slugs if none provided
    #     if program_slugs is None:
    #         program_slugs = [
    #             "informatics-master-of-science-msc",
    #             "mathematics-master-of-science-msc",
    #             "mathematics-in-data-science-master-of-science-msc",
    #             "mathematics-in-science-and-engineering-master-of-science-msc",
    #             "mathematical-finance-and-actuarial-science-master-of-science-msc",
    #             "informatics-games-engineering-master-of-science-msc",
    #             "informatics-bachelor-of-science-bsc"
    #         ]
        
    #     print(f"\n[LOADER] Loading documents for {len(program_slugs)} programs...")
        
    #     for slug in program_slugs:
    #         program_dir = self.data_dir / slug
            
    #         # If cache exists and use_cache is True, load from files
    #         if use_cache and program_dir.exists():
    #             print(f"  [LOADER] Loading cached data for: {slug}")
    #             docs = self._load_from_cache(program_dir, slug)
    #             documents.extend(docs)
    #         else:
    #             # Run crawler to fetch fresh data
    #             print(f"  [LOADER] Crawling fresh data for: {slug}")
    #             docs = self._crawl_and_load(slug)
    #             documents.extend(docs)
        
    #     print(f"  [LOADER] [OK] Loaded {len(documents)} total documents")
    #     return documents
    
    # def _crawl_and_load(self, program_slug: str) -> List[Document]:
    #     """
    #     Crawl a program and convert to documents.
        
    #     Args:
    #         program_slug: Program slug to crawl
            
    #     Returns:
    #         List of Document objects
    #     """
    #     documents = []
    #     data = None
    #     try:
    #         # Run crawler
    #         self.crawler.load_by_slug(program_slug)
    #         self.crawler.parse(program_slug)
    #         data = self.crawler.to_dict()
    #         self.crawler.save_json(data, program_slug)

    #         # Load the generated files
    #         program_dir = self.data_dir / program_slug
    #         docs = self._load_from_cache(program_dir, program_slug)
    #         documents.extend(docs)

    #     except Exception as e:
    #         traceback.print_exc()
    #         print(f"  [LOADER] [FAIL] Error crawling {program_slug}: {e}")

    #     return documents
    
    def _load_from_cache(self, program_dir: Path, program_slug: str) -> List[Document]:
        """
        Load documents from cached files in program directory.
        
        Args:
            program_dir: Directory containing program files
            program_slug: Program slug for metadata
            
        Returns:
            List of Document objects
        """
        documents = []
        
        # Load JSON metadata file
        json_file = program_dir / f"{program_slug}.json"
        if json_file.exists():
            print(f"    [LOADER] Found JSON file: {json_file.name}")
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert JSON to documents
            json_docs = self._json_to_documents(data, program_slug)
            print(f"    [LOADER] Converted JSON to {len(json_docs)} documents")
            documents.extend(json_docs)
        else:
            print(f"    [LOADER] WARNING: JSON file not found: {json_file}")
        
        # Load markdown chunks from aptitude assessment
        md_json_file = program_dir / "aptitude-assessment-de.json"
        if md_json_file.exists():
            with open(md_json_file, 'r', encoding='utf-8') as f:
                md_data = json.load(f)
            
            # Convert markdown chunks to documents
            md_docs = self._markdown_chunks_to_documents(md_data, program_slug)
            documents.extend(md_docs)
        
        # Also try loading markdown file directly if JSON doesn't exist
        md_file = program_dir / "aptitude-assessment-de.md"
        if md_file.exists() and not md_json_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
                md_content = f.read()
            
            # Split markdown by headers
            md_chunks = self.md_splitter.split_markdown(md_content)
            md_mapping = self.md_splitter.build_header_content_mapping(md_chunks)
            md_docs = self._markdown_chunks_to_documents(md_mapping, program_slug)
            documents.extend(md_docs)
        
        return documents
    
    def _json_to_documents(self, data: Dict[str, Any], program_slug: str) -> List[Document]:
        """
        Convert JSON metadata to Document objects.
        
        Improved version that creates better documents for RAG:
        - Keeps related information together
        - Adds context about the program
        - Creates more searchable content
        
        Args:
            data: JSON data dictionary
            program_slug: Program slug for metadata
            
        Returns:
            List of Document objects
        """
        documents = []
        
        # Extract program name from slug for context
        program_name = program_slug.replace("-", " ").title()
        
        def create_document(section: str, key: str, value: Any, full_path: str = "") -> None:
            """Create a document with better formatting for searchability."""
            # Add relevant keywords based on the key to improve searchability
            keywords = ""
            if "deadline" in key.lower() or "period" in key.lower():
                keywords = "\n(Application deadline, admission deadline, application period, when to apply)"
            elif "admission" in key.lower() or "requirement" in key.lower():
                keywords = "\n(Admission requirements, entry requirements)"
            elif "credit" in key.lower() or "ects" in key.lower():
                keywords = "\n(ECTS credits, credit points, course credits, total credits required)"
            elif "language" in key.lower() or "proficiency" in key.lower():
                keywords = "\n(Language requirements, language proficiency, German requirement, English requirement, language certificate, language test)"
            
            # Format the content to be more searchable
            if isinstance(value, str) and len(value) > 50:
                # For long text values, create a document with context
                content = f"Program: {program_name}\nSection: {section}\nTopic: {key}\n\n{value}{keywords}"
                # Debug: Verify long documents are created correctly
                if key == "Application deadlines" or key == "Application Period":
                    print(f"      [LOADER DEBUG] Created '{key}' document:")
                    print(f"        Length: {len(content)} characters")
                    print(f"        Preview: {content[:150]}...")
            elif isinstance(value, (dict, list)):
                # For nested structures, convert to readable format
                if isinstance(value, list):
                    # Handle lists - join items or format nicely
                    if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                        # List of dicts (like links or credits)
                        items = []
                        credit_values = []  # Track credit information separately
                        for item in value:
                            if isinstance(item, dict):
                                for k, v in item.items():
                                    # Special handling for credits: extract the number
                                    if key.lower() == "credits" and "ects" in k.lower():
                                        credit_values.append(k)  # e.g., "120 ECTS"
                                    items.append(f"{k}: {v}")
                            else:
                                items.append(str(item))
                        
                        # For credits, make the answer more explicit
                        if credit_values:
                            value_str = f"The {program_name} program requires {', '.join(credit_values)}."
                            if items:  # Include links if present
                                value_str += f"\n\nDetails:\n" + "\n".join(items)
                        else:
                            value_str = "\n".join(items)
                    else:
                        value_str = ", ".join(str(v) for v in value)
                    content = f"Program: {program_name}\nSection: {section}\n{key}: {value_str}{keywords}"
                else:
                    # Dict - format as key-value pairs
                    value_str = "\n".join([f"{k}: {v}" for k, v in value.items()])
                    content = f"Program: {program_name}\nSection: {section}\n{key}:\n{value_str}"
            else:
                # Simple value - keywords already set above
                content = f"Program: {program_name}\nSection: {section}\n{key}: {value}{keywords}"
            
            # Parse degree, degree level information
            degree, degree_level = self._parse_program_slug(program_slug)
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": program_slug,
                        "university": self.university,
                        "degree": degree,
                        "degree_level": degree_level,
                        "type": "metadata",
                        "section": section,
                        "key": key,
                        "full_path": full_path or f"{section}/{key}"
                    }
                )
            )
        
        # Process the JSON structure more intelligently
        # Top-level sections (Key Data, Application and Admission)
        for section_name, section_data in data.items():
            if isinstance(section_data, dict):
                # Process each key-value pair in the section
                for key, value in section_data.items():
                    full_path = f"{section_name}/{key}"
                    create_document(section_name, key, value, full_path)
            else:
                # Direct value
                create_document("General", section_name, section_data, section_name)
        
        print(f"      [LOADER] Created {len(documents)} documents from JSON for {program_slug}")
        return documents
    
    def _markdown_chunks_to_documents(
        self, 
        md_chunks: Dict[str, str], 
        program_slug: str
    ) -> List[Document]:
        """
        Convert markdown chunks to Document objects.
        
        Args:
            md_chunks: Dictionary of header -> content
            program_slug: Program slug for metadata
            
        Returns:
            List of Document objects
        """
        documents = []
        degree, degree_level = self._parse_program_slug(program_slug)
        for header, content in md_chunks.items():
            documents.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": program_slug,
                        "university": self.university,
                        "degree": degree,
                        "degree_level": degree_level,
                        "type": "aptitude_assessment",
                        "header": header,
                        "section": f"aptitude_assessment/{header}"
                    }
                )
            )
        
        return documents

    def _parse_program_slug(self, program_slug: str):
        """
        Parse a hyphen-separated program slug into degree and level.

        Args:
            program_slug: Hyphen-separated slug (e.g. "informatics-master-of-science-msc").

        Returns:
            Tuple[str, Optional[str]]: `(degree, degree_level)` where `degree` is
            the part before 'master'/'bachelor' (or the original slug if not found),
            and `degree_level` is 'master', 'bachelor', or `None`.
        """

        parts = program_slug.split("-")
        degree_level = None
        degree = program_slug
        for idx, part in enumerate(parts):
            p = part.lower()
            if p in ("master", "bachelor"):
                degree_level = p
                degree = "-".join(parts[:idx]) if idx > 0 else ""
                break
        return degree, degree_level


def loaded_docs_to_chunks(documents: List[Document], chunk_size, chunk_overlap):
    """
    Split documents into character-based chunks while preserving short docs.

    Args:
        documents: List of `Document` objects to split or keep.
        chunk_size: Maximum characters per chunk.
        chunk_overlap: Number of overlapping characters between chunks.

    Returns:
        List[Document]: Flattened list of document chunks.
    """

    text_splitter = RecursiveTextSplitter(chunk_size, chunk_overlap)
    all_chunks = []

    for doc in documents:
        # If document is already from markdown chunks, use as-is
        if doc.metadata.get("type") == "aptitude_assessment":
            # Already chunked by markdown splitter, just add to chunks
            chunks = text_splitter.split_documents([doc])
            all_chunks.extend(chunks)
        else:
            # For metadata/JSON content, only split if document is very long
            # Most metadata documents are complete units and shouldn't be split
            doc_length = len(doc.page_content)
            doc_key = doc.metadata.get("key", "unknown")
            
            # Only split if document is significantly longer than chunk_size
            # This preserves complete information for metadata documents
            if doc_length > chunk_size * 2:  # Only split if > 3x chunk_size (1500+ chars)
                # Document is long enough to warrant splitting
                chunks = text_splitter.split_documents([doc])
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
    return all_chunks