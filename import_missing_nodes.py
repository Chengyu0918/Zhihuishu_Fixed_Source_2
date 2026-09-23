"""
导入缺失的节点到数据库
从"新增知识点(1).xlsx"读取节点信息，并添加系统级节点
"""

import sqlite3
import hashlib
import pandas as pd

DB_PATH = 'database.db'

# 层级映射：数字 -> LAYER_*格式
LAYER_MAPPING = {
    3: 'LAYER_PROFESSIONAL',      # 专业课
    4: 'LAYER_DISCIPLINE_BASE',   # 学科基础
    5: 'LAYER_ADVANCED_BASE',     # 高阶基础
    6: 'LAYER_MATH_BASE',         # 数理基础
}

# 系统级节点（问题层）- 这些是拓展路径的顶层节点
SYSTEM_NODES = [
    ("抗干扰协同感知系统设计", "LAYER_PROBLEM", "tag", "问题层-抗干扰协同感知系统"),
    ("分布式无源协同定位网络", "LAYER_PROBLEM", "tag", "问题层-分布式无源协同定位"),
    ("认知电子战闭环对抗系统", "LAYER_PROBLEM", "tag", "问题层-认知电子战闭环对抗"),
    ("多模态光电-雷达目标识别系统", "LAYER_PROBLEM", "tag", "问题层-多模态光电雷达识别"),
    ("资源受限平台的轻量化感知系统", "LAYER_PROBLEM", "tag", "问题层-资源受限轻量化感知"),
]

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_node_id(name, layer):
    """生成节点ID"""
    return hashlib.md5(f"{name}_{layer}".encode()).hexdigest()[:12]

def import_nodes_from_excel():
    """从Excel文件导入节点"""
    print("=" * 60)
    print("从Excel文件导入新增知识点")
    print("=" * 60)
    
    # 读取Excel文件
    df = pd.read_excel('data/2/新增知识点(1).xlsx')
    print(f"读取到 {len(df)} 条记录")
    
    conn = get_db()
    cursor = conn.cursor()
    
    added_count = 0
    skipped_count = 0
    
    # 去重处理
    df_unique = df.drop_duplicates(subset=['知识点'])
    print(f"去重后 {len(df_unique)} 条唯一记录")
    
    for _, row in df_unique.iterrows():
        name = str(row['知识点']).strip()
        course = str(row['课程名']).strip()
        layer_num = int(row['层级'])
        
        # 转换层级
        layer = LAYER_MAPPING.get(layer_num)
        if not layer:
            print(f"⚠ 未知层级 {layer_num}: {name}")
            continue
        
        # 检查节点是否已存在
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (name,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⏭ 跳过（已存在）: {name}")
            skipped_count += 1
            continue
        
        # 生成节点ID
        node_id = generate_node_id(name, layer)
        
        # 插入节点
        try:
            cursor.execute('''
                INSERT INTO nodes (id, name, layer, node_type, description, metadata)
                VALUES (?, ?, ?, ?, ?, '{}')
            ''', (node_id, name, layer, 'leaf', f"课程: {course}"))
            
            print(f"✓ 添加: {name} (层级: {layer}, 课程: {course})")
            added_count += 1
        except sqlite3.IntegrityError as e:
            print(f"✗ 失败: {name} - {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\nExcel导入完成！新增 {added_count} 个节点，跳过 {skipped_count} 个已存在节点")
    return added_count

def import_system_nodes():
    """导入系统级节点"""
    print("\n" + "=" * 60)
    print("导入系统级节点（问题层）")
    print("=" * 60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    added_count = 0
    skipped_count = 0
    
    for name, layer, node_type, description in SYSTEM_NODES:
        # 检查节点是否已存在
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (name,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"⏭ 跳过（已存在）: {name}")
            skipped_count += 1
            continue
        
        # 生成节点ID
        node_id = generate_node_id(name, layer)
        
        # 插入节点
        try:
            cursor.execute('''
                INSERT INTO nodes (id, name, layer, node_type, description, metadata)
                VALUES (?, ?, ?, ?, ?, '{}')
            ''', (node_id, name, layer, node_type, description))
            
            print(f"✓ 添加: {name} (层级: {layer})")
            added_count += 1
        except sqlite3.IntegrityError as e:
            print(f"✗ 失败: {name} - {e}")
    
    conn.commit()
    conn.close()
    
    print(f"\n系统节点导入完成！新增 {added_count} 个节点，跳过 {skipped_count} 个已存在节点")
    return added_count

def update_main_path_node_ids():
    """更新主路径表中的节点ID"""
    print("\n" + "=" * 60)
    print("更新主路径表中的节点ID")
    print("=" * 60)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # 获取所有主路径记录
    cursor.execute('SELECT id, source_name, target_name FROM main_path')
    records = cursor.fetchall()
    
    updated_count = 0
    still_missing = []
    
    for record in records:
        # 查找源节点ID
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (record['source_name'],))
        source_row = cursor.fetchone()
        source_id = source_row['id'] if source_row else None
        
        # 查找目标节点ID
        cursor.execute('SELECT id FROM nodes WHERE name = ?', (record['target_name'],))
        target_row = cursor.fetchone()
        target_id = target_row['id'] if target_row else None
        
        # 更新记录
        cursor.execute('''
            UPDATE main_path 
            SET source_id = ?, target_id = ?
            WHERE id = ?
        ''', (source_id, target_id, record['id']))
        
        if source_id and target_id:
            updated_count += 1
        else:
            if not source_id:
                still_missing.append(record['source_name'])
            if not target_id:
                still_missing.append(record['target_name'])
    
    conn.commit()
    
    # 显示更新后的统计
    cursor.execute('''
        SELECT path_id, path_name, COUNT(*) as count,
               SUM(CASE WHEN source_id IS NOT NULL AND target_id IS NOT NULL THEN 1 ELSE 0 END) as valid_count
        FROM main_path 
        GROUP BY path_id, path_name
        ORDER BY path_id
    ''')
    
    print("\n更新后的主路径统计:")
    for row in cursor.fetchall():
        print(f"  路径 {row['path_id']}: {row['path_name']}")
        print(f"    总记录数: {row['count']}, 有效记录数: {row['valid_count']}")
    
    # 显示仍然缺失的节点
    still_missing = list(set(still_missing))
    if still_missing:
        print(f"\n⚠ 仍有 {len(still_missing)} 个节点缺失:")
        for name in sorted(still_missing):
            print(f"  - {name}")
    
    conn.close()
    return updated_count

def main():
    """主函数"""
    # 1. 从Excel导入节点
    excel_count = import_nodes_from_excel()
    
    # 2. 导入系统级节点
    system_count = import_system_nodes()
    
    # 3. 更新主路径表中的节点ID
    update_main_path_node_ids()
    
    print("\n" + "=" * 60)
    print(f"总计新增 {excel_count + system_count} 个节点")
    print("=" * 60)

if __name__ == '__main__':
    main()
