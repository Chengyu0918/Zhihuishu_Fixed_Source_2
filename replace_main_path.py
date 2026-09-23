#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
删除现有主路径(path_id=1)并从Excel导入新的主路径
"""

import sqlite3
import openpyxl
import hashlib

DATABASE_PATH = 'database.db'
EXCEL_FILE = 'data/2/副本副本电子信息工程主路径梳理.xlsx'

def generate_id(name):
    """生成节点ID"""
    return hashlib.md5(name.encode()).hexdigest()[:12]

def main():
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 1. 删除现有的主路径(path_id=1)
    print("删除现有主路径(path_id=1)...")
    cursor.execute('DELETE FROM main_path WHERE path_id = 1')
    deleted_count = cursor.rowcount
    print(f"  已删除 {deleted_count} 条记录")
    
    # 2. 读取Excel文件
    print(f"\n读取Excel文件: {EXCEL_FILE}")
    wb = openpyxl.load_workbook(EXCEL_FILE)
    ws = wb.active
    
    # 3. 导入新的主路径
    print("\n导入新的主路径...")
    path_order = 0
    imported_count = 0
    
    for row in ws.iter_rows(min_row=2, values_only=True):
        source_name = row[0]
        target_name = row[1]
        
        if not source_name or not target_name:
            continue
            
        source_name = str(source_name).strip()
        target_name = str(target_name).strip()
        
        if not source_name or not target_name:
            continue
        
        # 查找节点ID
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (source_name,))
        source_result = cursor.fetchone()
        source_id = source_result[0] if source_result else generate_id(source_name)
        
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (target_name,))
        target_result = cursor.fetchone()
        target_id = target_result[0] if target_result else generate_id(target_name)
        
        # 插入主路径记录
        cursor.execute('''
            INSERT INTO main_path (source_name, target_name, source_id, target_id, path_order, path_id, path_name)
            VALUES (?, ?, ?, ?, ?, 1, '主路径')
        ''', (source_name, target_name, source_id, target_id, path_order))
        
        path_order += 1
        imported_count += 1
        
        if not source_result:
            print(f"  警告: 源节点 '{source_name}' 不在数据库中")
        if not target_result:
            print(f"  警告: 目标节点 '{target_name}' 不在数据库中")
    
    conn.commit()
    
    print(f"\n导入完成!")
    print(f"  共导入 {imported_count} 条主路径关系")
    
    # 4. 验证导入结果
    cursor.execute('SELECT COUNT(*) FROM main_path WHERE path_id = 1')
    count = cursor.fetchone()[0]
    print(f"  数据库中主路径(path_id=1)记录数: {count}")
    
    conn.close()

if __name__ == '__main__':
    main()
