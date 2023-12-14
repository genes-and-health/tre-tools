import os
import csv

def process_custom_codelist(input_file, output_directory, output_prefix, code_col_name='term', ICD10_col_name='ICD10', SNOMED_col_name='SNOMED', OPCS4_col_name='OPCS4'):
    '''
    The main function reads the custom codelists original file
    '''
    # useful_cols = ['phenotype', 'code', 'term']

    with open(input_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
        
        def process_all_codelists():
            '''
            This nested function formats all three codelists (SNOMED, OPCS4, and ICD10) to be used as inputs custom package
            '''
            nonlocal rows  # Access the outer 'rows' variable

            total_generated_records = 0  # Variable to track the total length of the generated CSV files

            for codelist_type in [ICD10_col_name, SNOMED_col_name, OPCS4_col_name]:
                filtered_rows = [row for row in rows if row[code_col_name] == codelist_type]
                total_generated_records += len(filtered_rows)

            # Check if the sum of counts from three separate files (SNOMED, ICD10, OPCS4) is equal to the number of rows in the original file
            original_length = len(rows) 

            if total_generated_records == original_length:

                # If the lengths are equal, write the CSV files
                for codelist_type in [ICD10_col_name, SNOMED_col_name, OPCS4_col_name]:
                    filtered_rows = [row for row in rows if row[code_col_name] == codelist_type]
                    header = ['code', 'term']
                    output_file = os.path.join(output_directory, f'{output_prefix}_{codelist_type}.csv')

                    with open(output_file, 'w', newline='') as csvfile_out:
                        writer = csv.DictWriter(csvfile_out, fieldnames=header)
                        writer.writeheader()
                        writer.writerows([{'code': row['code'], 'term': row['phenotype']} for row in filtered_rows])
                print(f"Separate files for SNOMED, ICD10, and OPCS4 are generated")
            else:
                assert False, f"Error: Original custom phenotype file has {original_length} records " \
                      f"while the generated ICD10, SNOMED, and OPCS4 files have {total_generated_records} records in total. This may indicate that there is a codelist type in the original.\
                          file that is not any of ICD10, SNOMED, or OPCS4. Alternatively, typos should be checked"

        process_all_codelists()

