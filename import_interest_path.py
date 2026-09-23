#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入兴趣路径 - 从"电子信息工程兴趣路径梳理（v1）.xlsx"的Sheet1
"""

import pandas as pd
import sqlite3

def main():
    # 读取Excel文件
    df = pd.read_excel('data/2/电子信息工程兴趣路径梳理（v1）.xlsx', sheet_name='Sheet1')
    print("=" * 60)
    print("读取兴趣路径数据:")
    print("=" * 60)
    print(df)
    print(f"\n共 {len(df)} 行数据")
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. 先删除现有的兴趣路径 (path_id=100)
    print("\n" + "=" * 60)
    print("删除现有的兴趣路径 (path_id=100)...")
    print("=" * 60)
    cursor.execute("DELETE FROM main_path WHERE path_id = 100")
    print(f"  已删除 {cursor.rowcount} 条记录")
    
    # 2. 获取所有节点的映射
    cursor.execute("SELECT id, name FROM nodes")
    nodes = cursor.fetchall()
    node_map = {name: id for id, name in nodes}
    print(f"\n数据库中共有 {len(node_map)} 个节点")
    
    # 3. 导入新的兴趣路径
    print("\n" + "=" * 60)
    print("导入新的兴趣路径...")
    print("=" * 60)
    
    path_id = 100
    inserted = 0
    missing_nodes = set()
    
    for idx, row in df.iterrows():
        source_name = str(row['出发节点']).strip() if pd.notna(row['出发节点']) else None
        target_name = str(row['目的节点']).strip() if pd.notna(row['目的节点']) else None
        
        if not source_name or not target_name:
            continue
        
        # 查找节点ID
        source_id = node_map.get(source_name)
        target_id = node_map.get(target_name)
        
        if not source_id:
            missing_nodes.add(source_name)
            print(f"  [警告] 找不到出发节点: {source_name}")
        if not target_id:
            missing_nodes.add(target_name)
            print(f"  [警告] 找不到目的节点: {target_name}")
        
        if source_id and target_id:
            cursor.execute("""
                INSERT INTO main_path (path_id, source_id, target_id, path_order)
                VALUES (?, ?, ?, ?)
            """, (path_id, source_id, target_id, idx + 1))
            inserted += 1
            print(f"  [{idx+1}] {source_name} -> {target_name}")
    
    conn.commit()
    
    # 4. 显示结果
    print("\n" + "=" * 60)
    print("导入结果:")
    print("=" * 60)
    print(f"  成功导入: {inserted} 条记录")
    
    if missing_nodes:
        print(f"\n  缺失的节点 ({len(missing_nodes)} 个):")
        for node in sorted(missing_nodes):
            print(f"    - {node}")
    
    # 5. 验证
    cursor.execute("SELECT COUNT(*) FROM main_path WHERE path_id = 100")
    count = cursor.fetchone()[0]
    print(f"\n  兴趣路径 (path_id=100) 现有 {count} 条记录")
    
    conn.close()
    print("\n完成！")

if __name__ == '__main__':
    main()
