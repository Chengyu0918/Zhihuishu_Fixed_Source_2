"""
重新导入所有关系并更新节点 weight
1. 先重置所有节点的 weight 为 0
2. 导入能力层关系（2  14能力-xxx.xlsx）
3. 导入同层关系（1xxx.xlsx）
4. 导入跨层关系（3  xxx.xlsx）- 如果有对应的导入脚本
"""

import sqlite3
import subprocess
import sys

def reset_node_weights(db_path='database.db'):
    """重置所有节点的 weight 为 0"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('UPDATE nodes SET weight = 0')
    count = cursor.rowcount
    conn.commit()
    conn.close()
    print(f"已重置 {count} 个节点的 weight 为 0")
    return count

def show_weight_stats(db_path='database.db'):
    """显示节点 weight 统计"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 各层统计
    cursor.execute('''
        SELECT layer, COUNT(*) as total, SUM(weight) as total_weight, MAX(weight) as max_weight 
        FROM nodes GROUP BY layer
    ''')
    print('\n各层节点 weight 统计:')
    print('层 | 节点数 | 总weight | 最大weight')
    print('-' * 60)
    for row in cursor.fetchall():
        print(f'{row[0]} | {row[1]} | {row[2]} | {row[3]}')
    
    # weight 最高的节点
    cursor.execute('''
        SELECT name, layer, weight FROM nodes 
        WHERE weight > 0 ORDER BY weight DESC LIMIT 15
    ''')
    print('\nweight 最高的15个节点:')
    for row in cursor.fetchall():
        print(f'  {row[0]} ({row[1]}): weight={row[2]}')
    
    conn.close()

def main():
    print("=" * 60)
    print("重新导入所有关系并更新节点 weight")
    print("=" * 60)
    
    # 1. 重置节点 weight
    print("\n步骤1: 重置所有节点的 weight 为 0")
    reset_node_weights()
    
    # 2. 导入能力层关系
    print("\n步骤2: 导入能力层关系 (2  14能力-xxx.xlsx)")
    print("-" * 40)
    subprocess.run([sys.executable, 'import_ability_relations.py'], check=True)
    
    # 3. 导入同层关系（需要修改脚本不询问用户）
    print("\n步骤3: 导入同层关系 (1xxx.xlsx)")
    print("-" * 40)
    # 直接调用导入函数，不通过 main()
    from import_layer_relations import build_name_to_id_map, import_layer_excel, clear_layer_edges
    import glob
    
    excel_files = glob.glob('data/1*.xlsx')
    print(f"找到 {len(excel_files)} 个同层关系文件")
    
    name_to_id = build_name_to_id_map()
    clear_layer_edges()
    
    total_added = 0
    total_updated = 0
    total_skipped = 0
    
    for excel_file in excel_files:
        try:
            added, updated, skipped = import_layer_excel(excel_file, name_to_id=name_to_id)
            total_added += added
            total_updated += updated
            total_skipped += skipped
        except Exception as e:
            print(f"导入出错: {e}")
    
    print(f"\n同层关系总计: 新增={total_added}, 更新={total_updated}, 跳过={total_skipped}")
    
    # 4. 显示最终统计
    print("\n" + "=" * 60)
    print("导入完成！最终统计:")
    show_weight_stats()

if __name__ == '__main__':
    main()
