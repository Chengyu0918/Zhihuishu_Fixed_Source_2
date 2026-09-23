#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入拓展路径（多条路径从多个Sheet）
"""

import pandas as pd
import sqlite3
import sys
import os

DB_PATH = 'database.db'


def get_node_id_by_name(cursor, name):
    """根据节点名称查找节点ID"""
    cursor.execute('SELECT id FROM nodes WHERE name = ?', (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def import_extension_paths(excel_file, base_path_id=2):
    """
    导入拓展路径数据（从多个Sheet）
    
    Args:
        excel_file: Excel文件路径
        base_path_id: 基础路径ID，每个Sheet会递增
    """
    if not os.path.exists(excel_file):
        print(f"错误: 文件不存在 {excel_file}")
        return False
    
    # 读取Excel文件
    print(f"读取文件: {excel_file}")
    xl = pd.ExcelFile(excel_file)
    print(f"Sheet列表: {xl.sheet_names}")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 确保main_path表有path_id和path_name列
    cursor.execute('PRAGMA table_info(main_path)')
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'path_id' not in columns:
        print("添加 path_id 列...")
        cursor.execute('ALTER TABLE main_path ADD COLUMN path_id INTEGER DEFAULT 1')
    
    if 'path_name' not in columns:
        print("添加 path_name 列...")
        cursor.execute('ALTER TABLE main_path ADD COLUMN path_name TEXT')
    
    # 清除所有拓展路径数据（path_id >= 2）
    cursor.execute('DELETE FROM main_path WHERE path_id >= 2')
    print(f"已清除所有拓展路径数据")
    
    total_imported = 0
    all_missing_nodes = set()
    
    # 路径名称映射（根据Sheet内容的第一行确定）
    path_names = {
        'Sheet1': '拓展路径1-抗干扰协同感知',
        'Sheet2': '拓展路径2-分布式无源协同定位',
        'Sheet3': '拓展路径3-认知电子战闭环对抗',
        'Sheet5': '拓展路径4-多模态光电雷达识别',
        'Sheet6': '拓展路径5-资源受限轻量化感知'
    }
    
    for idx, sheet in enumerate(xl.sheet_names):
        df = pd.read_excel(xl, sheet_name=sheet)
        
        # 检查列名（支持"出发点/结束点"或"出发节点/目的节点"）
        source_col = None
        target_col = None
        
        if '出发点' in df.columns:
            source_col = '出发点'
        elif '出发节点' in df.columns:
            source_col = '出发节点'
        
        if '结束点' in df.columns:
            target_col = '结束点'
        elif '目的节点' in df.columns:
            target_col = '目的节点'
        
        if not source_col or not target_col:
            print(f"警告: {sheet} 缺少必要的列，跳过")
            continue
        
        path_id = base_path_id + idx
        path_name = path_names.get(sheet, f'拓展路径{idx + 1}')
        
        print(f"\n导入 {sheet}: {path_name} (path_id={path_id})")
        print(f"  数据行数: {len(df)}")
        
        imported_count = 0
        missing_nodes = set()
        
        for row_idx, row in df.iterrows():
            source_name = str(row[source_col]).strip()
            target_name = str(row[target_col]).strip()
            
            if pd.isna(row[source_col]) or pd.isna(row[target_col]):
                continue
            
            # 查找节点ID
            source_id = get_node_id_by_name(cursor, source_name)
            target_id = get_node_id_by_name(cursor, target_name)
            
            if not source_id:
                missing_nodes.add(source_name)
                all_missing_nodes.add(source_name)
            if not target_id:
                missing_nodes.add(target_name)
                all_missing_nodes.add(target_name)
            
            # 插入数据
            cursor.execute('''
                INSERT INTO main_path (source_name, target_name, source_id, target_id, path_order, path_id, path_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (source_name, target_name, source_id, target_id, row_idx + 1, path_id, path_name))
            
            imported_count += 1
        
        print(f"  导入记录数: {imported_count}")
        if missing_nodes:
            print(f"  缺失节点: {len(missing_nodes)} 个")
        
        total_imported += imported_count
    
    conn.commit()
    
    # 统计结果
    print(f"\n========== 导入完成 ==========")
    print(f"总导入记录数: {total_imported}")
    
    if all_missing_nodes:
        print(f"\n警告: 以下 {len(all_missing_nodes)} 个节点在数据库中不存在:")
        for node in sorted(all_missing_nodes):
            print(f"  - {node}")
    
    # 显示当前所有路径
    cursor.execute('SELECT DISTINCT path_id, path_name, COUNT(*) as cnt FROM main_path GROUP BY path_id, path_name ORDER BY path_id')
    print("\n当前所有路径:")
    for row in cursor.fetchall():
        print(f"  path_id={row[0]}, 名称={row[1]}, 记录数={row[2]}")
    
    conn.close()
    return True


def main():
    """主函数"""
    excel_file = 'data/2/电子信息工程拓展路径梳理（v1） (1).xlsx'
    import_extension_paths(excel_file)


if __name__ == '__main__':
    main()
