import os
import csv

class CustomPhenotypeError(Exception):
    pass

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
    '''
    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)

    process_all_codelists(rows, output_directory, config)