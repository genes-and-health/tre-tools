"""
This contains the SummaryReportTransformer class. This class is used to transform a list of PhenotypeReports
into a summary report per phenotype, an overall summary report, and a readme file.

The summary report per phenotype will be a csv file with the following structure:
- nhs_number
- code_of_first_event
- date_of_first_event
- dataset_type_of_first_event
- age_at_first_event

The overall summary report will be a csv file with the following structure:
- phenotype_name
- number of people with events across all datasets
- paths to the summary report per phenotype
- paths to the readme files for each phenotype

The readme file will be a md file with a table of the logs for each dataset.
"""
from __future__ import annotations
import polars as pl
from datetime import datetime
from typing import List, Dict
import os

from tretools.report_transformers.base import ReportTransformer
from tretools.phenotype_report.report import PhenotypeReport


class SummaryReportTransformer(ReportTransformer):
    def __init__(self):
        super().__init__()
        self.summary = []

    @classmethod
    def load_from_objects(cls, objects: List[PhenotypeReport]) -> SummaryReportTransformer:
        """
        Loads a list of PhenotypeReports into a SummaryReportTransformer. Each PhenotypeReport
        will be in a list under the attribute reports.

        Args:
            objects (List[PhenotypeReport]): A list of PhenotypeReports.

        Returns:
            ReportTransformer: A SummaryReportTransformer with the PhenotypeReports loaded into it.
        """
        transformer = SummaryReportTransformer()
        transformer.reports = objects
        return transformer

    def _combine_reports(self) -> Dict:
        # empty dict to hold summary reports per phenotype
        patient_table = {}
        logs = {}
        summary_reports = {}

        for phenotype in self.reports:
            # empty dataframe per phenotype
            df = pl.DataFrame()
            log = []
            summary_report = {}

            for name, report in phenotype.counts.items():
                # Add the logs for the phenotype report to the summary log
                summary_report[name] = {}
                summary_report[name]["codelists"] = {"codes": report["code"], "codelist_type": report["codelist_type"], "codelist_path": report["codelist_path"]}
                summary_report[name]["dataset_info"] = {"codelist_log": report["log"],
                                                        "dataset_type": report["dataset_type"],
                                                        "dataset_log": report["dataset_log"]}
                summary_report[name]["summary_report"] = {"patient_count": report["patient_count"], "event_count": report["event_count"]}

                # if report["nhs_numbers"] has code with i64, convert to str
                report["nhs_numbers"] = report["nhs_numbers"].with_columns(report["nhs_numbers"].cast(pl.Utf8))

                # drop gender
                report["nhs_numbers"] = report["nhs_numbers"].select(["nhs_number", "code", "date", "age_at_event"])

                # add new columns to the report["nhs_numbers"] with the dataset type and codelist type
                dataset_type = report["dataset_type"]
                report["nhs_numbers"] = report["nhs_numbers"].with_columns(
                    pl.Series("dataset_type", [dataset_type] * len(report["nhs_numbers"])))
                report["nhs_numbers"] = report["nhs_numbers"].with_columns(
                    pl.Series("codelist_type", [report["codelist_type"]] * len(report["nhs_numbers"])))

                # add the results to the dataframe whicih combines all the patients together
                df = df.vstack(report["nhs_numbers"])
            # return df

            # log the number of events and unique patients prior to filtering for first event
            total_events = len(df)
            log.append(f"{datetime.now()}: Total number of events prior to filtering for first event for {phenotype.name} is {total_events}, with {len(df['nhs_number'].unique())} unique patients.")

            # For each nhs number get the first event and drop the rows that have a date that is not the first event
            df = df.sort(["nhs_number", "date"]).groupby("nhs_number").first()
            first_events = (df.sort(["nhs_number", "date"])
                            .groupby("nhs_number").first())

            # log the number of events and unique patients after filtering for first event
            total_events = len(first_events)
            log.append(f"{datetime.now()}: Total number of events after filtering for first event for {phenotype.name} is {total_events}, with {len(first_events['nhs_number'].unique())} unique patients.")

            patient_table[phenotype.name] = first_events
            logs[phenotype.name] = log
            summary_reports[phenotype.name] = summary_report

        return patient_table, logs, summary_reports

    def _make_summary_report_per_phenotype(self, path: str):
        patient_table, logs, summary_reports = self._combine_reports()

        # for phenotype_name
        for phenotype_name, df in patient_table.items():

            # make folder to save the summary report to
            if not os.path.exists(f"{path}/{phenotype_name}/"):  # exclude from coverage as testing os rather than code
                os.mkdir(f"{path}/{phenotype_name}") # pragma: no cover

            # make a path to save the summary report to
            path_to_report = f"{path}/{phenotype_name}/{phenotype_name}_summary_report.csv"

            # # write the summary report to csv
            df.write_csv(path_to_report)

            path_to_readme =f"{path}/{phenotype_name}/README"

            # make a readme file for the summary report
            self._write_readme(phenotype_name, logs[phenotype_name],
                               summary_reports[phenotype_name],
                               path_to_readme,
                               path_to_report
                               )

            # add the details to the summary
            self.summary.append({"phenotype_name": phenotype_name,
                                 "patient_count": len(df),
                                 "path_to_summary_report": path_to_report,
                                 "path_to_readme": path_to_readme})


    def _write_readme(self, phenotype_name, logs, summary_reports, path_to_readme, path_to_report):

        # Make a title for the readme in H1
        markdown = f"# Summary Report Readme for '{phenotype_name}'\n\n"

        # Add datetime as String in format DD Month YYYY
        markdown += "## Report Generation Date and Time\n\n"
        markdown += f"This report was generated on {datetime.now().strftime('%d %B %Y')}.\n\n"

        # Explain what the report is
        markdown += "## Report Overview\n\n"
        markdown += f"This summary report provides an overview of the counts associated with the '{phenotype_name}' phenotype. " \
                    "It has been automatically generated using the 'tre-tools' package, " \
                    "available at [TRE Tools on GitHub](https://github.com/genes-and-health/tre-tools). " \
                    "For detailed information about this tool, please refer to the [README.md](https://github.com/genes-and-health/tre-tools/blob/main/README.md) " \
                    "in the 'tre-tools' GitHub repository. Your feedback on this tool is highly appreciated.\n\n" \
                    "This tool aggregates datasets from various sources and utilises specific codelists to identify events in the dataset. " \
                    "The focus of this report is to summarise these findings, particularly highlighting the first recorded event for each patient.\n\n"

        # Add the codelists used
        markdown += "## Codelists Utilised\n\nThis report utilises the codelists below. For more information on how these were constructed, please check the readme of the Codelist files. \n\n"

        for dataset_name, details in summary_reports.items():
            markdown += f"### {details['codelists']['codelist_type']} Codelist\n\n"
            markdown += f"**Path to Codelist**: {details['codelists']['codelist_path']}\n\n"
            markdown += codelist_to_markdown_table(details["codelists"]["codes"])
            markdown += "\n"

        # Explainer for the dataset pre-processing
        markdown += "## Datasets\n\n"
        markdown += "The datasets used in this report have been pre-processed using the 'tre-tools' package. " \
                    "This pre-processing includes the following steps:\n\n"
        markdown += "- The datasets are loaded into memory using the 'tre-tools' package.\n"
        markdown += "- The datasets are filtered to only include the columns required for the analysis.\n"
        markdown += "- The datasets are filtered to only include the rows that have a PseudoNHS number and a date/code for an event.\n"
        markdown += "- Duplicate rows are removed from the datasets. Duplicates are defined as rows that have the same PseudoNHS number, date, and code.\n"

        markdown += "In the interest of transparency, the logs for the pre-processing of each dataset are provided below.\n\n"

        markdown += "### Logs for Dataset Pre-processing\n\n"

        # Add the logs for the dataset pre-processing
        for dataset_name, details in summary_reports.items():
            markdown += f"**Name of Dataset**: {dataset_name}\n\n"
            markdown += f"**Type of Dataset**: {details['dataset_info']['dataset_type']}\n\n"  # Emphasise Dataset
            markdown += "**Logs**: The logs for this pre-processing are provided below.\n\n"
            markdown += logs_to_markdown_table(details["dataset_info"]["dataset_log"])
            markdown += "\n"

        # Explainer for the counting
        markdown += "## Counting first events\n\n"
        markdown += "### Logs for counting the Codelist against each dataset\n\n"
        markdown += ("The logs for counting the Codelist against each dataset are provided below. Please"
                     "be aware that patients can appear in multiple datasets, so the same patient may be counted"
                      "as having an event in multiple datasets. The number of patients and events in each dataset"
                      "who meet the criteria for an event defined by the Codelist are provided below. When"
                      "all the counts for the different datasets are combined, a patient can only appear one ("
                      "date of first event regardless of dataset). This gives the impression that the total "
                      "has reduced in number. \n\n")

        # Add the logs for the dataset pre-processing
        for dataset_name, details in summary_reports.items():
            markdown += f"**Name of Dataset**: {dataset_name}\n\n"  # Emphasise Dataset
            markdown += f"**Type of Dataset**: {details['dataset_info']['dataset_type']}\n\n" \
                        "**Logs**: The logs for this counting are provided below.\n\n"
            markdown += logs_to_markdown_table(details["dataset_info"]["codelist_log"])
            markdown += "\n"

        # write to file
        with open(f"{path_to_readme}.md", "w") as f:
            f.write(markdown)


    def _write_overall_summary_readme(self, path: str) -> None:
        """
        - phenotype_name
        - number of people with events across all datasets
        - number of events across all datasets
        - paths to the summary report per phenotype
        - paths to the readme files for each phenotype
        """
        # Make a title for the readme in H1
        markdown = "# Overall Summary Report Readme\n\n"

        # Add datetime as String in format DD Month YYYY
        markdown += "## Report Generation Date and Time\n\n"
        markdown += f"This report was generated on {datetime.now().strftime('%d %B %Y')}.\n\n"

        # Explain what the report is
        markdown += "## Report Overview\n\n"
        markdown += "This summary report provides an overview of the counts associated with each phenotype. " \
                    "It has been automatically generated using the 'tre-tools' package, " \
                    "available at [TRE Tools on GitHub](https://github.com/genes-and-health/tre-tools). " \

        # write a markdown table with the summary
        markdown += "\n\n## Summary\n\n"
        markdown += "| Phenotype Name | Number of People with Events Across All Datasets | Paths to Summary Report per Phenotype | Paths to Readme Files for Each Phenotype |\n"
        markdown += "| --- | --- | --- | --- |\n"
        for summary in self.summary:
            markdown += f"| {summary['phenotype_name']} | {summary['patient_count']} | {summary['path_to_summary_report']} | {summary['path_to_readme']}.md |\n"

        # write to file
        with open(f"{path}/overall_summary_report_README.md", "w") as f:
            f.write(markdown)

    def transform(self, path: str = "summary_reports") -> None:
        """
        This will transform the list of PhenotypeReports into a summary report per phenotype, an overall summary report,
        and a readme file for each phenotype.
        """
        # make a folder to save the summary reports to
        if not os.path.exists(path): # exclude from coverage as testing os rather than code
            os.mkdir(path) # pragma: no cover

        # make a summary report per phenotype
        self._make_summary_report_per_phenotype(path)

        # make a readme for the overall summary report
        self._write_overall_summary_readme(path)


def logs_to_markdown_table(logs):
    """
    Convert a list of log entries to a Markdown table.
    Each log entry is assumed to be in the format 'YYYY-MM-DD HH:MM:SS.ssssss: Message'.
    We format the timestamp to 'YYYY-MM-DD HH:MM' and separate the message.
    """
    markdown = "| Date | Message |\n| --- | --- |\n"

    for log in logs:
        # Split the log entry into timestamp and message
        timestamp, message = log.split(": ", 1)
        # Format the timestamp to 'YYYY-MM-DD HH:MM'
        timestamp = timestamp.split(".")[0]
        # Add the row to the table
        markdown += f"| {timestamp} | {message} |\n"

    return markdown

def codelist_to_markdown_table(codes):
    """
    Convert a list of codes to a Markdown table.
    """
    markdown = "| Code |\n| --- |\n"  # Table header
    for code in codes:
        markdown += f"| {code} |\n"  # Table rows
    return markdown
