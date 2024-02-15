import pytest
import os

from tretools.phenotype_report.engine import PhenotypeReportEngine
from tretools.phenotype_report.engine import FileNotFoundError
from tretools.datasets.demographic_dataset import DemographicDataset

TEST_INSTRUCTION_PRIMARY_CARE = {'phenotype_name': 'Disease A', 'dataset_name': 'primary_care', 'dataset_path': 'tests/test_data/primary_care/processed_data.csv', 'dataset_type': 'primary_care', 'codelist_name': 'Disease_A_snomed', 'codelist_path': 'tests/codelists/test_data/good_snomed_codelist.csv', 'codelist_type': 'SNOMED', 'with_x_in_icd': ''}
TEST_INSTRUCTION_SECONDARY_CARE = {'phenotype_name': 'Disease A', 'dataset_name': 'barts_health', 'dataset_path': 'tests/test_data/barts_health/diagnosis.csv', 'dataset_type': 'barts_health', 'codelist_name': 'Disease_A_ICD10', 'codelist_path': 'tests/codelists/test_data/good_icd_codelist.csv', 'codelist_type': 'ICD10', 'with_x_in_icd': 'no'}

def test_create_engine():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    assert engine.index_file_path == "tests/phenotype_report/test_index.csv"

    assert engine.datasets == {}
    assert engine.codelists == {}


def test_load_instructions():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    assert engine.raw_instructions[0] == TEST_INSTRUCTION_PRIMARY_CARE
    assert engine.raw_instructions[1] == TEST_INSTRUCTION_SECONDARY_CARE


def test__check_all_dataset_reachable():
    with pytest.raises(FileNotFoundError) as e:
        engine = PhenotypeReportEngine("tests/phenotype_report/test_fake_index.csv")

    assert "Dataset file FAKE not found." in str(e.value)

def test__check_all_codelist_reachable():
    with pytest.raises(FileNotFoundError) as e:
        PhenotypeReportEngine("tests/phenotype_report/test_index_bad_codelist_path.csv")

    assert "Codelist file FAKE PATH not found." in str(e.value)



def test_orgainse_into_phenotypes():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    engine.organise_into_phenotypes()

    phenotype_instructions = engine.processed_instructions['Disease A'] 

    assert phenotype_instructions['primary_care_Disease_A_snomed'] == TEST_INSTRUCTION_PRIMARY_CARE
    assert phenotype_instructions['barts_health_Disease_A_ICD10'] == TEST_INSTRUCTION_SECONDARY_CARE


def test__generate_phenotype_report():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    engine.organise_into_phenotypes()

    phenotype_report = engine._generate_phenotype_report(engine.processed_instructions['Disease A'], "Disease A", overlaps=False)
    assert engine.datasets['primary_care'].data.shape == (7, 3)
    assert engine.datasets['barts_health'].data.shape == (10, 4)
    
    assert phenotype_report.counts['primary_care_Disease_A_snomed']['patient_count'] == 2
    assert phenotype_report.counts['primary_care_Disease_A_snomed']['event_count'] == 4

    assert phenotype_report.counts['barts_health_Disease_A_ICD10']['patient_count'] == 2
    assert phenotype_report.counts['barts_health_Disease_A_ICD10']['event_count'] == 2


def test__generate_phenotype_report_with_demographics():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    engine.organise_into_phenotypes()

    demographics = DemographicDataset("tests/test_data/demographics/processed.arrow")

    phenotype_report = engine._generate_phenotype_report(engine.processed_instructions['Disease A'],
                                                         "Disease A",
                                                         overlaps=False,
                                                         demographics=demographics)
    assert engine.datasets['primary_care'].data.shape == (7, 3)
    assert engine.datasets['barts_health'].data.shape == (10, 4)

    expected_keys = ["primary_care_Disease_A_snomed", "barts_health_Disease_A_ICD10"]
    assert set(phenotype_report.counts.keys()) == set(expected_keys)


def test__generate_phenotype_report_with_overlaps():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    engine.organise_into_phenotypes()

    phenotype_report = engine._generate_phenotype_report(engine.processed_instructions['Disease A'], "Disease A", overlaps=True)
    assert engine.datasets['primary_care'].data.shape == (7, 3)
    assert engine.datasets['barts_health'].data.shape == (10, 4)

    expected_keys = ["primary_care_Disease_A_snomed_only", "barts_health_Disease_A_ICD10_only", "primary_care_Disease_A_snomed_and_barts_health_Disease_A_ICD10", "all_datasets"]
    assert set(phenotype_report.overlaps.keys()) == set(expected_keys)


def test__generate_phenotype_report_write_to_file():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    engine.organise_into_phenotypes()
    engine._generate_phenotype_report(engine.processed_instructions['Disease A'], "Disease A", reports_folder_path="tests/phenotype_report/test_reports", overlaps=False)
    
    # check the file exists
    assert os.path.exists("tests/phenotype_report/test_reports/Disease A.json") == True

    # delte the file
    os.remove("tests/phenotype_report/test_reports/Disease A.json")


def test_generate_empty_template_file():
    PhenotypeReportEngine.generate_empty_template_file("tests/phenotype_report/test_reports/test_template.csv")

    # check the file exists
    assert os.path.exists("tests/phenotype_report/test_reports/test_template.csv") == True

    # delte the file
    os.remove("tests/phenotype_report/test_reports/test_template.csv")


def test_generate_reports():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_full_index.csv")
    engine.organise_into_phenotypes()
    reports = engine.generate_reports(overlaps=False)

    # assert that the dataset is only loaded once per primary care and secondary care
    assert len(engine.datasets) == 2

    # assert 2 reports are generated
    assert len(reports) == 2
    assert reports['Disease A'].name == "Disease A"
    assert reports['Disease B'].name == "Disease B"

    # assert the counts are correct
    assert reports['Disease A'].counts['primary_care_Disease_A_snomed']['patient_count'] == 2
    assert reports['Disease A'].counts['primary_care_Disease_A_snomed']['event_count'] == 4
    assert reports['Disease A'].counts['barts_health_Disease_A_ICD10']['patient_count'] == 2
    assert reports['Disease A'].counts['barts_health_Disease_A_ICD10']['event_count'] == 2

    assert reports['Disease B'].counts['primary_care_Disease_B_snomed']['patient_count'] == 2
    assert reports['Disease B'].counts['primary_care_Disease_B_snomed']['event_count'] == 3
    assert reports['Disease B'].counts['barts_health_Disease_B_ICD10']['patient_count'] == 2
    assert reports['Disease B'].counts['barts_health_Disease_B_ICD10']['event_count'] == 3


def test__load_codelist():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    engine.organise_into_phenotypes()

    codelist = engine._load_codelist(codelist_name="Disease_A_snomed",
                                     codelist_path="tests/codelists/test_data/good_snomed_codelist.csv",
                                     codelist_type="SNOMED",
                                     add_x_codes="no")
    assert len(codelist.data) == 2
    assert codelist.data[0] == {'code': '100000001', 'term': 'Disease A - 1'}
    assert codelist.data[1] == {'code': '100000002', 'term': 'Disease A - 2'}

def test__load_codelist_without_x():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    engine.organise_into_phenotypes()

    codelist = engine._load_codelist(codelist_name="Disease_A_ICD10",
                                        codelist_path="tests/codelists/test_data/good_icd_codelist.csv",
                                        codelist_type="ICD10",
                                        add_x_codes="no")
    assert len(codelist.data) == 2

    assert codelist.data[0] == {'code': 'A01', 'term': 'Disease A - 1'}
    assert codelist.data[1] == {'code': 'A02', 'term': 'Disease A - 2'}


def test__load_codelist_with_x():
    engine = PhenotypeReportEngine("tests/phenotype_report/test_index.csv")
    engine.organise_into_phenotypes()

    codelist = engine._load_codelist(codelist_name="Disease_A_ICD10",
                                        codelist_path="tests/codelists/test_data/good_icd_codelist.csv",
                                        codelist_type="ICD10",
                                        add_x_codes="yes")
    assert len(codelist.data) == 4
    assert codelist.data[0] == {'code': 'A01', 'term': 'Disease A - 1'}
    assert codelist.data[1] == {'code': 'A01X', 'term': 'Disease A - 1'}
    assert codelist.data[2] == {'code': 'A02', 'term': 'Disease A - 2'}
    assert codelist.data[3] == {'code': 'A02X', 'term': 'Disease A - 2'}
