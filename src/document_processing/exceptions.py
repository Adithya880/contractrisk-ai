"""
Document Processing Custom Exceptions

Defines exception types for handling file access, format validation,
document corruption, and extraction failures in ContractRisk AI.
"""


class DocumentProcessingError(Exception):
    """Base exception for all document processing errors."""
    pass


class UnsupportedFileTypeError(DocumentProcessingError):
    """Raised when an unsupported file extension or MIME type is encountered."""
    def __init__(self, file_path: str, supported_types: list[str] | None = None):
        self.file_path = file_path
        self.supported_types = supported_types or [".pdf", ".docx"]
        message = (
            f"Unsupported file type for '{file_path}'. "
            f"Supported extensions: {', '.join(self.supported_types)}"
        )
        super().__init__(message)


class CorruptedDocumentError(DocumentProcessingError):
    """Raised when a document file cannot be opened or parsed due to corruption."""
    def __init__(self, file_path: str, cause: str | None = None):
        self.file_path = file_path
        self.cause = cause
        message = f"Failed to parse document '{file_path}' (file may be corrupted)."
        if cause:
            message += f" Cause: {cause}"
        super().__init__(message)


class EmptyDocumentError(DocumentProcessingError):
    """Raised when an extracted document contains no text content."""
    def __init__(self, file_path: str):
        self.file_path = file_path
        message = f"Document '{file_path}' is empty or contains no extractable text."
        super().__init__(message)
