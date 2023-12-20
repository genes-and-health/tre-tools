import pytest
import os
import csv
from tretools.utility.custom_phen_conversion import process_custom_codelist, CustomPhenotypeError, process_all_codelists

# For making a temporary CSV file for testing
def create_temp_csv(data, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        header = ['code', 'term', 'phenotype']
        writer = csv.DictWriter(csvfile, fieldnames=header)
        writer.writeheader()
        writer.writerows(data)

@pytest.fixture
def input_data():
    return [
        {'term': 'ICD10', 'code': 'A01.123', 'phenotype': 'Disease A - 1'},
        {'term': 'SNOMED', 'code': '100000001', 'phenotype': 'Disease A - 1'},
        {'term': 'SNOMED', 'code': '100000002', 'phenotype': 'Disease A - 2'},
        {'term': 'ICD10', 'code': 'A01X', 'phenotype': 'Disease A - 1'},
        {'term': 'ICD10', 'code': 'A011', 'phenotype': 'Disease A - 1'},
        {'term': 'OPCS4', 'code': 'K123', 'phenotype': 'Procedure'},
    ]

def test_process_all_codelists(input_data, tmp_path):
    config = {
        'code_col_name': 'term',
        'ICD10_col_name': 'ICD10',
        'SNOMED_col_name': 'SNOMED',
        'OPCS4_col_name': 'OPCS4',
    }
    output_directory = str(tmp_path)

    # Create a temporary CSV file of the inputs (similar to the original CSV file)
    input_file_path = os.path.join(output_directory, 'input_file.csv')
    create_temp_csv(input_data, input_file_path)

    # Print the contents of the original customs
    # with open(input_file_path, 'r') as infile:
    #     print("Contents of input_file.csv:")
    #     print(infile.read())

    # Only for testing purpose
    generated_data = process_all_codelists(input_data, output_directory, config)


def test_process_custom_codelist(input_data, tmp_path):
    config = {
        'code_col_name': 'term',
        'ICD10_col_name': 'ICD10',
        'SNOMED_col_name': 'SNOMED',
        'OPCS4_col_name': 'OPCS4',
    }
    output_directory = str(tmp_path)

    # Temporary CSV file
    create_temp_csv(input_data, os.path.join(output_directory, 'input_file.csv'))

    # Tesing process_custom_codelist function
    process_custom_codelist(os.path.join(output_directory, 'input_file.csv'), output_directory, config)

    # Verifying the generated SNOMED-ICD10-OPCS files
    expected_content = {
        "customs_ICD10.csv": """code,term
A01.123,Disease A - 1
A01X,Disease A - 1
A011,Disease A - 1
        """,
        "customs_SNOMED.csv": """code,term
100000001,Disease A - 1
100000002,Disease A - 2
            """,
            "customs_OPCS4.csv": """code,term
K123,Procedure
            """
    }

    for file_name in expected_content.keys():
        file_path = os.path.join(output_directory, file_name)
        assert os.path.exists(file_path)

        with open(file_path, 'r') as csvfile:
            content = csvfile.read()
            # Getting the corresponding expected content dynamically
            expected_content_str = expected_content[file_name]
            # print(content.strip())

            assert content.strip() == expected_content_str.strip()



    


def test_process_custom_codelist_with_error(input_data, tmp_path):
    config = {
        'code_col_name': 'term',
        'ICD10_col_name': 'ICD11',  # Intentionally wrong column name ICD11 to raise an error
        'SNOMED_col_name': 'SNOMED',
        'OPCS4_col_name': 'OPCS4',
    }
    output_directory = str(tmp_path)

    # Creating a temporary CSV file for testing
    create_temp_csv(input_data, os.path.join(output_directory, 'input_file.csv'))

    # Testing the process_custom_codelist function with an error
    with pytest.raises(CustomPhenotypeError):
        process_custom_codelist(os.path.join(output_directory, 'input_file.csv'), output_directory, config)

