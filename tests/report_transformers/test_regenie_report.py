from tretools.report_transformers.regenie_report import RegenieReportTransformer
from tests.report_transformers.utils import make_phenotype_reports_for_testing

import polars as pl
import pytest
import os


MAPPING_PATH = "tests/test_data/mapping_files/regenie_mapping_file.csv"
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
    result = regenie_reporter.transform("tests/report_transformers/regenie_reports")
    first_phenotype = result[1]
    assert set(first_phenotype['FID']) == {1}

    # since the order of the rows is not guaranteed, we need to check the values of each column separately
    # get the row with nhs_number = "73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B"
    # this should have both disease A and disease B
    first_phenotype = result.filter(pl.col("nhs_number") == "73951AB0712D6E241E8222EDCCF28AE86DA72814078D6F48ECE512C91B5B104B")
    assert set(first_phenotype['broad_id']) == {"GNH-15001987654322"}
    assert set(first_phenotype['gsa_id']) == {"15001987654322_123456789012_R01C01"}
    assert set(first_phenotype['Disease A']) == {1}
    assert set(first_phenotype['Disease B']) == {1}

    # get the row with nhs_number = "84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"
    # this should have disease A and disease B
    second_phenotype = result.filter(pl.col("nhs_number") == "84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A")
    assert set(second_phenotype['nhs_number']) == {"84950DE0614A5C241F7223FBCCD27BE87DB61915972C7E49EDF519B72A3A104A"}
    assert set(second_phenotype['Disease A']) == {1}
    assert set(second_phenotype['Disease B']) == {1}

    # get the row with nhs_number = "53952EF0503F7F341D9121DBCCC39DE95EA83713167E5E57EDB613A60D4C104C"
    # this should have disease A but not disease B
    third_phenotype = result.filter(pl.col("nhs_number") == "53952EF0503F7F341D9121DBCCC39DE95EA83713167E5E57EDB613A60D4C104C")
    assert set(third_phenotype['nhs_number']) == {"53952EF0503F7F341D9121DBCCC39DE95EA83713167E5E57EDB613A60D4C104C"}
    assert set(third_phenotype['Disease A']) == {1}
    assert set(third_phenotype['Disease B']) == {0}


def test_mapping_file_missing():
    with pytest.raises(ValueError) as e:
        # make a list of PhenotypeReports
        phenotype_reports = make_phenotype_reports_for_testing()

        # make a SummaryReportTransformer
        regenie_reporter = RegenieReportTransformer.load_from_objects(phenotype_reports)

        # load the mapping file
        regenie_reporter.load_mapping_file("BAD_PATH", MAPPING_CONFIG)

    assert str(e.value) == "The Broad ID/GSA reference file BAD_PATH does not exist or is empty."


def test_mapping_file_empty():
    with pytest.raises(ValueError) as e:
        # make a list of PhenotypeReports
        phenotype_reports = make_phenotype_reports_for_testing()

        # make a SummaryReportTransformer
        regenie_reporter = RegenieReportTransformer.load_from_objects(phenotype_reports)

        # load the mapping file
        regenie_reporter.load_mapping_file("tests/test_data/mapping_files/empty_file.csv", MAPPING_CONFIG)

    assert str(e.value) == "The Broad ID/GSA reference file tests/test_data/mapping_files/empty_file.csv does not exist or is empty."


def test_makes_dir_is_absent():
    # make a list of PhenotypeReports
    phenotype_reports = make_phenotype_reports_for_testing()

    # make a SummaryReportTransformer
    regenie_reporter = RegenieReportTransformer.load_from_objects(phenotype_reports)

    # load the mapping file
    regenie_reporter.load_mapping_file(MAPPING_PATH, MAPPING_CONFIG)

    # make the summary report
    result = regenie_reporter.transform("tests/report_transformers/regenie_reports/missing_dir")

    # check that the directory was created
    assert os.path.exists("tests/report_transformers/regenie_reports/missing_dir")

    # check that the file was created
    assert os.path.exists("tests/report_transformers/regenie_reports/missing_dir/summary.csv")

    # remove the directory and all files
    os.remove("tests/report_transformers/regenie_reports/missing_dir/summary.csv")
    os.remove("tests/report_transformers/regenie_reports/missing_dir/README.md")
    os.rmdir("tests/report_transformers/regenie_reports/missing_dir")

