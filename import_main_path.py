"""
导入主路径数据
从 data/2/副本电子信息工程主路径梳理 (1).xlsx 导入主路径关系
"""

import sqlite3
import pandas as pd

DB_PATH = 'database.db'

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def import_main_path():
    """导入主路径数据"""
    # 读取Excel文件
    file_path = 'data/2/副本电子信息工程主路径梳理 (1).xlsx'
    df = pd.read_excel(file_path)
    
    print(f"读取到 {len(df)} 条主路径关系")
    print(f"列名: {df.columns.tolist()}")
    print(f"\n前5条数据:")
    print(df.head())
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 创建主路径表（如果不存在）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS main_path (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source_name TEXT NOT NULL,
            target_name TEXT NOT NULL,
            source_id TEXT,
            target_id TEXT,
            path_order INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # 清空现有数据
    cursor.execute('DELETE FROM main_path')
    print("\n已清空现有主路径数据")
    
    # 导入新数据
    imported_count = 0
    not_found_nodes = set()
    
    for index, row in df.iterrows():
        source_name = str(row['出发节点']).strip() if pd.notna(row['出发节点']) else None
        target_name = str(row['目的节点']).strip() if pd.notna(row['目的节点']) else None
        
        if not source_name or not target_name:
            continue
        
        # 查找源节点ID
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (source_name,))
        source_row = cursor.fetchone()
        source_id = source_row['id'] if source_row else None
        
        # 查找目标节点ID
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (target_name,))
        target_row = cursor.fetchone()
        target_id = target_row['id'] if target_row else None
        
        # 记录未找到的节点
        if not source_id:
            not_found_nodes.add(source_name)
        if not target_id:
            not_found_nodes.add(target_name)
        
        # 插入主路径关系
        cursor.execute('''
            INSERT INTO main_path (source_name, target_name, source_id, target_id, path_order)
            VALUES (?, ?, ?, ?, ?)
        ''', (source_name, target_name, source_id, target_id, index))
        
        imported_count += 1
        print(f"导入: {source_name} -> {target_name} (source_id={source_id}, target_id={target_id})")
    
    conn.commit()
    
    print(f"\n导入完成！共导入 {imported_count} 条主路径关系")
    
    if not_found_nodes:
        print(f"\n警告：以下 {len(not_found_nodes)} 个节点在数据库中未找到:")
        for node in sorted(not_found_nodes):
            print(f"  - {node}")
    
    # 显示导入结果
    cursor.execute('SELECT COUNT(*) as count FROM main_path')
    total = cursor.fetchone()['count']
    
    cursor.execute('SELECT COUNT(*) as count FROM main_path WHERE source_id IS NOT NULL AND target_id IS NOT NULL')
    valid = cursor.fetchone()['count']
    
    print(f"\n主路径表统计:")
    print(f"  总记录数: {total}")
    print(f"  有效记录数（两端节点都存在）: {valid}")
    
    conn.close()

if __name__ == '__main__':
    import_main_path()
