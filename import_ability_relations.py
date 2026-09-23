"""
从 Excel 文件导入能力层与其他层的关系到数据库
Excel结构：
- 第1列：专业能力名称（能力层节点）
- 第2列：课程类别（连接层类型）
- 第3列：课程名称（大类）
- 第4列：知识点内容（小类/具体知识节点）
- 第8列：综合相关度（权重值）
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

def import_ability_excel(excel_file, db_path='database.db', name_to_id=None):
    """导入单个Excel文件"""
    print(f"\n正在处理: {excel_file}")
    
    df = pd.read_excel(excel_file)
    print(f"  读取到 {len(df)} 行数据")
    
    # 列名
    ability_col = '专业能力名称'
    course_type_col = '课程类别'
    course_name_col = '课程名称'
    kp_col = '知识点内容'
    weight_col = '综合相关度'
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    edges_added = 0
    edges_updated = 0
    edges_skipped = 0
    not_found_abilities = set()
    not_found_kps = set()
    
    for idx, row in df.iterrows():
        ability_name = str(row[ability_col]).strip() if pd.notna(row[ability_col]) else None
        kp_name = str(row[kp_col]).strip() if pd.notna(row[kp_col]) else None
        weight = float(row[weight_col]) if pd.notna(row[weight_col]) else 0.0
        
        if not ability_name or not kp_name:
            edges_skipped += 1
            continue
        
        # 查找能力节点ID
        source_id = name_to_id.get(ability_name)
        if not source_id:
            not_found_abilities.add(ability_name)
            edges_skipped += 1
            continue
        
        # 查找知识点节点ID
        target_id = name_to_id.get(kp_name)
        if not target_id:
            not_found_kps.add(kp_name)
            edges_skipped += 1
            continue
        
        # 检查边是否已存在（同一类型的边）
        cursor.execute('''
            SELECT id, weight FROM edges 
            WHERE source_id = ? AND target_id = ? AND relation_type = 'ability_to_kp'
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
            ''', (source_id, target_id, 'ability_to_kp', 1.0))
            edges_added += 1
        
        # 无论边是否已存在，两个节点的 weight 都要加1（表示被引用次数）
        cursor.execute('UPDATE nodes SET weight = weight + 1 WHERE id = ?', (source_id,))
        cursor.execute('UPDATE nodes SET weight = weight + 1 WHERE id = ?', (target_id,))
        
        # 每次操作后立即提交，确保后续查询能看到
        conn.commit()
    
    conn.close()
    
    print(f"  新增: {edges_added}, 更新: {edges_updated}, 跳过: {edges_skipped}")
    
    if not_found_abilities:
        print(f"  未找到的能力节点 ({len(not_found_abilities)}个): {list(not_found_abilities)[:5]}...")
    if not_found_kps:
        print(f"  未找到的知识点节点 ({len(not_found_kps)}个): {list(not_found_kps)[:5]}...")
    
    return edges_added, edges_updated, edges_skipped

def clear_ability_edges(db_path='database.db'):
    """清空能力相关的边"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM edges WHERE relation_type = 'ability_to_kp'")
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"已删除 {deleted} 条能力相关的边")
    return deleted

def main():
    # 查找所有 "2  14能力-xxx" 的Excel文件
    excel_pattern = 'data/2  14能力-*.xlsx'
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
    
    # 清空旧数据，确保重新导入时 weight 正确
    print("\n清空旧的能力关系数据...")
    clear_ability_edges()
    
    # 开始导入
    total_added = 0
    total_updated = 0
    total_skipped = 0
    
    for excel_file in excel_files:
        try:
            added, updated, skipped = import_ability_excel(
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
    print(f"  更新的关系: {total_updated}")
    print(f"  跳过: {total_skipped}")

if __name__ == '__main__':
    main()
