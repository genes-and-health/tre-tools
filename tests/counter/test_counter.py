import pytest

from tretools.counter.counter import EventCounter
from tretools.counter.errors import MismatchBetweenDatasetAndCodelist
from tretools.codelists.codelist import Codelist
from tretools.datasets.processed_dataset import ProcessedDataset



def test_count_events():
    # load codelist
    codelist = Codelist("tests/codelists/test_data/good_snomed_codelist.csv", "SNOMED")

    # load data
    dataset = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")

    counter = EventCounter(dataset)
    counter.count_events("test_count", codelist)

    nhs_numbers_df = counter.counts["test_count"]["nhs_numbers"]
    nhs_numbers_col = nhs_numbers_df["nhs_number"].to_list()

    expected_values = ['73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B', '84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A']
    assert set(nhs_numbers_col) == set(expected_values)

    # check the counts are correct. Comparing this to the data that was manually counted. 
    output_dicts = counter.counts["test_count"]["nhs_numbers"].to_dicts()
    nhs_number_dict = {item['nhs_number']: item for item in output_dicts}
    assert nhs_number_dict['73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B']['code'] == 100000001
    assert nhs_number_dict['73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B']['date'] == "2013-06-03"

    assert nhs_number_dict['84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A']['code'] == 100000001
    assert nhs_number_dict['84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A']['date'] == "2018-10-05"

    assert counter.counts["test_count"]["patient_count"] == 2
    assert counter.counts["test_count"]["event_count"] == 4
    assert counter.counts["test_count"]["codelist_type"] == "SNOMED"
    assert counter.counts["test_count"]["dataset_type"] == "primary_care"

    assert "There are 7 events in the dataset" in counter.counts["test_count"]["log"][0]
    assert "Counting events for codelist test_count" in counter.counts["test_count"]["log"][1]
    assert "There are 4 events in the dataset for the codelist" in counter.counts["test_count"]["log"][2]
    assert "There are 2 people in the dataset for the codelist" in counter.counts["test_count"]["log"][3]


def test_count_events_mismatched_coding_system():
    with pytest.raises(MismatchBetweenDatasetAndCodelist) as e:
        # load codelist with icd10 codes
        codelist = Codelist("tests/codelists/test_data/good_icd_codelist.csv", "ICD10")

        # load data
        dataset = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")

        counter = EventCounter(dataset)
        counter.count_events("test_count", codelist)

    assert "Coding system of dataset (SNOMED) does not match coding system of codelist (ICD10)" in str(e.value)


