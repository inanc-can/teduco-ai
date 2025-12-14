import json
from pathlib import Path
from typing import Dict, List
from langchain_text_splitters import MarkdownHeaderTextSplitter
from langchain_core.documents import Document


class MarkdownHeaderSplitter:
    """
    Split markdown content by H2 headers (##) and organize content by header keys.
    
    This class uses LangChain's MarkdownHeaderTextSplitter to break down markdown
    documents into sections based on H2 headers.
    """
    
    def __init__(self, headers_to_split_on: List[tuple] = [("##", "Header 2")]):
        """
        Initialize the splitter.
        
        Args:
            headers_to_split_on: List of (header_symbol, header_name) tuples.
                Defaults to [("##", "Header 2")] for H2 headers.
        """
        
        self.headers_to_split_on = headers_to_split_on
        self.splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=headers_to_split_on
        )
    
    def split_by_headers(self, markdown_text: str) -> Dict[str, str]:
        """
        Split markdown content by headers.
        
        Args:
            markdown_text: The markdown content to split.
        
        Returns:
            Dictionary with headers as keys and content as values.
        
        Raises:
            ValueError: If markdown_text is empty or None.
        """
        if not markdown_text or not isinstance(markdown_text, str):
            raise ValueError("markdown_text must be a non-empty string")
        
        splits: List[Document] = self.splitter.split_text(markdown_text)
        content_by_header: Dict[str, str] = {}
        
        for split in splits:
            header = split.metadata.get("Header 2", "Untitled").strip()
            content = split.page_content.strip()
            
            if header in content_by_header:
                content_by_header[header] += "\n\n" + content
            else:
                content_by_header[header] = content
        
        return content_by_header
    
    def export_to_json(self, content_dict: Dict[str, str], output_path: Path) -> None:
        """
        Export content dictionary to JSON file.
        
        Args:
            content_dict: Dictionary with headers and content.
            output_path: Path where the JSON file will be saved.
        
        Raises:
            IOError: If the file cannot be written.
        """
        try:
            output_file = output_path / "aptitude-assessment-de.json"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with output_file.open("w", encoding="utf-8") as f:
                json.dump(content_dict, f, ensure_ascii=False, indent=2)
            
            print(f"✓ Exported {len(content_dict)} headers to {output_path}")
        except IOError as e:
            raise IOError(f"Failed to write to {output_path}: {str(e)}")
    
    def split_and_export(self, markdown_text: str, output_path: Path) -> Dict[str, str]:
        """
        Split markdown and export to JSON in one call.
        
        Args:
            markdown_text: The markdown content.
            output_path: Path for the output JSON file.
        
        Returns:
            Dictionary with headers and content.
        """
        content_dict = self.split_by_headers(markdown_text)
        self.export_to_json(content_dict, output_path)
        return content_dict
    
    def get_headers_list(self, markdown_text: str) -> List[str]:
        """
        Get list of all H2 headers in the markdown.
        
        Args:
            markdown_text: The markdown content.
        
        Returns:
            List of header names in order of appearance.
        """
        content_dict = self.split_by_headers(markdown_text)
        return list(content_dict.keys())