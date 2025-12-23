from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
from docling.datamodel.base_models import InputFormat
from docling_core.types.io import DocumentStream
from docling.datamodel.document import ConversionResult
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions
)
from docling_core.types.doc.document import DoclingDocument
from docling.document_converter import DocumentConverter, PdfFormatOption
from pathlib import Path
from io import BytesIO
import logging
from typing import Optional, Union, cast

# Configure logging
logging.basicConfig(level=logging.INFO)

class DoclingPDFParser:
    """
    Parser for converting PDF files using Docling and exporting results.

    This class encapsulates the Docling pipeline options and exposes simple
    methods to convert a PDF file into a Docling ConversionResult and to
    export the converted document to Markdown (optionally persisting it).

    Attributes:
        pipeline_options: PdfPipelineOptions configured for OCR and table detection.
        doc_converter: DocumentConverter instance configured for PDF input.
    """

    def __init__(self, force_full_page_ocr: bool = False) -> None:
        """
        Initialize the PDF parser with Docling pipeline options.

        Args:
            force_full_page_ocr: Whether to apply OCR to full pages instead of
            detected text regions only.
        """
        logging.info("Initializing DoclingPDFParser...")
        self.force_full_page_ocr = force_full_page_ocr
        self.pipeline_options = PdfPipelineOptions(
            do_ocr=True,
            ocr_options=EasyOcrOptions(
                force_full_page_ocr=self.force_full_page_ocr,
                lang=["de", "en"]
            ),
            accelerator_options=AcceleratorOptions(
                device=AcceleratorDevice.AUTO
            ),
            do_table_structure=True
        )
        self.doc_converter = DocumentConverter(
            format_options={
                InputFormat.PDF: PdfFormatOption(
                    pipeline_options=self.pipeline_options)
            }
        )
        logging.info("DoclingPDFParser initialized.")

    def convert_document(
            self,
            source: Union[Path, bytes, str, DocumentStream],
            name: Optional[str] = None
        ) -> ConversionResult:
        """
        Convert a PDF source into a Docling ConversionResult.

        Args:
            source: Either a Path/str to a file, raw PDF bytes
                    (e.g. requests.Response.content), or a DocumentStream.
            name: Optional filename to use when source is bytes or
                    a stream (used by conversion.input.file).

        Returns:
            ConversionResult: The full conversion result produced by Docling.

        Example:
            response = requests.get(url)
            pdf_bytes = response.content
            conversion = parser.convert_document(
                pdf_bytes, name="aptitude-assessment-de.pdf")
        """
        logging.info(f"Converting document from source type {type(source)}...")
        try:
            # if raw bytes: wrap into a BytesIO and DocumentStream with a sensible name
            if isinstance(source, (bytes, bytearray)):
                buff = BytesIO(source)
                filename = name or "file.pdf"
                if not filename.endswith(".pdf"):
                    # keep extension for downstream components
                    filename = f"{filename}.pdf"
                doc_stream = DocumentStream(name=filename, stream=buff)
                # cast to the expected union type for the converter
                conversion = self.doc_converter.convert(
                    cast(Union[Path, str, DocumentStream], doc_stream))
            # if already a DocumentStream, pass through (cast for the type checker)
            elif isinstance(source, DocumentStream):
                conversion = self.doc_converter.convert(
                    cast(Union[Path, str, DocumentStream], source))
            # Path or str (or any other accepted type): cast source to the expected union
            else:
                conversion = self.doc_converter.convert(
                    cast(Union[Path, str, DocumentStream], source))
        except Exception as e:
            logging.exception("Failed to convert document.")
            raise RuntimeError(f"Document conversion failed for \
                        {getattr(source, 'name', source)}: {e}") from e
        logging.info("Document conversion completed.")
        return conversion

    def conversion_to_markdown(
            self,
            conversion: ConversionResult,
            out_file_path: Optional[Path] = None,
            file_name: Optional[str] = None) -> str:
        """
        Produce a Markdown representation from a ConversionResult.

        The method returns the Markdown string generated from conversion.document.
        If out_file_path is provided it will be treated as a directory path and the
        Markdown will be written to `<out_file_path>/<input_filename>.md`.

        Args:
            conversion: ConversionResult returned by convert_document().
            out_file_path: Optional directory Path where the Markdown file will be
                           written. If provided, the directory will be created if necessary.
            file_name: file name for the output file.

        Returns:
            str: The generated Markdown content.
        """
        logging.info("Exporting document to markdown string...")
        try:
            md = conversion.document.export_to_markdown()
        except Exception as e:
            logging.exception("Failed to export conversion to markdown.")
            raise RuntimeError(f"Export to markdown failed for input \
                {getattr(conversion, 'input', None)}: {e}") from e

        if out_file_path:
            out_file = out_file_path / f"{file_name}.md"
            try:
                self.export_to_markdown(md, out_file)
            except Exception as e:
                logging.exception("Failed to write markdown to disk.")
                raise RuntimeError(f"Writing markdown failed for {out_file}: {e}") from e
        logging.info("Document exported to markdown.")
        return md

    def export_to_markdown(self, md: str, out_file_path: Path) -> Path:
        """
        Persist markdown content to disk, ensuring parent directories exist.

        Args:
            md: Markdown content to write.
            out_file_path: Destination file path (including filename) to write the markdown.

        Returns:
            Path: The written file path.
        """
        try:
            out_file_path.parent.mkdir(parents=True, exist_ok=True)
            with out_file_path.open("w", encoding="utf-8") as fp:
                fp.write(md)
        except Exception as e:
            logging.exception("Failed to persist markdown file.")
            raise RuntimeError(f"Failed to write markdown to {out_file_path}: {e}") from e
        logging.info(f"Markdown written to {out_file_path}")
        return out_file_path
