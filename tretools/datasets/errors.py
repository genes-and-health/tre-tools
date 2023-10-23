class DatasetPathNotCorrect(Exception):
    """Path to Dataset not valid"""
    pass

class WriteOptionsInvalid(Exception):
    """Write options are not valid"""
    pass

class UnsupportedFileType(Exception):
    """File type is not supported"""
    pass

class ColumnsValidationError(Exception):
    """Error in columns validation"""
    pass

class DeduplicationError(Exception):
    """Error in deduplication"""
    pass