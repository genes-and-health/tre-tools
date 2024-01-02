from tretools.report_transformers.summary_report import SummaryReportTransformer
from tests.report_transformers.utils import make_phenotype_reports_for_testing

import os



def test_summary_report_transformer():
    # make a list of PhenotypeReports
    phenotype_reports = make_phenotype_reports_for_testing()

    # make a SummaryReportTransformer
    summary_reporter = SummaryReportTransformer.load_from_objects(phenotype_reports)

    # combine the reports
    summary_reporter.transform(path="tests/report_transformers/summary_reports")

    # check that the directory was created
    assert os.path.exists("tests/report_transformers/summary_reports/Disease A")
    assert os.path.exists("tests/report_transformers/summary_reports/Disease B")

    # check that the files were created
    assert os.path.exists("tests/report_transformers/summary_reports/Disease A/Disease A_summary_report.csv")
    assert os.path.exists("tests/report_transformers/summary_reports/Disease A/README.md")
    assert os.path.exists("tests/report_transformers/summary_reports/Disease B/Disease B_summary_report.csv")
    assert os.path.exists("tests/report_transformers/summary_reports/Disease B/README.md")
    assert os.path.exists("tests/report_transformers/summary_reports/overall_summary_report_README.md")

    # remove the directories and all files
    os.remove("tests/report_transformers/summary_reports/Disease A/Disease A_summary_report.csv")
    os.remove("tests/report_transformers/summary_reports/Disease A/README.md")
    os.rmdir("tests/report_transformers/summary_reports/Disease A")
    os.remove("tests/report_transformers/summary_reports/Disease B/Disease B_summary_report.csv")
    os.remove("tests/report_transformers/summary_reports/Disease B/README.md")
    os.rmdir("tests/report_transformers/summary_reports/Disease B")
    os.remove("tests/report_transformers/summary_reports/overall_summary_report_README.md")


