# Summary Report Readme for 'Disease A'

## Report Generation Date and Time

This report was generated on 13 December 2023.

## Report Overview

This summary report provides an overview of the counts associated with the 'Disease A' phenotype. It has been automatically generated using the 'tre-tools' package, available at [TRE Tools on GitHub](https://github.com/genes-and-health/tre-tools). For detailed information about this tool, please refer to the [README.md](https://github.com/genes-and-health/tre-tools/blob/main/README.md) in the 'tre-tools' GitHub repository. Your feedback on this tool is highly appreciated.

This tool aggregates datasets from various sources and utilises specific codelists to identify events in the dataset. The focus of this report is to summarise these findings, particularly highlighting the first recorded event for each patient.

## Codelists Utilised

This report utilises the codelists below. For more information on how these were constructed, please check the readme of the Codelist files. 

### SNOMED Codelist

**Path to Codelist**: codelists/disease_a_snomed.csv

| Code |
| --- |
| 100000001 |
| 100000002 |

### ICD10 Codelist

**Path to Codelist**: Codelists/disease_a_icd.csv

| Code |
| --- |
| A021 |
| A01 |

## Datasets

The datasets used in this report have been pre-processed using the 'tre-tools' package. This pre-processing includes the following steps:

- The datasets are loaded into memory using the 'tre-tools' package.
- The datasets are filtered to only include the columns required for the analysis.
- The datasets are filtered to only include the rows that have a PseudoNHS number and a date/code for an event.
- Duplicate rows are removed from the datasets. Duplicates are defined as rows that have the same PseudoNHS number, date, and code.
In the interest of transparency, the logs for the pre-processing of each dataset are provided below.

### Logs for Dataset Pre-processing

**Name of Dataset**: primary_care

**Type of Dataset**: primary_care

**Logs**: The logs for this pre-processing are provided below.

| Date | Message |
| --- | --- |
| 2023-12-13 23:36:02 | Loaded data from Datasets/primary_care_data.csv |
| 2023-12-13 23:37:01 | Column names not validated |
| 2023-12-13 23:37:01 | Key columns are standardised, however extra columns found: extra_col. Run _drop_unneeded_columns() to drop these columns. |
| 2023-12-13 23:37:01 | Unneeded 2 column(s) dropped |
| 2023-12-13 23:37:01 | Dropped 6 rows with empty values or empty date strings |
| 2023-12-13 23:37:01 | Date format standarised |
| 2023-12-13 23:37:01 | Deduplicated data based on: nhs_number, code, date |

**Name of Dataset**: secondary_care

**Type of Dataset**: barts_health

**Logs**: The logs for this pre-processing are provided below.

| Date | Message |
| --- | --- |
| 2023-12-13 23:51:30 | Loaded data from datasets/barts_diagnosis.tab |
| 2023-12-13 23:51:30 | Column names not validated |
| 2023-12-13 23:51:30 | Key columns are standardised, however extra columns found: ICD_Diagnosis_Num, CDS_Activity_Dt. Run _drop_unneeded_columns() to drop these columns. |
| 2023-12-13 23:51:30 | Unneeded 3 column(s) dropped |
| 2023-12-13 23:51:30 | Dropped 0 rows with empty values or empty date strings |
| 2023-12-13 23:51:30 | Date format standarised |
| 2023-12-13 23:51:30 | Deduplicated data based on: nhs_number, code, date |

## Counting first events

### Logs for counting the Codelist against each dataset

The logs for counting the Codelist against each dataset are provided below. Pleasebe aware that patients can appear in multiple datasets, so the same patient may be countedas having an event in multiple datasets. The number of patients and events in each datasetwho meet the criteria for an event defined by the Codelist are provided below. Whenall the counts for the different datasets are combined, a patient can only appear one (date of first event regardless of dataset). This gives the impression that the total has reduced in number. 

**Name of Dataset**: primary_care

**Type of Dataset**: primary_care

**Logs**: The logs for this counting are provided below.

| Date | Message |
| --- | --- |
| 2023-12-13 23:51:30 | There are 7 events in the dataset |
| 2023-12-13 23:51:30 | Counting events for codelist primary_care |
| 2023-12-13 23:51:30 | There are 4 events in the dataset for the codelist |
| 2023-12-13 23:51:30 | There are 2 people in the dataset for the codelist |
| 2023-12-13 23:51:30 | Demographic data added to the report |

**Name of Dataset**: secondary_care

**Type of Dataset**: barts_health

**Logs**: The logs for this counting are provided below.

| Date | Message |
| --- | --- |
| 2023-12-13 23:51:30 | There are 10 events in the dataset |
| 2023-12-13 23:51:30 | Counting events for codelist secondary_care |
| 2023-12-13 23:51:30 | There are 2 events in the dataset for the codelist |
| 2023-12-13 23:51:30 | There are 2 people in the dataset for the codelist |
| 2023-12-13 23:51:30 | Demographic data added to the report |

