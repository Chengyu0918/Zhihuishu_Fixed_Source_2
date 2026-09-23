#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
通用路径导入脚本
支持导入主路径(path_id=1)、拓展路径(path_id=2)、个性路径(path_id=3)
"""

import pandas as pd
import sqlite3
import sys
import os

DB_PATH = 'database.db'

# 路径类型配置
PATH_TYPES = {
    1: '主路径',
    2: '拓展路径',
    3: '个性路径'
}


def get_node_id_by_name(cursor, name):
    """根据节点名称查找节点ID"""
    cursor.execute('SELECT id FROM nodes WHERE name = ?', (name,))
    result = cursor.fetchone()
    return result[0] if result else None


def import_path(excel_file, path_id, path_name=None, clear_existing=True):
    """
    导入路径数据
    
    Args:
        excel_file: Excel文件路径
        path_id: 路径ID (1=主路径, 2=拓展路径, 3=个性路径)
        path_name: 路径名称（可选，默认使用PATH_TYPES中的名称）
        clear_existing: 是否清除该路径的现有数据
    """
    if path_id not in PATH_TYPES:
        print(f"错误: 无效的路径ID {path_id}，有效值为 1, 2, 3")
        return False
    
    if not os.path.exists(excel_file):
        print(f"错误: 文件不存在 {excel_file}")
        return False
    
    # 读取Excel文件
    print(f"读取文件: {excel_file}")
    df = pd.read_excel(excel_file)
    
    # 检查必要的列
    if '出发节点' not in df.columns or '目的节点' not in df.columns:
        print("错误: Excel文件必须包含'出发节点'和'目的节点'列")
        return False
    
    # 设置路径名称
    if path_name is None:
        path_name = PATH_TYPES[path_id]
    
    print(f"导入路径: {path_name} (path_id={path_id})")
    print(f"数据行数: {len(df)}")
    
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
    
    # 清除现有数据
    if clear_existing:
        cursor.execute('DELETE FROM main_path WHERE path_id = ?', (path_id,))
        print(f"已清除 path_id={path_id} 的现有数据")
    
    # 导入数据
    imported_count = 0
    missing_nodes = set()
    
    for idx, row in df.iterrows():
        source_name = str(row['出发节点']).strip()
        target_name = str(row['目的节点']).strip()
        
        if pd.isna(row['出发节点']) or pd.isna(row['目的节点']):
            continue
        
        # 查找节点ID
        source_id = get_node_id_by_name(cursor, source_name)
        target_id = get_node_id_by_name(cursor, target_name)
        
        if not source_id:
            missing_nodes.add(source_name)
        if not target_id:
            missing_nodes.add(target_name)
        
        # 插入数据
        cursor.execute('''
            INSERT INTO main_path (source_name, target_name, source_id, target_id, path_order, path_id, path_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (source_name, target_name, source_id, target_id, idx + 1, path_id, path_name))
        
        imported_count += 1
    
    conn.commit()
    
    # 统计结果
    print(f"\n导入完成!")
    print(f"导入记录数: {imported_count}")
    
    if missing_nodes:
        print(f"\n警告: 以下 {len(missing_nodes)} 个节点在数据库中不存在:")
        for node in sorted(missing_nodes):
            print(f"  - {node}")
    
    # 显示当前所有路径
    cursor.execute('SELECT DISTINCT path_id, path_name, COUNT(*) as cnt FROM main_path GROUP BY path_id, path_name')
    print("\n当前所有路径:")
    for row in cursor.fetchall():
        print(f"  path_id={row[0]}, 名称={row[1]}, 记录数={row[2]}")
    
    conn.close()
    return True


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: python import_path.py <excel_file> <path_id> [path_name]")
        print("")
        print("参数:")
        print("  excel_file  - Excel文件路径")
        print("  path_id     - 路径ID (1=主路径, 2=拓展路径, 3=个性路径)")
        print("  path_name   - 路径名称（可选）")
        print("")
        print("示例:")
        print("  python import_path.py data/2/主路径.xlsx 1")
        print("  python import_path.py data/2/拓展路径.xlsx 2 '拓展路径-目标检测'")
        print("  python import_path.py data/2/个性路径.xlsx 3 '个性路径-深度学习'")
        return
    
    excel_file = sys.argv[1]
    path_id = int(sys.argv[2])
    path_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    import_path(excel_file, path_id, path_name)


if __name__ == '__main__':
    main()
