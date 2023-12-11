# tretools

`tretools` is a Python package tailored for data scientists and researchers looking to streamline the process of running codelist numbers against various datasets in the Genes and Health TRE. It also provides a variety of data cleaning functions to prepare your datasets for analysis.

## Getting Started
### Prerequisites

Before installing `tretools`, ensure you have the following installed:
- Python 3.8+
- pip 
- pip-tools for managing dependencies
- Just

### Installation
The package is being installed into the TRE and can be used in the usual way there. 

If you wish to install it locally, you can do so in two ways. 

#### 1. Install from GitHub
```
pip install git+https://github.com/genes-and-health/tre-tools.git
```

#### 2. Install from local directory in order to make changes to the package
Clone the repo:
```
git clone https://github.com/genes-and-health/tre-tools.git
```

Install the package in editable mode:
```
pip install -e <path-to-tre-tools>
```

## Usage
There are two building blocks to `tretools`:

1. `Codelist`
2. `Dataset`

### Codelists
A `Codelist` is a collection of codelist numbers that can be used to run against a dataset. There are 3 types of codelists:

1. SNOMED
2. ICD10
3. OPCS

A codelist can be created by reading in a CSV file. This CSV must have a code column and a term column. 

```
diabetes_codelist = Codelist("diabetes.csv", "SNOMED")
```

The easiest way is if these columns are named `code` and `term` respectively. If they are not, you can specify the column names when creating the codelist. In the example below, the code column is called `snomed_code` and the term column is called `snomed_term`.

```
diabetes_codelist = Codelist("diabetes.csv", "SNOMED", code_column="snomed_code", term_column="snomed_term")
```

The codelist will validate the codes to ensure they meet the expected format for the codelist type. For example, a SNOMED code must contain a restricted quantity of numbers.

There is also an additional option for use with ICD10 codes to specify where you also want to add X codes - that is if you have a code that is A01, you also want to add A01X. This is done by setting the `add_x_codes` parameter to `True` when creating the codelist.

```
diabetes_codelist = Codelist("diabetes.csv", "ICD10", add_x_codes=True)
```

### Datasets
A `Dataset` is a collection of data that can be used to run against a codelist. There are 2 types of datasets:

1. `RawDataset`
2. `ProcessedDataset`

All datasets have the ability to be written to a CSV file or a feather file. 

#### RawDataset
A `RawDataset` is a dataset that has not been cleaned or processed in any way. A `ProcessedDataset` is a dataset that has been cleaned and processed.

```
dataset = RawDataset(path="procedures.csv", dataset_type="primary_care", coding_system="SNOMED")
```

We can convert this dataset to a `ProcessedDataset` by calling the `process_dataset()`. This will clean the dataset by standarising the column names, dropping unneeded columns, standarising the date format and deduplicating. It requires two parameters:

1. `deduplication_options`: A list of columns to deduplicate on. This must include `nhs_number` and `code`, and can optionally include `term` and `date`.
2. `column_maps`: A dictionary of column names to be renamed. This means indicating which of the column name in the dataset is the NHS number, code and term.

The `process_dataset()` method will return a `ProcessedDataset` instance. It does the following things:

- Standarise the column names so the NHS number column is called `nhs_number`, the code column is called `code`, term column is called `term` and the date column is called `date`.
- Drop unneeded columns - We are only interested in the NHS number, code, term and date columns.
- Drop all rows with null values - We are only interested in rows where we have a full set of data. 
- Standarise the date format - We want the date to be in the format `YYYY-MM-DD`. It can handle a variety of date formats.
- Deduplicate - We want to deduplicate on the NHS number and code. 

At this stage, the same code for the same patient on a different date is included. 

#### ProcessedDataset
A `ProcessedDataset` is a dataset that has been cleaned and processed. 

A `ProcessedDataset` can be created by reading in a CSV file or a feather file, or directly from a `RawDataset` instance by calling the `process_dataset()` method. 

There are two main methods for a `ProcessedDataset`:
1. `merge_with_dataset()`: This method allows you to merge two ProcessedDatasets together. It will check that the coding system and dataset type are the same, and that the column names are the same. It will then merge the two datasets together.
2. `deduplicate()`: This method allows you to deduplicate the dataset. It will remove rows where the entire row is the same, and for duplicate NHS number and code, it will keep the first event after a specified date. If no date is specified, it will keep the first event.

## Phenotype Reports
A phenotype report is a report that shows the number of patients in a dataset that have a code in a codelist. It takes a codelist and a dataset as input, and outputs a report showing the number of patients in the dataset that have a code in the codelist.

### Creating a Phenotype Report
A phenotype report can be created by calling the `PhenotypeReport` class and passing in a name for the report. 

```
diabetes_report = PhenotypeReport("diabetes")
```

### Adding a count to a Phenotype Report
A count can be added to a phenotype report by calling the `add_count()` method. This method takes 3 parameters:

1. `name_of_count`: The name of the count. This will be used to identify the count in the report.
2. `codelist`: The codelist to count. This must be a `Codelist` instance.
3. `dataset`: The dataset to count. This must be a `ProcessedDataset` instance.

```
diabetes_report.add_count("primary_care", diabetes_codelist, primary_care_dataset)
```

Note that the name of the count must be unique within the report. If you try to add a count with the same name as an existing count, it will raise an error.

The `add_count()` method will count the number of patients in the dataset that have a code in the codelist. 

### Overlaps
A phenotype report can also report on the overlaps between datasets. This can be done by calling the `report_overlaps()` method. This will report on patients unique to each dataset and those appearing in one or more datasets.

```
diabetes_report.report_overlaps()
```

### Saving a Phenotype Report
A phenotype report can be saved to a JSON file by calling the `save_to_json()` method. This method takes 2 parameters:

1. `path`: The path to save the JSON file to.
2. `overwrite`: Whether to overwrite the file if it already exists. Defaults to `True`.

### Loading a Phenotype Report
A phenotype report can be loaded from a JSON file by calling the `load_from_json()` method. This method takes 1 parameter:

1. `path`: The path to the JSON file.

## Examples
### Creating a codelist
```
# Create codelists 
diabetes_snomed_codelist = Codelist("diabetes_snomed.csv", "SNOMED")
diabetes_icd_codelists = Codelist("diabetes_icd.csv", "ICD10", add_x_codes=True)

# Clean datasets
## Primary Care
primary_care_dataset = RawDataset("primary_care.csv", "primary_care", "SNOMED")
primary_care_dataset = primary_care_dataset.process_dataset(deduplication_options=["nhs_number", "code"], column_maps={"psuedo_nhs_number": "nhs_number", "code": "code", "term": "term", "date_of_event": "date"})

## Hospital Observations
hospital_dataset_1 = RawDataset("hospital_obs.csv", "barts_health", "SNOMED")
hospital_dataset_1 = hospital_dataset_1.process_dataset(deduplication_options=["nhs_number", "code"], column_maps={"pseudo_nhs_number": "nhs_number", "code": "code", "term": "term", "date_of_event": "date"})

## Hospital Admissions
hospital_dataset_2 = RawDataset("hospital_admissions.csv", "barts_health", "ICD10")
hospital_dataset_2 = hospital_dataset_2.process_dataset(deduplication_options=["nhs_number", "code"], column_maps={"pseudo_nhs_number": "nhs_number", "code": "code", "term": "term", "date_of_event": "date"})

# Combine hospital datasets
combined_hospital_dataset = hospital_dataset_1.merge_with_dataset(hospital_dataset_2)
combined_hospital_dataset = combined_hospital_dataset.deduplicate()

# Create phenotype report
diabetes_report = PhenotypeReport("diabetes")
diabetes_report.add_count("primary_care", diabetes_snomed_codelist, primary_care_dataset)
diabetes_report.add_count("hospital", diabetes_icd_codelists, combined_hospital_dataset)
diabetes_report.report_overlaps()
diabetes_report.save_to_json("diabetes_report.json")
```

## Engine
We can also run the above example using the `tretools` engine. This creates phenotypes reports using a CSV configuration file.

### Configuration File
A template configuration file can be created by:

```
from tretools.phenotype_report.engine import PhenotypeReportEngine

PhenotypeReportEngine.generate_empty_template_file("path/to/config/file.csv")
```

This will create a CSV file that can be filled in with the details of the codelists and datasets you want to use. It has the following columns:

- `phenotype_name`: The name of the phenotype. This will be used as the name of the report.
- `dataset_name`: The name of the dataset. This will be used to identify the dataset in the report.
- `dataset_path`: The path to the dataset.
- `dataset_type`: The type of the dataset. This can be `primary_care`, `barts_health`,  `nhs_digital` or `bradford`


### Running the Engine
```
from tretools.phenotype_report.engine import PhenotypeReportEngine

engine = PhenotypeReportEngine("path/to/config/file.csv")
engine.organise_into_phenotypes()
reports = engine.generate_reports(reports_folder_path="path/to/save/reports/to")
```

