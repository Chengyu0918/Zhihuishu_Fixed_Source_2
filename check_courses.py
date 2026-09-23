#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# 检查课程名是否存在
courses = [
    '电子战技术与应用',
    '光电探测原理',
    '雷达数据处理',
    '雷达信号截获与分析',
    '雷达原理与系统',
    '无源测向与定位技术',
    '信号检测与估计',
    '场、波与天线技术',
    '电子电路基础',
    '数字信号处理',
    '通信与网络',
    '信号与系统',
    '程序设计(C)',
    '大数据导论',
    '人工智能引论',
    '大学物理',
    '高等代数'
]

print("检查课程名是否存在于数据库中：")
for course in courses:
    cursor.execute("SELECT id, name, node_type, layer FROM nodes WHERE name = ?", (course,))
    result = cursor.fetchone()
    if result:
        print(f"  ✓ {course} - 类型: {result[2]}, 层级: {result[3]}")
    else:
        print(f"  ✗ {course} - 不存在")

# 检查所有 category 类型的节点
print("\n\n所有 category 类型的节点：")
cursor.execute("SELECT name, layer FROM nodes WHERE node_type = 'category' ORDER BY layer, name")
for row in cursor.fetchall():
    print(f"  {row[0]} - {row[1]}")

conn.close()
