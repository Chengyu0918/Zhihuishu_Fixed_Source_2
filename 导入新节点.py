#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入知识节点程序
Excel格式：第一列是知识点名称，第二列是所属大类，第三列是所属层级
- 如果知识点已存在，则更新其层级
- 如果知识点不存在，则根据大类创建新节点并建立关联
"""

import sqlite3
import pandas as pd
import os
import hashlib

# 层级名称映射
LAYER_MAPPING = {
    # 中文名称映射
    '能力层': 'LAYER_ABILITY',
    '问题层': 'LAYER_PROBLEM',
    '专业课': 'LAYER_PROFESSIONAL',
    '学科基础': 'LAYER_DISCIPLINE_BASE',
    '高阶基础': 'LAYER_ADVANCED_BASE',
    '数理基础': 'LAYER_MATH_PHYSICS',
    # 数字映射（1-6层）
    '1': 'LAYER_ABILITY',
    '2': 'LAYER_PROBLEM',
    '3': 'LAYER_PROFESSIONAL',
    '4': 'LAYER_DISCIPLINE_BASE',
    '5': 'LAYER_ADVANCED_BASE',
    '6': 'LAYER_MATH_PHYSICS',
    # 整数映射
    1: 'LAYER_ABILITY',
    2: 'LAYER_PROBLEM',
    3: 'LAYER_PROFESSIONAL',
    4: 'LAYER_DISCIPLINE_BASE',
    5: 'LAYER_ADVANCED_BASE',
    6: 'LAYER_MATH_PHYSICS',
    # 英文映射
    'LAYER_ABILITY': 'LAYER_ABILITY',
    'LAYER_PROBLEM': 'LAYER_PROBLEM',
    'LAYER_PROFESSIONAL': 'LAYER_PROFESSIONAL',
    'LAYER_DISCIPLINE_BASE': 'LAYER_DISCIPLINE_BASE',
    'LAYER_ADVANCED_BASE': 'LAYER_ADVANCED_BASE',
    'LAYER_MATH_PHYSICS': 'LAYER_MATH_PHYSICS',
}

def generate_id(name):
    """生成节点ID"""
    return hashlib.md5(name.encode('utf-8')).hexdigest()[:12]

def get_or_create_category(cursor, category_name, layer_key):
    """获取或创建大类节点"""
    # 先查找是否存在
    cursor.execute("SELECT id FROM nodes WHERE name = ?", (category_name,))
    result = cursor.fetchone()
    if result:
        return result[0]
    
    # 不存在则创建
    category_id = generate_id(category_name)
    cursor.execute('''
        INSERT INTO nodes (id, name, layer, node_type)
        VALUES (?, ?, ?, 'category')
    ''', (category_id, category_name, layer_key))
    print(f"  [新建大类] {category_name} (层级: {layer_key})")
    return category_id

def create_edge_if_not_exists(cursor, source_id, target_id):
    """如果边不存在则创建"""
    cursor.execute('''
        SELECT 1 FROM edges WHERE source_id = ? AND target_id = ?
    ''', (source_id, target_id))
    if not cursor.fetchone():
        cursor.execute('''
            INSERT INTO edges (source_id, target_id) VALUES (?, ?)
        ''', (source_id, target_id))
        return True
    return False

def import_knowledge_nodes(filename):
    """
    导入知识节点
    
    Args:
        filename: Excel文件名（不含路径，放在 data/2 文件夹下）
    """
    # 构建完整路径
    filepath = os.path.join('data', '2', filename)
    
    if not os.path.exists(filepath):
        print(f"错误：文件不存在 - {filepath}")
        return
    
    print(f"正在读取文件: {filepath}")
    
    # 读取Excel文件
    try:
        df = pd.read_excel(filepath)
    except Exception as e:
        print(f"读取Excel文件失败: {e}")
        return
    
    # 检查列数
    if len(df.columns) < 3:
        print(f"错误：Excel文件至少需要3列（知识点、所属大类、所属层级），当前只有 {len(df.columns)} 列")
        return
    
    # 获取列名
    col_name = df.columns[0]  # 知识点名称
    col_category = df.columns[1]  # 所属大类
    col_layer = df.columns[2]  # 所属层级
    
    print(f"列名: {col_name}, {col_category}, {col_layer}")
    print(f"共 {len(df)} 行数据")
    
    # 连接数据库
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 统计
    updated_count = 0
    inserted_count = 0
    skipped_count = 0
    error_count = 0
    
    for index, row in df.iterrows():
        name = str(row[col_name]).strip() if pd.notna(row[col_name]) else ''
        category = str(row[col_category]).strip() if pd.notna(row[col_category]) else ''
        layer = str(row[col_layer]).strip() if pd.notna(row[col_layer]) else ''
        
        # 跳过空行
        if not name:
            skipped_count += 1
            continue
        
        # 转换层级名称
        layer_key = LAYER_MAPPING.get(layer)
        if not layer_key:
            print(f"  警告：未知层级 '{layer}'，跳过节点 '{name}'")
            error_count += 1
            continue
        
        # 查找节点是否存在
        cursor.execute("SELECT id, layer FROM nodes WHERE name = ?", (name,))
        existing = cursor.fetchone()
        
        if existing:
            # 节点存在，始终用Excel中的层级覆盖
            old_layer = existing[1]
            if old_layer != layer_key:
                cursor.execute("UPDATE nodes SET layer = ? WHERE name = ?", (layer_key, name))
                print(f"  更新: {name} 层级从 {old_layer} 改为 {layer_key}")
                updated_count += 1
            else:
                # 层级相同，也算更新（覆盖）
                cursor.execute("UPDATE nodes SET layer = ? WHERE name = ?", (layer_key, name))
                print(f"  覆盖: {name} 层级保持 {layer_key}")
                updated_count += 1
        else:
            # 节点不存在，插入新节点
            node_id = generate_id(name)
            
            # 获取或创建大类节点
            parent_id = None
            if category:
                # 先尝试查找已存在的大类（不限制node_type，因为可能是其他类型）
                cursor.execute("SELECT id FROM nodes WHERE name = ?", (category,))
                parent_result = cursor.fetchone()
                if parent_result:
                    parent_id = parent_result[0]
                else:
                    # 大类不存在，创建新的大类节点
                    parent_id = get_or_create_category(cursor, category, layer_key)
            
            # 插入新节点
            cursor.execute('''
                INSERT INTO nodes (id, name, layer, node_type, parent_id)
                VALUES (?, ?, ?, 'leaf', ?)
            ''', (node_id, name, layer_key, parent_id))
            
            # 如果有大类，创建边关系（大类 -> 知识点）
            if parent_id:
                create_edge_if_not_exists(cursor, parent_id, node_id)
            
            print(f"  新增: {name} (层级: {layer_key}, 大类: {category or '无'})")
            inserted_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n导入完成!")
    print(f"  更新: {updated_count} 个节点")
    print(f"  新增: {inserted_count} 个节点")
    print(f"  跳过: {skipped_count} 个节点")
    print(f"  错误: {error_count} 个节点")

def main():
    print("=" * 50)
    print("知识节点导入程序")
    print("=" * 50)
    print("\nExcel格式要求：")
    print("  第一列：知识点名称")
    print("  第二列：所属大类")
    print("  第三列：所属层级（能力层/问题层/专业课/学科基础/高阶基础/数理基础）")
    print("\n文件位置：data/1/ 文件夹下")
    print("-" * 50)
    
    # 列出 data/2 文件夹下的 Excel 文件
    data_dir = os.path.join('data', '2')
    if os.path.exists(data_dir):
        excel_files = [f for f in os.listdir(data_dir) if f.endswith(('.xlsx', '.xls'))]
        if excel_files:
            print("\n可用的Excel文件：")
            for i, f in enumerate(excel_files, 1):
                print(f"  {i}. {f}")
    
    print()
    filename = input("请输入Excel文件名（如 test.xlsx）: ").strip()
    
    if filename:
        import_knowledge_nodes(filename)
    else:
        print("未输入文件名，退出程序")

if __name__ == '__main__':
    main()
