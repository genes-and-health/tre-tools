from tretools.report_transformers.summary_report import SummaryReportTransformer
from tests.report_transformers.utils import make_phenotype_reports_for_testing

import os



def test_summary_report_transformer():
    # make a list of PhenotypeReports
    phenotype_reports = make_phenotype_reports_for_testing()

    # make a SummaryReportTransformer
    summary_reporter = SummaryReportTransformer.load_from_objects(phenotype_reports)

    # combine the reports
    summary_reporter.transform(path="tests/report_transformers/reports")


