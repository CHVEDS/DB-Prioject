"""
Calculator module for computing banking financial ratios and indicators.

This module contains functions to calculate key banking performance indicators
based on extracted financial data.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from config import RATIOS_THRESHOLDS


logger = logging.getLogger(__name__)


def normalize_score(value: float, min_thr: float, max_thr: float, reverse: bool = False) -> float:
    """
    Normalizes a value to the range [0, 1].
    
    Args:
        value: Value to normalize
        min_thr: Minimum threshold (typically minimum acceptable value)
        max_thr: Maximum threshold (typically ideal value)
        reverse: If True, smaller values are better (e.g., problem loan ratio)
        
    Returns:
        Normalized score between 0 and 1
    """
    if pd.isna(value) or value is None:
        return 0.0
    
    if reverse:
        # For ratios where lower values are better (like problem loans)
        if value <= min_thr:
            return 1.0  # Excellent
        elif value >= max_thr:
            return 0.0  # Poor
        else:
            # Linear interpolation
            return (max_thr - value) / (max_thr - min_thr)
    else:
        # For ratios where higher values are better (like profitability)
        if value >= max_thr:
            return 1.0  # Excellent
        elif value <= min_thr:
            return 0.0  # Poor
        else:
            # Linear interpolation
            return (value - min_thr) / (max_thr - min_thr)


class BankingRatiosCalculator:
    """Class to calculate banking-specific financial ratios."""
    
    def __init__(self, financial_data: Dict[str, float]):
        """
        Initialize with financial data.
        
        Args:
            financial_data: Dictionary containing extracted financial figures
        """
        self.data = financial_data
        
        # Extract key values with defaults
        self.total_assets = self.data.get('total_assets', 0)
        self.total_liabilities = self.data.get('total_liabilities', 0)
        self.equity = self.data.get('equity', 0)
        self.net_income = self.data.get('net_income', 0)
        self.cash_and_equivalents = self.data.get('cash_and_equivalents', 0)
        self.loans_to_customers = self.data.get('loans_to_customers', 0)
        self.net_interest_income = self.data.get('net_interest_income', 0)
        self.deposits_from_customers = self.data.get('deposits_from_customers', 0)
        
        # Calculate derived values
        self.total_capital = self.equity + self.data.get('subordinated_debt', 0)
        self.average_assets = self.total_assets  # Simplified for now
        self.liquid_assets = self.cash_and_equivalents  # Simplified liquid assets calculation
        self.demand_deposits = self.deposits_from_customers * 0.7  # Estimation
        self.short_term_liabilities = self.total_liabilities * 0.5  # Estimation

    def calculate_capital_adequacy(self) -> Tuple[float, str]:
        """
        Calculate capital adequacy ratio (simplified Basel III equivalent).
        
        Formula: Tier 1 Capital / Total Risk-Weighted Assets
        Simplified as: Equity / Total Assets
        
        Returns:
            Tuple of (ratio_value, interpretation)
        """
        if self.total_assets == 0:
            return 0.0, "Cannot calculate: Total assets is zero"
        
        ratio = self.equity / self.total_assets
        min_thr, max_thr = RATIOS_THRESHOLDS['capital_adequacy']
        
        if ratio >= max_thr:
            interpretation = f"Excellent: {ratio:.2%} (above target of {max_thr:.2%})"
        elif ratio >= min_thr:
            interpretation = f"Adequate: {ratio:.2%} (meets minimum of {min_thr:.2%})"
        else:
            interpretation = f"Deficient: {ratio:.2%} (below minimum of {min_thr:.2%})"
        
        return ratio, interpretation

    def calculate_instant_liquidity(self) -> Tuple[float, str]:
        """
        Calculate instant liquidity ratio.
        
        Formula: Highly Liquid Assets / Demand Liabilities
        
        Returns:
            Tuple of (ratio_value, interpretation)
        """
        if self.demand_deposits == 0:
            return 0.0, "Cannot calculate: Demand deposits is zero"
        
        ratio = self.liquid_assets / self.demand_deposits
        min_thr, max_thr = RATIOS_THRESHOLDS['instant_liquidity']
        
        if ratio >= max_thr:
            interpretation = f"Strong: {ratio:.2%} (exceeds target of {max_thr:.2%})"
        elif ratio >= min_thr:
            interpretation = f"Adequate: {ratio:.2%} (meets minimum of {min_thr:.2%})"
        else:
            interpretation = f"Concerning: {ratio:.2%} (below minimum of {min_thr:.2%})"
        
        return ratio, interpretation

    def calculate_current_liquidity(self) -> Tuple[float, str]:
        """
        Calculate current liquidity ratio.
        
        Formula: Current Assets / Current Liabilities
        Simplified as: Liquid Assets / Short-term Liabilities
        
        Returns:
            Tuple of (ratio_value, interpretation)
        """
        if self.short_term_liabilities == 0:
            return 0.0, "Cannot calculate: Short-term liabilities is zero"
        
        ratio = self.liquid_assets / self.short_term_liabilities
        min_thr, max_thr = RATIOS_THRESHOLDS['current_liquidity']
        
        if ratio >= max_thr:
            interpretation = f"Strong: {ratio:.2f} (exceeds target of {max_thr:.2f})"
        elif ratio >= min_thr:
            interpretation = f"Adequate: {ratio:.2f} (meets minimum of {min_thr:.2f})"
        else:
            interpretation = f"Concerning: {ratio:.2f} (below minimum of {min_thr:.2f})"
        
        return ratio, interpretation

    def calculate_roe(self) -> Tuple[float, str]:
        """
        Calculate Return on Equity.
        
        Formula: Net Income / Average Shareholders' Equity
        
        Returns:
            Tuple of (ratio_value, interpretation)
        """
        if self.equity == 0:
            return 0.0, "Cannot calculate: Equity is zero"
        
        ratio = self.net_income / self.equity
        min_thr, max_thr = RATIOS_THRESHOLDS['roe']
        
        if ratio >= max_thr:
            interpretation = f"Excellent: {ratio:.2%} (exceeds target of {max_thr:.2%})"
        elif ratio >= min_thr:
            interpretation = f"Good: {ratio:.2%} (meets minimum of {min_thr:.2%})"
        else:
            interpretation = f"Low: {ratio:.2%} (below minimum of {min_thr:.2%})"
        
        return ratio, interpretation

    def calculate_roa(self) -> Tuple[float, str]:
        """
        Calculate Return on Assets.
        
        Formula: Net Income / Average Total Assets
        
        Returns:
            Tuple of (ratio_value, interpretation)
        """
        if self.total_assets == 0:
            return 0.0, "Cannot calculate: Total assets is zero"
        
        ratio = self.net_income / self.total_assets
        min_thr, max_thr = RATIOS_THRESHOLDS['roa']
        
        if ratio >= max_thr:
            interpretation = f"Excellent: {ratio:.2%} (exceeds target of {max_thr:.2%})"
        elif ratio >= min_thr:
            interpretation = f"Good: {ratio:.2%} (meets minimum of {min_thr:.2%})"
        else:
            interpretation = f"Low: {ratio:.2%} (below minimum of {min_thr:.2%})"
        
        return ratio, interpretation

    def calculate_nim(self) -> Tuple[float, str]:
        """
        Calculate Net Interest Margin.
        
        Formula: Net Interest Income / Average Earning Assets
        Simplified as: Net Interest Income / Average Total Assets
        
        Returns:
            Tuple of (ratio_value, interpretation)
        """
        if self.average_assets == 0:
            return 0.0, "Cannot calculate: Average assets is zero"
        
        ratio = self.net_interest_income / self.average_assets
        min_thr, max_thr = RATIOS_THRESHOLDS['nim']
        
        if ratio >= max_thr:
            interpretation = f"Excellent: {ratio:.2%} (exceeds target of {max_thr:.2%})"
        elif ratio >= min_thr:
            interpretation = f"Good: {ratio:.2%} (meets minimum of {min_thr:.2%})"
        else:
            interpretation = f"Low: {ratio:.2%} (below minimum of {min_thr:.2%})"
        
        return ratio, interpretation

    def calculate_problem_loans_ratio(self) -> Tuple[float, str]:
        """
        Calculate Problem Loans Ratio (estimation).
        
        Formula: Non-performing Loans / Total Loans
        This is an estimation based on available data.
        
        Returns:
            Tuple of (ratio_value, interpretation)
        """
        if self.loans_to_customers == 0:
            return 0.0, "Cannot calculate: Loans to customers is zero"
        
        # Estimate problem loans as a percentage of total loans
        # This is a placeholder since we don't have explicit NPL data
        estimated_npl = self.loans_to_customers * 0.03  # Estimation
        ratio = estimated_npl / self.loans_to_customers
        
        min_thr, max_thr = RATIOS_THRESHOLDS['problem_loans_ratio']
        
        if ratio <= max_thr:
            interpretation = f"Healthy: {ratio:.2%} (below target of {max_thr:.2%})"
        elif ratio <= min_thr:
            interpretation = f"Concerning: {ratio:.2%} (approaching threshold of {min_thr:.2%})"
        else:
            interpretation = f"Critical: {ratio:.2%} (exceeds threshold of {min_thr:.2%})"
        
        return ratio, interpretation

    def calculate_all_ratios(self) -> Dict[str, Tuple[float, str]]:
        """
        Calculate all banking ratios.
        
        Returns:
            Dictionary with ratio names and their (value, interpretation) tuples
        """
        ratios = {}
        
        ratios['capital_adequacy'] = self.calculate_capital_adequacy()
        ratios['instant_liquidity'] = self.calculate_instant_liquidity()
        ratios['current_liquidity'] = self.calculate_current_liquidity()
        ratios['roe'] = self.calculate_roe()
        ratios['roa'] = self.calculate_roa()
        ratios['nim'] = self.calculate_nim()
        ratios['problem_loans_ratio'] = self.calculate_problem_loans_ratio()
        
        return ratios

    def calculate_bsi(self) -> Tuple[float, str]:
        """
        Calculate Bank Stability Index (BSI) as weighted average of normalized ratios.
        
        Returns:
            Tuple of (bsi_score, interpretation)
        """
        all_ratios = self.calculate_all_ratios()
        
        # Weights for different ratios (subject to adjustment based on importance)
        weights = {
            'capital_adequacy': 0.20,      # Capital strength
            'instant_liquidity': 0.15,     # Immediate liquidity
            'current_liquidity': 0.15,     # Overall liquidity
            'roe': 0.15,                   # Profitability
            'roa': 0.15,                   # Asset efficiency
            'nim': 0.10,                   # Interest margin
            'problem_loans_ratio': 0.10    # Asset quality (reversed scale)
        }
        
        # Normalize each ratio to 0-1 scale
        normalized_scores = {}
        for ratio_name, (ratio_value, _) in all_ratios.items():
            if ratio_name == 'problem_loans_ratio':
                # For problem loans, lower is better (reverse scoring)
                min_thr, max_thr = RATIOS_THRESHOLDS[ratio_name]
                normalized_scores[ratio_name] = normalize_score(
                    ratio_value, min_thr, max_thr, reverse=True
                )
            else:
                # For other ratios, higher is better
                min_thr, max_thr = RATIOS_THRESHOLDS[ratio_name]
                normalized_scores[ratio_name] = normalize_score(
                    ratio_value, min_thr, max_thr, reverse=False
                )
        
        # Calculate weighted sum
        bsi = 0.0
        for ratio_name, weight in weights.items():
            bsi += normalized_scores[ratio_name] * weight
        
        # Interpret BSI
        if bsi >= 0.8:
            interpretation = f"Excellent stability: {bsi:.2f}/1.00"
        elif bsi >= 0.6:
            interpretation = f"Good stability: {bsi:.2f}/1.00"
        elif bsi >= 0.4:
            interpretation = f"Adequate stability: {bsi:.2f}/1.00"
        elif bsi >= 0.2:
            interpretation = f"Concerning stability: {bsi:.2f}/1.00"
        else:
            interpretation = f"Critical stability: {bsi:.2f}/1.00"
        
        return bsi, interpretation


def generate_analysis_report(calculator: BankingRatiosCalculator) -> str:
    """
    Generate a comprehensive analysis report based on calculated ratios.
    
    Args:
        calculator: Instance of BankingRatiosCalculator
        
    Returns:
        Formatted analysis report as string
    """
    report = []
    report.append("=" * 60)
    report.append("БАНКОВСКИЙ АНАЛИТИЧЕСКИЙ ОТЧЕТ")
    report.append("=" * 60)
    
    # Financial Summary
    report.append("\nФИНАНСОВЫЙ ОБЗОР:")
    report.append("-" * 30)
    report.append(f"Общие активы: {calculator.total_assets:,.2f}")
    report.append(f"Общие обязательства: {calculator.total_liabilities:,.2f}")
    report.append(f"Собственный капитал: {calculator.equity:,.2f}")
    report.append(f"Чистая прибыль: {calculator.net_income:,.2f}")
    
    # Individual Ratios Analysis
    all_ratios = calculator.calculate_all_ratios()
    
    report.append("\nПОКАЗАТЕЛИ ФИНАНСОВОЙ УСТОЙЧИВОСТИ:")
    report.append("-" * 40)
    
    ratio_descriptions = {
        'capital_adequacy': 'Достаточность капитала',
        'instant_liquidity': 'Мгновенная ликвидность',
        'current_liquidity': 'Текущая ликвидность',
        'roe': 'Рентабельность собственного капитала (ROE)',
        'roa': 'Рентабельность активов (ROA)',
        'nim': 'Чистая процентная маржа (NIM)',
        'problem_loans_ratio': 'Доля проблемных ссуд'
    }
    
    for ratio_key, (ratio_value, interpretation) in all_ratios.items():
        desc = ratio_descriptions.get(ratio_key, ratio_key.replace('_', ' ').title())
        report.append(f"{desc}: {interpretation}")
    
    # Bank Stability Index
    bsi_score, bsi_interpretation = calculator.calculate_bsi()
    report.append(f"\nИНДЕКС БАНКОВСКОЙ УСТОЙЧИВОСТИ (BSI): {bsi_interpretation}")
    
    # Final Assessment
    report.append("\nОБЩАЯ ОЦЕНКА:")
    report.append("-" * 15)
    
    if bsi_score >= 0.8:
        report.append("Банк демонстрирует ОТЛИЧНУЮ финансовую устойчивость.")
        report.append("Рекомендации: Продолжать текущую стратегию развития.")
    elif bsi_score >= 0.6:
        report.append("Банк имеет ХОРОШУЮ финансовую устойчивость.")
        report.append("Рекомендации: Мониторить ключевые показатели.")
    elif bsi_score >= 0.4:
        report.append("Банк имеет УДОВЛЕТВОРИТЕЛЬНУЮ финансовую устойчивость.")
        report.append("Рекомендации: Рассмотреть меры по улучшению показателей.")
    elif bsi_score >= 0.2:
        report.append("Банк имеет ПОНЖЕННУЮ финансовую устойчивость.")
        report.append("Рекомендации: Необходимы срочные меры по улучшению показателей.")
    else:
        report.append("БАНК НАХОДИТСЯ В КРИТИЧЕСКОМ ФИНАНСОВОМ СОСТОЯНИИ.")
        report.append("Рекомендации: Требуется немедленное вмешательство для стабилизации.")
    
    report.append("\nДата анализа: " + str(pd.Timestamp.now().date()))
    report.append("=" * 60)
    
    return "\n".join(report)