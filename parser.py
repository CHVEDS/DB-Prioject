"""
Parser module for extracting financial data from bank reports.

This module handles PDF parsing using MinerU and extracts structured
data from balance sheets and income statements.
"""

import logging
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from bs4 import BeautifulSoup
from config import BANK_ACCOUNT_CODES, BALANCE_SHEET_ITEMS
import tempfile


logger = logging.getLogger(__name__)


def clean_number(value: str) -> Optional[float]:
    """
    Clean and convert string values to float.

    Args:
        value: String representation of a number

    Returns:
        Float value or None if conversion fails
    """
    if not value or pd.isna(value) or value == '' or value.lower() in ['-', '—', 'n/a', 'nan']:
        return None

    # Remove extra spaces and special characters
    cleaned = str(value).strip().replace(' ', '').replace(',', '.')

    # Handle common formatting issues
    cleaned = re.sub(r'[^\d.-]', '', cleaned)

    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not convert '{value}' to float")
        return None


def extract_bank_tables(markdown_content: str) -> Dict[str, pd.DataFrame]:
    """
    Extract tables from markdown content representing bank financial statements.

    Args:
        markdown_content: Content extracted from PDF using MinerU

    Returns:
        Dictionary of DataFrames with identified financial statement tables
    """
    soup = BeautifulSoup(markdown_content, 'html.parser')
    text_content = soup.get_text()

    # Look for specific patterns in the text to identify table sections
    balance_sheet_pattern = r'(Актив|Пассив|Balance Sheet|Statement of Financial Position)'
    income_statement_pattern = r'(Отчет о прибылях и убытках|Income Statement|Profit and Loss)'

    tables = {}

    # Find and extract balance sheet
    if re.search(balance_sheet_pattern, text_content, re.IGNORECASE):
        balance_table = extract_balance_sheet(text_content)
        if balance_table is not None:
            tables['balance_sheet'] = balance_table

    # Find and extract income statement
    if re.search(income_statement_pattern, text_content, re.IGNORECASE):
        income_table = extract_income_statement(text_content)
        if income_table is not None:
            tables['income_statement'] = income_table

    return tables


def extract_balance_sheet(content: str) -> Optional[pd.DataFrame]:
    """
    Extract balance sheet data from content.

    Args:
        content: Text content containing balance sheet information

    Returns:
        DataFrame with balance sheet data or None if not found
    """
    # This is a simplified extraction method
    # In practice, you would need more sophisticated parsing

    # Look for patterns indicating assets and liabilities
    asset_patterns = [
        r'(Актив|Assets)',
        r'(I\. .*Актив|1\. .*Assets)',
        r'(1\.1\. .*Актив|1\.1\. .*Assets)'
    ]

    liability_patterns = [
        r'(Пассив|Liabilities)',
        r'(II\. .*Пассив|2\. .*Liabilities)',
        r'(2\.1\. .*Пассив|2\.1\. .*Liabilities)'
    ]

    # Find relevant sections
    asset_section = None
    liability_section = None

    for pattern in asset_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            # Get the next section until liability section starts
            start_pos = match.end()
            for lp in liability_patterns:
                liab_match = re.search(lp, content[start_pos:], re.IGNORECASE)
                if liab_match:
                    asset_section = content[start_pos:start_pos + liab_match.start()]
                    break
            if asset_section is None:
                # If no liability section found, take until end of document
                asset_section = content[start_pos:]
            break

    for pattern in liability_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            # Get the next section
            start_pos = match.end()
            liability_section = content[start_pos:start_pos + 2000]  # Limit to reasonable size
            break

    # Process both sections to extract account numbers and values
    assets_data = extract_accounts_from_section(asset_section) if asset_section else {}
    liabilities_data = extract_accounts_from_section(liability_section) if liability_section else {}

    # Combine into a single DataFrame
    if assets_data or liabilities_data:
        all_accounts = {**assets_data, **liabilities_data}

        df = pd.DataFrame(list(all_accounts.items()), columns=['account_code', 'amount'])
        return df

    return None


def extract_income_statement(content: str) -> Optional[pd.DataFrame]:
    """
    Extract income statement data from content.

    Args:
        content: Text content containing income statement information

    Returns:
        DataFrame with income statement data or None if not found
    """
    # Look for income statement indicators
    income_patterns = [
        r'(Отчет о прибылях и убытках|Income Statement|Profit and Loss)',
        r'(Выручка|Revenue|Доходы|Expenses|Расходы)'
    ]

    for pattern in income_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            # Extract a reasonable section around the match
            start_pos = max(0, match.start() - 500)
            end_pos = min(len(content), match.end() + 2000)
            income_section = content[start_pos:end_pos]

            # Extract account numbers and values
            income_data = extract_accounts_from_section(income_section)

            if income_data:
                df = pd.DataFrame(list(income_data.items()), columns=['account_code', 'amount'])
                return df

    return None


def extract_accounts_from_section(section: str) -> Dict[str, float]:
    """
    Extract account numbers and their corresponding values from a text section.

    Args:
        section: Text section to parse

    Returns:
        Dictionary mapping account codes to their values
    """
    if not section:
        return {}

    accounts = {}

    # Look for account codes followed by numbers
    # Pattern: Account code (4-5 digits) followed by description and amount
    pattern = r'(\d{4,5})[^\d]*?([\d\s\.,-]+)(?:\s|$)'

    matches = re.findall(pattern, section)

    for account_code, amount_str in matches:
        # Clean the amount string
        amount = clean_number(amount_str)
        if amount is not None:
            # Map to known account codes if possible
            if account_code in BANK_ACCOUNT_CODES:
                accounts[account_code] = amount
            else:
                # Check if it's a partial match (first 4 digits)
                for known_code in BANK_ACCOUNT_CODES:
                    if known_code.startswith(account_code):
                        accounts[known_code] = amount
                        break
                else:
                    # Add as unknown code
                    accounts[account_code] = amount

    return accounts


def parse_pdf_with_mineru(pdf_path: str) -> Dict[str, pd.DataFrame]:
    """
    Parse PDF file using MinerU and extract financial tables.

    Args:
        pdf_path: Path to the PDF file to parse

    Returns:
        Dictionary of DataFrames containing parsed financial data
    """
    try:
        # Import here to avoid issues if mineru is not installed
        from mineru.cli.common import do_parse
        import os

        # Create temporary directory for output
        with tempfile.TemporaryDirectory() as temp_dir:
            # Prepare arguments for do_parse
            args = type('Args', (), {
                'input_file': pdf_path,
                'output_dir': temp_dir,
                'format': ['markdown'],
                'model_cfg': None,
                'table_config': None,
                'device': 'cpu',
                'pdf_file_names': [os.path.basename(pdf_path)],
                'pdf_bytes_list': [Path(pdf_path).read_bytes()],
                'p_lang_list': ['ru']  # Set language to Russian for bank reports
            })()

            # Parse the PDF
            do_parse(args)

            # Read the generated markdown file
            md_files = list(Path(temp_dir).glob("*.md"))
            if not md_files:
                logger.error("No markdown files generated by MinerU")
                return {}

            md_file = md_files[0]
            with open(md_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Extract tables from markdown content
            tables = extract_bank_tables(markdown_content)

            return tables

    except ImportError:
        logger.error("MinerU library not found. Please install it using 'pip install mineru'")
        return {}
    except Exception as e:
        logger.error(f"Error parsing PDF with MinerU: {str(e)}")
        return {}


def aggregate_financial_data(tables: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """
    Aggregate extracted data into key financial metrics.

    Args:
        tables: Dictionary of DataFrames with parsed financial data

    Returns:
        Dictionary of aggregated financial metrics
    """
    aggregated = {}

    # Process balance sheet data
    if 'balance_sheet' in tables:
        bs_df = tables['balance_sheet']

        # Calculate total assets
        total_assets = 0
        for _, row in bs_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount):
                # Check if this is an asset account (typically starting with 1)
                if code.startswith('1'):
                    total_assets += amount
                elif code in BALANCE_SHEET_ITEMS['total_assets']:
                    total_assets += amount

        aggregated['total_assets'] = total_assets

        # Calculate total liabilities
        total_liabilities = 0
        for _, row in bs_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount):
                # Check if this is a liability account (typically starting with 2)
                if code.startswith('2'):
                    total_liabilities += amount
                elif code in BALANCE_SHEET_ITEMS['total_liabilities']:
                    total_liabilities += amount

        aggregated['total_liabilities'] = total_liabilities

        # Calculate equity
        aggregated['equity'] = aggregated.get('total_assets', 0) - aggregated.get('total_liabilities', 0)

        # Calculate cash and equivalents
        cash_equivalents = 0
        for _, row in bs_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount) and code in BALANCE_SHEET_ITEMS.get('cash_and_equivalents', []):
                cash_equivalents += amount

        aggregated['cash_and_equivalents'] = cash_equivalents

        # Calculate loans to customers
        loans = 0
        for _, row in bs_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount) and code in BALANCE_SHEET_ITEMS.get('loans_to_customers', []):
                loans += amount

        aggregated['loans_to_customers'] = loans

    # Process income statement data
    if 'income_statement' in tables:
        is_df = tables['income_statement']

        # Calculate net interest income
        interest_income = 0
        interest_expense = 0

        for _, row in is_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount):
                if code in ['70601']:  # Interest income
                    interest_income += amount
                elif code in ['70602']:  # Interest expense
                    interest_expense += amount
                elif code in ['70701']:  # Commission income
                    interest_income += amount  # Treat as part of net income
                elif code in ['70702']:  # Commission expense
                    interest_expense += amount  # Treat as part of net expenses

        aggregated['net_interest_income'] = interest_income - interest_expense

        # Calculate net income
        net_income = 0
        for _, row in is_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount):
                # Positive amounts are typically income, negative are expenses
                net_income += amount

        aggregated['net_income'] = net_income

    return aggregated


"""
Parser module for extracting financial data from bank reports.

This module handles PDF parsing using MinerU and extracts structured
data from balance sheets and income statements.
"""

import logging
import re
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from bs4 import BeautifulSoup
from config import BANK_ACCOUNT_CODES, BALANCE_SHEET_ITEMS
import tempfile


logger = logging.getLogger(__name__)


def clean_number(value: str) -> Optional[float]:
    """
    Clean and convert string values to float.

    Args:
        value: String representation of a number

    Returns:
        Float value or None if conversion fails
    """
    if not value or pd.isna(value) or value == '' or value.lower() in ['-', '—', 'n/a', 'nan']:
        return None

    # Remove extra spaces and special characters
    cleaned = str(value).strip().replace(' ', '').replace(',', '.')

    # Handle common formatting issues
    cleaned = re.sub(r'[^\d.-]', '', cleaned)

    try:
        return float(cleaned)
    except ValueError:
        logger.warning(f"Could not convert '{value}' to float")
        return None


def extract_bank_tables(markdown_content: str) -> Dict[str, pd.DataFrame]:
    """
    Extract tables from markdown content representing bank financial statements.

    Args:
        markdown_content: Content extracted from PDF using MinerU

    Returns:
        Dictionary of DataFrames with identified financial statement tables
    """
    soup = BeautifulSoup(markdown_content, 'html.parser')
    text_content = soup.get_text()

    # Look for specific patterns in the text to identify table sections
    balance_sheet_pattern = r'(Актив|Пассив|Balance Sheet|Statement of Financial Position)'
    income_statement_pattern = r'(Отчет о прибылях и убытках|Income Statement|Profit and Loss)'

    tables = {}

    # Find and extract balance sheet
    if re.search(balance_sheet_pattern, text_content, re.IGNORECASE):
        balance_table = extract_balance_sheet(text_content)
        if balance_table is not None:
            tables['balance_sheet'] = balance_table

    # Find and extract income statement
    if re.search(income_statement_pattern, text_content, re.IGNORECASE):
        income_table = extract_income_statement(text_content)
        if income_table is not None:
            tables['income_statement'] = income_table

    return tables


def extract_balance_sheet(content: str) -> Optional[pd.DataFrame]:
    """
    Extract balance sheet data from content.

    Args:
        content: Text content containing balance sheet information

    Returns:
        DataFrame with balance sheet data or None if not found
    """
    # This is a simplified extraction method
    # In practice, you would need more sophisticated parsing

    # Look for patterns indicating assets and liabilities
    asset_patterns = [
        r'(Актив|Assets)',
        r'(I\. .*Актив|1\. .*Assets)',
        r'(1\.1\. .*Актив|1\.1\. .*Assets)'
    ]

    liability_patterns = [
        r'(Пассив|Liabilities)',
        r'(II\. .*Пассив|2\. .*Liabilities)',
        r'(2\.1\. .*Пассив|2\.1\. .*Liabilities)'
    ]

    # Find relevant sections
    asset_section = None
    liability_section = None

    for pattern in asset_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            # Get the next section until liability section starts
            start_pos = match.end()
            for lp in liability_patterns:
                liab_match = re.search(lp, content[start_pos:], re.IGNORECASE)
                if liab_match:
                    asset_section = content[start_pos:start_pos + liab_match.start()]
                    break
            if asset_section is None:
                # If no liability section found, take until end of document
                asset_section = content[start_pos:]
            break

    for pattern in liability_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            # Get the next section
            start_pos = match.end()
            liability_section = content[start_pos:start_pos + 2000]  # Limit to reasonable size
            break

    # Process both sections to extract account numbers and values
    assets_data = extract_accounts_from_section(asset_section) if asset_section else {}
    liabilities_data = extract_accounts_from_section(liability_section) if liability_section else {}

    # Combine into a single DataFrame
    if assets_data or liabilities_data:
        all_accounts = {**assets_data, **liabilities_data}

        df = pd.DataFrame(list(all_accounts.items()), columns=['account_code', 'amount'])
        return df

    return None


def extract_income_statement(content: str) -> Optional[pd.DataFrame]:
    """
    Extract income statement data from content.

    Args:
        content: Text content containing income statement information

    Returns:
        DataFrame with income statement data or None if not found
    """
    # Look for income statement indicators
    income_patterns = [
        r'(Отчет о прибылях и убытках|Income Statement|Profit and Loss)',
        r'(Выручка|Revenue|Доходы|Expenses|Расходы)'
    ]

    for pattern in income_patterns:
        match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
        if match:
            # Extract a reasonable section around the match
            start_pos = max(0, match.start() - 500)
            end_pos = min(len(content), match.end() + 2000)
            income_section = content[start_pos:end_pos]

            # Extract account numbers and values
            income_data = extract_accounts_from_section(income_section)

            if income_data:
                df = pd.DataFrame(list(income_data.items()), columns=['account_code', 'amount'])
                return df

    return None


def extract_accounts_from_section(section: str) -> Dict[str, float]:
    """
    Extract account numbers and their corresponding values from a text section.

    Args:
        section: Text section to parse

    Returns:
        Dictionary mapping account codes to their values
    """
    if not section:
        return {}

    accounts = {}

    # Look for account codes followed by numbers
    # Pattern: Account code (4-5 digits) followed by description and amount
    pattern = r'(\d{4,5})[^\d]*?([\d\s\.,-]+)(?:\s|$)'

    matches = re.findall(pattern, section)

    for account_code, amount_str in matches:
        # Clean the amount string
        amount = clean_number(amount_str)
        if amount is not None:
            # Map to known account codes if possible
            if account_code in BANK_ACCOUNT_CODES:
                accounts[account_code] = amount
            else:
                # Check if it's a partial match (first 4 digits)
                for known_code in BANK_ACCOUNT_CODES:
                    if known_code.startswith(account_code):
                        accounts[known_code] = amount
                        break
                else:
                    # Add as unknown code
                    accounts[account_code] = amount

    return accounts


def parse_pdf_with_mineru(pdf_path: str) -> Dict[str, pd.DataFrame]:
    """
    Parse PDF file using MinerU and extract financial tables.
    """
    try:
        import os
        import tempfile
        from pathlib import Path

        # Проверка установки библиотеки
        try:
            import magic_pdf
            logger.info(f"magic-pdf installed: {getattr(magic_pdf, '__version__', 'unknown')}")
        except ImportError:
            logger.error("magic-pdf library not installed")
            return parse_pdf_fallback(pdf_path)

        # Импортируем do_parse из правильного модуля
        do_parse = None
        try:
            from magic_pdf.pdf_parse_union_core import do_parse
            logger.info("Using magic_pdf.pdf_parse_union_core")
        except ImportError:
            try:
                from magic_pdf.parsers.pdf_parse_union import do_parse
                logger.info("Using magic_pdf.parsers.pdf_parse_union")
            except ImportError:
                try:
                    from magic_pdf.pdf_parse import do_parse
                    logger.info("Using magic_pdf.pdf_parse")
                except ImportError:
                    logger.warning("Could not import do_parse, using fallback parser")
                    return parse_pdf_fallback(pdf_path)

        if do_parse is None:
            logger.warning("do_parse not found, using fallback parser")
            return parse_pdf_fallback(pdf_path)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Подготовка данных
            file_name = os.path.basename(pdf_path)
            file_bytes = Path(pdf_path).read_bytes()
            lang_list = ['ru']

            logger.info(f"Parsing PDF: {file_name}")

            # Вызов функции с правильными аргументами
            do_parse(
                pdf_file_names=[file_name],
                pdf_bytes_list=[file_bytes],
                p_lang_list=lang_list,
                output_dir=temp_dir,
                model_cfg=None,
                table_config=None,
                device='cpu'
            )

            # Читаем сгенерированный markdown файл
            md_files = list(Path(temp_dir).glob("*.md"))
            if not md_files:
                logger.error("No markdown files generated by MinerU")
                all_files = list(Path(temp_dir).glob("*"))
                logger.error(f"Files in temp dir: {all_files}")
                return parse_pdf_fallback(pdf_path)

            md_file = md_files[0]
            logger.info(f"Found markdown file: {md_file.name}")

            with open(md_file, 'r', encoding='utf-8') as f:
                markdown_content = f.read()

            # Извлекаем таблицы из markdown
            tables = extract_bank_tables(markdown_content)
            logger.info(f"Extracted {len(tables)} tables")

            if not tables:
                logger.warning("No tables extracted, using fallback parser")
                return parse_pdf_fallback(pdf_path)

            return tables

    except Exception as e:
        logger.error(f"Error parsing PDF with MinerU: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return parse_pdf_fallback(pdf_path)


def parse_pdf_fallback(pdf_path: str) -> Dict[str, pd.DataFrame]:
    """
    Fallback PDF parser using PyPDF2 (works without magic-pdf).
    """
    try:
        from PyPDF2 import PdfReader
        import re

        logger.info("Using fallback PDF parser (PyPDF2)")

        reader = PdfReader(pdf_path)
        text = ""

        for page in reader.pages:
            text += page.extract_text() or ""

        # Извлекаем счета и суммы из текста
        accounts = extract_accounts_from_section(text)

        if accounts:
            df = pd.DataFrame(list(accounts.items()), columns=['account_code', 'amount'])
            return {'balance_sheet': df}

        logger.warning("Fallback parser could not extract data")
        return {}

    except Exception as e:
        logger.error(f"Fallback parser error: {str(e)}")
        return {}


def aggregate_financial_data(tables: Dict[str, pd.DataFrame]) -> Dict[str, float]:
    """
    Aggregate extracted data into key financial metrics.

    Args:
        tables: Dictionary of DataFrames with parsed financial data

    Returns:
        Dictionary of aggregated financial metrics
    """
    aggregated = {}

    # Process balance sheet data
    if 'balance_sheet' in tables:
        bs_df = tables['balance_sheet']

        # Calculate total assets
        total_assets = 0
        for _, row in bs_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount):
                # Check if this is an asset account (typically starting with 1)
                if code.startswith('1'):
                    total_assets += amount
                elif code in BALANCE_SHEET_ITEMS['total_assets']:
                    total_assets += amount

        aggregated['total_assets'] = total_assets

        # Calculate total liabilities
        total_liabilities = 0
        for _, row in bs_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount):
                # Check if this is a liability account (typically starting with 2)
                if code.startswith('2'):
                    total_liabilities += amount
                elif code in BALANCE_SHEET_ITEMS['total_liabilities']:
                    total_liabilities += amount

        aggregated['total_liabilities'] = total_liabilities

        # Calculate equity
        aggregated['equity'] = aggregated.get('total_assets', 0) - aggregated.get('total_liabilities', 0)

        # Calculate cash and equivalents
        cash_equivalents = 0
        for _, row in bs_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount) and code in BALANCE_SHEET_ITEMS.get('cash_and_equivalents', []):
                cash_equivalents += amount

        aggregated['cash_and_equivalents'] = cash_equivalents

        # Calculate loans to customers
        loans = 0
        for _, row in bs_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount) and code in BALANCE_SHEET_ITEMS.get('loans_to_customers', []):
                loans += amount

        aggregated['loans_to_customers'] = loans

    # Process income statement data
    if 'income_statement' in tables:
        is_df = tables['income_statement']

        # Calculate net interest income
        interest_income = 0
        interest_expense = 0

        for _, row in is_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount):
                if code in ['70601']:  # Interest income
                    interest_income += amount
                elif code in ['70602']:  # Interest expense
                    interest_expense += amount
                elif code in ['70701']:  # Commission income
                    interest_income += amount  # Treat as part of net income
                elif code in ['70702']:  # Commission expense
                    interest_expense += amount  # Treat as part of net expenses

        aggregated['net_interest_income'] = interest_income - interest_expense

        # Calculate net income
        net_income = 0
        for _, row in is_df.iterrows():
            code = str(row['account_code'])
            amount = row['amount']
            if pd.notna(amount):
                # Positive amounts are typically income, negative are expenses
                net_income += amount

        aggregated['net_income'] = net_income

    return aggregated
