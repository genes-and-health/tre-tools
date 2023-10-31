"""
This file contains the types of codelists that are supported by the tretools
"""
from enum import Enum


class CodelistType(Enum):
    SNOMED = "SNOMED"
    ICD10 = "ICD10"
    OPCS = "OPCS"
