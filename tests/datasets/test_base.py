import pytest
import os
import csv

from tretools.datasets.base import Dataset
from tretools.datasets.errors import DatasetPathNotCorrect, DatasetPathNotCorrect, WriteOptionsInvalid, UnsupportedFileType


def test_good_dataset():
    observed_dataset = Dataset(path="tests/test_data/primary_care/procedures.csv", dataset_type="primary_care", coding_system="SNOMED")
    assert observed_dataset.dataset_type == "primary_care"
    assert observed_dataset.coding_system == "SNOMED"

    # assert column names are correct
    assert observed_dataset.data.columns == ["pseudo_nhs_number", "id", "clinical_effective_date", "original_code", "original_term"]
    
    # Check first row of data is correct
    first_row = observed_dataset.data.slice(0, 1)
    assert first_row["pseudo_nhs_number"][0] == "84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"
    assert first_row["clinical_effective_date"][0] == "2018-10-05"
    assert first_row["original_code"][0] == 100000001
    assert first_row["original_term"][0] == "Disease A - 1"


def test_bad_path_dataset():
    with pytest.raises(DatasetPathNotCorrect) as e:
        observed_dataset = Dataset(path="bad/path/to/dataset.csv", dataset_type="primary_care", coding_system="SNOMED")

    assert "Invalid path for Dataset: bad/path/to/dataset.csv" in str(e.value)


def test_processed_log():
    ingested_data = Dataset(path="tests/test_data/primary_care/procedures_many_diffs.csv", dataset_type="primary_care", coding_system="SNOMED")
    ingested_data.log.append("test log")

    assert ingested_data.log == ["test log"]
    assert len(ingested_data.log) == 1


def test_log_gets_written():
    ingested_data = Dataset(path="tests/test_data/primary_care/procedures_many_diffs.csv", dataset_type="primary_care", coding_system="SNOMED")
    ingested_data.log.append("first test log")
    ingested_data.log.append("second test log")
    
    # write the log
    ingested_data.write_to_log("tests/test_data/primary_care/test_log.txt", overwrite_or_append="overwrite")

    # read in the log and check it is correct
    with open("tests/test_data/primary_care/test_log.txt", "r") as f:
        log = f.read()

    # check first line and how many lines in the log - should be 7 (6 logs and empty line)
    assert "first test log" in log
    assert len(log.split("\n")) == 3

    # write the log again but this time append
    ingested_data.write_to_log("tests/test_data/primary_care/test_log.txt", overwrite_or_append="append")

    # check how many lines in the log - should be 5 (2 logs * 2 and one empty line)
    with open("tests/test_data/primary_care/test_log.txt", "r") as f:
        log = f.read()
    
    assert len(log.split("\n")) == 5

    # delete the log file
    os.remove("tests/test_data/primary_care/test_log.txt")


def test_log_with_wrong_args():
    with pytest.raises(WriteOptionsInvalid) as e:
        ingested_data = Dataset(path="tests/test_data/primary_care/procedures_many_diffs.csv", dataset_type="primary_care", coding_system="SNOMED")
        ingested_data.log.append("first test log")
        ingested_data.write_to_log("tests/test_data/primary_care/log.txt", overwrite_or_append="wrong")

    assert "Invalid option for overwrite_or_append. Must be either 'overwrite' or 'append'" in str(e.value)


def test_raises_error_if_not_csv_or_feather():
    with pytest.raises(UnsupportedFileType) as e:
        ingested_data = Dataset(path="tests/test_data/primary_care/fake_data.txt", dataset_type="primary_care", coding_system="SNOMED")

    assert "File type not supported. Must be either .csv or .arrow" in str(e.value)


def test_writes_csv():
    ingested_data = Dataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")

    # write the processed data to csv
    ingested_data.write_to_csv("tests/test_data/primary_care/test_data.csv")

    # read in the csv and check it is correct using csv reader. I am using csv reader
    # to avoid a dependency on ProcessedDataset which is what we are testing. 
    with open("tests/test_data/primary_care/test_data.csv", "r") as f:
        reader = csv.reader(f)
        rows = list(reader)

    assert len(rows) == 8
    assert rows[0] == ["nhs_number", "code", "term", "date"]
    
    os.remove("tests/test_data/primary_care/test_data.csv")

def test_write_to_feather():
    ingested_data = Dataset(path="tests/test_data/primary_care/processed_data.arrow", dataset_type="primary_care", coding_system="SNOMED")

    # write to feather
    ingested_data.write_to_feather("tests/test_data/primary_care/test_data.arrow")

    # assert a file has been created
    assert os.path.isfile("tests/test_data/primary_care/test_data.arrow")

    # assert file not empty
    assert os.stat("tests/test_data/primary_care/test_data.arrow").st_size != 0

    # delete the file
    os.remove("tests/test_data/primary_care/test_data.arrow")


def test_read_from_csv():
    # read the csv back in
    loaded_data = Dataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    assert loaded_data.data.shape == (7, 4)

def test_read_from_feather():
    # read the feather file back in
    loaded_data = Dataset(path="tests/test_data/primary_care/processed_data.arrow", dataset_type="primary_care", coding_system="SNOMED")
    assert loaded_data.data.shape == (7, 4)

def test_read_from_tab():
    # read from a tab file
    loaded_data = Dataset(path="tests/test_data/barts_health/diagnosis.tab", dataset_type="secondary_care", coding_system="ICD10")
    assert loaded_data.data.shape == (10, 6)
