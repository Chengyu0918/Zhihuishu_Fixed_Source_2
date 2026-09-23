import sqlite3

# 层级映射：数字 -> 字符串
LAYER_MAPPING = {
    '3': 'LAYER_PROFESSIONAL',      # 专业课
    '4': 'LAYER_DISCIPLINE_BASE',   # 学科基础
    '5': 'LAYER_ADVANCED_BASE',     # 高阶基础
    '6': 'LAYER_MATH_PHYSICS',      # 数理基础
    3: 'LAYER_PROFESSIONAL',
    4: 'LAYER_DISCIPLINE_BASE',
    5: 'LAYER_ADVANCED_BASE',
    6: 'LAYER_MATH_PHYSICS',
}

def main():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 查找所有使用数字层级的节点
    cursor.execute("SELECT id, name, layer FROM nodes WHERE layer IN ('3', '4', '5', '6', 3, 4, 5, 6)")
    nodes = cursor.fetchall()
    
    print(f"找到 {len(nodes)} 个需要修复层级的节点")
    print("=" * 60)
    
    fixed_count = 0
    for node_id, name, layer in nodes:
        new_layer = LAYER_MAPPING.get(layer)
        if new_layer:
            cursor.execute("UPDATE nodes SET layer = ? WHERE id = ?", (new_layer, node_id))
            print(f"  修复: {name}: {layer} -> {new_layer}")
            fixed_count += 1
    
    conn.commit()
    
    print("=" * 60)
    print(f"修复完成！共修复 {fixed_count} 个节点")
    
    # 显示修复后的层级分布
    cursor.execute("SELECT layer, COUNT(*) FROM nodes GROUP BY layer ORDER BY layer")
    print("\n修复后各层节点分布:")
    for layer, count in cursor.fetchall():
        print(f"  {layer}: {count} 个节点")
    
    conn.close()

if __name__ == '__main__':
    main()
