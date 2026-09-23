#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查数据库中的路径信息"""

import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 查看所有表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print("数据库表:", tables)

# 查看edges表中的path_id
if 'edges' in tables:
    cursor.execute("SELECT DISTINCT relation_type FROM edges WHERE relation_type LIKE '%path%' OR relation_type LIKE '%PATH%'")
    path_types = cursor.fetchall()
    print("\n路径相关的relation_type:", path_types)
    
    # 统计各种relation_type
    cursor.execute("SELECT relation_type, COUNT(*) FROM edges GROUP BY relation_type ORDER BY COUNT(*) DESC")
    print("\n所有relation_type统计:")
    for r in cursor.fetchall():
        print(f"  {r[0]}: {r[1]}条")

# 查看是否有main_path表
if 'main_path' in tables:
    cursor.execute("SELECT * FROM main_path LIMIT 10")
    print("\nmain_path表内容:", cursor.fetchall())

# 查看是否有learning_paths表
if 'learning_paths' in tables:
    cursor.execute("SELECT * FROM learning_paths")
    print("\nlearning_paths表内容:")
    for r in cursor.fetchall():
        print(f"  {r}")

conn.close()
