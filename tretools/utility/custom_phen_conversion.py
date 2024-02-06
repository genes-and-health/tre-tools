"""
This module contains functions to process custom phenotype files and convert them into separate CSV files
for ICD10, SNOMED, and OPCS4 codelists
"""
import os
import csv
import polars as pl


from tretools.utility.errors import CustomPhenotypeError


def process_all_codelists(rows, output_directory, config):
    '''
    This function formats all three codelists (SNOMED, OPCS4, and ICD10) to be used as inputs for a custom package
    '''
    total_generated_records = 0  # A variable to track the total length of the generated separate CSV files

    for codelist_type in [config['ICD10_col_name'], config['SNOMED_col_name'], config['OPCS4_col_name']]:
        filtered_rows = [row for row in rows if row[config['code_col_name']] == codelist_type]
        total_generated_records += len(filtered_rows)

    # Check if the sum of counts from three separate files (SNOMED, ICD10, OPCS4) is equal to the number of rows in the original customs file
    original_length = len(rows) 

    if total_generated_records != original_length:
        raise CustomPhenotypeError(
            f"Error: Original custom phenotype file has {original_length} records, "
            f"while the generated ICD10, SNOMED, and OPCS4 files have {total_generated_records} records in total. "
            f"This may indicate that there is a codelist type in the original file that is not any of ICD10, SNOMED, or OPCS4. Alternatively, typos should be checked"
        )

    # If the lengths are equal, write the CSV files
    for codelist_type in [config['ICD10_col_name'], config['SNOMED_col_name'], config['OPCS4_col_name']]:
        filtered_rows = [row for row in rows if row[config['code_col_name']] == codelist_type]
        header = ['code', 'term']
        output_file = os.path.join(output_directory, f'customs_{codelist_type}.csv')

        with open(output_file, 'w', newline='') as csvfile_out:
            writer = csv.DictWriter(csvfile_out, fieldnames=header)
            writer.writeheader()
            writer.writerows([{'code': row['code'], 'term': row['phenotype']} for row in filtered_rows])

def process_custom_codelist(input_file, output_directory, config):
    '''
    The main function reads the custom codelists original file

    Args:
        input_file (str): The path to the original custom codelist file
        output_directory (str): The directory to save the generated separate CSV files
        config (dict): A dictionary containing the column names for the custom codelist file

    Example of the config dictionary:
    config = {
        'code_col_name': 'codelist_type',
        'ICD10_col_name': 'ICD10',
        'SNOMED_col_name': 'SNOMED',
        'OPCS4_col_name': 'OPCS4'
    }
    '''
    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    process_all_codelists(rows, output_directory, config)


def process_codelists_to_reference_files(input_file: str,
                                         output_directory: str,
                                         reference_file_path: str,
                                         dataset_config: dict,
                                         codelist_config: dict) -> None:
    """
    This function takes the output of the process_custom_codelist function and
    writes a separate CSV file to be used as a reference file.

    Args:
        input_file:
        output_directory:
        reference_file_path:
        dataset_config:
        codelist_config:

    Returns:
        None
    """
    # Read the input file
    df = pl.read_csv(input_file)

    # Loop through the df and save the separate CSV files, and then append the file paths
    # to the reference file
    for term, group in df.group_by('term'):
        # create filename
        filename = f"{output_directory}/{term}.csv"

        # grab the rows with the term
        group = df.filter(df['term'] == term)
        group = group.unique()

        # write to file
        group.write_csv(filename)

        # append to reference file
        with open(reference_file_path, 'a') as reference_file:
            line_to_append = {
                "phenotype_name": term,
                "dataset_name": dataset_config['dataset_name'],
                "dataset_path": dataset_config['dataset_path'],
                "dataset_type": dataset_config['dataset_type'],
                "codelist_name": f"{codelist_config['codelist_name']}_{term}",
                "codelist_path": filename,
                "codelist_type": codelist_config['codelist_type'],
                "with_x_in_icd": "no" # we may need to change this in the end
            }
            writer = csv.DictWriter(reference_file, fieldnames=line_to_append.keys())
            writer.writerow(line_to_append)
