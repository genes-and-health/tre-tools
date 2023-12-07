import pytest

from tretools.codelists.codelist import Codelist
from tretools.codelists.errors import InvalidSNOMEDCodeError, InvalidOPCSCodesError, InvalidICD10CodeError, RepeatedCodeError, InvalidDataShapeError
from tretools.codelists.codelist_types import CodelistType


GOOD_SNOMED_PATH = "tests/codelists/test_data/good_snomed_codelist.csv"
GOOD_ICD10_PATH = "tests/codelists/test_data/good_icd_codelist.csv"
CORRECT_DATA = [{'code': '100000001', 'term': 'Disease A - 1'}, {'code': '100000002', 'term': 'Disease A - 2'}]
CORRECT_ICD_DATA_WITH_X = [{'code': 'A01', 'term': 'Disease A - 1'}, {'code': 'A01X', 'term': 'Disease A - 1'}, {'code': 'A02', 'term': 'Disease A - 2'}, {'code': 'A02X', 'term': 'Disease A - 2'}]
CORRECT_ICD_DATA_WITHOUT_X = [{'code': 'A01', 'term': 'Disease A - 1'}, {'code': 'A02', 'term': 'Disease A - 2'}]


def test_good_codelist():
    data = Codelist(GOOD_SNOMED_PATH, CodelistType.SNOMED.value)
    assert data.codelist_type == "SNOMED"
    assert data.data == CORRECT_DATA    


def test_bad_path_codelist():
    with pytest.raises(FileNotFoundError) as e:
        data = Codelist("BAD_PATH", CodelistType.SNOMED.value)
    
    assert "Could not find codelist at BAD_PATH" in str(e.value)


def test_invalid_codelist_type():
    with pytest.raises(ValueError) as e:
        data = Codelist(GOOD_SNOMED_PATH, "INVALID_CODELIST_TYPE")

    assert "Invalid codelist type: INVALID_CODELIST_TYPE" in str(e.value)


def test_bad_snomed_validate_codelist():
    with pytest.raises(InvalidSNOMEDCodeError) as e:
        data = Codelist(GOOD_ICD10_PATH, CodelistType.SNOMED.value)
    
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
        Codelist(GOOD_SNOMED_PATH, CodelistType.ICD10.value)
    
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
        data = Codelist("tests/codelists/test_data/bad_icd_codelist.csv", CodelistType.ICD10.value)
    
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
    data = Codelist(GOOD_ICD10_PATH, CodelistType.ICD10.value, add_x_codes=True)
    assert data.data == CORRECT_ICD_DATA_WITH_X

def test_check_x_code_not_added_to_icd10():
    data = Codelist(GOOD_ICD10_PATH, CodelistType.ICD10.value, add_x_codes=False)
    assert data.data == CORRECT_ICD_DATA_WITHOUT_X

def test_if_x_code_conditions_not_met():
    data = Codelist("tests/codelists/test_data/good_icd_codelist_with_x.csv", CodelistType.ICD10.value, add_x_codes=True)
    expected_result = [{'code': 'A01X', 'term': 'Disease A - 1'}, {'code': 'A02.1', 'term': 'Disease A - 2'}]
    assert data.data == expected_result

def test_repeated_code_codelist():
    with pytest.raises(RepeatedCodeError) as e:
        data = Codelist("tests/codelists/test_data/repeated_code_snomed_codelist.csv", CodelistType.SNOMED.value)
    
    assert "Repeated code found: 100000002" in str(e.value)

def test_data_shape_codelist():
    with pytest.raises(InvalidDataShapeError) as e:
        data = Codelist("tests/codelists/test_data/extra_columns_snomed_codelist.csv", CodelistType.SNOMED.value)
    
    assert "Invalid data shape. Expected 2 columns, but got 4 columns." in str(e.value)