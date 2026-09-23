"""
从 Excel 文件导入跨层关系到数据库
Excel结构（3  xxx.xlsx 文件）：
- 第1列：源层课程名称（大类）
- 第2列：源层知识点（小类）- 源节点
- 第3列：目标层课程名称（大类）
- 第4列：目标层知识点（小类）- 目标节点

每建立一条关系，两个节点的 weight 都加1（表示被引用次数）
"""

import pandas as pd
import sqlite3
import os
import glob

def build_name_to_id_map(db_path='database.db'):
    """构建节点名称到ID的映射表"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM nodes')
    rows = cursor.fetchall()
    
    name_to_id = {}
    for row in rows:
        node_id = row[0]
        name = row[1]
        if name not in name_to_id:
            name_to_id[name] = node_id
    
    conn.close()
    return name_to_id

def import_cross_layer_excel(excel_file, db_path='database.db', name_to_id=None):
    """导入单个Excel文件"""
    print(f"\n正在处理: {excel_file}")
    
    df = pd.read_excel(excel_file)
    print(f"  读取到 {len(df)} 行数据")
    print(f"  列名: {df.columns.tolist()}")
    
    # 根据列名获取数据
    # 第2列是源节点（知识点），第4列是目标节点（知识点）
    cols = df.columns.tolist()
    source_col = cols[1]  # 源层知识点
    target_col = cols[3]  # 目标层知识点
    
    print(f"  源节点列: {source_col}")
    print(f"  目标节点列: {target_col}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    edges_added = 0
    edges_updated = 0
    edges_skipped = 0
    not_found_sources = set()
    not_found_targets = set()
    
    for idx, row in df.iterrows():
        source_name = str(row[source_col]).strip() if pd.notna(row[source_col]) else None
        target_name = str(row[target_col]).strip() if pd.notna(row[target_col]) else None
        
        if not source_name or not target_name:
            edges_skipped += 1
            continue
        
        # 查找源节点ID
        source_id = name_to_id.get(source_name)
        if not source_id:
            not_found_sources.add(source_name)
            edges_skipped += 1
            continue
        
        # 查找目标节点ID
        target_id = name_to_id.get(target_name)
        if not target_id:
            not_found_targets.add(target_name)
            edges_skipped += 1
            continue
        
        # 检查边是否已存在（跨层关系类型为 cross）
        cursor.execute('''
            SELECT id FROM edges 
            WHERE source_id = ? AND target_id = ? AND relation_type = 'cross'
        ''', (source_id, target_id))
        
        existing = cursor.fetchone()
        
        if existing:
            # 边已存在，跳过（不重复创建边）
            edges_updated += 1
        else:
            # 如果不存在，插入新边
            cursor.execute('''
                INSERT INTO edges (source_id, target_id, relation_type, weight)
                VALUES (?, ?, ?, ?)
            ''', (source_id, target_id, 'cross', 1.0))
            edges_added += 1
        
        # 无论边是否已存在，两个节点的 weight 都要加1（表示被引用次数）
        cursor.execute('UPDATE nodes SET weight = weight + 1 WHERE id = ?', (source_id,))
        cursor.execute('UPDATE nodes SET weight = weight + 1 WHERE id = ?', (target_id,))
    
    conn.commit()
    conn.close()
    
    print(f"  新增边: {edges_added}, 已存在: {edges_updated}, 跳过: {edges_skipped}")
    
    if not_found_sources:
        print(f"  未找到的源节点 ({len(not_found_sources)}个): {list(not_found_sources)[:5]}...")
    if not_found_targets:
        print(f"  未找到的目标节点 ({len(not_found_targets)}个): {list(not_found_targets)[:5]}...")
    
    return edges_added, edges_updated, edges_skipped

def clear_cross_edges(db_path='database.db'):
    """清空跨层关系的边"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM edges WHERE relation_type = 'cross'")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"已删除 {deleted} 条跨层关系的边")
    return deleted

def show_weight_stats(db_path='database.db'):
    """显示节点 weight 统计"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 各层统计
    cursor.execute('''
        SELECT layer, COUNT(*) as total, SUM(weight) as total_weight, MAX(weight) as max_weight 
        FROM nodes GROUP BY layer
    ''')
    print('\n各层节点 weight 统计:')
    print('层 | 节点数 | 总weight | 最大weight')
    print('-' * 60)
    for row in cursor.fetchall():
        print(f'{row[0]} | {row[1]} | {row[2]} | {row[3]}')
    
    conn.close()

def main():
    # 查找所有 "3  xxx.xlsx" 的Excel文件
    excel_pattern = 'data/3  *.xlsx'
    excel_files = glob.glob(excel_pattern)
    
    if not excel_files:
        print(f"没有找到匹配 '{excel_pattern}' 的文件")
        return
    
    print(f"找到 {len(excel_files)} 个Excel文件:")
    for f in excel_files:
        print(f"  - {f}")
    
    # 构建名称到ID的映射
    print("\n正在构建节点名称映射...")
    name_to_id = build_name_to_id_map()
    print(f"已加载 {len(name_to_id)} 个节点名称")
    
    # 显示导入前的统计
    print("\n导入前的节点 weight 统计:")
    show_weight_stats()
    
    # 开始导入
    total_added = 0
    total_updated = 0
    total_skipped = 0
    
    for excel_file in excel_files:
        try:
            added, updated, skipped = import_cross_layer_excel(
                excel_file, 
                name_to_id=name_to_id
            )
            total_added += added
            total_updated += updated
            total_skipped += skipped
        except Exception as e:
            print(f"导入出错: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print("总计:")
    print(f"  新建立的关系: {total_added}")
    print(f"  已存在的关系: {total_updated}")
    print(f"  跳过: {total_skipped}")
    
    # 显示导入后的统计
    print("\n导入后的节点 weight 统计:")
    show_weight_stats()

if __name__ == '__main__':
    main()
