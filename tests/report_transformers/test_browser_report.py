import polars as pl
import pytest
import os
from tests.report_transformers.utils import make_phenotype_reports_for_testing


from tretools.report_transformers.browser_report import BrowserReportTransformer


def test_browser_report_transformer():
    # make a list of PhenotypeReports
    phenotype_reports = make_phenotype_reports_for_testing()

    # make a BrowserReportTransformer
    browser_reporter = BrowserReportTransformer.load_from_objects(phenotype_reports)

    # make the browser report
    metadata = {
        "author": "G&H phenotype taskforce",
        "year_of_creation": 2023,
        "tag": "MultipleAI",
        "body_system": "Endocrine System",
        "description": "This phenotype aims to capture instances of Type 2 Diabetes while excluding cases of Gestational and Type 1 Diabetes.",
        "github_url": [
            "https://github.com/example_repo/codelist_type2_diabetes"
        ]}

    browser_reporter.transform(metadata_path="tests/report_transformers/browser_reports/metadata.csv", path="tests/report_transformers/browser_reports")


