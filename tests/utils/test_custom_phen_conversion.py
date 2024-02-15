import pytest
import os
import csv
import shutil


from tretools.utility.custom_phen_conversion import (process_custom_codelist,
                                                     CustomPhenotypeError,
                                                     process_all_codelists,
                                                     process_codelists_to_reference_files)


CONFIG = {
        'code_col_name': 'term',
        'ICD10_col_name': 'ICD10',
        'SNOMED_col_name': 'SNOMED',
        'OPCS4_col_name': 'OPCS4',
    }

def test_process_all_codelists():
    output_directory = 'tests/utils'

    # load the input data from "tests/utils/input_file.csv"
    input_file_path = 'tests/utils/input_file.csv'
    with open(input_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        input_data = list(reader)

    # Testing process_all_codelists function. this will create separate CSV files for each codelist
    process_all_codelists(input_data, output_directory, CONFIG)

    # Verify that the separate CSV files are created
    expected_files = ['customs_ICD10.csv', 'customs_SNOMED.csv', 'customs_OPCS4.csv']
    for file in expected_files:
        file_path = os.path.join(output_directory, file)
        assert os.path.exists(file_path)

    # Verifying the content of the separate CSV files.
    # if we look at the input data, we can see that there are two SNOMED codes
    # 100000001 and 100000002, representing two different diseases
    snomed_file = os.path.join(output_directory, 'customs_SNOMED.csv')
    with open(snomed_file, 'r') as test_file:
        content = test_file.readlines()  # Read lines into a list
        data = [line.strip().split(',') for line in content] # Splitting the lines into a list of lists
        assert data[0] == ['code', 'term']

        # The order of the rows is not guaranteed, so we need to check both possibilities
        assert data[1] == ['100000001', 'Disease A - 1'] or data[1] == ['100000002', 'Disease A - 2']


    opcs4_file = os.path.join(output_directory, 'customs_OPCS4.csv')
    with open(opcs4_file, 'r') as test_file:
        content = test_file.readlines()  # Read lines into a list
        data = [line.strip().split(',') for line in content] # Splitting the lines into a list of lists
        assert data[0] == ['code', 'term']
        assert data[1] == ['K123', 'Procedure']

    icd10_file = os.path.join(output_directory, 'customs_ICD10.csv')
    with open(icd10_file, 'r') as test_file:
        content = test_file.readlines()  # Read lines into a list
        data = [line.strip().split(',') for line in content] # Splitting the lines into a list of lists
        assert data[0] == ['code', 'term']
        assert data[1] == ['A01.123', 'Disease A - 1']
        assert data[2] == ['A01X', 'Disease A - 1']
        assert data[3] == ['A011', 'Disease A - 1']

    # clean up
    os.remove(snomed_file)
    os.remove(opcs4_file)
    os.remove(icd10_file)


def test_process_custom_codelist_with_error():
    wrong_config = {
        'code_col_name': 'term',
        'ICD10_col_name': 'ICD11',  # Intentionally wrong column name ICD11 to raise an error
        'SNOMED_col_name': 'SNOMED',
        'OPCS4_col_name': 'OPCS4',
    }

    output_directory = 'tests/utils'

    # load the input data from "tests/utils/input_file.csv"
    input_file_path = 'tests/utils/input_file.csv'
    with open(input_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        input_data = list(reader)

    # Testing the process_custom_codelist function with an error
    with pytest.raises(CustomPhenotypeError) as e:
        process_all_codelists(input_data, output_directory, wrong_config)

    assert ("Original custom phenotype file has 6 records, while the generated ICD10, SNOMED, and OPCS4 files have 3 records in total. This may indicate that there is a codelist type in the original file that is not any of ICD10, SNOMED, or OPCS4."
            " Alternatively, typos should be checked") in str(e.value)


def test_process_custom_codelist():
    output_directory = 'tests/utils'

    # load the input data from "tests/utils/input_file.csv"
    input_file_path = 'tests/utils/input_file.csv'

    # Testing process_custom_codelist function. this will create separate CSV files for each codelist
    process_custom_codelist(input_file_path, output_directory, CONFIG)

    # Verify that the separate CSV files are created
    expected_files = ['customs_ICD10.csv', 'customs_SNOMED.csv', 'customs_OPCS4.csv']
    for file in expected_files:
        file_path = os.path.join(output_directory, file)
        assert os.path.exists(file_path)

    # Verifying the content of the separate CSV files.
    # if we look at the input data, we can see that there are two SNOMED codes
    # 100000001 and 100000002, representing two different diseases
    snomed_file = os.path.join(output_directory, 'customs_SNOMED.csv')
    with open(snomed_file, 'r') as test_file:
        content = test_file.readlines()  # Read lines into a list
        data = [line.strip().split(',') for line in content] # Splitting the lines into a list of lists
        assert data[0] == ['code', 'term']
        assert data[1] == ['100000001', 'Disease A - 1']
        assert data[2] == ['100000002', 'Disease A - 2']

    opcs4_file = os.path.join(output_directory, 'customs_OPCS4.csv')
    with open(opcs4_file, 'r') as test_file:
        content = test_file.readlines()  # Read lines into a list
        data = [line.strip().split(',') for line in content] # Splitting the lines into a list of lists
        assert data[0] == ['code', 'term']
        assert data[1] == ['K123', 'Procedure']

    icd10_file = os.path.join(output_directory, 'customs_ICD10.csv')
    # clean up
    os.remove(snomed_file)
    os.remove(opcs4_file)
    os.remove(icd10_file)

def test_process_codelists_to_reference_files():
    input_file = 'tests/utils/snomed.csv'
    output_directory = 'tests/utils'
    reference_file_path = 'tests/utils/reference_file.csv'
    copied_reference_file_path = 'tests/utils/reference_file_copy.csv'

    # copy the reference file as we will be modifying it so best
    # to keep the original, and use the copy for testing
    shutil.copy(reference_file_path, copied_reference_file_path)

    dataset_config = {
        'dataset_type': 'primary_care',
        'dataset_name': 'test_dataset',
        'dataset_path': 'tests/utils/test_dataset.csv',  # This is a dummy path
        'coding_system': 'SNOMED'
    }

    codelist_config = {
        'codelist_type': 'SNOMED',
        'codelist_name': 'test_codelist',
    }

    # Testing process_codelists_to_reference_files function. this will create a reference file
    process_codelists_to_reference_files(input_file, output_directory, copied_reference_file_path, dataset_config, codelist_config)

    # Verify that the refernce file has the correct entries
    with open(copied_reference_file_path, 'r') as test_file:
        content = test_file.readlines()  # Read lines into a list
        data = [line.strip().split(',') for line in content] # Splitting the lines into a list of lists

        # The order of the rows is not guaranteed, so we need to check both possibilities
        assert data[1] == ['Disease_A', 'test_dataset', 'tests/utils/test_dataset.csv', 'primary_care', 'test_codelist_Disease_A', 'tests/utils/Disease_A.csv', 'SNOMED', 'no'] or data[1] == ['Disease_B', 'test_dataset', 'tests/utils/test_dataset.csv', 'primary_care', 'test_codelist_Disease_B', 'tests/utils/Disease_B.csv', 'SNOMED', 'no']

    # Now we test that the separated csv files are also created
    # assert the content of the separated csv files
    disease_a_file = 'tests/utils/Disease_A.csv'
    with open(disease_a_file, 'r') as test_file:
        content = test_file.readlines()  # Read lines into a list
        data = [line.strip().split(',') for line in content] # Splitting the lines into a list of lists
        assert data[0] == ['code', 'term']
        assert data[1] == ['100000001', 'Disease_A']

    disease_b_file = 'tests/utils/Disease_B.csv'

    # clean up
    os.remove(disease_a_file)
    os.remove(disease_b_file)
    os.remove(copied_reference_file_path)

