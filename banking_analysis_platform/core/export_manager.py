"""Export manager for banking analysis platform."""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from io import BytesIO
import zipfile
from datetime import datetime
import json


class ReportExportManager:
    """Manager for exporting analysis reports in various formats."""
    
    def __init__(self, banks_data: Dict[str, Any]):
        """
        Initialize the export manager.
        
        Args:
            banks_data: Dictionary containing analysis data for all banks
        """
        self.banks_data = banks_data
    
    def generate_individual_report(self, bank_name: str, formats: List[str]) -> Dict[str, bytes]:
        """
        Generate individual report for a specific bank.
        
        Args:
            bank_name: Name of the bank to generate report for
            formats: List of desired formats (e.g., ['.xlsx', '.csv', '.txt'])
            
        Returns:
            Dictionary mapping file names to file contents (bytes)
        """
        files = {}
        bank_data = self.banks_data[bank_name]
        
        for fmt in formats:
            if fmt == '.xlsx':
                # Create Excel file with multiple sheets
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    # Financial indicators sheet
                    financial_data = bank_data.get('financial_data', {})
                    if financial_data:
                        df_financial = pd.DataFrame(list(financial_data.items()), 
                                                  columns=['Indicator', 'Value'])
                        df_financial.to_excel(writer, sheet_name='Финансовые показатели', 
                                             index=False)
                    
                    # Ratios sheet
                    ratios = bank_data.get('ratios', {})
                    if ratios:
                        ratio_data = []
                        for key, (value, interpretation) in ratios.items():
                            ratio_data.append({
                                'Ratio': key,
                                'Value': value,
                                'Interpretation': interpretation
                            })
                        df_ratios = pd.DataFrame(ratio_data)
                        df_ratios.to_excel(writer, sheet_name='Коэффициенты', index=False)
                    
                    # BSI sheet
                    bsi = bank_data.get('bsi', (0, ''))
                    if isinstance(bsi, tuple):
                        bsi_value, bsi_interp = bsi
                    else:
                        bsi_value, bsi_interp = bsi, 'N/A'
                    
                    df_bsi = pd.DataFrame({
                        'BSI Score': [bsi_value],
                        'Interpretation': [bsi_interp]
                    })
                    df_bsi.to_excel(writer, sheet_name='BSI Индекс', index=False)
                
                buffer.seek(0)
                files[f"{bank_name}_отчёт_{datetime.now().strftime('%Y%m%d')}.xlsx"] = buffer.getvalue()
            
            elif fmt == '.csv':
                # Create CSV with financial data
                financial_data = bank_data.get('financial_data', {})
                if financial_data:
                    df = pd.DataFrame(list(financial_data.items()), 
                                     columns=['Indicator', 'Value'])
                    csv_bytes = df.to_csv(index=False).encode('utf-8-sig')
                    files[f"{bank_name}_фин_данные_{datetime.now().strftime('%Y%m%d')}.csv"] = csv_bytes
            
            elif fmt == '.txt':
                # Create text report
                report_text = self._generate_text_report(bank_name, bank_data)
                txt_bytes = report_text.encode('utf-8')
                files[f"{bank_name}_отчёт_{datetime.now().strftime('%Y%m%d')}.txt"] = txt_bytes
        
        return files
    
    def generate_summary_report(self, formats: List[str]) -> Dict[str, bytes]:
        """
        Generate summary report for all banks.
        
        Args:
            formats: List of desired formats
            
        Returns:
            Dictionary mapping file names to file contents (bytes)
        """
        files = {}
        
        # Prepare summary data
        summary_data = []
        for bank_name, data in self.banks_data.items():
            bsi_score = data.get('bsi', (0, ''))[0] if isinstance(data.get('bsi'), tuple) else data.get('bsi', 0)
            ratios = data.get('ratios', {})
            
            summary_data.append({
                '🏦 Банк': bank_name,
                '📅 Год': data.get('year', 'N/A'),
                '📊 BSI Индекс': f"{bsi_score:.3f}",
                '💰 Активы (млрд ₽)': f"{data.get('financial_data', {}).get('total_assets', 0) / 1e9:.2f}",
                '🏛️ Капитал (млрд ₽)': f"{data.get('financial_data', {}).get('equity', 0) / 1e9:.2f}",
                '📈 ROE (%)': f"{ratios.get('roe', (0, ''))[0] * 100:.2f}" if isinstance(ratios.get('roe'), tuple) else f"{ratios.get('roe', 0) * 100:.2f}",
                '💧 Ликвидность': f"{ratios.get('current_liquidity', (0, ''))[0]:.2f}" if isinstance(ratios.get('current_liquidity'), tuple) else f"{ratios.get('current_liquidity', 0):.2f}",
            })
        
        df_summary = pd.DataFrame(summary_data)
        df_summary = df_summary.sort_values('📊 BSI Индекс', ascending=False)
        df_summary.insert(0, '🥇 Место', range(1, len(df_summary) + 1))
        
        for fmt in formats:
            if fmt == '.xlsx':
                buffer = BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    # Summary table
                    df_summary.to_excel(writer, sheet_name='Сводная таблица', index=False)
                    
                    # Ratios comparison
                    ratios_comparison = []
                    for bank_name, data in self.banks_data.items():
                        ratios = data.get('ratios', {})
                        row = {'Банк': bank_name}
                        for ratio_name, (value, interp) in ratios.items():
                            row[ratio_name] = value
                        ratios_comparison.append(row)
                    
                    if ratios_comparison:
                        df_ratios_comp = pd.DataFrame(ratios_comparison)
                        df_ratios_comp.to_excel(writer, sheet_name='Сравнение коэффициентов', index=False)
                    
                    # BSI ranking
                    bsi_ranking = []
                    for bank_name, data in self.banks_data.items():
                        bsi = data.get('bsi', (0, ''))
                        if isinstance(bsi, tuple):
                            bsi_value = bsi[0]
                            bsi_interp = bsi[1]
                        else:
                            bsi_value = bsi
                            bsi_interp = 'N/A'
                        
                        bsi_ranking.append({
                            'Банк': bank_name,
                            'BSI': bsi_value,
                            'Интерпретация': bsi_interp
                        })
                    
                    if bsi_ranking:
                        df_bsi_rank = pd.DataFrame(bsi_ranking)
                        df_bsi_rank = df_bsi_rank.sort_values('BSI', ascending=False)
                        df_bsi_rank.insert(0, 'Место', range(1, len(df_bsi_rank) + 1))
                        df_bsi_rank.to_excel(writer, sheet_name='Рейтинг BSI', index=False)
                
                buffer.seek(0)
                files[f"сводный_отчёт_{datetime.now().strftime('%Y%m%d')}.xlsx"] = buffer.getvalue()
            
            elif fmt == '.csv':
                csv_bytes = df_summary.to_csv(index=False).encode('utf-8-sig')
                files[f"сводный_отчёт_{datetime.now().strftime('%Y%m%d')}.csv"] = csv_bytes
        
        return files
    
    def generate_ratios_report(self, selected_banks: List[str], formats: List[str]) -> Dict[str, bytes]:
        """
        Generate report with only ratios for selected banks.
        
        Args:
            selected_banks: List of bank names to include
            formats: List of desired formats
            
        Returns:
            Dictionary mapping file names to file contents (bytes)
        """
        files = {}
        
        # Prepare ratios data
        ratios_data = []
        for bank_name in selected_banks:
            if bank_name in self.banks_data:
                data = self.banks_data[bank_name]
                ratios = data.get('ratios', {})
                
                row = {'Банк': bank_name}
                for ratio_name, (value, interp) in ratios.items():
                    row[f'{ratio_name}_value'] = value
                    row[f'{ratio_name}_interp'] = interp
                ratios_data.append(row)
        
        if ratios_data:
            df_ratios = pd.DataFrame(ratios_data)
            
            for fmt in formats:
                if fmt == '.xlsx':
                    buffer = BytesIO()
                    df_ratios.to_excel(buffer, sheet_name='Коэффициенты', index=False)
                    buffer.seek(0)
                    files[f"коэффициенты_{datetime.now().strftime('%Y%m%d')}.xlsx"] = buffer.getvalue()
                
                elif fmt == '.csv':
                    csv_bytes = df_ratios.to_csv(index=False).encode('utf-8-sig')
                    files[f"коэффициенты_{datetime.now().strftime('%Y%m%d')}.csv"] = csv_bytes
        
        return files
    
    def generate_full_archive(self) -> Dict[str, bytes]:
        """
        Generate a ZIP archive with all available reports.
        
        Returns:
            Dictionary mapping file names to file contents (bytes)
        """
        files = {}
        
        # Create a ZIP archive
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add individual reports
            for bank_name in self.banks_data.keys():
                bank_files = self.generate_individual_report(bank_name, ['.xlsx'])
                for filename, content in bank_files.items():
                    zip_file.writestr(f"individual/{filename}", content)
            
            # Add summary report
            summary_files = self.generate_summary_report(['.xlsx'])
            for filename, content in summary_files.items():
                zip_file.writestr(f"summary/{filename}", content)
            
            # Add ratios report
            ratios_files = self.generate_ratios_report(list(self.banks_data.keys()), ['.xlsx'])
            for filename, content in ratios_files.items():
                zip_file.writestr(f"ratios/{filename}", content)
        
        buffer.seek(0)
        files[f"архив_отчётов_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"] = buffer.getvalue()
        
        return files
    
    def _generate_text_report(self, bank_name: str, bank_data: Dict[str, Any]) -> str:
        """
        Generate a text-based report for a bank.
        
        Args:
            bank_name: Name of the bank
            bank_data: Bank's analysis data
            
        Returns:
            Formatted text report
        """
        report = []
        report.append("=" * 60)
        report.append(f"БАНКОВСКИЙ АНАЛИТИЧЕСКИЙ ОТЧЕТ - {bank_name.upper()}")
        report.append("=" * 60)
        
        # Financial Summary
        report.append("\nФИНАНСОВЫЙ ОБЗОР:")
        report.append("-" * 30)
        financial_data = bank_data.get('financial_data', {})
        report.append(f"Общие активы: {financial_data.get('total_assets', 0):,.2f}")
        report.append(f"Общие обязательства: {financial_data.get('total_liabilities', 0):,.2f}")
        report.append(f"Собственный капитал: {financial_data.get('equity', 0):,.2f}")
        report.append(f"Чистая прибыль: {financial_data.get('net_income', 0):,.2f}")
        
        # Individual Ratios Analysis
        all_ratios = bank_data.get('ratios', {})
        
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
        bsi_score = bank_data.get('bsi', (0, ''))
        if isinstance(bsi_score, tuple):
            bsi_value, bsi_interp = bsi_score
        else:
            bsi_value, bsi_interp = bsi_score, 'N/A'
        
        report.append(f"\nИНДЕКС БАНКОВСКОЙ УСТОЙЧИВОСТИ (BSI): {bsi_interp}")
        
        # Final Assessment
        report.append("\nОБЩАЯ ОЦЕНКА:")
        report.append("-" * 15)
        
        if bsi_value >= 0.8:
            report.append("Банк демонстрирует ОТЛИЧНУЮ финансовую устойчивость.")
            report.append("Рекомендации: Продолжать текущую стратегию развития.")
        elif bsi_value >= 0.6:
            report.append("Банк имеет ХОРОШУЮ финансовую устойчивость.")
            report.append("Рекомендации: Мониторить ключевые показатели.")
        elif bsi_value >= 0.4:
            report.append("Банк имеет УДОВЛЕТВОРИТЕЛЬНУЮ финансовую устойчивость.")
            report.append("Рекомендации: Рассмотреть меры по улучшению показателей.")
        elif bsi_value >= 0.2:
            report.append("Банк имеет ПОНЖЕННУЮ финансовую устойчивость.")
            report.append("Рекомендации: Необходимы срочные меры по улучшению показателей.")
        else:
            report.append("БАНК НАХОДИТСЯ В КРИТИЧЕСКОМ ФИНАНСОВОМ СОСТОЯНИИ.")
            report.append("Рекомендации: Требуется немедленное вмешательство для стабилизации.")
        
        report.append(f"\nДата анализа: {pd.Timestamp.now().date()}")
        report.append("=" * 60)
        
        return "\n".join(report)