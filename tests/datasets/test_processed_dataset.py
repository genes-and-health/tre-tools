import pytest
import datetime
import polars as pl

from tretools.datasets.processed_dataset import ProcessedDataset
from tretools.datasets.demographic_dataset import DemographicDataset
from tretools.codelists.codelist_types import CodelistType
from tretools.datasets.errors import DeduplicationError, CodeNotMappable

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


def test_mapped_to_icd():
    observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system=CodelistType.SNOMED.value)
    mapped_dataset = observed_dataset.map_snomed_to_icd(mapping_file="tests/test_data/mapping_files/snomed_icd_map.csv")

    # there are 7 rows in the original dataset, of these there are 3 instances of 100000001, 1 instance of 100000002 
    # and 3 instances of 200000001. Our mapping file only has maps for 100000001 and 100000002. So, we should have
    # ended up with 4 rows in the mapped dataset.
    assert mapped_dataset.data.shape == (4, 3)
    
    first_patient = mapped_dataset.data.filter(mapped_dataset.data["nhs_number"].eq("84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"))
    first_patient = first_patient.sort(pl.col("date"))
    assert first_patient['code'][0] == "A010"
    assert first_patient['code'][1] == "A010"
    assert first_patient['code'][2] == "A020"


def test_mapped_to_icd_with_specific_col():
    with pytest.raises(CodeNotMappable) as e:
        observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system=CodelistType.ICD10.value)
        observed_dataset.map_snomed_to_icd(mapping_file="tests/test_data/mapping_files/snomed_icd_map.csv", snomed_col="conceptID", icd_col="mapTarget")

    assert "Coding system must be SNOMED for mapping to ICD10" in str(e.value)

def test_mapped_to_icd_logs():
    observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system=CodelistType.SNOMED.value, log_path="tests/test_data/primary_care/processed_data_log.txt")
    mapped_dataset = observed_dataset.map_snomed_to_icd(mapping_file="tests/test_data/mapping_files/snomed_icd_map.csv")

    # there are 7 logs in the original dataset, 1 from loading and 4 created by the mapping function
    assert len(mapped_dataset.log) == 11
    assert "Loading mapping file from tests/test_data/mapping_files/snomed_icd_map.csv" in mapped_dataset.log[7]
    assert "Pre-mapping dataset has 7 rows" in mapped_dataset.log[8]
    assert "Post-mapping dataset has 4 rows" in mapped_dataset.log[9]



def test_truncate_icd_to_3_digits():
    observed_dataset = ProcessedDataset(path="tests/test_data/barts_health/diagnosis.csv", dataset_type="secondary_care", coding_system=CodelistType.ICD10.value)
    truncated_dataset = observed_dataset.truncate_icd_to_3_digits()

    # there are 10 rows in the original dataset. there should be 10 rows in the truncated dataset
    assert truncated_dataset.data.shape == (10, 3)

    # first patient. There are 2 codes with A01 (A01 and A01X). The truncated dataset should only have A01
    first_patient = truncated_dataset.data.filter(truncated_dataset.data["nhs_number"].eq("84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"))
    first_patient = first_patient.sort(pl.col("date"), pl.col("code"))

    assert first_patient['code'][0] == "A01"
    assert first_patient['code'][1] == "A01"


def test_truncate_icd_to_3_digits_logs():
    observed_dataset = ProcessedDataset(path="tests/test_data/barts_health/diagnosis.csv", dataset_type="secondary_care", coding_system=CodelistType.ICD10.value, log_path="tests/test_data/barts_health/diagnosis_log.txt")
    truncated_dataset = observed_dataset.truncate_icd_to_3_digits()

    # there are 7 logs in the original dataset, 1 from loading and 3 created by the truncation function
    assert len(truncated_dataset.log) == 11
    assert "Post-truncation dataset has 10 rows" in truncated_dataset.log[9]


def test_truncate_icd_to_3_digits_wrong_coding_system():
    with pytest.raises(CodeNotMappable) as e:
        observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/processed_data.csv", dataset_type="primary_care", coding_system=CodelistType.SNOMED.value)
        observed_dataset.truncate_icd_to_3_digits()

    assert "Coding system must be ICD10 for truncating to 3 digits" in str(e.value)

def test_removes_unrealistic_data():
    observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/procedures_with_unrealistic_values.csv", dataset_type="primary_care", coding_system="SNOMED")
    cleaned_dataset = observed_dataset.remove_unrealistic_dates(before_born=False)

    # assert no data is dropped
    assert cleaned_dataset.data.shape == (1, 3)

    # assert that the date is 1910-01-01
    assert cleaned_dataset.data["date"][0] == "1910-01-01"


def test_removes_unrealistic_data_before_born():
    observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/procedures_with_unrealistic_values.csv", dataset_type="primary_care", coding_system="SNOMED")
    demographic_dataset = DemographicDataset(path="tests/test_data/demographics/processed.csv")

    cleaned_dataset = observed_dataset.remove_unrealistic_dates(before_born=True, demographic_dataset=demographic_dataset)
    assert cleaned_dataset.data.shape == (0, 3)



def test_removes_unrealistic_data_before_born_but_no_data():
    observed_dataset = ProcessedDataset(path="tests/test_data/primary_care/procedures_with_unrealistic_values.csv", dataset_type="primary_care", coding_system="SNOMED")

    with pytest.raises(ValueError) as e:
        observed_dataset.remove_unrealistic_dates(before_born=True)

    assert "A demographic dataset must be provided if before_born is True" in str(e.value)