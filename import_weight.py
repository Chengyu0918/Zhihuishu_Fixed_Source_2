"""
导入知识点权重数据
从【汇总】所有知识点总调用次数表.xlsx读取数据，更新数据库中节点的weight值
"""
import sqlite3
import pandas as pd

def main():
    # 读取Excel文件
    excel_path = 'data/【汇总】所有知识点总调用次数表.xlsx'
    print(f"正在读取Excel文件: {excel_path}")
    
    df = pd.read_excel(excel_path)
    print(f"读取到 {len(df)} 条记录")
    print(f"列名: {df.columns.tolist()}")
    
    # 获取知识点名称和总调用次数列
    # 根据Excel结构，第二列是知识点名称，第三列是总调用次数
    name_col = df.columns[1]  # 知识点
    weight_col = df.columns[2]  # 总调用次数
    
    print(f"知识点列: {name_col}")
    print(f"权重列: {weight_col}")
    
    # 连接数据库
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. 首先检查nodes表是否有weight列，如果没有则添加
    cursor.execute("PRAGMA table_info(nodes)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'weight' not in columns:
        print("添加weight列到nodes表...")
        cursor.execute("ALTER TABLE nodes ADD COLUMN weight INTEGER DEFAULT 0")
        conn.commit()
    
    # 2. 清空所有节点的weight值
    print("清空所有节点的weight值...")
    cursor.execute("UPDATE nodes SET weight = 0")
    conn.commit()
    
    # 3. 获取所有节点名称和ID的映射
    cursor.execute("SELECT id, name FROM nodes")
    node_map = {row[1]: row[0] for row in cursor.fetchall()}
    print(f"数据库中共有 {len(node_map)} 个节点")
    
    # 4. 更新匹配节点的weight值
    updated_count = 0
    not_found_count = 0
    not_found_names = []
    
    for _, row in df.iterrows():
        name = str(row[name_col]).strip()
        weight = int(row[weight_col]) if pd.notna(row[weight_col]) else 0
        
        if name in node_map:
            node_id = node_map[name]
            cursor.execute("UPDATE nodes SET weight = ? WHERE id = ?", (weight, node_id))
            updated_count += 1
        else:
            not_found_count += 1
            if not_found_count <= 20:  # 只记录前20个未找到的
                not_found_names.append(name)
    
    conn.commit()
    
    print(f"\n更新完成:")
    print(f"  成功更新: {updated_count} 个节点")
    print(f"  未找到: {not_found_count} 个知识点")
    
    if not_found_names:
        print(f"\n未找到的知识点示例（前20个）:")
        for name in not_found_names:
            print(f"  - {name}")
    
    # 5. 显示更新后的统计
    cursor.execute("SELECT COUNT(*) FROM nodes WHERE weight > 0")
    nodes_with_weight = cursor.fetchone()[0]
    
    cursor.execute("SELECT MAX(weight), MIN(weight), AVG(weight) FROM nodes WHERE weight > 0")
    max_w, min_w, avg_w = cursor.fetchone()
    
    print(f"\n权重统计:")
    print(f"  有权重的节点数: {nodes_with_weight}")
    print(f"  最大权重: {max_w}")
    print(f"  最小权重: {min_w}")
    print(f"  平均权重: {avg_w:.2f}")
    
    # 显示权重最高的10个节点
    cursor.execute("""
        SELECT name, weight, layer 
        FROM nodes 
        WHERE weight > 0 
        ORDER BY weight DESC 
        LIMIT 10
    """)
    print(f"\n权重最高的10个节点:")
    for row in cursor.fetchall():
        print(f"  {row[0]}: {row[1]} (层级: {row[2]})")
    
    conn.close()
    print("\n导入完成!")

if __name__ == '__main__':
    main()
