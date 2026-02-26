"""Validation utilities for banking analysis platform."""

import re
from typing import Any, Dict, List, Union
import pandas as pd


def validate_financial_data(data: Dict[str, Any]) -> List[str]:
    """
    Validate financial data structure and values.
    
    Args:
        data: Financial data dictionary to validate
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Check required fields
    required_fields = [
        'total_assets', 'total_liabilities', 'equity', 
        'net_income', 'cash_and_equivalents', 'loans_to_customers'
    ]
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None or pd.isna(data[field]):
            errors.append(f"Field '{field}' has invalid value: {data[field]}")
        elif not isinstance(data[field], (int, float)):
            errors.append(f"Field '{field}' should be numeric, got {type(data[field])}")
    
    # Validate numerical ranges
    if 'total_assets' in data and data['total_assets'] < 0:
        errors.append("total_assets should be non-negative")
    
    if 'equity' in data and data['equity'] < 0:
        errors.append("equity should be non-negative")
    
    if 'net_income' in data and abs(data['net_income']) > 1e15:  # Over 1 quadrillion
        errors.append("net_income seems unreasonably large")
    
    return errors


def validate_bank_name(bank_name: str) -> List[str]:
    """
    Validate bank name format.
    
    Args:
        bank_name: Name of the bank to validate
        
    Returns:
        List of validation errors
    """
    errors = []
    
    if not bank_name or not isinstance(bank_name, str):
        errors.append("Bank name must be a non-empty string")
        return errors
    
    if len(bank_name.strip()) < 2:
        errors.append("Bank name must be at least 2 characters long")
    
    if len(bank_name) > 200:
        errors.append("Bank name is too long (max 200 characters)")
    
    # Check for potentially problematic patterns
    if re.search(r'[<>:"/\\|?*]', bank_name):
        errors.append("Bank name contains invalid characters")
    
    return errors


def validate_report_year(year: int) -> List[str]:
    """
    Validate report year.
    
    Args:
        year: Year to validate
        
    Returns:
        List of validation errors
    """
    errors = []
    
    current_year = pd.Timestamp.now().year
    
    if not isinstance(year, int):
        errors.append("Year must be an integer")
    elif year < 1900:
        errors.append("Year is too early (before 1900)")
    elif year > current_year + 1:
        errors.append(f"Year {year} is in the future (current year: {current_year})")
    
    return errors


def validate_ratio_value(value: Union[float, tuple]) -> List[str]:
    """
    Validate ratio value.
    
    Args:
        value: Ratio value (can be just the value or (value, interpretation) tuple)
        
    Returns:
        List of validation errors
    """
    errors = []
    
    # Extract value if it's a tuple
    if isinstance(value, tuple):
        if len(value) != 2:
            errors.append("Ratio tuple must have exactly 2 elements (value, interpretation)")
            return errors
        ratio_value = value[0]
    else:
        ratio_value = value
    
    if pd.isna(ratio_value):
        errors.append("Ratio value cannot be NaN")
    elif not isinstance(ratio_value, (int, float)):
        errors.append(f"Ratio value must be numeric, got {type(ratio_value)}")
    elif abs(ratio_value) > 1000:  # Very large ratios are suspicious
        errors.append(f"Ratio value {ratio_value} seems unreasonably large")
    
    return errors


def validate_pdf_content(content: str) -> List[str]:
    """
    Validate PDF content for basic banking report characteristics.
    
    Args:
        content: Text content extracted from PDF
        
    Returns:
        List of validation warnings (not errors since content might be valid)
    """
    warnings = []
    
    if not content or len(content.strip()) < 100:
        warnings.append("PDF content appears to be very short (< 100 characters)")
    
    # Check for typical banking report keywords
    banking_keywords = [
        'баланс', 'активы', 'обязательства', 'капитал', 'доходы', 
        'расходы', 'прибыль', 'убыток', 'кредит', 'депозит', 'банк'
    ]
    
    content_lower = content.lower()
    found_keywords = [kw for kw in banking_keywords if kw in content_lower]
    
    if len(found_keywords) < 3:
        warnings.append(
            f"Content contains few banking keywords: {found_keywords}. "
            "May not be a proper banking report."
        )
    
    return warnings