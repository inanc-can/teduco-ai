import re
import os
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from langchain_text_splitters import (
    MarkdownHeaderTextSplitter, 
    RecursiveCharacterTextSplitter
)
from langchain_core.documents import Document


class MarkdownHeaderSplitter:
    """Split markdown text into header-based LangChain Documents."""
    def __init__(
        self,
        headers_to_split_on: Optional[List[Tuple[str, str]]] = None,
    ):
        """Initialize splitter.

        Args:
            headers_to_split_on: List of (markdown_prefix, key) tuples used by
                MarkdownHeaderTextSplitter. Defaults to [("##", "Header 2")].
        """
        self.headers_to_split_on = headers_to_split_on or [
            ("##", "Header 2")
        ]
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=self.headers_to_split_on
        )

    
    def split_markdown(self, markdown_text: str) -> List[Document]:
        """Split markdown content into header sections.

        Args:
            markdown_text: The markdown content to split.

        Returns:
            List[Document]: One document per header section.

        Raises:
            ValueError: If markdown_text is empty or None.
        """
        if not markdown_text or not isinstance(markdown_text, str):
            raise ValueError("markdown_text must be a non-empty string")
        
        splits: List[Document] = self.header_splitter.split_text(markdown_text)
        return splits

    def build_header_content_mapping(
        self,
        chunks: List[Document],
        header_key: str = "Header 2",
        default_header: str = "Untitled",
    ) -> Dict[str, str]:
        """Create a {header: combined_text} mapping from header-split docs.

        Args:
            chunks: Documents that contain header info in metadata.
            header_key: Metadata key that holds the header title.
            default_header: Fallback title if header metadata is missing.

        Returns:
            Dict[str, str]: Mapping from header title to concatenated text.
        """
        content_by_header: Dict[str, str] = {}
        for chunk in chunks:
            header = chunk.metadata.get(header_key, default_header).strip()
            content = chunk.page_content.strip()

            if header in content_by_header:
                content_by_header[header] += "\n\n" + content
            else:
                content_by_header[header] = content

        return content_by_header

    def export_to_json(
            self,
            chunks: List[Document],
            output_path: Optional[Union[str, Path]],
            file_name: str
        ) -> None:
        """Export header → text mapping to a JSON file.

        Args:
            chunks: Documents produced by split_markdown.
            output_path: Directory to write the JSON file to.
            file_name: Base name (without .json) for the output file.

        Raises:
            IOError: If the file cannot be written.
        """
        output_path = output_path or os.getcwd()
        if isinstance(output_path, str):
            output_path = Path(output_path)

        content_by_header = self.build_header_content_mapping(chunks)
        try:
            output_file = output_path / f"{file_name}.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(content_by_header, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Exported markdown-header-json splits to {output_path}")
        except IOError as e:
            raise IOError(f"Failed to write to {output_path}: {str(e)}")
    
    def split_and_export(
            self,
            markdown_text: str,
            output_path: Optional[Union[str, Path]],
            file_name: str,
        ) -> List[Document]:
        """Split markdown and export to JSON in one call.

        Args:
            markdown_text: The markdown content.
            output_path: Directory to write the JSON file to.
            file_name: Base name (without .json) for the output file.

        Returns:
            List[Document]: Documents returned by split_markdown.
        """
        chunks = self.split_markdown(markdown_text)
        self.export_to_json(chunks, output_path, file_name)
        return chunks



class RecursiveTextSplitter:
    """Split plain text/langchain documents into overlapping character-based chunks."""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: Optional[List[str]] = None,
    ):
        """Initialize recursive text splitter.

        Args:
            chunk_size: Maximum characters per chunk.
            chunk_overlap: Number of overlapping characters between chunks.
            separators: Optional list of separator priorities; falls back to
                RecursiveCharacterTextSplitter defaults when None.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [    
            "\n\n",   # paragraph breaks (if present)
            "\n",     # line breaks (VERY important for your text)
            ". ",     # sentence boundaries
            " ",      # word boundaries (fallback)
            ""        # character-level fallback
        ]

        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=self.separators,
        )
    
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split list of documents into chunks.

        Args:
            documents: List of langchain document objects with metadata.

        Returns:
            List[Document]: One document per chunk with metadata.
        """
        return self._splitter.split_documents(documents)

    def split_text(self, text: str) -> List[Document]:
        """Split raw text into LangChain Document chunks.

        Args:
            text: Input text to split.
            doc_type: Value stored in the "doc_type" metadata field.

        Returns:
            List[Document]: One document per chunk with metadata.

        Raises:
            ValueError: If text is empty or not a string.
        """
        if not text or not isinstance(text, str):
            raise ValueError("text must be a non-empty string")

        chunks: List[str] = self._splitter.split_text(text)
        documents: List[Document] = []

        for i, chunk in enumerate(chunks):
            documents.append(
                Document(
                    page_content=chunk,
                    metadata={
                        "chunk_index": i,
                    },
                )
            )

        return documents