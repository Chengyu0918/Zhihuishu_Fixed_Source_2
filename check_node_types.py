#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 检查节点类型
cursor.execute('SELECT DISTINCT node_type FROM nodes')
print('节点类型:', [r[0] for r in cursor.fetchall()])

# 检查category类型节点数
cursor.execute("SELECT COUNT(*) FROM nodes WHERE node_type = 'category'")
print('category类型节点数:', cursor.fetchone()[0])

# 查看一些示例节点
cursor.execute("SELECT name, node_type, layer FROM nodes LIMIT 10")
print('\n示例节点:')
for row in cursor.fetchall():
    print(f"  {row[0]} - 类型: {row[1]}, 层级: {row[2]}")

conn.close()
