"""
导入第二条主路径数据
从 data/2/电子信息工程主路径梳理（v1）.xlsx 导入主路径关系
支持多条主路径，通过 path_id 区分不同的主路径
"""

import sqlite3
import pandas as pd

DB_PATH = 'database.db'

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_path_id_column():
    """确保 main_path 表有 path_id 列"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查表是否存在
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='main_path'")
    if not cursor.fetchone():
        # 创建表（包含 path_id）
        cursor.execute('''
            CREATE TABLE main_path (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path_id INTEGER DEFAULT 1,
                path_name TEXT DEFAULT '主路径1',
                source_name TEXT NOT NULL,
                target_name TEXT NOT NULL,
                source_id TEXT,
                target_id TEXT,
                path_order INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        print("创建了新的 main_path 表（包含 path_id 列）")
    else:
        # 检查是否有 path_id 列
        cursor.execute('PRAGMA table_info(main_path)')
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'path_id' not in columns:
            # 添加 path_id 列
            cursor.execute('ALTER TABLE main_path ADD COLUMN path_id INTEGER DEFAULT 1')
            conn.commit()
            print("添加了 path_id 列")
        
        if 'path_name' not in columns:
            # 添加 path_name 列
            cursor.execute('ALTER TABLE main_path ADD COLUMN path_name TEXT DEFAULT "主路径1"')
            conn.commit()
            print("添加了 path_name 列")
        
        # 更新现有数据的 path_id 和 path_name
        cursor.execute('UPDATE main_path SET path_id = 1, path_name = "主路径1" WHERE path_id IS NULL')
        conn.commit()
    
    conn.close()

def import_main_path_v2():
    """导入第二条主路径数据"""
    # 确保表结构正确
    ensure_path_id_column()
    
    # 读取Excel文件
    file_path = 'data/2/电子信息工程主路径梳理（v1）.xlsx'
    df = pd.read_excel(file_path)
    
    print(f"读取到 {len(df)} 条主路径关系")
    print(f"列名: {df.columns.tolist()}")
    print(f"\n前5条数据:")
    print(df.head())
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 检查是否已存在 path_id = 2 的数据
    cursor.execute('SELECT COUNT(*) as count FROM main_path WHERE path_id = 2')
    existing_count = cursor.fetchone()['count']
    
    if existing_count > 0:
        print(f"\n发现已存在 {existing_count} 条主路径2的数据，将先删除...")
        cursor.execute('DELETE FROM main_path WHERE path_id = 2')
        conn.commit()
        print("已删除现有主路径2数据")
    
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
        
        # 插入主路径关系（path_id = 2）
        cursor.execute('''
            INSERT INTO main_path (path_id, path_name, source_name, target_name, source_id, target_id, path_order)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (2, '主路径2-目标协同跟踪', source_name, target_name, source_id, target_id, index))
        
        imported_count += 1
        status = "✓" if source_id and target_id else "⚠"
        print(f"{status} 导入: {source_name} -> {target_name}")
    
    conn.commit()
    
    print(f"\n导入完成！共导入 {imported_count} 条主路径关系")
    
    if not_found_nodes:
        print(f"\n警告：以下 {len(not_found_nodes)} 个节点在数据库中未找到:")
        for node in sorted(not_found_nodes):
            print(f"  - {node}")
    
    # 显示所有主路径统计
    print("\n" + "=" * 50)
    print("所有主路径统计:")
    print("=" * 50)
    
    cursor.execute('''
        SELECT path_id, path_name, COUNT(*) as count,
               SUM(CASE WHEN source_id IS NOT NULL AND target_id IS NOT NULL THEN 1 ELSE 0 END) as valid_count
        FROM main_path 
        GROUP BY path_id, path_name
        ORDER BY path_id
    ''')
    
    for row in cursor.fetchall():
        print(f"\n主路径 {row['path_id']}: {row['path_name'] or '未命名'}")
        print(f"  总记录数: {row['count']}")
        print(f"  有效记录数（两端节点都存在）: {row['valid_count']}")
    
    conn.close()

def show_all_paths():
    """显示所有主路径"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT DISTINCT path_id, path_name FROM main_path ORDER BY path_id
    ''')
    paths = cursor.fetchall()
    
    print("=" * 60)
    print("所有主路径:")
    print("=" * 60)
    
    for path in paths:
        print(f"\n【主路径 {path['path_id']}】{path['path_name'] or '未命名'}")
        print("-" * 40)
        
        cursor.execute('''
            SELECT source_name, target_name, source_id, target_id, path_order
            FROM main_path 
            WHERE path_id = ?
            ORDER BY path_order
        ''', (path['path_id'],))
        
        for row in cursor.fetchall():
            status = "✓" if row['source_id'] and row['target_id'] else "⚠"
            print(f"  {status} {row['source_name']} -> {row['target_name']}")
    
    conn.close()

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == '--show':
        show_all_paths()
    else:
        import_main_path_v2()
        print("\n" + "=" * 50)
        show_all_paths()
