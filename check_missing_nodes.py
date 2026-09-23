"""
检查主路径中缺失的节点
"""

import sqlite3

DB_PATH = 'database.db'

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_missing_nodes():
    """检查缺失的节点"""
    conn = get_db()
    cursor = conn.cursor()
    
    # 查找所有缺失的节点名称
    cursor.execute('''
        SELECT DISTINCT source_name FROM main_path WHERE source_id IS NULL
        UNION
        SELECT DISTINCT target_name FROM main_path WHERE target_id IS NULL
    ''')
    missing = cursor.fetchall()
    
    print(f"缺失节点数量: {len(missing)}")
    print("\n缺失的节点列表:")
    for m in missing:
        print(f"  - {m[0]}")
    
    # 按路径统计缺失情况
    print("\n" + "=" * 60)
    print("按路径统计缺失情况:")
    cursor.execute('''
        SELECT path_id, path_name, 
               COUNT(*) as total,
               SUM(CASE WHEN source_id IS NULL THEN 1 ELSE 0 END) as missing_source,
               SUM(CASE WHEN target_id IS NULL THEN 1 ELSE 0 END) as missing_target
        FROM main_path
        GROUP BY path_id, path_name
        ORDER BY path_id
    ''')
    
    for row in cursor.fetchall():
        print(f"\n路径 {row['path_id']}: {row['path_name']}")
        print(f"  总记录数: {row['total']}")
        print(f"  缺失源节点: {row['missing_source']}")
        print(f"  缺失目标节点: {row['missing_target']}")
    
    conn.close()
    return [m[0] for m in missing]

if __name__ == '__main__':
    check_missing_nodes()
