#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导入新增知识点(4).xlsx - 覆盖已有的，添加新的
列：知识点、课程名（大类）、层级
"""

import pandas as pd
import sqlite3
import uuid

def main():
    # 读取Excel文件
    df = pd.read_excel('data/2/新增知识点(4).xlsx')
    print("=" * 60)
    print("读取新增知识点数据:")
    print("=" * 60)
    print(f"总行数: {len(df)}")
    print(f"列名: {df.columns.tolist()}")
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 获取所有现有节点
    cursor.execute("SELECT id, name, layer FROM nodes")
    existing_nodes = {row[1]: {'id': row[0], 'layer': row[2]} for row in cursor.fetchall()}
    print(f"\n数据库中现有 {len(existing_nodes)} 个节点")
    
    # 获取所有大类节点（用于建立关系）
    cursor.execute("SELECT id, name FROM nodes WHERE node_type = 'category'")
    category_nodes = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"数据库中现有 {len(category_nodes)} 个大类节点")
    
    # 统计
    added = 0
    updated = 0
    skipped = 0
    relations_added = 0
    
    print("\n" + "=" * 60)
    print("处理知识点...")
    print("=" * 60)
    
    for idx, row in df.iterrows():
        knowledge_name = str(row['知识点']).strip() if pd.notna(row['知识点']) else None
        course_name = str(row['课程名']).strip() if pd.notna(row['课程名']) else None
        layer = int(row['层级']) if pd.notna(row['层级']) else 4
        
        if not knowledge_name:
            skipped += 1
            continue
        
        # 检查节点是否已存在
        if knowledge_name in existing_nodes:
            # 更新层级（如果不同）
            existing = existing_nodes[knowledge_name]
            if existing['layer'] != layer:
                cursor.execute("UPDATE nodes SET layer = ? WHERE id = ?", (layer, existing['id']))
                print(f"  [更新] {knowledge_name}: 层级 {existing['layer']} -> {layer}")
                updated += 1
            else:
                # 层级相同，跳过
                pass
            node_id = existing['id']
        else:
            # 添加新节点
            node_id = f"new_v4_{uuid.uuid4().hex[:8]}"
            cursor.execute("""
                INSERT INTO nodes (id, name, layer, node_type)
                VALUES (?, ?, ?, 'knowledge')
            """, (node_id, knowledge_name, layer))
            existing_nodes[knowledge_name] = {'id': node_id, 'layer': layer}
            print(f"  [新增] {knowledge_name} (层级: {layer}, 课程: {course_name})")
            added += 1
        
        # 建立与大类的关系（如果大类存在）
        if course_name and course_name in category_nodes:
            category_id = category_nodes[course_name]
            # 检查关系是否已存在
            cursor.execute("""
                SELECT 1 FROM edges WHERE source_id = ? AND target_id = ?
            """, (category_id, node_id))
            if not cursor.fetchone():
                edge_id = f"edge_{uuid.uuid4().hex[:8]}"
                cursor.execute("""
                    INSERT INTO edges (id, source_id, target_id, relation_type)
                    VALUES (?, ?, ?, 'contains')
                """, (edge_id, category_id, node_id))
                relations_added += 1
    
    conn.commit()
    
    # 显示结果
    print("\n" + "=" * 60)
    print("导入结果:")
    print("=" * 60)
    print(f"  新增节点: {added} 个")
    print(f"  更新节点: {updated} 个")
    print(f"  跳过: {skipped} 个")
    print(f"  新增关系: {relations_added} 条")
    
    # 验证
    cursor.execute("SELECT COUNT(*) FROM nodes")
    total_nodes = cursor.fetchone()[0]
    print(f"\n  数据库现有节点总数: {total_nodes}")
    
    conn.close()
    print("\n完成！")

if __name__ == '__main__':
    main()
