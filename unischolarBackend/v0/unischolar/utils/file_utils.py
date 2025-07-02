"""
File utilities for UniScholar platform.

Provides utilities for file I/O operations, CSV handling, and data persistence.
"""

import csv
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from ..core.config import get_config
from ..core.exceptions import ProcessingError


class FileUtils:
    """Utilities for file operations"""
    
    def __init__(self):
        self.config = get_config()
        self._ensure_output_directory()
    
    def _ensure_output_directory(self):
        """Ensure output directory exists"""
        os.makedirs(self.config.output.output_directory, exist_ok=True)
    
    def get_output_path(self, filename: str) -> str:
        """Get full path for output file"""
        return os.path.join(self.config.output.output_directory, filename)
    
    def save_search_results(self, results: List[Dict[str, str]], filename: str):
        """Save search results to CSV file"""
        try:
            output_path = self.get_output_path(filename)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
                if results:
                    fieldnames = results[0].keys()
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(results)
            
            print(f"Saved {len(results)} search results to {output_path}")
            
        except Exception as e:
            raise ProcessingError(f"Failed to save search results: {e}")
    
    def save_organizations(self, organizations: List[Any], filename: str):
        """Save organizations to CSV file"""
        try:
            output_path = self.get_output_path(filename)
            
            # Convert organizations to dictionaries
            org_dicts = []
            for org in organizations:
                if hasattr(org, '__dict__'):
                    org_dict = org.__dict__.copy()
                    # Convert lists to strings for CSV compatibility
                    for key, value in org_dict.items():
                        if isinstance(value, list):
                            org_dict[key] = ', '.join(map(str, value))
                    org_dicts.append(org_dict)
            
            if org_dicts:
                df = pd.DataFrame(org_dicts)
                df.to_csv(output_path, index=False, encoding='utf-8')
                print(f"Saved {len(org_dicts)} organizations to {output_path}")
            
        except Exception as e:
            raise ProcessingError(f"Failed to save organizations: {e}")
    
    def load_csv(self, filename: str) -> pd.DataFrame:
        """Load CSV file as DataFrame"""
        try:
            if not os.path.isabs(filename):
                filename = self.get_output_path(filename)
            
            return pd.read_csv(filename, encoding='utf-8')
            
        except Exception as e:
            raise ProcessingError(f"Failed to load CSV file {filename}: {e}")
    
    def save_json(self, data: Any, filename: str):
        """Save data to JSON file"""
        try:
            output_path = self.get_output_path(filename)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
                
            print(f"Saved data to {output_path}")
            
        except Exception as e:
            raise ProcessingError(f"Failed to save JSON file: {e}")
    
    def load_json(self, filename: str) -> Any:
        """Load JSON file"""
        try:
            if not os.path.isabs(filename):
                filename = self.get_output_path(filename)
            
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            raise ProcessingError(f"Failed to load JSON file {filename}: {e}")
    
    def file_exists(self, filename: str) -> bool:
        """Check if file exists"""
        if not os.path.isabs(filename):
            filename = self.get_output_path(filename)
        return os.path.exists(filename)
    
    def create_backup(self, filename: str) -> str:
        """Create backup of file"""
        if not self.config.output.backup_enabled:
            return filename
        
        try:
            if not os.path.isabs(filename):
                filename = self.get_output_path(filename)
            
            if os.path.exists(filename):
                backup_filename = f"{filename}.backup"
                import shutil
                shutil.copy2(filename, backup_filename)
                return backup_filename
            
            return filename
            
        except Exception as e:
            raise ProcessingError(f"Failed to create backup: {e}") 