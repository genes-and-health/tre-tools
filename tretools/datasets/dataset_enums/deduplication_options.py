from enum import Enum

class DeduplicationOptions(Enum):
    """
    Enum for the deduplication options.
    """
    NHS_NUMBER = "nhs_number"
    CODE = "code"
    DATE = "date"