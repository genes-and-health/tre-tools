import pytest

from tretools.codelists.codelist import Codelist
from tretools.codelists.errors import InvalidSNOMEDCodeError, InvalidProcessingRequest, InvalidICD10CodeError, RepeatedCodeError, InvalidDataShapeError

# Path to the codelists
GOOD_SNOMED_PATH = "tests/codelists/test_data/good_snomed_codelist.csv"
GOOD_ICD10_PATH = "tests/codelists/test_data/good_icd_codelist.csv"
GOOD_ICD10_to_be_3digit_PATH = "tests/codelists/test_data/good_icd_codelist_to_be3digit.csv"
GOOD_SNOMED_to_be_ICD10_PATH = "tests/codelists/test_data/good_SNOMEDS_to_be_ICD10.csv"
REPEATED_SNOMED_to_be_ICD10_PATH= "tests/codelists/test_data/repeats_SNOMEDS_to_be_ICD10.csv"

# Correct data for the codelists
CORRECT_DATA = [{'code': '100000001', 'term': 'Disease A - 1'}, {'code': '100000002', 'term': 'Disease A - 2'}]
CORRECT_ICD_DATA_WITH_X = [{'code': 'A01', 'term': 'Disease A - 1'}, {'code': 'A01X', 'term': 'Disease A - 1'}, {'code': 'A02', 'term': 'Disease A - 2'}, {'code': 'A02X', 'term': 'Disease A - 2'}]
CORRECT_ICD_DATA_WITHOUT_X = [{'code': 'A01', 'term': 'Disease A - 1'}, {'code': 'A02', 'term': 'Disease A - 2'}]
CORRECT_3DigitICD10_DATA = [{'code': 'A01', 'term': 'Disease A - 1'},{'code': 'A02', 'term': 'Disease A - 2'},{'code': 'A02', 'term': 'Disease A - 3'}]


def test_good_codelist():
    data = Codelist(GOOD_SNOMED_PATH, "SNOMED")
    assert data.codelist_type == "SNOMED"
    assert data.data == CORRECT_DATA    


def test_bad_path_codelist():
    with pytest.raises(FileNotFoundError) as e:
        data = Codelist("BAD_PATH", "SNOMED")
    
    assert "Could not find codelist at BAD_PATH" in str(e.value)


def test_invalid_codelist_type():
    with pytest.raises(ValueError) as e:
        data = Codelist(GOOD_SNOMED_PATH, "INVALID_CODELIST_TYPE")

    assert "Invalid codelist type: INVALID_CODELIST_TYPE" in str(e.value)


def test_bad_snomed_validate_codelist():
    with pytest.raises(InvalidSNOMEDCodeError) as e:
        data = Codelist(GOOD_ICD10_PATH, "SNOMED")
    
    assert "Invalid SNOMED code: A01 for term: Disease A - 1" in str(e.value)


def test_bad_snomed_wrong_length():
    # too short < 6
    validation_check = Codelist.validate_snomed_code("10001")
    assert validation_check == False

    # too long > 18 
    validation_check = Codelist.validate_snomed_code("1000000000000000001")
    assert validation_check == False

def test_bad_icd10_validate_codelist_wrong_type():
    with pytest.raises(InvalidICD10CodeError) as e:
        Codelist(GOOD_SNOMED_PATH, "ICD10")
    
    assert "Invalid ICD10 code: 100000001 for term: Disease A - 1" in str(e.value)

def test_bad_icd10_wrong_length():
    validation_check = Codelist.validate_icd10_code("A1")
    assert validation_check == False

def test_bad_icd10_wrong_format():
    # First letter is not a letter
    validation_check = Codelist.validate_icd10_code("001")
    assert validation_check == False

    # Dot is in the wrong place
    validation_check = Codelist.validate_icd10_code("A010.1")
    assert validation_check == False

    # Fourth character is either a number, an X or a dot
    validation_check = Codelist.validate_icd10_code("A01A")
    assert validation_check == False

    validation_check = Codelist.validate_icd10_code("A01X")
    assert validation_check == True

    validation_check = Codelist.validate_icd10_code("A01X1")
    assert validation_check == False

    validation_check = Codelist.validate_icd10_code("A01.")
    assert validation_check == False

    validation_check = Codelist.validate_icd10_code("A01.1")
    assert validation_check == True

    validation_check = Codelist.validate_icd10_code("A011111")
    assert validation_check == True


def test_bad_icd10_incorrect_format_in_csv():
    with pytest.raises(InvalidICD10CodeError) as e:
        data = Codelist("tests/codelists/test_data/bad_icd_codelist.csv", "ICD10")
    
    assert "Invalid ICD10 code: A012.1 for term: Disease A - 1" in str(e.value)


def test_bad_opcs_wrong_format():
    # First letter is not a letter
    validation_check = Codelist.validate_opcs_code("001")
    assert validation_check == False

    # Dot is in the wrong place
    validation_check = Codelist.validate_opcs_code("A010.1")
    assert validation_check == False

    # Fourth character is a dot if present
    validation_check = Codelist.validate_opcs_code("A01A")
    assert validation_check == False

    # Do not need a dot
    validation_check = Codelist.validate_opcs_code("A01")
    assert validation_check == True

    # Dot without following number
    validation_check = Codelist.validate_opcs_code("A01.")
    assert validation_check == False

    # Proper format with dot and a following number
    validation_check = Codelist.validate_opcs_code("A01.1")
    assert validation_check == True

    # Incorrect format with a letter after the dot
    validation_check = Codelist.validate_opcs_code("A01.A")
    assert validation_check == False

    # Incorrect format with a X as the 4th character like in ICD10
    validation_check = Codelist.validate_opcs_code("A01X")
    assert validation_check == False

    # Format not allowed - too many characters after the dot
    validation_check = Codelist.validate_opcs_code("A01.21")
    assert validation_check == False

def test_check_x_code_added_to_icd10():
    data = Codelist(GOOD_ICD10_PATH, "ICD10", add_x_codes=True)
    assert data.data == CORRECT_ICD_DATA_WITH_X

def test_check_x_code_not_added_to_icd10():
    data = Codelist(GOOD_ICD10_PATH, "ICD10", add_x_codes=False)
    assert data.data == CORRECT_ICD_DATA_WITHOUT_X

def test_if_x_code_conditions_not_met():
    data = Codelist("tests/codelists/test_data/good_icd_codelist_with_x.csv", "ICD10", add_x_codes=True)
    expected_result = [{'code': 'A01X', 'term': 'Disease A - 1'}, {'code': 'A02.1', 'term': 'Disease A - 2'}]
    assert data.data == expected_result

def test_repeated_code_codelist():
    with pytest.raises(RepeatedCodeError) as e:
        data = Codelist("tests/codelists/test_data/repeated_code_snomed_codelist.csv", "SNOMED")
    
    assert "Repeated code found: 100000002" in str(e.value)

def test_data_shape_codelist():
    with pytest.raises(InvalidDataShapeError) as e:
        data = Codelist("tests/codelists/test_data/extra_columns_snomed_codelist.csv", "SNOMED")
    
    assert "Invalid data shape. Expected 2 columns, but got 4 columns." in str(e.value)

def test_ICD10_3Digit():
    # This data file contains various definitions of ICD for the same disease (A01)
    # for example, A01, A01X, A01.1 etc.
    data = Codelist(GOOD_ICD10_to_be_3digit_PATH, "ICD10", icd10_3_digit_only=True)

    # We are asserting each of these combinations of ICD codes are the same - they are all A01
    for row in data.data:
        assert row == {'code': 'A01', 'term': 'Disease A - 1'}


def test_ICD10_3Digit_with_X():
    # Should not be able to have X codes when icd10_3_digit_only is True
    # as truncating the code to 3 digits will remove the X
    with pytest.raises(InvalidProcessingRequest) as e:
        data = Codelist(GOOD_ICD10_PATH, "ICD10", icd10_3_digit_only=True, add_x_codes=True)

    assert "Cannot add X codes and truncate ICD10 codes to 3 digits at the same time." in str(e.value)



def test_SNOMED_to_ICD10_mapping():
    mapping_file = 'tests/codelists/test_data/snomed_to_icd_map.csv'
    data = Codelist(GOOD_SNOMED_to_be_ICD10_PATH, "SNOMED")
    mapped_data = data.map_snomed_to_icd10(data, mapping_file)

    assert mapped_data.codelist_type == "ICD10"
    assert len(mapped_data.data) == 4

    print(mapped_data.data)
    assert mapped_data.data[0] == {'code': 'A011', 'term': 'Mapped from SNOMED Code: 100000001, Term: Disease A - 1'}
    assert mapped_data.data[1] == {'code': 'A02.1', 'term': 'Mapped from SNOMED Code: 100000002, Term: Disease A - 2'}
    assert mapped_data.data[2] == {'code': 'A03X', 'term': 'Mapped from SNOMED Code: 100000003, Term: Disease A - 3'}
    assert mapped_data.data[3] == {'code': 'B0111', 'term': 'Mapped from SNOMED Code: 200000001, Term: Disease B - 1'}

def test_SNOMED_to_ICD10_mapping_with_3_digit_truncating():
    mapping_file = 'tests/codelists/test_data/snomed_to_icd_map.csv'
    data = Codelist(GOOD_SNOMED_to_be_ICD10_PATH, "SNOMED")
    mapped_data = data.map_snomed_to_icd10(data, mapping_file, icd10_3_digit_only=True)

    assert mapped_data.codelist_type == "ICD10"
    assert len(mapped_data.data) == 4

    assert mapped_data.data[0] == {'code': 'A01', 'term': 'Mapped from SNOMED Code: 100000001, Term: Disease A - 1'}
    assert mapped_data.data[1] == {'code': 'A02', 'term': 'Mapped from SNOMED Code: 100000002, Term: Disease A - 2'}
    assert mapped_data.data[2] == {'code': 'A03', 'term': 'Mapped from SNOMED Code: 100000003, Term: Disease A - 3'}
    assert mapped_data.data[3] == {'code': 'B01', 'term': 'Mapped from SNOMED Code: 200000001, Term: Disease B - 1'}


def test_SNOMED_to_ICD10_map_with_repeats():
    mapping_file = 'tests/codelists/test_data/snomed_to_icd_map.csv'
    data = Codelist(REPEATED_SNOMED_to_be_ICD10_PATH, "SNOMED")
    mapped_data = data.map_snomed_to_icd10(data, mapping_file)

    assert mapped_data.codelist_type == "ICD10"

    # Should only have 2 rows of data, as the first two rows
    # with different snomed codes are mapped to the same ICD10 code
    assert len(mapped_data.data) == 2

    assert mapped_data.data[0] == {'code': 'B02.1', 'term': 'Mapped from SNOMED Code: 200000012, Term: Disease B - 1'}
    assert mapped_data.data[1] == {'code': 'B02.2', 'term': 'Mapped from SNOMED Code: 200000022, Term: Disease B - 2'}

def test_SNOMED_to_ICD10_map_with_repeats_3_digits():
    mapping_file = 'tests/codelists/test_data/snomed_to_icd_map.csv'
    data = Codelist(REPEATED_SNOMED_to_be_ICD10_PATH, "SNOMED")
    mapped_data = data.map_snomed_to_icd10(data, mapping_file, icd10_3_digit_only=True)

    assert mapped_data.codelist_type == "ICD10"

    # Should only have 1 row of data, as all the snomed codes are mapped to the same ICD10 code
    assert len(mapped_data.data) == 1

    assert mapped_data.data[0] == {'code': 'B02', 'term': 'Mapped from SNOMED Code: 200000022, Term: Disease B - 2'}