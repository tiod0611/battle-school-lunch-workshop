#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Excel 파일을 분석하고 OpenAPI JSON 문서를 생성합니다.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

def analyze_excel_structure():
    """Excel 파일 구조 분석"""
    try:
        import openpyxl
        
        data_dir = Path(__file__).parent.parent / "data"
        excel_files = list(data_dir.glob("*.xlsx"))
        
        print(f"Found {len(excel_files)} Excel files:")
        
        for excel_file in excel_files:
            print(f"\n{'='*60}")
            print(f"File: {excel_file.name}")
            print(f"{'='*60}")
            
            wb = openpyxl.load_workbook(excel_file)
            
            for sheet_name in wb.sheetnames:
                ws = wb[sheet_name]
                print(f"\nSheet: {sheet_name}")
                print(f"Dimensions: {ws.max_row} rows x {ws.max_column} columns")
                
                # 첫 10개 행 출력
                print("\nFirst rows:")
                for i, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=True), 1):
                    print(f"  Row {i}: {row}")
            
            wb.close()
            
    except ImportError as e:
        print(f"Error: openpyxl module not found. Please install it with: pip install -r requirements.txt")
        print(f"Details: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Analyzing Excel file structure...")
    analyze_excel_structure()
