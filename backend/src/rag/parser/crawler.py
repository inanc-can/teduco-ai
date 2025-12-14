import re
import os
import sys
import bs4
import json
import logging
import requests
import argparse
from pathlib import Path
from urllib.parse import urljoin
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from conversion import DoclingPDFParser
from langchain_community.document_loaders import WebBaseLoader
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))          # .../rag/parser
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, ".."))   # .../rag
sys.path.append(PROJECT_ROOT)
from chunker.langchain_splitters import MarkdownHeaderSplitter


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

class TumDegreeParser:
    """
    Generic parser for TUM degree program pages.

    Usage:
        parser = TumDegreeParser()
        parser.load_by_slug("informatics-master-of-science-msc")
        parser.parse()
        data = parser.to_dict()
    """

    WHITESPACE_RE = re.compile(r"\s+")

    def __init__(
        self,
        data_dir: str,
        base_url: str = "https://www.tum.de",
        detail_suffix: str = "/en/studies/degree-programs/detail/",
    ) -> None:
        """
        Initialize a TUM degree page parser.

        Args:
            base_url (str): TUM root URL.
            detail_suffix (str): Path prefix for program detail pages.
        """
        load_dotenv()
        self.base_url = base_url.rstrip("/")
        self.detail_suffix = detail_suffix
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.notify(f"{self.data_dir} created.")
        self.soup: Optional[bs4.BeautifulSoup] = None
        self.pdf_parser = DoclingPDFParser()
        self.bluebox: Dict[str, Any] = {}
        self.accordion: Dict[str, Any] = {}
        self.md_header_splitter = MarkdownHeaderSplitter()
        

    def notify(self, message: str) -> None:
        """Log a message like a print statement."""
        logging.info(message)

    def clean(self, text: str) -> str:
        """
        Normalize whitespace by replacing sequences of whitespace
        with a single space and stripping leading/trailing spaces.

        Args:
            text (str): Input text.

        Returns:
            str: Cleaned text.
        """
        cleaned = self.WHITESPACE_RE.sub(" ", text).strip()
        return cleaned

    def load_by_slug(self, program_slug: str) -> "TumDegreeParser":
        """
        Load the HTML page for a degree program using its slug.

        Args:
            program_slug (str): Program slug as used in TUM URLs.

        Returns:
            TumDegreeParser: Self, for method chaining.
        """

        url = f"{self.base_url}{self.detail_suffix}{program_slug}"
        return self.load_by_url(url)

    def load_by_url(self, url: str) -> "TumDegreeParser":
        """
        Load and parse the HTML page from a direct URL.

        Args:
            url (str): Full URL to load.

        Returns:
            TumDegreeParser: Self for method chaining.
        """
        loader = WebBaseLoader(
            web_path=url,
            default_parser="html.parser",
        )
        docs = loader.scrape()

        if isinstance(docs, bs4.BeautifulSoup):
            self.soup = docs
        else:
            self.soup = bs4.BeautifulSoup(str(docs), "html.parser")

        return self

    def parse(self, program_slug: str) -> "TumDegreeParser":
        """
        Parse the loaded HTML into structured data:
        - Bluebox section ("Key Data")
        - Second accordion ("Application and Admission")

        Returns:
            TumDegreeParser: Self for chaining.

        Raises:
            RuntimeError: If HTML hasn't been loaded yet.
        """
        if self.soup is None:
            raise RuntimeError("HTML not loaded. Call load_by_slug() or load_by_url() first.")

        self.bluebox = self.parse_bluebox()
        self.accordion = self.parse_accordion(program_slug)
        return self

    def parse_bluebox(self) -> Dict[str, Any]:
        """
        Parse the `bluebox` section containing key data about the program.

        Returns:
            Dict[str, Any]: Mapping of key/value pairs extracted from the bluebox.
        """
        if not self.soup:
            return {}

        bluebox_div = self.soup.find("div", class_="bluebox")
        result: Dict[str, Any] = {}

        if not bluebox_div:
            return result

        for child in bluebox_div.find_all("div"):
            strong_tags = child.select("strong")
            if not strong_tags:
                continue

            key = self.clean(strong_tags[0].get_text(strip=True))
            list_items = child.select("ul li")

            # Case 1: single <p> value
            if not list_items:
                p = child.select_one("p")
                value = self.clean(p.get_text(strip=True)) if p else ""

            # Case 2: list of items (with or without links)
            else:
                values = []
                for li in list_items:
                    a = li.find("a")
                    if a and a.get("href"):
                        values.append({
                            self.clean(li.get_text(strip=True)): self.base_url + str(a["href"])
                        })
                    else:
                        values.append(self.clean(li.get_text(strip=True)))
                value = values

            result[key] = value

        return result

    def parse_accordion(self, program_slug: str) -> Dict[str, Any]:
        """
        Parse the second `accordion` section.
        Typically contains "Application and Admission" info.

        Returns:
            Dict[str, Any]: Mapping of accordion entry titles to text content.
        """
        if not self.soup:
            return {}

        accordion_divs = self.soup.find_all("div", class_="accordion")
        result: Dict[str, Any] = {}

        if len(accordion_divs) < 2:
            return result

        second_accordion = accordion_divs[1]

        for child in second_accordion.find_all("div", class_="in2template-accordion"):
            title_el = child.select_one("button span")
            if not title_el:
                continue

            key = self.clean(title_el.get_text(" ", strip=True))
            if key == "Admission process":
                href_suffix = str(child.select("ul li a")[1]["href"])

                # download aptitude assessment pdf
                slug_url = f"{self.base_url}{self.detail_suffix}{program_slug}"
                download_url = urljoin(slug_url, href_suffix)
                output_dir = self.data_dir / program_slug
                output_dir.mkdir(exist_ok=True)
                output_path = self.data_dir / f"{program_slug}/aptitude-assessment-de.pdf"
                
                # download_pdf returns raw bytes; set write_to_disk=True to also save file
                pdf_bytes = self.download_pdf(download_url, output_path, write_to_disk=True)
                # convert using Docling: pass bytes + original filename so conversion.input.file is populated
                # split by headers
                try:
                    conversion = self.pdf_parser.convert_document(pdf_bytes)
                    # optionally export markdown
                    try:
                        md = self.pdf_parser.conversion_to_markdown(conversion, output_dir)
                        self.md_header_splitter.split_and_export(md, output_dir)
                        self.notify(f"Converted PDF to markdown for {program_slug}.")
                    except Exception as e:
                        logging.exception("Markdown export failed")
                        self.notify(f"Markdown export failed for {program_slug}")
                except Exception as e:
                    logging.exception("PDF conversion failed")
                    self.notify(f"PDF conversion failed for {program_slug}")

            body = child.find(class_="ce-textmedia")
            if not body:
                continue

            value_text = self.clean(body.get_text(" ", strip=True))
            result[key] = value_text

        return result

    def download_pdf(self, url: str, output_path: Optional[Path] = None, write_to_disk: bool = True) -> bytes:
        """
        Download aptitude assessment PDF and return raw bytes.

        Args:
            url: URL to download the PDF from.
            output_path: Optional Path to save the PDF. If provided and write_to_disk is True,
                         the file will be written to disk.
            write_to_disk: If False, do not write the downloaded bytes to disk even if output_path is provided.

        Returns:
            bytes: Raw PDF content (response.content)
        """
        response = requests.get(url)
        response.raise_for_status()  # error if download fails
        pdf_bytes = response.content
        if output_path and write_to_disk:
            with open(output_path, "wb") as f:
                f.write(pdf_bytes)
            self.notify(f"{output_path} file downloaded.")
        return pdf_bytes

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert parsed data into a JSON-serializable structure.

        Returns:
            Dict[str, Any]: Combined bluebox + accordion data.
        """
        return {
            "Key Data": self.bluebox,
            "Application and Admission": self.accordion,
        }

    def save_json(self, data: Dict, program_slug: str):
        """
        Save parsed data into a JSON file.

        Args:
            path (Path): Output file path.
        """
        output_dir = self.data_dir / program_slug
        output_dir.mkdir(exist_ok=True)
        file_name = self.data_dir / f"{program_slug}/{program_slug}.json"
        with file_name.open("w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
        self.notify(f"{program_slug} files created.")


def scrape_all(program_slugs):
    parser = argparse.ArgumentParser(description="Run crawler")
    parser.add_argument("--data-dir", help="Path to crawler data dir.")
    args = parser.parse_args()
    data_dir = args.data_dir or "backend/src/rag/data"
    parser = TumDegreeParser(data_dir=data_dir)
    for ps in program_slugs:
        parser.load_by_slug(ps)
        parser.parse(ps)
        data = parser.to_dict()
        parser.save_json(data, ps)


if __name__ == "__main__":
    program_slugs = [
        "informatics-master-of-science-msc",
        "mathematics-master-of-science-msc",
        "mathematics-in-data-science-master-of-science-msc",
        "mathematics-in-science-and-engineering-master-of-science-msc",
        "mathematical-finance-and-actuarial-science-master-of-science-msc",
        "informatics-games-engineering-master-of-science-msc",
        "informatics-bachelor-of-science-bsc"
        # TODO: scrape all degrees afterwards
    ]
    scrape_all(program_slugs)
