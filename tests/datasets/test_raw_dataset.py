import pytest
import datetime

from tretools.datasets.raw_dataset import RawDataset
from tretools.datasets.errors import ColumnsValidationError, DeduplicationError



def test_good_rawdataset():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/procedures.csv", dataset_type="primary_care", coding_system="SNOMED")
    assert observed_dataset.dataset_type == "primary_care"
    assert observed_dataset.coding_system == "SNOMED"

    # assert column names are correct
    assert observed_dataset.data.columns == ["pseudo_nhs_number", "id", "clinical_effective_date", "original_code", "original_term"]

    # assert column validation is False
    assert observed_dataset.column_validation == False
    
    # Check first row of data is correct
    first_row = observed_dataset.data.slice(0, 1)
    assert first_row["pseudo_nhs_number"][0] == "84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"
    assert first_row["clinical_effective_date"][0] == "2018-10-05"
    assert first_row["original_code"][0] == 100000001
    assert first_row["original_term"][0] == "Disease A - 1"


def test_check_col_validation_on_load():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")
    assert observed_dataset.column_validation == True


def test_check_col_validation_second_time():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system="SNOMED")

    with pytest.raises(ColumnsValidationError) as e:
        observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})

    assert "Column names have already been validated" in str(e.value)


def test__standarise_column_names():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/good_procedures_no_extra_cols.csv", dataset_type="primary_care", coding_system="SNOMED")
    assert observed_dataset.column_validation == False

    # Standarise the column names
    observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})
    assert observed_dataset.column_validation == True

    # Check the column names are correct
    assert observed_dataset.data.columns == ["nhs_number", "date", "code", "term"]


def test__standarised_column_names_with_missing_columns():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/procedures_missing_cols.csv", dataset_type="primary_care", coding_system="SNOMED")

    with pytest.raises(ColumnsValidationError) as e:
        observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})

    assert "Column 'original_term' not found in data. Expected columns: original_code, original_term, clinical_effective_date, pseudo_nhs_number" in str(e.value)


def test__standarise_column_names_but_extra_columns():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/procedures.csv", dataset_type="primary_care", coding_system="SNOMED")
    assert observed_dataset.column_validation == False

    # Standarise the column names
    observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})
    assert observed_dataset.column_validation == False

    # Check the column names are correct
    assert observed_dataset.data.columns == ["nhs_number", "id", "date", "code", "term"]

    # Assert that the log contains the correct message
    assert "Key columns are standardised, however extra columns found: id" in observed_dataset.log[2]


def test__standarise_date_format_with_correct_data():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/good_procedures_no_extra_cols.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})

    # Standarise the date format
    observed_dataset._standarise_date_format()

    # Check the date format is correct
    first_row = observed_dataset.data.slice(0, 1)
    expected_date = datetime.datetime.strptime("2018-10-05", "%Y-%m-%d").date()
    assert first_row["date"][0] == expected_date


def test__standarised_date_format_with_mixed_data():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/procedures_with_mixed_dates.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})

    # Standarise the date format
    observed_dataset._standarise_date_format()

    # Get the expected dates into the correct format i.e. Datetime objects
    expected_dates_in_datetime = []
    expected_dates_as_string = [
        "2018-10-05",
        "2018-11-05",
        "2019-02-12",
        "2020-05-22",
        "2012-11-21",
        "2013-06-03",
        "2016-07-19",
        "2016-08-20",
        "2015-10-08",
    ]
    for date in expected_dates_as_string:
        expected_dates_in_datetime.append(datetime.datetime.strptime(date, "%Y-%m-%d").date())

    # Check the date format is correct
    date_column = observed_dataset.data["date"].to_list()
    assert date_column == expected_dates_in_datetime


def test__standarised_date_format_before_col_validation():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/good_procedures_no_extra_cols.csv", dataset_type="primary_care", coding_system="SNOMED")

    with pytest.raises(ColumnsValidationError) as e:
        observed_dataset._standarise_date_format()

    assert "Column names have not been validated. Please run _standarise_column_names() first" in str(e.value)


def test__drop_unneeded_columns():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/procedures.csv", dataset_type="primary_care", coding_system="SNOMED")

    observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})
    expected_columns = ["nhs_number", "id", "date", "code", "term"]
    assert set(observed_dataset.data.columns) == set(expected_columns)

    observed_dataset._drop_unneeded_columns()
    expected_columns.remove("id")
    assert set(observed_dataset.data.columns) == set(expected_columns)


def test__drop_all_null_rows():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/good_procedures_with_nulls.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})
    
    # check shape of data
    assert observed_dataset.data.shape == (9, 4)

    # drop all null rows
    observed_dataset._drop_all_null_rows()

    # check shape of data
    assert observed_dataset.data.shape == (6, 4)


def test__deduplicate():
    # the csv file has 27 rows which is basically the regular csv multiplied by 3 so 
    # there are 3 repeated rows for each row in the regular csv
    observed_dataset = RawDataset(path="tests/test_data/primary_care/good_procedures_with_multiples.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})

    # check shape of data
    assert observed_dataset.data.shape == (27, 4)

    # deduplicate
    dedup_dataset = observed_dataset._deduplicate(deduplication_options=["nhs_number", "code", "date"])

    # check shape of data
    assert dedup_dataset.data.shape == (9, 4)


def test__deduplicate_with_wrong_options():
    observed_dataset = RawDataset(path="tests/test_data/primary_care/good_procedures_with_multiples.csv", dataset_type="primary_care", coding_system="SNOMED")
    observed_dataset._standarise_column_names({"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})

    with pytest.raises(DeduplicationError) as e:
        observed_dataset._deduplicate(deduplication_options=["code"])

    assert "deduplication_options must include 'nhs_number' and 'code'" in str(e.value)


def test_process_dataset():
    # the csv file has 27 rows which is basically the regular csv multiplied by 3 so
    # there are 3 repeated rows for each row in the regular csv. In addition to this
    # there is an extra column called extra_col which should be dropped, and there are
    # 6 rows that have null values in them which should also be dropped. The final
    # dataset should have 7 rows and 4 columns.
    ingested_data = RawDataset(path="tests/test_data/primary_care/procedures_many_diffs.csv", dataset_type="primary_care", coding_system="SNOMED")
    assert ingested_data.data.shape == (27, 5)

    processed_dataset = ingested_data.process_dataset(deduplication_options=["nhs_number", "code", "date"], column_maps={"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})
    assert processed_dataset.data.shape == (7, 4)

    # Check the column names are correct
    assert set(processed_dataset.data.columns) == set(["nhs_number", "date", "code", "term"])


def test_processed_log():
    ingested_data = RawDataset(path="tests/test_data/primary_care/procedures_many_diffs.csv", dataset_type="primary_care", coding_system="SNOMED")
    assert "Loaded data from tests/test_data/primary_care/procedures_many_diffs.csv" in ingested_data.log[0]

    # run the process_dataset method
    ingested_data.process_dataset(deduplication_options=["nhs_number", "code", "date"], column_maps={"original_code": "code", "original_term": "term", "clinical_effective_date": "date", "pseudo_nhs_number": "nhs_number"})
    assert "Column names not validated" in ingested_data.log[1]
    assert "Key columns are standardised, however extra columns found: extra_col. Run _drop_unneeded_columns() to drop these columns" in ingested_data.log[2]
    assert "Unneeded 1 column(s) dropped" in ingested_data.log[3]
    assert "Dropped 6 rows with empty values or empty date strings" in ingested_data.log[4]
    assert "Date format standarised" in ingested_data.log[5]


