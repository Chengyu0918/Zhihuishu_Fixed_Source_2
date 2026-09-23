"""
检查并清理涉及大类节点的关系
"""
import sqlite3

def main():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. 检查涉及大类节点的关系数量
    cursor.execute("""
        SELECT COUNT(*) FROM edges e 
        JOIN nodes n1 ON e.source_id = n1.id 
        JOIN nodes n2 ON e.target_id = n2.id 
        WHERE n1.node_type = 'category' OR n2.node_type = 'category'
    """)
    category_relations = cursor.fetchone()[0]
    print(f"涉及大类节点的关系数量: {category_relations}")
    
    # 2. 检查关系类型分布
    cursor.execute("SELECT relation_type, COUNT(*) FROM edges GROUP BY relation_type")
    print("\n关系类型分布:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]}条")
    
    # 3. 查看一些涉及大类节点的关系示例
    cursor.execute("""
        SELECT e.source_id, n1.name, n1.node_type, e.target_id, n2.name, n2.node_type, e.relation_type
        FROM edges e 
        JOIN nodes n1 ON e.source_id = n1.id 
        JOIN nodes n2 ON e.target_id = n2.id 
        WHERE n1.node_type = 'category' OR n2.node_type = 'category'
        LIMIT 10
    """)
    results = cursor.fetchall()
    if results:
        print("\n涉及大类节点的关系示例:")
        for row in results:
            print(f"  {row[1]}({row[2]}) -> {row[4]}({row[5]}) [{row[6]}]")
    
    # 4. 如果有涉及大类节点的关系，询问是否删除
    if category_relations > 0:
        print(f"\n发现 {category_relations} 条涉及大类节点的关系")
        response = input("是否删除这些关系? (y/n): ")
        if response.lower() == 'y':
            # 删除涉及大类节点的关系
            cursor.execute("""
                DELETE FROM edges WHERE id IN (
                    SELECT e.id FROM edges e 
                    JOIN nodes n1 ON e.source_id = n1.id 
                    JOIN nodes n2 ON e.target_id = n2.id 
                    WHERE n1.node_type = 'category' OR n2.node_type = 'category'
                )
            """)
            deleted = cursor.rowcount
            conn.commit()
            print(f"已删除 {deleted} 条涉及大类节点的关系")
            
            # 显示删除后的统计
            cursor.execute("SELECT COUNT(*) FROM edges")
            remaining = cursor.fetchone()[0]
            print(f"剩余关系数量: {remaining}")
    else:
        print("\n没有涉及大类节点的关系，无需清理")
    
    conn.close()

if __name__ == '__main__':
    main()
