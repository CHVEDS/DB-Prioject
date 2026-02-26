#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PDF Table Extractor — обработка всех PDF в папке
✅ Отдельный Excel-файл для КАЖДОГО PDF
✅ Все таблицы из одного PDF — на ОДНОМ листе с отступами
✅ Прогресс-бары и визуализация процесса
✅ Фильтрация мусора + поддержка разного количества столбцов
✅ Совместимость с pandas ≥ 2.1
✅ ИСПРАВЛЕНО: ошибка кодировки 'charmap' в Windows
"""
import sys
import io
import tabula
import pandas as pd
import numpy as np
import warnings
from pathlib import Path
from tqdm import tqdm
from datetime import datetime
import time
import subprocess
import re

# Исправление кодировки для Windows
if sys.platform == 'win32':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    except:
        pass

warnings.filterwarnings('ignore')

def clean_cell(value):
    """Очистка значения ячейки от спецсимволов и лишних пробелов"""
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
    """Совместимость с разными версиями pandas (applymap → map)"""
    try:
        return df.map(func)
    except AttributeError:
        return df.applymap(func)

def is_valid_table(df: pd.DataFrame, min_rows: int = 3, min_cols: int = 2) -> bool:
    """Проверка, является ли объект реальной таблицей (фильтрация мусора)"""
    if df.empty or df.shape[0] < min_rows or df.shape[1] < min_cols:
        return False
    fill_ratio = df.notna().sum().sum() / (df.shape[0] * df.shape[1])
    if fill_ratio < 0.3:
        return False
    numeric_cells = df.apply(lambda s: pd.to_numeric(s, errors='coerce')).notna().sum().sum()
    if numeric_cells < 2 and df.shape[1] < 3:
        return False
    return True

def extract_tables_from_pdf(pdf_path: Path, method: str = "stream") -> list:
    """Извлечение и очистка таблиц из одного PDF"""
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
        print(f"  ⚠ Ошибка при извлечении из {pdf_path.name}: {str(e)[:80]}")
    return tables

def save_tables_to_single_sheet(tables: list, output_path: Path, source_file: str):
    """Сохранение всех таблиц на ОДИН лист Excel с отступами"""
    if not tables:
        return False, 0
    max_cols = max(df.shape[1] for df in tables)
    rows = []
    rows.append(["ТАБЛИЦЫ ИЗ PDF", "", "", ""])
    rows.append(["Исходный файл:", source_file, "", ""])
    rows.append(["Дата обработки:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "", ""])
    rows.append(["Извлечено таблиц:", len(tables), "", ""])
    rows.append(["", "", "", ""])
    for idx, df in enumerate(tables, 1):
        rows.append([f"ТАБЛИЦА #{idx} | Размер: {df.shape[0]}×{df.shape[1]}", "", "", ""])
        header_row = list(df.columns) + [np.nan] * (max_cols - len(df.columns))
        rows.append(header_row)
        for _, row in df.iterrows():
            row_data = list(row.values) + [np.nan] * (max_cols - len(row.values))
            rows.append(row_data)
        rows.append([np.nan] * max_cols)
        rows.append([np.nan] * max_cols)
    combined_df = pd.DataFrame(rows)
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            combined_df.to_excel(writer, index=False, header=False, sheet_name="Таблицы")
        try:
            from openpyxl import load_workbook
            wb = load_workbook(output_path)
            ws = wb.active
            for idx, col in enumerate(ws.columns[:15], 1):
                max_length = 0
                column = col[0].column_letter
                for cell in col[:100]:
                    try:
                        if cell.value and len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                ws.column_dimensions[column].width = adjusted_width
            wb.save(output_path)
        except Exception as e:
            pass
        return True, len(tables)
    except Exception as e:
        print(f"  ⚠ Ошибка сохранения: {e}")
        return False, 0

def process_single_pdf(pdf_path: Path, output_folder: Path) -> tuple:
    """Обработка одного PDF-файла"""
    print(f"\n📄 Обработка: {pdf_path.name}")
    start = time.time()
    tables = extract_tables_from_pdf(pdf_path, method="stream")
    extract_time = time.time() - start
    if not tables:
        print(f"  ⚠️  Таблицы не найдены")
        return False, 0, extract_time
    print(f"  ✅ Найдено таблиц: {len(tables)} (время извлечения: {extract_time:.1f}с)")
    output_file = output_folder / f"{pdf_path.stem}_tables.xlsx"
    save_start = time.time()
    success, table_count = save_tables_to_single_sheet(tables, output_file, pdf_path.name)
    save_time = time.time() - save_start
    if success:
        print(f"  💾 Сохранено: {output_file.name} ({table_count} таблиц, время: {save_time:.1f}с)")
        return True, table_count, extract_time + save_time
    else:
        print(f"  ❌ Ошибка сохранения")
        return False, 0, extract_time + save_time

def check_java():
    """Проверка наличия Java"""
    try:
        result = subprocess.run(["java", "-version"], capture_output=True, text=True, check=True, encoding='utf-8')
        version_line = result.stderr.split('\n')[0] if result.stderr else result.stdout
        print(f"☕ Java обнаружена: {version_line.strip()}")
        return True
    except FileNotFoundError:
        print("❌ Java не найдена! Установите JRE/JDK:")
        print("   https://www.java.com/ru/download/")
        return False
    except Exception as e:
        print(f"⚠️  Ошибка проверки Java: {e}")
        return True

def process_folder(input_folder: str = "rep", output_folder: str = None):
    """Основная функция: обработка всех PDF в папке"""
    folder = Path(input_folder)
    if not folder.exists() or not folder.is_dir():
        print(f"❌ Папка не найдена: {folder.absolute()}")
        return False
    pdf_files = sorted([f for f in folder.glob("*.pdf") if not f.name.startswith('~$')])
    if not pdf_files:
        print(f"⚠️  В папке {folder} не найдено PDF-файлов")
        return False
    print(f"📁 Найдено {len(pdf_files)} PDF-файлов в папке: {folder}")
    if output_folder is None:
        output_folder = folder / "excel_results"
    else:
        output_folder = Path(output_folder)
    output_folder.mkdir(exist_ok=True)
    print(f"📁 Результаты будут сохранены в: {output_folder}")
    print("=" * 70)
    total_files = 0
    total_tables = 0
    total_time = 0
    results = []
    for idx, pdf_path in enumerate(tqdm(pdf_files, desc="Обработка файлов", unit="файл", dynamic_ncols=True), 1):
        print(f"\n[{idx}/{len(pdf_files)}] ", end="", flush=True)
        success, table_count, proc_time = process_single_pdf(pdf_path, output_folder)
        results.append({
            "file": pdf_path.name,
            "success": success,
            "tables": table_count,
            "time": proc_time
        })
        if success:
            total_files += 1
            total_tables += table_count
            total_time += proc_time
    print("\n" + "=" * 70)
    print("📊 ИТОГИ ОБРАБОТКИ")
    print("=" * 70)
    print(f"✅ Успешно обработано файлов: {total_files} из {len(pdf_files)}")
    print(f"📊 Всего извлечено таблиц: {total_tables}")
    print(f"⏱️  Общее время обработки: {total_time:.1f} сек")
    print(f"📁 Результаты сохранены в: {output_folder.absolute()}")
    print("\n📄 Детали по файлам:")
    print("-" * 70)
    for res in results:
        status = "✅" if res["success"] else "❌"
        print(f"{status} {res['file']:<30} | Таблиц: {res['tables']:<4} | Время: {res['time']:.1f}с")
    print("\n💡 Советы по работе с результатами:")
    print("   • Каждый Excel-файл содержит все таблицы из соответствующего PDF")
    print("   • Таблицы разделены 2 пустыми строками для удобства чтения")
    print("   • В начале листа — метаданные (исходный файл, дата обработки)")
    print("   • Для поиска таблиц используйте фильтр по 'ТАБЛИЦА #'")
    return total_files > 0

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Извлечение таблиц из ВСЕХ PDF в папке → отдельные Excel-файлы",
        epilog="Примеры:\n"
               "  python pdf_extractor.py\n"
               "  python pdf_extractor.py --folder rep --output results",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("-f", "--folder", default="rep", help="Папка с PDF-файлами (по умолчанию: rep)")
    parser.add_argument("-o", "--output", help="Папка для сохранения Excel-файлов")
    args = parser.parse_args()
    print("=" * 70)
    print(" PDF → Excel Batch Processor (отдельный файл для каждого PDF)")
    print("=" * 70)
    if not check_java():
        sys.exit(1)
    print(f"\n📁 Входная папка: {Path(args.folder).absolute()}")
    if args.output:
        print(f"📁 Выходная папка: {Path(args.output).absolute()}")
    else:
        print(f"📁 Выходная папка: {Path(args.folder) / 'excel_results'}")
    print("-" * 70)
    start_overall = time.time()
    success = process_folder(args.folder, args.output)
    elapsed = time.time() - start_overall
    print("\n" + "=" * 70)
    print(f"⏱️  Общее время выполнения: {elapsed:.1f} сек")
    if success:
        print("🎉 Обработка завершена успешно!")
    else:
        print("⚠️  Обработка завершена с ошибками")
    print("=" * 70)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()