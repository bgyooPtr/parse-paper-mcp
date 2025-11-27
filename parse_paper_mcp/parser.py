"""PDF parsing logic for academic papers."""

import os
import tempfile
from pathlib import Path
from typing import Literal
import pymupdf4llm
import pymupdf

from .image_utils import (
    compress_and_resize_image,
    image_to_base64,
    QualityLevel,
    ImageFormat,
)


class PaperParser:
    """Parser for academic papers in PDF format."""

    def __init__(self, pdf_path: str | Path):
        """
        Initialize parser with PDF file.

        Args:
            pdf_path: Path to the PDF file
        """
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    def extract_text(
        self,
        pages: list[int] | None = None,
        max_chars: int | None = None,
        save_to_file: str | Path | None = None,
    ) -> str:
        """
        Extract text from PDF in Markdown format.

        Args:
            pages: List of page numbers (0-based) to extract. None for all pages.
            max_chars: Maximum number of characters to return. None for no limit.
            save_to_file: Path to save the full text. If provided, only metadata is returned.

        Returns:
            Markdown-formatted text (or metadata if saved to file)
        """
        md_text = pymupdf4llm.to_markdown(str(self.pdf_path), pages=pages)

        # Save to file if requested
        if save_to_file:
            save_path = Path(save_to_file)
            save_path.parent.mkdir(parents=True, exist_ok=True)
            save_path.write_text(md_text, encoding='utf-8')

            return (
                f"# Text Saved to File\n\n"
                f"- **File**: `{save_path}`\n"
                f"- **Size**: {len(md_text):,} characters\n"
                f"- **Pages**: {pages if pages else 'All'}\n\n"
                f"**Preview (first 500 characters):**\n\n{md_text[:500]}"
            )

        # Apply character limit if specified
        original_length = len(md_text)
        if max_chars and len(md_text) > max_chars:
            md_text = md_text[:max_chars]
            md_text += (
                f"\n\n---\n\n"
                f"**⚠️ TEXT TRUNCATED**: Showing {max_chars:,} of {original_length:,} characters "
                f"({100 * max_chars / original_length:.1f}%). "
                f"Use `pages` parameter to extract specific pages, or `save_to_file` to save the full text."
            )

        return md_text

    def extract_images(
        self,
        output_dir: str | Path | None = None,
        quality: QualityLevel = "medium",
        image_format: ImageFormat = "jpg",
        return_base64: bool = False,
    ) -> list[dict]:
        """
        Extract images from PDF with compression using PyMuPDF.

        Args:
            output_dir: Directory to save images (None for temp directory)
            quality: Quality level (high/medium/low)
            image_format: Output format (png/jpg)
            return_base64: If True, return base64 encoded images instead of paths

        Returns:
            List of dictionaries with image information
        """
        # Create output directory
        if output_dir is None:
            output_dir = tempfile.mkdtemp(prefix="parse_paper_")
        else:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)

        # Create a temporary directory for raw images
        temp_dir = Path(tempfile.mkdtemp(prefix="parse_paper_raw_"))

        try:
            # Use PyMuPDF directly for better image extraction
            doc = pymupdf.open(str(self.pdf_path))
            images_info = []

            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                image_list = page.get_images(full=True)

                for img_index, img_info in enumerate(image_list, start=1):
                    xref = img_info[0]

                    try:
                        # Extract image
                        base_image = doc.extract_image(xref)
                        if base_image:
                            image_bytes = base_image["image"]
                            image_ext = base_image["ext"]

                            # Save raw image temporarily
                            raw_image_path = temp_dir / f"temp_{page_num}_{img_index}.{image_ext}"
                            with open(raw_image_path, "wb") as img_file:
                                img_file.write(image_bytes)

                            # Generate output filename
                            output_filename = f"page{page_num + 1}_img{img_index}.{image_format}"
                            output_path = Path(output_dir) / output_filename

                            # Compress and resize
                            metadata = compress_and_resize_image(
                                raw_image_path,
                                output_path,
                                quality=quality,
                                image_format=image_format,
                            )

                            img_data = {
                                "page": page_num + 1,
                                "index": img_index,
                                "filename": output_filename,
                                "path": str(output_path),
                                **metadata,
                            }

                            # Add base64 if requested
                            if return_base64:
                                img_data["base64"] = image_to_base64(output_path, quality)

                            images_info.append(img_data)

                    except Exception as e:
                        # Skip images that can't be extracted
                        print(f"Warning: Could not extract image {img_index} from page {page_num + 1}: {e}")
                        continue

            doc.close()
            return images_info

        finally:
            # Clean up temporary raw images
            import shutil
            if temp_dir.exists():
                shutil.rmtree(temp_dir, ignore_errors=True)

    def get_metadata(self) -> dict:
        """
        Extract PDF metadata.

        Returns:
            Dictionary with metadata
        """
        doc = pymupdf.open(str(self.pdf_path))

        metadata = {
            "filename": self.pdf_path.name,
            "file_size": os.path.getsize(self.pdf_path),
            "page_count": len(doc),
            "title": doc.metadata.get("title", ""),
            "author": doc.metadata.get("author", ""),
            "subject": doc.metadata.get("subject", ""),
            "creator": doc.metadata.get("creator", ""),
            "producer": doc.metadata.get("producer", ""),
            "creation_date": doc.metadata.get("creationDate", ""),
            "modification_date": doc.metadata.get("modDate", ""),
        }

        doc.close()
        return metadata

    def parse_full(
        self,
        output_dir: str | Path | None = None,
        quality: QualityLevel = "medium",
        image_format: ImageFormat = "jpg",
        extract_images: bool = True,
        return_base64: bool = False,
        pages: list[int] | None = None,
        max_chars: int | None = None,
        save_text_to_file: str | Path | None = None,
    ) -> dict:
        """
        Parse entire paper: text, images, and metadata.

        Args:
            output_dir: Directory to save images
            quality: Image quality level
            image_format: Image output format
            extract_images: Whether to extract images
            return_base64: Whether to include base64 encoded images
            pages: List of page numbers (0-based) to extract. None for all pages.
            max_chars: Maximum number of characters in text response. None for no limit.
            save_text_to_file: Path to save the full text. If provided, text metadata is returned instead.

        Returns:
            Dictionary with text, images, and metadata
        """
        result = {
            "text": self.extract_text(
                pages=pages,
                max_chars=max_chars,
                save_to_file=save_text_to_file,
            ),
            "metadata": self.get_metadata(),
        }

        if extract_images:
            result["images"] = self.extract_images(
                output_dir=output_dir,
                quality=quality,
                image_format=image_format,
                return_base64=return_base64,
            )
        else:
            result["images"] = []

        return result
