"""Metadata extractor for banking reports."""

import re
import pandas as pd
from typing import List, Dict, Tuple, Optional
from datetime import datetime
import logging


logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extraction of metadata from PDF content."""
    
    def __init__(self):
        # Patterns for extracting bank name
        self.bank_name_patterns = [
            r'(?:АО|ПАО|ООО|ЗАО)\s*[«"]([^»"]+)[»"]',
            r'(?:Банк|Кредитная организация)\s*[«"]([^»"]+)[»"]',
            r'полное\s*наименование[:\s]*([^\n]+)',
            r'фирменное\s*наименование[:\s]*([^\n]+)',
            r'Наименование[:\s]*([^\n]+)',
            r'Кредитная\s+организация[:\s]*([^\n]+)',
            r'Организация[:\s]*([^\n]+)',
            r'Банк[:\s]*([^\n]+)'
        ]
        
        # Patterns for extracting report year
        self.year_patterns = [
            r'за\s*(\d{4})\s*год',
            r'годовой\s*отчёт\s*(\d{4})',
            r'отчётный\s*период[:\s]*(\d{4})',
            r'(\d{4})\s*год[а]?[:\s]',
            r'(\d{4})\s*г\.',
            r'(\d{4})\s*года',
            r'отчет\s+за\s+(\d{4})',
            r'годовой отчет[\s\n]*[:\s]*[^\w\d]*(\d{4})'
        ]

    def extract_bank_name(self, tables: List[pd.DataFrame], text_content: str) -> str:
        """
        Extract bank name from PDF content.
        
        Args:
            tables: List of tables extracted from PDF
            text_content: Raw text content from PDF
            
        Returns:
            Real bank name extracted from document (not "Bank A")
        """
        # First try to find bank name in text content
        for pattern in self.bank_name_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE | re.MULTILINE)
            if match:
                bank_name = match.group(1).strip()
                if bank_name and len(bank_name) > 2:
                    return bank_name
        
        # Fallback: search in first few tables
        for df in tables[:3]:
            if df.empty:
                continue
                
            # Search in first few rows and columns
            for row_idx in range(min(10, len(df))):
                row = df.iloc[row_idx]
                for cell in row.values[:20]:  # Check first 20 cells in row
                    if isinstance(cell, str) and len(cell.strip()) > 2:
                        cell_lower = cell.lower()
                        # Look for bank-related terms
                        if ('банк' in cell_lower or 'пао' in cell_lower or 
                            'ао' in cell_lower or 'ооо' in cell_lower or 
                            'зао' in cell_lower):
                            # Extract potential bank name
                            parts = re.split(r'[,:;()«»""]', cell)
                            for part in parts:
                                part = part.strip()
                                if (part and len(part) > 2 and 
                                    not re.match(r'^\d+$', part) and  # Not just numbers
                                    not re.match(r'^[IVX]+$', part)):  # Not Roman numerals
                                    return part
        
        return "Неопределённая организация"

    def extract_report_year(self, tables: List[pd.DataFrame], text_content: str) -> int:
        """
        Extract report year from PDF content.
        
        Args:
            tables: List of tables extracted from PDF
            text_content: Raw text content from PDF
            
        Returns:
            Report year as integer
        """
        # First try to find year in text content
        for pattern in self.year_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            for match in matches:
                try:
                    year = int(match.strip())
                    if 2010 <= year <= datetime.now().year:
                        return year
                except ValueError:
                    continue
        
        # Fallback: search in tables
        for df in tables:
            if df.empty:
                continue
                
            # Search through all cells in first few rows
            for row_idx in range(min(20, len(df))):
                row = df.iloc[row_idx]
                for cell in row.values:
                    if isinstance(cell, str):
                        # Look for 4-digit years
                        year_matches = re.findall(r'\b(201[0-9]|202[0-9])\b', cell)
                        for year_match in year_matches:
                            try:
                                year = int(year_match)
                                if 2010 <= year <= datetime.now().year:
                                    return year
                            except ValueError:
                                continue
        
        # Default to previous year if nothing found
        return datetime.now().year - 1

    def extract_metadata(self, tables: List[pd.DataFrame], text_content: str) -> Dict[str, any]:
        """
        Extract both bank name and report year.
        
        Args:
            tables: List of tables extracted from PDF
            text_content: Raw text content from PDF
            
        Returns:
            Dictionary with 'bank_name' and 'year' keys
        """
        bank_name = self.extract_bank_name(tables, text_content)
        report_year = self.extract_report_year(tables, text_content)
        
        return {
            'bank_name': bank_name,
            'year': report_year
        }


def extract_metadata(tables: List[pd.DataFrame], text_content: str) -> Dict[str, any]:
    """
    Convenience function to extract metadata from PDF content.
    
    Args:
        tables: List of tables extracted from PDF
        text_content: Raw text content from PDF
        
    Returns:
        Dictionary with metadata
    """
    extractor = MetadataExtractor()
    return extractor.extract_metadata(tables, text_content)