from enum import Enum


class DatasetType(Enum):
    """
    Enum for the dataset type.
    """
    PRIMARY_CARE = "primary_care"
    BARTS_HEALTH = "barts_health"
    NHS_DIGITAL = "nhs_digital"
    BRADFORD = "bradford"
    MERGED = "merged"
