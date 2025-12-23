import re
import os
import json
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter, 
    RecursiveCharacterTextSplitter
)
from langchain_core.documents import Document


class MarkdownSplitter:
    """
    Split Markdown documents into sections and optional text chunks.

    This class uses a Markdown header splitter to divide content by headers
    and a recursive character text splitter to further split large sections
    into manageable chunks.
    """
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 150,
        text_separators: Optional[List[str]] = None,
        headers_to_split_on: Optional[List[Tuple[str, str]]] = None,
    ):
        """
        Initialize the document splitter.

        Args:
            chunk_size: Max characters per chunk
            chunk_overlap: Overlap between chunks
            text_separators: Character split priority
            headers_to_split_on: Markdown headers for semantic splitting
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_separators = text_separators or [
            "\n\n", "\n", "- ", "; ", " "
        ]
        self.headers_to_split_on = headers_to_split_on or [
            ("##", "Header 2")
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )
        self.character_text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.text_separators
        )

    
    def split_markdown(self, markdown_text: str, doc_type: str) -> List[Document]:
        """
        Split markdown content by headers.
        
        Args:
            markdown_text: The markdown content to split.
            doc_type: Doc type information for the chunk metadata.
        
        Returns:
            List of Document objects containing splitted text based on headers.
        
        Raises:
            ValueError: If markdown_text is empty or None.
        """
        if not markdown_text or not isinstance(markdown_text, str):
            raise ValueError("markdown_text must be a non-empty string")
        
        splits: List[Document] = self.header_splitter.split_text(markdown_text)
        documents: List[Document] = []
        for split in splits:
            header = split.metadata.get("Header 2", "Untitled").strip()
            content = split.page_content.strip()
            cleaned_content = self.normalize_text(content)
            chunks = self.text_to_chunks(header, cleaned_content, doc_type)
            documents.extend(chunks)
        return documents
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text by cleaning common OCR and formatting artifacts.

        Args:
            text: Raw text to normalize.

        Returns:
            Normalized text with cleaned spacing and punctuation.
        """
        text = re.sub(r"[‘’“”]", "'", text)
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = text.replace(" ;", ";").replace(" ,", ",")
        return text.strip()

    def text_to_chunks(
        self,
        title: str,
        text: str,
        doc_type: str
    ) -> List[Document]:
        """
        Split text into chunks and wrap them as LangChain Document objects.

        Args:
            title: Section title used as metadata.
            text: Text content to split.
            doc_type: Document type identifier.

        Returns:
            List of Document objects containing chunked text and metadata.
        """
        chunks = []
        splits = self.character_text_splitter.split_text(text)

        for i, split in enumerate(splits):
            chunks.append(
                Document(
                    page_content=split,
                    metadata={
                        "section_title": title,
                        "section_index": i,
                        "doc_type": doc_type
                    }
                )
            )

        return chunks

    def export_to_json(
            self,
            chunks: List[Document],
            output_path: Optional[Union[str, Path]],
            file_name: str
        ) -> None:
        """
        Export content dictionary to JSON file.
        
        Args:
            chunks: List of Document objects containing chunked text and metadata.
            output_path: Parent directory where the JSON file will be saved.
            file_name: file name for the output JSON file.
        
        Raises:
            IOError: If the file cannot be written.
        """
        output_path = output_path or os.getcwd()
        if isinstance(output_path, str):
            output_path = Path(output_path) 
        serializable_docs : List[Dict] = []
        for chunk in chunks:
            serializable_docs.append({
                "id": str(uuid.uuid4()),
                "page_content": chunk.page_content,
                "metadata": chunk.metadata
            })
        try:
            output_file = output_path / f"{file_name}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(serializable_docs, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Exported {len(serializable_docs)} chunks to {output_path}")
        except IOError as e:
            raise IOError(f"Failed to write to {output_path}: {str(e)}")
    
    def split_and_export(
            self,
            markdown_text: str,
            output_path: Optional[Union[str, Path]],
            file_name: str,
            doc_type: str
        ) -> List[Document]:
        """
        Split markdown and export to JSON in one call.
        
        Args:
            markdown_text: The markdown content.
            output_path: Parent directory for the output JSON file.
            file_name: file name for the output JSON file.
            doc_type: Doc type information for the chunk metadata.
        
        Returns:
            List of Document objects containing chunked text and metadata.
        """
        chunks = self.split_markdown(markdown_text, doc_type)
        self.export_to_json(chunks, output_path, file_name)
        return chunks