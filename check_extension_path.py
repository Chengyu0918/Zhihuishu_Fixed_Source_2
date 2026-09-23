#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查拓展路径Excel文件结构"""

import pandas as pd

def main():
    file_path = 'data/2/电子信息工程拓展路径梳理（v1） (1).xlsx'
    xl = pd.ExcelFile(file_path)
    
    print(f"文件: {file_path}")
    print(f"Sheet列表: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        print(f"\n=== {sheet} ===")
        print(f"列名: {df.columns.tolist()}")
        print(f"行数: {len(df)}")
        print("前5行:")
        print(df.head(5))

if __name__ == '__main__':
    main()
