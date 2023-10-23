from __future__ import annotations
# We use the __future__ import to allow us to use the ProcessedDataset class in the type hint
# of the merge_with_dataset method. This means thatit can be used as a type hint even though the 
# class isn't fully defined yet.

from datetime import datetime
from typing import Dict, List, Optional


from tretools.datasets.base import Dataset
from tretools.datasets.dataset_enums.dataset_types import DatasetType
from tretools.codelists.codelist_types import CodelistType
# from tretools.datasets.dataset_enums.deduplication_options import DeduplicationOptions
from tretools.datasets.errors import DeduplicationError


class ProcessedDataset(Dataset):
    def __init__(self, path, dataset_type: DatasetType, coding_system: CodelistType) -> None:
        super().__init__(path, dataset_type, coding_system)

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


        # Sort the data by nhs_number, code, and date. This ensures that when we drop duplicates based on nhs_number and code, we'll keep the first event.
        sorted_data = filtered_data.sort(["nhs_number", "code", "date"])

        # Now, drop duplicates based on nhs_number and code, keeping the first event after the date_start or just the first event if no date_start.
        final_data = sorted_data.unique(subset=["nhs_number", "code"])

        # Create a new ProcessedDataset instance and return
        processed_dataset = ProcessedDataset(path=self.path, dataset_type=self.dataset_type, coding_system=self.coding_system)
        processed_dataset.data = final_data

        return processed_dataset

    
