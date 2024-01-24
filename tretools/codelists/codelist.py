"""
This file contains the codelist class.
"""
from __future__ import annotations
import csv
import os
from typing import Optional, List, Dict
import re
import tempfile

from tretools.codelists.codelist_types import CodelistType
from tretools.codelists.errors import InvalidSNOMEDCodeError, RepeatedCodeError, InvalidDataShapeError, InvalidICD10CodeError, InvalidOPCSCodesError, InvalidProcessingRequest

class Codelist:
    def __init__(self, path: str,
                 codelist_type: CodelistType,
                 code_column: str = "code",
                 term_column: str = "term",
                 add_x_codes: bool = False,
                 icd10_3_digit_only: bool = False) -> None:
        self.codelist_type = codelist_type
        self.code_column = code_column
        self.term_column = term_column
        self.codes = set()
        self.path = path
        
        # Load the data from the path
        if self.codelist_type == "ICD10":
            if add_x_codes or icd10_3_digit_only:
                self.data = self._load_codelist(path, add_x_codes=add_x_codes, icd10_3_digit_only=icd10_3_digit_only)
            else:
                self.data = self._load_codelist(path)
        else:
            self.data = self._load_codelist(path)


    def _load_codelist(self, path, add_x_codes: bool = False, icd10_3_digit_only: bool = False) -> List[Dict[str, str]]:
        """
        Loads the codelist from the path.

        Args:
            path (str): The path to the codelist.

        Returns:
            list: The codelist as a list of dictionaries.
        """
        if not self._check_path(path):
            raise FileNotFoundError(f"Could not find codelist at {path}")

        if add_x_codes and icd10_3_digit_only:
            raise InvalidProcessingRequest("Cannot add X codes and truncate ICD10 codes to 3 digits at the same time.")

        data = []
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                
                # Check for correct data shape
                if len(row) != 2:
                    raise InvalidDataShapeError(f"Invalid data shape. Expected 2 columns, but got {len(row)} columns.")

                # Validate the codelist. Raises errors if invalid.
                self._validate_codelist(row)

                # Truncating ICD10 codes to contain the first 3 digits only if icd10_3_digit_only is True
                if icd10_3_digit_only:
                    row = self._icd10_3_digit_only(row)

                # Add the row to the data
                data.append(row)

                # Add the X codes for ICD-10 codes that do not have an X code
                if add_x_codes and self.codelist_type == "ICD10":
                    new_row = self._add_X_codes_for_ICD(row)
                    if new_row is not None:
                        data.append(new_row)
                        self.codes.add(new_row[self.code_column])
        
        return data

    def _validate_codelist(self, row: Dict[str, str]):
        """
        Validates the codelist.

        Args:
            row (Dict[str, str]): A dictionary containing the data for the current row.

        Raises:
            InvalidSNOMEDCodeError: If the SNOMED code is invalid.
            RepeatedCodeError: If a code is repeated.
            RepeatedTermError: If a term is repeated.
        """
        code = row.get(self.code_column, "")
        term = row.get(self.term_column, "")

        # validate the codelist against the expected format depending on the codelist type
        validation_methods = {
            "SNOMED": (self.validate_snomed_code, InvalidSNOMEDCodeError),
            "ICD10": (self.validate_icd10_code, InvalidICD10CodeError),
            "OPCS": (self.validate_opcs_code, InvalidOPCSCodesError)
        }
        validate_method, exception_type = validation_methods.get(self.codelist_type, (None, ValueError))
        if validate_method:
            if not validate_method(code):
                raise exception_type(f"Invalid {self.codelist_type} code: {code} for term: {term}")
        else:
            raise ValueError(f"Invalid codelist type: {self.codelist_type}")

        # Check for repeated codes. We do not check for repeated terms as this occurs when we have both
        # an ICD code with and without an X that mean the same thing. i.e. A01 and A01X are the same. 
        if code in self.codes:
            raise RepeatedCodeError(f"Repeated code found: {code}")
        else:
            self.codes.add(code)

    @staticmethod
    def _check_path(path: str) -> bool:
        """
        Checks the path to the codelist exists.

        Args:
            path (str): The path to the codelist.

        Returns:
            bool: True if the path exists, False otherwise.
        """
        return os.path.exists(path)

    @staticmethod
    def validate_snomed_code(code: str, min_length: int = 6, max_length: int = 18) -> bool:
        """
        Validate the form of a SNOMED CT code.
        
        Args:
            code (str): The code to validate.
            min_length (int, optional): The minimum length of the code. Defaults to 6.
            max_length (int, optional): The maximum length of the code. Defaults to 18.
        
        Returns:
            bool: True if the code is valid, False otherwise.
        """
        if not code.isdigit():
            return False
        if not min_length <= len(code) <= max_length:
            return False
        return True

    @staticmethod
    def validate_icd10_code(code: str) -> bool:
        """
        Validate the form of an ICD-10 code.

        The rules are:
        - The code must be 7 characters or less
        - The first character must be a letter
        - The second and third characters must be numbers
        - The fourth character must be a dot, or a number or X
        - If the fourth character is a dot, there must be at least 1 number after the dot
        - If the fourth character is a X, there are no further characters
        - The fifth to seventh characters must be numbers if present 

        Args:
            code (str): The code to validate.

        Returns:
            bool: True if the code is valid, False otherwise.
        """
        # Regex pattern to match the ICD-10 formats
        pattern = re.compile(r"^[A-Z]\d{2}(X|(\.\d{1,3})?|\d{1,4})?$")

        if len(code) > 7:
            return False

        if pattern.match(code):
            return True

        return False

    @staticmethod
    def validate_opcs_code(code: str) -> bool:
        """
        Validates the form of an OPCS code.

        Rules:
        - The code must be 3-5 characters long
        - The first character must be a letter
        - The second and third characters must be numbers
        - If there is a fourth character and it is a dot, there must be a number after the dot
        - The fifth character, if present, is a number
        """
        pattern = re.compile(r"^[A-Z]\d{2}(\.\d{1,2}|\d{1,2})?$")
        if len(code) > 5:
            return False

        if pattern.match(code):
            return True

        return False

    def _add_X_codes_for_ICD(self, row: Dict[str, str]) -> Optional[Dict[str, str]]:
        """
        Add the X code for ICD-10 codes that do not have an X code
        and appends the X code to the end of the codelist with the 
        correct term.

        E.g. if A01 is in the codelist, then A01X is added to the codelist

        Args:
            row (Dict[str, str]): The row data containing the code and term.

        Returns:
            Optional[Dict[str, str]]: A new row with the X code, or None if the row already contains an X code.
        """
        code = row.get(self.code_column, "")

        # If the code is already an X code or doesn't match the pattern, don't add another
        if 'X' in code or not re.match(r"^[A-Z]\d{2}$", code):
            return None

        # Create the new row with the X code
        new_code = f"{code}X"
        new_row = {
            self.code_column: new_code,
            self.term_column: row[self.term_column]
        }

        return new_row
    
    @classmethod
    def map_snomed_to_icd10(cls, codelist: Codelist, mapping_file: str, icd10_3_digit_only: bool = False) -> Codelist:
        """
        Maps SNOMED codes to their corresponding ICD10

        Args:
            mapping_file (str): mapping file path
        """
        # Raise error if the codelist is not SNOMED

        # Check path to mapping file exists

        # Decide whether to truncate ICD10 codes to 3 digits
        if icd10_3_digit_only:
            col_map = "ICD10_3digit"
        else:
            col_map = "mapTarget"

        # Load the mapping file into a dictionary
        with open(mapping_file, "r") as f:
            reader = csv.DictReader(f)
            mapping = {row["conceptId"]: row[col_map] for row in reader}

        # Iterate through the data and map the SNOMED codes to ICD10 codes
        new_data = {}
        for row in codelist.data:
            # If the SNOMED code is in the mapping file, add the ICD10 code to the new data
            if row["code"] in mapping:
                new_data[mapping[row["code"]]] = f"Mapped from SNOMED Code: {row['code']}, Term: {row['term']}"

        # write the new data to a temporary file so it can be loaded into a new codelist object
        # TODO: In the future, we should be able to load the data directly into a new codelist object
        # without having to write to a temporary file first
        temp_file = tempfile.NamedTemporaryFile(mode="w", delete=False)
        writer = csv.DictWriter(temp_file, fieldnames=["code", "term"])
        writer.writeheader()
        for code, term in new_data.items():
            writer.writerow({"code": code, "term": term})
        temp_file.close()

        # # make a new codelist object with the new data
        new_codelist = Codelist(temp_file.name, "ICD10")
        return new_codelist


    def _icd10_3_digit_only(self, row: Dict[str, str]) -> [Dict[str, str]]:
        """
        Truncating ICD10 codes to contain the first 3 digits only

        Args:
            row (Dict[str, str]): The row data containing the code and term.

        Returns:
            Dict[str, str]: A new row with the truncated ICD10 code.
        """
        if len(row[self.code_column]) > 3:
            row[self.code_column] = row[self.code_column][:3]
        return row
