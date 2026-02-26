"""Bank Stability Index (BSI) calculation module."""

import pandas as pd
from typing import Dict, Tuple, Any
from banking_analysis_platform.config.patterns import RATIO_THRESHOLDS


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


def calculate_bsi(financial_data: Dict[str, Any], ratios: Dict[str, Tuple[float, str]]) -> Tuple[float, str]:
    """
    Calculate Bank Stability Index (BSI) as weighted average of normalized ratios.

    Args:
        financial_data: Dictionary with financial data
        ratios: Dictionary with calculated ratios
        
    Returns:
        Tuple of (bsi_score, interpretation)
    """
    # Weights for different ratios (subject to adjustment based on importance)
    weights = {
        'capital_adequacy_ratio': 0.20,      # Capital strength
        'instant_liquidity_ratio': 0.15,     # Immediate liquidity
        'current_liquidity_ratio': 0.15,     # Overall liquidity
        'roe': 0.15,                         # Profitability
        'roa': 0.15,                         # Asset efficiency
        'net_interest_margin': 0.10,         # Interest margin
        'non_performing_loan_ratio': 0.10    # Asset quality (reversed scale)
    }

    # Normalize each ratio to 0-1 scale
    normalized_scores = {}
    for ratio_name in weights.keys():
        if ratio_name in ratios:
            ratio_value, _ = ratios[ratio_name]
            
            if ratio_name == 'non_performing_loan_ratio':
                # For problem loans, lower is better (reverse scoring)
                min_thr, max_thr = RATIO_THRESHOLDS[ratio_name]
                normalized_scores[ratio_name] = normalize_score(
                    ratio_value, min_thr, max_thr, reverse=True
                )
            else:
                # For other ratios, higher is better
                if ratio_name in RATIO_THRESHOLDS:
                    min_thr, max_thr = RATIO_THRESHOLDS[ratio_name]
                    normalized_scores[ratio_name] = normalize_score(
                        ratio_value, min_thr, max_thr, reverse=False
                    )
                else:
                    # Default normalization if threshold not defined
                    normalized_scores[ratio_name] = min(ratio_value, 1.0) if ratio_value >= 0 else 0.0
        else:
            # Default to 0 if ratio not calculated
            normalized_scores[ratio_name] = 0.0

    # Calculate weighted sum
    bsi = 0.0
    total_weight = 0.0
    for ratio_name, weight in weights.items():
        bsi += normalized_scores[ratio_name] * weight
        total_weight += weight

    # Ensure we have a valid BSI
    if total_weight > 0:
        bsi = bsi / total_weight
    else:
        bsi = 0.0

    # Interpret BSI
    if bsi >= 0.8:
        interpretation = f"Отличная устойчивость: {bsi:.2f}/1.00"
    elif bsi >= 0.6:
        interpretation = f"Хорошая устойчивость: {bsi:.2f}/1.00"
    elif bsi >= 0.4:
        interpretation = f"Удовлетворительная устойчивость: {bsi:.2f}/1.00"
    elif bsi >= 0.2:
        interpretation = f"Пониженная устойчивость: {bsi:.2f}/1.00"
    else:
        interpretation = f"Критическая устойчивость: {bsi:.2f}/1.00"

    return bsi, interpretation