"""
This file contains the custom errors for the codelists module.
"""

class InvalidSNOMEDCodeError(Exception):
    """Raised when a SNOMED CT code is found to be invalid."""
    pass

class InvalidICD10CodeError(Exception):
    """Raised when an ICD-10 code is found to be invalid."""
    pass

class InvalidOPCSCodesError(Exception):
    """Raised when an OPCS code is found to be invalid."""
    pass

class RepeatedCodeError(Exception):
    """Raised when a code is repeated in the codelist."""
    pass

class InvalidDataShapeError(Exception):
    """Raised when the data shape is invalid."""
    pass

class InvalidProcessingRequest(Exception):
    """Raised when the processing request is invalid."""
    pass