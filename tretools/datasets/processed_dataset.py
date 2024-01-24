from __future__ import annotations
# We use the __future__ import to allow us to use the ProcessedDataset class in the type hint
# of the merge_with_dataset method. This means thatit can be used as a type hint even though the 
# class isn't fully defined yet.

from datetime import datetime
from typing import Dict, List, Optional
import polars as pl

from tretools.datasets.base import Dataset
from tretools.datasets.dataset_enums.dataset_types import DatasetType
from tretools.codelists.codelist_types import CodelistType
from tretools.datasets.errors import DeduplicationError, CodeNotMappable


class ProcessedDataset(Dataset):
    def __init__(self, path, dataset_type: DatasetType, coding_system: CodelistType, log_path: Optional[str] = None) -> None:
        super().__init__(path, dataset_type, coding_system)

        # load the log if a log path is provided
        if log_path:
            self._load_log_from_file(log_path)

    def _load_log_from_file(self, log_path: str) -> None:
        """
        Loads a log from a file.

        Args:
            log_path (str): The path to the log file.
        """
        with open(log_path, "r") as f:
            self.log = f.read().splitlines()

    def merge_with_dataset(self, dataset: ProcessedDataset) -> None:
        """
        Merges the current dataset with another dataset.

        Args:
            dataset (ProcessedDataset): The dataset to merge with.
        """
        # Check the coding system and dataset type are the same
        if self.coding_system != dataset.coding_system:
            raise DeduplicationError("Coding system must be the same for both datasets")
        
        if self.dataset_type != dataset.dataset_type:
            raise DeduplicationError("Dataset type must be the same for both datasets")
        
        # check if the datasets have the same column names
        if self.data.columns != dataset.data.columns:
            raise DeduplicationError("Column names must be the same for both datasets")

        # merge
        self.data = self.data.vstack(dataset.data)
        self.log.append(f"{datetime.now()}: Merged dataset with {dataset.path}")

    def deduplicate(self, date_start: Optional[str] = None) -> ProcessedDataset:
        """
        Deduplicates the DataFrame. Removes rows where entire row is the same and 
        for duplicate nhs_number and code, keeps the first event after date_start.

        Args:
            date_start (str, optional): A starting date to filter from. Defaults to None.

        Returns:
            ProcessedDataset: A new dataset containing deduplicated data.
        """
        # Remove rows where the entire row is duplicated
        deduplicated_data = self.data.unique()

        # If date_start is provided, filter rows after date_start, else use the entire data
        filtered_data = deduplicated_data.filter(deduplicated_data["date"] >= date_start) if date_start else deduplicated_data

        # Now, drop duplicates based on nhs_number, code and date.
        unique_data = filtered_data.unique(subset=["nhs_number", "code", "date"])
        unique_sorted_data = unique_data.sort(pl.col("nhs_number"), pl.col("code"), pl.col("date"))

        # Create a new ProcessedDataset instance and return
        processed_dataset = ProcessedDataset(path=self.path, dataset_type=self.dataset_type, coding_system=self.coding_system)
        processed_dataset.data = unique_sorted_data

        return processed_dataset
    
    def map_snomed_to_icd(self, mapping_file: str, snomed_col: str = "conceptID", icd_col: str = "mapTarget") -> ProcessedDataset:
        """
        Maps snomed codes to icd codes using a mapping file.

        Args:
            mapping_file (str): The path to the mapping file.

        Returns:
            ProcessedDataset: A new dataset containing the mapped data.
        """
        # Check the coding system is snomed
        if self.coding_system != CodelistType.SNOMED.value:
            raise CodeNotMappable("Coding system must be SNOMED for mapping to ICD10")

        # Add to the log
        new_log = []
        new_log.append(f"{datetime.now()}: Loading mapping file from {mapping_file}")
        new_log.append(f"{datetime.now()}: Pre-mapping dataset has {self.data.shape[0]} rows")

        # Load the mapping file
        mapping_df = pl.read_csv(mapping_file)

        # Join the mapping file to the dataset
        mapped_data = self.data.join(mapping_df, left_on="code", right_on=snomed_col, how="inner")
        new_log.append(f"{datetime.now()}: Post-mapping dataset has {mapped_data.shape[0]} rows")
        mapped_data = mapped_data.select([pl.col("nhs_number"), pl.col("date"), pl.col(icd_col).alias("code")])
        new_log.append(f"{datetime.now()}: Renamed column {snomed_col} to code, and dropped other columns")

        # Create a new ProcessedDataset instance and return
        processed_dataset = ProcessedDataset(path=self.path, dataset_type=self.dataset_type, coding_system=self.coding_system)
        processed_dataset.data = mapped_data

        # Add the new log to the processed dataset together with the old log
        for log in new_log:
            processed_dataset.log.append(log)

        for log in self.log:
            processed_dataset.log.append(log)
        processed_dataset.log.sort()

        return processed_dataset

    def truncate_icd_to_3_digits(self) -> ProcessedDataset:
        """
        Truncates the icd codes to 3 digits.

        Returns:
            ProcessedDataset: A new dataset containing the truncated data.
        """
        # Check the coding system is icd
        if self.coding_system != CodelistType.ICD10.value:
            raise CodeNotMappable("Coding system must be ICD10 for truncating to 3 digits")

        # Add to the log
        new_log = []
        new_log.append(f"{datetime.now()}: Truncating ICD codes to 3 digits")
        new_log.append(f"{datetime.now()}: Pre-truncation dataset has {self.data.shape[0]} rows")

        # Truncate the icd codes
        truncated_data = self.data.select([pl.col("nhs_number"), pl.col("date"), pl.col("code").str.slice(0, 3).alias("code")])
        new_log.append(f"{datetime.now()}: Post-truncation dataset has {truncated_data.shape[0]} rows")

        # Create a new ProcessedDataset instance and return
        processed_dataset = ProcessedDataset(path=self.path, dataset_type=self.dataset_type, coding_system=self.coding_system)
        processed_dataset.data = truncated_data

        # Add the new log to the processed dataset together with the old log
        for log in new_log:
            processed_dataset.log.append(log)

        for log in self.log:
            processed_dataset.log.append(log)
        processed_dataset.log.sort()

        return processed_dataset