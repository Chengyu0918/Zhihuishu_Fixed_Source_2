#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
只保留一条拓展路径和一条兴趣路径
- 保留 path_id=2 (第一条拓展路径)
- 保留 path_id=100 (第一条兴趣路径)
- 删除其他拓展路径 (path_id=3,4,5,6...)
- 删除其他兴趣路径 (path_id=101,102,103...)
"""

import sqlite3

def main():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 1. 查看当前所有路径
    print("=" * 60)
    print("当前所有路径:")
    print("=" * 60)
    
    cursor.execute("""
        SELECT path_id, COUNT(*) as count 
        FROM main_path 
        GROUP BY path_id 
        ORDER BY path_id
    """)
    paths = cursor.fetchall()
    
    for path_id, count in paths:
        if path_id == 1:
            path_type = "主路径"
        elif path_id < 100:
            path_type = f"拓展路径{path_id-1}"
        else:
            path_type = f"兴趣路径{path_id-99}"
        print(f"  路径 {path_id} ({path_type}): {count} 条记录")
    
    # 2. 删除多余的拓展路径 (保留 path_id=2)
    print("\n" + "=" * 60)
    print("删除多余的拓展路径 (保留 path_id=2)...")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM main_path WHERE path_id > 2 AND path_id < 100")
    extra_extension_count = cursor.fetchone()[0]
    print(f"  将删除 {extra_extension_count} 条拓展路径记录 (path_id=3,4,5,6...)")
    
    cursor.execute("DELETE FROM main_path WHERE path_id > 2 AND path_id < 100")
    
    # 3. 删除多余的兴趣路径 (保留 path_id=100)
    print("\n" + "=" * 60)
    print("删除多余的兴趣路径 (保留 path_id=100)...")
    print("=" * 60)
    
    cursor.execute("SELECT COUNT(*) FROM main_path WHERE path_id > 100")
    extra_interest_count = cursor.fetchone()[0]
    print(f"  将删除 {extra_interest_count} 条兴趣路径记录 (path_id=101,102,103...)")
    
    cursor.execute("DELETE FROM main_path WHERE path_id > 100")
    
    conn.commit()
    
    # 4. 显示最终结果
    print("\n" + "=" * 60)
    print("删除后的路径:")
    print("=" * 60)
    
    cursor.execute("""
        SELECT path_id, COUNT(*) as count 
        FROM main_path 
        GROUP BY path_id 
        ORDER BY path_id
    """)
    paths = cursor.fetchall()
    
    for path_id, count in paths:
        if path_id == 1:
            path_type = "主路径"
        elif path_id < 100:
            path_type = f"拓展路径{path_id-1}"
        else:
            path_type = f"兴趣路径{path_id-99}"
        print(f"  路径 {path_id} ({path_type}): {count} 条记录")
    
    conn.close()
    print("\n完成！")

if __name__ == '__main__':
    main()
