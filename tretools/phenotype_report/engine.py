import csv
import os
from typing import Dict, Optional, List
from datetime import datetime

from tretools.datasets.processed_dataset import ProcessedDataset
from tretools.codelists.codelist import Codelist
from tretools.codelists.codelist_types import CodelistType
from tretools.phenotype_report.report import PhenotypeReport
from tretools.phenotype_report.errors import FileNotFoundError


# Singleton design pattern
class PhenotypeReportEngine():
    def __init__(self, index_file_path: str) -> None:
        self.index_file_path = index_file_path

        # this is a singleton so we are storing each datset
        # that we use so we are only loading them once
        self.datasets: Dict[str, ProcessedDataset] = {}
        self.codelists: Dict[str, Codelist] = {}

        self.raw_instructions = self._load_instructions()

    def _load_instructions(self) -> Dict:
        """
        Loads the instructions from the index file.

        Returns:
            Dict: The instructions.
        """
        with open(self.index_file_path, "r") as index_file:
            reader = csv.DictReader(index_file)
            instructions = list(reader)

        # check all files are reachable
        self._check_all_files_reachable(instructions)

        return instructions
    
    def _check_all_files_reachable(self, instructions: Dict) -> None:
        """
        Checks if all the files in the instructions are reachable.

        Args:
            instructions (Dict): The instructions
        Raises:
            FileNotFoundError: If a file is not found.
        """
        for instruction in instructions:
            if not os.path.exists(instruction['dataset_path']):
                raise FileNotFoundError(f"Dataset file {instruction['dataset_path']} not found.")
            if not os.path.exists(instruction['codelist_path']):
                raise FileNotFoundError(f"Codelist file {instruction['codelist_path']} not found.")
            
    def organise_into_phenotypes(self) -> None:
        """
        Consumes the instructions dict and organises them into phenotypes, where each phenotype has a key and then 
        a dictionary of instructions.

        Args:
            instructions (Dict): The instructions.

        Returns:
            Dict: The organised instructions.
        """
        phenotypes = {}
        for instruction in self.raw_instructions:
            if instruction['phenotype_name'] not in phenotypes.keys():
                phenotypes[instruction['phenotype_name']] = {}
            phenotypes[instruction['phenotype_name']][f"{instruction['dataset_name']}_{instruction['codelist_name']}"] = instruction

        self.processed_instructions = phenotypes

    def generate_reports(self, reports_folder_path: Optional[str] = None, overlaps: bool = True) -> List[PhenotypeReport]:
        """
        Loops through the instructions and generates a report for each phenotype.

        Args:
            reports_folder_path (Optional[str], optional): The path to save the reports to. Defaults to None.
            overlaps (bool, optional): Whether to report overlaps. Defaults to True.
        """
        reports = {}

        for phenotype_name, instructions in self.processed_instructions.items():
            report = self._generate_phenotype_report(instructions, phenotype_name, reports_folder_path, overlaps)
            reports[phenotype_name] = report

        return reports

    def _generate_phenotype_report(self, instructions: Dict[str, Dict[str, str]], phenotype_name: str, reports_folder_path: Optional[str] = None, overlaps: bool = True) -> PhenotypeReport:
        report = PhenotypeReport(phenotype_name)

        for name, phenotype_instructions in instructions.items():
            # load the dataset either from the path or from self.datasets if already present
            dataset = self._load_dataset(phenotype_instructions['dataset_name'], phenotype_instructions['dataset_path'], phenotype_instructions['dataset_type'], phenotype_instructions['codelist_type'])
            codelist = self._load_codelist(phenotype_instructions['codelist_name'], phenotype_instructions['codelist_path'], phenotype_instructions['codelist_type'], phenotype_instructions['with_x_in_icd'])
            report.add_count(name, dataset=dataset, codelist=codelist)

        if overlaps:
            report.report_overlaps()

        if reports_folder_path is not None:
            report.save_to_json(f"{reports_folder_path}/{phenotype_name}.json")
        return report
    

    def _load_dataset(self, dataset_name, path: str, dataset_type: str, codelist_type: CodelistType) -> ProcessedDataset:
        """
        Loads the dataset either from the path or from self.datasets if already present.

        Args:
            dataset_name (str): The name of the dataset.
            path (str): The path to the dataset.
            dataset_type (str): The type of the dataset.
            codelist_type (CodelistType): The type of the codelist.
        
        Returns:
            ProcessedDataset: The dataset.
        """
        # load the dataset if it has not already been loaded and add it to the datasets dict
        if dataset_name in self.datasets.keys():
            dataset = self.datasets[dataset_name]
        else:
            dataset = ProcessedDataset(path, dataset_type, codelist_type)
            self.datasets[dataset_name] = dataset
        
        return dataset


    def _load_codelist(self, codelist_name: str, codelist_path: str, codelist_type: CodelistType, add_x_codes) -> Codelist:
        """
        Loads the codelist if it has not already been loaded and add it to the codelists dict.

        Args:
            codelist_name (str): The name of the codelist.
            codelist_path (str): The path to the codelist.
            codelist_type (CodelistType): The type of the codelist.
            add_x_codes (bool, str): Whether to add x codes to the codelist.
        
        """
        # Allow the user to specify whether to add x codes by passing a boolean or a string 
        # with yes, y, no, n
        if add_x_codes in ['Yes', 'yes', 'Y', 'y', True]:
            add_x_codes = True
        else:
            add_x_codes = False

        # load the codelist if it has not already been loaded and add it to the codelists dict
        if codelist_name in self.codelists.keys():
            # if the codelist has already been loaded, check that the x status is the same as the one in the codelist
            # if not, reload the codelist with the correct x status
            if add_x_codes and not self.codelists[codelist_name].add_x_codes:
                codelist = Codelist(codelist_path, codelist_type, add_x_codes=True)
            else:
                codelist = self.codelists[codelist_name]

        else:
            if add_x_codes:
                codelist = Codelist(codelist_path, codelist_type, add_x_codes=True)
            else:
                codelist = Codelist(codelist_path, codelist_type)
            self.codelists[codelist_name] = codelist
        
        return codelist


    @staticmethod
    def generate_empty_template_file(path: str) -> None:
        """
        Generates a template CSV file with the specified columns.
        
        Args:
            path (str): The path to save the CSV file to.
        """
        
        columns = [
            "phenotype_name",
            "dataset_name",
            "dataset_path",
            "dataset_type",
            "codelist_name",
            "codelist_path",
            "codelist_type",
            "with_x_in_icd"
        ]
        
        with open(path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(columns)