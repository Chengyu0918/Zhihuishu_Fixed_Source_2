#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
更新指定节点的weight值
"""

import sqlite3

def update_weight():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 要更新的节点名称
    node_names = ['卷积的求法', '数字下变频、数字上变频']
    
    # 先查询这些节点的当前状态
    print("更新前的节点状态：")
    for name in node_names:
        cursor.execute("SELECT id, name, weight FROM nodes WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            print(f"  ID: {result[0]}, 名称: {result[1]}, weight: {result[2]}")
        else:
            print(f"  未找到节点: {name}")
    
    # 更新weight值为10
    print("\n正在更新weight值为10...")
    for name in node_names:
        cursor.execute("UPDATE nodes SET weight = 10 WHERE name = ?", (name,))
        if cursor.rowcount > 0:
            print(f"  已更新: {name}")
        else:
            print(f"  未找到节点: {name}")
    
    conn.commit()
    
    # 验证更新结果
    print("\n更新后的节点状态：")
    for name in node_names:
        cursor.execute("SELECT id, name, weight FROM nodes WHERE name = ?", (name,))
        result = cursor.fetchone()
        if result:
            print(f"  ID: {result[0]}, 名称: {result[1]}, weight: {result[2]}")
    
    conn.close()
    print("\n完成!")

if __name__ == '__main__':
    update_weight()
