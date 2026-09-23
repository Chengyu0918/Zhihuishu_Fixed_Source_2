#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入主干知识点程序
处理"新增知识点 - 主干.xlsx"文件
- 将知识点导入数据库
- 设置权重为15
"""

import sqlite3
import pandas as pd
import os
import hashlib

# 层级名称映射
LAYER_MAPPING = {
    '3': 'LAYER_PROFESSIONAL',
    '4': 'LAYER_DISCIPLINE_BASE',
    '5': 'LAYER_ADVANCED_BASE',
    '6': 'LAYER_MATH_PHYSICS',
    3: 'LAYER_PROFESSIONAL',
    4: 'LAYER_DISCIPLINE_BASE',
    5: 'LAYER_ADVANCED_BASE',
    6: 'LAYER_MATH_PHYSICS',
}

def generate_id(name):
    """生成节点ID"""
    return hashlib.md5(name.encode('utf-8')).hexdigest()[:12]

def import_main_knowledge():
    """导入主干知识点"""
    filepath = os.path.join('data', '2', '新增知识点 - 主干.xlsx')
    
    if not os.path.exists(filepath):
        print(f"错误：文件不存在 - {filepath}")
        return
    
    print(f"正在读取文件: {filepath}")
    
    # 读取Excel文件
    df = pd.read_excel(filepath)
    
    print(f"列名: {list(df.columns)}")
    print(f"共 {len(df)} 行数据")
    
    # 获取列名
    col_name = df.columns[0]  # 知识点
    col_category = df.columns[1]  # 课程名
    col_layer = df.columns[2]  # 层级
    
    # 连接数据库
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 统计
    updated_count = 0
    inserted_count = 0
    weight_updated_count = 0
    
    for index, row in df.iterrows():
        name = str(row[col_name]).strip() if pd.notna(row[col_name]) else ''
        category = str(row[col_category]).strip() if pd.notna(row[col_category]) else ''
        layer = row[col_layer] if pd.notna(row[col_layer]) else ''
        
        # 跳过空行
        if not name:
            continue
        
        # 转换层级
        layer_key = LAYER_MAPPING.get(layer) or LAYER_MAPPING.get(str(layer))
        if not layer_key:
            print(f"  警告：未知层级 '{layer}'，跳过节点 '{name}'")
            continue
        
        # 查找节点是否存在
        cursor.execute("SELECT id, layer, weight FROM nodes WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            # 节点存在，更新层级和权重
            node_id = existing[0]
            old_layer = existing[1]
            old_weight = existing[2]
            
            # 更新层级
            if old_layer != layer_key:
                cursor.execute("UPDATE nodes SET layer = ? WHERE id = ?", (layer_key, node_id))
                print(f"  更新层级: {name} ({old_layer} -> {layer_key})")
                updated_count += 1
            
            # 更新权重为15
            if old_weight != 15:
                cursor.execute("UPDATE nodes SET weight = 15 WHERE id = ?", (node_id,))
                print(f"  更新权重: {name} ({old_weight} -> 15)")
                weight_updated_count += 1
        else:
            # 节点不存在，插入新节点
            node_id = generate_id(name)
            
            # 查找大类节点
            parent_id = None
            if category:
                cursor.execute("SELECT id FROM nodes WHERE name = ?", (category,))
                parent_result = cursor.fetchone()
                if parent_result:
                    parent_id = parent_result[0]
            
            # 插入新节点，权重设为15
            cursor.execute('''
                INSERT INTO nodes (id, name, layer, node_type, parent_id, weight)
                VALUES (?, ?, ?, 'leaf', ?, 15)
            ''', (node_id, name, layer_key, parent_id))
            
            # 如果有大类，创建边关系
            if parent_id:
                cursor.execute('''
                    SELECT 1 FROM edges WHERE source_id = ? AND target_id = ?
                ''', (parent_id, node_id))
                if not cursor.fetchone():
                    cursor.execute('''
                        INSERT INTO edges (source_id, target_id) VALUES (?, ?)
                    ''', (parent_id, node_id))
            
            print(f"  新增: {name} (层级: {layer_key}, 大类: {category}, 权重: 15)")
            inserted_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n导入完成!")
    print(f"  新增节点: {inserted_count} 个")
    print(f"  更新层级: {updated_count} 个")
    print(f"  更新权重: {weight_updated_count} 个")
    print(f"  所有主干知识点权重已设为 15")

if __name__ == '__main__':
    import_main_knowledge()
