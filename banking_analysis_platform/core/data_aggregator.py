"""Data aggregator for banking reports - adapted from redyxlsx.py."""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
import warnings
from datetime import datetime


warnings.filterwarnings('ignore')


def aggregate_financial_data(tables: List[pd.DataFrame]) -> Dict[str, float]:
    """
    Aggregate financial data from extracted tables following the logic from redyxlsx.py.
    
    Args:
        tables: List of pandas DataFrames representing tables from PDF
        
    Returns:
        Dictionary with aggregated financial data
    """
    # Initialize result dictionary with default values
    financial_data = {
        'total_assets': 0,
        'total_liabilities': 0,
        'equity': 0,
        'net_income': 0,
        'cash_and_equivalents': 0,
        'loans_to_customers': 0,
        'deposits_from_customers': 0,
        'operating_income': 0,
        'operating_profit': 0,
        'roa': 0,
        'roe': 0,
        'net_interest_margin': 0,
        'cost_to_income_ratio': 0,
        'non_performing_loan_ratio': 0,
        'capital_adequacy_ratio': 0,
        'current_liquidity_ratio': 0,
        'instant_liquidity_ratio': 0,
        'digital_penetration': 0,
        'mobile_penetration': 0,
        'active_digital_customers': 0,
        'number_of_branches': 0,
        'it_staff': 0,
        'api_count': 0,
        'paperless_operations': 0,
        'electronic_signature_usage': 0,
        'remote_account_opening': 0,
        'churn_rate': 0,
        'retention_rate': 0,
        'products_per_customer': 0,
        'cross_sell_rate': 0,
        'wallet_share': 0,
        'credit_cost': 0,
        'loan_loss_provision_coverage': 0,
        'net_interest_income': 0,
        'subordinated_debt': 0,
        'interest_earning_assets': 0,
        'interest_bearing_liabilities': 0,
        'net_interest_spread': 0,
        'interbank_assets': 0,
        'interbank_liabilities': 0,
        'equity_to_debt_ratio': 0,
        'retained_earnings_to_total_assets': 0,
        'ebit_to_total_assets': 0,
        'total_assets_turnover': 0,
        'return_on_net_assets': 0,
        'return_on_average_total_assets': 0,
        'return_on_net_assets_after_deducting_non_recurring': 0,
        'interbank_assets_to_interest_earning_assets': 0,
        'deposits_to_interest_bearing_liabilities': 0,
        'interbank_liabilities_to_interest_bearing_liabilities': 0
    }

    # Financial patterns from the original redyxlsx.py
    financial_patterns = {
        'total_assets': [r'итого активов', r'валюта баланса', r'активы всего', r'^активы$', r'активы.*конец'],
        'loans_to_customers': [r'кредиты и авансы клиентам', r'кредитный портфель', r'ссуды клиентам',
                              r'выданные кредиты', r'кредиты.*физическим', r'кредиты.*юридическим'],
        'deposits_from_customers': [r'депозиты', r'привлеченные средства', r'средства клиентов', r'обязательства.*клиентов',
                         r'вклады'],
        'net_income': [r'чистая прибыль', r'прибыль.*налог', r'прибыль за год', r'чистая прибыль.*год',
                       r'прибыль.*отчетный период'],
        'operating_income': [r'операционный доход', r'операционные поступления', r'доходы от основной деятельности',
                             r'доходы.*основная'],
        'operating_profit': [r'операционная прибыль', r'прибыль от основной деятельности'],
        'roa': [r'roa', r'рентабельность активов', r'роа', r'рентабельность.*активов'],
        'roe': [r'roe', r'рентабельность собственного капитала', r'роэ', r'рентабельность.*капитала'],
        'net_interest_margin': [r'чистая процентная маржа', r'процентная маржа', r'npm', r'чистая.*маржа'],
        'cost_to_income_ratio': [r'затраты к доходу', r'cir', r'отношение затрат к доходу', r'коэффициент затрат'],
        'non_performing_loan_ratio': [r'неработающ.*кредит', r'npl', r'просрочен.*кредит', r'стадия 3',
                      r'просроченная задолженность', r'нпл'],
        'capital_adequacy_ratio': [r'коэффициент.*адекватности', r'базель', r'капитал.*уровень', r'cet1', r'базовый капитал'],
        'digital_penetration': [r'доля цифровых клиентов', r'цифровая проницаемость', r'цифровые клиенты.*доля',
                                r'цифровизация.*клиентов'],
        'mobile_penetration': [r'мобильная проницаемость', r'доля мобильных клиентов', r'мобильный банкинг.*доля',
                               r'мобильные.*клиенты'],
        'active_digital_customers': [r'активные цифровые клиенты', r'mau', r'активные пользователи',
                                     r'активные клиенты.*мобильный', r'активные.*цифровые'],
        'number_of_branches': [r'количество отделений', r'число отделений', r'сеть отделений',
                               r'отделения и филиалы.*количество', r'офисы.*количество'],
        'it_staff': [r'it-персонал', r'технический персонал', r'it staff', r'сотрудники.*информационные технологии',
                     r'специалисты.*ит'],
        'api_count': [r'api', r'интерфейс прикладного программирования', r'открытые api', r'api.*интеграция'],
        'paperless_operations': [r'безбумажный', r'безбумажные операции', r'безбумажные процессы',
                          r'электронный документооборот'],
        'electronic_signature_usage': [r'электронная подпись', r'цифровая подпись', r'e-подпись', r'эцп',
                                       r'электронно-цифровая подпись'],
        'remote_account_opening': [r'удаленное открытие счета', r'дистанционное открытие счета',
                                   r'онлайн-открытие счета', r'цифровое открытие счета'],
        'churn_rate': [r'коэффициент оттока', r'отток клиентов', r'churn', r'отток.*клиенты'],
        'retention_rate': [r'коэффициент удержания', r'удержание клиентов', r'лояльность', r'удержание.*клиенты'],
        'products_per_customer': [r'продукты на клиента', r'количество продуктов на клиента',
                                  r'среднее число продуктов', r'продуктовая.*корзина'],
        'cross_sell_rate': [r'кросс-продажи', r'перекрестные продажи', r'дополнительные продукты', r'кросс.*продажи'],
        'wallet_share': [r'доля кошелька', r'рыночная доля', r'доля рынка', r'кошелек.*клиента'],
        'credit_cost': [r'стоимость кредитов', r'стоимость риска', r'кор', r'резервы.*кредитные убытки',
                        r'стоимость.*кредитования'],
        'loan_loss_provision_coverage': [
            r'резервы под кредитные убытки к проблемным кредитам',
            r'коэффициент резервирования',
            r'покрытие нпл резервами',
            r'резервы.*нпл'
        ],
        'net_interest_income': [r'чистый процентный доход', r'процентный доход.*чистый', r'nii'],
        'subordinated_debt': [r'субординированный долг', r'субординированные обязательства'],
        'interest_earning_assets': [r'процентные активы', r'доходные активы'],
        'interest_bearing_liabilities': [r'процентные обязательства', r'доходные обязательства'],
        'net_interest_spread': [r'процентный спред', r'разница ставок'],
        'interbank_assets': [r'межбанковские активы', r'активы.*межбанк'],
        'interbank_liabilities': [r'межбанковские обязательства', r'обязательства.*межбанк'],
        'equity_to_debt_ratio': [r'соотношение собственного капитала к заемному', r'капитал.*долг'],
        'retained_earnings_to_total_assets': [r'соотношение нераспределенной прибыли к активам', r'нераспределенная прибыль.*активы'],
        'ebit_to_total_assets': [r'соотношение прибыли до вычета процентов и налогов к активам', r'ebit.*активы'],
        'total_assets_turnover': [r'оборачиваемость активов', r'оборот активов'],
        'return_on_net_assets': [r'рентабельность чистых активов', r'рна'],
        'return_on_average_total_assets': [r'рентабельность средних активов', r'рсна'],
        'return_on_net_assets_after_deducting_non_recurring': [r'рентабельность чистых активов после исключения разовых факторов', r'рнапосле'],
        'interbank_assets_to_interest_earning_assets': [r'соотношение межбанковских активов к процентным активам', r'межбанк.*доходные активы'],
        'deposits_to_interest_bearing_liabilities': [r'соотношение депозитов к процентным обязательствам', r'депозиты.*процентные обязательства'],
        'interbank_liabilities_to_interest_bearing_liabilities': [r'соотношение межбанковских обязательств к процентным обязательствам', r'межбанк.*процентные обязательства']
    }

    # Unit conversion patterns
    unit_patterns = [
        (r'млрд\\.?\\s*р\\.?', 1e9),
        (r'млрд\\.?\\s*руб\\.?', 1e9),
        (r'млрд', 1e9),
        (r'млн\\.?\\s*р\\.?', 1e6),
        (r'млн\\.?\\s*руб\\.?', 1e6),
        (r'млн', 1e6),
        (r'тыс\\.?\\s*р\\.?', 1e3),
        (r'тыс\\.?\\s*руб\\.?', 1e3),
        (r'тыс', 1e3)
    ]

    def parse_number_with_unit(value) -> tuple:
        """Parse number with unit from a single cell (e.g. '98,1 МЛРД РУБ')."""
        if pd.isna(value) or value == '' or value == '-' or value == '—':
            return None, 1.0

        if isinstance(value, str):
            val_str = value.replace('\xa0', ' ').strip()

            # Look for units in the string
            for pattern, multiplier in unit_patterns:
                match = re.search(pattern, val_str, re.IGNORECASE)
                if match:
                    # Remove unit from string
                    clean_str = re.sub(pattern, '', val_str, flags=re.IGNORECASE).strip()
                    num = parse_russian_number(clean_str)
                    if num is not None:
                        return num, multiplier

            # If no unit - parse just the number
            num = parse_russian_number(val_str)
            return num, 1.0

        # For numeric values
        if isinstance(value, (int, float)):
            return float(value) if not pd.isna(value) else None, 1.0

        return None, 1.0

    def parse_russian_number(value) -> float:
        """Convert Russian number format (1 234,56 → 1234.56)."""
        if pd.isna(value) or value == '' or value == '-' or value == '—' or value == '–':
            return None

        if isinstance(value, (int, float)):
            return float(value) if not pd.isna(value) else None

        val_str = str(value).replace('\xa0', ' ').strip()

        # Remove currency symbols and junk at the end
        val_str = re.sub(r'[₽\$€%\s]+$', '', val_str)
        # Remove junk at the beginning
        val_str = re.sub(r'^[^\d\-\.]+', '', val_str)

        # Handle Russian format: 1 234,56 → 1234.56
        if ',' in val_str:
            parts = val_str.rsplit(',', 1)
            if len(parts) == 2 and parts[1].strip().isdigit() and len(parts[1].strip()) <= 3:
                integer_part = parts[0].replace(' ', '').replace('\xa0', '')
                decimal_part = parts[1].strip()
                val_str = f"{integer_part}.{decimal_part}"
            else:
                val_str = val_str.replace(',', '').replace(' ', '').replace('\xa0', '')
        else:
            val_str = val_str.replace(' ', '').replace('\xa0', '')

        try:
            num = float(val_str)
            if abs(num) > 1e16 or (abs(num) < 1e-6 and num != 0):
                return None
            return num
        except (ValueError, TypeError):
            return None

    def detect_units_in_context(row, col_idx: int) -> float:
        """Detect units from context (neighboring cells, headers)."""
        # Check current cell for units
        cell_value = row.iloc[col_idx] if col_idx < len(row) else None
        if isinstance(cell_value, str):
            for pattern, multiplier in unit_patterns:
                if re.search(pattern, cell_value, re.IGNORECASE):
                    return multiplier

        # Check next cell (often units are to the right)
        if col_idx + 1 < len(row):
            next_cell = row.iloc[col_idx + 1]
            if isinstance(next_cell, str):
                for pattern, multiplier in unit_patterns:
                    if re.search(pattern, next_cell, re.IGNORECASE):
                        return multiplier

        # Check previous cell
        if col_idx - 1 >= 0:
            prev_cell = row.iloc[col_idx - 1]
            if isinstance(prev_cell, str):
                for pattern, multiplier in unit_patterns:
                    if re.search(pattern, prev_cell, re.IGNORECASE):
                        return multiplier

        return 1.0

    def is_table_header(row) -> bool:
        """Check if row is a table header."""
        if row.empty or pd.isna(row.iloc[0]):
            return False
        first_cell = str(row.iloc[0]).strip().lower()
        return 'таблица #' in first_cell

    # Process each table
    for df in tables:
        if df.empty or len(df.columns) < 2:
            continue

        current_units = {}  # Units for columns

        # Go through rows
        for idx in range(len(df)):
            row = df.iloc[idx]

            # Skip headers and empty rows
            if is_table_header(row) or row.isna().all():
                continue

            # Look for units in the row (for all columns)
            for col_idx in range(min(10, len(row))):
                cell = row.iloc[col_idx]
                if pd.isna(cell) or not isinstance(cell, str):
                    continue
                cell_upper = cell.upper().strip()
                for pattern, multiplier in unit_patterns:
                    if re.search(pattern.upper(), cell_upper):
                        current_units[col_idx] = multiplier
                        break

            # Get non-empty cells
            non_empty = [(i, cell) for i, cell in enumerate(row)
                         if pd.notna(cell) and str(cell).strip() != '' and len(str(cell).strip()) > 1]

            if len(non_empty) < 2:
                continue

            # Combine first 1-3 cells into indicator name
            indicator_parts = []
            value_start_idx = 0
            for i, (col_idx, cell) in enumerate(non_empty[:3]):
                cell_str = str(cell).strip()
                if re.match(r'^[\d\s\.,%\-]+$', cell_str) or len(cell_str) < 3:
                    value_start_idx = i
                    break
                indicator_parts.append(cell_str)

            if not indicator_parts:
                continue

            indicator_name = ' '.join(indicator_parts).lower()

            # Look for pattern matches
            for param_name, patterns in financial_patterns.items():
                if any(re.search(pattern, indicator_name, re.IGNORECASE) for pattern in patterns):
                    # Extract values
                    for j in range(value_start_idx, len(non_empty)):
                        col_idx, cell_value = non_empty[j]

                        # Parse number with units from the cell itself
                        num, inline_multiplier = parse_number_with_unit(cell_value)
                        if num is None:
                            continue

                        # Determine multiplier from context
                        context_multiplier = current_units.get(col_idx,
                                                               detect_units_in_context(row, col_idx))

                        # Final multiplier
                        multiplier = inline_multiplier * context_multiplier

                        # For percentage indicators don't apply multiplier unless explicitly stated
                        is_percentage = param_name in [
                            'roa', 'roe', 'net_interest_margin', 'cost_to_income_ratio',
                            'non_performing_loan_ratio', 'capital_adequacy_ratio', 'churn_rate', 
                            'retention_rate', 'digital_penetration', 'mobile_penetration', 
                            'wallet_share', 'credit_cost', 'loan_loss_provision_coverage',
                            'return_on_net_assets', 'return_on_average_total_assets',
                            'return_on_net_assets_after_deducting_non_recurring'
                        ]

                        if is_percentage:
                            # If value > 100 and no explicit units - it's not a percentage
                            if num > 100 and multiplier == 1.0:
                                continue
                            # For percentages multiplier is always 1.0 (unless explicitly stated)
                            final_value = num
                        else:
                            # For absolute values apply multiplier
                            final_value = num * multiplier

                            # Heuristic: if indicator is assets/loans/deposits and value < 1000
                            # and no explicit units - assume billions
                            if (param_name in ['total_assets', 'loans_to_customers', 'deposits_from_customers', 'net_income',
                                               'operating_income']
                                    and final_value < 1e12  # less than 1 trillion
                                    and multiplier == 1.0
                                    and num > 1):
                                final_value *= 1e9

                        # Store the most accurate value (last one in table)
                        financial_data[param_name] = final_value

                    break

    return financial_data