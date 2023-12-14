import os
import csv

def process_custom_codelist(input_file, output_directory, output_prefix, code_col_name='term', ICD10_col_name='ICD10', SNOMED_col_name='SNOMED', OPCS4_col_name='OPCS4'):
    '''
    This function reads the custom codelists original file, keeping only the useful columns
    '''
    useful_cols = ['phenotype', 'code', 'term']

    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile, fieldnames=useful_cols)
        rows = list(reader)

        def process_codelist(codelist_type):
            '''
            This function splits the original file into the three categories (SNOMED, OPCS4, and ICD10) with a proper format
            '''
            filtered_rows = [row for row in rows if row[code_col_name] == codelist_type]
            header = ['code', 'term']
            output_file = os.path.join(output_directory, f'{output_prefix}_{codelist_type}.csv')
            
            with open(output_file, 'w', newline='') as csvfile_out:
                writer = csv.DictWriter(csvfile_out, fieldnames=header)
                writer.writeheader()
                writer.writerows([{'code': row['code'], 'term': row['phenotype']} for row in filtered_rows])

        process_codelist(ICD10_col_name)
        process_codelist(SNOMED_col_name)
        process_codelist(OPCS4_col_name)
