import pytest
import datetime

from tretools.datasets.processed_dataset import ProcessedDataset
from tretools.datasets.errors import DeduplicationError
import os

def test_load_processed_dataset():
    observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    valid_column_names = observed_dataset._validate_column_names()
    assert valid_column_names == True

    # assert data shape
    assert observed_dataset.data.shape == (7, 3)


def test_merge_with_dataset():
    observed_dataset_one = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset_two = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")

    observed_dataset_one.merge_with_dataset(observed_dataset_two)

    # assert data shape
    assert observed_dataset_one.data.shape == (14, 3)


def test_merge_with_dataset_different_coding_system():
    observed_dataset_one = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset_two = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="ICD10")

    with pytest.raises(DeduplicationError) as e:
        observed_dataset_one.merge_with_dataset(observed_dataset_two)

    assert "Coding system must be the same for both datasets" in str(e.value)


def test_merge_with_dataset_different_dataset_type():
    observed_dataset_one = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset_two = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="secondary_care", coding_system="SNOMED")

    with pytest.raises(DeduplicationError) as e:
        observed_dataset_one.merge_with_dataset(observed_dataset_two)

    assert "Dataset type must be the same for both datasets" in str(e.value)


def test_merge_with_dataset_different_column_names():
    observed_dataset_one = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset_two = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    # change the column name of the second dataset to check that it fails
    observed_dataset_two.data = observed_dataset_two.data.rename({"nhs_number": "nhs_number_two"})

    with pytest.raises(DeduplicationError) as e:
        observed_dataset_one.merge_with_dataset(observed_dataset_two)

    assert "Column names must be the same for both datasets" in str(e.value)


def test_dedupe_no_date_limit():
    observed_dataset_one = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset_two = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset_one.merge_with_dataset(observed_dataset_two)

    dedup = observed_dataset_one.deduplicate()
    assert dedup.data.shape == (7, 3)

    # find row that has nhs_number = 84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A
    # and code = 100000001. Make sure that the date is the earliest date which is 2018-10-05
    
    data = dedup.data

    specific_row = data.filter((data["nhs_number"].eq("84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A")) & (data["code"].eq("100000001")))
    assert specific_row["date"][0] == "2018-10-05"

    specific_row = data.filter((data["nhs_number"].eq("53952EF0503F7F341D9121DBCCC39DE95EA83713167E5E57EDB613A60D4C104C")) & (data["code"].eq("200000001")))
    assert specific_row["date"][0] == "2016-07-19"

    
def test_dedupe_with_date_limit():
    observed_dataset_one = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset_two = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset_one.merge_with_dataset(observed_dataset_two)

    # deduplicate with date_start = 2018-10-06. This should drop most of the data
    # except for 3 rows. 
    dedup = observed_dataset_one.deduplicate(date_start="2018-10-06")
    assert dedup.data.shape == (3, 3)

    # find row that has nhs_number = 84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A
    # and code = 100000001. Make sure that the date is the earliest date which is 2018-11-05 
    # which is the first date after the date_start
    data = dedup.data
    specific_row = data.filter((data["nhs_number"].eq("84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A")) & (data["code"].eq("100000001")))
    assert specific_row["date"][0] == "2018-11-05"
    
def test_SNOMED_to_ICD10_mapping():
    # Get the current working directory
    current_directory = os.getcwd()
    # Construct the path to the test_data folder
    test_data_path = os.path.join(current_directory, 'tests', 'codelists', 'test_data')
    # Test data
    GOOD_SNOMED_to_be_ICD10_PATH = f"{test_data_path}/good_SNOMEDS_to_be_ICD10.csv"
    # Mapping file
    mapping_file = f"{test_data_path}/snomed_to_icd_map.csv"

    data = ProcessedDataset(GOOD_SNOMED_to_be_ICD10_PATH, dataset_type="primary_care", coding_system ="SNOMED")
    mapped_data = data.map_snomed_to_icd10(data, mapping_file)

    assert mapped_data.coding_system == "SNOMED" # Original coding system is meant to be SNOMED (can be changed, if needed)
    assert len(mapped_data.data) == 4
    assert mapped_data.data[0]['code'][0] == 'A011'
    assert mapped_data.data[1]['code'][0] == 'A02.1'
    assert mapped_data.data[2]['code'][0] == 'A03X'
    assert mapped_data.data[3]['code'][0] == 'B0111'
    assert mapped_data.data[0]['term'][0] == 'Mapped from SNOMED Code: 100000001, Term: Disease A - 1'
    assert mapped_data.data[1]['term'][0] == 'Mapped from SNOMED Code: 100000002, Term: Disease A - 2'
    assert mapped_data.data[2]['term'][0] == 'Mapped from SNOMED Code: 100000003, Term: Disease A - 3'
    assert mapped_data.data[3]['term'][0] == 'Mapped from SNOMED Code: 200000001, Term: Disease B - 1'
