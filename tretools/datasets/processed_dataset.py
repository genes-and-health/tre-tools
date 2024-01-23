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
# from tretools.datasets.dataset_enums.deduplication_options import DeduplicationOptions
from tretools.datasets.errors import DeduplicationError


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

    
