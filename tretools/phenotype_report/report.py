from __future__ import annotations

import json
import os
import datetime as dt
from datetime import datetime
from itertools import combinations
from typing import Optional


from tretools.counter.counter import EventCounter
from tretools.datasets.base import Dataset
from tretools.datasets.demographic_dataset import DemographicDataset
from tretools.codelists.codelist import Codelist
from tretools.phenotype_report.errors import ReportAlreadyExists, FileExists, InsufficientCounts



class PhenotypeReport():
    """
    A class to represent a phenotype report.
    """
    def __init__(self, name) -> None:
        self.name = name
        self.counts = {}
        self.overlaps = {}
        self.logs = []

    def add_count(self, name_of_count: str, codelist: Codelist, dataset: Dataset, demographics: Optional[DemographicDataset] = None) -> None:
        """
        Count the events in the dataset for the codelist and add to the report.

        Args:
            name_of_count (str): The name of the count.
            codelist (Codelist): The codelist to count.
            dataset (Dataset): The dataset to count.
            demographics (DemographicDataset, optional): The demographic data to add to the report. Defaults to None.

        Raises:
            ReportAlreadyExists: If the report already exists.
        """
        # Check this codelist has not already been counted
        if name_of_count in self.counts.keys():
            raise ReportAlreadyExists(f"Report {name_of_count} already exists in this report.")

        counter = EventCounter(dataset)
        counter.count_events(name_of_count=name_of_count, codelist=codelist, demographics=demographics)

        self.counts[name_of_count] = counter.counts[name_of_count]

        self.logs.append(f"Codelist {name_of_count} added to report {self.name} at {datetime.now()}. Log below from this count to follow.")
        self.logs.append(counter.counts[name_of_count]["log"])

    def save_to_json(self, path: str, overwrite: bool = True) -> None:
        """
        Saves the report to a json file including the counts and the logs.
        
        Args:
            path (str): The path to save the json file to.
            overwrite (bool, optional): Whether to overwrite the file if it already exists. Defaults to True.

        Raises:
            FileExists: If the file already exists and overwrite is False.
        """
        # check if the file already exists
        if os.path.exists(path) and not overwrite:
            raise FileExists(f"File already exists at {path}. Set overwrite=True to overwrite this file.")

        output = {}
        output["name"] = self.name
        output["counts"] = self.counts

        # Convert the nhs_numbers column to a list of dictionaries. This is because the nhs_numbers column is a polars 
        # DataFrame and cannot be saved to json.
        for named_count, count_detail in output["counts"].items():
            output["counts"][named_count]["nhs_numbers"] = count_detail["nhs_numbers"].to_dicts()
            for person in output["counts"][named_count]["nhs_numbers"]:
                # check if the date is a datetime object and convert to string if it is
                if isinstance(person["date"], dt.date):
                    person["date"] = person["date"].strftime("%Y-%m-%d")

        output["logs"] = self.logs

        # if overlap
        if self.overlaps:
            output["overlaps"] = self.overlaps

        # save the report to a json file. 
        with open(path, "w") as f:
            output['logs'].append(f"{datetime.now()}: Report saved to {path}")
            json.dump(output, f, indent=4)

    @classmethod
    def load_from_json(cls, path: str) -> PhenotypeReport:
        """
        Load the report from a json file.

        Args:
            path (str): The path to the json file.

        Returns:
            PhenotypeReport: The report.
        """
        with open(path, "r") as f:
            data = json.load(f)

        report = PhenotypeReport(data["name"])
        report.counts = data["counts"]
        report.logs = data["logs"]
        report.logs.append(f"{datetime.now()}: Loaded report from {path}.")
        return report

    def report_overlaps(self) -> None:
        """
        Reports on patients unique to each dataset and those appearing in one or more datasets.
        """
        # Check at least 2 counts and raise error if not
        if len(self.counts) <= 1:
            raise InsufficientCounts("Only 1 count has been run so comparison between datasets is not possible")

        # Dictionary to hold NHS numbers for each dataset
        nhs_data = {}
        for name, count_detail in self.counts.items():
            nhs_data[name] = set(count_detail["nhs_numbers"]["nhs_number"].to_list())

        overlaps = {}
        
        # For each dataset, find numbers unique to it
        for name, nhs_numbers in nhs_data.items():
            others = set().union(*[nhs_data[other] for other in nhs_data if other != name])
            overlaps[f"{name}_only"] = list(nhs_numbers - others)

        # For combinations of datasets (2, 3, ...), find overlapping NHS numbers
        for i in range(2, len(self.counts) + 1):
            for combo in combinations(nhs_data.keys(), i):
                combo_key = '_and_'.join(combo)
                intersected = set.intersection(*[nhs_data[name] for name in combo])
                overlaps[combo_key] = list(intersected)

        # For the intersection of all datasets
        overlaps["all_datasets"] = list(set.intersection(*nhs_data.values()))

        # Store the overlaps in the report's overlaps attribute
        self.overlaps = overlaps
        self.logs.append(f"{datetime.now()}: Identified overlaps and unique NHS numbers for datasets.")



