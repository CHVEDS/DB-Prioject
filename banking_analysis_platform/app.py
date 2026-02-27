"""Banking Stability Analysis Platform - Main Application"""

import streamlit as st
import pandas as pd
from pathlib import Path
import logging
from typing import Dict, Optional
import tempfile

# Import modules from our package
from core.pdf_processor import extract_tables_from_pdf
from core.metadata_extractor import extract_metadata
from core.data_aggregator import aggregate_financial_data
from core.export_manager import ReportExportManager
from analytics.calculator import BankingRatiosCalculator, generate_analysis_report
from analytics.bsi import calculate_bsi
from config.styles import CSS_STYLES, APP_TITLE, APP_SUBTITLE, COLOR_SCHEME
from utils.logging_config import logger


def main():
    """Main function to run the Streamlit application."""
    st.set_page_config(
        page_title="Аналитический центр банковской устойчивости",
        page_icon="🏦",
        layout="wide"
    )
    
    # Apply custom CSS
    st.markdown(CSS_STYLES, unsafe_allow_html=True)
    
    st.title(APP_TITLE)
    st.subheader(APP_SUBTITLE)
    st.markdown("---")
    
    # Initialize session state
    if 'session_data' not in st.session_state:
        st.session_state.session_data = {}
    
    # File uploader for multiple PDFs
    uploaded_files = st.file_uploader(
        "Загрузите годовые отчёты банков (PDF)",
        type=["pdf"],
        accept_multiple_files=True,
        help="Поддерживается загрузка нескольких файлов одновременно"
    )
    
    if uploaded_files:
        # Process each uploaded file
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, file in enumerate(uploaded_files):
            status_text.text(f"Обработка файла {idx + 1} из {len(uploaded_files)}: {file.name}")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(file.getvalue())
                temp_path = tmp_file.name
            
            try:
                # 1. Extract tables from PDF
                tables = extract_tables_from_pdf(Path(temp_path))
                
                if not tables:
                    st.error(f"Не удалось извлечь финансовые данные из {file.name}. "
                            "Проверьте, что это годовой отчет банка в формате PDF.")
                    continue
                
                # 2. Extract metadata (bank name, year) from content
                # For now, we'll use a placeholder approach, later we can enhance with actual text extraction
                metadata = extract_metadata(tables, "")
                bank_name = metadata['bank_name']  # REAL name from PDF
                report_year = metadata['year']
                
                # 3. Aggregate financial data
                financial_data = aggregate_financial_data(tables)
                financial_data['bank_name'] = bank_name
                financial_data['year'] = report_year
                
                # 4. Calculate ratios
                calculator = BankingRatiosCalculator(financial_data)
                ratios = calculator.calculate_all_ratios()
                
                # 5. Calculate BSI
                bsi = calculate_bsi(financial_data, ratios)
                
                # 6. Store in session state
                st.session_state.session_data[bank_name] = {
                    'financial_data': financial_data,
                    'ratios': ratios,
                    'bsi': bsi,
                    'tables': tables,
                    'year': report_year
                }
                
            except Exception as e:
                st.error(f"Ошибка обработки файла {file.name}: {str(e)}")
                logger.error(f"Error processing file {file.name}: {str(e)}")
            finally:
                # Clean up temporary file
                Path(temp_path).unlink(missing_ok=True)
            
            progress_bar.progress((idx + 1) / len(uploaded_files))
        
        status_text.text("✅ Обработка завершена!")
    
    # Display results if data exists
    if st.session_state.session_data:
        display_results()
    
    # Show finish button
    show_finish_section()


def display_results():
    """Display analysis results in the Streamlit interface."""
    st.markdown("## 📊 Результаты анализа")
    
    # Display bank ranking if multiple banks
    if len(st.session_state.session_data) > 1:
        display_bank_ranking(st.session_state.session_data)
    
    # Allow selection of bank to view details
    if len(st.session_state.session_data) > 1:
        selected_bank = st.selectbox(
            "🏦 Выберите банк для просмотра:",
            options=list(st.session_state.session_data.keys())
        )
    else:
        selected_bank = list(st.session_state.session_data.keys())[0]
    
    data = st.session_state.session_data[selected_bank]
    
    # Display metrics in corporate style
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Активы</h4>
            <p style="font-size: 24px; color: #0052A3; font-weight: bold;">
                {data['financial_data'].get('total_assets', 0) / 1e9:.2f} млрд ₽
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <h4>Капитал</h4>
            <p style="font-size: 24px; color: #0052A3; font-weight: bold;">
                {data['financial_data'].get('equity', 0) / 1e9:.2f} млрд ₽
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <h4>ROE</h4>
            <p style="font-size: 24px; color: #0052A3; font-weight: bold;">
                {data['ratios'].get('roe', (0, ''))[0] * 100:.2f}%
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <h4>BSI</h4>
            <p style="font-size: 24px; color: #0052A3; font-weight: bold;">
                {data['bsi'][0]:.3f}
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Display detailed financial data
    st.subheader(f"📋 Финансовые данные - {selected_bank}")
    
    financial_data = data['financial_data']
    financial_summary = {
        'Показатель': [
            'Общие активы',
            'Общие обязательства', 
            'Собственный капитал',
            'Чистая прибыль',
            'Денежные средства',
            'Кредиты клиентам'
        ],
        'Значение (млрд ₽)': [
            f"{financial_data.get('total_assets', 0) / 1e9:.2f}",
            f"{financial_data.get('total_liabilities', 0) / 1e9:.2f}",
            f"{financial_data.get('equity', 0) / 1e9:.2f}",
            f"{financial_data.get('net_income', 0) / 1e9:.2f}",
            f"{financial_data.get('cash_and_equivalents', 0) / 1e9:.2f}",
            f"{financial_data.get('loans_to_customers', 0) / 1e9:.2f}"
        ]
    }
    
    df_financial = pd.DataFrame(financial_summary)
    st.dataframe(df_financial, use_container_width=True, hide_index=True)
    
    # Display calculated ratios
    st.subheader("📈 Рассчитанные коэффициенты устойчивости")
    
    all_ratios = data['ratios']
    
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
        status = ("🟢 Хорошо" if ratio_value >= 0.6 else 
                  "🟡 Удовл." if ratio_value >= 0.4 else 
                  "🟠 Риск" if ratio_value >= 0.2 else "🔴 Критично")
        
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
    bsi_score, bsi_interpretation = data['bsi']
    
    st.subheader("🎯 Индекс банковской устойчивости (BSI)")
    st.metric(
        label="Индекс устойчивости",
        value=f"{bsi_score:.3f}",
        delta=None
    )
    st.info(bsi_interpretation)


def display_bank_ranking(banks_data: Dict) -> None:
    """
    Display comparative table of banks with ranking
    """
    st.subheader("🏆 Рейтинг банков по устойчивости")
    
    # Collect data for comparison
    ranking_data = []
    for bank_name, data in banks_data.items():
        bsi_score = data.get('bsi', (0, ''))[0] if isinstance(data.get('bsi'), tuple) else data.get('bsi', 0)
        ratios = data.get('ratios', {})
        
        ranking_data.append({
            '🏦 Банк': bank_name,
            '📅 Год': data.get('year', 'N/A'),
            '📊 BSI Индекс': f"{bsi_score:.3f}",
            '💰 Активы (млрд ₽)': f"{data.get('financial_data', {}).get('total_assets', 0) / 1e9:.2f}",
            '🏛️ Капитал (млрд ₽)': f"{data.get('financial_data', {}).get('equity', 0) / 1e9:.2f}",
            '📈 ROE (%)': f"{ratios.get('roe', (0, ''))[0] * 100:.2f}" if isinstance(ratios.get('roe'), tuple) else f"{ratios.get('roe', 0) * 100:.2f}",
            '💧 Ликвидность': f"{ratios.get('current_liquidity', (0, ''))[0]:.2f}" if isinstance(ratios.get('current_liquidity'), tuple) else f"{ratios.get('current_liquidity', 0):.2f}",
            '🎯 Статус': get_status_emoji(bsi_score)
        })
    
    # Sort by BSI (descending)
    df_ranking = pd.DataFrame(ranking_data)
    df_ranking = df_ranking.sort_values('📊 BSI Индекс', ascending=False)
    
    # Add place in ranking
    df_ranking.insert(0, '🥇 Место', range(1, len(df_ranking) + 1))
    
    # Display with color indication
    st.dataframe(
        df_ranking,
        use_container_width=True,
        hide_index=True,
        column_config={
            "🥇 Место": st.column_config.NumberColumn(format="%d"),
            "📊 BSI Индекс": st.column_config.NumberColumn(format="%.3f"),
            "🎯 Статус": st.column_config.TextColumn()
        }
    )
    
    # Visualization of top 3
    if len(df_ranking) >= 3:
        st.markdown("### 🏅 Топ-3 банка")
        top3 = df_ranking.head(3)
        cols = st.columns(3)
        medals = ["🥇", "🥈", "🥉"]
        for idx, (_, row) in enumerate(top3.iterrows()):
            with cols[idx]:
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #E6F2FF 0%, #FFFFFF 100%); 
                            padding: 20px; border-radius: 10px; text-align: center; 
                            border: 2px solid #0052A3;">
                    <div style="font-size: 48px;">{medals[idx]}</div>
                    <div style="font-weight: bold; color: #003366; font-size: 18px;">{row['🏦 Банк']}</div>
                    <div style="color: #0052A3; font-size: 24px; font-weight: bold;">BSI: {row['📊 BSI Индекс']}</div>
                </div>
                """, unsafe_allow_html=True)


def get_status_emoji(bsi_score: float) -> str:
    if bsi_score >= 0.8:
        return "🟢 Отлично"
    elif bsi_score >= 0.6:
        return "🟢 Хорошо"
    elif bsi_score >= 0.4:
        return "🟡 Удовл."
    elif bsi_score >= 0.2:
        return "🟠 Риск"
    else:
        return "🔴 Критично"


def show_finish_section():
    """Show the finish section with export options."""
    st.markdown("---")
    st.subheader("📥 Экспорт результатов")

    with st.expander("⚙️ Настройки экспорта", expanded=True):
        col1, col2 = st.columns(2)
        
        with col1:
            report_type = st.radio(
                "Тип отчёта:",
                ["📋 Индивидуальный по банку",
                 "📊 Сводный по всем банкам",
                 "📈 Только коэффициенты",
                 "📦 Полный архив (ZIP)"],
                index=0
            )
        
        with col2:
            if report_type in ["📋 Индивидуальный по банку", "📈 Только коэффициенты"]:
                selected_banks = st.multiselect(
                    "Банки:",
                    options=list(st.session_state.session_data.keys()),
                    default=list(st.session_state.session_data.keys())
                )
            else:
                selected_banks = list(st.session_state.session_data.keys())
            
            format_options = st.multiselect(
                "Форматы:",
                [".xlsx", ".csv", ".txt"],
                default=[".xlsx"] if report_type != "📦 Полный архив (ZIP)" else []
            )

    if st.button("📊 Сгенерировать отчёты", type="primary"):
        with st.spinner("Генерация файлов..."):
            export_manager = ReportExportManager(st.session_state.session_data)
            
            if report_type == "📋 Индивидуальный по банку":
                files = {}
                for bank in selected_banks:
                    bank_files = export_manager.generate_individual_report(bank, format_options)
                    files.update(bank_files)
            elif report_type == "📊 Сводный по всем банкам":
                files = export_manager.generate_summary_report(format_options)
            elif report_type == "📈 Только коэффициенты":
                files = export_manager.generate_ratios_report(selected_banks, format_options)
            elif report_type == "📦 Полный архив (ZIP)":
                files = export_manager.generate_full_archive()
            
            # Download buttons
            for file_name, file_data in files.items():
                st.download_button(
                    label=f"📄 Скачать {file_name}",
                    data=file_data,
                    file_name=file_name,
                    mime=get_mime_type(file_name),
                    key=f"download_{file_name}"
                )
            
            st.success(f"✅ Сгенерировано файлов: {len(files)}")

    # Finish button
    st.markdown("---")
    st.subheader("⏹️ Завершение работы")

    col1, col2 = st.columns([3, 1])

    with col1:
        st.write("После завершения работы все данные сессии будут очищены.")

    with col2:
        if st.button("🔴 Завершить программу", type="secondary", use_container_width=True):
            # Clear session_state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            
            # Message about completion
            st.balloons()
            st.success("✅ Анализ успешно завершён! Спасибо за использование платформы.")
            st.info("🔄 Обновите страницу для начала нового анализа.")
            
            # Stop execution
            st.stop()


def get_mime_type(file_name: str) -> str:
    """Get MIME type based on file extension."""
    if file_name.endswith('.xlsx'):
        return 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif file_name.endswith('.csv'):
        return 'text/csv'
    elif file_name.endswith('.txt'):
        return 'text/plain'
    elif file_name.endswith('.zip'):
        return 'application/zip'
    else:
        return 'application/octet-stream'


if __name__ == "__main__":
    main()