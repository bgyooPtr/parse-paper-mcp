"""Tests for PDF parser."""

import pytest
from pathlib import Path
from parse_paper_mcp.parser import PaperParser


def test_paper_parser_init_with_nonexistent_file():
    """Test that parser raises error for non-existent file."""
    with pytest.raises(FileNotFoundError):
        PaperParser("nonexistent.pdf")


def test_paper_parser_init_with_existing_file(tmp_path):
    """Test parser initialization with a file."""
    # Create a dummy file
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_text("dummy")

    # This will fail because it's not a real PDF, but init should work
    parser = PaperParser(pdf_file)
    assert parser.pdf_path == pdf_file


# Note: Full integration tests would require actual PDF files
# For now, we have basic unit tests
