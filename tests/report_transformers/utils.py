import pytest

from tretools.datasets.demographic_dataset import DemographicDataset
from tretools.datasets.processed_dataset import ProcessedDataset
from tretools.codelists.codelist import Codelist
from tretools.codelists.codelist_types import CodelistType
from tretools.datasets.dataset_enums.dataset_types import DatasetType
from tretools.phenotype_report.report import PhenotypeReport
from tretools.report_transformers.base import ReportTransformer


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

def make_phenotype_reports_for_testing():
    snomed_codelist = Codelist(SNOMED_CODELIST, CodelistType.SNOMED.value)
    primary_care = ProcessedDataset(PRIMARY_CARE_DATASET, DatasetType.PRIMARY_CARE.value, CodelistType.SNOMED.value, log_path="tests/test_data/primary_care/processed_data_log.txt")
    secondary_care = ProcessedDataset(SECONDARY_CARE_DATASET, DatasetType.BARTS_HEALTH.value, CodelistType.ICD10.value, log_path="tests/test_data/barts_health/diagnosis_log.txt")
    icd_codelist = Codelist(ICD_CODELIST, CodelistType.ICD10.value)

    # load the demographic data
    demographic_data = DemographicDataset(path_to_mapping_file=DEMOGRAPHIC_MAPPING_FILE, path_to_demographic_file=DEMOGRAPHIC_FILE)
    demographic_data.process_dataset(MAPPING_CONFIG)

    # Make a list of PhenotypeReports
    reports = []
    phenotype_report_1 = PhenotypeReport("Disease A")
    phenotype_report_1.add_count("disease_a_primary_care", snomed_codelist, primary_care, demographics=demographic_data)
    phenotype_report_1.add_count("disease_a_secondary_care", icd_codelist, secondary_care, demographics=demographic_data)
    reports.append(phenotype_report_1)

    phenotype_report_2 = PhenotypeReport("Disease B")
    phenotype_report_2.add_count("disease_b_primary_care", snomed_codelist, primary_care, demographics=demographic_data)
    reports.append(phenotype_report_2)
    return reports

