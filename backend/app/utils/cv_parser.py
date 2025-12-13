"""
CV text extraction utilities for PDF, DOCX, and TXT files
"""
from typing import Optional
import io
from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file_content: bytes) -> str:
    """
    Extract text from PDF file

    Args:
        file_content: PDF file content as bytes

    Returns:
        Extracted text from all pages

    Raises:
        Exception: If PDF reading fails
    """
    try:
        pdf_file = io.BytesIO(file_content)
        reader = PdfReader(pdf_file)

        text_parts = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                text_parts.append(text)

        return "\n\n".join(text_parts)
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {str(e)}")


def extract_text_from_docx(file_content: bytes) -> str:
    """
    Extract text from DOCX file

    Args:
        file_content: DOCX file content as bytes

    Returns:
        Extracted text from all paragraphs

    Raises:
        Exception: If DOCX reading fails
    """
    try:
        docx_file = io.BytesIO(file_content)
        doc = Document(docx_file)

        text_parts = []
        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                text_parts.append(paragraph.text)

        return "\n\n".join(text_parts)
    except Exception as e:
        raise Exception(f"Failed to extract text from DOCX: {str(e)}")


def extract_text_from_txt(file_content: bytes) -> str:
    """
    Extract text from TXT file

    Args:
        file_content: TXT file content as bytes

    Returns:
        Decoded text content

    Raises:
        Exception: If text decoding fails
    """
    try:
        # Try UTF-8 first, fall back to latin-1
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            return file_content.decode('latin-1')
    except Exception as e:
        raise Exception(f"Failed to extract text from TXT: {str(e)}")


def extract_cv_text(filename: str, file_content: bytes) -> str:
    """
    Extract text from CV file based on file extension

    Args:
        filename: Original filename
        file_content: File content as bytes

    Returns:
        Extracted text content

    Raises:
        ValueError: If file format is not supported
        Exception: If text extraction fails
    """
    filename_lower = filename.lower()

    if filename_lower.endswith('.pdf'):
        return extract_text_from_pdf(file_content)
    elif filename_lower.endswith('.docx'):
        return extract_text_from_docx(file_content)
    elif filename_lower.endswith('.txt'):
        return extract_text_from_txt(file_content)
    else:
        raise ValueError(
            f"Unsupported file format. Please upload PDF, DOCX, or TXT file. Got: {filename}"
        )


def validate_cv_file(filename: str, file_size: int, max_size_mb: int = 5) -> None:
    """
    Validate CV file before processing

    Args:
        filename: Original filename
        file_size: File size in bytes
        max_size_mb: Maximum allowed file size in MB

    Raises:
        ValueError: If validation fails
    """
    # Check file extension
    allowed_extensions = ['.pdf', '.docx', '.txt']
    filename_lower = filename.lower()

    if not any(filename_lower.endswith(ext) for ext in allowed_extensions):
        raise ValueError(
            f"Invalid file format. Allowed formats: {', '.join(allowed_extensions)}"
        )

    # Check file size
    max_size_bytes = max_size_mb * 1024 * 1024
    if file_size > max_size_bytes:
        raise ValueError(
            f"File too large. Maximum size: {max_size_mb}MB, got: {file_size / (1024 * 1024):.2f}MB"
        )

    # Check filename is not empty
    if not filename.strip():
        raise ValueError("Filename cannot be empty")
