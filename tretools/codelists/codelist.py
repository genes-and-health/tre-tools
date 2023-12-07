"""
This file contains the codelist class.
"""
import csv
import os
from typing import Optional, List, Dict
import re
import polars as pl

from tretools.codelists.codelist_types import CodelistType
from tretools.codelists.errors import InvalidSNOMEDCodeError, RepeatedCodeError, InvalidDataShapeError, InvalidICD10CodeError, InvalidOPCSCodesError

class Codelist:
    def __init__(self, path: str,
                 codelist_type: CodelistType,
                 code_column: str = "code",
                 term_column: str = "term",
                 snomed_to_icd10_path: str = '',
                 add_x_codes: bool = False,
                 snomed_to_icd10: bool = False,
                 ICD10_3Digit: bool = False) -> None:
        self.codelist_type = codelist_type
        self.code_column = code_column
        self.term_column = term_column
        self.codes = set()
        
        if add_x_codes and self.codelist_type == "ICD10":
            self.data = self._load_codelist(path, add_x_codes)
        else:
            self.data = self._load_codelist(path)
        if snomed_to_icd10:
            self.data = self._SNOMED_to_ICD10(snomed_to_icd10_path)
        if ICD10_3Digit:
            self.data = self._ICD10_3Digit()

    def _load_codelist(self, path, add_x_codes: bool = False) -> List[Dict[str, str]]:
        """
        Loads the codelist from the path.

        Args:
            path (str): The path to the codelist.

        Returns:
            list: The codelist as a list of dictionaries.
        """
        if not self._check_path(path):
            raise FileNotFoundError(f"Could not find codelist at {path}")

        data = []
        with open(path, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                
                # Check for correct data shape
                if len(row) != 2:
                    raise InvalidDataShapeError(f"Invalid data shape. Expected 2 columns, but got {len(row)} columns.")

                # Validate the codelist. Raises errors if invalid.
                self._validate_codelist(row)
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
        - The fourth character if present is a dot
        - The fifth character if present is a number
        - The fifth character must be present if the fourth character is a dot
        """
        pattern = re.compile(r"^[A-Z]\d{2}(\.\d{1,2})?$")

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
    

    def _SNOMED_to_ICD10(self, SNOMED_to_ICD10_map_file: str) -> None:
        """
        maps SNOMED codes to their corresponding ICD10

        Args:
            SNOMED_to_ICD10_map_file (str): mapping file path
        """
        
        # Using Polars for joining (otherwise longer code is needed)
        map_file = pl.read_csv(SNOMED_to_ICD10_map_file)
        # Assuming self.data (should be checked) is a DataFrame (or Table) containing SNOMED codes

        df_data = pl.DataFrame(self.data)

        df_data = df_data.with_columns([
            pl.col('code').cast(pl.Int64) 
        ])

        # df_data = df_data.with_column(df_data['code'].cast(pl.Object))

        # Joining data

        df_ICD10_codes = df_data.join(map_file, left_on='code', right_on='conceptId' , how='inner') 
        df_ICD10_codes = df_ICD10_codes.drop(['ICD10_3digit','code'])
        df_ICD10_codes = df_ICD10_codes.rename({"mapTarget": "code"})
        df_ICD10_codes = df_ICD10_codes.unique()
        df_ICD10_codes = df_ICD10_codes[['code','term']]


        list_of_dicts = df_ICD10_codes.to_dict(as_series=False)
        list_of_dicts = [
            {'code': str(code), 'term': term.strip()}
            for code, term in zip(list_of_dicts['code'], list_of_dicts['term'])
        ]

        self.data = list_of_dicts

        return self.data
        # If pandas is allowed:
        

    def _ICD10_3Digit(self):
        """
        Truncating ICD10 codes to contain the first 3 digits only
        """
        print(self.data)
        print(self.code_column)
        for entry in self.data:
            entry['code'] = entry['code'][:3]
        return self.data
        # self.data[self.code_column] = self.data[self.code_column].str[:3]