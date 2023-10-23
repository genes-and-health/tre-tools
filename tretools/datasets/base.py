"""
File containing the Dataset class.
"""
import os
import polars as pl

from datetime import datetime
from typing import List, Dict

from tretools.codelists.codelist_types import CodelistType
from tretools.datasets.dataset_enums.dataset_types import DatasetType
from tretools.datasets.dataset_enums.deduplication_options import DeduplicationOptions
from tretools.datasets.errors import DatasetPathNotCorrect, WriteOptionsInvalid, UnsupportedFileType, ColumnsValidationError, DeduplicationError


class Dataset():
    def __init__(self, path, dataset_type: DatasetType, coding_system: CodelistType) -> None:
        self.dataset_type = dataset_type
        self.coding_system = coding_system
        self.log = []
        self.path = path
        self.data = self._load_data(path)

    @staticmethod
    def _check_path(path: str) -> bool:
        """
        Checks the path is valid and the file exists.

        Args:
            path (str): The path to the file.

        Returns:
            bool: True if the path is valid, False otherwise.
        """
        return os.path.exists(path)

    def _load_data(self, path: str) -> pl.DataFrame:
        """
        Load the data using polars from a csv file.

        Args:
            path (str): The path to the csv file.

        Returns:
            polars.DataFrame: The data.
        """
        if not self._check_path(path):
            raise DatasetPathNotCorrect(f"Invalid path for Dataset: {path}")
        
        # if csv file, load using polars
        if path.endswith(".csv"):
            return pl.read_csv(path)
        # if feather file, load using polars
        elif path.endswith(".arrow"):
            return pl.read_ipc(path)
        else:
            raise UnsupportedFileType("File type not supported. Must be either .csv or .arrow")

    def _validate_column_names(self) -> bool:
        """
        Validates if the column names of the DataFrame match the specified list

        Returns:
            bool: True if the column names match the expected ones, False otherwise.
        """
        # expected column names
        expected_col_names = ["code", "term", "date", "nhs_number"]

        # get column names of pl.DataFrame
        col_names = self.data.columns
        
        # Check if the column names match the expected ones
        if set(col_names) == set(expected_col_names):
            return True
        else:
            return False


    def write_to_log(self, path: str, overwrite_or_append: str = "overwrite") -> None:
        """
        Write self.log to a log file.

        Args:
            path (str): The path to the log file.
            overwrite_or_append (str, optional): Whether to overwrite the log file or append to it. Defaults to "overwrite".
        """
        if overwrite_or_append == "overwrite":
            with open(path, "w") as f:
                for line in self.log:
                    f.write(line + "\n")
        elif overwrite_or_append == "append":
            with open(path, "a") as f:
                for line in self.log:
                    f.write(line + "\n")
        else:
            raise WriteOptionsInvalid("Invalid option for overwrite_or_append. Must be either 'overwrite' or 'append'")


    def write_to_csv(self, path: str) -> None:
        """
        Write data to a csv file.

        Args:
            path (str): The path to the csv file.
        """
        self.data.write_csv(path)
        self.log.append(f"{datetime.now()}: Data written to {path}")

    def write_to_feather(self, path: str) -> None:
        """
        Write data to a feather file. 

        Args:
            path (str): The path to the feather file.
        """
        self.data.write_ipc(path)
        self.log.append(f"{datetime.now()}: Data written to {path}")

