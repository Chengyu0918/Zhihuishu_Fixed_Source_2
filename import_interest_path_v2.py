#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入兴趣路径 - 从"电子信息工程兴趣路径梳理（v1）.xlsx"的Sheet1
包括添加缺失的节点
"""

import pandas as pd
import sqlite3
import uuid

# 课程到层级的映射
COURSE_LAYER_MAP = {
    '雷达原理与系统': 3,      # 专业课
    '场、波与天线技术': 4,    # 学科基础
    '通信与网络': 4,          # 学科基础
    '信号检测与估计': 4,      # 学科基础
    '大数据导论': 4,          # 学科基础
    '人工智能引论': 4,        # 学科基础
}

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
    
    # 3. 收集所有需要的节点
    all_nodes = set()
    node_course_map = {}  # 节点名 -> 课程名
    
    for idx, row in df.iterrows():
        source_name = str(row['出发节点']).strip() if pd.notna(row['出发节点']) else None
        target_name = str(row['目的节点']).strip() if pd.notna(row['目的节点']) else None
        course_name = str(row['Unnamed: 2']).strip() if pd.notna(row['Unnamed: 2']) else None
        
        if source_name:
            all_nodes.add(source_name)
            if course_name and source_name not in node_course_map:
                node_course_map[source_name] = course_name
        if target_name:
            all_nodes.add(target_name)
    
    # 4. 添加缺失的节点
    print("\n" + "=" * 60)
    print("检查并添加缺失的节点...")
    print("=" * 60)
    
    added_nodes = 0
    for node_name in all_nodes:
        if node_name not in node_map:
            # 确定层级
            course_name = node_course_map.get(node_name, '')
            layer = COURSE_LAYER_MAP.get(course_name, 3)  # 默认专业课层
            
            # 生成节点ID
            node_id = f"interest_{uuid.uuid4().hex[:8]}"
            
            # 插入节点
            cursor.execute("""
                INSERT INTO nodes (id, name, layer, node_type)
                VALUES (?, ?, ?, 'knowledge')
            """, (node_id, node_name, layer))
            
            node_map[node_name] = node_id
            added_nodes += 1
            print(f"  添加节点: {node_name} (层级: {layer}, 课程: {course_name})")
    
    print(f"\n  共添加 {added_nodes} 个新节点")
    
    # 5. 导入兴趣路径
    print("\n" + "=" * 60)
    print("导入兴趣路径...")
    print("=" * 60)
    
    path_id = 100
    path_name = "兴趣路径1"
    inserted = 0
    
    for idx, row in df.iterrows():
        source_name = str(row['出发节点']).strip() if pd.notna(row['出发节点']) else None
        target_name = str(row['目的节点']).strip() if pd.notna(row['目的节点']) else None
        
        if not source_name or not target_name:
            continue
        
        source_id = node_map.get(source_name)
        target_id = node_map.get(target_name)
        
        if source_id and target_id:
            cursor.execute("""
                INSERT INTO main_path (path_id, path_name, source_name, target_name, source_id, target_id, path_order)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (path_id, path_name, source_name, target_name, source_id, target_id, idx + 1))
            inserted += 1
            print(f"  [{idx+1}] {source_name} -> {target_name}")
    
    conn.commit()
    
    # 6. 显示结果
    print("\n" + "=" * 60)
    print("导入结果:")
    print("=" * 60)
    print(f"  新增节点: {added_nodes} 个")
    print(f"  导入路径: {inserted} 条记录")
    
    # 7. 验证
    cursor.execute("SELECT COUNT(*) FROM main_path WHERE path_id = 100")
    count = cursor.fetchone()[0]
    print(f"\n  兴趣路径 (path_id=100) 现有 {count} 条记录")
    
    conn.close()
    print("\n完成！")

if __name__ == '__main__':
    main()
