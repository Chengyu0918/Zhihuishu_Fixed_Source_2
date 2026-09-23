"""
删除涉及大类节点的关系
"""
import sqlite3

def main():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. 先获取所有大类节点的ID
    cursor.execute("SELECT id FROM nodes WHERE node_type = 'category'")
    category_ids = [row[0] for row in cursor.fetchall()]
    print(f"大类节点数量: {len(category_ids)}")
    
    # 2. 检查涉及大类节点的关系数量
    cursor.execute("""
        SELECT COUNT(*) FROM edges 
        WHERE source_id IN (SELECT id FROM nodes WHERE node_type = 'category')
           OR target_id IN (SELECT id FROM nodes WHERE node_type = 'category')
    """)
    category_relations = cursor.fetchone()[0]
    print(f"涉及大类节点的关系数量: {category_relations}")
    
    # 3. 显示删除前的统计
    cursor.execute("SELECT COUNT(*) FROM edges")
    total_before = cursor.fetchone()[0]
    print(f"删除前总关系数量: {total_before}")
    
    if category_relations > 0:
        # 4. 删除涉及大类节点的关系
        cursor.execute("""
            DELETE FROM edges 
            WHERE source_id IN (SELECT id FROM nodes WHERE node_type = 'category')
               OR target_id IN (SELECT id FROM nodes WHERE node_type = 'category')
        """)
        deleted = cursor.rowcount
        conn.commit()
        print(f"已删除 {deleted} 条涉及大类节点的关系")
        
        # 5. 显示删除后的统计
        cursor.execute("SELECT COUNT(*) FROM edges")
        total_after = cursor.fetchone()[0]
        print(f"删除后总关系数量: {total_after}")
        print(f"实际删除: {total_before - total_after} 条")
    else:
        print("没有涉及大类节点的关系，无需清理")
    
    conn.close()

if __name__ == '__main__':
    main()
