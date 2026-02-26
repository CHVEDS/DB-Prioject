"""
Streamlit web application for automated analysis of banking annual reports.

This application allows users to upload PDF files of bank annual reports,
extracts financial data, calculates key banking ratios, and generates
comprehensive analytical reports.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Optional
import tempfile

from config import SUPPORTED_FORMATS
from magic_pdf_parser import parse_pdf_with_magic_pdf, aggregate_financial_data
from calculator import BankingRatiosCalculator, generate_analysis_report


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main function to run the Streamlit application."""
    st.set_page_config(
        page_title="Аналитический центр банковской устойчивости",
        page_icon="🏦",
        layout="wide"
    )
    
    st.title("🏦 Аналитический центр банковской устойчивости")
    st.markdown("---")
    
    st.header("Анализ годовых отчетов банков")
    st.write("""
    Загрузите PDF-файл годового отчета банка для автоматического анализа финансовой устойчивости.
    Приложение извлекает данные из баланса и отчета о прибылях и убытках, 
    рассчитывает ключевые банковские коэффициенты и формирует аналитический отчет.
    """)
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Выберите PDF-файл(ы) годового отчета банка",
        type=["pdf"],
        accept_multiple_files=True,
        help="Поддерживаются только PDF файлы годовых отчетов банков"
    )
    
    # Use the first file if multiple are uploaded
    uploaded_file = uploaded_files[0] if uploaded_files else None
    
    if uploaded_file is not None:
        st.success(f"Файл загружен: {uploaded_file.name}")
        
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            temp_path = tmp_file.name
        
        try:
            # Process button
            if st.button("📊 Анализировать отчет", type="primary"):
                with st.spinner("Идет анализ отчета... Это может занять несколько минут."):
                    
                    # Parse the PDF
                    tables = parse_pdf_with_magic_pdf(temp_path)
                    
                    if not tables:
                        st.error("Не удалось извлечь финансовые данные из загруженного файла. "
                                "Проверьте, что это годовой отчет банка в формате PDF.")
                        logger.error(f"No tables extracted from {uploaded_file.name}")
                        return
                    
                    # Log the tables for debugging
                    logger.info(f"Extracted {len(tables)} tables from {uploaded_file.name}")
                    for table_name in tables.keys():
                        logger.info(f"Table found: {table_name}")
                    
                    # Aggregate financial data
                    financial_data = aggregate_financial_data(tables)
                    
                    if not financial_data:
                        st.error("Не удалось извлечь достаточное количество данных для анализа. "
                                "Проверьте, что отчет содержит баланс и отчет о прибылях и убытках.")
                        logger.error(f"No financial data aggregated from {uploaded_file.name}")
                        return
                    
                    # Log the financial data for debugging
                    logger.info(f"Financial data keys: {list(financial_data.keys())}")
                    
                    # Calculate ratios
                    calculator = BankingRatiosCalculator(financial_data)
                    
                    # Display results
                    display_results(calculator, financial_data, tables)
        
        except Exception as e:
            st.error(f"Произошла ошибка при обработке файла: {str(e)}")
            logger.error(f"Error processing file: {str(e)}")
        
        finally:
            # Clean up temporary file
            Path(temp_path).unlink(missing_ok=True)


def display_results(calculator: BankingRatiosCalculator, financial_data: Dict, tables: Dict):
    """Display the analysis results in the Streamlit interface."""
    
    # Financial summary section
    st.header("📋 Финансовый обзор")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Общие активы",
            value=f"{calculator.total_assets:,.0f}",
            delta=None
        )
    
    with col2:
        st.metric(
            label="Собственный капитал",
            value=f"{calculator.equity:,.0f}",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Чистая прибыль",
            value=f"{calculator.net_income:,.0f}",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Кредиты клиентам",
            value=f"{calculator.loans_to_customers:,.0f}",
            delta=None
        )
    
    # Extracted data table
    st.subheader("🔍 Извлеченные ключевые статьи баланса")
    
    # Prepare comparison data
    comparison_data = []
    
    # Add some key items to comparison
    key_items = {
        "total_assets": "Общие активы",
        "total_liabilities": "Общие обязательства", 
        "equity": "Собственный капитал",
        "cash_and_equivalents": "Денежные средства",
        "loans_to_customers": "Кредиты клиентам"
    }
    
    for key, label in key_items.items():
        if key in financial_data:
            current_value = financial_data[key]
            comparison_data.append({
                "Статья": label,
                "Текущий период": f"{current_value:,.0f}",
                "Прошлый период": "N/A",  # Placeholder - in real implementation would compare years
                "Изменение (%)": "N/A"   # Placeholder
            })
    
    if comparison_data:
        df_comparison = pd.DataFrame(comparison_data)
        st.dataframe(df_comparison, use_container_width=True, hide_index=True)
    else:
        st.info("Не удалось извлечь ключевые статьи баланса")
    
    # Digital banking indicators section
    st.subheader("📱 Показатели цифрового банкинга")
    
    digital_indicators = {
        "number_corporate_online_banking_customers": "Количество корпоративных клиентов онлайн-банкинга",
        "number_personal_online_banking_customers": "Количество частных клиентов онлайн-банкинга",
        "number_mobile_banking_customers": "Количество пользователей мобильного банкинга",
        "number_telephone_banking_customers": "Количество клиентов телефонного банкинга",
        "monthly_active_mobile_banking_customers": "Количество активных пользователей мобильного банка в месяц",
        "ebanking_transaction_volume": "Объем электронных транзакций",
        "customer_satisfaction_level": "Уровень удовлетворенности клиентов",
        "ebanking_substitution_ratio": "Доля электронных каналов в общем количестве операций"
    }
    
    digital_data = []
    for key, label in digital_indicators.items():
        if key in financial_data:
            value = financial_data[key]
            digital_data.append({
                "Показатель": label,
                "Значение": f"{value:,.0f}" if isinstance(value, (int, float)) and not pd.isna(value) else "N/A"
            })
    
    if digital_data:
        df_digital = pd.DataFrame(digital_data)
        st.dataframe(df_digital, use_container_width=True, hide_index=True)
    else:
        st.info("Не удалось извлечь показатели цифрового банкинга")
    
    # Financial performance indicators section
    st.subheader("💼 Финансовые показатели эффективности")
    
    financial_performance = {
        "operating_income": "Операционный доход (млн руб.)",
        "operating_profit": "Операционная прибыль (млн руб.)",
        "profit_for_the_year": "Прибыль за год (млн руб.)",
        "eps_basic": "EPS (базовая)",
        "roa": "ROA (%)",
        "roe": "ROE (%)",
        "net_interest_margin": "Чистая процентная маржа (%)",
        "cost_to_income_ratio": "Соотношение расходов к доходам (%)",
        "non_interest_income_ratio": "Доля прочих доходов в операционных доходах (%)",
        "credit_cost": "Кредитные издержки (%)",
        "non_performing_loan_ratio": "Доля просроченных кредитов (%)",
        "loan_loss_provision_coverage": "Покрытие просроченных кредитов резервами (%)"
    }
    
    performance_data = []
    for key, label in financial_performance.items():
        if key in financial_data:
            value = financial_data[key]
            performance_data.append({
                "Показатель": label,
                "Значение": f"{value:,.2f}" if isinstance(value, (int, float)) and not pd.isna(value) else "N/A"
            })
    
    if performance_data:
        df_performance = pd.DataFrame(performance_data)
        st.dataframe(df_performance, use_container_width=True, hide_index=True)
    else:
        st.info("Не удалось извлечь финансовые показатели эффективности")
    
    # Calculated ratios section
    st.subheader("📈 Рассчитанные коэффициенты устойчивости")
    
    all_ratios = calculator.calculate_all_ratios()
    
    ratio_descriptions = {
        'capital_adequacy': 'Достаточность капитала',
        'instant_liquidity': 'Мгновенная ликвидность',
        'current_liquidity': 'Текущая ликвидность',
        'roe': 'Рентабельность собственного капитала (ROE)',
        'roa': 'Рентабельность активов (ROA)',
        'nim': 'Чистая процентная маржа (NIM)',
        'problem_loans_ratio': 'Доля проблемных ссуд'
    }
    
    # Create a dataframe for ratios
    ratios_list = []
    for ratio_key, (ratio_value, interpretation) in all_ratios.items():
        desc = ratio_descriptions.get(ratio_key, ratio_key.replace('_', ' ').title())
        status = "🟢 Норма" if "Excellent" in interpretation or "Good" in interpretation or "Adequate" in interpretation else "🔴 Риск"
        
        ratios_list.append({
            "Коэффициент": desc,
            "Значение": f"{ratio_value:.4f}" if isinstance(ratio_value, (int, float)) and not pd.isna(ratio_value) else "N/A",
            "Интерпретация": interpretation.split(':')[-1].strip() if ':' in interpretation else interpretation,
            "Статус": status
        })
    
    if ratios_list:
        df_ratios = pd.DataFrame(ratios_list)
        st.dataframe(df_ratios, use_container_width=True, hide_index=True)
    
    # Bank Stability Index
    bsi_score, bsi_interpretation = calculator.calculate_bsi()
    
    st.subheader("🎯 Индекс банковской устойчивости (BSI)")
    st.metric(
        label="Индекс устойчивости",
        value=f"{bsi_score:.3f}",
        delta=None
    )
    st.info(bsi_interpretation)
    
    # Detailed analysis section
    st.subheader("📊 Детальный аналитический отчет")
    
    # Generate full report
    full_report = generate_analysis_report(calculator)
    st.text_area("Аналитический отчет", value=full_report, height=400)
    
    # Download buttons
    st.subheader("📥 Скачать результаты")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Download detailed report as text
        st.download_button(
            label="Скачать аналитический отчет (.txt)",
            data=full_report,
            file_name="bank_analysis_report.txt",
            mime="text/plain"
        )
    
    with col2:
        # Download ratios as CSV
        if ratios_list:
            df_ratios_csv = pd.DataFrame(ratios_list)
            csv = df_ratios_csv.to_csv(index=False, sep=';')
            st.download_button(
                label="Скачать коэффициенты (.csv)",
                data=csv,
                file_name="bank_ratios.csv",
                mime="text/csv"
            )
    
    with col3:
        # Add finish button
        if st.button("Завершить работу"):
            st.balloons()
            st.success("Анализ успешно завершен!")
            st.stop()


if __name__ == "__main__":
    main()