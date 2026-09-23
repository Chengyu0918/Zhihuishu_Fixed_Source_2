import sqlite3
import pandas as pd
import uuid

# 层级映射：数字 -> 字符串
LAYER_MAPPING = {
    3: 'LAYER_PROFESSIONAL',      # 专业课
    4: 'LAYER_DISCIPLINE_BASE',   # 学科基础
    5: 'LAYER_ADVANCED_BASE',     # 高阶基础
    6: 'LAYER_MATH_PHYSICS',      # 数理基础
}

def main():
    # 读取Excel文件
    df = pd.read_excel('data/2/新增知识点(4).xlsx')
    
    print("=" * 60)
    print("读取新增知识点数据:")
    print("=" * 60)
    print(f"总行数: {len(df)}")
    print(f"列名: {df.columns.tolist()}")
    
    # 连接数据库
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 获取现有节点
    cursor.execute("SELECT id, name, layer FROM nodes")
    existing_nodes = {row[1]: {'id': row[0], 'layer': row[1]} for row in cursor.fetchall()}
    print(f"\n数据库中现有 {len(existing_nodes)} 个节点")
    
    # 获取大类节点（课程名）
    cursor.execute("SELECT id, name FROM nodes WHERE node_type = 'category' OR layer IN ('LAYER_PROFESSIONAL', 'LAYER_DISCIPLINE_BASE', 'LAYER_ADVANCED_BASE', 'LAYER_MATH_PHYSICS')")
    category_nodes = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"数据库中现有 {len(category_nodes)} 个大类/课程节点")
    
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
        category_name = str(row['课程名']).strip() if pd.notna(row['课程名']) else None
        layer_num = row['层级'] if pd.notna(row['层级']) else None
        
        if not knowledge_name or knowledge_name == 'nan':
            continue
        
        # 转换层级
        layer_str = LAYER_MAPPING.get(int(layer_num)) if layer_num else None
        
        if not layer_str:
            print(f"  [跳过] {knowledge_name}: 无效层级 {layer_num}")
            skipped += 1
            continue
        
        # 检查节点是否存在
        if knowledge_name in existing_nodes:
            # 更新层级
            node_id = existing_nodes[knowledge_name]['id']
            old_layer = existing_nodes[knowledge_name]['layer']
            cursor.execute("UPDATE nodes SET layer = ? WHERE id = ?", (layer_str, node_id))
            print(f"  [更新] {knowledge_name}: 层级 {old_layer} -> {layer_str}")
            updated += 1
        else:
            # 添加新节点
            node_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO nodes (id, name, layer, node_type)
                VALUES (?, ?, ?, 'knowledge')
            """, (node_id, knowledge_name, layer_str))
            existing_nodes[knowledge_name] = {'id': node_id, 'layer': layer_str}
            print(f"  [新增] {knowledge_name} (层级: {layer_str}, 课程: {category_name})")
            added += 1
        
        # 建立与大类的关系
        if category_name and category_name in category_nodes:
            category_id = category_nodes[category_name]
            # 检查关系是否已存在
            cursor.execute("""
                SELECT 1 FROM edges WHERE source_id = ? AND target_id = ?
            """, (category_id, node_id))
            if not cursor.fetchone():
                edge_id = str(uuid.uuid4())
                cursor.execute("""
                    INSERT INTO edges (id, source_id, target_id, relation_type)
                    VALUES (?, ?, ?, 'contains')
                """, (edge_id, category_id, node_id))
                relations_added += 1
    
    conn.commit()
    
    # 统计结果
    cursor.execute("SELECT COUNT(*) FROM nodes")
    total_nodes = cursor.fetchone()[0]
    
    print("\n" + "=" * 60)
    print("导入结果:")
    print("=" * 60)
    print(f"  新增节点: {added} 个")
    print(f"  更新节点: {updated} 个")
    print(f"  跳过: {skipped} 个")
    print(f"  新增关系: {relations_added} 条")
    print(f"\n  数据库现有节点总数: {total_nodes}")
    
    # 显示各层分布
    cursor.execute("SELECT layer, COUNT(*) FROM nodes GROUP BY layer ORDER BY layer")
    print("\n各层节点分布:")
    for layer, count in cursor.fetchall():
        print(f"  {layer}: {count} 个节点")
    
    conn.close()
    print("\n完成！")

if __name__ == '__main__':
    main()
