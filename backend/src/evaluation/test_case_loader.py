"""
Test Case Loader for LLM Evaluation Framework

This module handles loading and validating test cases from JSON files.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class TestCaseLoader:
    """
    Load and validate test cases for evaluation.
    """
    
    def __init__(self, datasets_dir: str = None):
        """
        Initialize the test case loader.
        
        Args:
            datasets_dir: Directory containing test case JSON files
        """
        if datasets_dir is None:
            # Default to datasets directory relative to this file
            self.datasets_dir = Path(__file__).parent / "datasets"
        else:
            self.datasets_dir = Path(datasets_dir)
        
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
    
    def load_dataset(self, filename: str) -> Dict[str, Any]:
        """
        Load a test case dataset from a JSON file.
        
        Args:
            filename: Name of the JSON file (with or without .json extension)
        
        Returns:
            Dictionary containing the dataset
        """
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        filepath = self.datasets_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"Dataset not found: {filepath}")
        
        with open(filepath, 'r', encoding='utf-8') as f:
            dataset = json.load(f)
        
        # Validate dataset structure
        self._validate_dataset(dataset)
        
        return dataset
    
    def _validate_dataset(self, dataset: Dict[str, Any]) -> None:
        """
        Validate that a dataset has the required structure.
        
        Args:
            dataset: Dataset dictionary to validate
        
        Raises:
            ValueError: If dataset is invalid
        """
        required_fields = ['dataset_name', 'version', 'test_cases']
        
        for field in required_fields:
            if field not in dataset:
                raise ValueError(f"Dataset missing required field: {field}")
        
        if not isinstance(dataset['test_cases'], list):
            raise ValueError("test_cases must be a list")
        
        # Validate each test case
        for i, test_case in enumerate(dataset['test_cases']):
            self._validate_test_case(test_case, i)
    
    def _validate_test_case(self, test_case: Dict[str, Any], index: int) -> None:
        """
        Validate a single test case.
        
        Args:
            test_case: Test case dictionary
            index: Index of the test case in the dataset
        
        Raises:
            ValueError: If test case is invalid
        """
        required_fields = ['test_id', 'question', 'expected_output']
        
        for field in required_fields:
            if field not in test_case:
                raise ValueError(
                    f"Test case {index} (ID: {test_case.get('test_id', 'unknown')}) "
                    f"missing required field: {field}"
                )
    
    def list_datasets(self) -> List[str]:
        """
        List all available dataset files.
        
        Returns:
            List of dataset filenames
        """
        json_files = list(self.datasets_dir.glob("*.json"))
        return [f.name for f in json_files]
    
    def save_dataset(self, dataset: Dict[str, Any], filename: str) -> None:
        """
        Save a dataset to a JSON file.
        
        Args:
            dataset: Dataset dictionary
            filename: Name of the JSON file
        """
        if not filename.endswith('.json'):
            filename = f"{filename}.json"
        
        filepath = self.datasets_dir / filename
        
        # Validate before saving
        self._validate_dataset(dataset)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    def get_test_cases(self, dataset: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract test cases from a dataset.
        
        Args:
            dataset: Dataset dictionary
        
        Returns:
            List of test case dictionaries
        """
        return dataset.get('test_cases', [])
