class ReportAlreadyExists(Exception):
    """Report already exists."""
    pass

class FileExists(Exception):
    """File already exists."""
    pass

class InsufficientCounts(Exception):
    """
    Attempts to report overlaps when only one count
    """
    pass

class FileNotFoundError(Exception):
    """
    Raised when a file is not found.
    """
    pass