"""
This contains the base class for report transformers.
"""
from __future__ import annotations
from typing import List
from abc import ABC, abstractmethod

import pytest

from tretools.phenotype_report.report import PhenotypeReport


class ReportTransformer(ABC):
    def __init__(self) -> None:
        self.reports = []
        self.logs = []

    # @classmethod
    # def _load_from_json(cls, paths: List[str]) -> ReportTransformer:
    #     pass

    @abstractmethod
    def load_from_objects(self, objects: List[PhenotypeReport]) -> ReportTransformer:
        pass

    @abstractmethod
    def _write_readme(self, path: str) -> None:
        pass

    @abstractmethod
    def transform(self) -> None:
        pass