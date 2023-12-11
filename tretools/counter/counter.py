

from datetime import datetime
from typing import Optional
import polars as pl

from tretools.codelists.codelist_types import CodelistType
from tretools.counter.errors import MismatchBetweenDatasetAndCodelist
from tretools.codelists.codelist import Codelist

from tretools.datasets.demographic_dataset import DemographicDataset


def categorise_age(age):
    if age < 18:
        raise ValueError("Age is less than 18")
    if age < 25:
        return "18-24"
    elif age < 35:
        return "25-34"
    elif age < 45:
        return "35-44"
    elif age < 55:
        return "45-54"
    elif age < 65:
        return "55-64"
    elif age < 75:
        return "65-74"
    elif age < 85:
        return "75-84"
    else:
        return "85+"



class EventCounter:
    """
    This class counts the number of events in a dataset when given a codelist.
    """
    def __init__(self, dataset):
        self.dataset = dataset
        self.counts = {}
        self.log = [f"{datetime.now()}: There are {self.dataset.data.shape[0]} events in the dataset"]

    def count_events(self, name_of_count: str, codelist: Codelist, demographics: Optional[DemographicDataset] = None) -> None:
        """
        Counts the number of events in the dataset for each code in the codelist.

        Args:
            name_of_count (str): The name of the count.
            codelist (Codelist): The codelist to count events for.
        """
        # Log the number of events in the dataset
        log = self.log
        log.append(f"{datetime.now()}: Counting events for codelist {name_of_count}")

        # Check if the codelist and dataset have the same coding system
        if self.dataset.coding_system != codelist.codelist_type:
            raise MismatchBetweenDatasetAndCodelist(f"Coding system of dataset ({self.dataset.coding_system}) does not match coding system of codelist ({codelist.codelist_type})")

        # Get the codes from the codelist
        codes = list(codelist.codes)

        # if snomed, make sure the codes are integers
        if codelist.codelist_type == CodelistType.SNOMED.value:
            codes = [int(code) for code in codelist.codes if code.isdigit()]

        # Filter the dataset to only include rows where the code is in the codelist
        filtered_data = self.dataset.data.filter(self.dataset.data["code"].is_in(codes))

        # event count
        event_count = filtered_data.shape[0]
        log.append(f"{datetime.now()}: There are {event_count} events in the dataset for the codelist")

        # Sort the data by nhs_number and date, then group by nhs_number to get the first event
        first_events = (filtered_data.sort(["nhs_number", "date"])
                        .groupby("nhs_number").first())

        # person count
        person_count = first_events.shape[0]
        log.append(f"{datetime.now()}: There are {person_count} people in the dataset for the codelist")

        if demographics is not None:
            first_events = self._calculate_demographics(first_events=first_events, demographics=demographics)

        # Construct the counts DataFrame
        counts = {
            "code": codes,
            "patient_count": person_count,
            "event_count": event_count,
            "nhs_numbers": first_events,
            "codelist_type": codelist.codelist_type,
            "dataset_type": self.dataset.dataset_type,
            "log": log
        }

        # Add the counts to the counts dictionary
        self.counts[name_of_count] = counts

    def _calculate_demographics(self, first_events, demographics: DemographicDataset):
        # Merge the first events data with demographic together
        first_events = first_events.join(demographics.data, on="nhs_number", how="inner")

        # Convert 'date' and 'dob' columns to datetime if they are not already
        first_events = first_events.with_columns([
            pl.col("date").str.strptime(pl.Date, "%Y-%m-%d", strict=False).alias("date"),
        ])

        gender_map = {1: "M", 2: "F"}

        # Calculate the age at event
        first_events = first_events.with_columns(
            ((pl.col("date") - pl.col("dob")).dt.days() / 365.25).cast(int).alias("age_at_event")
        )

        # Apply categorization and mapping
        first_events = first_events.with_columns([
            first_events["age_at_event"].apply(categorise_age).alias("age_range"),
            first_events["gender"].apply(lambda x: gender_map[x]).alias("gender_label")
        ])

        # select the columns we want (nhs_number, code, date, age at event, gender_label)
        first_events = first_events.select(["nhs_number", "code", "date", "age_at_event", "gender_label"])
        # Rename gender_label as gender
        first_events = first_events.rename({"gender_label": "gender"})

        self.log.append(f"{datetime.now()}: Demographic data added to the report")
        return first_events


# count of how many events per year and then drop the year column
#         first_events = first_events.with_columns([
#             first_events["date"].str.slice(0, 4).alias("year_of_event"),
#         ])
#         year_of_event = first_events.groupby("year_of_event").agg(pl.count())
#         first_events = first_events.drop("year_of_event")



        # # Group by age range and gender, then count
        # result = first_events.groupby(["age_range", "gender_label"]).agg(pl.count())
        #
        # # Drop the dempgraphic columns from the nhs_numbers DataFrame as we are only interested in the counts
        # # and wherever possible want to make it less easy to identify individuals
        # first_events = first_events.select(["nhs_number", "code", "date"])
        #
        # # Convert the result to the desired dictionary format
        # result_dict = {age_range: {} for age_range in result["age_range"].unique()}
        # for row in result.rows():
        #     age_range, gender, count = row
        #     result_dict[age_range][gender] = count