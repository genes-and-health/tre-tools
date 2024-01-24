"""
File containing the Dataset class.
"""
import os
import polars as pl

from datetime import datetime
from typing import List


from tretools.codelists.codelist_types import CodelistType
from tretools.datasets.dataset_enums.dataset_types import DatasetType
from tretools.datasets.errors import DatasetPathNotCorrect, WriteOptionsInvalid, UnsupportedFileType


class Dataset():
    def __init__(self, path, dataset_type: DatasetType, coding_system: CodelistType) -> None:
        self.dataset_type = dataset_type
        self.coding_system = coding_system
        self.path = path
        self.log = []
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
        if not self._check_path(path):
            raise DatasetPathNotCorrect(f"Invalid path for Dataset: {path}")
        
        null_values = ["", " ", "NULL", "NA", "               ", ".", "                    ", "-", "NOT CLOSE"]
        try:
            # Attempt to read the data normally
            data = self._read_file(path, null_values)
        except pl.exceptions.ComputeError:
            # If a ComputeError occurs, read the data with all columns as strings
            data = self._read_file(path, null_values, infer_schema_length=0)
            # Convert columns with scientific notation to int
            data = self._convert_scientific_notation_columns(data)

        return data
    
    def _convert_scientific_notation_columns(self, df: pl.DataFrame) -> pl.DataFrame:
        # Function to convert columns with scientific notation
        for col in df.columns:
            if df[col].dtype == pl.Utf8:
                try:
                    # Try converting to int, if fails, keep as is
                    df = df.with_columns(df[col].cast(pl.Float64).cast(pl.Int64).alias(col))
                except pl.exceptions.ComputeError:
                    continue
        return df

    def _read_file(self, path: str, null_values: List, infer_schema_length = None ) -> pl.DataFrame:
        """
        Load the data using polars from a csv file.

        Args:
            path (str): The path to the csv file.

        Returns:
            polars.DataFrame: The data.
        """
        # if feather file, load using polars
        if path.endswith(".arrow"):
            data = pl.read_ipc(path)
            self.log.append(f"{datetime.now()}: Loaded data from {path}")
            return data
        # if tab file, load using polars
        elif path.endswith(".tab"):
            separator = "\t"
            data = pl.read_csv(path, separator=separator, null_values=null_values, infer_schema_length=infer_schema_length)
            self.log.append(f"{datetime.now()}: Loaded data from {path} using separator '{separator}' with these values as null: {null_values}")
            return data
        # if txt file, separator is "|" or ","
        # if txt file, determine separator by inspecting the first line
        elif path.endswith(".txt") or path.endswith(".tsv") or path.endswith(".csv"):
            with open(path, 'r') as file:
                first_line = file.readline()
                if '|' in first_line:
                    separator = '|'
                elif ',' in first_line:
                    separator = ','
                elif '\t' in first_line:
                    separator = '\t'
                else:
                    raise Exception("Unable to determine the file separator.")
            data = pl.read_csv(path, separator=separator, null_values=null_values, infer_schema_length=infer_schema_length)
            self.log.append(f"{datetime.now()}: Loaded data from {path} using separator '{separator}' with these values as null: {null_values}")
            return data
        else:
            raise UnsupportedFileType("File type not supported. File type not supported. Must be either .csv, .txt or .arrow")

    def _validate_column_names(self) -> bool:
        """
        Validates if the column names of the DataFrame match the specified list

        Returns:
            bool: True if the column names match the expected ones, False otherwise.
        """
        # expected column names
        expected_col_names = ["code", "date", "nhs_number"]

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


