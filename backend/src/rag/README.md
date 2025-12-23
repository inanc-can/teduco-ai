# Teduco-AI RAG

RAG (Retrieval-Augmented Generation) module for processing TUM degree program information. This module scrapes program pages, converts PDFs to markdown, and chunks content for vector storage.

## TUM Degree Program Scraper

The script is used to scrape degree program pages from the Technical University of Munich (TUM) and stores structured data (key facts + application/admission info) as JSON files.  
It also downloads the aptitude assessment PDF (German) for programs that have an **"Admission process"** section.

### What it does

For each program slug (e.g. `{degree-name}-master-of-science-msc`):

- Loads the program detail page via `WebBaseLoader` (LangChain)
- Parses:
  - **Bluebox** → "Key Data"
  - **2nd accordion** → "Application and Admission"
- Saves the result as `DATA_DIR/<slug>/<slug>.json`
- If present, downloads the aptitude assessment PDF to  
  `DATA_DIR/<slug>/aptitude-assessment-de.pdf`
- Converts downloaded aptitude assessment PDF to markdown
- Splits markdown by using header tags

### Directory Structure

```
rag/
├── parser/                    # Scraping and PDF conversion
│   ├── crawler.py             # Web scraper for TUM degree programs
│   └── conversion.py          # Docling PDF to markdown converter
├── chunker/                   # Content splitting and chunking
│   └── langchain_splitters.py # Markdown header-based text splitter
├── data/                      # Scraped program data and PDFs
│   └── {program-slug}/
│       ├── {slug}.json                       # Program metadata
│       ├── aptitude-assessment-de.pdf        # Original PDF file
│       ├── aptitude-assessment-de.md         # Converted markdown
│       └── aptitude-assessment-de.json       # Structured JSON chunks
├── docs/                      # Generated documentation
└── README.md
```

### Scripts Overview

#### `parser/crawler.py`
- Main scraper that extracts program information from TUM website
- Uses BeautifulSoup for HTML parsing and WebBaseLoader for page loading
- Handles JSON export and PDF downloading

#### `parser/conversion.py`
- Converts PDF files to markdown using the Docling library
- Supports OCR and table detection
- Returns ConversionResult for downstream processing
- Exports converted content as both markdown (`.md`) and JSON (`.json`)

#### `chunker/langchain_splitters.py`
- Splits markdown content by H2 headers (##)
- Uses LangChain's MarkdownHeaderTextSplitter
- Organizes chunks with metadata for semantic retrieval
- Generates structured JSON output for vector database ingestion

### Data Files

For each degree program, the following files are generated:

- **`{slug}.json`** - Program metadata (key facts, admission info)
- **`aptitude-assessment-de.pdf`** - Original PDF file (if available)
- **`aptitude-assessment-de.md`** - Markdown version of the PDF
- **`aptitude-assessment-de.json`** - Chunked and structured data ready for vector embedding

### Setup

1. Create and activate virtual environment:

```bash
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

2. Configure environment variables:

```bash
cp .ENV.EXAMPLE .env
```

3. Run the scraper:

```bash
python src/rag/parser/crawler.py
```


### TODOs

- [ ] Define comprehensive data schema
- [ ] Increase coverage of scraped degree programs
- [ ] Implement semantic chunking strategies
- [ ] Optimize on-the-fly chunking
- [ ] Vectorstore selection and integration
- [ ] Add error handling and retry logic
- [ ] Performance optimization for large PDF conversions