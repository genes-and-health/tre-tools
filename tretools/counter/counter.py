

from datetime import datetime

from tretools.codelists.codelist_types import CodelistType
from tretools.counter.errors import MismatchBetweenDatasetAndCodelist
from tretools.codelists.codelist import Codelist


class EventCounter:
    """
    This class counts the number of events in a dataset when given a codelist.
    """
    def __init__(self, dataset):
        self.dataset = dataset
        self.counts = {}
        self.log = [f"{datetime.now()}: There are {self.dataset.data.shape[0]} events in the dataset"]

    def count_events(self, name_of_count: str, codelist: Codelist) -> None:
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
        codes = codelist.codes

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
        person_count = first_events.shape[0]
        log.append(f"{datetime.now()}: There are {person_count} people in the dataset for the codelist")

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
