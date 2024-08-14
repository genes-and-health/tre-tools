"""
This file is responsible for the BrowserReportTransformer class. This class is used to transform the reports into
a format that can be used in the Phenotype Browser.
"""

from __future__ import annotations
import polars as pl
from datetime import datetime
from typing import List, Dict
import json
import csv


from tretools.phenotype_report.report import PhenotypeReport
from tretools.report_transformers.base import ReportTransformer
from tretools.counter.counter import categorise_age


class BrowserReportTransformer(ReportTransformer):
    def __init__(self) -> None:
        """
        Initialises the BrowserReportTransformer.
        """
        super().__init__()
        self.data = None
        self.log = []
        self.summary = []

    @classmethod
    def load_from_objects(cls, objects: List[PhenotypeReport]) -> BrowserReportTransformer:
        """
        Loads a list of PhenotypeReports into a BrowserReportTransformer. Each PhenotypeReport
        will be in a list under the attribute reports.

        Args:
            objects (List[PhenotypeReport]): A list of PhenotypeReports.

        Returns:
            BrowserReportTransformer: A BrowserReportTransformer with the PhenotypeReports loaded into it.
        """
        transformer = BrowserReportTransformer()
        transformer.reports = objects
        transformer.log.append(f"{datetime.now()}: Loaded {len(objects)} Phenotype Reports into the BrowserReportTransformer.")
        return transformer

    def _write_readme(self, path: str) -> None:
        # TODO: Implement this method
        pass

    def transform(self, metadata_path = str, path: str = "browser_reports") -> None:
        """
        This method transforms the reports into a format that can be used in the Phenotype Browser.
        It must receive the information with the metadata and the path where the reports will be saved.

        Args:
            metadata_path: The path to the metadata file.
            path: The path where the reports will be saved.

        Returns:
            None - The reports will be saved in the path specified.
        """
        # Read the metadata file in as a dictionary, with teh first column as the keys
        with open(metadata_path, "r") as meta_file:
            csv_reader = csv.DictReader(meta_file)
            metadata = {}
            for row in csv_reader:
                metadata[row['report_name']] = row

        # Loop through the reports and create a json object for each one. It uses the metadata
        # to add the extra information to the json object.
        for report in self.reports:
            self._transform_report_to_json(report, metadata[report.name], path)

    def _transform_report_to_json(self, report: PhenotypeReport,  phenotype_data: dict, path: str) -> None:
        """
        This method transforms a PhenotypeReport into a json object that can be used in the Phenotype Browser.
        It saves the json object in the path specified, and it uses the phenotype_data to add extra information.
        This phenotype data comes from the metadata file.

        Args:
            report: The PhenotypeReport to be transformed.
            phenotype_data: The metadata for the report.
            path: The path where the report will be saved.

        Returns:
            None - The report will be saved in the path specified.
        """
        # Add the "types of coding systems" to the phenotype_data. First we
        # need to get the unique codelist types from the report.
        codelist_types = []
        for named_count, count_details in report.counts.items():
            codelist_types.append(count_details['codelist_type'])
        codelist_types = list(set(codelist_types)) # remove duplicates

        # Now we can add the codelist types to the phenotype_data
        phenotype_data["coding_systems"] = {}
        possible_coding_systems = ["ICD10", "SNOMED", "OPCS"]
        for codelist_type in codelist_types:
            if codelist_type in possible_coding_systems:
                phenotype_data["coding_systems"][codelist_type] = True
            else:
                phenotype_data["coding_systems"][codelist_type] = False

        # Add this codelist types to the phenotype_data
        phenotype_data["coding_systems"] = codelist_types

        # Now we open up the codelist file and add the codes to the phenotype_data
        phenotype_data["codes_by_system"] = {}
        for named_count, count_details in report.counts.items():
            phenotype_data["codes_by_system"][named_count] = {}
            codelist_path = count_details["codelist_path"]
            codelist = pl.read_csv(codelist_path).to_dicts()
            phenotype_data["codes_by_system"][named_count]['terms'] = []
            for code in codelist:
                new_code = {
                    "code": code['code'],
                    "term": code['term']
                }
                phenotype_data["codes_by_system"][named_count]['terms'].append(new_code)

        # Add the data source to the phenotype_data, This is the number of NHS numbers
        # that are unique to each dataset and those appearing in one or more datasets.
        if report.overlaps:
            phenotype_data["data_source"] = {}
            for named_count, list_of_nhs in report.overlaps.items():
                if named_count[:-5] in report.counts:
                    named_count = report.counts[named_count[:-5]]["dataset_type"]
                    phenotype_data["data_source"][named_count] = len(list_of_nhs)
                elif named_count == "all_datasets":
                    phenotype_data["data_source"]["all"] = len(list_of_nhs)

        # add counts based on year of event
        year_of_event = {}
        age_of_event = {
            "<18": 0,
            "18-24": 0,
            "25-34": 0,
            "35-44": 0,
            "45-54": 0,
            "55-64": 0,
            "65-74": 0,
            "75-84": 0,
            "85+": 0
        }

        gender_of_event = {
            "F": 0,
            "M": 0
        }

        # empty dataframe to store the nhs_numbers, year_of_event, age_of_event and gender
        schema = [
            ("nhs_number", pl.Utf8),
            ("gender", pl.Utf8),
            ("year_of_event", pl.Int32),
            ("age_group", pl.Utf8)
        ]
        final_df = pl.DataFrame({name: pl.Series([], dtype=dtype) for name, dtype in schema})


        for named_count, count_details in report.counts.items():

            # Add extra columns to the dataframe for year of event for date
            temp_df = count_details['nhs_numbers'].with_columns([
                pl.col("date").dt.year().alias("year_of_event")
            ])

            # add extra column of age category
            temp_df = temp_df.with_columns([pl.col("age_at_event").apply(categorise_age).alias("age_group")])

            # drop code, date and age_at_event
            temp_df = temp_df.drop(["code", "date", "age_at_event"])
            final_df = pl.concat([final_df, temp_df])

        # Nowe get rid of duplicates, and take the earliest year of event for
        # each nhs_number so we sort by year of event
        final_df = (final_df.sort(["nhs_number", "year_of_event"]).group_by("nhs_number").first())

        # Now we can count the number of events for each year, age and gender
        # Count occurrences per year
        year_counts = final_df.group_by("year_of_event").agg(pl.count("year_of_event").alias("count")).to_dict(as_series=False)
        year_of_event = {year: count for year, count in zip(year_counts["year_of_event"], year_counts["count"])}

        # Update age_of_event counts
        age_counts = final_df.group_by("age_group").agg(pl.count("age_group").alias("count")).to_dict(as_series=False)
        for age_group, count in zip(age_counts["age_group"], age_counts["count"]):
            if age_group in age_of_event:
                age_of_event[age_group] = count

        # Update gender_of_event final_dfcounts
        gender_counts = final_df.group_by("gender").agg(pl.count("gender").alias("count")).to_dict(as_series=False)
        for gender, count in zip(gender_counts["gender"], gender_counts["count"]):
            if gender in gender_of_event:
                gender_of_event[gender] = count

        phenotype_data["year_of_event"] = year_of_event
        phenotype_data["age_of_event"] = age_of_event
        phenotype_data["gender"] = gender_of_event

        # write the phenotype_data to a json file
        with open(f"{path}/{report.name}.json", "w") as f:
            json.dump(phenotype_data, f)
