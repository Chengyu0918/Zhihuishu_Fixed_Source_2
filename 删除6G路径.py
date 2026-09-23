#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
删除兴趣路径中"1-6G"开头的记录
"""

import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 查看所有路径
print("当前所有路径:")
cursor.execute('SELECT DISTINCT path_id, path_name, COUNT(*) as cnt FROM main_path GROUP BY path_id, path_name ORDER BY path_id')
for row in cursor.fetchall():
    print(f"  path_id={row[0]}, name={row[1]}, count={row[2]}")

# 查找包含6G的兴趣路径记录
print("\n查找包含 '6G' 的兴趣路径:")
cursor.execute("SELECT DISTINCT path_id, path_name, COUNT(*) as cnt FROM main_path WHERE path_name LIKE '%6G%' GROUP BY path_id, path_name")
results = cursor.fetchall()
for row in results:
    print(f"  path_id={row[0]}, name={row[1]}, count={row[2]}")

if results:
    # 删除这些记录
    cursor.execute("DELETE FROM main_path WHERE path_name LIKE '%6G%'")
    deleted = cursor.rowcount
    conn.commit()
    print(f"\n已删除 {deleted} 条记录")
else:
    print("\n没有找到 '1-6G' 开头的路径")

# 显示删除后的路径
print("\n删除后的路径:")
cursor.execute('SELECT DISTINCT path_id, path_name, COUNT(*) as cnt FROM main_path GROUP BY path_id, path_name ORDER BY path_id')
for row in cursor.fetchall():
    print(f"  path_id={row[0]}, name={row[1]}, count={row[2]}")

conn.close()
