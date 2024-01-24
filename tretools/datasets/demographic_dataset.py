"""
This module contains the DemographicDataset class.
"""
import polars as pl
import os

from typing import Dict, Optional
from datetime import datetime

from tretools.datasets.base import Dataset


class DemographicDataset(Dataset):
    def __init__(self, path: Optional[str] = None, path_to_mapping_file: Optional[str] = None, path_to_demographic_file: Optional[str] = None) -> None:
        self.log = []
        self.data = None

        if path is None:
            self.mapped_data = self._load_data(path_to_mapping_file)
            self.demographics = self._load_data(path_to_demographic_file)

        if path is not None:
            self.data = self._load_data(path)
            

    def _clean_columns(self, data: pl.DataFrame, config: Dict[str, str]) -> None:
        """
        Drop all columns that are not needed for the demographic dataset, and
        rename the columns to the standard names.
        """
        # Rename key columns
        data = data.rename(config)

        # Drop all unnecessary columns
        data = data.select(config.values())

        return data
    
    def _merge_data(self, mapping: pl.DataFrame, demographic_data: pl.DataFrame, ) -> pl.DataFrame:
        """
        Merge the data and demographics dataframes together.
        """
        # Merge the dataframes together
        mapping = mapping.join(demographic_data, on="study_id", how="inner")
        
        # drop study_id column
        mapping = mapping.drop("study_id")
        return mapping
    

    def _convert_date(self, rounded_day: int) -> None:
        """
        Convert the date of birth to a date with rounded day so 01-2000 becomes 15-01-2000
        if rounded_day is 15.

        Args:
            rounded_day (int): The day to round to.
        """
        # Convert the date of birth to a date with rounded day so 01-2000 becomes 15-01-2000
        self.data = self.data.with_columns(
            (pl.lit(f"{str(rounded_day)}-") + self.data["dob"]).alias("dob")
        )

        # Convert the date of birth to a date
        date_converted = self.data.select(
        pl.coalesce(
            pl.col("dob").str.strptime(pl.Date, "%d-%m-%Y", strict=False),             # "12-02-2019"
            ).alias("dob")
        )
        # Drop the original date column and concatenate the converted one
        self.data = self.data.drop("dob").hstack(date_converted)

        
    def process_dataset(self, column_maps: Dict[str, str] = None, round_to_day_in_month: int = 15) -> None:
        """
        Combine the datasets and produce a new dataset with basic demographic information.

        Args:
            column_maps (Dict[str, str], optional): The column mappings to use. Defaults to None.
            round_to_day_in_month (int, optional): The day to round the date of birth to. Defaults to 15.
        
        Raises:
            ValueError: If the column_maps are not provided.
        """
        # should not run if self.data has content
        if self.data is not None:
            raise ValueError("This method should not be called if demographic data is already loaded.")

        # Drop all unnecessary columns
        self.mapped_data = self._clean_columns(self.mapped_data, column_maps["mapping"])
        self.demographics = self._clean_columns(self.demographics, column_maps["demographics"])

        # Merge the dataframes together
        self.data = self._merge_data(self.mapped_data, self.demographics)

        # Convert the date of birth to a date with rounded day so 01-2000 becomes 15-01-2000
        self._convert_date(round_to_day_in_month)

        