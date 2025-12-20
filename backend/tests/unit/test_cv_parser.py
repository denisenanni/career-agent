"""
Unit tests for CV parser utilities
"""
import pytest
from unittest.mock import patch, MagicMock
import io

from app.utils.cv_parser import (
    extract_text_from_pdf,
    extract_text_from_docx,
    extract_text_from_txt,
    extract_cv_text,
    validate_cv_file,
)


class TestExtractTextFromPdf:
    """Test PDF text extraction"""

    def test_extract_text_from_valid_pdf(self):
        """Test extracting text from a valid PDF"""
        # Create a mock PdfReader
        with patch('app.utils.cv_parser.PdfReader') as mock_reader_class:
            mock_page = MagicMock()
            mock_page.extract_text.return_value = "Page 1 content"

            mock_reader = MagicMock()
            mock_reader.pages = [mock_page]
            mock_reader_class.return_value = mock_reader

            result = extract_text_from_pdf(b"fake pdf content")

            assert result == "Page 1 content"

    def test_extract_text_from_multipage_pdf(self):
        """Test extracting text from a multi-page PDF"""
        with patch('app.utils.cv_parser.PdfReader') as mock_reader_class:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Page 1"

            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = "Page 2"

            mock_reader = MagicMock()
            mock_reader.pages = [mock_page1, mock_page2]
            mock_reader_class.return_value = mock_reader

            result = extract_text_from_pdf(b"fake pdf content")

            assert result == "Page 1\n\nPage 2"

    def test_extract_text_from_pdf_with_empty_pages(self):
        """Test extracting text from PDF with some empty pages"""
        with patch('app.utils.cv_parser.PdfReader') as mock_reader_class:
            mock_page1 = MagicMock()
            mock_page1.extract_text.return_value = "Content"

            mock_page2 = MagicMock()
            mock_page2.extract_text.return_value = None

            mock_reader = MagicMock()
            mock_reader.pages = [mock_page1, mock_page2]
            mock_reader_class.return_value = mock_reader

            result = extract_text_from_pdf(b"fake pdf content")

            assert result == "Content"

    def test_extract_text_from_invalid_pdf(self):
        """Test that invalid PDF raises ValueError"""
        with patch('app.utils.cv_parser.PdfReader') as mock_reader_class:
            mock_reader_class.side_effect = Exception("Invalid PDF")

            with pytest.raises(ValueError) as exc_info:
                extract_text_from_pdf(b"invalid content")

            assert "Failed to extract text from PDF" in str(exc_info.value)


class TestExtractTextFromDocx:
    """Test DOCX text extraction"""

    def test_extract_text_from_valid_docx(self):
        """Test extracting text from a valid DOCX"""
        with patch('app.utils.cv_parser.Document') as mock_doc_class:
            mock_para1 = MagicMock()
            mock_para1.text = "Paragraph 1"

            mock_para2 = MagicMock()
            mock_para2.text = "Paragraph 2"

            mock_doc = MagicMock()
            mock_doc.paragraphs = [mock_para1, mock_para2]
            mock_doc_class.return_value = mock_doc

            result = extract_text_from_docx(b"fake docx content")

            assert result == "Paragraph 1\n\nParagraph 2"

    def test_extract_text_from_docx_with_empty_paragraphs(self):
        """Test extracting text from DOCX with empty paragraphs"""
        with patch('app.utils.cv_parser.Document') as mock_doc_class:
            mock_para1 = MagicMock()
            mock_para1.text = "Content"

            mock_para2 = MagicMock()
            mock_para2.text = "   "  # Empty/whitespace

            mock_doc = MagicMock()
            mock_doc.paragraphs = [mock_para1, mock_para2]
            mock_doc_class.return_value = mock_doc

            result = extract_text_from_docx(b"fake docx content")

            assert result == "Content"

    def test_extract_text_from_invalid_docx(self):
        """Test that invalid DOCX raises ValueError"""
        with patch('app.utils.cv_parser.Document') as mock_doc_class:
            mock_doc_class.side_effect = Exception("Invalid DOCX")

            with pytest.raises(ValueError) as exc_info:
                extract_text_from_docx(b"invalid content")

            assert "Failed to extract text from DOCX" in str(exc_info.value)


class TestExtractTextFromTxt:
    """Test TXT text extraction"""

    def test_extract_text_from_utf8_txt(self):
        """Test extracting text from UTF-8 encoded TXT"""
        content = "Hello, World! こんにちは".encode('utf-8')
        result = extract_text_from_txt(content)
        assert result == "Hello, World! こんにちは"

    def test_extract_text_from_latin1_txt(self):
        """Test extracting text from Latin-1 encoded TXT"""
        # Latin-1 specific characters that would fail UTF-8
        content = b"Hello \xe9\xe8\xea"  # é, è, ê in Latin-1
        result = extract_text_from_txt(content)
        assert "Hello" in result

    def test_extract_text_from_txt_general_error(self):
        """Test that general errors raise ValueError"""
        # Create a mock that will fail on all decode attempts
        class BadBytes:
            def decode(self, encoding):
                raise Exception("Decode error")

        with pytest.raises(ValueError) as exc_info:
            # Patch the BytesIO to return our bad bytes-like object
            extract_text_from_txt(BadBytes())

        assert "Failed to extract text from TXT" in str(exc_info.value)


class TestExtractCvText:
    """Test main CV text extraction function"""

    def test_extract_cv_text_pdf(self):
        """Test extracting text from PDF file"""
        with patch('app.utils.cv_parser.extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "PDF content"

            result = extract_cv_text("resume.pdf", b"content")

            assert result == "PDF content"
            mock_extract.assert_called_once_with(b"content")

    def test_extract_cv_text_docx(self):
        """Test extracting text from DOCX file"""
        with patch('app.utils.cv_parser.extract_text_from_docx') as mock_extract:
            mock_extract.return_value = "DOCX content"

            result = extract_cv_text("resume.docx", b"content")

            assert result == "DOCX content"
            mock_extract.assert_called_once_with(b"content")

    def test_extract_cv_text_txt(self):
        """Test extracting text from TXT file"""
        with patch('app.utils.cv_parser.extract_text_from_txt') as mock_extract:
            mock_extract.return_value = "TXT content"

            result = extract_cv_text("resume.txt", b"content")

            assert result == "TXT content"
            mock_extract.assert_called_once_with(b"content")

    def test_extract_cv_text_case_insensitive(self):
        """Test that file extension matching is case insensitive"""
        with patch('app.utils.cv_parser.extract_text_from_pdf') as mock_extract:
            mock_extract.return_value = "content"

            extract_cv_text("RESUME.PDF", b"content")
            mock_extract.assert_called_once()

    def test_extract_cv_text_unsupported_format(self):
        """Test that unsupported formats raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            extract_cv_text("resume.doc", b"content")

        assert "Unsupported file format" in str(exc_info.value)


class TestValidateCvFile:
    """Test CV file validation"""

    def test_validate_valid_pdf(self):
        """Test validating a valid PDF file"""
        # Should not raise
        validate_cv_file("resume.pdf", 1024)

    def test_validate_valid_docx(self):
        """Test validating a valid DOCX file"""
        validate_cv_file("resume.docx", 1024)

    def test_validate_valid_txt(self):
        """Test validating a valid TXT file"""
        validate_cv_file("resume.txt", 1024)

    def test_validate_invalid_extension(self):
        """Test that invalid extensions raise ValueError"""
        with pytest.raises(ValueError) as exc_info:
            validate_cv_file("resume.doc", 1024)

        assert "Invalid file format" in str(exc_info.value)

    def test_validate_file_too_large(self):
        """Test that oversized files raise ValueError"""
        # 10MB file when max is 5MB
        file_size = 10 * 1024 * 1024

        with pytest.raises(ValueError) as exc_info:
            validate_cv_file("resume.pdf", file_size, max_size_mb=5)

        assert "File too large" in str(exc_info.value)

    def test_validate_empty_filename(self):
        """Test that empty filename raises ValueError"""
        # Empty string doesn't end with any valid extension
        # so it raises "Invalid file format" first
        with pytest.raises(ValueError) as exc_info:
            validate_cv_file("", 1024)

        assert "Invalid file format" in str(exc_info.value)

    def test_validate_custom_max_size(self):
        """Test validation with custom max size"""
        # 3MB file, 2MB max
        file_size = 3 * 1024 * 1024

        with pytest.raises(ValueError):
            validate_cv_file("resume.pdf", file_size, max_size_mb=2)

        # Same file, 5MB max - should pass
        validate_cv_file("resume.pdf", file_size, max_size_mb=5)
