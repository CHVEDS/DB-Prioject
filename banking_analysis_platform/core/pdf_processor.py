"""PDF processor for banking reports - adapted from pdf_extractor.py."""

import sys
import io
import tabula
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from typing import List
import re
import logging

# Setup logging
logger = logging.getLogger(__name__)

warnings.filterwarnings('ignore')

def clean_cell(value):
    """Clean cell value from special characters and extra spaces"""
    if pd.isna(value) or value == '' or str(value).strip() == '':
        return np.nan
    if isinstance(value, str):
        value = (value.replace('\xa0', ' ')
                      .replace('\n', ' ')
                      .replace('\r', ' ')
                      .strip())
        return value if value else np.nan
    return value

def safe_applymap(df, func):
    """Compatibility with different pandas versions (applymap → map)"""
    try:
        return df.map(func)
    except AttributeError:
        return df.applymap(func)

def is_valid_table(df: pd.DataFrame, min_rows: int = 3, min_cols: int = 2) -> bool:
    """Check if object is a real table (filtering out garbage)"""
    if df.empty or df.shape[0] < min_rows or df.shape[1] < min_cols:
        return False
    fill_ratio = df.notna().sum().sum() / (df.shape[0] * df.shape[1])
    if fill_ratio < 0.3:
        return False
    numeric_cells = df.apply(lambda s: pd.to_numeric(s, errors='coerce')).notna().sum().sum()
    if numeric_cells < 2 and df.shape[1] < 3:
        return False
    return True

def extract_tables_from_pdf(pdf_path: Path, method: str = "stream") -> List[pd.DataFrame]:
    """Extract and clean tables from a single PDF"""
    tables = []
    try:
        raw_tables = tabula.read_pdf(
            str(pdf_path),
            pages="all",
            multiple_tables=True,
            stream=(method == "stream"),
            lattice=(method == "lattice"),
            pandas_options={'dtype': str},
            silent=True,
            guess=True,
            encoding='utf-8'
        )
        if not raw_tables:
            return tables
        for df in raw_tables:
            df = safe_applymap(df, clean_cell)
            df = df.dropna(how='all').dropna(axis=1, how='all')
            if is_valid_table(df):
                df.columns = [
                    str(col).strip() if pd.notna(col) and str(col).strip() else f"Col_{i + 1}"
                    for i, col in enumerate(df.columns)
                ]
                tables.append(df)
    except Exception as e:
        logger.warning(f"Error extracting from {pdf_path.name}: {str(e)[:80]}")
        print(f"  ⚠ Ошибка при извлечении из {pdf_path.name}: {str(e)[:80]}")
    return tables