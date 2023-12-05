import pytest
import datetime

from tretools.datasets.processed_dataset import ProcessedDataset
from tretools.datasets.errors import DeduplicationError

def test_load_processed_dataset():
    observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    valid_column_names = observed_dataset._validate_column_names()
    assert valid_column_names == True

    # assert data shape
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
    assert dedup.data.shape == (5, 3)

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
