#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
搜索包含特定关键词的节点
"""

import sqlite3

def search_nodes():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # 搜索包含"变频"的节点
    print("搜索包含'变频'的节点：")
    cursor.execute("SELECT id, name, weight FROM nodes WHERE name LIKE '%变频%'")
    results = cursor.fetchall()
    if results:
        for r in results:
            print(f"  ID: {r[0]}, 名称: {r[1]}, weight: {r[2]}")
    else:
        print("  未找到")
    
    # 搜索包含"数字"的节点
    print("\n搜索包含'数字'的节点：")
    cursor.execute("SELECT id, name, weight FROM nodes WHERE name LIKE '%数字%'")
    results = cursor.fetchall()
    if results:
        for r in results:
            print(f"  ID: {r[0]}, 名称: {r[1]}, weight: {r[2]}")
    else:
        print("  未找到")
    
    conn.close()

if __name__ == '__main__':
    search_nodes()
