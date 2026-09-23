"""
添加主路径2中缺失的节点
"""

import sqlite3
import hashlib

DB_PATH = 'database.db'

def get_db():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def generate_node_id(name, layer):
    """生成节点ID"""
    return hashlib.md5(f"{name}_{layer}".encode()).hexdigest()[:12]

def add_missing_nodes():
    """添加缺失的节点"""
    
    # 缺失的节点列表（根据内容推断层级）
    # 这些节点大多是专业课或学科基础层级的知识点
    missing_nodes = [
        # (节点名称, 层级, 节点类型, 描述)
        ("如何提高目标协同跟踪？", "LAYER_PROBLEM", "tag", "问题层-目标协同跟踪问题"),
        ("集成A/D转换器", "LAYER_DISCIPLINE_BASE", "leaf", "学科基础-模数转换器"),
        ("光电系统作用距离计算", "LAYER_PROFESSIONAL", "leaf", "专业课-光电系统性能分析"),
        ("光电系统信噪比分析", "LAYER_PROFESSIONAL", "leaf", "专业课-光电系统性能分析"),
        ("背景抑制与杂波滤除", "LAYER_PROFESSIONAL", "leaf", "专业课-信号处理"),
        ("红外小目标检测", "LAYER_PROFESSIONAL", "leaf", "专业课-目标检测"),
        ("光电图像配准", "LAYER_PROFESSIONAL", "leaf", "专业课-图像处理"),
        ("质心跟踪算法", "LAYER_PROFESSIONAL", "leaf", "专业课-目标跟踪算法"),
        ("深度学习的典型应用", "LAYER_DISCIPLINE_BASE", "leaf", "学科基础-深度学习应用"),
        ("多模态特征融合（红外+可见光）", "LAYER_PROFESSIONAL", "leaf", "专业课-多模态融合"),
        ("检测性能分析", "LAYER_PROFESSIONAL", "leaf", "专业课-系统性能评估"),
    ]
    
    conn = get_db()
    cursor = conn.cursor()
    
    added_count = 0
    skipped_count = 0
    
    print("=" * 60)
    print("添加主路径2缺失的节点")
    print("=" * 60)
    
    for name, layer, node_type, description in missing_nodes:
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
            
            print(f"✓ 添加: {name} (层级: {layer}, ID: {node_id})")
            added_count += 1
        except sqlite3.IntegrityError as e:
            print(f"✗ 失败: {name} - {e}")
    
    conn.commit()
    
    print("\n" + "=" * 60)
    print(f"添加完成！新增 {added_count} 个节点，跳过 {skipped_count} 个已存在节点")
    print("=" * 60)
    
    conn.close()
    
    return added_count

def update_main_path_node_ids():
    """更新主路径表中的节点ID"""
    conn = get_db()
    cursor = conn.cursor()
    
    print("\n更新主路径表中的节点ID...")
    
    # 获取所有主路径记录
    cursor.execute('SELECT id, source_name, target_name FROM main_path WHERE source_id IS NULL OR target_id IS NULL')
    records = cursor.fetchall()
    
    updated_count = 0
    
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
        if source_id or target_id:
            cursor.execute('''
                UPDATE main_path 
                SET source_id = COALESCE(?, source_id), 
                    target_id = COALESCE(?, target_id)
                WHERE id = ?
            ''', (source_id, target_id, record['id']))
            updated_count += 1
    
    conn.commit()
    print(f"更新了 {updated_count} 条主路径记录")
    
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
        print(f"  主路径 {row['path_id']}: {row['path_name']}")
        print(f"    总记录数: {row['count']}, 有效记录数: {row['valid_count']}")
    
    conn.close()

if __name__ == '__main__':
    add_missing_nodes()
    update_main_path_node_ids()
