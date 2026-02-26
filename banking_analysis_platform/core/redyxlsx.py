#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bank Data Aggregator — финальная версия для обработки таблиц из pdf_extractor.py
✅ Корректное определение года из имени файла (ТОЛЬКО 4 цифры перед _tables)
✅ Точная конвертация единиц измерения (МЛРД РУБ → рубли, МЛН РУБ → рубли)
✅ Расширенные паттерны поиска показателей на русском языке
✅ Обработка единиц измерения в той же ячейке, что и число ("98,1 МЛРД РУБ")
✅ Игнорирование временных файлов (~$*.xlsx)
✅ Приоритизация наиболее точных значений
✅ Обработка ошибок при сохранении + уникальные имена файлов
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path
from datetime import datetime
import warnings
import sys

warnings.filterwarnings('ignore')


class BankTablesProcessor:
    def __init__(self, input_dir: str = "rep/excel_results", output_dir: str = "bank_reports"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

        # Паттерны показателей (только русский язык)
        self.financial_patterns = {
            'total_assets': [r'итого активов', r'валюта баланса', r'активы всего', r'^активы$', r'активы.*конец'],
            'loans_clients': [r'кредиты и авансы клиентам', r'кредитный портфель', r'ссуды клиентам',
                              r'выданные кредиты', r'кредиты.*физическим', r'кредиты.*юридическим'],
            'deposits': [r'депозиты', r'привлеченные средства', r'средства клиентов', r'обязательства.*клиентов',
                         r'вклады'],
            'net_profit': [r'чистая прибыль', r'прибыль.*налог', r'прибыль за год', r'чистая прибыль.*год',
                           r'прибыль.*отчетный период'],
            'operating_income': [r'операционный доход', r'операционные поступления', r'доходы от основной деятельности',
                                 r'доходы.*основная'],
            'operating_profit': [r'операционная прибыль', r'прибыль от основной деятельности'],
            'roa': [r'roa', r'рентабельность активов', r'роа', r'рентабельность.*активов'],
            'roe': [r'roe', r'рентабельность собственного капитала', r'роэ', r'рентабельность.*капитала'],
            'net_interest_margin': [r'чистая процентная маржа', r'процентная маржа', r'npm', r'чистая.*маржа'],
            'cost_to_income': [r'затраты к доходу', r'cir', r'отношение затрат к доходу', r'коэффициент затрат'],
            'npl_ratio': [r'неработающ.*кредит', r'npl', r'просрочен.*кредит', r'стадия 3',
                          r'просроченная задолженность', r'нпл'],
            'cet1_ratio': [r'коэффициент.*адекватности', r'базель', r'капитал.*уровень', r'cet1', r'базовый капитал'],
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
            'api': [r'api', r'интерфейс прикладного программирования', r'открытые api', r'api.*интеграция'],
            'paperless': [r'безбумажный', r'безбумажные операции', r'безбумажные процессы',
                          r'электронный документооборот'],
            'electronic_signature': [r'электронная подпись', r'цифровая подпись', r'e-подпись', r'эцп',
                                     r'электронно-цифровая подпись'],
            'remote_account_opening': [r'удаленное открытие счета', r'дистанционное открытие счета',
                                       r'онлайн-открытие счета', r'цифровое открытие счета'],
            'churn_rate': [r'коэффициент оттока', r'отток клиентов', r'churn', r'отток.*клиенты'],
            'retention_rate': [r'коэффициент удержания', r'удержание клиентов', r'лояльность', r'удержание.*клиенты'],
            'products_per_customer': [r'продукты на клиента', r'количество продуктов на клиента',
                                      r'среднее число продуктов', r'продуктовая.*корзина'],
            'cross_sell': [r'кросс-продажи', r'перекрестные продажи', r'дополнительные продукты', r'кросс.*продажи'],
            'wallet_share': [r'доля кошелька', r'рыночная доля', r'доля рынка', r'кошелек.*клиента'],
            'credit_cost': [r'стоимость кредитов', r'стоимость риска', r'кор', r'резервы.*кредитные убытки',
                            r'стоимость.*кредитования'],
            'allowance_for_loan_impairment_losses_to_non_performing_loans': [
                r'резервы под кредитные убытки к проблемным кредитам',
                r'коэффициент резервирования',
                r'покрытие нпл резервами',
                r'резервы.*нпл'
            ]
        }

        # Единицы измерения
        self.unit_patterns = [
            (r'млрд\.?\s*р\.?', 1e9),
            (r'млрд\.?\s*руб\.?', 1e9),
            (r'млрд', 1e9),
            (r'млн\.?\s*р\.?', 1e6),
            (r'млн\.?\s*руб\.?', 1e6),
            (r'млн', 1e6),
            (r'тыс\.?\s*р\.?', 1e3),
            (r'тыс\.?\s*руб\.?', 1e3),
            (r'тыс', 1e3)
        ]

    def find_table_files(self) -> list:
        """Поиск файлов с таблицами, игнорируя временные файлы ~$"""
        files = []
        for f in self.input_dir.glob("*.xlsx"):
            if f.name.startswith('~$') or not '_tables.xlsx' in f.name.lower():
                continue
            files.append(f)
        return sorted(files)

    def extract_year_from_filename(self, filename: str) -> int:
        """ТОЧНОЕ извлечение года из имени файла (только 4 цифры ПЕРЕД _tables)"""
        # Ищем: буквы + 4 цифры + _tables.xlsx
        match = re.search(r'[a-zа-яё]+(\d{4})_tables\.xlsx$', filename, re.IGNORECASE)
        if match:
            year = int(match.group(1))
            if 2010 <= year <= datetime.now().year:
                return year

        # Fallback: последний валидный год в имени
        years = re.findall(r'\b(201[0-9]|202[0-9])\b', filename)
        if years:
            return int(years[-1])

        return datetime.now().year

    def extract_bank_name(self, filename: str) -> str:
        """Извлечение кода банка из имени файла"""
        name = re.sub(r'_tables\.xlsx$', '', filename, flags=re.IGNORECASE)
        name = re.sub(r'\d{4}$', '', name)
        name = re.sub(r'[^a-zа-яё]', '', name, flags=re.IGNORECASE)
        return name.lower().strip() or 'unknown'

    def parse_number_with_unit(self, value) -> tuple:
        """Парсинг числа с единицей измерения из одной ячейки (например "98,1 МЛРД РУБ")"""
        if pd.isna(value) or value == '' or value == '-' or value == '—':
            return None, 1.0

        # Для строковых значений
        if isinstance(value, str):
            val_str = value.replace('\xa0', ' ').strip()

            # Ищем единицу измерения в строке
            for pattern, multiplier in self.unit_patterns:
                match = re.search(pattern, val_str, re.IGNORECASE)
                if match:
                    # Удаляем единицу измерения из строки
                    clean_str = re.sub(pattern, '', val_str, flags=re.IGNORECASE).strip()
                    num = self.parse_russian_number(clean_str)
                    if num is not None:
                        return num, multiplier

            # Если единицы нет — парсим просто число
            num = self.parse_russian_number(val_str)
            return num, 1.0

        # Для числовых значений
        if isinstance(value, (int, float)):
            return float(value) if not pd.isna(value) else None, 1.0

        return None, 1.0

    def parse_russian_number(self, value) -> float:
        """Преобразование русского формата чисел (1 234,56 → 1234.56)"""
        if pd.isna(value) or value == '' or value == '-' or value == '—' or value == '–':
            return None

        if isinstance(value, (int, float)):
            return float(value) if not pd.isna(value) else None

        val_str = str(value).replace('\xa0', ' ').strip()

        # Удаляем валютные символы и мусор в конце
        val_str = re.sub(r'[₽\$€%\s]+$', '', val_str)
        # Удаляем мусор в начале
        val_str = re.sub(r'^[^\d\-\.,]+', '', val_str)

        # Обработка русского формата: 1 234,56 → 1234.56
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

    def detect_units_in_context(self, row, col_idx: int) -> float:
        """Определение единиц измерения из контекста (соседние ячейки, заголовки)"""
        # Проверяем текущую ячейку на наличие единицы измерения
        cell_value = row.iloc[col_idx] if col_idx < len(row) else None
        if isinstance(cell_value, str):
            for pattern, multiplier in self.unit_patterns:
                if re.search(pattern, cell_value, re.IGNORECASE):
                    return multiplier

        # Проверяем следующую ячейку (часто единица измерения справа)
        if col_idx + 1 < len(row):
            next_cell = row.iloc[col_idx + 1]
            if isinstance(next_cell, str):
                for pattern, multiplier in self.unit_patterns:
                    if re.search(pattern, next_cell, re.IGNORECASE):
                        return multiplier

        # Проверяем предыдущую ячейку
        if col_idx - 1 >= 0:
            prev_cell = row.iloc[col_idx - 1]
            if isinstance(prev_cell, str):
                for pattern, multiplier in self.unit_patterns:
                    if re.search(pattern, prev_cell, re.IGNORECASE):
                        return multiplier

        return 1.0

    def is_table_header(self, row) -> bool:
        """Проверка заголовка таблицы"""
        if row.empty or pd.isna(row.iloc[0]):
            return False
        first_cell = str(row.iloc[0]).strip().lower()
        return 'таблица #' in first_cell

    def extract_financial_data(self, df: pd.DataFrame) -> dict:
        """Извлечение финансовых показателей с обработкой единиц измерения"""
        if df.empty or len(df.columns) < 2:
            return {}

        data = {}
        current_units = {}  # Единицы измерения для столбцов

        # Проходим по строкам
        for idx in range(len(df)):
            row = df.iloc[idx]

            # Пропускаем заголовки и пустые строки
            if self.is_table_header(row) or row.isna().all():
                continue

            # Ищем единицы измерения в строке (для всех столбцов)
            for col_idx in range(min(10, len(row))):
                cell = row.iloc[col_idx]
                if pd.isna(cell) or not isinstance(cell, str):
                    continue
                cell_upper = cell.upper().strip()
                for pattern, multiplier in self.unit_patterns:
                    if re.search(pattern.upper(), cell_upper):
                        current_units[col_idx] = multiplier
                        break

            # Получаем непустые ячейки
            non_empty = [(i, cell) for i, cell in enumerate(row)
                         if pd.notna(cell) and str(cell).strip() != '' and len(str(cell).strip()) > 1]

            if len(non_empty) < 2:
                continue

            # Объединяем первые 1-3 ячейки в название показателя
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

            # Ищем совпадения с паттернами
            for param_name, patterns in self.financial_patterns.items():
                if any(re.search(pattern, indicator_name, re.IGNORECASE) for pattern in patterns):
                    # Извлекаем значения
                    for j in range(value_start_idx, len(non_empty)):
                        col_idx, cell_value = non_empty[j]

                        # Парсим число с единицей измерения из самой ячейки
                        num, inline_multiplier = self.parse_number_with_unit(cell_value)
                        if num is None:
                            continue

                        # Определяем множитель из контекста
                        context_multiplier = current_units.get(col_idx,
                                                               self.detect_units_in_context(row, col_idx))

                        # Итоговый множитель
                        multiplier = inline_multiplier * context_multiplier

                        # Для процентных показателей не применяем множитель (кроме случаев, когда явно указано "млрд")
                        is_percentage = param_name in ['roa', 'roe', 'net_interest_margin', 'cost_to_income',
                                                       'npl_ratio', 'cet1_ratio', 'churn_rate', 'retention_rate']

                        if is_percentage:
                            # Если значение > 100 и нет явного указания единиц — это не процент
                            if num > 100 and multiplier == 1.0:
                                continue
                            # Для процентов множитель всегда 1.0 (если не указано иное)
                            final_value = num
                        else:
                            # Для абсолютных показателей применяем множитель
                            final_value = num * multiplier

                            # Эвристика: если показатель — активы/кредиты/депозиты и значение < 1000
                            # и не было явного указания единиц — предполагаем млрд
                            if (param_name in ['total_assets', 'loans_clients', 'deposits', 'net_profit',
                                               'operating_income']
                                    and final_value < 1e12  # меньше 1 трлн
                                    and multiplier == 1.0
                                    and num > 1):
                                final_value *= 1e9

                        # Сохраняем наиболее точное значение (последнее в таблице)
                        data[param_name] = final_value

                    break

        return data

    def parse_tables_file(self, file_path: Path) -> dict:
        """Парсинг файла *_tables.xlsx"""
        try:
            df = pd.read_excel(file_path, sheet_name=0, header=None)
            if df.empty:
                print(f"  ⚠️  Файл {file_path.name} пустой")
                return {}

            print(f"  📊 Обработка {file_path.name}: {df.shape[0]} строк")

            # Определяем банк и год
            bank_name = self.extract_bank_name(file_path.name)
            year = self.extract_year_from_filename(file_path.name)
            print(f"  🏦 Банк: {bank_name.upper()} | 📅 Год: {year}")

            # Разделяем на таблицы
            tables = []
            current_table_start = None

            for idx in range(len(df)):
                row = df.iloc[idx]
                if self.is_table_header(row):
                    if current_table_start is not None and idx - current_table_start > 3:
                        table_df = df.iloc[current_table_start:idx].dropna(how='all', axis=1)
                        if len(table_df) > 3 and len(table_df.columns) > 1:
                            tables.append(table_df)
                    current_table_start = idx + 1

            # Последняя таблица
            if current_table_start is not None and len(df) - current_table_start > 3:
                table_df = df.iloc[current_table_start:].dropna(how='all', axis=1)
                if len(table_df) > 3 and len(table_df.columns) > 1:
                    tables.append(table_df)

            print(f"  🔍 Найдено таблиц: {len(tables)}")

            # Извлекаем данные
            financial_data = {}
            for tbl_idx, table_df in enumerate(tables):
                tbl_data = self.extract_financial_data(table_df)
                financial_data.update(tbl_data)  # Последнее значение обычно точнее

            if not financial_data:
                print(f"  ⚠️  Финансовые показатели не найдены")
                return {}

            print(f"  ✅ Извлечено показателей: {len(financial_data)}")

            return {
                'bank': bank_name,
                'year': year,
                'source_file': file_path.name,
                **financial_data
            }

        except Exception as e:
            print(f"  ❌ Ошибка при парсинге {file_path.name}: {str(e)[:100]}")
            return {}

    def process_all_files(self) -> dict:
        """Обработка всех файлов"""
        files = self.find_table_files()
        if not files:
            print("❌ Не найдено файлов для обработки (ищем *_tables.xlsx, игнорируем ~$*.xlsx)")
            return {}

        print(f"\n{'=' * 70}")
        print("НАЧАЛО ОБРАБОТКИ ФАЙЛОВ С ТАБЛИЦАМИ")
        print(f"{'=' * 70}")

        bank_data = {}

        for idx, file_path in enumerate(files, 1):
            print(f"\n📄 [{idx}/{len(files)}] {file_path.name}")
            data = self.parse_tables_file(file_path)

            if data and 'bank' in data and 'year' in data:
                bank = data['bank']
                year = data['year']

                if bank not in bank_data:
                    bank_data[bank] = {}

                bank_data[bank][year] = data

        # Статистика
        print(f"\n{'=' * 70}")
        print("ИТОГИ ОБРАБОТКИ")
        print(f"{'=' * 70}")
        total_banks = len(bank_data)
        total_records = sum(len(years) for years in bank_data.values())
        print(f"✅ Обработано банков: {total_banks}")
        print(f"✅ Извлечено записей (банк+год): {total_records}")

        for bank, years_data in bank_data.items():
            years = sorted(years_data.keys())
            params = set(k for year_data in years_data.values()
                         for k in year_data.keys()
                         if k not in ['bank', 'year', 'source_file'])
            print(f"\n🏦 {bank.upper()}:")
            print(f"   Годы: {years}")
            print(f"   Показателей: {len(params)}")
            if params:
                sample_params = list(params)[:8]
                print(f"   Примеры: {', '.join(sample_params)}{'...' if len(params) > 8 else ''}")

        return bank_data

    def save_results(self, bank_data: dict):
        """Сохранение результатов с обработкой ошибок"""
        if not bank_data:
            print("\n❌ Нет данных для сохранения")
            return

        print(f"\n{'=' * 70}")
        print("СОХРАНЕНИЕ РЕЗУЛЬТАТОВ")
        print(f"{'=' * 70}")

        # Формируем сводную таблицу
        all_records = []
        for bank, years_data in bank_data.items():
            for year, data in years_data.items():
                record = {'bank': bank, 'year': year}
                for param in self.financial_patterns.keys():
                    record[param] = data.get(param, np.nan)
                all_records.append(record)

        if not all_records:
            print("❌ Нет данных для сохранения")
            return

        df_summary = pd.DataFrame(all_records)
        df_summary = df_summary.sort_values(['bank', 'year'])

        # Уникальное имя файла с временной меткой
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f"bank_financial_summary_{timestamp}.xlsx"

        try:
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                # Сводная таблица
                df_summary.to_excel(writer, sheet_name='Сводная таблица', index=False)

                # Детальные данные по банкам
                for bank in sorted(bank_data.keys()):
                    bank_records = [r for r in all_records if r['bank'] == bank]
                    df_bank = pd.DataFrame(bank_records)
                    if not df_bank.empty:
                        df_bank = df_bank.dropna(axis=1, how='all')
                        sheet_name = bank[:31]
                        df_bank.to_excel(writer, sheet_name=sheet_name, index=False)

                # Словарь показателей
                dict_data = []
                for param_name, patterns in self.financial_patterns.items():
                    dict_data.append({
                        'Код показателя': param_name,
                        'Примеры поиска': ' | '.join(patterns[:3])
                    })
                df_dict = pd.DataFrame(dict_data)
                df_dict.to_excel(writer, sheet_name='Словарь показателей', index=False)

            print(f"✅ Сводный отчёт сохранён: {output_file.name}")

            # CSV
            csv_file = self.output_dir / f"bank_data_{timestamp}.csv"
            df_summary.to_csv(csv_file, index=False, encoding='utf-8-sig')
            print(f"✅ CSV для анализа: {csv_file.name}")

            # Превью данных
            print(f"\n📈 ПРЕДПРОСМОТР ДАННЫХ (первые 10 записей):")
            preview = df_summary.head(10).copy()

            # Форматируем для вывода
            display_cols = ['bank', 'year'] + [col for col in preview.columns if col not in ['bank', 'year']][:10]
            preview_display = preview[display_cols].copy()

            for col in preview_display.select_dtypes(include=[np.number]).columns:
                if preview_display[col].abs().max() > 1e12:
                    preview_display[col] = preview_display[col].apply(
                        lambda x: f"{x / 1e12:.2f} трлн" if pd.notna(x) else x
                    )
                elif preview_display[col].abs().max() > 1e9:
                    preview_display[col] = preview_display[col].apply(
                        lambda x: f"{x / 1e9:.2f} млрд" if pd.notna(x) else x
                    )
                elif preview_display[col].abs().max() > 1e6:
                    preview_display[col] = preview_display[col].apply(
                        lambda x: f"{x / 1e6:.2f} млн" if pd.notna(x) else x
                    )

            print(preview_display.to_string(index=False))

            print(f"\n📁 Все результаты сохранены в папку: {self.output_dir.absolute()}")
            print("\n💡 Важно:")
            print("   • Абсолютные показатели (активы, кредиты) конвертированы в рубли")
            print("   • Процентные показатели (ROA, ROE, NPL) сохранены как есть (3.5 = 3.5%)")
            print("   • Для точности проверьте исходные таблицы в *_tables.xlsx")

        except PermissionError:
            print(f"❌ Ошибка: Файл открыт в Excel или нет прав на запись")
            print(f"   Закройте файл {output_file.name} и повторите запуск")
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")
            import traceback
            traceback.print_exc()

    def run(self):
        """Запуск обработки"""
        print("=" * 70)
        print(" BANK DATA AGGREGATOR (финальная версия)")
        print("=" * 70)
        print(f"\n📁 Входная папка: {self.input_dir.absolute()}")
        print(f"📁 Выходная папка: {self.output_dir.absolute()}")

        if not self.input_dir.exists():
            print(f"\n❌ Папка не найдена: {self.input_dir}")
            print("   Создайте папку 'rep/excel_results' и поместите туда файлы *_tables.xlsx")
            return

        bank_data = self.process_all_files()
        self.save_results(bank_data)

        print("\n" + "=" * 70)
        if bank_data:
            print("🎉 Обработка завершена успешно!")
        else:
            print("⚠️  Обработка завершена, но данные не найдены")
            print("\n🔍 Возможные причины:")
            print("   1. В папке нет файлов вида *_tables.xlsx")
            print("   2. В таблицах отсутствуют искомые финансовые показатели")
            print("   3. Структура таблиц отличается от ожидаемой")
        print("=" * 70)


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Агрегация финансовых данных из таблиц *_tables.xlsx",
        epilog="Примеры:\n"
               "  python redyxlsx.py\n"
               "  python redyxlsx.py --input rep/excel_results --output bank_reports",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-i", "--input", default="rep/excel_results",
                        help="Папка с файлами *_tables.xlsx (по умолчанию: rep/excel_results)")
    parser.add_argument("-o", "--output", default="bank_reports",
                        help="Папка для сохранения результатов (по умолчанию: bank_reports)")

    args = parser.parse_args()

    processor = BankTablesProcessor(input_dir=args.input, output_dir=args.output)
    processor.run()


if __name__ == "__main__":
    main()