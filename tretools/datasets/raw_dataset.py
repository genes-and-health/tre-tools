import polars as pl

from datetime import datetime
from typing import List, Dict

from tretools.datasets.base import Dataset
from tretools.datasets.errors import ColumnsValidationError, DeduplicationError
from tretools.datasets.dataset_enums.dataset_types import DatasetType
from tretools.codelists.codelist_types import CodelistType
from tretools.datasets.dataset_enums.deduplication_options import DeduplicationOptions
from tretools.datasets.processed_dataset import ProcessedDataset


class RawDataset(Dataset):
    def __init__(self, path, dataset_type: DatasetType, coding_system: CodelistType) -> None:
        super().__init__(path, dataset_type, coding_system)
        self.data = self._load_data(path)
        self.log.append(f"{datetime.now()}: Loaded data from {path}")
        self.column_validation: bool = self._validate_column_names()

        if self.column_validation:
            self.log.append(f"{datetime.now()}: Column names validated")

    def _standarise_column_names(self, column_maps: Dict[str, str]) -> None:
        """
        Standarises the column names of the DataFrame.

        Args:
            column_maps (Dict[str, str]): A dictionary of column names to be renamed.

        Raises:
            ValueError: If the column names have already been validated.
        """
        if self.column_validation:
            raise ColumnsValidationError("Column names have already been validated")
        else:
            self.log.append(f"{datetime.now()}: Column names not validated")

        # Check if all columns in the mapping exist in the data
        for old_col in column_maps.keys():
            if old_col not in self.data.columns:
                raise ColumnsValidationError(f"Column '{old_col}' not found in data. Expected columns: {', '.join(column_maps.keys())}")

        # Rename the columns based on a dictionary of column names
        self.data = self.data.rename(column_maps)
        self.column_validation: bool = self._validate_column_names()
        if self.column_validation:
            self.log.append(f"{datetime.now()}: Column names validated")

        # If not validated, likely due to extra columns.
        elif not self.column_validation:
            # List of standardized column names
            standard_cols = list(column_maps.values())

            # All columns in the current data
            current_cols = list(self.data.columns)

            # Identify extra columns and log the message
            extra_cols = [col for col in current_cols if col not in standard_cols]
            if extra_cols:
                self.log.append(f"{datetime.now()}: Key columns are standardised, however extra columns found: {', '.join(extra_cols)}. Run _drop_unneeded_columns() to drop these columns.")

    def _standarise_date_format(self) -> None:
        """
        Standardises the date format of the 'date' column in the DataFrame.

        Raises:
            ColumnsValidationError: If the column names have not been validated.
        """
        if not self.column_validation:
            raise ColumnsValidationError("Column names have not been validated. Please run _standarise_column_names() first")

        date_col = "date"

        # Convert the date strings using strptime
        date_converted = self.data.select(
        pl.coalesce(
            pl.col(date_col).str.strptime(pl.Date, "%F", strict=False),                   # "2018-10-05"
            pl.col(date_col).str.strptime(pl.Date, "%F %T", strict=False),                # "2018-10-05 12:15:30"
            pl.col(date_col).str.strptime(pl.Date, "%d/%m/%Y", strict=False),             # "05/11/2018"
            pl.col(date_col).str.strptime(pl.Date, "%d-%m-%Y", strict=False),             # "12-02-2019"
            pl.col(date_col).str.strptime(pl.Date, "%FT%T", strict=False),                # "2020-05-22T08:45:50"
            pl.col(date_col).str.strptime(pl.Date, "%d.%m.%Y", strict=False),             # "21.11.2012"
            pl.col(date_col).str.strptime(pl.Date, "%d-%m-%Y %H:%M", strict=False),      # "03-06-2013 15:23"
            pl.col(date_col).str.strptime(pl.Date, "%d-%m-%Y %H:%M:%S", strict=False),   # "19/10/2015 17:25:00"
            pl.col(date_col).str.strptime(pl.Date, "%B %d, %Y", strict=False),           # "July 19, 2016"
            pl.col(date_col).str.strptime(pl.Date, "%Y-%m-%d %H:%M", strict=False),       # "2016-08-20 07:10"
            pl.col(date_col).str.strptime(pl.Date, "%d/%m/%Y %H:%M", strict=False)       # "01/01/2009 15:09"
            ).alias(date_col)
        )
        # Drop the original date column and concatenate the converted one
        self.data = self.data.drop(date_col).hstack(date_converted)
        self.log.append(f"{datetime.now()}: Date format standarised")

    def _drop_all_null_rows(self) -> None:
        """
        Drops all rows where any cell has a missing value or the date column is an empty string.
        """
        # Count the number of rows before dropping
        num_rows_before = self.data.shape[0]

        # Drop rows where the date column is an empty string
        condition = self.data["date"] != ''
        
        # Drop rows with any missing value
        self.data = self.data.filter(condition).drop_nulls()
        num_rows_after = self.data.shape[0]
        
        self.log.append(f"{datetime.now()}: Dropped {num_rows_before - num_rows_after} rows with empty values or empty date strings")

    def _deduplicate(self, deduplication_options: List[DeduplicationOptions]) -> ProcessedDataset:
        """
        Deduplicates the DataFrame based on nhs_number and code, with an optional inclusion of term.

        Args:
            deduplication_options (List[str]): List containing columns to deduplicate on. Must include "nhs_number" and "code", 
            can optionally include "term".

        Returns:
            ProcessedDataset: A new dataset containing deduplicated data.
        """
        
        if "nhs_number" not in deduplication_options or "code" not in deduplication_options:
            raise DeduplicationError("deduplication_options must include 'nhs_number' and 'code'")
        
        # Deduplicate based on the provided columns
        deduplicated_data = self.data.unique(subset=deduplication_options, keep="first")

        # Create a new ProcessedDataset instance and return
        processed_dataset = ProcessedDataset(path=self.path, dataset_type=self.dataset_type, coding_system=self.coding_system)
        processed_dataset.data = deduplicated_data

        return processed_dataset

    def _drop_unneeded_columns(self) -> None:
        """
        Drops unneeded columns from the DataFrame.
        """
        num_of_cols_before = self.data.shape[1]
        self.data = self.data.select(["nhs_number", "code", "term", "date"])
        num_of_cols_after = self.data.shape[1]
        self.log.append(f"{datetime.now()}: Unneeded {num_of_cols_before - num_of_cols_after} column(s) dropped")

    def process_dataset(self, deduplication_options: List[DeduplicationOptions], column_maps: Dict[str, str]) -> ProcessedDataset:
        """
        Processes a raw dataset by standarising the column names, dropping unneeded columns, standarising the date format and deduplicating.

        Args:
            deduplication_options (List[str]): List containing columns to deduplicate on. Must include "nhs_number" and "code", 
            can optionally include "term".
            column_maps (Dict[str, str]): A dictionary of column names to be renamed.

        Returns:
            ProcessedDataset: A new dataset containing processed data.
        """
        # Standarise the column names
        self._standarise_column_names(column_maps)

        # Drop unneeded columns
        self._drop_unneeded_columns()

        # Drop all rows with null values
        self._drop_all_null_rows()

        # Validate the column names
        self.column_validation: bool = self._validate_column_names()

        # Time format the date
        self._standarise_date_format()

        # Deduplicate
        processed_dataset = self._deduplicate(deduplication_options)

        # Create a new ProcessedDataset instance and return
        return processed_dataset
    






