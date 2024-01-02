from tretools.report_transformers.regenie_report import RegenieReportTransformer
from tests.report_transformers.utils import make_phenotype_reports_for_testing

import polars as pl


MAPPING_PATH = "tests/test_data/mapping_files/mapping_file.csv"
MAPPING_CONFIG = {"Pseudonhs_2023-11-08_uniq": "nhs_number",
                  "40028exomes_release_2023-JUL-07": "broad_id",
                  "51176GSA_Oct2023release": "gsa_id"
                  }


def test_summary_report_transformer():
    # make a list of PhenotypeReports
    phenotype_reports = make_phenotype_reports_for_testing()

    # make a SummaryReportTransformer
    regenie_reporter = RegenieReportTransformer.load_from_objects(phenotype_reports)

    # load the mapping file
    regenie_reporter.load_mapping_file(MAPPING_PATH, MAPPING_CONFIG)

    first_patient_nhs_number = "84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"
    first_mapping = regenie_reporter.data.filter(pl.col("nhs_number") == first_patient_nhs_number)

    assert set(first_mapping["nhs_number"]) == {first_patient_nhs_number}
    assert set(first_mapping["broad_id"]) == {"GNH-15001987654321"}
    assert set(first_mapping["gsa_id"]) == {"15001987654321_123456789012_R01C01"}

    # make the summary report
    result = regenie_reporter.transform()
    print(result)
    # result = regenie_reporter._combine_reports()
    # print(result)

    assert False

