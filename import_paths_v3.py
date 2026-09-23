import sqlite3
import pandas as pd
import uuid

def get_or_create_node(cursor, name, existing_nodes):
    """获取节点ID，如果不存在则创建"""
    if name in existing_nodes:
        return existing_nodes[name]
    
    # 创建新节点
    node_id = str(uuid.uuid4())
    cursor.execute("""
        INSERT INTO nodes (id, name, layer, node_type)
        VALUES (?, ?, 'LAYER_PROFESSIONAL', 'knowledge')
    """, (node_id, name))
    existing_nodes[name] = node_id
    print(f"    [新增节点] {name}")
    return node_id

def import_interest_path(cursor, existing_nodes):
    """导入兴趣路径"""
    print("\n" + "=" * 60)
    print("导入兴趣路径: 电子信息工程兴趣路径梳理（v1）(3).xlsx")
    print("=" * 60)
    
    df = pd.read_excel('data/2/电子信息工程兴趣路径梳理（v1）(3).xlsx', sheet_name='Sheet1')
    
    path_id = 100
    path_name = "兴趣路径1-6G通感一体化"
    added = 0
    new_nodes = 0
    
    for idx, row in df.iterrows():
        source_name = str(row['出发节点']).strip() if pd.notna(row['出发节点']) else None
        target_name = str(row['目的节点']).strip() if pd.notna(row['目的节点']) else None
        
        if not source_name or source_name == 'nan':
            continue
        if not target_name or target_name == 'nan':
            continue
        
        # 获取或创建节点
        old_count = len(existing_nodes)
        source_id = get_or_create_node(cursor, source_name, existing_nodes)
        target_id = get_or_create_node(cursor, target_name, existing_nodes)
        new_nodes += len(existing_nodes) - old_count
        
        # 检查路径是否已存在
        cursor.execute("""
            SELECT 1 FROM main_path WHERE source_name = ? AND target_name = ? AND path_id = ?
        """, (source_name, target_name, path_id))
        
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO main_path (source_name, target_name, source_id, target_id, path_order, path_id, path_name)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (source_name, target_name, source_id, target_id, idx + 1, path_id, path_name))
            print(f"  [{idx+1}] {source_name} -> {target_name}")
            added += 1
    
    print(f"\n兴趣路径导入完成: {added} 条记录, {new_nodes} 个新节点")
    return added, new_nodes

def import_main_paths(cursor, existing_nodes):
    """导入主路径"""
    print("\n" + "=" * 60)
    print("导入主路径")
    print("=" * 60)
    
    # 先删除现有主路径
    cursor.execute("DELETE FROM main_path WHERE path_id = 1")
    print(f"删除了现有主路径记录")
    
    path_id = 1
    path_name = "主路径"
    added = 0
    new_nodes = 0
    path_order = 0
    
    # 导入第一个文件: 副本电子信息工程主路径梳理 (1).xlsx
    print("\n--- 副本电子信息工程主路径梳理 (1).xlsx ---")
    df1 = pd.read_excel('data/2/副本电子信息工程主路径梳理 (1).xlsx')
    
    for idx, row in df1.iterrows():
        source_name = str(row['出发节点']).strip() if pd.notna(row['出发节点']) else None
        target_name = str(row['目的节点']).strip() if pd.notna(row['目的节点']) else None
        
        if not source_name or source_name == 'nan':
            continue
        if not target_name or target_name == 'nan':
            continue
        
        # 获取或创建节点
        old_count = len(existing_nodes)
        source_id = get_or_create_node(cursor, source_name, existing_nodes)
        target_id = get_or_create_node(cursor, target_name, existing_nodes)
        new_nodes += len(existing_nodes) - old_count
        
        path_order += 1
        cursor.execute("""
            INSERT INTO main_path (source_name, target_name, source_id, target_id, path_order, path_id, path_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source_name, target_name, source_id, target_id, path_order, path_id, path_name))
        print(f"  [{path_order}] {source_name} -> {target_name}")
        added += 1
    
    # 导入第二个文件: 电子信息工程主路径梳理（v1）.xlsx
    print("\n--- 电子信息工程主路径梳理（v1）.xlsx ---")
    df2 = pd.read_excel('data/2/电子信息工程主路径梳理（v1）.xlsx')
    
    for idx, row in df2.iterrows():
        source_name = str(row['出发节点']).strip() if pd.notna(row['出发节点']) else None
        target_name = str(row['目的节点']).strip() if pd.notna(row['目的节点']) else None
        
        if not source_name or source_name == 'nan':
            continue
        if not target_name or target_name == 'nan':
            continue
        
        # 检查是否已存在相同的路径记录
        cursor.execute("""
            SELECT 1 FROM main_path WHERE source_name = ? AND target_name = ? AND path_id = ?
        """, (source_name, target_name, path_id))
        
        if cursor.fetchone():
            print(f"  [跳过] {source_name} -> {target_name} (已存在)")
            continue
        
        # 获取或创建节点
        old_count = len(existing_nodes)
        source_id = get_or_create_node(cursor, source_name, existing_nodes)
        target_id = get_or_create_node(cursor, target_name, existing_nodes)
        new_nodes += len(existing_nodes) - old_count
        
        path_order += 1
        cursor.execute("""
            INSERT INTO main_path (source_name, target_name, source_id, target_id, path_order, path_id, path_name)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (source_name, target_name, source_id, target_id, path_order, path_id, path_name))
        print(f"  [{path_order}] {source_name} -> {target_name}")
        added += 1
    
    print(f"\n主路径导入完成: {added} 条记录, {new_nodes} 个新节点")
    return added, new_nodes

def main():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 获取现有节点
    cursor.execute("SELECT name, id FROM nodes")
    existing_nodes = {row[0]: row[1] for row in cursor.fetchall()}
    print(f"数据库中现有 {len(existing_nodes)} 个节点")
    
    # 导入兴趣路径
    interest_added, interest_new_nodes = import_interest_path(cursor, existing_nodes)
    
    # 导入主路径
    main_added, main_new_nodes = import_main_paths(cursor, existing_nodes)
    
    conn.commit()
    
    # 显示最终状态
    print("\n" + "=" * 60)
    print("导入结果汇总")
    print("=" * 60)
    print(f"兴趣路径: {interest_added} 条记录, {interest_new_nodes} 个新节点")
    print(f"主路径: {main_added} 条记录, {main_new_nodes} 个新节点")
    
    cursor.execute("SELECT path_id, path_name, COUNT(*) FROM main_path GROUP BY path_id, path_name ORDER BY path_id")
    print("\n当前路径状态:")
    for row in cursor.fetchall():
        print(f"  路径 {row[0]} ({row[1]}): {row[2]} 条记录")
    
    cursor.execute("SELECT COUNT(*) FROM nodes")
    print(f"\n数据库节点总数: {cursor.fetchone()[0]}")
    
    conn.close()
    print("\n完成！")

if __name__ == '__main__':
    main()
