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
from tretools.codelists.errors import InvalidSNOMEDCodeError

import csv
import tempfile
import polars as pl
import os



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


        # Sort the data by nhs_number, code, and date. This ensures that when we drop duplicates based on nhs_number and code, we'll keep the first event.
        sorted_data = filtered_data.sort(["nhs_number", "code", "date"])

        # Now, drop duplicates based on nhs_number and code, keeping the first event after the date_start or just the first event if no date_start.
        final_data = sorted_data.unique(subset=["nhs_number", "code", "date"])

        # Create a new ProcessedDataset instance and return
        processed_dataset = ProcessedDataset(path=self.path, dataset_type=self.dataset_type, coding_system=self.coding_system)
        processed_dataset.data = final_data

        return processed_dataset
    
    def snomed_to_icd10(self, SNOMED_ICD10_map, dataset) -> ProcessedDataset:
        '''
        It maps SNOMED data to ICD10s using a mapping file.
        Args:
            SNOMED_ICD10_map: The mapping file
            dataset (ProcessedDataset): The dataset for mapping
        '''
        processed_dataset = ProcessedDataset(path=self.path, dataset_type=self.dataset_type, coding_system=self.coding_system)

        return processed_dataset
    def map_snomed_to_icd10(self, processeddataset: ProcessedDataset, mapping_file: str, icd10_3_digit_only: bool = False) -> ProcessedDataset:
        """
        Maps SNOMED codes to their corresponding ICD10

        Args:
            mapping_file (str): mapping file path
        """
        # Raise error if the original code type is not SNOMED
        if processeddataset.coding_system != 'SNOMED':
            raise InvalidSNOMEDCodeError("The original code type must be SNOMED")

        # Check path to mapping file exists
        if not os.path.exists(mapping_file):
            raise FileNotFoundError(f"requested mapping file is NOT found in {mapping_file}")

            
        # Decide whether to truncate ICD10 codes to 3 digits
        if icd10_3_digit_only:
            col_map = "ICD10_3digit"
        else:
            col_map = "mapTarget"
        # Load the mapping file into a dictionary
        with open(mapping_file, "r") as f:
            reader = csv.DictReader(f)
            mapping = {row["conceptId"]: row[col_map] for row in reader}

        # Iterate through the data and map the SNOMED codes to ICD10 codes
        mapped_data = {}

        mapping = {int(key): value for key, value in mapping.items()}
        
        # Making a new column for ICD10 in the dataframe
        df = processeddataset.data.with_columns(pl.col("code").map_dict(mapping).alias("ICD10"))
        
        # Making a list of dictionaries
        mapped_data = [
            {'code': entry['ICD10'], 'term': f'Mapped from SNOMED Code: {entry["code"]}, Term: {entry["term"]}'}
            for entry in df.to_dicts()
        ]

        # Converting all to one dictionary (the last two steps can be merged, if needed)
        mapped_data = {entry['code']: entry['term'] for entry in mapped_data}

       # without having to write to a temporary file first
        temp_file = tempfile.NamedTemporaryFile(suffix=".csv",mode="w", delete=False)
        writer = csv.DictWriter(temp_file, fieldnames=["code", "term"])
        writer.writeheader()
        for code, term in mapped_data.items():
            writer.writerow({"code": code, "term": term})
        temp_file.close()
        # # make a new codelist object with the new data
        new_codelist = ProcessedDataset(temp_file.name, "ICD10",coding_system ="SNOMED")
        # new_codelist = Codelist(temp_file.name, "ICD10")
        return new_codelist


    
