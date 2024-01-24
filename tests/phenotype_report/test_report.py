import pytest
import os
from datetime import datetime

from tretools.phenotype_report.report import PhenotypeReport
from tretools.phenotype_report.errors import ReportAlreadyExists, FileExists, InsufficientCounts
from tretools.codelists.codelist import Codelist
from tretools.datasets.processed_dataset import ProcessedDataset
from tretools.datasets.demographic_dataset import DemographicDataset


SNOMED_CODELIST = "tests/codelists/test_data/good_snomed_codelist.csv"
PRIMARY_CARE_DATASET = "tests/test_data/primary_care/processed_data.csv"
ICD_CODELIST = "tests/codelists/test_data/good_icd_codelist.csv"
SECONDARY_CARE_DATASET = "tests/test_data/barts_health/diagnosis.csv"
DEMOGRAPHIC_MAPPING_FILE = "tests/test_data/demographics/mapping.txt"
DEMOGRAPHIC_FILE = "tests/test_data/demographics/gender_dummy.txt"
MAPPING_CONFIG = {
    "mapping": {
        "OrageneID": "study_id",
        "PseudoNHS_2023-11-08": "nhs_number"
    },
    "demographics": {
        "S1QST_Oragene_ID": "study_id",
        "S1QST_MM-YYYY_ofBirth": "dob",
        "S1QST_Gender": "gender"
    }
}
SNOMED_TO_ICD10_MAP = "tests/test_data/MappingFiles/snomed_to_icd_map.csv"


def test_load_phenotype_report():
    report = PhenotypeReport("Disease A")
    
    assert report.counts == {}
    assert report.logs == []


def test_add_count():
    codelist = Codelist(SNOMED_CODELIST, "SNOMED")
    dataset = ProcessedDataset(PRIMARY_CARE_DATASET, "primary_care", "SNOMED")

    report = PhenotypeReport("Disease A")
    report.add_count("test_count_primary_care", codelist, dataset)

    result = report.counts["test_count_primary_care"]
    assert set(result['code']) == set([100000001, 100000002])
    assert result['patient_count'] == 2
    assert result['event_count'] == 4

    output_dicts = result["nhs_numbers"].to_dicts()
    nhs_number_dict = {item['nhs_number']: item for item in output_dicts}
    assert nhs_number_dict['73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B']['code'] == 100000001
    assert nhs_number_dict['73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B']['date'] == "2013-06-03"

    assert nhs_number_dict['84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A']['code'] == 100000001
    assert nhs_number_dict['84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A']['date'] == "2018-10-05"


def test_add_count_already_exists():
    with pytest.raises(ReportAlreadyExists) as e:
        codelist = Codelist(SNOMED_CODELIST, "SNOMED")
        dataset = ProcessedDataset(PRIMARY_CARE_DATASET, "primary_care", "SNOMED")

        report = PhenotypeReport("Disease A")
        report.add_count("test_count_primary_care", codelist, dataset)
        report.add_count("test_count_primary_care", codelist, dataset)

    assert "Report test_count_primary_care already exists in this report." in str(e.value)


def test_save_to_json_with_snomed():
    codelist = Codelist(SNOMED_CODELIST, "SNOMED")
    dataset = ProcessedDataset(PRIMARY_CARE_DATASET, "primary_care", "SNOMED")

    report = PhenotypeReport("Disease A")
    report.add_count("test_count_primary_care", codelist, dataset)
    report.save_to_json("tests/phenotype_report/test_report_temp.json")
    
    # test that the file exists
    assert os.path.exists("tests/phenotype_report/test_report_temp.json")
    
    # delete the file
    os.remove("tests/phenotype_report/test_report_temp.json")

def test_save_to_json_with_icd():
    codelist = Codelist(ICD_CODELIST, "ICD10")
    dataset = ProcessedDataset(SECONDARY_CARE_DATASET, "barts_health", "ICD10")

    report = PhenotypeReport("Disease A")
    report.add_count("test_count_secondary_care", codelist, dataset)
    report.save_to_json("tests/phenotype_report/test_report_temp.json")
    
    # test that the file exists
    assert os.path.exists("tests/phenotype_report/test_report_temp.json")
    
    # delete the file
    os.remove("tests/phenotype_report/test_report_temp.json")


def test_save_to_json_already_exists():
    codelist = Codelist(SNOMED_CODELIST, "SNOMED")
    dataset = ProcessedDataset(PRIMARY_CARE_DATASET, "primary_care", "SNOMED")

    report = PhenotypeReport("Disease A")
    report.add_count("test_count_primary_care", codelist, dataset)

    with pytest.raises(FileExists) as e:
        report.save_to_json("tests/phenotype_report/test_report.json", overwrite=False)

    assert "File already exists at tests/phenotype_report/test_report.json. Set overwrite=True to overwrite this file." in str(e.value)    


def test_load_from_json():
    report = PhenotypeReport.load_from_json("tests/phenotype_report/test_report.json")

    assert isinstance(report, PhenotypeReport)
    assert report.name == "Disease A"

    assert isinstance(report.counts['test_count_primary_care'], dict)
    assert set(report.counts['test_count_primary_care']['code']) == set([100000001, 100000002])
    assert report.counts['test_count_primary_care']['patient_count'] == 2
    assert report.counts['test_count_primary_care']['event_count'] == 4


def test_report_overlaps():
    # snomed code and primary care
    snomed_codelist = Codelist(SNOMED_CODELIST, "SNOMED")
    primary_care = ProcessedDataset(PRIMARY_CARE_DATASET, "primary_care", "SNOMED")
    
    # icd 10 and secondary care
    icd_codelist = Codelist(ICD_CODELIST, "ICD10")
    secondary_care = ProcessedDataset(SECONDARY_CARE_DATASET, "barts_health", "ICD10")
    
    report = PhenotypeReport("Disease A")
    report.add_count("test_count_primary_care", snomed_codelist, primary_care)
    report.add_count("test_secondary_care", icd_codelist, secondary_care)

    report.report_overlaps()

    # we can manually check the overlaps in the datasets. Remember we are finding only 
    # the patients with Disease A. In the primary care dataset, there are 2 patients with
    # Disease A. In the secondary care dataset, there is 2 patient with Disease A. One of 
    # these patients is the same patient as in the primary care dataset. Therefore, there
    # is only 1 patient with Disease A in the secondary care dataset that is not in the
    # primary care dataset. Therefore, the overlap is 1.
    assert len(report.overlaps['test_count_primary_care_only']) == 1
    assert len(report.overlaps['test_secondary_care_only']) == 1
    assert len(report.overlaps['test_count_primary_care_and_test_secondary_care']) == 1

    assert report.overlaps['test_count_primary_care_and_test_secondary_care'] == ["84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"]


def test_report_overlaps_insufficient_counts():
    # snomed code and primary care
    snomed_codelist = Codelist(SNOMED_CODELIST, "SNOMED")
    primary_care = ProcessedDataset(PRIMARY_CARE_DATASET, "primary_care", "SNOMED")
    
    report = PhenotypeReport("Disease A")
    report.add_count("test_count_primary_care", snomed_codelist, primary_care)

    # run with only one count
    with pytest.raises(InsufficientCounts) as e:
        report.report_overlaps()

    assert "Only 1 count has been run so comparison between datasets is not possible" in str(e.value)


def test_report_with_demographics():
    # snomed code and primary care
    snomed_codelist = Codelist(SNOMED_CODELIST, "SNOMED")
    primary_care = ProcessedDataset(PRIMARY_CARE_DATASET, "primary_care", "SNOMED")

    # load the demographic data
    demographic_data = DemographicDataset(path_to_mapping_file=DEMOGRAPHIC_MAPPING_FILE, path_to_demographic_file=DEMOGRAPHIC_FILE)
    demographic_data.process_dataset(MAPPING_CONFIG)
    
    report = PhenotypeReport("Disease A")
    report.add_count("test_count_primary_care", snomed_codelist, primary_care, demographics=demographic_data)

    observed_report = report.counts["test_count_primary_care"]
    assert set(observed_report['code']) == set([100000001, 100000002])
    assert observed_report['patient_count'] == 2
    assert observed_report['event_count'] == 4

    patients = observed_report["nhs_numbers"].to_dicts()
    assert len(patients) == 2

    # first patient with nhs number 84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A
    # was born in Oct-1983 and had an event on 2018-10-05. We have not changed the rounding from the
    # standard so we will round day of birth to 15. For age, we are rounding down to the nearest year.
    # Therefore, the age at event should be 34, as the patient was born on 15th Oct 1982 and had an
    # event on 5th Oct 2018.
    assert patients[0]['nhs_number'] == "84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"
    assert patients[0]['code'] == 100000001
    assert patients[0]['date'] == datetime(2018, 10, 5).date()
    assert patients[0]['age_at_event'] == 34
    assert patients[0]['gender'] == "F"

    # second patient with nhs number 73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B
    # was born in Jan-1979 and had an event on 2013-06-03. For age, we are rounding down to the nearest
    # year. Therefore, the age at event should be 34, as the patient was born in Jan 1979 and had an
    # event on 3rd June 2013.
    assert patients[1]['nhs_number'] == "73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B"
    assert patients[1]['code'] == 100000001
    assert patients[1]['date'] == datetime(2013, 6, 3).date()
    assert patients[1]['age_at_event'] == 34
    assert patients[1]['gender'] == "M"

    # Now we are changing the rounding to the 1st of the month, therefore the patient with nhs number
    # 84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A should have an age of 35 as the
    # patient was born on 1st Oct 1982 and had an event on 5th Oct 2018.
    demographic_data = DemographicDataset(path_to_mapping_file=DEMOGRAPHIC_MAPPING_FILE, path_to_demographic_file=DEMOGRAPHIC_FILE)
    demographic_data.process_dataset(MAPPING_CONFIG, round_to_day_in_month=1)

    report = PhenotypeReport("Disease A")
    report.add_count("test_count_primary_care", snomed_codelist, primary_care, demographics=demographic_data)
    observed_report = report.counts["test_count_primary_care"]

    patients = observed_report["nhs_numbers"].to_dicts()
    assert patients[0]['nhs_number'] == "84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"
    assert patients[0]['code'] == 100000001
    assert patients[0]['date'] == datetime(2018, 10, 5).date()
    assert patients[0]['age_at_event'] == 35
    assert patients[0]['gender'] == "F"
